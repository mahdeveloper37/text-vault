#!/usr/bin/env python3
"""
generate_manifest.py
────────────────────
Scans a local directory of Interactive Fiction story files and produces
a manifest.json ready to drop into your text-vault/scripts/ folder on
GitHub Pages.

Usage
─────
  python generate_manifest.py                   # scans ./scripts by default
  python generate_manifest.py /path/to/scripts  # custom directory
  python generate_manifest.py --help

The manifest is written to <scripts_dir>/manifest.json and also printed
to stdout so you can review it before committing.
"""

import json
import os
import re
import sys
from pathlib import Path

# ── Supported Interactive Fiction formats ─────────────────────────────────────
EXTENSIONS = {
    ".z3":    "Z-MACHINE",
    ".z4":    "Z-MACHINE",
    ".z5":    "Z-MACHINE",
    ".z6":    "Z-MACHINE",
    ".z7":    "Z-MACHINE",
    ".z8":    "Z-MACHINE",
    ".zblorb":"BLORB",
    ".zlb":   "BLORB",
    ".gblorb":"BLORB (GLULX)",
    ".glb":   "BLORB (GLULX)",
    ".ulx":   "GLULX",
    ".blb":   "BLORB",
    ".blorb": "BLORB",
    ".t3":    "TADS 3",
    ".gam":   "TADS 2",
    ".acd":   "ALAN",
    ".a3c":   "ALAN 3",
    ".hex":   "HUGO",
    ".saga":  "SCOTT ADAMS",
    ".dat":   "SCOTT ADAMS",
    ".d$$":   "SCOTT ADAMS",
}

# ── Known games database ──────────────────────────────────────────────────────
# Maps lowercase filename (without extension) → {title, author, desc}
# Add your own entries here if you want richer auto-fill.
KNOWN_GAMES = {
    "zork1": {
        "title":  "ZORK I: THE GREAT UNDERGROUND EMPIRE",
        "author": "Infocom",
        "desc":   "You are standing west of a white house, with a boarded front door. "
                  "Your quest: plunder the Great Underground Empire of its 19 treasures.",
    },
    "zork2": {
        "title":  "ZORK II: THE WIZARD OF FROBOZZ",
        "author": "Infocom",
        "desc":   "Deep in the caverns of the Great Underground Empire, the Wizard of Frobozz "
                  "wields erratic magic against you.",
    },
    "zork3": {
        "title":  "ZORK III: THE DUNGEON MASTER",
        "author": "Infocom",
        "desc":   "The final chapter. Prove yourself worthy in the land of the Dungeon Master.",
    },
    "hitchhiker": {
        "title":  "THE HITCHHIKER'S GUIDE TO THE GALAXY",
        "author": "Infocom / Douglas Adams",
        "desc":   "Don't panic.",
    },
    "hitchhikers": {
        "title":  "THE HITCHHIKER'S GUIDE TO THE GALAXY",
        "author": "Infocom / Douglas Adams",
        "desc":   "Don't panic.",
    },
    "trinity": {
        "title":  "TRINITY",
        "author": "Infocom",
        "desc":   "Race against time across history to prevent nuclear disaster.",
    },
    "planetfall": {
        "title":  "PLANETFALL",
        "author": "Infocom",
        "desc":   "Stranded on an alien planet with only a robot companion named Floyd.",
    },
    "infidel": {
        "title":  "INFIDEL",
        "author": "Infocom",
        "desc":   "An archaeological adventure set amid the pyramids of Egypt.",
    },
    "wishbringer": {
        "title":  "WISHBRINGER",
        "author": "Infocom",
        "desc":   "A beginner-friendly tale of a magic stone that grants wishes.",
    },
    "lurking": {
        "title":  "THE LURKING HORROR",
        "author": "Infocom",
        "desc":   "A Lovecraftian nightmare at G.U.E. Tech on a stormy winter night.",
    },
    "anchorhead": {
        "title":  "ANCHORHEAD",
        "author": "Michael Gentry",
        "desc":   "A tale of cosmic horror in a rain-soaked New England town.",
    },
    "curses": {
        "title":  "CURSES",
        "author": "Graham Nelson",
        "desc":   "A sweeping puzzlefest through time, beginning in a dusty attic.",
    },
    "advent":     {"title": "COLOSSAL CAVE ADVENTURE", "author": "Crowther & Woods", "desc": "The original. All others owe it a debt."},
    "adventure":  {"title": "COLOSSAL CAVE ADVENTURE", "author": "Crowther & Woods", "desc": "The original. All others owe it a debt."},
    "frotz":      {"title": "FROTZ", "author": "Unknown", "desc": ""},
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def stem_to_title(stem: str) -> str:
    """Convert a filename stem to a readable uppercase title.
    e.g. 'zork_one' → 'ZORK ONE', 'myGame2' → 'MYGAME2'
    """
    # Split on underscores/hyphens/dots then uppercase
    words = re.split(r"[_\-\.]+", stem)
    return " ".join(w.upper() for w in words if w)


def scan_directory(scripts_dir: Path) -> list[dict]:
    entries = []
    files = sorted(
        (f for f in scripts_dir.iterdir() if f.is_file() and f.suffix.lower() in EXTENSIONS),
        key=lambda f: f.name.lower()
    )

    if not files:
        return entries

    print(f"\n  Found {len(files)} story file(s):\n")

    for f in files:
        stem   = f.stem.lower()
        ext    = f.suffix.lower()
        genre  = EXTENSIONS[ext]
        known  = KNOWN_GAMES.get(stem, {})
        size   = f.stat().st_size

        title  = known.get("title",  stem_to_title(f.stem))
        author = known.get("author", "Unknown")
        desc   = known.get("desc",   "")

        entry = {
            "file":   f"scripts/{f.name}",
            "title":  title,
            "author": author,
            "genre":  genre,
        }
        if desc:
            entry["desc"] = desc

        entries.append(entry)

        # Pretty console summary
        kb = size / 1024
        print(f"  ✔  {f.name:<30} {kb:>6.1f} KB   {genre}")
        print(f"     {title}")
        print(f"     by {author}")
        print()

    return entries


def write_manifest(scripts_dir: Path, entries: list[dict]) -> Path:
    out = scripts_dir / "manifest.json"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(entries, fh, indent=2, ensure_ascii=False)
    return out


def main():
    # ── Parse argument ────────────────────────────────────────────────────────
    args = [a for a in sys.argv[1:] if a != "--help"]
    show_help = "--help" in sys.argv or "-h" in sys.argv

    if show_help:
        print(__doc__)
        sys.exit(0)

    scripts_dir = Path(args[0]) if args else Path("scripts")

    # ── Banner ────────────────────────────────────────────────────────────────
    print()
    print("  ╔══════════════════════════════════════╗")
    print("  ║   TEXT VAULT — Manifest Generator   ║")
    print("  ╚══════════════════════════════════════╝")
    print(f"\n  Scanning: {scripts_dir.resolve()}")

    if not scripts_dir.exists():
        print(f"\n  ERROR: Directory '{scripts_dir}' not found.")
        print("  Create it or pass a different path as the first argument.\n")
        sys.exit(1)

    if not scripts_dir.is_dir():
        print(f"\n  ERROR: '{scripts_dir}' is not a directory.\n")
        sys.exit(1)

    # ── Scan ──────────────────────────────────────────────────────────────────
    entries = scan_directory(scripts_dir)

    if not entries:
        exts = ", ".join(sorted(EXTENSIONS.keys()))
        print(f"\n  No story files found in '{scripts_dir}'.")
        print(f"  Supported extensions: {exts}\n")
        sys.exit(0)

    # ── Write ─────────────────────────────────────────────────────────────────
    out_path = write_manifest(scripts_dir, entries)

    print("  ─────────────────────────────────────────")
    print(f"  manifest.json written → {out_path.resolve()}")
    print(f"  {len(entries)} game(s) registered.")
    print()
    print("  Next steps:")
    print("  1. Review/edit scripts/manifest.json if needed.")
    print("  2. Commit manifest.json alongside your story files.")
    print("  3. Push to GitHub — the arcade will update automatically.")
    print()

    # ── Preview ───────────────────────────────────────────────────────────────
    print("  ── manifest.json preview ─────────────────")
    print(json.dumps(entries, indent=2, ensure_ascii=False))
    print()


if __name__ == "__main__":
    main()
