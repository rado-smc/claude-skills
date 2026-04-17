#!/usr/bin/env python3
"""
uninstall_triggers_hook.py — Remove the doc-generator trigger hook cleanly.

Reads the install log written by install_triggers_hook.py, removes the
matching entry from .claude/settings.json, shows a diff, asks for
confirmation, then writes. Works even if the install log is missing by
falling back to a marker match on the hook command string.

Usage:
    python3 uninstall_triggers_hook.py [--root PATH] [--yes]
"""

from __future__ import annotations

import argparse
import difflib
import json
import sys
from pathlib import Path


HOOK_MARKER = "doc-generator/trigger_hook"
INSTALL_LOG_REL = ".claude/skills/doc-generator/.hook-installed.json"


def load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def remove_hook(settings: dict) -> tuple[dict, int]:
    """Remove every bucket that carries the doc-generator marker. Returns the
    new settings dict and the count of removed hook entries."""
    new = json.loads(json.dumps(settings))
    post = new.get("hooks", {}).get("PostToolUse")
    if not post:
        return new, 0
    removed = 0
    kept: list[dict] = []
    for bucket in post:
        bucket_hooks = bucket.get("hooks", [])
        surviving = [
            hook for hook in bucket_hooks
            if hook.get("_source") != HOOK_MARKER
            and HOOK_MARKER not in hook.get("command", "")
        ]
        removed += len(bucket_hooks) - len(surviving)
        if surviving:
            new_bucket = dict(bucket)
            new_bucket["hooks"] = surviving
            kept.append(new_bucket)
    new["hooks"]["PostToolUse"] = kept
    if not kept:
        new["hooks"].pop("PostToolUse", None)
    if not new.get("hooks"):
        new.pop("hooks", None)
    return new, removed


def format_json(data: dict) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def show_diff(before: dict, after: dict, path: Path) -> None:
    before_text = format_json(before).splitlines(keepends=True)
    after_text = format_json(after).splitlines(keepends=True)
    diff = difflib.unified_diff(
        before_text,
        after_text,
        fromfile=f"{path} (current)",
        tofile=f"{path} (after uninstall)",
        n=3,
    )
    sys.stdout.writelines(diff)
    sys.stdout.write("\n")


def confirm(prompt: str) -> bool:
    if not sys.stdin.isatty():
        return False
    try:
        answer = input(prompt).strip().lower()
    except EOFError:
        return False
    return answer in ("y", "yes", "o", "oui")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--root", default=".", help="Repository root (default: cwd)")
    parser.add_argument("--yes", action="store_true", help="Skip the confirmation prompt")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    settings_path = root / ".claude" / "settings.json"
    log_path = root / INSTALL_LOG_REL

    current = load_json(settings_path)
    if current is None:
        sys.stdout.write(f"[uninstall] No settings.json found at {settings_path}. Nothing to do.\n")
        return 0

    proposed, removed = remove_hook(current)
    if removed == 0:
        sys.stdout.write("[uninstall] No doc-generator hook entry found. Nothing to do.\n")
        # Still clean up the log file if it lingers.
        if log_path.exists():
            try:
                log_path.unlink()
                sys.stdout.write(f"[uninstall] Removed stale install log: {log_path}\n")
            except OSError:
                pass
        return 0

    sys.stdout.write(f"Target file: {settings_path}\n")
    sys.stdout.write(f"Entries to remove: {removed}\n\n")
    show_diff(current, proposed, settings_path)

    if not args.yes and not confirm("Apply this change? [y/N] "):
        sys.stdout.write("[uninstall] Aborted. No changes written.\n")
        return 1

    settings_path.write_text(format_json(proposed), encoding="utf-8")
    if log_path.exists():
        try:
            log_path.unlink()
        except OSError:
            pass

    sys.stdout.write("\n[uninstall] Done.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
