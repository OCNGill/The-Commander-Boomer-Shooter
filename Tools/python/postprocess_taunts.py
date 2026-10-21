"""Normalise the rendered taunt bank through the shared normaliser and report.

Runs the same loudness convergence used for the SFX so every delivered file
in the project meets one spec: 44.1 kHz, 16-bit, mono, -16 LUFS integrated,
true peak < -1.0 dBTP, no clipping, taunt duration within [1.5, 6.0] s.

Input  : .audio_work/raw/<id>.wav   (24 kHz mono, straight from the service)
Output : Content/Audio/Insults/<id>.wav
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import normalizer as nz  # noqa: E402
from taunt_lines import TAUNTS  # noqa: E402

RAW = sys.argv[1] if len(sys.argv) > 1 else ".audio_work/raw"
OUT = sys.argv[2] if len(sys.argv) > 2 else "Content/Audio/Insults"
WORK = sys.argv[3] if len(sys.argv) > 3 else ".audio_work/norm"

os.makedirs(OUT, exist_ok=True)
os.makedirs(WORK, exist_ok=True)

results = []
for t in TAUNTS:
    tid = t["id"]
    src = os.path.join(RAW, tid + ".wav")
    dst = os.path.join(OUT, tid + ".wav")
    if not os.path.exists(src):
        print(f"MISSING raw {src}", flush=True)
        results.append({"id": tid, "problems": ["missing raw render"]})
        continue
    m = nz.normalize(src, dst, WORK, dur_max=6.0, dur_min=1.5, is_taunt=True,
                     max_atempo=2.5)
    probs = nz.check(m, 1.5, 6.0, is_taunt=True)
    results.append({"id": tid, "phase": t["phase"], "filename": tid + ".wav",
                    "measured": m, "problems": probs})
    print(f"{tid:18s} dur={m['duration_s']:>6.2f}s LUFS={m['integrated_lufs']:>7} "
          f"TP={m['true_peak_dbtp']:>6} clip={m['clipped_samples']:>5} "
          f"sr={m['sample_rate']} ch={m['channels']} "
          f"atempo={m.get('atempo_used')} "
          f"{'OK' if not probs else probs}", flush=True)

with open(os.path.join(WORK, "taunt_results.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

ok = sum(1 for r in results if not r.get("problems"))
print(f"\nnormalised {ok}/{len(TAUNTS)} taunts", flush=True)
print("TAUNT_NORMALISE_DONE", flush=True)
