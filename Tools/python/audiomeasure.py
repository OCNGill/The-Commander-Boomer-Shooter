"""Accurate ffmpeg-based measurement helpers.

ebur128 prints per-frame progress lines whose integrated value starts at
-70.0 LUFS, plus a final summary block. Always read the LAST occurrence
(the summary) -- reading the first yields the -70.0 placeholder.
"""
import re
import subprocess


def _run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace")


def ebur128(path):
    """Return {integrated_lufs, true_peak_dbtp, lra_lu, threshold} from the
    ebur128 summary block (last occurrence of each)."""
    p = _run(["ffmpeg", "-hide_banner", "-nostats", "-i", path,
              "-af", "ebur128=peak=true", "-f", "null", "-"])
    err = p.stderr
    # summary block looks like:  "    I:         -19.9 LUFS"
    i_vals = re.findall(r"^\s*I:\s*(-?[\d.]+)\s*LUFS", err, re.M)
    pk_vals = re.findall(r"^\s*Peak:\s*(-?[\d.]+)\s*dBFS", err, re.M)
    lra_vals = re.findall(r"^\s*LRA:\s*(-?[\d.]+)\s*LU", err, re.M)
    thr_vals = re.findall(r"^\s*Threshold:\s*(-?[\d.]+)\s*LUFS", err, re.M)

    def last(vals):
        if not vals:
            return None
        try:
            return float(vals[-1])
        except ValueError:
            return None

    return {
        "integrated_lufs": last(i_vals),
        "true_peak_dbtp": last(pk_vals),
        "lra_lu": last(lra_vals),
        "threshold": last(thr_vals),
    }


def astats(path):
    """Sample-domain peak / RMS / DC from astats."""
    p = _run(["ffmpeg", "-hide_banner", "-nostats", "-i", path,
              "-af", "astats=metadata=1:reset=0", "-f", "null", "-"])
    err = p.stderr
    out = {}
    for key, pat in (
        ("peak_level_dbfs", r"Peak level dB:\s*(-?[\d.]+|inf)"),
        ("rms_level_dbfs", r"RMS level dB:\s*(-?[\d.]+|inf)"),
        ("dc_offset", r"DC offset:\s*(-?[\d.]+)"),
    ):
        m = re.search(pat, err)
        if m:
            v = m.group(1)
            out[key] = None if v == "inf" else float(v)
    return out


def probe(path):
    """Duration / sample rate / channels / codec via ffprobe."""
    p = _run(["ffprobe", "-v", "error", "-show_entries",
              "format=duration:stream=sample_rate,channels,codec_name,sample_fmt",
              "-of", "json", path])
    import json as _json
    try:
        d = _json.loads(p.stdout)
    except Exception:  # noqa: BLE001
        return {}
    st = (d.get("streams") or [{}])[0]
    dur = (d.get("format") or {}).get("duration")
    try:
        dur = float(dur)
    except (TypeError, ValueError):
        dur = None
    return {
        "duration_s": dur,
        "sample_rate": int(st["sample_rate"]) if st.get("sample_rate") else None,
        "channels": st.get("channels"),
        "codec": st.get("codec_name"),
        "sample_fmt": st.get("sample_fmt"),
    }


def exact_scan(path):
    """Exact sample-domain scan of a 16-bit PCM wav: peak abs, clipped count."""
    import wave
    import numpy as np

    with wave.open(path, "rb") as w:
        nch, sw, sr, n = (w.getnchannels(), w.getsampwidth(), w.getframerate(),
                          w.getnframes())
        raw = w.readframes(n)
    if sw != 2:
        return {"peak_abs": None, "clipped_samples": None, "sr": sr, "frames": n}
    data = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    if nch > 1:
        data = data.reshape(-1, nch).mean(axis=1)
    return {
        "peak_abs": float(np.max(np.abs(data))) if data.size else 0.0,
        "clipped_samples": int(np.sum(np.abs(data) >= 0.9995)),
        "sr": sr,
        "frames": n,
        "duration_s": n / sr if sr else 0.0,
        "rms_abs": float(np.sqrt(np.mean(data ** 2))) if data.size else 0.0,
    }


def measure_all(path):
    """Full measured property set for a delivered file."""
    e = ebur128(path)
    a = astats(path)
    pr = probe(path)
    sc = exact_scan(path)
    return {
        "duration_s": round(pr.get("duration_s") or sc.get("duration_s") or 0.0, 3),
        "integrated_lufs": e["integrated_lufs"],
        "true_peak_dbtp": e["true_peak_dbtp"],
        "lra_lu": e["lra_lu"],
        "sample_peak_dbfs": a.get("peak_level_dbfs"),
        "rms_level_dbfs": a.get("rms_level_dbfs"),
        "dc_offset": a.get("dc_offset"),
        "peak_abs": sc.get("peak_abs"),
        "clipped_samples": sc.get("clipped_samples"),
        "sample_rate": pr.get("sample_rate") or sc.get("sr"),
        "channels": pr.get("channels"),
        "codec": pr.get("codec"),
        "sample_fmt": pr.get("sample_fmt"),
    }
