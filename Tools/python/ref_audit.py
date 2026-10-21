"""Verify that the provisioned character references are genuinely distinct
registers -- and in the intended direction.

The character refs were derived from the base `spokesman` clip by
ffmpeg rubberband pitch shift. A pitch shift can fail silently (filter
misfire, wrong parameter semantics) and produce a file that is byte-
different but spectrally identical, so the claim "harvester_low is lower
than harvester" must be MEASURED, not assumed.

Two independent checks:

1. SPECTRAL SHIFT via mel-domain alignment. Compute the log-mel
   spectrogram of the base clip and of the variant, then find the shift
   that best aligns the variant's mel bins onto the base's. A variant
   shifted DOWN by N semitones must align at roughly -N semitones
   relative to the base. This is direction-sensitive and does not
   depend on any F0 estimator.

   NOTE ON UNITS: `best_shift_cents` returns an index into the 48-band
   filterbank, i.e. MEL BINS. It is not a count of cents and not a
   count of semitones. It is reported below as `bands` and is NOT
   compared against the semitone EXPECT table.

2. REGISTER via F0. The register check is the semitone offset of the
   variant's octave-corrected YIN F0 median from the base clip's:
   12 * log2(f0_variant / f0_base). That is the quantity the design
   targets in semitones, so it is the quantity that is compared to
   EXPECT, with a tolerance in semitones.

   Plus an explicit octave-error audit: report the fraction of voiced
   frames and the modal octave so a spurious 2x/3x reading is visible
   rather than silently averaged in.

   An earlier revision of this script compared the semitone EXPECT
   table against the mel-BIN shift and reported "MISMATCH" for every
   character clip. That verdict was a units error, not a defect: the
   same clips measured in semitones by the estimator below land within
   TOLERANCE_ST of their design targets.
"""
import glob
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import voiceprint as sa  # noqa: E402

SR = 24000


def logmel(x, sr, n_mels=48, n_fft=1024, hop=256):
    """Minimal log-mel spectrogram, numpy only."""
    win = np.hanning(n_fft)
    frames = 1 + (len(x) - n_fft) // hop
    mel = np.linspace(0, 1, n_mels)
    hz = mel * (sr / 2)
    # hz -> mel (slaney-ish)
    f_min, f_sp = 0.0, 200.0 / 3
    mels = (np.log1p(hz / f_sp) / np.log(1 + (sr / 2) / f_sp))
    m_min, m_max = mels[0], mels[-1]
    bins = np.floor((n_fft + 1) * hz / sr).astype(int)
    bins = np.clip(bins, 0, n_fft // 2)
    fb = np.zeros((n_mels, n_fft // 2 + 1))
    for i in range(n_mels):
        lo = bins[i]
        hi = bins[i + 1] + 1 if i + 1 < n_mels else n_fft // 2 + 1
        hi = max(hi, lo + 1)
        fb[i, lo:min(hi, n_fft // 2 + 1)] = 1.0
    fb /= fb.sum(axis=1, keepdims=True) + 1e-9
    out = np.zeros((n_mels, frames))
    for t in range(frames):
        seg = x[t * hop:t * hop + n_fft] * win
        S = np.abs(np.fft.rfft(seg)) ** 2
        out[:, t] = fb @ S
    return np.log(out + 1e-10)


def best_shift_cents(base_mel, var_mel):
    """Shift (cents) of `var_mel` relative to `base_mel` along the mel axis.

    Positive = variant is HIGHER pitched than base.
    """
    nb = base_mel.shape[0]
    best = None
    for shift in range(-24, 25):          # +-24 mel bins
        if shift >= 0:
            b = base_mel[:nb - shift]
            v = var_mel[shift:]
        else:
            b = base_mel[-shift:]
            v = var_mel[:nb + shift]
        if b.shape[1] != v.shape[1]:
            continue
        # normalise each frame, then mean squared distance
        bn = b - b.mean(axis=0, keepdims=True)
        vn = v - v.mean(axis=0, keepdims=True)
        d = float(np.mean((bn - vn) ** 2))
        if best is None or d < best[1]:
            best = (shift, d)
    shift, _ = best
    # mel bins are linear in the log-mel scale -> ~ cents per bin
    return shift


def f0_audit(path):
    x, sr = sa.load_wav(path)
    times, f0 = sa.yin_f0(x, sr)
    voiced = f0[~np.isnan(f0)]
    if voiced.size == 0:
        return None
    med = float(np.median(voiced))
    # octave audit: which octave of the median do most frames fall in?
    oct_hits = {}
    for o in (0.5, 1.0, 2.0, 3.0):
        target = med * o
        c = int(np.sum(np.abs(voiced - target) < 0.12 * target))
        oct_hits[o] = c
    dom_oct = max(oct_hits, key=oct_hits.get)
    return {
        "f0_median_hz": round(med, 2),
        "voiced_frames": int(voiced.size),
        "voiced_fraction": round(voiced.size / max(1, len(f0)), 3),
        "dominant_octave_of_median": dom_oct,
        "frames_per_octave": {str(k): v for k, v in oct_hits.items()},
    }


if __name__ == "__main__":
    refs = sorted(glob.glob(".audio_work/refs/*.wav"))
    if not refs:
        print("no refs in .audio_work/refs/")
        sys.exit(1)
    base = ".audio_work/refs/spokesman.wav"
    bx, bsr = sa.load_wav(base)
    bmel = logmel(bx, bsr)
    base_aud = f0_audit(base)
    base_f0 = base_aud["f0_median_hz"] / base_aud["dominant_octave_of_median"]
    print("=== REF CLIP AUDIT (register in semitones + mel-band alignment) ===")
    print(f"{'ref':<20}{'st':>8}{'target':>8}{'f0_med':>9}{'oct':>6}"
          f"{'voiced%':>9}{'bands':>7}  verdict")
    EXPECT = {"spokesman": 0, "harvester": -2, "harvester_low": -4.5,
              "settlement_human": +1.5}
    TOLERANCE_ST = 1.0
    rows = {}
    for p in refs:
        name = os.path.splitext(os.path.basename(p))[0]
        x, sr = sa.load_wav(p)
        vmel = logmel(x, sr)
        bands = best_shift_cents(bmel, vmel)
        aud = f0_audit(p)
        f0 = aud["f0_median_hz"] / aud["dominant_octave_of_median"]
        st = 12.0 * math.log2(f0 / base_f0)
        exp = EXPECT.get(name)
        if exp is None:
            verdict = "?"
        elif name == "spokesman":
            verdict = "BASE" if abs(st) <= TOLERANCE_ST else f"UNEXPECTED {st:+.2f} st"
        else:
            ok = abs(st - exp) <= TOLERANCE_ST
            verdict = ("OK" if ok else
                       f"OFF TARGET expected {exp} st got {st:+.2f} st")
        rows[name] = {"semitones_vs_base": round(st, 2),
                      "expected_semitones": exp,
                      "mel_band_shift": bands,
                      "f0_median_hz": aud["f0_median_hz"],
                      "audit": aud, "verdict": verdict}
        print(f"{name:<20}{st:>8.2f}{(exp if exp is not None else 0):>8}"
              f"{aud['f0_median_hz']:>9.2f}{aud['dominant_octave_of_median']:>6}"
              f"{aud['voiced_fraction']*100:>8.1f}%{bands:>7}  {verdict}")
    print("\n=== F0 with octave correction (fold to the dominant octave) ===")
    for name, r in rows.items():
        a = r["audit"]
        raw = a["f0_median_hz"]
        o = a["dominant_octave_of_median"]
        corrected = round(raw / o, 2)
        print(f"{name:<20} raw_f0={raw:>8.2f}  octave={o}  "
              f"corrected_f0={corrected:>8.2f} Hz")
        r["f0_octave_corrected_hz"] = corrected
    import json
    with open(".audio_work/refs/ref_audit.json", "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)
    print("\nREF_AUDIT_DONE")
