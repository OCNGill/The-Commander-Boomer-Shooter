#!/usr/bin/env python3
"""Generate the roster bible's engine-boundary doctrine.

THE GENERATOR IS THE SOURCE OF TRUTH for the engine boundary. `roster_bible.md` and
`roster_bible.json` are generated artifacts: the surrounding design prose is
hand-authored, but every statement about WHICH runtime ships, what belongs in C++,
and how the JSON contract is consumed is rendered from the constants in this file.
Editing the generated files by hand is how they drift; edit this file and re-run.

Usage:
    python Tools/python/gen_roster_bible.py          # write the generated files
    python Tools/python/gen_roster_bible.py --check  # exit 1 if the files drifted

Idempotent: running it twice produces byte-identical output.
"""

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MD_PATH = REPO / "Docs" / "generated" / "roster_bible.md"
JSON_PATH = REPO / "Docs" / "generated" / "roster_bible.json"

# ---------------------------------------------------------------------------
# DOCTRINE - the shipped runtime is UE5 5.8 with C++ module code.
# ---------------------------------------------------------------------------

DOC_VERSION = "1.2"
DOC_DATE = "2026-10-22"

AMENDMENT_12 = (
    "**Amendment 1.2:** the shipped runtime is UE5 5.8 with C++ module code - the "
    "boundary is now C++ vs UE5/Blender, and `roster_bible.json` stays the only "
    "interface (a build-time generator emits the C++ stat tables from it)."
)

ENGINE_FIELD = (
    "Unreal Engine 5.8 + Blender 4.2.23 (authoring); C++ / UE5 runtime (ship)"
)

PORTABILITY_LOGIC = (
    "pure C++ (UE5 module code) - damage math, AI state machines, encounter "
    "scripting, audio scheduling, taunt selection, pickup rules, weapon stats"
)
PORTABILITY_ENGINE = (
    "UE5/Blender-side - meshes, skeletons, materials, textures, lighting rigs, "
    "level geometry, particles"
)
PORTABILITY_CONTRACT = (
    "This file is the ONLY interface between the two. The C++ runtime reads these "
    "numbers verbatim; no value here is re-derived in code, and a build-time "
    "generator emits the C++ stat tables from it."
)

SECTION_9_HEADING = "## 9. Engine / C++ boundary"

SECTION_9_INTRO = (
    "The shipped game is a **UE5 5.8 build whose runtime is C++** - the gameplay "
    "logic is an Unreal module compiled from C++ under `Source/`, not a separate "
    "executable. Blender is the authoring tool. The split is not negotiable and it "
    "is not fuzzy:"
)

BOUNDARY_ROWS = [
    ("Damage math, hit resolution, resistance scalars",
     "Meshes, skeletons, FBX import, LODs"),
    ("AI state machines, telegraph timers, aggro, pathing costs",
     "Materials, textures, material instances"),
    ("Encounter scripting, wave timing, spawn tables",
     "Lighting rigs, level geometry, fog, post-process"),
    ("Weapon stats, ammo economy, pickup rules",
     "Particles, decals, gib meshes, audio *assets*"),
    ("Audio **scheduling** (when, at what volume, with what priority)",
     "Audio playback (the mixer)"),
    ("Taunt/insult selection, cooldowns, phase gating",
     "The rendered insult WAVs themselves"),
    ("Difficulty scalar application", ""),
    ("Score, one-liner selection, gib-request dispatch", ""),
]

BOUNDARY_TABLE_HEADER = (
    "| Belongs in **C++** (UE5 module code - pure logic, unit-testable) "
    "| Belongs in **UE5 / Blender** (engine-side content) |"
)

SECTION_9_CONTRACT = (
    "**The contract file is `Docs/generated/roster_bible.json`.** The C++ side "
    "reads it verbatim at build time - a build-time generator emits the C++ stat "
    "tables from it. No value in that JSON is re-typed into C++ by hand - a "
    "generator consumes it, so the two can never drift. The same is true of the "
    "boss spec and the insult-bank spec."
)

LINUX_NOTE = (
    "**Linux note.** The game must build and run on Linux (fleet nodes develop it; "
    "the Deck runs it under Proton). Therefore:"
)
LINUX_NOTE_BULLETS = [
    "All paths in tooling are POSIX-normalised and relative; no Windows-only path assumptions.",
    "All asset names are lowercase-with-underscores for the C++ side's asset manifest, even "
    "though the UE assets keep their display casing.",
    "The headless Blender and UE commandlet invocations in `Tools/blender/` and "
    "`Tools/python/` are written to run on both; the Windows equivalents use `flock` "
    "equivalents via `Tools/blender/blender_turn_htpc.sh`.",
    "No Windows-only audio or filesystem API in the C++ runtime. The WAV reader is written "
    "against UE's platform-agnostic file API (`FFileHelper` / `IFileManager`) plus a "
    "hand-rolled RIFF parser (the TTS service emits plain RIFF/PCM - see §11.3).",
]

# Terminology swept across both generated files. Ordered; applied to the whole file.
TERMINOLOGY = [
    ("the Rust runtime", "the C++ runtime"),
    ("pure Rust", "pure C++"),
    ("the Rust side", "the C++ side"),
    ("the Rust lane", "the C++ lane"),
    ("the Rust core", "the C++ core"),
    ("the Rust taunt rotation", "the C++ taunt rotation"),
    ("Rust/engine boundary", "C++/engine boundary"),
]

STALE_WORDING = re.compile(r"\brust\b", re.IGNORECASE)


def apply_terminology(text):
    for old, new in TERMINOLOGY:
        text = text.replace(old, new)
    return text


def render_section_9():
    rows = "\n".join("| {0} | {1} |".format(l, r) for l, r in BOUNDARY_ROWS)
    bullets = "\n".join("- " + b for b in LINUX_NOTE_BULLETS)
    return "\n\n".join([
        SECTION_9_HEADING,
        SECTION_9_INTRO,
        BOUNDARY_TABLE_HEADER + "\n|---|---|\n" + rows,
        SECTION_9_CONTRACT,
        LINUX_NOTE + "\n" + bullets,
    ])


def patch_header(md):
    md = md.replace("**Version:** 1.1 \u00b7 **Date:** 2026-10-21 \u00b7",
                    "**Version:** " + DOC_VERSION + " \u00b7 **Date:** " + DOC_DATE + " \u00b7")
    if AMENDMENT_12 in md:
        return md
    lines = md.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("**Amendment 1.1:**"):
            lines.insert(i + 1, AMENDMENT_12)
            break
    else:
        raise SystemExit("generator: could not find the amendment header line")
    return "\n".join(lines)


def splice_section_9(md):
    start = re.search(r"^## 9\..*$", md, re.M)
    end = re.search(r"^## 10\..*$", md, re.M)
    if not start or not end or end.start() <= start.start():
        raise SystemExit("generator: could not locate the section 9 / section 10 headings")
    head, tail = md[:start.start()], md[end.start():]
    return head + render_section_9().rstrip("\n") + "\n\n---\n\n" + tail


def render_md(raw):
    md = apply_terminology(raw)
    md = patch_header(md)
    md = splice_section_9(md)
    return md


def render_json(raw):
    data = json.loads(apply_terminology(raw))
    data["engine"] = ENGINE_FIELD
    data["generated"] = DOC_DATE
    if "version" in data:
        data["version"] = DOC_VERSION
    if "amended" in data:
        data["amended"] = DOC_DATE
    data["portability"] = {
        "logic": PORTABILITY_LOGIC,
        "engine": PORTABILITY_ENGINE,
        "contract": PORTABILITY_CONTRACT,
    }
    out = json.dumps(data, indent=2, ensure_ascii=False)
    if raw.endswith("\n"):
        out += "\n"
    return out


def assert_no_stale(name, text):
    hits = [ln for ln in text.split("\n") if STALE_WORDING.search(ln)]
    if hits:
        for ln in hits:
            print("generator: stale runtime wording in " + name + ": " + ln.strip())
        raise SystemExit(1)


def main(argv):
    check = "--check" in argv
    md_raw = MD_PATH.read_text(encoding="utf-8")
    json_raw = JSON_PATH.read_text(encoding="utf-8")
    md_new = render_md(md_raw)
    json_new = render_json(json_raw)
    assert_no_stale("roster_bible.md", md_new)
    assert_no_stale("roster_bible.json", json_new)
    outputs = [(MD_PATH, md_new), (JSON_PATH, json_new)]
    if check:
        drift = [str(p.relative_to(REPO)) for p, t in outputs if p.read_text(encoding="utf-8") != t]
        if drift:
            print("generator: DRIFT - " + ", ".join(drift))
            return 1
        print("generator: generated files are up to date")
        return 0
    for path, text in outputs:
        if path.read_text(encoding="utf-8") != text:
            path.write_text(text, encoding="utf-8", newline="\n")
            print("generator: wrote " + str(path.relative_to(REPO)))
        else:
            print("generator: unchanged " + str(path.relative_to(REPO)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
