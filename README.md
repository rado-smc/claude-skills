# Claude Skills

Skills for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) — Anthropic's CLI for Claude.

## Available Skills

### doc-generator

Generates and maintains living technical documentation from your project's real sources: code, feature specs, DB migrations, agent definitions, decisions, and session logs.

**Key features:**
- **Universal and portable** — works on any project (Node, Python, Go, Rust, etc.) by auto-detecting what exists
- **Graceful degradation** — produces a minimal bootstrap (4-5 files) on a bare project, enriches progressively as sources appear
- **Non-tech friendly** — output is written in simple language with technical terms always explained in parentheses
- **4 modes**: `generate` (full), `update [slug]` (after feature closure), `schema` (after DB migration), `bundle` (single concatenated document)
- **Drift detection** — tracks sources that appear or disappear between runs and proposes updates accordingly
- **Smart delegation** — uses Haiku/Sonnet subagents for heavy scanning, keeps Opus for synthesis and writing
- **Source-driven strict** — never invents information; signals gaps in the final report instead

**Install:**
```bash
# Copy into your project's .claude/skills/ directory
cp -r doc-generator /path/to/your/project/.claude/skills/

# Or clone this repo and symlink
git clone https://github.com/rado-smc/claude-skills.git
ln -s /path/to/claude-skills/doc-generator /path/to/your/project/.claude/skills/doc-generator
```

**First run:**
Just ask Claude Code: "generate the docs for this project" or invoke the skill directly. On the first run, the skill will:
1. Run `scripts/detect_sources.py` to scan your repo
2. Ask you 3-5 questions about roles, entities, and glossary
3. Create a `project-config.md` tailored to your project
4. Generate the documentation

**Documentation:** See [doc-generator/SKILL.md](doc-generator/SKILL.md) for full instructions.

## License

MIT
