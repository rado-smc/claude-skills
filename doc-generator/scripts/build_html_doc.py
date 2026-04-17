#!/usr/bin/env python3
"""
build_html_doc.py — Assemble Markdown docs into a single self-contained HTML site.

Usage:
    python3 .claude/skills/doc-generator/scripts/build_html_doc.py --root . --output docs/site.html

Zero external dependencies (stdlib only).
"""

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path


# ── Section mapping ──────────────────────────────────────────────────────────

FOLDER_TO_SECTION = {
    ".": "Accueil",
    "how-to": "Fonctionnalites",
    "reference": "Reference",
    "reference/decisions": "Decisions",
    "explanation": "Architecture",
    "onboarding": "Demarrer",
}

# Patterns used to assign section when folder mapping alone is not enough
FILENAME_SECTION_PATTERNS = [
    # Demarrer
    (re.compile(r"^README-dev", re.I), "Demarrer"),
    (re.compile(r"^OVERVIEW", re.I), "Demarrer"),
    # Fonctionnalites
    (re.compile(r"^FEATURES", re.I), "Fonctionnalites"),
    # Reference
    (re.compile(r"^schema", re.I), "Reference"),
    (re.compile(r"^roles", re.I), "Reference"),
    (re.compile(r"^conventions", re.I), "Reference"),
    # Architecture
    (re.compile(r"^architecture", re.I), "Architecture"),
    (re.compile(r"^agents?-architecture", re.I), "Architecture"),
    (re.compile(r"^agent-retex", re.I), "Architecture"),
    (re.compile(r"-logic$", re.I), "Architecture"),
]

# ── Section ordering (matches new sidebar structure) ─────────────────────────

SECTION_ORDER = [
    "__home__",
    "Demarrer",
    "Fonctionnalites",
    "Reference",
    "Architecture",
    "Decisions",
]

# ── Sidebar titles: slug -> clean short title ────────────────────────────────

#
# Override any of the slug -> title mappings for your project.
# If a slug is not listed here, the script derives the title from the
# first heading of the Markdown file (falling back to a humanised slug).
# Common generic entries are pre-populated; extend as your `docs/` grows.
#
SIDEBAR_TITLES = {
    "readme": "Home",
    "overview": "Vue d'ensemble",
    "features": "Liste des features",
    "onboarding-readme-dev": "Installation locale",
    # Reference
    "reference-schema": "Schéma de la base",
    "reference-roles": "Rôles et permissions",
    "reference-conventions": "Conventions de code",
    # Architecture
    "explanation-architecture": "Vue technique",
    "explanation-agents-architecture": "Équipe des agents",
    "explanation-agent-retex": "Retour d'expérience",
}

# ── Explicit ordering within sections ────────────────────────────────────────

#
# Override display order for specific slugs. Lower numbers come first
# inside their section. Any slug not listed is sorted alphabetically
# after the explicit entries of the same section.
#
SLUG_ORDER = {
    # Démarrer
    "overview": 0,
    "onboarding-readme-dev": 1,
    # Fonctionnalités
    "features": 0,
    # Référence
    "reference-schema": 0,
    "reference-roles": 1,
    "reference-conventions": 2,
    # Architecture
    "explanation-architecture": 0,
    "explanation-agents-architecture": 1,
    "explanation-agent-retex": 2,
}

# ── Home page card definitions ───────────────────────────────────────────────

HOME_POPULAR_CARDS = [
    {
        "emoji": "&#128203;",  # clipboard
        "title": "Demarrer",
        "desc": "Setup local et premiers pas",
        "target": "overview",
    },
    {
        "emoji": "&#128640;",  # rocket
        "title": "Features",
        "desc": "Ce qui est livre et en cours",
        "target": "features",
    },
    {
        "emoji": "&#128295;",  # wrench
        "title": "Reference",
        "desc": "Schema DB, roles, conventions",
        "target": "reference-schema",
    },
    {
        "emoji": "&#128101;",  # people
        "title": "Architecture",
        "desc": "Comment le systeme est construit",
        "target": "explanation-architecture",
    },
]


# ── Helpers ──────────────────────────────────────────────────────────────────

def slugify(path_str: str) -> str:
    """Derive a URL-safe slug from a relative path (without extension)."""
    stem = Path(path_str).with_suffix("").as_posix()
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", stem).strip("-").lower()
    return slug


def extract_title(content: str, filename: str) -> str:
    """Extract the first H1 from Markdown content, or fall back to filename."""
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if match:
        title = match.group(1).strip()
        # Remove trailing markdown formatting
        title = re.sub(r"\s*[#]+\s*$", "", title)
        return title
    # Fallback: humanise filename
    name = Path(filename).stem
    name = re.sub(r"[-_]", " ", name)
    return name.strip().title()


def clean_sidebar_title(doc_id: str, raw_title: str) -> str:
    """Return a clean short title for the sidebar."""
    # Check explicit mapping first
    if doc_id in SIDEBAR_TITLES:
        return SIDEBAR_TITLES[doc_id]

    # Decision files: extract part after ":"
    decision_match = re.match(r"Fiche de decision \d+\s*:\s*(.+)", raw_title, re.I)
    if decision_match:
        return decision_match.group(1).strip()

    # Remove common prefixes
    for prefix in ["Reference --", "Schema --", "Guide --", "How-to --"]:
        if raw_title.startswith(prefix):
            return raw_title[len(prefix):].strip()

    return raw_title


def determine_section(relative_path: str) -> str:
    """Determine which sidebar section a doc belongs to."""
    parts = Path(relative_path).parts
    filename_stem = Path(relative_path).stem

    # Check deepest folder match first (e.g. reference/decisions before reference)
    if len(parts) > 1:
        folder = "/".join(parts[:-1])
        if folder in FOLDER_TO_SECTION:
            return FOLDER_TO_SECTION[folder]

    # Single level folder
    if len(parts) > 1:
        parent = parts[0]
        if parent in FOLDER_TO_SECTION:
            return FOLDER_TO_SECTION[parent]

    # Filename patterns
    for pattern, section in FILENAME_SECTION_PATTERNS:
        if pattern.search(filename_stem):
            return section

    # Root-level files default to Demarrer
    if len(parts) == 1:
        return "Demarrer"

    return "Autre"


def section_sort_key(section: str) -> int:
    try:
        return SECTION_ORDER.index(section)
    except ValueError:
        return len(SECTION_ORDER)


def doc_sort_key(doc: dict) -> tuple:
    """Sort key: section order, then explicit slug order, then alphabetical."""
    sec_idx = section_sort_key(doc["section"])
    slug_prio = SLUG_ORDER.get(doc["id"], 50)
    return (sec_idx, slug_prio, doc["title"].lower())


def detect_project_name(root: Path) -> str:
    """Try to read project name from package.json, fall back to directory name."""
    pkg = root / "package.json"
    if pkg.is_file():
        try:
            data = json.loads(pkg.read_text(encoding="utf-8"))
            name = data.get("name", "")
            if name:
                return name
        except (json.JSONDecodeError, OSError):
            pass
    return root.resolve().name


# ── Home page generation ────────────────────────────────────────────────────

def generate_home_page(docs: list[dict]) -> dict:
    """Generate the __home__ doc entry with card data for the home page."""
    # Collect how-to guides for the feature grid
    guide_cards = []
    for doc in docs:
        if doc["section"] == "Fonctionnalites" and doc["id"] != "features":
            guide_cards.append({
                "title": doc["sidebarTitle"],
                "target": doc["id"],
            })

    home_data = {
        "popularCards": HOME_POPULAR_CARDS,
        "guideCards": guide_cards,
    }

    return {
        "id": "__home__",
        "title": "Accueil",
        "section": "__home__",
        "sidebarTitle": "Accueil",
        "content": "",
        "path": "",
        "homeData": home_data,
    }


# ── Main logic ───────────────────────────────────────────────────────────────

def scan_docs(docs_dir: Path, project_root: Path) -> list[dict]:
    """Scan docs_dir recursively for .md files and build DOC_DATA."""
    docs = []
    exclude_dirs = {"_bundle", "node_modules", ".git"}

    for md_file in sorted(docs_dir.rglob("*.md")):
        # Skip excluded directories
        if any(part in exclude_dirs for part in md_file.parts):
            continue

        # Relative path from docs_dir (for section mapping)
        rel_to_docs = md_file.relative_to(docs_dir).as_posix()

        # Relative path from project root (for display)
        try:
            rel_to_root = md_file.relative_to(project_root).as_posix()
        except ValueError:
            rel_to_root = md_file.as_posix()

        content = md_file.read_text(encoding="utf-8", errors="replace")
        title = extract_title(content, md_file.name)
        doc_id = slugify(rel_to_docs)
        section = determine_section(rel_to_docs)
        sidebar_title = clean_sidebar_title(doc_id, title)

        docs.append({
            "id": doc_id,
            "title": title,
            "sidebarTitle": sidebar_title,
            "section": section,
            "content": content,
            "path": rel_to_root,
        })

    # Sort by section order then by explicit slug order
    docs.sort(key=doc_sort_key)

    # Exclude README.md from sidebar (we use __home__ instead)
    # but keep it in DOC_DATA for search
    # Generate home page and prepend
    home = generate_home_page(docs)
    docs.insert(0, home)

    return docs


def build_html(
    docs: list[dict],
    template_path: Path,
    project_name: str,
    generated_date: str,
) -> str:
    """Read the template and inject data."""
    template = template_path.read_text(encoding="utf-8")

    # Encode docs as JSON — escape </script> sequences
    json_data = json.dumps(docs, ensure_ascii=False, indent=None)
    json_data = json_data.replace("</", "<\\/")

    # Replace placeholders
    html = template.replace("__DOC_DATA_PLACEHOLDER__", json_data)
    html = html.replace("__PROJECT_NAME_PLACEHOLDER__", project_name)
    html = html.replace("__GENERATED_DATE_PLACEHOLDER__", generated_date)

    return html


def main():
    parser = argparse.ArgumentParser(
        description="Build a self-contained HTML documentation site from Markdown files."
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Project root directory (default: .)",
    )
    parser.add_argument(
        "--output",
        default="docs/site.html",
        help="Output HTML file path (default: docs/site.html)",
    )
    parser.add_argument(
        "--project-name",
        default=None,
        help="Project name (default: auto-detected from package.json)",
    )
    parser.add_argument(
        "--docs-dir",
        default="docs",
        help="Documentation directory relative to root (default: docs)",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    docs_dir = root / args.docs_dir
    output_path = root / args.output

    # Validate
    if not docs_dir.is_dir():
        print(f"Erreur : le dossier docs '{docs_dir}' n'existe pas.", file=sys.stderr)
        sys.exit(1)

    # Locate template
    script_dir = Path(__file__).resolve().parent
    template_path = script_dir.parent / "assets" / "doc-site-template.html"
    if not template_path.is_file():
        print(f"Erreur : template introuvable a '{template_path}'.", file=sys.stderr)
        sys.exit(1)

    # Project name
    project_name = args.project_name or detect_project_name(root)

    # Scan
    docs = scan_docs(docs_dir, root)
    if not docs:
        print("Attention : aucun fichier .md trouve dans", docs_dir, file=sys.stderr)
        sys.exit(0)

    # __home__ is generated, so actual file count is len-1
    file_count = len(docs) - 1
    print(f"[doc-generator] {file_count} fichiers Markdown trouves")

    # Build
    generated_date = date.today().isoformat()
    html = build_html(docs, template_path, project_name, generated_date)

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")

    size_kb = output_path.stat().st_size / 1024
    print(f"[doc-generator] Site genere : {output_path} ({size_kb:.0f} KB)")
    print(f"[doc-generator] Sections :")
    sections_count = {}
    for d in docs:
        if d["section"] == "__home__":
            continue
        sections_count[d["section"]] = sections_count.get(d["section"], 0) + 1
    for sec in SECTION_ORDER:
        if sec in sections_count:
            print(f"  - {sec} : {sections_count[sec]} doc(s)")
    for sec, count in sections_count.items():
        if sec not in SECTION_ORDER:
            print(f"  - {sec} : {count} doc(s)")


if __name__ == "__main__":
    main()
