# portability.md — Matrice de portabilité

Ce fichier décrit **exactement ce que le skill produit en fonction des sources présentes** dans le projet. Le skill est conçu pour fonctionner sur n'importe quel projet, du plus nu (juste `package.json` et `README.md`) au plus riche (projet mature avec agents, sessions, features, décisions).

Règle d'or : **aucun fichier de sortie n'est produit s'il n'a pas au moins une source pour le nourrir.** Pas de doc inventée.

---

## Matrice : fichier de sortie → sources requises → fallback si absent

### `docs/README.md`
- **Sources principales** : `package.json` ou manifeste équivalent, `README.md` existant (s'il y en a un), détection stack
- **Fallback si rien** : nom du dossier + contenu du `project_name` détecté
- **Toujours produit** : oui. Même sur un projet nu on génère au moins un README minimal.

### `docs/OVERVIEW.md`
- **Sources principales** : config projet (rôles, entités), `project-state.md` (état global), `features/` (comptage), `CHANGELOG.md`
- **Fallback si aucune source métier** : vue d'ensemble basée uniquement sur la stack + les frameworks détectés (ex : "projet Next.js 14 avec Supabase, déployé sur Cloudflare Pages")
- **Toujours produit** : oui (version dégradée si pas de métier détecté)

### `docs/FEATURES.md`
- **Sources principales** : `features/*.md`, `features/*-spec.md`
- **Sources secondaires** : commits git avec préfixes conventionnels (`feat:`, `fix:`), `CHANGELOG.md`, issues GitHub/GitLab via CLI si disponible
- **Fallback si rien** : si ni `features/` ni convention de commits → **fichier non produit**, signalé dans le rapport avec recommandation "adopter une convention de commits ou créer un dossier features/ pour activer FEATURES.md"
- **Toujours produit** : non

### `docs/reference/schema.md`
- **Sources principales** : dossier de migrations détecté (supabase, prisma, drizzle, alembic, rails, knex, etc.), ou fichier schéma ORM (`prisma/schema.prisma`, `drizzle/schema.ts`)
- **Sources secondaires** : types TypeScript dans `src/types/` ou équivalent
- **Fallback si rien** : **fichier non produit**, signalé dans le rapport
- **Toujours produit** : non

### `docs/reference/roles.md`
- **Sources principales** : config projet section "Rôles utilisateurs", policies RLS dans migrations, rôles hardcodés dans le code (enums `UserRole`, etc.)
- **Fallback si rien** : **fichier non produit**. Un projet sans rôles n'a pas besoin de cette page.
- **Toujours produit** : non

### `docs/reference/conventions.md`
- **Sources principales** : `CONVENTIONS.md`, `.claude/rules/*.md`, `.eslintrc*`, `.prettierrc*`, `pyproject.toml [tool.ruff]`, `.editorconfig`
- **Fallback si rien** : **fichier non produit** (un projet sans conventions formalisées n'a rien à documenter ici — le skill ne réinvente pas les règles)
- **Toujours produit** : non

### `docs/reference/decisions/decision-NNN-slug.md` (fiches de décision)
- **Sources principales** : `DECISIONS.md` (format LIFO — dernière décision en haut), `docs/adr/` s'il existe déjà (format Nygard classique), ou mentions `D-[scope]-[num]` dans les sessions
- **Solution de secours si rien** : **dossier de décisions vide**, signalé dans le rapport avec recommandation "adopter un fichier DECISIONS.md à la racine pour tracer les décisions techniques structurantes"
- **Toujours produit** : non

### `docs/how-to/[slug]-guide.md`
- **Sources principales** : `features/[slug].md` + `features/[slug]-spec.md`
- **Sources secondaires** : si pas de dossier features, on peut produire un guide par route Next.js / endpoint REST détecté — à condition que le route ait un nom parlant
- **Fallback si rien** : **aucun how-to produit**
- **Toujours produit** : non

### `docs/explanation/architecture.md`
- **Sources principales** : config projet, arbo `src/`, manifeste stack, dossiers clés détectés (`api/`, `lib/`, `components/`, etc.)
- **Fallback si rien** : description minimale basée sur la stack
- **Toujours produit** : oui (version dégradée si projet nu)

### `docs/explanation/agents-architecture.md`
- **Sources principales** : `.claude/agents/*.md` + `CLAUDE.md` section routage
- **Fallback si rien** : **fichier NON produit**. Un projet sans agents n'a pas d'architecture d'agents à documenter.
- **Toujours produit** : non

### `docs/explanation/agent-retex.md`
- **Sources principales** : `.claude/agents/*.md`, `RETOUR-EXPERIENCE-AGENTS.md`, sessions qui mentionnent des ajustements d'agents
- **Fallback si rien** : **fichier NON produit**
- **Toujours produit** : non

### `docs/explanation/[domain]-logic.md`
- **Sources principales** : mentions récurrentes d'un domaine métier dans les specs features (ex : "facturation", "timesheet", "billing")
- **Fallback si rien** : **fichier NON produit**
- **Toujours produit** : non

### `docs/onboarding/README-dev.md`
- **Sources principales** : `package.json` (scripts), `.env.example`, `README.md` section installation, `CONVENTIONS.md`, variables d'environnement détectées
- **Fallback si rien** : onboarding minimal basé sur la stack détectée (ex : "node → `npm install` et `npm run dev`")
- **Toujours produit** : oui (même dégradé, utile pour un nouveau dev)

---

## Modes de fonctionnement selon ce qui existe

### Mode « bootstrap minimal » (projet nu)

Déclenché quand la détection renvoie : stack détectée mais aucune source de doc ni agents ni features.

**Fichiers produits (5 max)** :
1. `docs/README.md` (reformulé depuis l'existant ou créé à partir du nom du projet)
2. `docs/OVERVIEW.md` (vue basée uniquement sur la stack)
3. `docs/explanation/architecture.md` (description de l'arbo `src/`)
4. `docs/onboarding/README-dev.md` (commandes standard de la stack)
5. `project-config.md` dans le skill (squelette à compléter)

Dans le rapport final, le skill liste **les fichiers qu'il aurait pu produire si certaines sources existaient**, avec une recommandation par fichier manquant. Exemple :

> Pour activer `FEATURES.md`, crée un dossier `features/` avec un fichier `.md` par feature, ou adopte des commits conventionnels (`feat:`, `fix:`). Le skill lira ces sources au prochain run.

### Mode « standard » (projet normal avec specs et conventions)

Déclenché quand il y a au moins : `package.json` + `README.md` + soit `features/`, soit `CHANGELOG.md` structuré, soit un dossier `docs/`.

Produit la plupart des fichiers de la matrice sauf ceux liés aux agents (pas de `.claude/agents/`) et ceux qui manquent de source spécifique.

### Mode « enrichi » (projet mature)

Tous les signaux sont présents : agents, sessions, features, décisions, rôles, RLS, retex. Le skill produit l'intégralité de l'arbo décrite dans `SKILL.md`.

---

## Gestion du drift entre runs

Entre deux runs du skill sur le même projet, les sources peuvent **apparaître** ou **disparaître**. Exemples :

| Changement détecté | Action du skill |
|---|---|
| `.claude/agents/` absente → maintenant présente avec 3 agents | Rapport de drift : "Nouvelle source détectée : agents. Je peux créer `explanation/agents-architecture.md` maintenant." En mode `generate`, le fichier est créé automatiquement. En mode `update`, une confirmation humaine est demandée. |
| `features/` présente → maintenant absente (déplacée, supprimée) | Rapport de drift : "Source disparue : features. Les `how-to/*.md` existants sont conservés (append-only). Aucun nouveau how-to ne sera créé tant que le dossier n'est pas restauré." |
| Nouvelle migration détectée depuis le dernier run | Mode `schema` suggéré automatiquement : "Nouvelle migration `YYYY-MM-DD_foo.sql` détectée. Veux-tu rafraîchir `reference/schema.md` ?" |
| Nouvel agent ajouté à `.claude/agents/` depuis le dernier run | Le prochain `update` ou `generate` ajoute le bloc correspondant dans `agents-architecture.md` et une ligne dans `agent-retex.md`. |
| Agent supprimé de `.claude/agents/` | Rapport de drift : "Agent `X` supprimé. Son bloc dans `agents-architecture.md` est marqué `(retiré le YYYY-MM-DD)`. Append-only préservé — le bloc n'est pas effacé." |

Le drift est détecté par le script `scripts/detect_sources.py` qui compare la détection actuelle à la `project-config.md` précédente. Le rapport JSON contient une clé `drift` avec deux listes : `appeared` et `disappeared`.

---

## Principe de non-régression

Une règle forte : **le skill ne supprime jamais un fichier de sortie qu'il a produit précédemment**, même si la source originale a disparu. Les fichiers historiques sont soit :
- conservés tels quels (mode *ajout seul* strict sur retours d'expérience, fiches de décision, et colonne "Terminées" de FEATURES.md)
- marqués comme "retiré le YYYY-MM-DD" dans leur en-tête

C'est cohérent avec le principe général : la doc est une mémoire, pas un miroir en temps réel du code.
