#!/usr/bin/env python3
"""
install_triggers_hook.py — Opt-in installer for the doc-generator trigger hook.

Merges a PostToolUse hook entry into .claude/settings.json at the repository
root. Shows a diff and asks for explicit confirmation before writing anything.

The hook runs scripts/trigger_hook.py, which writes a line to `.doc-pending`
whenever Claude Code edits a tracked source file (backlog item, migration,
decision). The doc-generator skill then reads `.doc-pending` at its next run
and knows exactly what changed.

This installer is intentionally opt-in: silently editing settings.json would
violate the skill's non-surprise guarantee. Run it yourself when you want the
automation, remove it with uninstall_triggers_hook.py when you don't.

Usage:
    python3 install_triggers_hook.py [--root PATH] [--yes]

Supported on macOS, Linux and Windows (Python 3.9+, stdlib only).
"""

from __future__ import annotations

import argparse
import difflib
import json
import platform
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


HOOK_MARKER = "doc-generator/trigger_hook"  # used to recognise our own entry
INSTALL_LOG_REL = ".claude/skills/doc-generator/.hook-installed.json"


def detect_python_command() -> str:
    """Pick an interpreter command likely to resolve on this OS.

    On Windows, `python` is usually on PATH when Python is installed from
    python.org; the `py` launcher is also common. On macOS/Linux, `python3`
    is the safe bet.
    """
    if platform.system() == "Windows":
        if shutil.which("python"):
            return "python"
        if shutil.which("py"):
            return "py"
        return "python"  # fall through; user can edit the settings file
    return shutil.which("python3") or "python3"


def build_hook_entry(python_cmd: str, trigger_script: Path) -> dict:
    """Build a PostToolUse matcher targeting Write/Edit/MultiEdit/NotebookEdit."""
    # json.dumps escapes backslashes correctly on Windows; we serialise the
    # string representation here for transparency when the user reviews the
    # diff.
    command_parts = [python_cmd, str(trigger_script)]
    # Quote paths on Windows to survive spaces in user names.
    if platform.system() == "Windows":
        quoted = " ".join(f'"{p}"' if " " in p else p for p in command_parts)
    else:
        quoted = " ".join(f'"{p}"' if " " in p else p for p in command_parts)
    return {
        "matcher": "Write|Edit|MultiEdit|NotebookEdit",
        "hooks": [
            {
                "type": "command",
                "command": quoted,
                "timeout": 5,
                "_source": HOOK_MARKER,
            }
        ],
    }


def load_settings(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(
            f"[install] Could not parse {path}: {exc}\n"
            "Please back it up and fix the JSON manually before running this installer."
        )


def already_installed(settings: dict) -> bool:
    post = settings.get("hooks", {}).get("PostToolUse", [])
    for bucket in post:
        for hook in bucket.get("hooks", []):
            if HOOK_MARKER in hook.get("command", "") or hook.get("_source") == HOOK_MARKER:
                return True
    return False


def merge_hook(settings: dict, entry: dict) -> dict:
    """Return a new settings dict with our hook entry added to PostToolUse."""
    new = json.loads(json.dumps(settings))  # deep copy via serialise/parse
    new.setdefault("hooks", {}).setdefault("PostToolUse", []).append(entry)
    return new


def format_json(data: dict) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def show_diff(before: dict, after: dict, path: Path) -> None:
    before_text = format_json(before).splitlines(keepends=True)
    after_text = format_json(after).splitlines(keepends=True)
    diff = difflib.unified_diff(
        before_text,
        after_text,
        fromfile=f"{path} (current)",
        tofile=f"{path} (after install)",
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


def write_install_log(root: Path, entry: dict) -> None:
    log_path = root / INSTALL_LOG_REL
    log_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "installed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "hook_marker": HOOK_MARKER,
        "entry": entry,
        "platform": platform.system(),
    }
    log_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--root", default=".", help="Repository root (default: cwd)")
    parser.add_argument("--yes", action="store_true", help="Skip the confirmation prompt")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    settings_path = root / ".claude" / "settings.json"
    trigger_script = (
        root / ".claude" / "skills" / "doc-generator" / "scripts" / "trigger_hook.py"
    )

    if not trigger_script.exists():
        sys.stderr.write(f"[install] trigger_hook.py not found at {trigger_script}\n")
        return 2

    python_cmd = detect_python_command()
    entry = build_hook_entry(python_cmd, trigger_script)
    current = load_settings(settings_path)

    if already_installed(current):
        sys.stdout.write(
            "[install] doc-generator hook is already installed. "
            "Run uninstall_triggers_hook.py first to replace it.\n"
        )
        return 0

    proposed = merge_hook(current, entry)

    sys.stdout.write(f"Target file: {settings_path}\n")
    sys.stdout.write(f"Python command detected: {python_cmd}\n")
    sys.stdout.write(f"Trigger script: {trigger_script}\n\n")
    sys.stdout.write("Proposed change:\n\n")
    show_diff(current, proposed, settings_path)

    if not args.yes and not confirm("Apply this change? [y/N] "):
        sys.stdout.write("[install] Aborted. No changes written.\n")
        return 1

    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(format_json(proposed), encoding="utf-8")
    write_install_log(root, entry)

    sys.stdout.write("\n[install] Done.\n")
    sys.stdout.write(
        f"  - Updated: {settings_path}\n"
        f"  - Install log: {root / INSTALL_LOG_REL}\n"
        "  - To remove: python3 .claude/skills/doc-generator/scripts/uninstall_triggers_hook.py\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
