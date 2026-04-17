#!/usr/bin/env python3
"""
detect_triggers.py — Detect when the doc-generator skill should run.

Reads project-config.md (section "Triggers" if present, otherwise falls back
to common conventions), compares the repository state against the sentinel
file `docs/.last-generation`, and emits a JSON payload describing which of
the six abstract triggers are currently active.

The six triggers are intentionally platform-agnostic:

    T1  backlog item just closed / shipped / marked done
    T2  data-schema change committed
    T3  technical decision recorded
    T4  merge into the default branch
    T5  generated docs are older than the tracked sources (staleness)
    T6  explicit marker file present (.doc-pending)

Usage:
    python3 detect_triggers.py [--root PATH] [--config PATH] [--since ISO8601]

The script has zero third-party dependencies and runs on macOS, Linux and
Windows (Python 3.9+).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Defaults — used when project-config.md has no "Triggers" section.
# They reflect conventions seen across many stacks; the config file is still
# the source of truth when present.
# ---------------------------------------------------------------------------

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

DEFAULT_SENTINEL = "docs/.last-generation"
DEFAULT_MARKER = ".doc-pending"

# Substrings (case-insensitive) that, when found on a line of a backlog file
# touched since the last run, suggest the item has been closed. Intentionally
# broad: projects carry different vocabularies.
BACKLOG_CLOSURE_SIGNALS = [
    "status: done",
    "status: closed",
    "status: shipped",
    "status: deployed",
    "statut: livré",
    "statut: terminé",
    "statut: clôturé",
    "statut: déployé",
    "deployed_prod",
    "deploye_prod",
    "✅",
]


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class TriggerHit:
    code: str
    reason: str
    details: list[str] = field(default_factory=list)


@dataclass
class DetectionContext:
    root: Path
    config_path: Path | None
    since: datetime | None
    backlog_globs: list[str]
    migration_globs: list[str]
    decisions_globs: list[str]
    sentinel_path: Path
    marker_path: Path
    default_branch: str | None


# ---------------------------------------------------------------------------
# Config parsing — best-effort Markdown section reader.
# We accept either a fenced YAML-ish block under "## Triggers" or a bullet
# list under the same heading. The goal is tolerant, not strict.
# ---------------------------------------------------------------------------

TRIGGERS_HEADING = re.compile(r"^##\s+Triggers\s*$", re.MULTILINE)
NEXT_HEADING = re.compile(r"^##\s+", re.MULTILINE)
FIELD_LINE = re.compile(r"^\s*-\s*\*\*(?P<key>[^*]+)\*\*\s*:\s*(?P<value>.+?)\s*$")


def parse_triggers_section(config_text: str) -> dict[str, list[str]]:
    """Extract trigger-related globs from the Triggers section of the config.

    Returns a dict with keys `backlog`, `migrations`, `decisions`, `marker`,
    `sentinel`, each mapping to a list of strings (globs or paths). Missing
    keys fall back to defaults at call site.
    """
    out: dict[str, list[str]] = {}
    match = TRIGGERS_HEADING.search(config_text)
    if not match:
        return out

    section_start = match.end()
    next_match = NEXT_HEADING.search(config_text, pos=section_start)
    section_end = next_match.start() if next_match else len(config_text)
    block = config_text[section_start:section_end]

    for raw_line in block.splitlines():
        line_match = FIELD_LINE.match(raw_line)
        if not line_match:
            continue
        key = line_match.group("key").strip().lower()
        value = line_match.group("value").strip()
        # Values can be comma-separated or a single path. Strip backticks.
        items = [v.strip().strip("`") for v in value.split(",") if v.strip()]
        # Normalize key synonyms.
        if key in ("backlog", "backlog paths", "features"):
            out["backlog"] = items
        elif key in ("migrations", "schema", "migration paths"):
            out["migrations"] = items
        elif key in ("decisions", "adr", "decisions paths"):
            out["decisions"] = items
        elif key in ("marker", "marker file"):
            out["marker"] = items
        elif key in ("sentinel", "sentinel file", "last-generation"):
            out["sentinel"] = items
    return out


# ---------------------------------------------------------------------------
# Filesystem and git helpers
# ---------------------------------------------------------------------------

def iter_glob(root: Path, patterns: list[str]) -> list[Path]:
    """Expand a list of globs relative to root, returning existing files."""
    results: list[Path] = []
    for pattern in patterns:
        for path in root.glob(pattern):
            if path.is_file():
                results.append(path)
    return results


def run_git(root: Path, args: list[str]) -> str | None:
    """Run a git command; return stdout as text or None on failure."""
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=False,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError:
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout


def detect_default_branch(root: Path) -> str | None:
    head = run_git(root, ["symbolic-ref", "refs/remotes/origin/HEAD"])
    if head:
        # Format: refs/remotes/origin/main
        return head.strip().rsplit("/", 1)[-1]
    # Fallback: test common names
    for candidate in ("main", "master", "trunk"):
        if run_git(root, ["rev-parse", "--verify", candidate]):
            return candidate
    return None


def since_iso(ctx: DetectionContext) -> str | None:
    if ctx.since is None:
        return None
    # Git accepts ISO 8601.
    return ctx.since.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+0000")


def load_sentinel_time(sentinel: Path) -> datetime | None:
    if not sentinel.exists():
        return None
    try:
        mtime = sentinel.stat().st_mtime
    except OSError:
        return None
    return datetime.fromtimestamp(mtime, tz=timezone.utc)


# ---------------------------------------------------------------------------
# Trigger detectors
# ---------------------------------------------------------------------------

def detect_t1_backlog_closure(ctx: DetectionContext) -> TriggerHit | None:
    """T1: a backlog item was modified since the last run AND its content
    now contains a closure signal. We do not require a git diff — touching
    the file with a new closure status is enough."""
    candidates = iter_glob(ctx.root, ctx.backlog_globs)
    sentinel_ts = load_sentinel_time(ctx.sentinel_path)
    closed: list[str] = []
    for path in candidates:
        try:
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        except OSError:
            continue
        if sentinel_ts is not None and mtime <= sentinel_ts:
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="replace").lower()
        except OSError:
            continue
        if any(signal in content for signal in BACKLOG_CLOSURE_SIGNALS):
            closed.append(str(path.relative_to(ctx.root)))
    if not closed:
        return None
    return TriggerHit(
        code="T1",
        reason=f"{len(closed)} backlog item(s) show a closure signal since last doc run",
        details=closed,
    )


def detect_t2_schema_change(ctx: DetectionContext) -> TriggerHit | None:
    """T2: at least one migration/schema file is newer than the sentinel."""
    candidates = iter_glob(ctx.root, ctx.migration_globs)
    sentinel_ts = load_sentinel_time(ctx.sentinel_path)
    newer: list[str] = []
    for path in candidates:
        try:
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        except OSError:
            continue
        if sentinel_ts is None or mtime > sentinel_ts:
            newer.append(str(path.relative_to(ctx.root)))
    if not newer:
        return None
    return TriggerHit(
        code="T2",
        reason=f"{len(newer)} schema/migration file(s) newer than last doc run",
        details=sorted(newer)[-5:],  # cap at five most recent
    )


def detect_t3_decision(ctx: DetectionContext) -> TriggerHit | None:
    """T3: a decisions file is newer than the sentinel."""
    candidates = iter_glob(ctx.root, ctx.decisions_globs)
    sentinel_ts = load_sentinel_time(ctx.sentinel_path)
    touched: list[str] = []
    for path in candidates:
        try:
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        except OSError:
            continue
        if sentinel_ts is None or mtime > sentinel_ts:
            touched.append(str(path.relative_to(ctx.root)))
    if not touched:
        return None
    return TriggerHit(
        code="T3",
        reason=f"{len(touched)} decision file(s) updated since last doc run",
        details=touched,
    )


def detect_t4_merge(ctx: DetectionContext) -> TriggerHit | None:
    """T4: at least one merge commit landed on the default branch since the
    sentinel. Falls back silently if git is unavailable."""
    if ctx.default_branch is None:
        return None
    args = ["log", "--merges", "--pretty=format:%h %s", ctx.default_branch]
    since = since_iso(ctx)
    if since:
        args.append(f"--since={since}")
    out = run_git(ctx.root, args)
    if not out:
        return None
    lines = [line.strip() for line in out.splitlines() if line.strip()]
    if not lines:
        return None
    return TriggerHit(
        code="T4",
        reason=f"{len(lines)} merge commit(s) on {ctx.default_branch} since last doc run",
        details=lines[:3],
    )


def detect_t5_staleness(ctx: DetectionContext) -> TriggerHit | None:
    """T5: the sentinel is older than the most recent file among tracked
    sources (backlog + migrations + decisions). This is what catches cases
    where T1-T4 missed the event but the repo is obviously ahead of the doc.
    """
    sentinel_ts = load_sentinel_time(ctx.sentinel_path)
    if sentinel_ts is None:
        # No sentinel = skill never ran successfully. The `suggested_mode`
        # logic at the top level will recommend `generate`. Not a T5 hit.
        return None
    tracked = (
        iter_glob(ctx.root, ctx.backlog_globs)
        + iter_glob(ctx.root, ctx.migration_globs)
        + iter_glob(ctx.root, ctx.decisions_globs)
    )
    newer_count = 0
    latest: tuple[datetime, str] | None = None
    for path in tracked:
        try:
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        except OSError:
            continue
        if mtime > sentinel_ts:
            newer_count += 1
            if latest is None or mtime > latest[0]:
                latest = (mtime, str(path.relative_to(ctx.root)))
    if newer_count == 0:
        return None
    details: list[str] = []
    if latest:
        details.append(f"most recent source change: {latest[1]} at {latest[0].isoformat()}")
    return TriggerHit(
        code="T5",
        reason=f"docs staleness — {newer_count} tracked source(s) newer than last generation",
        details=details,
    )


def detect_t6_marker(ctx: DetectionContext) -> TriggerHit | None:
    """T6: the explicit marker file exists at the repo root (or wherever the
    config points). Highest-confidence trigger because something upstream
    decided to raise the flag."""
    if not ctx.marker_path.exists():
        return None
    try:
        content = ctx.marker_path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        content = ""
    reason = f"marker file present: {ctx.marker_path.relative_to(ctx.root)}"
    details = [line for line in content.splitlines() if line.strip()][:5]
    return TriggerHit(code="T6", reason=reason, details=details)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_context(args: argparse.Namespace) -> DetectionContext:
    root = Path(args.root).resolve()
    config_path = Path(args.config).resolve() if args.config else None

    # Load config text if available.
    triggers_cfg: dict[str, list[str]] = {}
    if config_path and config_path.exists():
        try:
            config_text = config_path.read_text(encoding="utf-8", errors="replace")
            triggers_cfg = parse_triggers_section(config_text)
        except OSError:
            triggers_cfg = {}

    backlog_globs = triggers_cfg.get("backlog") or DEFAULT_BACKLOG_GLOBS
    migration_globs = triggers_cfg.get("migrations") or DEFAULT_MIGRATION_GLOBS
    decisions_globs = triggers_cfg.get("decisions") or DEFAULT_DECISIONS_GLOBS
    sentinel_rel = (triggers_cfg.get("sentinel") or [DEFAULT_SENTINEL])[0]
    marker_rel = (triggers_cfg.get("marker") or [DEFAULT_MARKER])[0]

    sentinel_path = (root / sentinel_rel).resolve()
    marker_path = (root / marker_rel).resolve()

    # "since" resolution: CLI flag wins, then sentinel mtime, else None.
    since: datetime | None = None
    if args.since:
        try:
            since = datetime.fromisoformat(args.since.replace("Z", "+00:00"))
            if since.tzinfo is None:
                since = since.replace(tzinfo=timezone.utc)
        except ValueError:
            since = None
    if since is None:
        since = load_sentinel_time(sentinel_path)

    return DetectionContext(
        root=root,
        config_path=config_path,
        since=since,
        backlog_globs=backlog_globs,
        migration_globs=migration_globs,
        decisions_globs=decisions_globs,
        sentinel_path=sentinel_path,
        marker_path=marker_path,
        default_branch=detect_default_branch(root),
    )


def suggest_mode(hits: list[TriggerHit], sentinel_exists: bool) -> str:
    """Map the set of hits to a suggested skill invocation mode.

    `generate` if no sentinel exists (never ran). `schema` if only T2.
    `update` when a single backlog item closed. `update-broad` otherwise.
    `none` if no trigger fired.
    """
    if not hits:
        return "none"
    if not sentinel_exists:
        return "generate"
    codes = {h.code for h in hits}
    if codes == {"T2"}:
        return "schema"
    if codes == {"T3"}:
        return "update"
    if "T6" in codes:
        return "update"
    if "T1" in codes and len(codes) == 1:
        return "update"
    return "update"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Detect doc-generator triggers.")
    parser.add_argument("--root", default=".", help="Repository root (default: cwd)")
    parser.add_argument(
        "--config",
        default=".claude/skills/doc-generator/project-config.md",
        help="Path to project-config.md",
    )
    parser.add_argument(
        "--since",
        default=None,
        help="Override 'since' timestamp (ISO 8601). Default: sentinel mtime.",
    )
    args = parser.parse_args(argv)

    ctx = build_context(args)

    detectors = (
        detect_t1_backlog_closure,
        detect_t2_schema_change,
        detect_t3_decision,
        detect_t4_merge,
        detect_t5_staleness,
        detect_t6_marker,
    )
    hits: list[TriggerHit] = []
    for detector in detectors:
        try:
            hit = detector(ctx)
        except Exception as exc:  # detection must never crash the run
            hit = None
            sys.stderr.write(f"[detect_triggers] {detector.__name__} failed: {exc}\n")
        if hit is not None:
            hits.append(hit)

    sentinel_exists = ctx.sentinel_path.exists()
    payload = {
        "triggered": [h.code for h in hits],
        "reasons": {h.code: h.reason for h in hits},
        "details": {h.code: h.details for h in hits},
        "since": ctx.since.isoformat() if ctx.since else None,
        "sentinel": {
            "path": str(ctx.sentinel_path.relative_to(ctx.root))
                    if ctx.sentinel_path.is_relative_to(ctx.root)  # type: ignore[attr-defined]
                    else str(ctx.sentinel_path),
            "exists": sentinel_exists,
        },
        "default_branch": ctx.default_branch,
        "config_used": str(ctx.config_path.relative_to(ctx.root))
                       if ctx.config_path and ctx.config_path.is_relative_to(ctx.root)  # type: ignore[attr-defined]
                       else (str(ctx.config_path) if ctx.config_path else None),
        "suggested_mode": suggest_mode(hits, sentinel_exists),
    }

    sys.stdout.write(json.dumps(payload, indent=2, ensure_ascii=False))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
