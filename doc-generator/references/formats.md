# formats.md — Templates exacts par fichier de doc

Ce fichier contient le squelette exact de chaque fichier que le skill produit. Respecte l'ordre des sections. Adapte le contenu aux sources réelles, pas aux exemples.

**Principe général** : 150 lignes max par fichier. Si tu dépasses, scinde. Horodatage en en-tête. Liens relatifs entre fichiers. Pas de jargon inutile dans les fichiers destinés aux non-techs (`README`, `OVERVIEW`, `FEATURES`, `how-to/*`).

---

## README.md

```markdown
# [Nom du projet]

> [Description courte en une phrase — pour qui, pour quoi faire]

*Dernière mise à jour : YYYY-MM-DD*

## C'est quoi ?

[3 à 5 lignes. Qui utilise l'app, quel problème elle résout, dans quel contexte.
Vocabulaire grand public. Pas de jargon technique.]

## Pour qui ?

- **[Rôle 1]** : [ce qu'il fait avec l'app]
- **[Rôle 2]** : [ce qu'il fait avec l'app]
- ...

## État actuel

- [N] features livrées
- [N] en cours
- Dernière mise en prod : [date]

## La doc

- [Vue d'ensemble](OVERVIEW.md) — comprendre le projet en 5 minutes
- [Features](FEATURES.md) — ce qui est fait, en cours, à venir
- [Guides par feature](how-to/) — comment chaque fonctionnalité s'utilise
- [Référence technique](reference/) — pour les devs
- [Onboarding dev](onboarding/README-dev.md) — setup local
```

---

## OVERVIEW.md

```markdown
# Vue d'ensemble

*Dernière mise à jour : YYYY-MM-DD*

## Le projet en une page

[10 lignes max. Raconte le projet à quelqu'un qui n'en a jamais entendu parler. Zéro jargon.]

## Contexte métier

[Explique pour qui c'est fait, quel problème métier ça résout, et pourquoi maintenant.
5 à 10 lignes. Garde simple.]

## Les rôles

[Liste les rôles. Pour chacun, une phrase simple sur ce qu'il peut faire.
Renvoie vers `reference/roles.md` pour le détail technique.]

## Les principes clés

[3 à 6 principes structurants, exprimés en une ligne chacun. Ex :
- "Les données sensibles ne sortent jamais du périmètre du client concerné."
- "Toute feature doit être utilisable sur mobile."]

## Où on en est

[Résumé de l'état — nombre de features livrées, jalon atteint, prochain gros chantier.
Renvoie vers `FEATURES.md` pour le détail.]
```

---

## FEATURES.md

```markdown
# Features

*Dernière mise à jour : YYYY-MM-DD*

## ✅ Terminées

| Feature | Description | Date | Guide |
|---|---|---|---|
| [slug] | [1 phrase courte] | YYYY-MM-DD | [[slug]-guide](how-to/[slug]-guide.md) |

## 🔄 En cours

| Feature | Tâche actuelle | Avancement |
|---|---|---|
| [slug] | T[N]/[total] — [titre court] | [%] |

## ⏳ À venir

| Feature | Priorité | Notes |
|---|---|---|
| [slug] | P[1-3] | [1 ligne de contexte] |
```

**Règle append** : quand tu passes une feature de 🔄 à ✅, tu l'ajoutes au bloc Terminées sans jamais effacer de ligne existante. L'historique est préservé.

---

## how-to/[slug]-guide.md

```markdown
# [Nom de la feature] — Guide

*Feature : [slug] | Clôturée : YYYY-MM-DD*

## État actuel

[Un bloc court et clair, immédiatement après le titre, pour qu'un lecteur qui survole sache en 10 secondes où en est cette feature.]

- **Statut** : ✅ livré / 🔄 partiellement livré / ⚠️ livré avec bugs connus
- **En production** : oui / non / sur staging uniquement
- **Dernière mise à jour de la feature** : YYYY-MM-DD
- **Bugs connus** : [liste courte avec ID bug, ou "aucun"]
- **Prochaine évolution prévue** : [en une ligne, ou "aucune"]

## Où la trouver

Les chemins d'accès dans l'app. Un par rôle si l'accès diffère.

- **[Rôle 1]** : [chemin URL — ex : `/dashboard/timesheets`] — [brève description de la page]
- **[Rôle 2]** : [chemin URL] — [description]

> 📸 *Améliorations futures : des captures d'écran seront ajoutées ici quand la feature screenshots sera implémentée.*

## À quoi ça sert

[3-5 lignes. Qui en a besoin, dans quel contexte, quel problème résolu.
Vocabulaire grand public.]

## Qui peut l'utiliser

- **[Rôle]** : [ce qu'il peut faire avec]
- ...

## Comment ça marche

[Explication fonctionnelle en 5-10 lignes. Le "quoi" et le "pourquoi", pas le "comment technique".
Si un concept métier apparaît pour la première fois, définis-le en une phrase ou renvoie vers OVERVIEW.]

## Mode d'emploi

**Cas normal :**
1. [Étape 1 en langage utilisateur]
2. [Étape 2]
3. [Résultat attendu]

**Cas alternatifs :**
- [Si X se produit] → [que fait le système]
- [Si Y se produit] → [que fait le système]

## Limites et comportements à connaître

- [Edge case 1 — ex : "Impossible de modifier après verrouillage"]
- [Edge case 2]

## Référence technique

Pour les devs qui veulent creuser :
- Tables concernées : [liens vers reference/schema.md#table]
- RLS active : [oui/non — lien vers reference/roles.md]
- Types TS clés : `[Type]` dans `[chemin/fichier.ts]`
- Routes applicatives : [liste des routes Next.js / API concernées]
```

### Comment remplir "Où la trouver"

Pour trouver le chemin URL d'une feature, le skill cherche dans cet ordre :
1. Les routes Next.js : fichiers `app/**/page.tsx` ou `pages/**/*.tsx`
2. Les mentions explicites dans la spec (`features/[slug]-spec.md`) — cherche `/` en début de ligne ou après "chemin", "route", "URL", "page"
3. Les mentions dans les sessions récentes qui parlent du slug

Si aucun chemin n'est trouvé, écris `chemin non détecté — à compléter` et signale-le dans le rapport de fin de run. **Ne pas inventer.**

---

## reference/schema.md

```markdown
# Référence — Schéma de base de données

*Dernière migration : [nom-fichier.sql] | YYYY-MM-DD*

## Conventions

- Clés primaires : `uuid` générées par la DB
- Timestamps : `created_at`, `updated_at` sur toutes les tables
- Sécurité : [RLS activée ou non, par défaut]

---

## Table : [nom_table]

**À quoi elle sert** : [1 phrase en langage métier]

**Colonnes principales :**

| Colonne | Type | Notes |
|---|---|---|
| `id` | `uuid` | PK |
| `...` | `...` | `...` |

**Sécurité (RLS) :**
- Activée : oui / non
- Politique lecture : [qui peut lire quoi]
- Politique écriture : [qui peut écrire quoi]

**Contraintes notables :**
- [ex : index unique sur (employee_id, client_id) où valid_until IS NULL]

**Types TypeScript associés :**
- `[NomType]` dans `[chemin/fichier.ts]`

---

[... une section par table ...]
```

Si le fichier dépasse 150 lignes, scinde par domaine fonctionnel : `schema-users.md`, `schema-billing.md`, etc., avec un index dans `schema.md`.

---

## reference/roles.md

```markdown
# Référence — Rôles et permissions

*Dernière mise à jour : YYYY-MM-DD*

## Matrice des permissions

| Ressource | admin | manager | hr-lead | employee | customer |
|---|---|---|---|---|---|
| [Ressource 1] | ✅ RW | ✅ R | ✅ R | ❌ | ❌ |
| ... | | | | | |

**Légende** : ✅ RW = lecture + écriture, ✅ R = lecture seule, ❌ = aucun accès. Adapter les colonnes aux rôles réels du projet (cf. `project-config.md`).

## Détails par rôle

### [Rôle]
[Ce qu'il voit, ce qu'il fait, ce qui lui est masqué — 3 à 5 lignes.]

## Confidentialités spéciales

- [ex : Le champ `hourly_rate` est visible uniquement par l'admin et par le client concerné. Masqué partout ailleurs, y compris dans les logs applicatifs.]
```

---

## reference/conventions.md

```markdown
# Référence — Conventions de code

*Dernière mise à jour : YYYY-MM-DD*

[Résumé en 80 lignes max des règles de CONVENTIONS.md du projet. Un bullet par règle, avec l'intention (le "pourquoi"), pas juste la règle sèche.]

Pour le détail complet, voir `/CONVENTIONS.md` à la racine du repo.
```

---

## reference/decisions/decision-NNN-slug.md

Une **fiche de décision** (aussi appelée ADR en anglais, pour "Architecture Decision Record") est un petit document qui explique une décision technique importante : qu'est-ce qu'on a choisi, pourquoi, et ce qu'on a écarté. Une par décision, rangée par numéro chronologique.

```markdown
# Fiche de décision NNN : [Titre court de la décision]

*Date : YYYY-MM-DD | Statut : Adoptée / Révisée / Abandonnée*

## Contexte

[3-5 lignes. Qu'est-ce qui a motivé cette décision, quel problème on cherchait à résoudre. Langage simple, compréhensible par un non-initié.]

## Décision

[La décision elle-même, en 2-3 phrases claires.]

## Ce qu'on a écarté

- **[Alternative A]** : [pourquoi pas retenue]
- **[Alternative B]** : [pourquoi pas retenue]

## Conséquences

- ✅ [impact positif]
- ⚠️ [impact négatif ou risque accepté]
- 🔗 [lien vers les features ou fichiers impactés]
```

**Règle d'écriture** : une fiche de décision ne se réécrit jamais (mode *ajout seul* — on ajoute des fiches, on n'efface pas les anciennes). Si une décision est révisée plus tard, on crée une nouvelle fiche avec le numéro suivant qui cite l'ancienne et explique pourquoi on change d'avis.

---

## explanation/architecture.md

```markdown
# Architecture — Le pourquoi des choix

*Dernière mise à jour : YYYY-MM-DD*

## Vue d'ensemble

[Schéma ASCII ou description en 10 lignes de la forme du système : frontend, backend, DB, services externes.]

## Choix structurants

### [Choix 1 — ex : "Pas de backend custom, tout passe par Supabase"]
**Pourquoi** : [raison métier ou technique]
**Impact** : [ce que ça implique pour les devs]
**Voir** : [lien vers la fiche de décision correspondante dans `reference/decisions/`]

[... un bloc par choix ...]
```

---

## explanation/agents-architecture.md

```markdown
# L'équipe des agents

*Dernière mise à jour : YYYY-MM-DD*

Ce projet est construit par une équipe d'agents IA spécialisés. Chaque agent a un rôle précis, des fichiers qu'il lit, des fichiers qu'il produit, et des règles pour passer la main au suivant. L'objectif : éviter qu'un seul acteur prenne des raccourcis en jouant à la fois l'architecte, le codeur et le relecteur.

## Le chef d'orchestre : l'Orchestrateur

**L'Orchestrateur est l'agent principal avec qui l'humain discute directement.** C'est lui qui coordonne toute l'équipe. Il ne code pas, il ne migre pas la base, il ne teste pas — il décide **qui appeler, quand, et avec quel contexte**.

- **Rôle** : reçoit les demandes de l'humain, choisit le bon agent à appeler, vérifie les signaux (ex : `PLAN_APPROVED:`), applique les règles de passage d'un agent à l'autre.
- **Ce qu'il lit** : uniquement les fichiers de contexte (`.claude/memory/agents/main-context.md` et les contextes agents). **Il ne lit jamais directement le code du projet** — c'est une règle stricte qui évite la pollution de contexte (mélanger trop d'infos qui font dériver la réflexion).
- **Ce qu'il produit** : des appels à d'autres agents via l'outil Task, avec un brief ciblé pour chacun.
- **Ce qu'il ne fait jamais** : écrire du code, lancer une migration, faire un commit, lire un fichier source directement.
- **Qui lui parle** : l'humain, et les autres agents via leurs signaux de fin.
- **Modèle utilisé** : [Opus / Sonnet / Haiku — généralement Opus pour la criticité]
- **Pourquoi ce modèle** : [1 à 2 phrases — généralement "l'orchestrateur jongle avec tout le contexte et une erreur de sa part se paie en cascade sur toute la chaîne"]

---

## La galerie des agents exécutants

Ces agents sont appelés par l'Orchestrateur selon les besoins du flow.

### [Nom de l'agent]
- **Rôle** : [en 1 phrase, langage simple]
- **Modèle utilisé** : [Opus / Sonnet / Haiku / hérite du modèle principal de la session]
- **Pourquoi ce modèle** : [en 1 phrase — la raison du choix, centrée sur le risque et la nature de la tâche]
- **Quand l'appeler** : [ce qui fait démarrer son action — ex : "après validation de la spec par l'humain"]
- **Ce qu'il lit** : [fichiers / contextes]
- **Ce qu'il produit** : [fichiers / signaux]
- **Ce qu'il ne fait jamais** : [garde-fou — ex : "ne modifie jamais le code directement"]
- **Passe la main à** : [agent suivant selon le signal produit]

[... un bloc par agent exécutant ...]

## Le flow de livraison d'une feature

[Diagramme ASCII ou liste ordonnée qui montre la séquence complète : qui est appelé après qui, quels signaux déclenchent quel passage. Exemple :]

```
1. Humain : validation spec
2. @architect  → plan technique (PLAN_APPROVED)
3. Humain : validation plan
4. @dba        → migration + RLS (si DB touchée)
5. Boucle par tâche T[N] :
   a. @coder    → génère le fichier
   b. @reviewer mode SPEC → conformité
   c. @reviewer mode QUALITÉ → TypeScript, RLS, edge cases
   d. GATE verification-before-completion
6. @tester     → scénarios depuis la spec
7. @e2etester  → exécution Playwright
8. @deployer   → checklist + déploiement
9. @scribe     → clôture + mise à jour contextes
```

## Principes de conception

[3 à 5 principes qui expliquent pourquoi l'équipe est organisée comme ça. Ex :]
- **Isolation de contexte** : chaque agent reçoit exactement ce qu'il a besoin — ni plus, ni moins.
- **Deux passes de review** : une passe "conformité spec" et une passe "qualité code" — séparées pour éviter qu'un reviewer fatigué ne valide l'un en croyant valider l'autre.
- **Gates explicites** : avant de fermer une tâche, une checklist obligatoire est passée en revue.
```

Ce fichier est **produit une fois en mode `generate`** puis **mis à jour seulement quand un nouvel agent est ajouté ou qu'un rôle change**. Il n'est pas append-only mais les évolutions doivent être visibles via l'horodatage.

---

## explanation/agent-retex.md

Ce fichier est le "carnet de bord" de l'équipe d'agents : ce qui a bien marché, ce qui a coincé, et comment on a corrigé. C'est un fichier **append-only** (on n'efface jamais le passé, on ajoute à la suite).

```markdown
# Retour d'expérience — Agents

*Dernière mise à jour : YYYY-MM-DD | Fichier append-only (on n'efface jamais, on ajoute à la fin)*

Ce document liste, pour chaque agent, ce qui a été observé après plusieurs features livrées : nombre de passages nécessaires avant validation, erreurs qui reviennent souvent, bonnes pratiques, et **journal des ajustements** (les changements apportés à l'agent pour corriger un problème). Il complète [l'équipe des agents](agents-architecture.md), qui décrit le rôle de chaque agent.

## Par agent

### [Nom de l'agent] — [résumé rôle en 1 ligne]
*Rôle complet : voir [agents-architecture.md](agents-architecture.md#[ancre]).*

**Chiffres clés :**
- Nombre de passages pour obtenir un résultat validé (en cas normal, sans erreur) : [N]
- Nombre de passages quand ça coince : [N]

**Erreurs qui reviennent souvent :**
- [Erreur 1 — expliquer en phrase simple]
- [Erreur 2]

**Ce qui marche bien :**
- [Bonne pratique 1]
- [Bonne pratique 2]

**Journal des ajustements**

| Date | Problème rencontré | Ce qu'on attendait | Solution appliquée | Source |
|---|---|---|---|---|
| YYYY-MM-DD | [ce qui a cassé ou frustré en une phrase] | [le comportement correct attendu] | [le changement appliqué à l'agent ou au flow — ou "pas encore résolu"] | [lien vers session ou bug] |

[... une ligne par ajustement, dans l'ordre chronologique, du plus ancien au plus récent ...]

[... un bloc par agent ...]

## Observations qu'on retrouve partout (valables pour plusieurs agents)

- [ex : "Les features qui touchent à la fois la sécurité des données (RLS) et l'interface prennent en moyenne 1,5 fois plus de passages avant validation que les features qui ne touchent que l'interface. Leçon : systématiquement relire les politiques de sécurité, pas juste le fichier livré."]
```

**Règles de rédaction :**

- **Append-only strict** : si le fichier existe déjà, tu préserves tout le contenu historique et tu ajoutes les nouvelles observations à la fin, avec une date.
- **Tableau "Journal des ajustements"** : une ligne = un problème réel rencontré sur une feature passée, avec sa solution. Si la solution n'existe pas encore, écris `pas encore résolu — à suivre`.
- **Source liée** : chaque ajustement renvoie à sa source (numéro de session, bug, ou feature) pour qu'on puisse retrouver le contexte.
- **Pas de jargon non défini** : applique la règle des parenthèses de `tone-guide.md`. Si tu écris "passage en nominal", précise "(dans les cas normaux, sans erreur)". Si tu écris "observations transversales", précise "(qu'on retrouve partout)".

---

## onboarding/README-dev.md

```markdown
# Onboarding Dev

*Dernière mise à jour : YYYY-MM-DD*

## Prérequis

- [Runtime + version — ex : Node 20+]
- [CLI DB — ex : Supabase CLI]
- [Compte accès — ex : Cloudflare Pages, Supabase]

## Installation locale

```bash
git clone [url]
cd [dossier]
npm install
cp .env.example .env.local
# remplir les variables (voir section suivante)
npm run dev
```

## Variables d'environnement

| Nom | Obligatoire | Description |
|---|---|---|
| `VAR_1` | ✅ | [à quoi ça sert] |

## Commandes utiles

| Commande | Effet |
|---|---|
| `npm run dev` | Serveur local |
| `npm run build` | Build de prod |

## Conventions à connaître

- [3-6 points clés extraits de CONVENTIONS.md — lien vers `reference/conventions.md` pour plus]

## Points d'attention

- [ex : "Dev et prod partagent la même base Supabase — toute migration impacte directement la prod."]
- [ex : "Les pages dynamiques Next.js doivent déclarer `export const runtime = 'edge'`."]
```
