# Claude Skills

Skills for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) — Anthropic's CLI for Claude.

## Available Skills

### doc-generator

Generates and maintains living technical documentation from your project's real sources: code, feature specs, DB migrations, agent definitions, decisions, and session logs.

**Key features:**
- **Universal and portable** — works on any project (Node, Python, Go, Rust, Ruby, PHP, etc.) by auto-detecting what exists
- **Graceful degradation** — produces a minimal bootstrap (4-5 files) on a bare project, enriches progressively as sources appear
- **Non-tech friendly** — output is written in simple language with technical terms always explained in parentheses
- **4 modes**: `generate` (full), `update [slug]` (after feature closure), `schema` (after DB migration), `bundle` (single concatenated document)
- **Auto-triggering** — detects 6 platform-agnostic events (backlog closure, schema change, new decision, merge to main, docs staleness, explicit marker) and proposes the right mode without needing a specific agent or orchestration pipeline
- **Drift detection** — tracks sources that appear or disappear between runs and proposes updates accordingly
- **Smart delegation** — uses Haiku/Sonnet subagents for heavy scanning, keeps Opus for synthesis and writing
- **Source-driven strict** — never invents information; signals gaps in the final report instead

**Install:**
```bash
# Clone this repo somewhere outside your project
git clone https://github.com/rado-smc/claude-skills.git ~/claude-skills

# Then either symlink the skill into your project
ln -s ~/claude-skills/doc-generator /path/to/your/project/.claude/skills/doc-generator

# Or copy it (simpler, but no automatic updates when you pull this repo)
cp -r ~/claude-skills/doc-generator /path/to/your/project/.claude/skills/
```

**First run:**
Just ask Claude Code: "generate the docs for this project" or invoke the skill directly. On the first run, the skill will:
1. Run `scripts/detect_sources.py` to scan your repo
2. Ask you 3-5 questions about roles, entities, and glossary
3. Create a `project-config.md` tailored to your project
4. Generate the documentation

**Keeping docs in sync (optional):**

The skill can detect on its own when your documentation is behind. Run the trigger detector any time:

```bash
python3 .claude/skills/doc-generator/scripts/detect_triggers.py
```

It returns a JSON telling you which of the 6 triggers (T1–T6) are active and which mode you should run. For fully hands-off syncing, you can install a Claude Code hook that watches for file edits and writes a `.doc-pending` marker the skill picks up on its next run:

```bash
python3 .claude/skills/doc-generator/scripts/install_triggers_hook.py
```

The installer shows you a diff of the change it wants to make to `.claude/settings.json`, asks for confirmation, and logs what it did so you can remove it cleanly later:

```bash
python3 .claude/skills/doc-generator/scripts/uninstall_triggers_hook.py
```

Both scripts run on macOS, Linux and Windows (Python 3.9+, standard library only). See [doc-generator/references/triggers.md](doc-generator/references/triggers.md) for the full definition of the 6 triggers, and [doc-generator/references/hooks-sample.md](doc-generator/references/hooks-sample.md) for the hook details and alternatives (cron, CI, git hooks).

**Documentation:** See [doc-generator/SKILL.md](doc-generator/SKILL.md) for full instructions.

## License

MIT
