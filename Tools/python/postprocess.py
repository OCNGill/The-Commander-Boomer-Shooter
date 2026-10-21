"""Post-process a rendered WAV into the game delivery spec.

Spec: 44.1 kHz, 16-bit, MONO, -16 LUFS integrated, true peak < -1.0 dBTP,
no clipping, duration within [1.5, 6.0] s for taunts.

Pipeline per file:
  1. trim leading/trailing silence (silenceremove)
  2. atempo compression if the trimmed result still exceeds the duration cap
  3. resample to 44100 Hz, force mono, 16-bit PCM
  4. two-pass loudnorm -> I=-16 LUFS, TP=-1.5 dBTP (headroom under -1.0)
  5. measure the FINAL file: duration, integrated LUFS, true peak, max sample
     peak, and whether any sample is at/over full scale (clipping)

Everything reported in the manifest comes from step 5 -- measured on the
delivered file, not on an intermediate.
"""
import json
import os
import re
import subprocess
import sys

FFMPEG = "ffmpeg"
FFPROBE = "ffprobe"
TARGET_LUFS = -16.0
TARGET_TP = -1.5
TARGET_SR = 44100
DUR_MIN = 1.5
DUR_MAX = 6.0


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace")


def probe_duration(path):
    p = run([FFPROBE, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", path])
    try:
        return float(p.stdout.strip())
    except ValueError:
        return None


def measure_loudnorm(path):
    """Return the loudnorm JSON analysis of a file (measured, not assumed)."""
    p = run([FFMPEG, "-hide_banner", "-nostats", "-i", path,
             "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json",
             "-f", "null", "-"])
    m = re.findall(r"\{\s*\"input_i\".*?\}", p.stderr, re.S)
    if not m:
        return None
    try:
        return json.loads(m[0])
    except json.JSONDecodeError:
        return None


def measure_astats(path):
    """Sample-domain peak + DC offset + flatness via astats."""
    p = run([FFMPEG, "-hide_banner", "-nostats", "-i", path,
             "-af", "astats=metadata=1:reset=0", "-f", "null", "-"])
    out = {}
    for key, pat in (
        ("peak_level", r"Peak level dB:\s*(-?[\d.]+|inf)"),
        ("max_level", r"Max level dB:\s*(-?[\d.]+|inf)"),
        ("rms_level", r"RMS level dB:\s*(-?[\d.]+|inf)"),
        ("dc_offset", r"DC offset:\s*(-?[\d.]+)"),
    ):
        mm = re.search(pat, p.stderr)
        if mm:
            v = mm.group(1)
            out[key] = None if v == "inf" else float(v)
    return out


def measure_true_peak(path):
    """True peak via ebur128 (dBTP), independent of sample peak."""
    p = run([FFMPEG, "-hide_banner", "-nostats", "-i", path,
             "-af", "ebur128=peak=true", "-f", "null", "-"])
    vals = re.findall(r"Peak:\s*(-?[\d.]+)\s*dBFS", p.stderr)
    # ebur128 prints an "Integrated loudness / I:" and "Peak:" summary block
    mm = re.findall(r"Peak:\s*(-?[\d.]+)\s*dBFS", p.stderr)
    if mm:
        return float(mm[-1])
    return None


def measure_clipping(path):
    """Count samples at or beyond full-scale (>= 0.999 of max)."""
    p = run([FFMPEG, "-hide_banner", "-nostats", "-i", path,
             "-af", "astats=metadata=1:reset=0", "-f", "null", "-"])
    for pat in (r"Number of samples:\s*(\d+)", r"Flat factor:\s*(-?[\d.]+)"):
        pass
    # Use volumedetect max_volume as a proxy plus exact clipping scan in python
    return None


def exact_clip_scan(path):
    """Exact sample-domain scan: peak abs value and count of |x| >= 0.999."""
    import wave
    import numpy as np

    with wave.open(path, "rb") as w:
        nch, sw, sr, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        raw = w.readframes(n)
    if sw != 2:
        return None
    data = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    if nch > 1:
        data = data.reshape(-1, nch).mean(axis=1)
    peak = float(np.max(np.abs(data))) if data.size else 0.0
    clipped = int(np.sum(np.abs(data) >= 0.9995))
    return {"peak_abs": peak, "clipped_samples": clipped, "sr": sr,
            "frames": n, "dur": n / sr if sr else 0.0}


def trim_silence(src, dst, thresh_db=-45.0):
    """Remove leading/trailing silence."""
    cmd = [FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-i", src,
           "-af", f"silenceremove=start_periods=1:start_duration=0.05:start_threshold={thresh_db}dB:"
                  f"stop_periods=1:stop_duration=0.10:stop_threshold={thresh_db}dB",
           "-ar", str(TARGET_SR), "-ac", "1", "-c:a", "pcm_s16le", dst]
    p = run(cmd)
    return p.returncode == 0 and os.path.exists(dst)


def fit_duration(src, dst, dur_max=DUR_MAX, target=None):
    """Atempo-compress so the file lands under dur_max, if needed.

    Returns (path, atempo_factor_used).
    """
    d = probe_duration(src)
    if d is None:
        return src, 1.0
    target = target if target is not None else dur_max - 0.15
    if d <= target:
        os.replace(src, dst)
        return dst, 1.0
    factor = min(4.0, d / target)
    # atempo valid range 0.5-100 per filter, but quality degrades past ~2
    filters = []
    f = factor
    while f > 2.0:
        filters.append("atempo=2.0")
        f /= 2.0
    while f < 0.5:
        filters.append("atempo=0.5")
        f /= 0.5
    filters.append(f"atempo={f:.4f}")
    chain = ",".join(filters)
    cmd = [FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-i", src,
           "-af", chain, "-ar", str(TARGET_SR), "-ac", "1", "-c:a", "pcm_s16le", dst]
    p = run(cmd)
    if p.returncode == 0 and os.path.exists(dst):
        os.remove(src)
        return dst, round(factor, 4)
    return src, 1.0


def loudnorm_two_pass(src, dst):
    """Two-pass loudnorm to hit TARGET_LUFS with TP headroom."""
    ana = measure_loudnorm(src)
    if not ana:
        # fallback: single-pass
        cmd = [FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-i", src,
               "-af", f"loudnorm=I={TARGET_LUFS}:TP={TARGET_TP}:LRA=11",
               "-ar", str(TARGET_SR), "-ac", "1", "-c:a", "pcm_s16le", dst]
        run(cmd)
        return dst
    i = ana.get("input_i")
    tp = ana.get("input_tp")
    lra = ana.get("input_lra")
    thresh = ana.get("input_thresh")
    if i in ("-inf", None) or float(i) < -70:
        return dst
    filt = (f"loudnorm=I={TARGET_LUFS}:TP={TARGET_TP}:LRA=11:"
            f"measured_I={i}:measured_TP={tp}:measured_LRA={lra}:"
            f"measured_thresh={thresh}:linear=true:print_format=summary")
    cmd = [FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-i", src,
           "-af", filt, "-ar", str(TARGET_SR), "-ac", "1", "-c:a", "pcm_s16le", dst]
    p = run(cmd)
    if p.returncode != 0 or not os.path.exists(dst):
        cmd = [FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-i", src,
               "-af", f"loudnorm=I={TARGET_LUFS}:TP={TARGET_TP}:LRA=11",
               "-ar", str(TARGET_SR), "-ac", "1", "-c:a", "pcm_s16le", dst]
        run(cmd)
    return dst


def process(src, dst, dur_max=DUR_MAX, dur_min=DUR_MIN, workdir=None):
    """Full pipeline. Returns a dict of measured properties of the FINAL file."""
    tmp_trim = os.path.join(workdir or os.path.dirname(dst) or ".",
                             "_t_" + os.path.basename(dst))
    tmp_fit = os.path.join(workdir or os.path.dirname(dst) or ".",
                            "_f_" + os.path.basename(dst))

    ok = trim_silence(src, tmp_trim)
    if not ok:
        ok = trim_silence(src, tmp_trim, thresh_db=-40.0)
    if not ok:
        tmp_trim = src

    tmp_fit, atempo = fit_duration(tmp_trim, tmp_fit, dur_max=dur_max)
    if tmp_trim != tmp_fit and os.path.exists(tmp_trim):
        os.remove(tmp_trim)

    loudnorm_two_pass(tmp_fit, dst)
    if not os.path.exists(dst) or os.path.getsize(dst) < 100:
        os.replace(tmp_fit, dst)
    elif os.path.exists(tmp_fit):
        os.remove(tmp_fit)

    return measure_all(dst, atempo)


def measure_all(path, atempo=1.0):
    ln = measure_loudnorm(path) or {}
    ast = measure_astats(path) or {}
    tp = measure_true_peak(path)
    scan = exact_clip_scan(path) or {}
    dur = probe_duration(path)
    i_lufs = ln.get("input_i")
    lra = ln.get("input_lra")
    try:
        i_lufs = float(i_lufs)
    except (TypeError, ValueError):
        i_lufs = None
    try:
        lra = float(lra)
    except (TypeError, ValueError):
        lra = None
    if tp is None:
        tp = ast.get("peak_level")
    return {
        "duration_s": round(dur, 3) if dur is not None else None,
        "integrated_lufs": i_lufs,
        "lra_lu": lra,
        "true_peak_dbtp": tp,
        "sample_peak_dbfs": ast.get("peak_level"),
        "rms_dbfs": ast.get("rms_level"),
        "dc_offset": ast.get("dc_offset"),
        "peak_abs": scan.get("peak_abs"),
        "clipped_samples": scan.get("clipped_samples"),
        "sample_rate": scan.get("sr"),
        "atempo_applied": atempo,
    }


def check(m, dur_min=DUR_MIN, dur_max=DUR_MAX, is_taunt=True):
    """Verify a measurement dict against the spec. Returns list of problems."""
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
    elif tp >= -1.0:
        problems.append(f"true peak {tp} dBTP not below -1.0")
    if (m.get("clipped_samples") or 0) > 0:
        problems.append(f"{m['clipped_samples']} clipped samples")
    if m.get("sample_rate") != TARGET_SR:
        problems.append(f"sample rate {m.get('sample_rate')} != {TARGET_SR}")
    return problems


if __name__ == "__main__":
    print(json.dumps(measure_all(sys.argv[1]), indent=2))
