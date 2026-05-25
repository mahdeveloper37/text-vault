#!/usr/bin/env python3
"""
generate_manifest.py
────────────────────
Scans a local directory of Interactive Fiction story files and produces
a manifest.json updated with the specific titles, authors, and descriptions
found in the project's manifest.
"""

import json
import os
import re
import sys
from pathlib import Path

# ── Updated Genre Formats ─────────────────────────────────────────────────────
# Adjusted to match the "Infocom - Z-MACHINE" format found in your manifest.json
EXTENSIONS = {
    ".z3":    "Infocom",
    ".z4":    "Infocom",
    ".z5":    "Adventure International",
    ".z6":    "Infocom",
    ".z7":    "Infocom",
    ".z8":    "Infocom",
    ".zblorb":"BLORB",
    ".gblorb":"BLORB (GLULX)",
    ".ulx":   "GLULX",
}

# ── Updated Games Database ────────────────────────────────────────────────────
# Mapping filename stem → {title, author, desc} based on your manifest.json
KNOWN_GAMES = {
    "amindforeverwandering": {
        "title": "A Mind Forever Voyaging",
        "author": "Steve Meretzky",
        "desc": "An AI simulates the future to test the impact of a new government plan."
    },
    "arthur-questforexcalibur": {
        "title": "Arthur: The Quest for Excalibur",
        "author": "Bob Bates",
        "desc": "You are young Arthur on a quest to pull Excalibur from the stone and prove your right to rule."
    },
    "ballyhoo": {
        "title": "Ballyhoo",
        "author": "Jeff O'Neill",
        "desc": "A mystery set in a traveling circus where you must find a missing girl."
    },
    "beyondzork": {
        "title": "Beyond Zork",
        "author": "Brian Moriarty",
        "desc": "An RPG-style adventure in the Zork universe where you seek the Coconut of Quendor."
    },
    "borderzone": {
        "title": "Border Zone",
        "author": "Marc Blank",
        "desc": "A real-time espionage thriller set in a fictional Cold War-era country."
    },
    "bureaucracy": {
        "title": "Bureaucracy",
        "author": "Douglas Adams",
        "desc": "A comedic satire about the frustrations of modern life and red tape."
    },
    "cutthroats": {
        "title": "Cutthroats",
        "author": "Michael Berlyn and Jerry Wolper",
        "desc": "You are a diver searching for sunken treasure while dealing with treacherous characters."
    },
    "deadline": {
        "title": "Deadline",
        "author": "Marc Blank",
        "desc": "The first interactive murder mystery, where you have 12 hours to solve a case."
    },
    "enchanter": {
        "title": "Enchanter",
        "author": "Marc Blank and Dave Lebling",
        "desc": "A fantasy adventure where a novice magician must stop an evil warlock."
    },
    "hitchhikersguidetothegalaxy": {
        "title": "The Hitchhiker's Guide to the Galaxy",
        "author": "Douglas Adams and Steve Meretzky",
        "desc": "A surreal comedy based on the book series."
    },
    "hollywoodhijinks": {
        "title": "Hollywood Hijinx",
        "author": "\"Hollywood\" Dave Anderson",
        "desc": "A scavenger hunt in a Hollywood mansion to claim an inheritance."
    },
    "infidel": {
        "title": "Infidel",
        "author": "Michael Berlyn",
        "desc": "An archaeological adventure set in an Egyptian pyramid, featuring an anti-hero."
    },
    "journey-thequestforisme": {
        "title": "Journey: The Quest for Isme",
        "author": "Marc Blank",
        "desc": "A party-based RPG/adventure hybrid following a group on a quest to save their land."
    },
    "milliways": {
        "title": "Milliways",
        "author": "Douglas Adams and Steve Meretzky",
        "desc": "The unreleased sequel to The Hitchhiker's Guide to the Galaxy."
    },
    "minizork1": {
        "title": "Mini-Zork I",
        "author": "Marc Blank and Dave Lebling",
        "desc": "A compact version of the original Zork I: The Great Underground Empire."
    },
    "minizork2": {
        "title": "Mini-Zork II",
        "author": "Marc Blank and Dave Lebling",
        "desc": "A compact version of Zork II: The Wizard of Frobozz."
    },
    "moonmist": {
        "title": "Moonmist",
        "author": "Stu Galley and Jim Lawrence",
        "desc": "A mystery for younger players set in a haunted Cornish castle."
    },
    "nordandbert": {
        "title": "Nord and Bert Couldn't Make Head or Tail of It",
        "author": "Jeff O'Neill",
        "desc": "A collection of wordplay-based short stories."
    },
    "planetfall": {
        "title": "Planetfall",
        "author": "Steve Meretzky",
        "desc": "Stranded on an alien planet with only a robot companion named Floyd."
    },
    "plunderedhearts": {
        "title": "Plundered Hearts",
        "author": "Amy Briggs",
        "desc": "A romantic adventure set on the high seas during the age of piracy."
    },
    "seastalker": {
        "title": "Seastalker",
        "author": "Stu Galley and Jim Lawrence",
        "desc": "A junior-level adventure involving a submarine and a sea monster."
    },
    "sherlock-theriddleofthecrownjewels": {
        "title": "Sherlock: The Riddle of the Crown Jewels",
        "author": "Bob Bates",
        "desc": "You play as Watson, assisting Holmes in solving a royal theft."
    },
    "shogun": {
        "title": "Shogun",
        "author": "Dave Lebling",
        "desc": "An epic historical adventure set in feudal Japan, adapted from James Clavell."
    },
    "sorcerer": {
        "title": "Sorcerer",
        "author": "Steve Meretzky",
        "desc": "The sequel to Enchanter, where you must rescue your mentor Belboz."
    },
    "spellbreaker": {
        "title": "Spellbreaker",
        "author": "Dave Lebling",
        "desc": "The final Enchanter game, dealing with the failure of magic itself."
    },
    "starcross": {
        "title": "Starcross",
        "author": "Dave Lebling",
        "desc": "A sci-fi adventure exploring a massive alien spaceship."
    },
    "stationfall": {
        "title": "Stationfall",
        "author": "Steve Meretzky",
        "desc": "The sequel to Planetfall, featuring the return of Floyd."
    },
    "suspect": {
        "title": "Suspect",
        "author": "Dave Lebling",
        "desc": "A murder mystery set at a Halloween masquerade ball."
    },
    "suspended-acryogenicnightmare": {
        "title": "Suspended: A Cryogenic Nightmare",
        "author": "Michael Berlyn",
        "desc": "A unique sci-fi game where you control six specialized robots from a cryogenic tank."
    },
    "thelurkinghorror": {
        "title": "The Lurking Horror",
        "author": "Dave Lebling",
        "desc": "A horror story set on a university campus, inspired by Lovecraft."
    },
    "trinity": {
        "title": "Trinity",
        "author": "Brian Moriarty",
        "desc": "A sophisticated fantasy weaving together history, physics, and the atomic age."
    },
    "wishbringer": {
        "title": "Wishbringer",
        "author": "Brian Moriarty",
        "desc": "A magical quest for a beginner audience, featuring a wish-granting stone."
    },
    "witness": {
        "title": "The Witness",
        "author": "Stu Galley",
        "desc": "A 1930s noir detective mystery."
    },
    "zork0-therevengeofmegaboz": {
        "title": "Zork Zero: The Revenge of Megaboz",
        "author": "Steve Meretzky",
        "desc": "A prequel to the original Zork trilogy, featuring many mini-games."
    },
    "zork1-thegreatundergroundempire": {
        "title": "Zork I: The Great Underground Empire",
        "author": "Marc Blank and Dave Lebling",
        "desc": "You are standing west of a white house. Your quest: plunder the Great Underground Empire of its 19 treasures. The classic dungeon crawl that started it all!"
    },
    "zork1": {
        "title": "Zork I: The Great Underground Empire",
        "author": "Marc Blank and Dave Lebling",
        "desc": "The classic dungeon crawl that started it all."
    },
    "zork2-thewizardoffrobozz": {
        "title": "Zork II: The Wizard of Frobozz",
        "author": "Marc Blank and Dave Lebling",
        "desc": "Continued exploration of the Great Underground Empire as you face the Wizard of Frobozz."
    },
    "zork3-thedungeonmaster": {
        "title": "Zork III: The Dungeon Master",
        "author": "Marc Blank and Dave Lebling",
        "desc": "The final chapter of the original trilogy, leading to a confrontation with the Dungeon Master."
    }
}

def stem_to_title(stem: str) -> str:
    words = re.split(r"[_\-\.]+", stem)
    return " ".join(w.capitalize() for w in words if w)

def scan_directory(scripts_dir: Path) -> list[dict]:
    entries = []
    files = sorted(
        (f for f in scripts_dir.iterdir() if f.is_file() and f.suffix.lower() in EXTENSIONS),
        key=lambda f: f.name.lower()
    )

    for f in files:
        stem   = f.stem.lower()
        ext    = f.suffix.lower()
        genre  = EXTENSIONS[ext]
        known  = KNOWN_GAMES.get(stem, {})

        title  = known.get("title",  stem_to_title(f.stem))
        author = known.get("author", "Unknown")
        desc   = known.get("desc",   "")

        entry = {
            "file":   f"scripts/{f.name}",
            "title":  title,
            "author": author,
            "genre":  genre,
            "desc":   desc
        }
        entries.append(entry)

    return entries

def write_manifest(scripts_dir: Path, entries: list[dict]) -> Path:
    out = scripts_dir / "manifest.json"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(entries, fh, indent=2, ensure_ascii=False)
    return out

def main():
    scripts_dir = Path("scripts")
    if not scripts_dir.exists():
        print(f"Error: {scripts_dir} not found.")
        sys.exit(1)

    entries = scan_directory(scripts_dir)
    if not entries:
        print("No matching files found.")
        sys.exit(0)

    write_manifest(scripts_dir, entries)
    print(f"manifest.json updated with {len(entries)} games.")

if __name__ == "__main__":
    main()