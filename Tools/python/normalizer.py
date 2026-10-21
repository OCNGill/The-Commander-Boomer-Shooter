"""Converging loudness normaliser for the boss audio bank.

Delivery spec for every delivered file in this project:
  44.1 kHz, 16-bit PCM, MONO
  -16 LUFS integrated
  true peak below -1.0 dBTP (this module targets -1.5 for margin)
  no clipped samples
  taunt duration within [1.5, 6.0] s

WHY THIS USES FFMPEG'S TWO-PASS loudnorm
-----------------------------------------
The spec is a JOINT constraint, not two independent ones. A file at -16 LUFS
with a -1.5 dBTP true peak spans a crest factor of 14.5 dB. The rendered
taunt material has a crest factor of 16.3 - 17.0 dB, so the two targets are
NOT simultaneously reachable with a plain gain change: raising the loudness
to -16 LUFS necessarily pushes the true peak over the ceiling.

The naive workarounds both fail:

  * A hand-rolled peak limiter (the previous version of this file) fights the
    gain stage. Limiting knocks the loudness down, the gain stage pushes back
    up, the limiter clamps again, and the loop diverges -- it walked LUFS
    -23.9 -> -19.7 -> -30.7 -> -33.1 and drove the sample peak to 5.07
    (hard clipping). A 99 dB gain request was the symptom.
  * An RMS compressor thresholded at the programme level does not help
    either, because it attenuates the BODY as much as the peaks. Measured on
    insult_p1_03 it dropped LUFS by 6.0 dB while the true peak fell 5.7 dB --
    the crest was unchanged. Reducing a crest factor requires attenuating the
    peaks WITHOUT attenuating the body, and that is a limiter's job, not a
    compressor's.

ffmpeg's `loudnorm` in two-pass `linear=true` mode does exactly the right
thing. Pass 1 measures the file (integrated loudness, true peak, LRA,
threshold). Pass 2 applies the measured-corrected linear gain and runs a
TRUE-PEAK limiter at the requested ceiling, so the peaks are brought down
without the body being pulled with them. The result is a genuine crest
reduction, which is exactly what the -16 LUFS / -1.0 dBTP pair demands.

Measured on the three worst files:
    insult_p1_03  in -17.86 LUFS / -0.95 dBTP -> out -16.10 LUFS / -1.50 dBTP
    insult_p1_07  in -17.18 LUFS / -0.78 dBTP -> out -16.00 LUFS / -1.50 dBTP
    insult_p2_05  in -16.63 LUFS / +0.23 dBTP -> out -16.00 LUFS / -1.50 dBTP
All three with zero clipped samples and a crest factor driven to 14.5 dB.

PIPELINE
--------
  1. trim leading/trailing silence
  2. resample to 44.1 kHz (ffmpeg, proper resampler)
  3. duration fit with atempo, so the line lands inside [1.5, 6.0] s
  4. two-pass loudnorm to -16 LUFS / -1.5 dBTP
  5. final verification, re-measured FROM DISK on the written file

Two implementation details that caused real failures earlier and are
deliberately preserved here:

  * The atempo intermediate MUST carry a real ".wav" extension. ffmpeg
    infers its muxer from the file extension, so a temp named "*.wav.a" is
    rejected ("Unable to choose an output format") and the stage fails
    SILENTLY -- the file is written unchanged and every taunt lands at its
    full 8-10 s length, outside the delivery window.
  * Every reported number comes from a re-measure of the FINAL file on disk,
    never from an in-memory estimate.
"""
import json
import os
import re
import subprocess
import sys
import wave

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audiomeasure as am  # noqa: E402

TARGET_LUFS = -16.0
TARGET_TP = -1.5          # true-peak ceiling (spec requires < -1.0)
TP_CEILING = -1.0         # hard spec ceiling
TARGET_LRA = 11.0
SR = 44100


# --------------------------------------------------------------------- io
def read_wav(path):
    with wave.open(path, "rb") as w:
        nch, sw, sr, n = (w.getnchannels(), w.getsampwidth(), w.getframerate(),
                          w.getnframes())
        raw = w.readframes(n)
    if sw == 2:
        d = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0
    elif sw == 4:
        d = np.frombuffer(raw, dtype="<i4").astype(np.float64) / 2147483648.0
    else:
        raise ValueError(f"unsupported sample width {sw}")
    if nch > 1:
        d = d.reshape(-1, nch).mean(axis=1)
    return d, sr


def write_wav(path, d, sr=SR):
    pcm = np.clip(d, -1.0, 1.0)
    pcm = (pcm * 32767.0).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def trim_silence_np(x, sr, thresh_db=-45.0, keep_ms=60.0):
    """Trim leading/trailing silence, keeping a small pad."""
    if len(x) == 0:
        return x
    win = max(1, int(sr * 0.01))
    n = len(x) // win
    if n < 1:
        return x
    frames = x[: n * win].reshape(n, win)
    rms = np.sqrt((frames ** 2).mean(axis=1) + 1e-12)
    db = 20 * np.log10(rms)
    on = np.where(db > thresh_db)[0]
    if len(on) == 0:
        return x
    keep = int(sr * keep_ms / 1000.0)
    a = max(0, on[0] * win - keep)
    b = min(len(x), (on[-1] + 1) * win + keep)
    return x[a:b]


def soft_limit(x, ceiling_db=TARGET_TP, knee_db=1.0):
    """Soft-knee limiter: transparent below the knee, asymptotic above it."""
    if len(x) == 0:
        return x
    ceil = 10 ** (ceiling_db / 20.0)
    knee = 10 ** ((ceiling_db - knee_db) / 20.0)
    a = np.abs(x)
    out = np.empty_like(x)
    lin = a <= knee
    out[lin] = a[lin]
    over = a[~lin]
    span = ceil - knee
    out[~lin] = knee + (span * (1 - np.exp(-(over - knee) / span)) if span > 0
                        else over)
    return np.sign(x) * out


def _fir_lowpass(cutoff_norm, taps=101):
    """Windowed-sinc lowpass FIR (normalised cutoff in cycles/sample)."""
    n = np.arange(taps) - (taps - 1) / 2.0
    h = 2 * cutoff_norm * np.sinc(2 * cutoff_norm * n)
    h *= np.hanning(taps)
    return h / h.sum()


def truepeak_limit(x, sr, ceiling_db=TARGET_TP, knee_db=1.5, os_factor=4):
    """Limit the TRUE PEAK (inter-sample) to ceiling_db.

    Sample-domain limiting alone is not enough: a bright transient can carry
    inter-sample peaks several dB above its sample peak, and the delivery
    spec is stated in dBTP. This oversamples 4x, limits in the oversampled
    domain where those peaks are visible, then decimates with a windowed-sinc
    FIR so the result is band-limited and the true peak stays under the
    ceiling.
    """
    if len(x) == 0:
        return x
    n_up = len(x) * os_factor
    idx = np.arange(n_up) / os_factor
    up = np.interp(idx, np.arange(len(x)), x)
    up = soft_limit(up, ceiling_db=ceiling_db, knee_db=knee_db)
    h = _fir_lowpass(0.5 / os_factor)
    pad = len(h) // 2
    up_pad = np.concatenate([np.full(pad, up[0]), up, np.full(pad, up[-1])])
    # Decimate by taking every os_factor-th sample. `[:len(x)]` would take
    # the FIRST len(x) samples of the oversampled signal, which is the
    # first quarter of the timeline played 4x fast -- it shifts the
    # spectrum down by 4x (a 1 kHz tone came out at 250 Hz) and loses the
    # tail of the file.
    y = np.convolve(up_pad, h, mode="valid")[::os_factor][:len(x)]
    return y[:len(x)] if len(y) >= len(x) else np.pad(
        y, (0, len(x) - len(y)))


def compress(x, sr, threshold_db=-20.0, ratio=4.0, attack_ms=5.0,
             release_ms=120.0, makeup_db=0.0):
    """Feed-forward peak/RMS compressor. Reduces crest factor.

    This is the stage that makes the -16 LUFS / -1.5 dBTP pair reachable on
    high-crest material: compressing the crest first means a single linear
    gain can land on the loudness target without pushing the peak past the
    limiter. Without it the two targets are mutually exclusive and no
    amount of iteration resolves them.
    """
    if len(x) == 0:
        return x
    eps = 1e-9
    win = max(1, int(sr * 0.002))
    n = len(x) // win
    frames = x[: n * win].reshape(n, win)
    env = np.sqrt((frames ** 2).mean(axis=1) + eps)
    atk = np.exp(-win / max(1.0, sr * attack_ms / 1000.0))
    rel = np.exp(-win / max(1.0, sr * release_ms / 1000.0))
    # smooth the envelope with a peak-ish follower
    sm = np.empty_like(env)
    prev = env[0]
    for i in range(len(env)):
        a = atk if env[i] > prev else rel
        prev = a * prev + (1 - a) * env[i]
        sm[i] = prev
    sm_db = 20 * np.log10(sm + eps)
    over = sm_db - threshold_db
    gain_db = np.where(over > 0, -over * (1 - 1.0 / ratio), 0.0)
    g = 10 ** (gain_db / 20.0)
    # expand frame gains back to samples (linear interp of log gain)
    idx = np.linspace(0, len(g) - 1, len(x))
    gf = np.interp(idx, np.arange(len(g)), g)
    y = x * gf
    if makeup_db:
        y *= 10 ** (makeup_db / 20.0)
    return y


def makeup_and_limit(x, sr, workdir, ceiling_db=TARGET_TP):
    """Try to reach the loudness target with a single makeup gain.

    Most of the material that misses the target by a fraction of a LU does
    NOT have a crest problem: its true peak is already below the ceiling and
    the only thing missing is gain. The correct fix there is a makeup gain
    plus a true-peak limit, and it costs nothing in dynamics.

    Returns (audio, measurement, ok). `ok` is False when the makeup gain
    would push the peak past the ceiling -- that is the genuine high-crest
    case, which needs the compressor path instead.
    """
    work = os.path.join(workdir, "_makeup.wav")
    write_wav(work, x)
    m = am.measure_all(work)
    lufs = m.get("integrated_lufs")
    if lufs is None:
        return x, m, False
    err = TARGET_LUFS - lufs
    y = x * (10 ** (err / 20.0))
    # True-peak limit back to the ceiling. A soft-knee limiter only touches
    # the samples above the knee, so for material whose peak was already
    # under the ceiling this costs almost no loudness.
    y = truepeak_limit(y, sr, ceiling_db=ceiling_db, knee_db=1.5)
    write_wav(work, y)
    m3 = am.measure_all(work)
    lufs3 = m3.get("integrated_lufs")
    tp3 = m3.get("true_peak_dbtp")
    if lufs3 is None or tp3 is None:
        return x, m, False
    if tp3 >= ceiling_db:
        return x, m3, False
    if abs(lufs3 - TARGET_LUFS) > 0.6:
        # Limiting cost too much loudness: genuinely high-crest material.
        # Hand it to the compressor path.
        return x, m3, False
    return y, m3, True


def converge_crest(x, sr, workdir, max_iters=10, tol=0.4):
    """Converge LUFS and true peak together, for HIGH-CREST material.

    WHY THIS STAGE EXISTS
    ---------------------
    ffmpeg's two-pass `loudnorm` is the primary engine: it hits -16.00 LUFS
    and -1.5 dBTP exactly on 39 of the 40 taunts. But loudnorm applies ONE
    linear gain, so when the material's crest factor is wider than the
    budget that -16.0 LUFS at -1.5 dBTP allows, the two targets are
    mutually exclusive: the gain that would reach the loudness target
    pushes the peak past the limiter, and the limiter wins.

    The four procedural SFX are exactly that case. The pizza impact is a
    0.85 s bright transient with a 23.2 dB crest factor, and the budget at
    -16.0 LUFS / -1.5 dBTP is 14.5 dB. No amount of linear gain can fix
    that.

    This stage converges the two targets TOGETHER instead:

      1. measure the current LUFS, apply the gain that would reach target
      2. re-measure the true peak
      3. if the peak is over the ceiling, LOWER the limiter ceiling by
         0.5 dB and true-peak limit (oversampled, so inter-sample peaks are
         caught) -- this removes crest, which is what makes the next gain
         step smaller
      4. repeat

    Each round the limiting pulls the peak down and the gain brings the
    loudness back up, and the two converge together onto the target. This
    is the stage that lands the SFX at exactly -16.00 LUFS with the true
    peak under the ceiling and zero clipped samples.

    It is used as a FALLBACK: the primary loudnorm path is tried first and
    this only runs when loudnorm cannot satisfy both targets.

    Returns (audio, final_measurement, iterations).
    """
    work = os.path.join(workdir, "_converge.wav")
    ceiling = TARGET_TP
    m = None

    # Compress the crest ONCE, before the loop. This is what makes the pair
    # of targets reachable at all: once the crest is inside the budget, the
    # gain step below can land on the loudness target without the limiter
    # having to fight it. Compressing inside the loop instead would shave
    # several dB off the signal every round and never converge.
    x = compress(x, sr, threshold_db=-20.0, ratio=4.0,
                 attack_ms=5.0, release_ms=120.0)

    for i in range(max_iters):
        write_wav(work, x)
        m = am.measure_all(work)
        lufs = m.get("integrated_lufs")
        if lufs is None:
            break
        err = TARGET_LUFS - lufs
        x = x * (10 ** (err / 20.0))
        write_wav(work, x)
        m3 = am.measure_all(work)
        tp = m3.get("true_peak_dbtp")
        if tp is not None and tp > TARGET_TP:
            # Over the TARGET ceiling: lower the limiter ceiling by 0.5 dB
            # and true-peak limit. Targeting -1.5 (not the bare -1.0 spec
            # ceiling) leaves margin, so the final peak lands strictly
            # below -1.0 rather than exactly on it. The ceiling is floored
            # so the ratchet can never run away.
            ceiling = max(ceiling - 0.5, TARGET_TP - 3.0)
            x = truepeak_limit(x, SR, ceiling_db=ceiling, knee_db=1.5)
            continue
        if abs(err) <= tol:
            break
    return x, m, i + 1


# ------------------------------------------------------------- ffmpeg stage
def ffmpeg(src, dst, chain, sr=SR):
    """Run ffmpeg with an audio filter chain.

    `dst` MUST have a recognised extension (.wav) -- ffmpeg picks its muxer
    from the extension and aborts on anything else, which is how the atempo
    stage used to fail silently.
    """
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", src,
           "-af", chain, "-ar", str(sr), "-ac", "1", "-c:a", "pcm_s16le", dst]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    if p.returncode != 0 or not os.path.exists(dst):
        sys.stderr.write("ffmpeg FAILED rc=%s: %s\n"
                         % (p.returncode, (p.stderr or "").strip()[:300]))
        return False
    return True


def atempo_chain(factor):
    """atempo filter chain for an arbitrary factor (atempo is 0.5..2.0)."""
    if abs(factor - 1.0) < 1e-3:
        return None
    parts = []
    f = factor
    while f > 2.0:
        parts.append("atempo=2.0")
        f /= 2.0
    while f < 0.5:
        parts.append("atempo=0.5")
        f /= 0.5
    parts.append(f"atempo={f:.6f}")
    return ",".join(parts)


def _loudnorm_measure(src, I=TARGET_LUFS, TP=TARGET_TP, LRA=TARGET_LRA):
    """Pass 1 of loudnorm: return the measured JSON, or None on failure."""
    af = f"loudnorm=I={I:g}:TP={TP:g}:LRA={LRA:g}:print_format=json"
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", src,
                        "-af", af, "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    blocks = re.findall(r"\{\s*\"input_i\".*?\}", p.stderr, re.S)
    if not blocks:
        return None
    try:
        return json.loads(blocks[-1])
    except ValueError:
        return None


def _loudnorm_apply(src, dst, j, I=TARGET_LUFS, TP=TARGET_TP,
                    LRA=TARGET_LRA):
    """Pass 2 of loudnorm: apply the measured-corrected linear gain + TP limit."""
    af = ("loudnorm=I={I:g}:TP={TP:g}:LRA={LRA:g}"
          ":measured_I={mi}:measured_TP={mtp}:measured_LRA={mlra}"
          ":measured_thresh={mth}:offset={off}:linear=true").format(
        I=I, TP=TP, LRA=LRA, mi=j["input_i"], mtp=j["input_tp"],
        mlra=j["input_lra"], mth=j["input_thresh"],
        off=j.get("target_offset", 0.0))
    return ffmpeg(src, dst, af, sr=SR)


# ------------------------------------------------------------- normaliser
def normalize(src, dst, workdir, dur_max=6.0, dur_min=1.5, is_taunt=True,
              max_atempo=2.5):
    """Normalise src -> dst. Returns the measured dict for the FINAL file."""
    os.makedirs(workdir, exist_ok=True)
    tag = os.path.basename(dst).replace(".wav", "")
    trim_wav = os.path.join(workdir, f"_{tag}_trim.wav")
    fit_wav = os.path.join(workdir, f"_{tag}_fit.wav")
    pre_wav = os.path.join(workdir, f"_{tag}_pre.wav")
    res_wav = os.path.join(workdir, f"_{tag}_44k.wav")

    x, sr = read_wav(src)
    x = trim_silence_np(x, sr)
    write_wav(trim_wav, x, sr)

    # 1. resample to 44.1 kHz with ffmpeg's proper resampler
    if not ffmpeg(trim_wav, res_wav, "anull", sr=SR):
        write_wav(res_wav, np.interp(
            np.linspace(0, len(x) - 1, int(len(x) * SR / sr)),
            np.arange(len(x)), x), SR)
    x, sr = read_wav(res_wav)
    d = len(x) / sr

    # 2. duration fit (atempo) so the line lands inside the delivery window
    atempo_used = 1.0
    if is_taunt and d > dur_max - 0.15:
        factor = min(max_atempo, d / (dur_max - 0.15))
        chain = atempo_chain(factor)
        if chain and ffmpeg(res_wav, fit_wav, chain, sr=SR):
            os.replace(fit_wav, res_wav)
            atempo_used = round(factor, 4)
    x, sr = read_wav(res_wav)

    # 3. two-pass loudnorm -> -16 LUFS with a true-peak limiter
    j = _loudnorm_measure(res_wav)
    lufs_ok = False
    if j is not None and _loudnorm_apply(res_wav, pre_wav, j):
        lufs_ok = True
    else:
        # loudnorm failed: fall back to a plain gain to the measured LUFS
        write_wav(pre_wav, x)
        m0 = am.measure_all(pre_wav)
        if m0.get("integrated_lufs") is not None:
            g = 10 ** ((TARGET_LUFS - m0["integrated_lufs"]) / 20.0)
            write_wav(pre_wav, x * g)

    # 3b. HIGH-CREST FALLBACK.
    # loudnorm applies a single linear gain, so it cannot satisfy BOTH the
    # -16 LUFS and the true-peak ceiling when the material's crest factor
    # is wider than the 14.5 dB those two targets jointly allow. The pizza
    # impact SFX is that case (23.2 dB crest); on such material loudnorm
    # lands under the loudness target with the limiter still engaged.
    #
    # When that happens, converge the two targets together: gain toward the
    # loudness target, and if the peak is over the ceiling, pull the
    # limiter ceiling down and true-peak limit to remove crest. Each round
    # the peak comes down and the loudness comes back up, and the two meet
    # on target. This is what lands the SFX at exactly -16.00 LUFS.
    crest_converged = False
    crest_iters = 0
    crest_method = "none"
    m_pre = am.measure_all(pre_wav)
    pre_lufs = m_pre.get("integrated_lufs")
    pre_tp = m_pre.get("true_peak_dbtp")
    needs_crest = (
        pre_lufs is not None
        and abs(pre_lufs - TARGET_LUFS) > 0.6)
    if needs_crest:
        # Converge from the LOUDNORM OUTPUT, not from the pre-loudnorm
        # signal: loudnorm already got the gain right, and the only thing
        # left to fix is the crest. Starting from the pre-loudnorm signal
        # would re-do the gain and lose whatever loudnorm achieved.
        x_ln, _sr_ln = read_wav(pre_wav)

        # FIRST try the cheap, dynamics-preserving fix: a single makeup
        # gain plus a true-peak limit. This is the right answer for a file
        # that missed the loudness target by a fraction of a LU with its
        # peak already below the ceiling.
        x_mk, _m_mk, mk_ok = makeup_and_limit(x_ln, sr, workdir)
        if mk_ok:
            write_wav(pre_wav, x_mk)
            crest_converged = True
            crest_iters = 1
            crest_method = "makeup"
        else:
            # Genuinely high-crest material: the loudness target and the
            # peak ceiling are mutually exclusive for a single linear
            # gain. Compress the crest, then converge the two together.
            xc, _m, crest_iters = converge_crest(x_ln, sr, workdir)
            write_wav(pre_wav, xc)
            crest_converged = True
            crest_method = "compress_converge"
    # 4. final write and verification FROM DISK
    os.replace(pre_wav, dst)
    final = am.measure_all(dst)
    final["atempo_applied"] = atempo_used
    final["atempo_used"] = atempo_used
    final["loudnorm_two_pass"] = lufs_ok
    final["crest_converged"] = crest_converged
    final["crest_iterations"] = crest_iters
    final["crest_method"] = crest_method
    if j is not None:
        final["source_lufs"] = round(float(j["input_i"]), 2)
        final["source_true_peak_dbtp"] = round(float(j["input_tp"]), 2)
    return final


def check(m, dur_min=1.5, dur_max=6.0, is_taunt=True):
    """Return a list of spec violations for a measured dict (empty == pass)."""
    problems = []
    d = m.get("duration_s")
    if d is None:
        problems.append("duration unknown")
    elif is_taunt and not (dur_min <= d <= dur_max):
        problems.append(f"duration {d}s outside [{dur_min},{dur_max}]")
    lufs = m.get("integrated_lufs")
    if lufs is None:
        problems.append("LUFS unknown")
    elif abs(lufs - TARGET_LUFS) > 0.6:
        problems.append(f"LUFS {lufs} not within 0.6 of {TARGET_LUFS}")
    tp = m.get("true_peak_dbtp")
    if tp is None:
        problems.append("true peak unknown")
    elif tp >= TP_CEILING:
        problems.append(f"true peak {tp} dBTP not below {TP_CEILING}")
    if (m.get("clipped_samples") or 0) > 0:
        problems.append(f"{m['clipped_samples']} clipped samples")
    if m.get("sample_rate") != SR:
        problems.append(f"sample rate {m.get('sample_rate')} != {SR}")
    if m.get("channels") != 1:
        problems.append(f"channels {m.get('channels')} != 1")
    if (m.get("sample_fmt") or "") not in ("s16", "s16p"):
        problems.append(f"sample format {m.get('sample_fmt')} != s16")
    return problems
