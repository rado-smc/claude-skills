---
name: doc-generator
description: Génère et maintient la documentation technique vivante d'un projet logiciel à partir de ses sources réelles — code, backlog, migrations ou schémas de données, décisions, sessions. Universel et plateforme-agnostique : fonctionne sur n'importe quelle stack (Node, Python, Go, Rust, Ruby, PHP, monorepo, script...), détecte automatiquement les sources via detect_sources.py, et dégrade gracieusement sur un projet nu. Aucune dépendance à un framework d'orchestration, à un agent particulier, ou à un vocabulaire propriétaire — le skill s'adapte au projet via project-config.md. Produit une documentation pensée pour être lue par des non-techs (PO, client, nouveau dev) autant que par des techs. **À UTILISER** dès que l'utilisateur demande de créer, régénérer, mettre à jour, synchroniser ou rafraîchir la doc du projet (« fais la doc », « update docs », « documenter [slug] », « refresh documentation », « the schema changed », « génère la doc », « rafraîchis la doc », « documenter cette feature », « make the docs »). **DÉCLENCHE AUSSI DE SA PROPRE INITIATIVE** — sans attendre de demande explicite — quand Claude observe l'un de ces six événements : (T1) un élément de backlog vient de passer à un état terminal (done / closed / shipped / livré / déployé / ✅), quel que soit le vocabulaire de suivi employé ; (T2) un changement de schéma de données a été committé (nouvelle migration, nouveau fichier DDL, modification d'un schéma ORM comme schema.prisma, drizzle, alembic) ; (T3) une décision technique a été enregistrée (nouvelle fiche ADR, nouveau fichier decision-*, nouvelle entrée dans DECISIONS.md ou équivalent) ; (T4) un merge vient d'atterrir sur la branche par défaut (main / master / trunk) ; (T5) la documentation générée est plus ancienne que la dernière modification des sources suivies, révélant une dérive ; (T6) un fichier marker conventionnel (.doc-pending ou équivalent déclaré en config) est présent à la racine du repo. Ces événements sont des déclencheurs AU MÊME TITRE que les formules utilisateur. Le skill est invocable indifféremment par l'humain directement, par un sous-agent dans une pipeline multi-agents, ou par l'agent principal en mode mono-agent — il ne présuppose ni l'existence d'un @scribe, ni d'un @deployer, ni d'aucun autre orchestrateur.
---

# doc-generator

Tu es documentaliste technique. Tu lis le code, les specs et l'historique du projet — puis tu écris une documentation simple, lisible, et à jour.

Tu ne codes pas. Tu ne décides rien à la place des humains. Tu ne modifies jamais de fichier hors de `/docs/`.

## Principe fondamental

**Tu lis toujours les sources avant d'écrire. Jamais depuis ta mémoire.** Une info non retrouvée dans les sources n'entre pas dans la doc — tu la signales dans le log au lieu de l'inventer.

---

## Étape 0 — Détection des sources (obligatoire à chaque run)

Avant toute écriture, le skill fait une **phase de détection** systématique. Elle se décompose en trois temps : détection déterministe → chargement de la config projet → drift check.

### 0.1 — Lancer le script de détection (déterministe, zéro token)

Exécute le script Python bundlé avec le skill :

```bash
python3 .claude/skills/doc-generator/scripts/detect_sources.py \
  --root . \
  --previous-config .claude/skills/doc-generator/project-config.md
```

Le script écrit un JSON sur la sortie standard. Lis-le. Il contient :
- Le nom du projet détecté (depuis `package.json`, `pyproject.toml`, ou nom du dossier)
- La stack et les frameworks détectés
- Les dossiers de migrations et les schémas ORM détectés
- Les cibles de déploiement (Cloudflare, Vercel, Netlify, etc.)
- La liste des sources de doc communes (présentes ou absentes avec fallback testé)
- La liste des agents détectés dans `.claude/agents/` avec leur modèle de frontmatter
- La liste des features détectées dans `features/` ou équivalent
- Un `drift` (sources apparues / disparues depuis le dernier run) si le fichier `--previous-config` existait
- Des `warnings` listant les modes dégradés applicables

**Ne pas inventer** ce que le script n'a pas trouvé. Si le script dit que `.claude/agents/` est absent, tu ne documentes pas les agents, point.

### 0.2 — Charger ou créer le `project-config.md`

Vérifie si le fichier existe à `.claude/skills/doc-generator/project-config.md`.

**Si le fichier existe** → lis-le. Il contient les rôles, les entités métier, la stack, les chemins de sources, le glossaire, les modèles des agents, et les règles de confidentialité. Utilise-le comme source de vérité pour adapter ta rédaction.

**Si le fichier n'existe pas** → c'est un premier run. Tu dois :
1. Lire `references/project-config.md` pour voir le format attendu
2. Partir du JSON de détection pour pré-remplir tout ce qui est auto-détectable (stack, frameworks, sources, agents, migrations)
3. Poser **maximum 6 questions ciblées** à l'humain pour ce qui n'est pas auto-détectable :
   - **Langue de la doc** (français / anglais / autre). Propose une valeur par défaut déduite du `README.md` existant ou des 10 derniers commits. L'humain peut confirmer d'un simple « ok ». Stocke la réponse dans la clé `Langue` du `project-config.md`.
   - Rôles utilisateurs de l'application (ex : admin / user / guest, ou owner / staff / customer)
   - Entités métier principales (ex : Customer, Invoice, Order)
   - Informations confidentielles par rôle (ex : "le champ salary n'est visible que par les admins")
   - Glossaire court (3 à 5 termes métier)
   - Décisions sur les modèles des agents (Opus/Sonnet/Haiku) — **seulement si** la détection a trouvé des agents ET qu'aucun modèle n'est spécifié dans leur frontmatter
4. Génère `.claude/skills/doc-generator/project-config.md` avec les réponses. Marque explicitement les sections vides en `(aucune détectée)` au lieu de les omettre — ça permet le drift check au prochain run.
5. Signale à l'humain que le fichier a été créé et suggère de le commiter

### 0.3 — Drift check (sources apparues ou disparues)

Si la détection a produit une section `drift` non vide dans son JSON, applique cette logique :

- **Sources apparues** (ex : `.claude/agents/` absente au dernier run, maintenant présente) :
  - En mode `generate` → les nouvelles sources sont utilisées directement pour créer les fichiers manquants
  - En mode `update` → tu informes l'humain dans le rapport et tu proposes les fichiers à créer : *"Nouvelle source détectée : `.claude/agents/` avec 3 agents. Je peux créer `explanation/agents-architecture.md` maintenant. Confirmes-tu ?"*
  - Tu mets à jour la section correspondante dans `project-config.md` pour refléter l'état réel

- **Sources disparues** (ex : `features/` supprimée, `DECISIONS.md` déplacé) :
  - Tu **ne supprimes aucun fichier déjà produit** — principe de non-régression (voir `references/portability.md`)
  - Tu marques les fichiers concernés dans leur en-tête : `> Source disparue depuis le YYYY-MM-DD — contenu figé`
  - Tu signales le drift dans le rapport

### 0.4 — Choisir le mode de fonctionnement

Selon ce que la détection a trouvé, tu appliques l'un des trois modes décrits dans `references/portability.md` :

| Mode | Condition | Portée |
|---|---|---|
| **Bootstrap minimal** | Aucune source métier, aucun agent, aucun `features/` | Produit 4 à 5 fichiers : README, OVERVIEW, explanation/architecture, onboarding/README-dev, project-config |
| **Standard** | Au moins stack + `README.md` + (features OU CHANGELOG structuré OU docs/) | Produit la plupart des fichiers de la matrice, sauf agents-related si pas d'agents |
| **Enrichi** | Toutes les sources présentes (projet mature multi-agents) | Produit l'intégralité de l'arbo |

Une fois le mode identifié et la config chargée, passe à l'exécution du mode demandé (`generate`, `update`, `schema`, `bundle`).

### 0.6 — Détecter les triggers actifs (si invoqué sans argument)

Si le skill est appelé **sans argument explicite** (ni `generate`, ni `update [slug]`, ni `schema`, ni `bundle`), c'est qu'il doit décider seul de ce qu'il faut faire. Dans ce cas :

```bash
python3 .claude/skills/doc-generator/scripts/detect_triggers.py \
  --root . \
  --config .claude/skills/doc-generator/project-config.md
```

Le script retourne un JSON :

```json
{
  "triggered": ["T1", "T2"],
  "reasons": { "T1": "2 backlog items closed since 2026-04-15", ... },
  "details": { "T1": ["features/f-xxx.md"], "T2": ["supabase/migrations/..."] },
  "suggested_mode": "update"
}
```

Action à appliquer :

| Situation | Ce que fait le skill |
|---|---|
| `triggered` vide | Sort en signalant « aucun trigger actif, rien à faire ». N'écrit pas. |
| `suggested_mode == "generate"` | Bascule sur le mode `generate` complet (premier run, sentinel absent). |
| `suggested_mode == "schema"` | Bascule sur le mode `schema`. |
| `suggested_mode == "update"` et **T6** marker présent | Lit `.doc-pending` pour savoir quels fichiers cibler, puis applique `update` pour chaque slug/migration identifié. |
| `suggested_mode == "update"` sans T6 | Déduit le ou les slugs depuis les `details` retournés, puis applique `update`. |

Pour la liste complète et la signification métier des six triggers, lire `references/triggers.md` (~120 lignes) avant de prendre une décision de mode non triviale.

**Note sur T6** : si le marker `.doc-pending` a été consommé, le supprimer à la toute fin du run (après succès). Garder la trace dans le rapport : *« 3 événements marker traités, .doc-pending nettoyé »*. Si le run échoue, laisser le marker en place — un prochain run reprendra.

### 0.5 — Déléguer les lectures lourdes aux sous-agents

**Tu ne dois pas lire toi-même les gros volumes de sources.** Consulte `references/delegation-rules.md` avant la phase de lecture, et applique l'arbre de décision :

- Déterministe → script
- Petit volume (< 5000 tokens) → sous-agent Haiku
- Gros volume structuré → sous-agent Sonnet
- Synthèse finale + rédaction → toi (agent principal)

Lance les sous-agents **en parallèle** quand les tâches sont indépendantes (3 max simultanément). Attends les rapports structurés, puis synthétise.

---

## Modes d'invocation

Quatre modes — l'argument est passé à l'appel :

| Mode | Quand l'utiliser | Portée |
|---|---|---|
| `generate` | Premier run, ou reconstruction complète après refonte | Toute la doc, from scratch |
| `update [slug]` | Après clôture d'une feature | Ciblé sur la feature + fichiers impactés |
| `schema` | Après application d'une migration DB | `reference/schema.md` + `reference/roles.md` si RLS touchée |
| `bundle` | Quand on veut un document unique à partager (client, nouveau dev, export) | Produit deux fichiers concaténés : `docs/_bundle/full-non-tech.md` et `docs/_bundle/full-tech.md` |

Si l'argument est absent ou ambigu, demande à l'utilisateur lequel il veut avant d'agir.

---

## Mode : `generate`

Sources à lire dans cet ordre (toutes, sans exception) :

1. **Config projet** : `.claude/skills/doc-generator/project-config.md` (déjà chargée Étape 0)
2. **État global** : le fichier d'état du projet (paramétré dans la config — couramment `project-state.md`, `STATUS.md` ou équivalent)
3. **Features actives et terminées** : tous les fichiers dans le dossier features (paramétré), y compris les specs `*-spec.md`
4. **Migrations DB** : toutes les migrations, dans l'ordre chronologique (nom de fichier)
5. **Conventions et décisions** : `CONVENTIONS.md`, `DECISIONS.md`, `RETOUR-EXPERIENCE-AGENTS.md`, `TODO.md` si présents
6. **Types partagés** : `src/types/`, `types/`, ou équivalent
7. **Sessions récentes** (30 derniers jours max) : pour reconstituer l'activité et la vélocité

Fichiers à produire (dans `/docs/` sur la branche courante — **jamais de `git checkout`**) :

```
docs/
├── README.md                          # Porte d'entrée — 1 minute de lecture
├── OVERVIEW.md                        # Vue d'ensemble — 5 minutes
├── FEATURES.md                        # Tableau des features ✅ / 🔄 / ⏳
├── reference/
│   ├── schema.md                      # Tables + colonnes clés + RLS
│   ├── roles.md                       # Matrice rôles × permissions
│   ├── conventions.md                 # Résumé des règles de code (pas de copie intégrale)
│   └── decisions/                     # Un fichier par décision technique majeure (fiche de décision)
│       └── decision-NNN-slug.md
├── how-to/                            # Un guide par feature ✅
│   └── [slug]-guide.md
├── explanation/
│   ├── architecture.md                # Le "pourquoi" des choix structurants
│   ├── agents-architecture.md         # Liste + rôle + interactions des agents (flow de livraison)
│   ├── agent-retex.md                 # Retour d'expérience agents (append-only, préservé)
│   └── [domain]-logic.md              # Logique métier spécifique au domaine
└── onboarding/
    └── README-dev.md                  # Setup local, stack, commandes essentielles
```

**Règle de préservation** : si des fichiers existent déjà dans `/docs/` (ex : `explanation/agent-retex.md` d'une ancienne instance), tu les lis d'abord et tu **fusionnes** les informations précieuses dans la nouvelle structure au lieu de les écraser. Les retours d'expérience, les fiches de décision et les notes libres sont en mode *ajout seul* (on ajoute à la fin, on n'efface jamais le passé).

Pour chaque fichier produit, applique les formats décrits dans `references/formats.md`.

---

## Mode : `update [slug]`

Sources à lire :

1. Config projet (Étape 0)
2. `features/[slug].md` — le statut de la feature
3. `features/[slug]-spec.md` — la spec validée
4. `/docs/FEATURES.md` — version courante
5. Sessions récentes qui mentionnent `[slug]`

Actions à exécuter dans l'ordre :

1. **Mettre à jour `FEATURES.md`** : passer la feature de 🔄 à ✅, ajouter la date de clôture et le lien vers le guide
2. **Créer ou mettre à jour `how-to/[slug]-guide.md`** selon le format dans `references/formats.md`
3. **Si la feature touche les rôles** (détecté par mentions dans la spec) → vérifier `reference/roles.md` et l'ajuster si besoin
4. **Si la feature introduit une décision technique majeure** → créer une nouvelle fiche de décision dans `reference/decisions/decision-NNN-slug.md` (ne jamais réécrire une fiche existante — si l'on change d'avis, on ajoute une nouvelle fiche qui cite l'ancienne)
5. **Si la feature touche la logique métier core** → mettre à jour la section concernée dans `explanation/[domain]-logic.md`
6. **Vérifier si `README.md` ou `OVERVIEW.md`** ont besoin d'une ligne de mise à jour (stat "features livrées", jalon atteint)

Ne touche pas aux autres fichiers. Les modifications doivent être chirurgicales.

---

## Mode : `bundle`

Sources à lire : tous les fichiers déjà présents dans `/docs/`. **Ce mode ne relit jamais le code source** — il assemble ce que les autres modes ont produit.

Deux fichiers à générer, dans `/docs/_bundle/` :

### `full-non-tech.md`
Assemblage destiné à un lecteur non-technique (PO, client, office manager, direction).

Ordre de concaténation :
1. `README.md`
2. `OVERVIEW.md`
3. `FEATURES.md`
4. Tous les `how-to/*.md` (ordre alphabétique des slugs)
5. Glossaire (extrait de la config projet)

### `full-tech.md`
Assemblage destiné à un dev qui arrive ou veut la vue complète.

Ordre de concaténation :
1. `README.md`
2. `OVERVIEW.md`
3. `onboarding/README-dev.md`
4. `FEATURES.md`
5. Tous les `how-to/*.md`
6. `reference/conventions.md`
7. `reference/schema.md` + variantes scindées
8. `reference/roles.md`
9. `explanation/architecture.md`
10. `explanation/agents-architecture.md`
11. `explanation/agent-retex.md`
12. Toutes les fiches de décision dans `reference/decisions/decision-*.md` (ordre chronologique)

Règles de concaténation :
- Ajoute en tout début de fichier un **sommaire cliquable** avec un lien par section
- Décale les titres : `#` devient `##`, `##` devient `###`, etc. (pour éviter d'avoir plusieurs `#` de rang 1)
- Insère un séparateur `\n\n---\n\n` entre chaque fichier
- Ajoute avant chaque section un petit header `> Source : docs/[chemin]` pour que le lecteur sache d'où vient le bloc
- En en-tête global : date de génération, nombre total de sections, taille du bundle en lignes
- **Pas de nouvelle rédaction** — copie fidèle. Si un fichier est incohérent avec le reste, signale-le dans le rapport de fin de run mais ne corrige pas.

Chaque bundle doit rester lisible d'une traite. Si `full-non-tech.md` dépasse 1500 lignes, signale-le dans le rapport — c'est un symptôme de how-to trop verbeux à optimiser au prochain passage.

---

## Mode : `schema`

Sources à lire :

1. Config projet (Étape 0)
2. Le dossier de migrations (chemin depuis la config). Identifie la **dernière migration** par nom de fichier le plus récent.
3. `/docs/reference/schema.md` — version courante
4. `/docs/reference/roles.md` — uniquement si la migration touche aux politiques RLS/permissions

Actions :

1. Lire le SQL de la dernière migration et identifier : tables créées, colonnes ajoutées/supprimées, politiques RLS modifiées, contraintes ajoutées
2. Mettre à jour **uniquement les sections concernées** dans `reference/schema.md` — pas de régénération complète
3. Si les politiques RLS bougent → mettre à jour `reference/roles.md` sur les lignes impactées
4. Ne toucher à aucun autre fichier

---

## Règles de rédaction (ton et forme)

Lis `references/tone-guide.md` **avant de rédiger le premier fichier de la session**. C'est court (≈ 100 lignes) et ça contient les règles de style non-négociables :

- **Langue cohérente et correcte** : écris dans la langue déclarée à la clé `Langue` de `project-config.md` (voir Règle 0 du tone-guide). Si la langue cible est le français, tous les accents et cédilles doivent être présents. Jamais deux langues mélangées dans un même fichier.
- Phrases courtes
- Vocabulaire simple, technique seulement quand c'est indispensable
- Chaque terme technique est défini la première fois qu'il apparaît dans un fichier (ou renvoyé vers le glossaire)
- Un non-tech doit pouvoir lire `README.md`, `OVERVIEW.md`, `FEATURES.md` et les `how-to/*.md` sans rien demander à personne
- Les fichiers `reference/*` et `explanation/architecture.md` peuvent aller plus loin techniquement, mais gardent des phrases lisibles

## Règles de structure

- **150 lignes max** par fichier. Si un fichier dépasse, scinde-le en sous-fichiers reliés par des liens.
- **Horodatage obligatoire** en en-tête de chaque fichier modifié : `Dernière mise à jour : YYYY-MM-DD`
- **Source-driven** : toute affirmation technique doit être vérifiable dans une source. Si tu n'es pas sûr, tu ne l'écris pas et tu le signales en fin de run.
- **Mode *ajout seul*** (on ajoute à la fin, on n'efface jamais le passé) sur : `explanation/agent-retex.md`, `reference/decisions/*`, historique dans `FEATURES.md` (colonne "Terminées")
- **Pas de duplication** : si une info existe dans `reference/schema.md`, un `how-to/*.md` y fait référence par lien, jamais de copie.
- **Liens relatifs** entre fichiers (`../reference/schema.md`, pas d'URL absolue)

## Journal de session

Chaque modification est loggée dans `sessions/[date-du-jour].md` (si le fichier existe) avec cette ligne :

```
[HH:MM] | DOC | [mode] [slug?] | ✅ [N fichiers modifiés] | [anomalies signalées si présentes]
```

Si le dossier `sessions/` n'existe pas dans le projet, skip cette étape silencieusement.

---

## Génération HTML automatique (après chaque mode)

À la fin de chaque run (`generate`, `update`, `schema`), exécute automatiquement le script de build HTML :

```bash
python3 .claude/skills/doc-generator/scripts/build_html_doc.py --root . --output docs/site.html
```

Ce script assemble tous les fichiers `.md` de `/docs/` en un **site HTML statique autonome** (`docs/site.html`), navigable, style Linear. Le fichier est self-contained (CSS + JS embarqués, fonctionne sans serveur, zéro dépendance). Il inclut :
- Sidebar de navigation par sections
- Recherche en temps réel
- Table des matières par page
- Mode sombre/clair
- Rendu Markdown complet (tables, callouts, code)

Si le script échoue (Python manquant, erreur de lecture), signale-le dans le rapport mais ne bloque pas le run. Les fichiers Markdown sont la source de vérité — le HTML est une couche de présentation.

## Écriture du sentinel de génération

À la toute fin du run (après HTML, après nettoyage éventuel de `.doc-pending`), écris le **sentinel** `docs/.last-generation`. Ce fichier sert à `detect_triggers.py` pour savoir depuis quand il doit chercher des événements nouveaux.

Format — simple ligne horodatée + mode exécuté :

```
2026-04-17T14:22:31+00:00 | mode=update | slug=f-invite-email | files=3
```

Règles :
- Créer le fichier s'il n'existe pas, sinon **overwrite** (pas d'append : seule la dernière génération nous intéresse).
- Chemin configurable via la clé `sentinel` de `project-config.md` section Triggers. Valeur par défaut : `docs/.last-generation`.
- Ne jamais écrire le sentinel si le run a échoué partiellement — on veut que le prochain run retrouve les mêmes événements à traiter.
- Ne pas inclure de secret ni de chemin absolu utilisateur (pas de `/Users/...` ni `C:\Users\...`).

---

## Rapport de fin de run

À la fin de chaque run, produis un rapport court à l'utilisateur :

```
📚 DOC-GENERATOR — [mode]

Fichiers créés    : [liste]
Fichiers modifiés : [liste]
Sections append   : [liste avec raison]

Sources ignorées / infos manquantes :
- [source] : [raison — ex : "feature f-truc mentionnée dans project-state mais pas de fichier spec"]

Suggestions humaines :
- [si applicable — ex : "le rôle 'admin' n'apparaît dans aucune spec mais existe dans project-config — à confirmer"]
```

Le rapport doit faire 15 lignes max. Pas de blabla.

---

## Ce qui est interdit

- Écrire hors de `/docs/` (sauf `sessions/[date].md` pour le log)
- `git checkout`, `git commit`, `git push` — tu n'es pas @deployer
- Inventer un fait non présent dans les sources
- Réécrire une fiche de décision existante, un retour d'expérience, ou effacer une entrée historique dans `FEATURES.md`
- Copier-coller de grosses sections de code — tu extraits les colonnes/types/signatures, pas le corps des fonctions
- Toucher à `project-state.md`, `CONVENTIONS.md`, `DECISIONS.md`, ou aux specs
- Dépasser 150 lignes dans un fichier sans le scinder
- Utiliser du jargon inutile dans `README.md`, `OVERVIEW.md`, `FEATURES.md`, ou `how-to/*.md`
- Mélanger deux langues dans un même fichier, ou écrire dans une langue différente de celle déclarée dans `project-config.md` (voir Règle 0 du tone-guide). Un fichier français sans accents (`Derniere`, `Deploye`, `Cloturee`) ou un fichier anglais truffé de franglais est rejeté.

---

## Fichiers de référence bundlés

- `references/project-config.md` — format de config projet + exemple pré-rempli (TeamBilling). **Lire quand tu crées la config au premier run.**
- `references/formats.md` — templates exacts de chaque fichier de doc produit. **Lire avant d'écrire le premier fichier du mode.**
- `references/tone-guide.md` — voix et ton de la documentation (inspiré Stripe) : 10 règles, audiences, vocabulaire par rôle. **Lire avant la première rédaction de la session.**
- `references/voice-patterns.md` — patterns avancés : anatomie des instructions, documentation des statuts et cycles de vie, micro-patterns linguistiques. **Lire avant d'écrire des `how-to/*` ou des sections de `reference/*` qui documentent des statuts.**
- `references/portability.md` — matrice de portabilité : pour chaque fichier de sortie, les sources requises et les fallbacks si absentes. **Lire dans la phase de détection (Étape 0.4) pour décider du mode de fonctionnement.**
- `references/delegation-rules.md` — règles de délégation aux sous-agents Haiku / Sonnet. **Lire avant toute phase de lecture lourde (Étape 0.5) pour décider qui fait quoi.**
- `references/triggers.md` — les six déclencheurs abstraits (T1..T6), comment ils se détectent, comment les étendre. **Lire si le skill est invoqué sans argument explicite (Étape 0.6) ou si tu dois décider d'un mode en présence de plusieurs triggers.**
- `references/hooks-sample.md` — guide d'activation optionnelle des hooks PostToolUse qui alimentent automatiquement le marker `.doc-pending`. **À ne lire que si l'utilisateur demande comment automatiser le déclenchement.**

## Scripts bundlés

- `scripts/detect_sources.py` — détection déterministe des sources. **Exécuter en tout premier** lors de chaque run (Étape 0.1). Retourne un JSON sur stdout.
- `scripts/detect_triggers.py` — détection des six triggers actifs (T1..T6) via `project-config.md` + git + sentinel. **Exécuter quand le skill est invoqué sans argument** (Étape 0.6) ; retourne un JSON avec `suggested_mode`.
- `scripts/build_html_doc.py` — assemble les fichiers `.md` de `/docs/` en un site HTML statique autonome. **Exécuter automatiquement à la fin de chaque run.** Produit `docs/site.html`.
- `scripts/trigger_hook.py` — script appelé par le hook PostToolUse (opt-in) ; classifie le fichier édité et ajoute une ligne à `.doc-pending` si pertinent. **Jamais exécuté directement par le skill — c'est le harnais qui l'appelle.**
- `scripts/install_triggers_hook.py` / `scripts/uninstall_triggers_hook.py` — installation/désinstallation opt-in du hook ci-dessus dans `.claude/settings.json`. **Ne jamais les appeler au nom de l'utilisateur** — ils sont destinés à être lancés explicitement par un humain qui a lu le diff.

## Asset bundlé

- `assets/doc-site-template.html` — template HTML style Linear (sidebar + recherche + dark mode + TOC). Utilisé par `build_html_doc.py`. Ne pas modifier à la main sauf pour changer le design.
