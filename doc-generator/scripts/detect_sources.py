#!/usr/bin/env python3
"""
detect_sources.py — Deterministic source detection for the doc-generator skill.

Run this script from the project root. It scans the repository for documentation
sources, stack signals, and existing agent definitions, then emits a JSON payload
the skill can consume to decide what to read, what to delegate, and what to skip.

Usage:
    python3 detect_sources.py [--root PATH] [--previous-config PATH]

If --previous-config points to an existing project-config.md, a drift section is
added showing sources that appeared or disappeared since the last run.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Configuration: what to look for
# ---------------------------------------------------------------------------

STACK_MANIFESTS = {
    "node": ["package.json"],
    "python": ["pyproject.toml", "requirements.txt", "setup.py"],
    "go": ["go.mod"],
    "rust": ["Cargo.toml"],
    "java": ["pom.xml", "build.gradle", "build.gradle.kts"],
    "ruby": ["Gemfile"],
    "php": ["composer.json"],
    "dotnet": ["*.csproj", "*.sln"],
}

FRAMEWORK_SIGNALS = {
    "next.js": ["next.config.js", "next.config.mjs", "next.config.ts"],
    "nuxt": ["nuxt.config.js", "nuxt.config.ts"],
    "vite": ["vite.config.js", "vite.config.ts"],
    "astro": ["astro.config.mjs", "astro.config.ts"],
    "sveltekit": ["svelte.config.js"],
    "remix": ["remix.config.js"],
    "django": ["manage.py"],
    "flask": ["app.py", "wsgi.py"],
    "fastapi": ["main.py"],
}

DB_MIGRATION_DIRS = {
    "supabase": "supabase/migrations",
    "prisma": "prisma/migrations",
    "drizzle": "drizzle",
    "alembic": "alembic/versions",
    "flyway": "db/migration",
    "rails": "db/migrate",
    "knex": "migrations",
}

ORM_SCHEMAS = {
    "prisma": "prisma/schema.prisma",
    "drizzle": "drizzle/schema.ts",
    "typeorm": "src/entities",
}

DEPLOY_SIGNALS = {
    "cloudflare": ["wrangler.toml", "wrangler.jsonc"],
    "vercel": ["vercel.json"],
    "netlify": ["netlify.toml"],
    "github-actions": [".github/workflows"],
    "docker": ["Dockerfile", "docker-compose.yml"],
    "fly.io": ["fly.toml"],
}

DOC_SOURCES_COMMON = {
    "readme": ["README.md", "readme.md"],
    "changelog": ["CHANGELOG.md", "CHANGES.md", "HISTORY.md"],
    "contributing": ["CONTRIBUTING.md"],
    "license": ["LICENSE", "LICENSE.md"],
    "conventions": ["CONVENTIONS.md"],
    "decisions": ["DECISIONS.md", "docs/adr"],
    "claude_md": ["CLAUDE.md"],
    "agents_dir": [".claude/agents"],
    "skills_dir": [".claude/skills"],
    "sessions_dir": ["sessions"],
    "features_dir": ["features", "specs", "docs/features"],
    "retex": ["RETOUR-EXPERIENCE-AGENTS.md", "LESSONS.md"],
    "project_state": ["project-state.md", "STATUS.md"],
    "todo": ["TODO.md"],
}


@dataclass
class DetectedSource:
    key: str
    path: str | None
    present: bool
    kind: str  # "file" or "dir"
    size_bytes: int | None = None
    file_count: int | None = None
    notes: str | None = None


@dataclass
class DetectionReport:
    project_root: str
    project_name: str
    stack: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    db_migrations: dict[str, Any] = field(default_factory=dict)
    orm_schemas: dict[str, str] = field(default_factory=dict)
    deploy_targets: list[str] = field(default_factory=list)
    sources: list[DetectedSource] = field(default_factory=list)
    agents_detected: list[dict[str, Any]] = field(default_factory=list)
    features_detected: list[str] = field(default_factory=list)
    drift: dict[str, list[str]] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _exists(root: Path, rel: str) -> Path | None:
    """Return the resolved path if it exists (supports glob)."""
    if any(ch in rel for ch in ["*", "?", "["]):
        matches = list(root.glob(rel))
        return matches[0] if matches else None
    p = root / rel
    return p if p.exists() else None


def _iter_glob(root: Path, rel: str) -> list[Path]:
    return sorted(root.glob(rel))


def _first_existing(root: Path, candidates: list[str]) -> tuple[str | None, Path | None]:
    for c in candidates:
        p = _exists(root, c)
        if p is not None:
            return c, p
    return None, None


def _count_files(dir_path: Path, pattern: str = "*") -> int:
    if not dir_path.is_dir():
        return 0
    return sum(1 for _ in dir_path.glob(pattern) if _.is_file())


def _read_frontmatter_model(md_path: Path) -> str | None:
    """Extract `model:` field from a YAML frontmatter block if present."""
    try:
        text = md_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None
    m = re.search(r"^---\s*\n(.*?)\n---", text, re.DOTALL | re.MULTILINE)
    if not m:
        return None
    block = m.group(1)
    for line in block.splitlines():
        if line.strip().startswith("model:"):
            return line.split(":", 1)[1].strip()
    return None


def _project_name(root: Path) -> str:
    pkg = root / "package.json"
    if pkg.exists():
        try:
            data = json.loads(pkg.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "name" in data:
                return str(data["name"])
        except Exception:
            pass
    pyproj = root / "pyproject.toml"
    if pyproj.exists():
        try:
            text = pyproj.read_text(encoding="utf-8")
            m = re.search(r'^\s*name\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE)
            if m:
                return m.group(1)
        except Exception:
            pass
    return root.name


# ---------------------------------------------------------------------------
# Detection phases
# ---------------------------------------------------------------------------

def detect_stack(root: Path, report: DetectionReport) -> None:
    for lang, manifests in STACK_MANIFESTS.items():
        for m in manifests:
            if _exists(root, m):
                report.stack.append(lang)
                break


def detect_frameworks(root: Path, report: DetectionReport) -> None:
    for fw, signals in FRAMEWORK_SIGNALS.items():
        for s in signals:
            if _exists(root, s):
                report.frameworks.append(fw)
                break


def detect_db(root: Path, report: DetectionReport) -> None:
    for flavor, rel in DB_MIGRATION_DIRS.items():
        p = _exists(root, rel)
        if p is not None and p.is_dir():
            migrations = sorted([f.name for f in p.iterdir() if f.is_file()])
            if migrations:
                report.db_migrations[flavor] = {
                    "dir": rel,
                    "count": len(migrations),
                    "latest": migrations[-1] if migrations else None,
                }
    for orm, schema in ORM_SCHEMAS.items():
        p = _exists(root, schema)
        if p is not None:
            report.orm_schemas[orm] = schema


def detect_deploy(root: Path, report: DetectionReport) -> None:
    for target, signals in DEPLOY_SIGNALS.items():
        for s in signals:
            if _exists(root, s):
                report.deploy_targets.append(target)
                break


def detect_doc_sources(root: Path, report: DetectionReport) -> None:
    for key, candidates in DOC_SOURCES_COMMON.items():
        matched, path = _first_existing(root, candidates)
        if path is None:
            report.sources.append(DetectedSource(
                key=key, path=None, present=False, kind="unknown",
                notes=f"checked: {', '.join(candidates)}",
            ))
            continue
        if path.is_dir():
            file_count = _count_files(path)
            report.sources.append(DetectedSource(
                key=key, path=matched, present=True, kind="dir",
                file_count=file_count,
            ))
        else:
            report.sources.append(DetectedSource(
                key=key, path=matched, present=True, kind="file",
                size_bytes=path.stat().st_size,
            ))


def detect_agents(root: Path, report: DetectionReport) -> None:
    agents_dir = root / ".claude" / "agents"
    if not agents_dir.is_dir():
        return
    for agent_file in sorted(agents_dir.glob("*.md")):
        name = agent_file.stem
        model = _read_frontmatter_model(agent_file)
        report.agents_detected.append({
            "name": name,
            "path": str(agent_file.relative_to(root)),
            "model_frontmatter": model,
            "size_bytes": agent_file.stat().st_size,
        })


def detect_features(root: Path, report: DetectionReport) -> None:
    features_dir = None
    for candidate in ["features", "specs", "docs/features"]:
        p = _exists(root, candidate)
        if p is not None and p.is_dir():
            features_dir = p
            break
    if features_dir is None:
        return
    slugs: set[str] = set()
    for f in features_dir.glob("*.md"):
        name = f.stem
        for suffix in ("-spec", "-plan"):
            if name.endswith(suffix):
                name = name[: -len(suffix)]
                break
        slugs.add(name)
    report.features_detected = sorted(slugs)


def compute_drift(report: DetectionReport, previous_config: Path | None) -> None:
    if previous_config is None or not previous_config.exists():
        return
    try:
        prev_text = previous_config.read_text(encoding="utf-8", errors="replace")
    except Exception:
        report.warnings.append(f"Could not read previous config: {previous_config}")
        return
    current_keys = {s.key for s in report.sources if s.present}
    # Very permissive drift detection: we just look for known section headers
    appeared: list[str] = []
    disappeared: list[str] = []
    for src in report.sources:
        mention = src.key in prev_text.lower() or (src.path and src.path in prev_text)
        if src.present and not mention:
            appeared.append(src.key)
        if (not src.present) and mention:
            disappeared.append(src.key)
    if appeared:
        report.drift["appeared"] = appeared
    if disappeared:
        report.drift["disappeared"] = disappeared


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def run(root: Path, previous_config: Path | None) -> DetectionReport:
    report = DetectionReport(
        project_root=str(root.resolve()),
        project_name=_project_name(root),
    )
    detect_stack(root, report)
    detect_frameworks(root, report)
    detect_db(root, report)
    detect_deploy(root, report)
    detect_doc_sources(root, report)
    detect_agents(root, report)
    detect_features(root, report)
    compute_drift(report, previous_config)

    if not report.stack:
        report.warnings.append(
            "No known language manifest detected. Skill will run in minimal mode."
        )
    if not report.sources or all(not s.present for s in report.sources):
        report.warnings.append(
            "No documentation sources detected. Only stack-based bootstrap is possible."
        )
    if not report.agents_detected:
        report.warnings.append(
            "No .claude/agents/*.md detected. Skipping explanation/agents-architecture.md "
            "and explanation/agent-retex.md from output."
        )
    return report


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Project root (default: cwd)")
    parser.add_argument("--previous-config", default=None, help="Path to previous project-config.md")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"Error: root {root} is not a directory", file=sys.stderr)
        return 2
    previous_config = Path(args.previous_config).resolve() if args.previous_config else None

    report = run(root, previous_config)
    payload = asdict(report)
    json.dump(payload, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
