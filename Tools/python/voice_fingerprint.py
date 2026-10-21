"""Voice fingerprint: render each reference TWICE, prove it reproduces, and
record the measured f0 + spectral centroid that identifies the voice.

The service registry is a DIRECTORY, not a hash:

    BASE/voices/<key>/{ref.wav, ref.txt}

scanned per request. A slot with both files is registered and selectable by
name; the request field is "ref" (NOT "voice"). An unknown ref returns
HTTP 400 with {"error": "unknown voice", "voices": [...]} -- it does NOT
fall back to the default, so a typo fails loudly.

IMPORTANT PROVENANCE NOTE: the pre-existing slots `spokesman`, `commander`
and `hermes` share a BYTE-IDENTICAL ref.wav (md5
44e918212e457a1bd6967ee479ef8b16). They are three names for one voice.
The three character slots (harvester, harvester_low, settlement_human) were
provisioned for this project from that same source clip, pitch-shifted to
create genuinely distinct registers, so they are spectrally separable
from the base voice and from each other.

For each reference this:
  1. renders the SAME line twice (reproducibility check),
  2. measures YIN f0 median + spectral centroid on both renders,
  3. reports the delta between the two renders of the same reference,
  4. reports the separation of every reference from every other.

The result is the voice table that goes in the manifest and the contract:
it is what lets a human change a character's voice by editing one line, and
what proves which voice any delivered file actually carries.
"""
import json
import os
import statistics
import sys
import threading
import time
import urllib.request

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import voiceprint as sa  # noqa: E402

URL = "http://10.0.0.42:8020/synth"
OUT = sys.argv[1] if len(sys.argv) > 1 else ".audio_work/voices"
CONCURRENCY = int(sys.argv[2]) if len(sys.argv) > 2 else 3
REPS = 2
TEXT = "Bring him the specimen."

REFERENCES = [
    ("spokesman", "machine / default register"),
    ("commander", "pre-existing alias (same ref as spokesman)"),
    ("hermes", "pre-existing alias (same ref as spokesman)"),
    ("harvester", "THE BOSS - phase 1-2"),
    ("harvester_low", "THE BOSS - phase 3, voice coming apart"),
    ("settlement_human", "settlement human voices"),
]

os.makedirs(OUT, exist_ok=True)
_lock = threading.Lock()
_it = {"i": 0}
JOBS = []
for ref, _role in REFERENCES:
    for r in range(REPS):
        JOBS.append((f"{ref}_r{r}", ref, r))


def synth(text, ref):
    payload = {"text": text}
    if ref is not None:
        payload["ref"] = ref
    req = urllib.request.Request(
        URL, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=1800) as r:
        return r.read()


def worker():
    while True:
        with _lock:
            if _it["i"] >= len(JOBS):
                return
            i = _it["i"]
            _it["i"] += 1
        name, ref, r = JOBS[i]
        t0 = time.time()
        try:
            data = synth(TEXT, ref)
            with open(os.path.join(OUT, name + ".wav"), "wb") as f:
                f.write(data)
            print(f"OK {name} wall={time.time()-t0:.1f}s bytes={len(data)}",
                  flush=True)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")[:200]
            print(f"ERR {name}: HTTP {e.code} {body}", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"ERR {name}: {e}", flush=True)


if __name__ == "__main__":
    t0 = time.time()
    ts = [threading.Thread(target=worker) for _ in range(CONCURRENCY)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    wall = time.time() - t0
    print(f"\nrendered {len(JOBS)} in {wall:.1f}s "
          f"({len(JOBS)/wall*60:.2f}/min at conc {CONCURRENCY})", flush=True)

    # ------------------------------------------------------------- measure
    print("\n=== PER RENDER ===", flush=True)
    per = {}
    for name, ref, r in JOBS:
        p = os.path.join(OUT, name + ".wav")
        if not os.path.exists(p):
            continue
        a = sa.analyse(p)
        per.setdefault(ref, []).append({
            "render": name,
            "f0_median_hz": a.get("f0_median_hz"),
            "f0_iqr_hz": a.get("f0_iqr_hz"),
            "spectral_centroid_hz": a.get("spectral_centroid_hz"),
            "spectral_spread_hz": a.get("spectral_spread_hz"),
            "duration_s": a.get("duration_s"),
        })

    print("\n=== VOICE FINGERPRINT TABLE ===", flush=True)
    table = {}
    for ref, role in REFERENCES:
        rows = per.get(ref, [])
        f0s = [r["f0_median_hz"] for r in rows if r["f0_median_hz"]]
        cen = [r["spectral_centroid_hz"] for r in rows
               if r["spectral_centroid_hz"]]
        if not f0s:
            print(f"{ref:18s} NO RENDERS", flush=True)
            continue
        f0_med = round(statistics.median(f0s), 2)
        cen_med = round(statistics.median(cen), 2) if cen else None
        # reproducibility: delta between the two renders of this same ref
        d_f0 = round(max(f0s) - min(f0s), 2) if len(f0s) > 1 else None
        d_cen = round(max(cen) - min(cen), 2) if len(cen) > 1 else None
        table[ref] = {
            "role": role,
            "renders_measured": len(f0s),
            "f0_median_hz": f0_med,
            "f0_render_spread_hz": d_f0,
            "spectral_centroid_hz": cen_med,
            "centroid_render_spread_hz": d_cen,
        }
        print(f"{ref:18s} f0={f0_med:8.2f}Hz (spread {d_f0}) "
              f"centroid={cen_med}Hz (spread {d_cen})  [{role}]", flush=True)

    # separation matrix
    print("\n=== SEPARATION (|dF0| Hz) ===", flush=True)
    refs = [r for r, _ in REFERENCES if r in table]
    print(f"{'':18s}" + "".join(f"{r[:9]:>11s}" for r in refs))
    for a_ref in refs:
        row = f"{a_ref:18s}"
        for b_ref in refs:
            d = abs(table[a_ref]["f0_median_hz"] - table[b_ref]["f0_median_hz"])
            row += f"{d:11.1f}"
        print(row)

    # verdict: is each character ref distinguishable from the base voice?
    print("\n=== VERDICT vs base voice (spokesman) ===", flush=True)
    base_f0 = table.get("spokesman", {}).get("f0_median_hz")
    base_cen = table.get("spokesman", {}).get("spectral_centroid_hz")
    for ref, _role in REFERENCES:
        if ref not in table:
            continue
        t = table[ref]
        d_f0 = abs(t["f0_median_hz"] - base_f0) if base_f0 else None
        d_cen = abs(t["spectral_centroid_hz"] - base_cen) if base_cen else None
        # a render-to-render spread is the noise floor for this reference
        nf = t["f0_render_spread_hz"]
        sep = (d_f0 is not None and nf is not None and d_f0 > nf)
        print(f"{ref:18s} |dF0|={d_f0} spread={nf} "
              f"|dCentroid|={d_cen} -> "
              f"{'DISTINCT' if sep else 'same-as-base/alias'}", flush=True)
        t["delta_f0_vs_base_hz"] = d_f0
        t["delta_centroid_vs_base_hz"] = d_cen
        t["distinct_from_base"] = bool(sep)

    out = {
        "text": TEXT,
        "replicates_per_reference": REPS,
        "concurrency": CONCURRENCY,
        "total_wall_s": round(wall, 1),
        "per_render": per,
        "voice_fingerprint_table": table,
    }
    with open(os.path.join(OUT, "voice_fingerprints.json"), "w",
              encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print("\nVOICE_FP_DONE", flush=True)
