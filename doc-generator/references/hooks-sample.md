# hooks-sample.md — Activer les triggers automatiques (optionnel)

Ce fichier explique comment câbler le skill `doc-generator` au harnais Claude Code pour que les triggers T1/T2/T3 se remplissent **tout seuls** quand Claude édite un fichier de backlog, une migration ou une décision.

**C'est 100 % optionnel.** Le skill fonctionne sans hook — il se contente alors d'attendre une invocation explicite (humaine ou par le script `detect_triggers.py` lancé à la demande). Le hook n'est qu'un accélérateur.

---

## Ce que fait le hook

Chaque fois que Claude Code utilise `Write`, `Edit`, `MultiEdit` ou `NotebookEdit`, le harnais appelle `scripts/trigger_hook.py`. Le script :

1. Reçoit le payload de l'appel d'outil sur stdin (JSON)
2. Extrait le chemin du fichier édité
3. Le compare aux globs déclarés dans `project-config.md` (section *Triggers*)
4. Si le fichier tombe dans une catégorie suivie (backlog, migration, décision), le script ajoute **une ligne** au fichier `.doc-pending` à la racine du repo. Sinon il sort silencieusement.

Au prochain run du skill, `detect_triggers.py` voit `.doc-pending`, le skill sait exactement quoi régénérer, puis il supprime le marker en fin de run.

**Aucune requête réseau, aucune commande externe, aucun effet sur les fichiers du projet au-delà de `.doc-pending`**.

---

## Option A — installation assistée (recommandée)

Depuis la racine de votre projet :

```bash
python3 .claude/skills/doc-generator/scripts/install_triggers_hook.py
```

Le script :
- Détecte votre OS et l'interpréteur Python disponible
- Charge `.claude/settings.json` (ou le crée s'il n'existe pas)
- Affiche le **diff unifié** exact qu'il veut appliquer
- Demande une confirmation `[y/N]`
- En cas de `y`, écrit le nouveau `settings.json` et un log d'installation dans `.claude/skills/doc-generator/.hook-installed.json`

Pour désinstaller proprement :

```bash
python3 .claude/skills/doc-generator/scripts/uninstall_triggers_hook.py
```

Le script lit le log, retire *uniquement* l'entrée marquée par `doc-generator/trigger_hook`, et laisse vos autres hooks intacts.

---

## Option B — installation manuelle

Si vous préférez éditer `settings.json` à la main, ajoutez cette entrée sous `hooks.PostToolUse` :

```jsonc
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit|NotebookEdit",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /chemin/absolu/vers/.claude/skills/doc-generator/scripts/trigger_hook.py",
            "timeout": 5,
            "_source": "doc-generator/trigger_hook"
          }
        ]
      }
    ]
  }
}
```

**Notes** :
- Remplacez `python3` par `python` ou `py` si `python3` n'est pas dans votre `PATH` (fréquent sur Windows).
- Le chemin doit être **absolu**. Les hooks tournent avec la *cwd* du harnais, pas celle du projet.
- Le champ `_source` sert uniquement au désinstalleur pour identifier l'entrée plus tard — vous pouvez l'omettre si vous installez à la main, mais dans ce cas vous devrez aussi retirer l'entrée à la main.
- `timeout: 5` est large ; le script finit en général en moins de 50 ms.

### Sur Windows

L'emplacement de `settings.json` reste `.claude/settings.json` à la racine du repo (identique aux trois OS). Dans la chaîne `command`, doublez les backslashes dans le JSON ou (plus simple) utilisez `/` — les deux fonctionnent :

```json
"command": "python C:/chemin/vers/.claude/skills/doc-generator/scripts/trigger_hook.py"
```

---

## Auditer ce qui sera exécuté

Avant d'activer le hook, vous pouvez lire le script en 150 lignes :

```bash
cat .claude/skills/doc-generator/scripts/trigger_hook.py
```

Il n'ouvre aucune socket, ne lance aucun sous-processus, ne touche à aucun fichier en dehors de `.doc-pending`. En cas d'erreur, il avale silencieusement — **il ne bloque jamais votre tool call**.

---

## Pourquoi l'installation n'est pas automatique

Un skill qui modifie silencieusement `settings.json` viole le principe de non-surprise : `settings.json` fait tourner des commandes shell sur votre machine, et vous seul décidez ce qui s'y trouve. Le script d'installation vous montre le diff, attend votre accord, et trace ce qu'il a fait pour pouvoir le retirer proprement. C'est le compromis correct entre confort et contrôle.

---

## Alternative aux hooks : le cron ou la CI

Si vous ne voulez pas que Claude Code écrive quoi que ce soit sur votre machine en dehors des fichiers explicites, vous pouvez aussi :

- **Cron** local : toutes les 10 min, lancer `detect_triggers.py`, et invoquer le skill si `triggered` est non vide.
- **CI** : ajouter un job qui tourne à chaque merge sur `main` et écrit le marker `.doc-pending`.
- **Git hook** : un `.git/hooks/post-merge` qui écrit `.doc-pending` quand `git log -1` matche certaines conventions de commit.

Toutes ces voies convergent vers le même marker — le skill reste indifférent à la source.
