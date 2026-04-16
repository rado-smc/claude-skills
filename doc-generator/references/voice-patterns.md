# voice-patterns.md — Patterns avancés (inspirés Stripe)

Ce fichier complète `tone-guide.md` avec les patterns détaillés. Lis-le après le tone-guide, avant de rédiger des `how-to/*` ou des sections de `reference/*` qui documentent des statuts ou des cycles de vie.

---

## Anatomie des instructions numérotées

Chaque étape suit la même grammaire :

```
N. [Verbe impératif] + [objet].
```

Variante avec résultat visible :
```
N. [Verbe impératif] + [objet]. [Résultat immédiatement observable].
```

Variante optionnelle :
```
(Optionnel) [Verbe impératif] + [objet].
```

**Impératif vs optionnel** : ne jamais mélanger dans la même liste numérotée. Les options vont après la liste, préfixées par "(Optionnel)".

❌ `1. Cliquez sur Créer. 2. Vous pouvez ajouter une note. 3. Renseignez le montant.`
✅ `1. Cliquez sur Créer. 2. Renseignez le montant. (Optionnel) Ajoutez une note.`

---

## Documenter les statuts et cycles de vie

### Tableau de statuts — toujours 3 colonnes

| Statut | Description | Actions possibles |
|---|---|---|
| Brouillon | L'arrêté n'est pas encore finalisé. | Modifier · Supprimer |
| Confirmé | Verrouillé. État définitif. | Exporter · Consulter |
| Exporté | Archivé en PDF. | Télécharger · Dupliquer |

La description est **une phrase**. Les actions sont des verbes courts séparés par `·`.

### Transitions — 3 éléments dans cet ordre

1. Ce qui **déclenche** la transition
2. Ce qui **change**
3. Ce qui **ne change pas**

```
Quand vous confirmez un arrêté :
- Son statut passe à Confirmé.
- Il ne peut plus être modifié.
- Le client reçoit une notification par email.

Ce qui ne change pas :
- Les jours déjà saisis restent visibles.
- L'historique des modifications est conservé.
```

### États définitifs — nommer et proposer une alternative

```
Un arrêté confirmé est en état définitif — il ne peut plus être modifié.

Si vous avez commis une erreur après confirmation :
- Créez un avoir pour corriger le montant.
- Contactez l'administrateur pour les cas exceptionnels.
```

---

## Micro-patterns

### "Par défaut" en premier

Toujours indiquer le comportement par défaut avant les options.

✅ "Par défaut, un arrêté créé est en statut Brouillon. Vous pouvez le confirmer ou le supprimer."

### "Ce que ça permet" avant le "comment"

Justifier une fonctionnalité en termes de ce que l'utilisateur peut faire, pas en termes d'implémentation.

❌ "Le champ `immutable_once_confirmed` utilise un trigger Postgres."
✅ "Une fois confirmé, l'arrêté est verrouillé. Cela garantit l'intégrité des données envoyées au client."

### "Rien ne se passe automatiquement" — le dire explicitement

Ce que le système ne fait PAS est aussi important que ce qu'il fait.

✅ "Par défaut, ScaleERP ne notifie pas le client quand un brouillon est créé. La notification est envoyée uniquement à la confirmation."

### "En savoir plus" — court et ciblé

Après une mention rapide d'un concept, ajouter un lien ciblé. Jamais expansif.

✅ "En savoir plus sur [les arrêtés de facturation](../how-to/f-arrete-guide.md)."

### Contrainte technique + alternative immédiate

Quand une action est bloquée, nommer la contrainte et proposer une alternative dans la même phrase ou le paragraphe suivant.

✅ "Vous ne pouvez pas modifier un arrêté confirmé. Pour corriger une erreur : créez un avoir ou contactez l'administrateur."

---

## Voix passive — quand l'utiliser

La voix passive est **tolérée uniquement** quand le sujet est le système lui-même et l'action est automatique.

❌ (passif interdit) "L'arrêté est confirmé par l'utilisateur en cliquant sur le bouton."
✅ (passif autorisé) "Une notification est envoyée automatiquement au client."

Si l'utilisateur est l'acteur → voix active impérative.

---

## Pas de phrases de transition

Ne jamais écrire "Maintenant que vous avez fait X, passons à Y". Un titre-action suffit. La progression est implicite.

---

## Mots savants → remplacements

| Mot savant | Remplacer par |
|---|---|
| nominal | "cas normal", "déroulement sans erreur" |
| transversal | "qu'on retrouve partout" |
| canonique | "la version officielle" |
| idempotent | "qu'on peut relancer sans risque" |
| atomique | "tout-ou-rien" |
| rollback | "retour en arrière" |
| upsert | "insérer ou mettre à jour" |
| cascade | "en chaîne" |
| append-only | "mode ajout seul" |
| fallback | "solution de secours" |
| drift | "écart" |
| pipeline | "chaîne de traitement" |
| edge case | "cas limite" |
| runtime | "environnement d'exécution" |
| frontmatter | "en-tête de fichier" |
| bootstrap | "démarrage minimal" |
| cache | "mémoire rapide" |
| middleware | "intermédiaire" |
| fiche de décision (ADR) | note qui explique une décision technique et pourquoi elle a été prise |

---

## Conformité et avertissements légaux

Si une action implique des règles légales ou de conformité :

> Vérifiez les règles applicables avant de [action]. En cas de doute, consultez [expert ou processus interne].

Donner l'info disponible, identifier la limite de compétence, orienter vers le bon interlocuteur.
