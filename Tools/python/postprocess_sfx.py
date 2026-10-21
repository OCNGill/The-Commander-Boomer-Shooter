"""Normalise the 4 procedural SFX through the shared normaliser and report.

Runs the same loudness convergence used for the taunts so every delivered
file in the bank meets one spec: 44.1 kHz, 16-bit, mono, -16 LUFS,
true peak < -1.0 dBTP, no clipping.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import normalizer as nz  # noqa: E402

SFX_DIR = sys.argv[1] if len(sys.argv) > 1 else "Content/Audio/SFX"
WORK = sys.argv[2] if len(sys.argv) > 2 else ".audio_work/sfx"
# Optional third argument: a directory of UNPROCESSED sources. The procedural
# SFX are seeded and deterministic, so they can be regenerated from source
# and re-normalised through the current normaliser. Without this argument
# the script normalises the files in SFX_DIR in place.
SRC_DIR = sys.argv[3] if len(sys.argv) > 3 else None

SFX_FILES = [
    ("sfx_burp", "spherical creature belch: low-frequency AM burst, fast decay, noisy tail"),
    ("sfx_pizza_impact", "pizza impact: short bright transient with splat tail"),
    ("sfx_menace_hum", "menace hum: slow detuned low drone"),
    ("sfx_defeat_squelch", "defeat squelch: downward pitch sweep with noise"),
]

os.makedirs(WORK, exist_ok=True)
results = []
for stem, desc in SFX_FILES:
    src = os.path.join(SFX_DIR, stem + ".wav")
    if SRC_DIR:
        src = os.path.join(SRC_DIR, stem + ".wav")
    if not os.path.exists(src):
        print(f"MISSING raw {src}")
        continue
    dst = os.path.join(SFX_DIR, stem + ".wav")
    # normalise in place: the source is fully read before the destination
    # is written, so src == dst is safe
    # NOTE: no `crest_comp` kwarg. The crest reduction is no longer a flag --
    # it is folded into the normaliser's loudness stage (the two-pass
    # loudnorm's true-peak limiter), which runs for EVERY file. The
    # `is_taunt` switch only controls the duration/atempo fit, which the
    # SFX do not want because their lengths are already correct.
    m = nz.normalize(src, dst, WORK, dur_max=10.0, dur_min=0.2,
                     is_taunt=False)
    probs = nz.check(m, 0.2, 10.0, is_taunt=False)
    results.append({"id": stem, "filename": stem + ".wav",
                    "description": desc, "measured": m, "problems": probs})
    print(f"{stem:20s} dur={m['duration_s']:>6.2f}s LUFS={m['integrated_lufs']} "
          f"TP={m['true_peak_dbtp']} clip={m['clipped_samples']} "
          f"sr={m['sample_rate']} ch={m['channels']} "
          f"{'OK' if not probs else probs}", flush=True)

with open(os.path.join(WORK, "sfx_results.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)
print("SFX_NORMALISE_DONE")
