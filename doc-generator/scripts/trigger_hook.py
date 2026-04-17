#!/usr/bin/env python3
"""
trigger_hook.py — Minimal PostToolUse hook for the doc-generator skill.

Invoked by the Claude Code harness whenever a Write/Edit/MultiEdit tool call
completes. Reads the tool payload from stdin, checks whether the edited file
matches a tracked source (backlog, migrations, decisions), and appends one
line to the marker file when it does. Stays completely silent otherwise.

The script is intentionally tiny and dependency-free: it must not block
the harness, must not raise, and must finish in well under the hook timeout.

Stdin payload (PostToolUse):
    {"tool_name": "Write", "tool_input": {"file_path": "...", ...}, ...}

Marker file format (append-only):
    2026-04-17T09:12:03+00:00 | T1 | features/f-invite-email.md
    2026-04-17T09:14:45+00:00 | T2 | supabase/migrations/20260417000001_xx.sql
"""

from __future__ import annotations

import fnmatch
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_BACKLOG_GLOBS = [
    "features/*.md",
    "backlog/*.md",
    "issues/*.md",
]
DEFAULT_MIGRATION_GLOBS = [
    "supabase/migrations/*.sql",
    "prisma/migrations/**/*.sql",
    "drizzle/**/*.sql",
    "alembic/versions/*.py",
    "db/migrate/*.rb",
    "db/migration/*.sql",
    "migrations/*",
]
DEFAULT_DECISIONS_GLOBS = [
    "DECISIONS.md",
    "docs/adr/*.md",
    "docs/decisions/*.md",
    "adr/*.md",
]
DEFAULT_MARKER = ".doc-pending"
DEFAULT_CONFIG = ".claude/skills/doc-generator/project-config.md"

TRIGGERS_HEADING = re.compile(r"^##\s+Triggers\s*$", re.MULTILINE)
NEXT_HEADING = re.compile(r"^##\s+", re.MULTILINE)
FIELD_LINE = re.compile(r"^\s*-\s*\*\*(?P<key>[^*]+)\*\*\s*:\s*(?P<value>.+?)\s*$")


def parse_config(root: Path) -> dict[str, list[str]]:
    config_path = root / DEFAULT_CONFIG
    cfg: dict[str, list[str]] = {}
    if not config_path.exists():
        return cfg
    try:
        text = config_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return cfg
    match = TRIGGERS_HEADING.search(text)
    if not match:
        return cfg
    next_match = NEXT_HEADING.search(text, pos=match.end())
    block = text[match.end(): next_match.start() if next_match else len(text)]
    for raw in block.splitlines():
        line_match = FIELD_LINE.match(raw)
        if not line_match:
            continue
        key = line_match.group("key").strip().lower()
        items = [v.strip().strip("`") for v in line_match.group("value").split(",") if v.strip()]
        if key in ("backlog", "features"):
            cfg["backlog"] = items
        elif key in ("migrations", "schema"):
            cfg["migrations"] = items
        elif key in ("decisions", "adr"):
            cfg["decisions"] = items
        elif key in ("marker", "marker file"):
            cfg["marker"] = items
    return cfg


def match_any(relpath: str, globs: list[str]) -> bool:
    normalized = relpath.replace(os.sep, "/")
    for pattern in globs:
        if fnmatch.fnmatch(normalized, pattern):
            return True
    return False


def classify(relpath: str, cfg: dict[str, list[str]]) -> str | None:
    """Return the trigger code (T1/T2/T3) matching the file, or None."""
    backlog = cfg.get("backlog") or DEFAULT_BACKLOG_GLOBS
    migrations = cfg.get("migrations") or DEFAULT_MIGRATION_GLOBS
    decisions = cfg.get("decisions") or DEFAULT_DECISIONS_GLOBS
    if match_any(relpath, migrations):
        return "T2"
    if match_any(relpath, decisions):
        return "T3"
    if match_any(relpath, backlog):
        return "T1"
    return None


def find_repo_root(start: Path) -> Path:
    """Walk up to find a .git directory; fall back to `start` otherwise."""
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return current


def read_stdin_payload() -> dict:
    try:
        raw = sys.stdin.read()
    except Exception:
        return {}
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def extract_file_path(payload: dict) -> str | None:
    tool_input = payload.get("tool_input") or {}
    for key in ("file_path", "path", "notebook_path"):
        value = tool_input.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def main() -> int:
    payload = read_stdin_payload()
    file_path = extract_file_path(payload)
    if not file_path:
        return 0  # nothing to classify, stay silent

    root = find_repo_root(Path.cwd())
    try:
        rel = Path(file_path).resolve().relative_to(root)
    except ValueError:
        # File lives outside the repo (e.g. /tmp, user config). Ignore.
        return 0

    cfg = parse_config(root)
    trigger_code = classify(str(rel), cfg)
    if trigger_code is None:
        return 0

    marker_rel = (cfg.get("marker") or [DEFAULT_MARKER])[0]
    marker_path = root / marker_rel
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    line = f"{timestamp} | {trigger_code} | {rel.as_posix()}\n"

    try:
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        with marker_path.open("a", encoding="utf-8") as handle:
            handle.write(line)
    except OSError:
        # We must never break the user's tool call — swallow write errors.
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
