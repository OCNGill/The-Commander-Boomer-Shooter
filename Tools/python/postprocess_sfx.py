"""Post-process the 4 procedural SFX and emit measured results as JSON."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import postprocess as pp  # noqa: E402

SFX_DIR = sys.argv[1]
OUT = sys.argv[2]
WORK = os.path.join(SFX_DIR, "_work")

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
    dst = os.path.join(SFX_DIR, stem + "_final.wav")
    m = pp.process(src, dst, dur_max=10.0, dur_min=0.2, workdir=WORK)
    probs = pp.check(m, dur_min=0.2, dur_max=10.0, is_taunt=False)
    m["description"] = desc
    m["problems"] = probs
    results.append({"id": stem, "filename": stem + "_final.wav", **m})
    print(f"{stem}: dur={m['duration_s']} lufs={m['integrated_lufs']} "
          f"tp={m['true_peak_dbtp']} clip={m['clipped_samples']} "
          f"problems={probs}", flush=True)

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)
print("SFX_POST_OK")
