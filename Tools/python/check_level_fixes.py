#!/usr/bin/env python3
"""
Check that the runtime level fixes and the offline render fixes agree.

The C++ header Source/CommanderLevelFix/CommanderLevelFixValues.h is the
RUNTIME source of truth.  Tools/blender/render_level.py carries a LEVEL_FIXES
dict that drives the offline Blender renders.  If the two drift, the level we
ship and the level we screenshot are different levels, and every screenshot
becomes a lie.

This script parses the LEVEL_FIXES block out of the header and compares it
with the dict, then exits non-zero on any mismatch.

    python Tools/python/check_level_fixes.py

Exit codes:
    0  the two agree (or the values are numerically equal within 1e-9)
    1  a key is missing, extra, or has a different value
    2  the header block or the Python dict could not be parsed at all
"""
from __future__ import annotations

import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HEADER = os.path.join(REPO, "Source", "CommanderLevelFix", "CommanderLevelFixValues.h")
RENDER_LEVEL = os.path.join(REPO, "Tools", "blender", "render_level.py")

BEGIN = "LEVEL_FIXES_BEGIN"
END = "LEVEL_FIXES_END"

# inline constexpr double Name = 1.25;
CXX_RE = re.compile(
    r"inline\s+constexpr\s+(?:double|float)\s+([A-Za-z_]\w*)\s*=\s*"
    r"(-?\d+(?:\.\d+)?)\s*;"
)
# 'Name': 1.25,
PY_RE = re.compile(r"['\"]([A-Za-z_]\w*)['\"]\s*:\s*(-?\d+(?:\.\d+)?)")


def parse_header(path: str) -> dict:
    """Pull the KEY -> value pairs out of the LEVEL_FIXES block."""
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    b = text.find(BEGIN)
    e = text.find(END)
    if b < 0 or e < 0 or e < b:
        raise ValueError("LEVEL_FIXES_BEGIN/END markers not found in %s" % path)
    block = text[b:e]
    return {name: float(val) for name, val in CXX_RE.findall(block)}


def parse_dict(path: str) -> dict:
    """Pull the LEVEL_FIXES dict out of render_level.py."""
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    m = re.search(r"^LEVEL_FIXES\s*=\s*\{(.*?)^\}", text, re.S | re.M)
    if not m:
        raise ValueError("LEVEL_FIXES dict not found in %s" % path)
    return {name: float(val) for name, val in PY_RE.findall(m.group(1))}


def main() -> int:
    for path in (HEADER, RENDER_LEVEL):
        if not os.path.exists(path):
            print("[FAIL] missing file: %s" % path)
            return 2

    try:
        header = parse_header(HEADER)
        py = parse_dict(RENDER_LEVEL)
    except (OSError, ValueError) as exc:
        print("[FAIL] could not parse: %s" % exc)
        return 2

    if not header:
        print("[FAIL] header block parsed as EMPTY - refusing to pass")
        return 2
    if not py:
        print("[FAIL] python dict parsed as EMPTY - refusing to pass")
        return 2

    print("Validating: %s" % HEADER)
    print("      vs: %s" % RENDER_LEVEL)
    print("-" * 70)
    print("header entries: %d   python entries: %d" % (len(header), len(py)))

    missing = sorted(set(header) - set(py))
    extra = sorted(set(py) - set(header))
    mismatched = sorted(
        k for k in set(header) & set(py) if abs(header[k] - py[k]) > 1e-9
    )

    for k in missing:
        print("[FAIL] missing from render_level.py: %s = %s" % (k, header[k]))
    for k in extra:
        print("[FAIL] not in the C++ header:      %s = %s" % (k, py[k]))
    for k in mismatched:
        print("[FAIL] value differs: %s  header=%s  python=%s"
              % (k, header[k], py[k]))

    if missing or extra or mismatched:
        print("-" * 70)
        print("RESULT: FAILED - %d missing, %d extra, %d mismatched"
              % (len(missing), len(extra), len(mismatched)))
        return 1

    print("[ OK] all %d level-fix values agree exactly" % len(header))
    print("-" * 70)
    print("RESULT: All checks PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
