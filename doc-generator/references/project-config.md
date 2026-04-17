# project-config.md — Format et exemple

Ce fichier décrit le format du fichier de configuration projet que le skill crée au premier run et maintient ensuite. **Ne pas confondre** avec le fichier réellement utilisé, qui vit à :

```
.claude/skills/doc-generator/project-config.md
```

Quand le skill s'exécute, il cherche ce fichier. S'il n'existe pas, il le crée en utilisant le format ci-dessous et en auto-détectant tout ce qu'il peut depuis le repo (voir SKILL.md Étape 0).

---

## Format canonique

Le fichier est en Markdown pour rester lisible à l'humain. Il contient des sections structurées que le skill parse par titres.

```markdown
# Project Config — [Nom du projet]

Dernière mise à jour : YYYY-MM-DD
Généré par doc-generator au premier run, modifiable à la main.

## Identité

- **Nom** : [nom du projet]
- **Description courte** : [une phrase — qui l'utilise, pour quoi faire]
- **Public doc** : [qui lit la doc — ex : "PO, client final, nouveaux devs"]

## Stack technique

- **Frontend** : [framework + version — ex : Next.js 14 App Router]
- **Backend / DB** : [ex : Supabase (Postgres + Auth + RLS)]
- **Styling** : [ex : Tailwind + shadcn/ui]
- **Deploy** : [ex : Cloudflare Pages — main→prod, dev→staging]
- **Langages** : [ex : TypeScript strict]

## Rôles utilisateurs

Liste les rôles qui existent dans l'app. Pour chaque rôle, une ligne : qui il est, ce qu'il peut faire globalement, et les infos qui lui sont cachées.

- **[ROLE]** : [qui] — peut : [actions] — ne voit pas : [infos confidentielles]
- ...

## Entités métier principales

Les objets "du vrai monde" manipulés par l'app. Une ligne chacun.

- **[Entité]** : [en une phrase, sans jargon]
- ...

## Confidentialités par rôle

Les règles de visibilité importantes (celles qui déclenchent des RLS, des policies, ou des masques applicatifs).

- **[Info sensible]** : visible par [rôles], masqué pour [rôles] — raison : [contexte]
- ...

## Sources à lire

Chemins relatifs depuis la racine du repo. Le skill lit ces chemins pour construire la doc.

**Convention de marquage** : si une source n'existe pas dans le projet, écris `(aucune détectée)` au lieu d'omettre la ligne. Ça permet au script `detect_sources.py` de faire le drift check au prochain run — quand une source apparaît, le skill sait qu'elle était explicitement absente avant.

- **État global** : [fichier — ex : project-state.md | ou `(aucune détectée)`]
- **Features** : [dossier + pattern — ex : features/*.md | ou `(aucune détectée)`]
- **Specs features** : [pattern — ex : features/*-spec.md | ou `(aucune détectée)`]
- **Migrations DB** : [dossier — ex : supabase/migrations/ | ou `(aucune détectée)`]
- **Conventions code** : [fichier — ex : CONVENTIONS.md | ou `(aucune détectée)`]
- **Décisions** : [fichier — ex : DECISIONS.md | ou `(aucune détectée)`]
- **Retours d'expérience agents** : [fichier — ex : RETOUR-EXPERIENCE-AGENTS.md | ou `(aucune détectée)`]
- **Sessions** : [dossier — ex : sessions/ | ou `(aucune détectée)`]
- **Types partagés** : [dossier — ex : src/types/ | ou `(aucune détectée)`]
- **Agents Claude Code** : [dossier — ex : .claude/agents/ | ou `(aucune détectée)`]

## Triggers

Cette section mappe les six déclencheurs abstraits du skill (voir `references/triggers.md`) aux chemins concrets du projet. Elle est lue par `scripts/detect_triggers.py` et `scripts/trigger_hook.py`.

**Clés attendues** (valeurs = globs relatifs au repo, séparés par virgule) :

- **Backlog** : [pattern — ex : `features/*.md`, `backlog/*.md`]
- **Migrations** : [pattern — ex : `supabase/migrations/*.sql`, `prisma/migrations/**/*.sql`]
- **Decisions** : [pattern — ex : `DECISIONS.md`, `docs/adr/*.md`]
- **Marker** : [nom de fichier — défaut : `.doc-pending`]
- **Sentinel** : [nom de fichier — défaut : `docs/.last-generation`]

Si la section est absente, `detect_triggers.py` utilise des valeurs par défaut couvrant les conventions les plus répandues (Supabase, Prisma, Drizzle, Alembic, Rails, Flyway, ADR Nygard, etc.). L'ajouter explicitement rend la détection plus fiable et évite les faux positifs sur des projets avec arborescences atypiques.

## Glossaire

Les termes métier ou techniques à expliquer en premier dans la doc. Une définition courte, compréhensible par un non-tech.

- **[Terme]** : [définition courte, 1 ligne]
- ...

## Conventions de nommage

- **Features** : [pattern — ex : f-[slug] ou f[N]-[slug]]
- **Fiches de décision** : [pattern — ex : decision-NNN-slug.md]
- **Migrations** : [pattern — ex : YYYYMMDDHHMMSS_description.sql]

## Modèles des agents

Pour chaque agent, indique le modèle utilisé et pourquoi. Le skill lit cette section pour remplir le champ "Modèle utilisé" dans `explanation/agents-architecture.md`.

Règles d'auto-détection au premier run :
- Si un agent `.claude/agents/[nom].md` a un champ `model:` dans son frontmatter, le skill l'utilise directement
- Sinon, le skill lit cette section ; si l'agent n'y figure pas, il écrit "hérite du modèle principal de la session" et signale dans le rapport que ce champ est à documenter

Format :

- **[nom-agent]** : [Opus / Sonnet / Haiku] — [raison en 1 à 2 phrases, centrée sur la criticité et la nature de la tâche]

## Anomalies et règles spéciales

Tout ce qui n'entre pas dans les cases ci-dessus mais doit influencer la rédaction.

- [règle] — exemple : "Le champ `hourly_rate` est strictement confidentiel. Ne jamais l'exposer dans la doc visible par un rôle autre qu'admin ou le client concerné."
```

---

## Exemple pré-rempli — TeamBilling (projet fictif)

Voici un exemple générique pour un projet fictif nommé **TeamBilling** : une app interne qui fait du suivi du temps (timesheets) et de la facturation pour des équipes externes. Remplace chaque bloc par ton contexte réel.

```markdown
# Project Config — TeamBilling

Dernière mise à jour : YYYY-MM-DD
Généré par doc-generator au premier run, modifiable à la main.

## Identité

- **Nom** : TeamBilling
- **Description courte** : app interne de suivi du temps et de facturation pour des équipes externes.
- **Public doc** : admin, manager, client final, nouveaux devs en onboarding.

## Stack technique

- **Frontend** : Next.js (App Router), TypeScript strict
- **Backend / DB** : Postgres + Row-Level Security
- **Styling** : Tailwind CSS
- **Deploy** : plateforme edge (main → prod, dev → staging)
- **Migrations** : fichiers SQL dans `db/migrations/` (source de vérité)

## Rôles utilisateurs

- **admin** : direction / support interne — peut tout voir et tout faire — voit les tarifs de tous les clients.
- **manager** : gestion opérationnelle — valide les timesheets, émet les factures — ne voit pas les tarifs.
- **hr-lead** : ressources humaines — droits équivalents manager + vue des absences — ne voit pas les tarifs.
- **employee** : collaborateur — saisit ses propres timesheets — ne voit ni les factures ni les tarifs.
- **customer** : client final — voit ses propres collaborateurs, ses factures, son portail — voit son propre tarif, pas ceux des autres clients.

## Entités métier principales

- **Employee** : un collaborateur qui travaille pour un ou plusieurs clients.
- **Customer** : une société cliente.
- **Assignment** : le lien entre un Employee et un Customer (qui travaille pour qui, à partir de quand).
- **hourly_rate** : le tarif journalier d'un Employee chez un Customer. Donnée confidentielle.
- **Timesheet** : la feuille de temps d'un Employee pour un mois donné chez un Customer.
- **Invoice** : une facture émise à un Customer sur la base de timesheets validées.

## Confidentialités par rôle

- **hourly_rate** : visible uniquement par admin et par le Customer concerné pour ses propres collaborateurs. Masqué pour manager, hr-lead, employee, et pour les autres Customers.
- **Factures d'un Customer** : visibles uniquement par ce Customer et les rôles internes (admin, manager, hr-lead).
- **Timesheets cross-clients** : un Customer ne voit que ses propres timesheets.

## Sources à lire

- **État global** : `project-state.md`
- **Features** : `features/*.md`
- **Specs features** : `features/*-spec.md`
- **Migrations DB** : `db/migrations/`
- **Conventions code** : `CONVENTIONS.md`
- **Décisions** : `DECISIONS.md`
- **Retours d'expérience agents** : `RETOUR-EXPERIENCE-AGENTS.md`
- **Sessions** : `sessions/`
- **Types partagés** : `src/types/`

## Glossaire

- **hourly_rate** : tarif journalier d'un collaborateur chez un client. Confidentiel.
- **Timesheet** : la feuille de temps mensuelle d'un collaborateur, qui liste les jours travaillés.
- **RLS** : Row-Level Security — mécanisme Postgres qui filtre automatiquement les lignes visibles selon qui lit la table.
- **manager** : rôle interne qui gère la facturation et les validations.
- **Assignment** : l'affectation d'un collaborateur à un client sur une période donnée.

## Conventions de nommage

- **Features** : `f-[slug]` ou `f[N]-[slug]` (ex : `f-email-invites`, `f3-reporting`)
- **Fiches de décision** : `decision-NNN-slug.md` (numérotation chronologique)
- **Migrations** : `YYYYMMDDHHMMSS_description.sql`

## Modèles des agents

- **orchestrateur** (agent principal) : **Opus** — il jongle avec tout le contexte projet et une erreur de sa part se paie en cascade sur toute la chaîne. Le coût se justifie par le risque.
- **@architect** : **Opus** — raisonnement architectural profond. Une erreur dans le plan multiplie les itérations pour tous les agents derrière.
- **@dba** : **Opus** — SQL + RLS = très haut risque (récursion, confidentialité des tarifs, intégrité référentielle). Pas de compromis.
- **@reviewer** : **Opus** — filet de sécurité à double passe (spec puis qualité) + investigation de bugs en 4 phases. Rater une régression RLS = bug en production.
- **@coder** : **Sonnet** — génération de code en suivant un plan précis. Le raisonnement architectural est déjà fait par @architect.
- **@tester** : **Sonnet** — écriture de scénarios de test structurés depuis une spec. Pas de créativité demandée.
- **@e2etester** : **Sonnet** — exécute des scénarios déjà écrits via Playwright. Pas de raisonnement, juste de l'exécution fiable.
- **@deployer** : **Sonnet** — suit un playbook strict. Pas de créativité, mais assez rigoureux pour détecter les patterns de build du pipeline CI/CD.
- **@scribe** : **Sonnet** — mémoire et édition de fichiers structurés. Pas de décision technique, risques faibles.
- **Haiku** *(renfort ponctuel)* : utilisé par d'autres agents pour des audits rapides, des sweeps de lecture, ou des recherches massives (ex : sous-agent Explore pour cartographier un dossier avant décision).

## Anomalies et règles spéciales

- Le champ `hourly_rate` est une information strictement confidentielle. Ne jamais l'exposer dans un `how-to` ou une `reference` visible par un rôle autre qu'admin ou le client concerné.
- Toutes les pages dynamiques doivent déclarer `export const runtime = 'edge'` (contrainte de la plateforme edge).
- Les migrations prod et dev partagent la même base en V1 — toute migration impacte directement la prod. À mentionner clairement dans `reference/schema.md`.
```

---

## Auto-détection au premier run

Quand le skill crée la config pour la première fois, il **exécute d'abord** le script `scripts/detect_sources.py` qui lui fournit un JSON listant ce qui existe. Ce JSON sert à pré-remplir automatiquement :

| Section | Source auto-détectée |
|---|---|
| Identité.Nom | `package.json:name` ou `pyproject.toml:name` ou nom du dossier |
| Stack | `package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, etc. |
| Frameworks | `next.config.*`, `nuxt.config.*`, `vite.config.*`, etc. |
| Déploiement | `wrangler.toml`, `vercel.json`, `netlify.toml`, `.github/workflows/` |
| Sources.Features | `features/`, `specs/`, `docs/features/` |
| Sources.Migrations | premier dossier de migrations trouvé (supabase, prisma, drizzle, alembic, rails, knex) |
| Sources.Agents | `.claude/agents/*.md` avec modèle en frontmatter si présent |
| Conventions de nommage features | analyse regex sur les fichiers existants |

Pour tout le reste (rôles, entités, confidentialités, glossaire, anomalies, modèles des agents sans frontmatter), le skill pose les questions à l'humain — maximum 5 questions au total, groupées en un seul message.

## Drift check entre runs

À chaque run, le script `detect_sources.py` est relancé avec l'argument `--previous-config` pointant vers **ce fichier** (`project-config.md`). Il compare la détection actuelle avec ce qui est marqué ici et remplit un champ `drift` dans son JSON :

- **appeared** : sources présentes maintenant mais marquées `(aucune détectée)` précédemment → déclenche la création des fichiers de sortie correspondants
- **disappeared** : sources marquées comme présentes précédemment mais absentes maintenant → déclenche le marquage "source disparue" dans les fichiers concernés (pas de suppression — principe append-only)

Quand le skill détecte un drift, il met à jour ce `project-config.md` à la fin du run pour refléter l'état réel.
