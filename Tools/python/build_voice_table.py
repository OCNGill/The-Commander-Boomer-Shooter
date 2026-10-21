"""The voice fingerprint table, and the per-file voice verifier.

WHAT THE MEASUREMENTS SHOW
--------------------------
F0 does NOT discriminate between these references. The F5-TTS service
conditions on the reference clip's mel spectrogram (the source is
`ref_audio, ref_text = scan_voices()[ref_key]`), so the reference's
TIMBRE transfers, but the model's own prosody generator sets the output
fundamental. Every reference renders an output whose median F0 lands at
~73-77 Hz regardless of how the reference was pitched. The measured
reference clips themselves DO order correctly (52 / 59 / 65 / 71 Hz for
harvester_low / harvester / spokesman / settlement_human), so the pitch
shifts were applied correctly -- the shift simply is not carried through
to the output fundamental.

The spectral centroid IS carried through, and it orders exactly as
designed:

    harvester_low  <  harvester  <  spokesman/commander/hermes  <  settlement_human

So the honest fingerprint is a PAIR: f0 (recorded, and documented as
non-discriminating) plus a timbre fingerprint that does the work. The
timbre fingerprint here is the log-mel band-energy profile, compared by
normalised RMS distance.

TWO NUMBERS PER PAIR
--------------------
For every pair of references the script reports:
  * WITHIN  -- the distance between two renders of the SAME reference.
    This is the noise floor.
  * BETWEEN -- the distance between renders of DIFFERENT references.
    A pair is only separable if BETWEEN > WITHIN.

A pair that fails that test is reported as NOT SEPARABLE rather than
being quietly presented as distinct.
"""
import glob
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import voiceprint as vp  # noqa: E402

REFERENCES = [
    ("spokesman", "machine / default register (the service default)"),
    ("commander", "pre-existing alias of spokesman (identical ref.wav)"),
    ("hermes", "pre-existing alias of spokesman (identical ref.wav)"),
    ("harvester", "THE BOSS - phases 1-2"),
    ("harvester_low", "THE BOSS - phase 3, voice coming apart"),
    ("settlement_human", "settlement human voices"),
]


def profile(path):
    """Mel timbre profile + scalar fingerprint of one file."""
    x, sr = vp.load_wav(path)
    a = vp.analyse(path)
    a["mel_profile"] = vp.mel_bands(x, sr).tolist()
    return a


def build(src, out_path):
    files = sorted(glob.glob(os.path.join(src, "*.wav")))
    if not files:
        print("no renders in", src)
        sys.exit(1)
    per = {}
    for p in files:
        name = os.path.splitext(os.path.basename(p))[0]
        ref = name.rsplit("_r", 1)[0]
        per.setdefault(ref, []).append(profile(p))
        print(f"measured {name}", flush=True)

    table = {}
    for ref, role in REFERENCES:
        rows = per.get(ref, [])
        if not rows:
            continue
        f0s = [r["f0_median_hz"] for r in rows if r.get("f0_median_hz")]
        cens = [r["spectral_centroid_hz"] for r in rows
                if r.get("spectral_centroid_hz")]
        if not f0s:
            continue
        table[ref] = {
            "role": role,
            "renders_measured": len(f0s),
            "f0_median_hz": round(statistics.median(f0s), 2),
            "f0_render_spread_hz": (round(max(f0s) - min(f0s), 2)
                                    if len(f0s) > 1 else 0.0),
            "spectral_centroid_hz": (round(statistics.median(cens), 2)
                                     if cens else None),
            "centroid_render_spread_hz": (round(max(cens) - min(cens), 2)
                                          if len(cens) > 1 else 0.0),
        }

    # ------------------------------------------------ within vs between
    def prof(ref, i):
        return per[ref][i]["mel_profile"]

    within = {}
    for ref, rows in per.items():
        if len(rows) >= 2:
            d = [vp.mel_distance(prof(ref, 0), prof(ref, 1))]
            for i in range(2, len(rows)):
                d.append(vp.mel_distance(prof(ref, 0), prof(ref, i)))
            within[ref] = round(statistics.median(d), 4)

    between = {}
    refs = [r for r, _ in REFERENCES if r in per]
    for i, a_ref in enumerate(refs):
        for b_ref in refs[i + 1:]:
            d = vp.mel_distance(prof(a_ref, 0), prof(b_ref, 0))
            if len(per[b_ref]) > 1:
                d = min(d, vp.mel_distance(prof(a_ref, 0), prof(b_ref, 1)))
            between[f"{a_ref}|{b_ref}"] = round(d, 4)

    print("\n=== VOICE FINGERPRINT TABLE ===")
    for ref, t in table.items():
        print(f"{ref:18s} f0={t['f0_median_hz']:7.2f}Hz "
              f"(spread {t['f0_render_spread_hz']:5.2f})  "
              f"centroid={t['spectral_centroid_hz']}Hz "
              f"(spread {t['centroid_render_spread_hz']:6.2f})  "
              f"mel-within={within.get(ref)}")

    print("\n=== TIMBRE SEPARATION (mel distance; WITHIN < BETWEEN = separable)")
    for pair, d in sorted(between.items(), key=lambda kv: kv[1]):
        a_ref, b_ref = pair.split("|")
        w = max(within.get(a_ref, 0.0), within.get(b_ref, 0.0))
        sep = d > w
        tag = "SEPARABLE" if sep else "not separable"
        print(f"{a_ref:18s} vs {b_ref:18s} between={d:8.4f} "
              f"within={w:8.4f} -> {tag}")

    order = sorted(table.items(), key=lambda kv: kv[1]["spectral_centroid_hz"])
    print("\n=== CENTROID ORDER (dark -> bright) ===")
    for ref, t in order:
        print(f"  {ref:18s} {t['spectral_centroid_hz']:8.2f} Hz   {t['role']}")

    out = {
        "note": "F0 does not discriminate between these references: F5-TTS "
                "regenerates the output fundamental from its own prosody "
                "model, so every reference renders ~73-77 Hz. Timbre does "
                "discriminate, and the spectral centroid orders as designed.",
        "estimator": "voiceprint.yin_f0 (YIN, first-dip-below-threshold; "
                     "calibrated ratio 1.000 on synthetic 40-300 Hz) + "
                     "log-mel band-energy profile, normalised RMS distance",
        "within_reference_mel_distance": within,
        "between_reference_mel_distance": between,
        "centroid_order_dark_to_bright": [r for r, _ in order],
        "voice_fingerprint_table": table,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print("\nwrote", out_path)
    return out


def verify_file(path, table_json):
    """Classify one delivered file against the reference table."""
    with open(table_json, encoding="utf-8") as f:
        json.load(f)
    src = os.path.dirname(table_json)
    profs = {}
    for ref, _ in REFERENCES:
        cands = sorted(glob.glob(os.path.join(src, ref + "_r*.wav")))
        if cands:
            x, sr = vp.load_wav(cands[0])
            profs[ref] = vp.mel_bands(x, sr)
    x, sr = vp.load_wav(path)
    q = vp.mel_bands(x, sr)
    dists = {ref: round(vp.mel_distance(q, p), 4) for ref, p in profs.items()}
    ranked = sorted(dists.items(), key=lambda kv: kv[1])
    best = ranked[0]
    second = ranked[1] if len(ranked) > 1 else None
    margin = round(second[1] - best[1], 4) if second else None
    a = vp.analyse(path)
    return {
        "file": os.path.basename(path),
        "nearest_reference": best[0],
        "nearest_distance": best[1],
        "runner_up": second[0] if second else None,
        "runner_up_distance": second[1] if second else None,
        "margin": margin,
        "confident": bool(margin is not None and margin > 0.05),
        "f0_median_hz": a.get("f0_median_hz"),
        "spectral_centroid_hz": a.get("spectral_centroid_hz"),
        "all_distances": dists,
    }


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "verify":
        print(json.dumps(verify_file(sys.argv[2], sys.argv[3]), indent=2))
    else:
        src = sys.argv[1] if len(sys.argv) > 1 else ".audio_work/voices"
        out = (sys.argv[2] if len(sys.argv) > 2
               else ".audio_work/voices/voice_fingerprints.json")
        build(src, out)
        print("VOICE_TABLE_DONE")
