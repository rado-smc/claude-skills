# delegation-rules.md — Quand déléguer à un sous-agent et lequel

Pour rester rapide et économique, le skill doit **déléguer la lecture et le résumé des sources volumineuses** à des sous-agents plus petits, au lieu de tout aspirer dans le contexte principal. L'agent principal (qui exécute le skill) se concentre sur la synthèse, la cohérence de ton et l'écriture finale — il ne doit jamais passer son temps à lire 40 migrations SQL une par une.

Ce fichier définit **qui fait quoi** et **pourquoi**.

---

## Règle générale

Trois acteurs, trois usages :

| Acteur | Usage | Quand |
|---|---|---|
| **Script Python** (`scripts/detect_sources.py`) | Détection pure, déterministe | Toujours, en premier — zéro token |
| **Sous-agent Haiku** | Scan et extraction sur petits volumes | Lecture de fichiers `.md` d'agents, extraction de frontmatter, résumé d'une spec courte, listage des routes Next.js |
| **Sous-agent Sonnet** | Scan et synthèse sur gros volumes | Lecture de 20 migrations SQL, cartographie d'une arbo complète, extraction de logique métier depuis 10 specs longues |
| **Agent principal (Opus)** | Synthèse finale, cohérence, écriture | Rédaction des fichiers de sortie, arbitrages, respect du `tone-guide.md` |

---

## Arbre de décision

Quand le skill rencontre une tâche de lecture, il suit cet arbre :

```
La tâche est-elle déterministe (existence fichier, parsing JSON/TOML, listage dir) ?
├── OUI → Script Python (detect_sources.py ou helper ad hoc)
└── NON
    │
    Le volume total à lire tient-il sous ~5 000 tokens ?
    ├── OUI → Sous-agent Haiku (fiable et peu coûteux sur du résumé fidèle de petit volume)
    └── NON
        │
        Le résultat demande-t-il un raisonnement plus complexe que du résumé ?
        ├── NON → Sous-agent Sonnet (volume élevé, extraction structurée)
        └── OUI → Sous-agent Sonnet en première passe, puis escalade à l'agent principal
```

---

## Cas concrets

### Cas 1 — Lister les agents et extraire leur modèle
- Volume : 8 fichiers .md, ~200 lignes chacun, frontmatter + corps
- **Délégation** : Script Python d'abord (détection existence, extraction frontmatter `model:`) puis **Haiku** pour résumer le rôle de chaque agent en 1 phrase si le corps n'est pas structuré
- **Pourquoi** : frontmatter est du YAML → parsable sans LLM ; le rôle d'un agent est généralement explicite dans les 5 premières lignes du corps → Haiku suffit largement

### Cas 2 — Cartographier les tables d'un schéma Supabase
- Volume : 42 migrations SQL, ~3 000 lignes total
- **Délégation** : **Sonnet** — trop volumineux pour Haiku, pas besoin d'Opus car la tâche est structurée (CREATE TABLE / ALTER TABLE / CREATE POLICY → liste de tables + colonnes + policies)
- **Pourquoi** : résumer 42 fichiers en une matrice structurée est le type de tâche où Sonnet brille. Opus serait du gâchis.

### Cas 3 — Comprendre la logique de facturation à partir des specs
- Volume : 8 specs features liées à la facturation, chacune 300-800 lignes
- **Délégation** : **Sonnet** pour extraire les règles métier explicites, puis **agent principal** pour rédiger `explanation/billing-logic.md` avec le ton approprié
- **Pourquoi** : l'extraction est un job Sonnet ; la rédaction finale demande la cohérence avec le reste de la doc donc reste à l'agent principal

### Cas 4 — Identifier la route URL d'une feature Next.js
- Volume : 1 fichier `page.tsx` à trouver via grep, plus 1 à 2 fichiers voisins
- **Délégation** : **Haiku** avec instruction précise : "trouve le fichier `page.tsx` dans `src/app/**/portal/**` et retourne le chemin URL dérivé"
- **Pourquoi** : tâche ciblée, petit volume, pas de raisonnement — Haiku est parfait

### Cas 5 — Détecter les drifts (sources apparues / disparues) depuis le dernier run
- Volume : 1 fichier `project-config.md` précédent + 1 JSON de détection courant
- **Délégation** : **Script Python** (déjà intégré dans `detect_sources.py --previous-config`)
- **Pourquoi** : comparaison de listes, aucun LLM nécessaire

### Cas 6 — Rédaction d'une fiche de décision à partir d'une entrée de `DECISIONS.md`
- Volume : 1 entrée de ~30 lignes
- **Délégation** : **agent principal** directement
- **Pourquoi** : volume trop petit pour justifier un sous-agent, et la rédaction doit respecter le format des fiches de décision + le ton du projet

### Cas 7 — Lecture du `RETOUR-EXPERIENCE-AGENTS.md` pour nourrir `agent-retex.md`
- Volume : fichier unique, souvent 500 à 2 000 lignes
- **Délégation** : **Sonnet** — trop gros pour Haiku, tâche structurée (extraire ajustements par agent)
- **Pourquoi** : Sonnet résume fidèlement et extrait la structure `agent → problème → solution` sans dériver

---

## Rédaction du prompt du sous-agent

Un sous-agent délégué ne voit pas la conversation principale — il démarre avec contexte vierge. Donc le prompt doit :

1. **Nommer le skill qui délègue** (« tu travailles pour le skill `doc-generator` »)
2. **Préciser le but** (ex : « je veux la liste des tables Supabase avec leurs colonnes clés et leur RLS »)
3. **Lister les fichiers à lire** en chemins absolus
4. **Définir le format de sortie** attendu (JSON structuré, Markdown, tableau)
5. **Poser les limites** : pas de créativité, pas d'invention, source-driven strict
6. **Demander un rapport court** (10 lignes max) avec signalement des ambiguïtés

Exemple type pour un délégué Sonnet :

> Tu travailles pour le skill `doc-generator`. Lis les 42 fichiers SQL dans `supabase/migrations/` et produis un JSON structuré avec la liste des tables créées, leurs colonnes clés (pk + colonnes métier importantes), et les policies RLS associées. Ne lis rien d'autre. Ne résume pas, structure. Format attendu : `[{"table": "...", "columns": [...], "rls": [...]}]`. Si une ambiguïté est détectée, ajoute un champ `_warning`. Rapport final : 10 lignes max, citant uniquement les anomalies. Démarre maintenant.

---

## Parallélisation

Quand plusieurs délégations sont indépendantes (ex : "scan des agents" + "scan des migrations" + "scan des features"), **lancer les sous-agents en parallèle** dans un seul message avec plusieurs appels d'outils Task simultanés. Le coût en temps humain devient celui du plus lent, pas la somme des trois.

Règle : **3 sous-agents en parallèle maximum**. Au-delà, la complexité de suivi dépasse le gain en latence.

---

## Ce qu'il ne faut PAS déléguer

- La **rédaction finale** des fichiers de sortie — doit rester dans l'agent principal pour garantir la cohérence du ton entre fichiers
- Les **arbitrages** : "faut-il produire ce fichier ?" → décision du skill, pas d'un sous-agent
- La **lecture de la config projet** (`project-config.md`) — c'est la référence qui pilote tout, l'agent principal doit l'avoir en contexte
- La **lecture du `tone-guide.md`** — c'est la base du style, à charger dans l'agent principal à la première rédaction

---

## Coût et latence attendus

Ordre de grandeur sur un projet mature (30 migrations, 50 features, 8 agents) :

| Phase | Acteur | Durée estimée | Coût relatif |
|---|---|---|---|
| Détection | Script Python | < 2 secondes | 0 |
| Scan agents | Haiku sous-agent | 15-30 secondes | très faible |
| Scan migrations | Sonnet sous-agent | 60-120 secondes | modéré |
| Scan features + logique métier | Sonnet sous-agent | 120-240 secondes | modéré |
| Synthèse + rédaction finale | Agent principal | 300-600 secondes | élevé |
| **Total** | — | **8-15 minutes** | **~60% moins cher** que tout faire dans l'agent principal |

Sur un projet nu (bootstrap minimal), la phase délégation est quasi vide — tout le budget part dans la synthèse, mais le total est petit (5 fichiers à produire).
