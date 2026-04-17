# triggers.md — Les six déclencheurs du skill doc-generator

Ce fichier définit **à quel moment le skill doit se déclencher**, indépendamment du projet, de la stack, et de l'éventuel agent d'orchestration (un humain seul, un sous-agent Scribe, une pipeline CI — tous peuvent appeler le skill).

Chaque trigger est **abstrait** : il décrit un événement métier observable, pas un chemin de fichier. La traduction vers des chemins concrets vit dans `project-config.md` de chaque projet. Le script `scripts/detect_triggers.py` fait la détection ; ce document l'explique.

---

## Les six triggers

### T1 — Clôture d'un élément de backlog
Un élément suivi (feature, ticket, issue, tâche) vient de passer à un état terminal : *done, closed, shipped, livré, déployé*. Peu importe la convention : le skill reconnaît une sélection large de signaux textuels (`status: done`, `statut: livré`, `deployed_prod`, `✅`, etc.) dans les fichiers déclarés comme backlog.

**Ce que ça déclenche** : une mise à jour ciblée de la doc (tableau des features, guide how-to de l'élément clos).

**Exemples de sources par stack** :
- Suivi Markdown : `features/*.md`, `backlog/*.md`, `issues/*.md`
- Suivi via commits conventionnels : `git log --grep="closes #"` (futur)
- Suivi externe (Linear, GitHub Issues) : hors périmètre du skill — déclarer plutôt le marker T6

### T2 — Changement de schéma de données
Un fichier de migration ou de schéma ORM vient d'être créé ou modifié : nouvelle migration SQL, modification de `schema.prisma`, nouvelle classe Alembic, etc.

**Ce que ça déclenche** : mise à jour de `reference/schema.md` et éventuellement `reference/roles.md` si les règles d'accès changent.

**Exemples** :
- Supabase : `supabase/migrations/*.sql`
- Prisma : `prisma/migrations/**/*.sql`, `prisma/schema.prisma`
- Drizzle : `drizzle/**/*.sql`
- Alembic : `alembic/versions/*.py`
- Rails : `db/migrate/*.rb`
- Flyway / Liquibase : `db/migration/*.sql`
- Knex / autres : `migrations/*`

### T3 — Décision technique enregistrée
Une décision d'architecture ou de design vient d'être consignée : nouvelle entrée dans un registre `DECISIONS.md`, nouveau fichier ADR, ou fiche de décision numérotée.

**Ce que ça déclenche** : création d'une fiche dans `reference/decisions/` et mention dans `OVERVIEW.md` si la décision est structurante.

**Exemples** :
- Registre plat : `DECISIONS.md` à la racine
- Format ADR Nygard : `docs/adr/*.md`, `adr/*.md`, `docs/decisions/*.md`
- Convention maison : toute ligne `D-[scope]-[num]` dans une session

### T4 — Merge dans la branche par défaut
Un merge commit vient de tomber sur `main`, `master`, `trunk` ou le nom détecté via `git symbolic-ref refs/remotes/origin/HEAD`. En général, cela correspond à la livraison effective d'une feature.

**Ce que ça déclenche** : vérifier que la feature mergée a bien sa doc à jour (T1 couvre le fichier de suivi, T4 couvre le cas où le suivi n'existe pas mais le merge a eu lieu).

**Limites** :
- Requiert `git` accessible (le trigger s'éteint silencieusement sans)
- Dans un repo monobranche sans merge commits (rebase-only), ce trigger ne se déclenche jamais — s'appuyer alors sur T5

### T5 — Obsolescence des docs (*staleness*)
La doc générée (`docs/site.html` ou le sentinel `docs/.last-generation`) est plus ancienne que le fichier le plus récemment modifié parmi les sources suivies. C'est le filet de sécurité : même si T1-T4 ont manqué leur cible, une divergence durable entre code et doc finit par déclencher une mise à jour.

**Ce que ça déclenche** : une suggestion de régénération. Si le retard est important, le skill peut proposer `generate`. Si faible, `update`.

### T6 — Marker explicite présent
Le fichier `.doc-pending` (ou le nom choisi dans `project-config.md`) existe à la racine. Ce trigger est **délibérément ouvert** : n'importe quel système externe — un hook Claude Code, un script CI, un git hook, une commande humaine — peut écrire ce fichier pour dire *« la doc a besoin d'un coup de jeune »*.

**Format du fichier (append-only)** :
```
2026-04-17T09:12:03+00:00 | T1 | features/f-invite-email.md
2026-04-17T09:14:45+00:00 | T2 | supabase/migrations/20260417_xxx.sql
```

Chaque ligne = un horodatage ISO, le code du trigger détecté par l'émetteur, le chemin relatif du fichier source.

**Important** : le skill **supprime ce fichier** à la fin du run, pour éviter de retriggerer en boucle. Si la génération échoue, le fichier reste en place et le prochain run verra les événements.

---

## Comment les triggers se combinent

`detect_triggers.py` les évalue tous et retourne :

```json
{
  "triggered": ["T1", "T2"],
  "reasons": { "T1": "...", "T2": "..." },
  "details": { "T1": [...], "T2": [...] },
  "suggested_mode": "update"
}
```

Le champ `suggested_mode` est une recommandation, pas un verrou :

| Triggers actifs | Mode suggéré |
|---|---|
| Aucun | `none` (ne rien faire) |
| Sentinel absent + n'importe quoi | `generate` (premier run) |
| T2 uniquement | `schema` |
| T1 ou T3 ou T6 ou combinaison | `update` |
| Large combinaison inclut T4/T5 | `update` (plusieurs cibles) |

L'utilisateur (humain ou agent) décide du mode final — le script propose.

---

## Pourquoi ces six et pas d'autres

Chaque trigger répond à une question différente :
- **T1** : « qu'est-ce qui vient d'être livré ? » (*pull* : le backlog signale)
- **T2** : « qu'est-ce qui a changé côté données ? » (le socle technique bouge)
- **T3** : « quelle nouvelle raison historique vient d'être posée ? » (la mémoire du projet s'enrichit)
- **T4** : « quelle intention a été consolidée ? » (un merge = un engagement)
- **T5** : « à quel point est-ce qu'on diverge ? » (*fallback* silencieux)
- **T6** : « qui me dit explicitement d'agir ? » (*push* : un émetteur quelconque force la main)

T1 à T4 sont des signaux *poussés* par l'activité du repo. T5 est un signal *temporel* qui émerge quand les autres ont failli. T6 est l'échappatoire : tout ce qui n'entre dans aucune des catégories ci-dessus peut toujours arriver via le marker. Cette combinaison garantit qu'aucun changement substantiel ne reste invisible à la doc pendant longtemps, quel que soit le process du projet.

---

## Étendre la détection

Si vous avez un trigger métier spécifique (ex : « régénérer quand un fichier OpenAPI change »), **ne modifiez pas le skill**. Préférez l'une des approches :

1. **Marker T6** : dans votre CI ou votre git hook, écrivez une ligne dans `.doc-pending` quand votre condition est atteinte. Le skill ne connaît pas OpenAPI, mais il verra le marker.
2. **Étendre `project-config.md`** : ajoutez votre chemin dans la section `Triggers` (sous `backlog`, `migrations`, ou `decisions` selon le domaine). Le skill fera de la détection cross-catégorie sans modification.

Garder le skill mince évite qu'il devienne stack-spécifique au fil du temps.
