"""A reliable F0 + centroid fingerprint for short speech clips.

WHY THIS EXISTS
---------------
The first YIN implementation returned medians around 62-85 Hz on a clip
that is clearly a low male voice reading "Bring him the specimen." and
marked only ~5% of frames voiced -- on audio that is 100% continuously
voiced by amplitude. Two separate faults:

  * the absolute threshold of 0.15 was too strict for this material, so
    most frames were discarded as unvoiced and the surviving frames were
    biased toward the most periodic part of the signal;
  * YIN's "first local minimum below threshold" rule can still land on a
    SUB-HARMONIC (tau too large -> f0 too low) when the signal has a
    strong low-frequency component, which is exactly what a pitch-shifted
    low voice has.

The fix is a two-stage estimator:
  1. compute the YIN cumulative mean normalised difference function;
  2. find ALL local minima below a relaxed threshold, then pick the
     SMALLEST tau (highest f0) whose minimum is within a factor of the
     global best -- i.e. prefer the true fundamental over a sub-harmonic,
     but do not chase noise.

On top of that, an octave-consistency check reports the dominant octave so
a spurious 2x/3x reading is visible rather than silently averaged in.

Everything is numpy only: scipy and librosa are not available on this host.
"""
import numpy as np
import wave

SR_EXPECTED = 24000


def load_wav(path):
    """Load a WAV as float64 mono in [-1, 1]."""
    with wave.open(path, "rb") as w:
        nch, sw, sr, n = (w.getnchannels(), w.getsampwidth(), w.getframerate(),
                          w.getnframes())
        raw = w.readframes(n)
    if sw != 2:
        raise ValueError(f"expected 16-bit PCM, got {sw * 8}-bit")
    d = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0
    if nch > 1:
        d = d.reshape(-1, nch).mean(axis=1)
    return d, sr


def _yin_dp(frame, tau_max, tau_min):
    """Cumulative mean normalised difference function for one frame."""
    d = np.zeros(tau_max + 1)
    for tau in range(1, tau_max + 1):
        diff = frame[:len(frame) - tau] - frame[tau:len(frame)]
        d[tau] = float(np.dot(diff, diff))
    dp = np.ones(tau_max + 1)
    running = 0.0
    for tau in range(1, tau_max + 1):
        running += d[tau]
        dp[tau] = d[tau] * tau / running if running > 0 else 1.0
    return dp


def yin_f0(x, sr, fmin=40.0, fmax=400.0, threshold=0.45,
           frame_ms=70.0, hop_ms=10.0, prefer_octave=True):
    """YIN F0 per frame, with sub-harmonic suppression.

    Returns (times, f0_hz). Unvoiced frames are NaN.
    """
    win = max(16, int(sr * frame_ms / 1000.0))
    hop = max(1, int(sr * hop_ms / 1000.0))
    tau_min = max(2, int(sr / fmax))
    # +1 so a fundamental exactly at fmin is still inside the band: the
    # period of a 40 Hz voice is 600 samples at 24 kHz, and an exclusive
    # upper bound dropped it entirely.
    tau_max = min(win - 2, int(sr / fmin) + 1)
    if tau_max <= tau_min + 1:
        return np.array([]), np.array([])

    times, f0s = [], []
    for start in range(0, max(1, len(x) - win), hop):
        frame = x[start:start + win]
        if len(frame) < win:
            break
        rms = float(np.sqrt((frame ** 2).mean()))
        if rms < 0.005:
            times.append(start / sr)
            f0s.append(np.nan)
            continue
        dp = _yin_dp(frame, tau_max, tau_min)

        # YIN's rule for avoiding octave errors: take the FIRST local
        # minimum that dips below the absolute threshold -- i.e. the
        # SMALLEST tau (highest f0) that is clearly periodic. A sub-
        # harmonic (tau ~ 2x) also produces a dip, but it comes LATER, so
        # "first dip wins" rejects it.
        #
        # An earlier version filtered the candidate minima by "within
        # 1.6x of the best score" before taking the smallest, which is
        # exactly backwards: when the true fundamental scores slightly
        # worse than its own sub-harmonic, the filter discards the
        # fundamental and the estimator reports half the true f0.
        best = None
        for tau in range(tau_min, tau_max):
            if dp[tau] < dp[tau - 1] and dp[tau] <= dp[tau + 1] \
                    and dp[tau] < threshold:
                best = tau
                break
        if best is None:
            times.append(start / sr)
            f0s.append(np.nan)
            continue
        t = best

        shift = 0.0
        if 0 < t < tau_max:
            a, b, c = dp[t - 1], dp[t], dp[t + 1]
            denom = a + c - 2 * b
            if denom != 0:
                shift = 0.5 * (a - c) / denom
        times.append(start / sr)
        f0s.append(sr / (t + shift))
    return np.array(times), np.array(f0s)


def f0_summary(x, sr, **kw):
    """Median F0 and spread over voiced frames, plus octave audit."""
    _, f0 = yin_f0(x, sr, **kw)
    voiced = f0[~np.isnan(f0)]
    total = len(f0)
    if voiced.size < 3:
        return None
    med = float(np.median(voiced))
    oct_hits = {}
    for o in (0.5, 1.0, 2.0, 3.0):
        target = med * o
        oct_hits[o] = int(np.sum(np.abs(voiced - target) < 0.15 * target))
    dom = max(oct_hits, key=oct_hits.get)
    return {
        "f0_median_hz": round(med, 2),
        "f0_p10_hz": round(float(np.percentile(voiced, 10)), 2),
        "f0_p90_hz": round(float(np.percentile(voiced, 90)), 2),
        "f0_iqr_hz": round(float(np.percentile(voiced, 75)
                                 - np.percentile(voiced, 25)), 2),
        "voiced_frames": int(voiced.size),
        "voiced_fraction": round(voiced.size / max(1, total), 3),
        "dominant_octave": dom,
        "frames_per_octave": {str(k): v for k, v in oct_hits.items()},
    }


def spectral_stats(x, sr):
    """Centroid, spread, flatness, rolloff from the power spectrum."""
    if len(x) == 0:
        return {}
    n_fft = 2048
    win = np.hanning(n_fft)
    hops = range(0, max(1, len(x) - n_fft), n_fft // 2)
    cents, spreads, flat, roll = [], [], [], []
    for s in hops:
        seg = x[s:s + n_fft] * win
        if len(seg) < n_fft:
            break
        S = np.abs(np.fft.rfft(seg)) ** 2
        if S.sum() <= 0:
            continue
        freqs = np.fft.rfftfreq(n_fft, 1.0 / sr)
        p = S / S.sum()
        cents.append(float((freqs * p).sum()))
        spreads.append(float(np.sqrt(((freqs - (freqs * p).sum()) ** 2 * p).sum())))
        flat.append(float(np.exp(np.mean(np.log(S + 1e-12)))
                         / (np.mean(S) + 1e-12)))
        c = np.cumsum(p)
        roll.append(float(freqs[int(np.searchsorted(c, 0.85))]))
    if not cents:
        return {}
    return {
        "spectral_centroid_hz": round(float(np.median(cents)), 2),
        "spectral_spread_hz": round(float(np.median(spreads)), 2),
        "spectral_flatness": round(float(np.median(flat)), 5),
        "spectral_rolloff85_hz": round(float(np.median(roll)), 2),
    }


def analyse(path, **kw):
    """Full fingerprint of a WAV file."""
    x, sr = load_wav(path)
    out = {
        "path": path,
        "sample_rate": sr,
        "duration_s": round(len(x) / sr, 3),
        "peak": round(float(np.max(np.abs(x))), 5) if len(x) else 0.0,
        "rms": round(float(np.sqrt((x ** 2).mean())), 5) if len(x) else 0.0,
    }
    f0 = f0_summary(x, sr, **kw)
    if f0:
        out.update(f0)
    out.update(spectral_stats(x, sr))
    return out


def mel_bands(x, sr, n_mels=40, n_fft=1024, hop=256):
    """Log-mel band energy profile, averaged over frames -- a timbre
    fingerprint that is far more stable than any single scalar."""
    win = np.hanning(n_fft)
    f_sp = 200.0 / 3
    hz = np.linspace(0, sr / 2, n_mels)
    mel = np.log1p(hz / f_sp) / np.log(1 + (sr / 2) / f_sp)
    bins = np.floor((n_fft + 1) * hz / sr).astype(int)
    bins = np.clip(bins, 0, n_fft // 2)
    fb = np.zeros((n_mels, n_fft // 2 + 1))
    for i in range(n_mels):
        lo = bins[i]
        hi = bins[i + 1] + 1 if i + 1 < n_mels else n_fft // 2 + 1
        hi = max(hi, lo + 1)
        fb[i, lo:min(hi, n_fft // 2 + 1)] = 1.0
    fb /= fb.sum(axis=1, keepdims=True) + 1e-9
    n_frames = 1 + max(0, (len(x) - n_fft) // hop)
    out = np.zeros((n_mels, n_frames))
    for t in range(n_frames):
        seg = x[t * hop:t * hop + n_fft] * win
        if len(seg) < n_fft:
            break
        out[:, t] = fb @ (np.abs(np.fft.rfft(seg)) ** 2)
    return np.log(out + 1e-10).mean(axis=1)


def mel_distance(a, b):
    """Normalised RMS distance between two mel band profiles."""
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    n = min(len(a), len(b))
    a, b = a[:n] - a[:n].mean(), b[:n] - b[:n].mean()
    return float(np.sqrt(np.mean((a - b) ** 2)))
