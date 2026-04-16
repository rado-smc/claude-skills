# tone-guide.md — Règles de style pour une doc lisible par tous

Cette doc est lue par des gens qui ne codent pas : chefs de projet, clients, office managers, nouveaux arrivants. Elle est aussi lue par des devs qui ouvrent le repo pour la première fois.

Ton objectif : qu'un non-tech comprenne `README.md`, `OVERVIEW.md`, `FEATURES.md` et n'importe quel `how-to/*.md` **sans rien demander à personne**. Les fichiers `reference/*` et `explanation/architecture.md` peuvent être plus techniques, mais gardent des phrases claires.

---

## Règle 1 — Phrases courtes

Une idée par phrase. Maximum 20 mots. Si tu sens que ta phrase est longue, coupe-la en deux.

❌ "Le système de validation, qui a été mis en place lors de la feature F4 afin de garantir que les timesheets ne soient pas modifiables une fois qu'elles sont passées en statut approuvé et rattachées à une facture, utilise une combinaison de RLS Postgres et de vérifications applicatives côté serveur."

✅ "Une fois une timesheet validée et facturée, elle ne peut plus être modifiée. Cette règle est vérifiée à deux endroits : dans la base de données, et dans le code serveur. Les deux couches protègent la même règle."

---

## Règle 2 — Vocabulaire concret

Préfère les mots du quotidien quand c'est possible. Le jargon technique n'arrive que quand il est indispensable, et il est défini à sa première apparition dans le fichier.

❌ "Le middleware d'authentification intercepte la requête et populate le contexte RLS."
✅ "Avant d'afficher la page, le système vérifie qui tu es. Cette vérification sert à filtrer ce que tu as le droit de voir."

---

## Règle 3 — Définir avant d'utiliser

Si un terme technique OU un mot savant apparaît pour la **première fois** dans un fichier, définis-le en **une courte phrase entre parenthèses**, dès son apparition. Cette règle vaut aussi pour les fichiers techniques — pas seulement pour les fichiers non-tech.

Les mots à surveiller en priorité :
- Le jargon technique : RLS, JWT, RPC, RPC, middleware, hook, runtime, edge, etc.
- Les mots "savants" qu'on croit universels mais qu'un non-initié ne comprend pas : transversal, nominal, idempotent, atomique, rollback, upsert, cascade, etc.
- Les abréviations projet : TJM, OM, RH, etc. (même si elles figurent dans le glossaire, rappelle-les à la première apparition du fichier).

✅ "La feature utilise les RLS (Row-Level Security : un système qui filtre automatiquement les lignes visibles selon qui lit la table)."

✅ "Dans le cas nominal (déroulement normal sans erreur), le traitement prend 2 secondes."

✅ "Ces observations transversales (valables pour tous les agents, pas juste un seul) aident à améliorer le flow."

❌ "Le traitement est atomique." (mot savant laissé seul — un non-initié ne sait pas)
✅ "Le traitement est atomique (soit tout réussit, soit rien n'est enregistré)."

Si le terme est déjà défini dans le glossaire (`OVERVIEW.md` ou config projet), mets un lien plutôt que la définition pleine.

## Règle 3-bis — Deux mots valent mieux qu'un mot savant

Quand un mot technique peut être remplacé par deux ou trois mots simples, préfère les deux mots simples.

| Mot savant ou jargon | À remplacer par |
|---|---|
| nominal | "cas normal", "déroulement sans erreur" |
| transversal | "qu'on retrouve partout", "commun à tous" |
| canonique | "la bonne version", "la version officielle" |
| déclencheur | "ce qui fait démarrer" |
| idempotent | "qu'on peut relancer sans risque" |
| orchestration | "la mise en musique", "la coordination" |
| intrinsèque | "qui vient de l'objet lui-même" |
| agnostique | "qui fonctionne avec n'importe quel..." |
| mutualisé | "partagé entre plusieurs" |
| pertinent | "utile ici" |
| ADR (Architecture Decision Record) | "fiche de décision" (note qui explique une décision technique importante et pourquoi elle a été prise) |
| append-only | "mode *ajout seul*" (on ajoute à la fin, on n'efface jamais le passé) |
| fallback | "solution de secours" (ce que le système fait quand la première option n'est pas possible) |
| drift | "écart" (quand l'état réel ne correspond plus à ce qui était prévu) |
| pipeline | "chaîne de traitement" (les étapes qu'un élément traverse de bout en bout) |
| edge case | "cas limite" (une situation rare ou inhabituelle à laquelle il faut penser) |
| runtime | "environnement d'exécution" (le programme qui fait tourner ton code) |
| frontmatter | "en-tête de fichier" (le petit bloc tout en haut du fichier, entre `---` et `---`) |
| bootstrap | "démarrage minimal" (se lancer quand on n'a presque rien d'existant) |
| cache | "mémoire rapide" (un endroit où on garde un résultat sous la main pour ne pas le recalculer) |
| middleware | "intermédiaire" (un petit bout de code qui s'exécute avant ou après une requête) |
| atomique | "tout-ou-rien" (soit tout réussit, soit rien n'est enregistré) |
| rollback | "retour en arrière" (annuler une modification pour revenir à l'état précédent) |
| upsert | "insérer ou mettre à jour" (crée si absent, modifie si présent) |
| cascade | "en chaîne" (quand une action en déclenche d'autres automatiquement) |

---

## Règle 4 — Pas de "nous", pas de "on", pas de "je"

La doc parle de l'app et de ses comportements, pas de l'équipe qui l'a construite. Reste neutre.

❌ "Nous avons décidé de stocker les mots de passe hashés."
✅ "Les mots de passe sont stockés hashés."

❌ "On utilise Supabase pour la base de données."
✅ "La base de données est hébergée sur Supabase."

---

## Règle 5 — Actions, pas états

Décris ce que fait l'utilisateur et ce que fait le système — pas l'état interne de la machine.

❌ "Le composant Container contient un useState qui maintient l'état local du formulaire."
✅ "Quand tu remplis le formulaire, le système garde ce que tu tapes jusqu'à ce que tu cliques sur Enregistrer."

---

## Règle 6 — Exemples concrets plutôt qu'abstraits

Quand tu décris un comportement, donne un exemple réel avec des noms, des chiffres, des dates. Un exemple vaut trois phrases d'explication.

❌ "L'utilisateur peut filtrer les timesheets par période."
✅ "Exemple : Marie veut voir ses heures de mars 2026. Elle sélectionne le mois dans le filtre, et seules les timesheets de mars s'affichent."

---

## Règle 7 — Pas de futur indéfini

Dans un `how-to/*`, décris le comportement **actuel** de la feature livrée, pas ce qui viendra plus tard. Les évolutions prévues vont dans `FEATURES.md` colonne "⏳ À venir".

❌ "Plus tard, on ajoutera un export PDF."
✅ (dans `FEATURES.md`) "⏳ Export PDF des timesheets — P2"

---

## Règle 8 — Signale les pièges

Quand un comportement peut surprendre, dis-le explicitement. Mieux vaut un paragraphe "Attention" de trois lignes qu'une heure de confusion chez le lecteur.

✅ "**Attention** : une fois une facture envoyée au client, elle ne peut plus être supprimée. Seule la création d'un avoir permet de la corriger."

---

## Règle 9 — Évite les tournures passives complexes

La voix active est plus directe. La voix passive est tolérée quand elle rend la phrase plus naturelle, mais jamais enchaînée sur 2 propositions.

❌ "Une fois que la timesheet a été approuvée et qu'elle a été rattachée à une facture, elle est verrouillée."
✅ "Quand la timesheet est approuvée et facturée, elle se verrouille."

---

## Règle 10 — Ne copie jamais de code long

Un bloc de code de 30 lignes n'est pas de la doc. Extrais ce qui compte (signature, colonnes, types) et renvoie vers le fichier source.

❌ Coller 40 lignes de SQL d'une migration.
✅ "La table `timesheets` est créée par la migration `[nom-fichier.sql]`. Colonnes principales : `id`, `employee_id`, `month`, `status`, `invoice_id`."

---

## Check rapide avant de valider un fichier

Avant de passer au fichier suivant, relis ce que tu viens d'écrire et pose-toi ces trois questions :

1. Est-ce qu'un office manager qui n'a jamais ouvert VS Code comprendrait tout ?
2. Est-ce qu'il y a des phrases de plus de 25 mots ? (Si oui, coupe.)
3. Est-ce qu'il y a un terme technique qui apparaît sans avoir été défini ou lié ?

Si tu réponds "non" aux trois, le fichier est prêt. Sinon, corrige avant de continuer.
