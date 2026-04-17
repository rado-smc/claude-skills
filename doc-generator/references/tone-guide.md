# tone-guide.md — Voix et ton de la documentation (inspiré Stripe)

Lis ce fichier **avant de rédiger le premier fichier de chaque session**. Il définit le ton, la structure et le vocabulaire de toute la documentation produite. Pour les patterns avancés (statuts, micro-patterns, anatomie des phrases), consulte `voice-patterns.md`.

---

## Règle 0 — Français correct obligatoire

Tous les accents, cédilles et trémas doivent être présents. Un fichier sans accents est défectueux.

❌ `Derniere mise a jour` · `Deploye` · `Role` · `Cloturee` · `Securite`
✅ `Dernière mise à jour` · `Déployé` · `Rôle` · `Clôturée` · `Sécurité`

Exceptions : noms de variables, chemins de fichiers et blocs de code restent en ASCII.

---

## Règle 1 — Une phrase = une information

Jamais deux concepts dans la même phrase. Si une phrase contient deux verbes d'action distincts, coupe-la en deux.

❌ "Confirmez l'arrêté, ce qui le verrouille et envoie une notification au client."
✅ "Confirmez l'arrêté. Il est verrouillé et le client reçoit une notification."

**Longueurs cibles** : titre de section 2-4 mots · instruction numérotée 8-14 mots · phrase d'intro de section 12-18 mots · phrase explicative 15-22 mots max.

---

## Règle 2 — Le titre de section = une action

Titre toujours avec un verbe. Jamais un sujet ou un nom abstrait.

❌ "Gestion des arrêtés" · "Cycle de facturation"
✅ "Créer un arrêté" · "Confirmer un arrêté" · "Exporter un arrêté"

---

## Règle 3 — La première phrase dit ce que ça fait et pour qui

Chaque section ouvre avec une phrase qui donne le contexte + l'audience en une ligne. Le lecteur sait en 5 secondes si la section le concerne.

✅ "Créez et gérez les arrêtés de facturation pour vos clients."
❌ "Cette section décrit le fonctionnement du module de facturation."

---

## Règle 4 — Les définitions sont intégrées, jamais renvoyées

Quand un terme apparaît pour la première fois, définis-le entre parenthèses sur place. Jamais "voir glossaire" ou "défini en section X".

✅ "Confirmez l'*arrêté* (récapitulatif mensuel verrouillé une fois confirmé)."
❌ "Confirmez l'arrêté (voir Glossaire pour la définition)."

3 usages distincts des parenthèses (ne jamais mélanger) :
1. **Définition** : *arrêté* (récapitulatif mensuel verrouillé)
2. **Option** : Confirmez (ou utilisez l'API)
3. **Exemple** : choisissez une devise (par exemple, EUR)

---

## Règle 5 — Nommer les états définitifs et ce qui ne se passe pas

**États définitifs** : quand une action est irréversible, le dire explicitement.

✅ "Un arrêté confirmé est verrouillé. C'est un état définitif — il ne peut plus être modifié."

**Ce qui ne se passe pas** : documenter aussi les comportements non-automatiques.

✅ "Supprimer un brouillon ne notifie pas le client."
❌ "Supprimez le brouillon depuis la liste."

**Contrainte bloquée + alternative** : quand une action est impossible, proposer immédiatement une alternative.

✅ "Vous ne pouvez pas modifier un arrêté confirmé. Pour corriger une erreur : créez un avoir."

---

## Règle 6 — "Si X, alors Y" pour chaque exception

Lister les cas alternatifs avec une structure conditionnelle explicite. Ne jamais laisser implicite.

```
Si le paiement échoue → [action à prendre].
Si le client ne répond pas → [action à prendre].
Si l'arrêté est déjà confirmé → [action à prendre].
```

---

## Règle 7 — Tableaux dès 3 propriétés, "Par défaut" avant les options

**Tableaux > listes** quand il y a 3+ éléments avec plusieurs dimensions (statut/description/actions).

**"Par défaut"** : toujours indiquer le comportement par défaut avant de décrire les options.

✅ "Par défaut, un arrêté créé est en statut Brouillon. Vous pouvez le confirmer ou le supprimer."

---

## Règle 8 — Callouts structurés

Format fixe, phrase courte :

> **Attention** — [conséquence si ignoré]. [Alternative ou contact].

> **Note** — [info utile non bloquante].

---

## Règle 9 — Chaque audience a son ton

**Identifier l'audience cible AVANT d'écrire.** Chaque fichier cible UNE audience.

| Audience | Ton | Ce qu'on évite | Fichiers concernés |
|---|---|---|---|
| **Dev** | Dense, technique, exemples de code d'abord | Aucune prise en main inutile | `reference/*`, `explanation/architecture.md`, `onboarding/README-dev.md` |
| **Ops** (non-dev) | Orienté décision : "quand faire quoi". Conséquences explicitées. | Jargon dev, noms de tables | `how-to/*`, `FEATURES.md` |
| **Client** | Ultra-court, max 3 étapes. Rassurant sur la confidentialité. | tarifs internes, acronymes métier, jargon technique (RLS, hook, payload) | `README.md`, `OVERVIEW.md`, portail |

Si un concept doit être documenté pour deux audiences, créer deux sections séparées — jamais "pour tout le monde".

---

## Règle 10 — "Étapes suivantes" en fin de section

Terminer chaque guide par 2-3 liens concrets vers les prochaines actions logiques. Jamais de lien générique "voir la doc complète".

✅ `Étapes suivantes : [Confirmer l'arrêté](./confirmer-arrete.md) · [Exporter en PDF](./exporter.md)`

---

## Vocabulaire par audience

| Terme technique | Ops / Client | Dev |
|---|---|---|
| RLS / row-level security | "droits d'accès" | RLS (conservé) |
| migration / schema | "mise à jour de la structure" | migration (conservé) |
| deploy / push en prod | "mettre en ligne" | deploy (conservé) |
| trigger / hook | "déclencher automatiquement" | hook (conservé) |
| payload / body | "données envoyées" | payload (conservé) |
| draft / brouillon | "Brouillon" | draft (conservé) |
| confirmed / locked | "Confirmé (verrouillé)" | confirmed (conservé) |
| terminal state | "état définitif (irréversible)" | terminal state (conservé) |
| arrêté (pour le client) | "récapitulatif mensuel" | arrêté (conservé) |
| tarif interne confidentiel (pour le client) | **ne jamais mentionner** | tarif / rate (conservé, accès restreint à l'admin) |
| webhook / event | "notification automatique" | webhook (conservé) |

Le tableau complet des mots savants est dans `voice-patterns.md`.

---

## Check rapide avant validation

1. L'audience cible est identifiée ?
2. Chaque phrase contient une seule information ?
3. Les titres sont des verbes d'action ?
4. Les états définitifs sont nommés ?
5. Les termes techniques sont définis entre parenthèses à leur première apparition ?
6. Les accents sont tous présents ?

Si un point échoue, corriger avant de continuer.
