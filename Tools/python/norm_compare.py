"""Compare normalization strategies that must hit BOTH -16 LUFS and TP < -1.0 dBTP."""
import json
import os
import re
import subprocess
import sys

F = sys.argv[1]
OUTDIR = sys.argv[2]
os.makedirs(OUTDIR, exist_ok=True)


def run(c):
    return subprocess.run(c, capture_output=True, text=True, encoding="utf-8",
                          errors="replace")


def loudnorm_json(path):
    p = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af",
             "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"])
    m = re.findall(r"\{\s*\"input_i\".*?\}", p.stderr, re.S)
    return json.loads(m[0]) if m else None


def ebur(path):
    p = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true",
             "-f", "null", "-"])
    i = re.search(r"I:\s*(-?[\d.]+)\s*LUFS", p.stderr)
    pk = re.findall(r"Peak:\s*(-?[\d.]+)\s*dBFS", p.stderr)
    return (float(i.group(1)) if i else None, float(pk[-1]) if pk else None)


def strategy_dynamic(src, dst):
    """Two-pass loudnorm with linear=false (full dynamic normaliser)."""
    a = loudnorm_json(src)
    if not a:
        return False
    filt = (f"loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={a['input_i']}:"
            f"measured_TP={a['input_tp']}:measured_LRA={a['input_lra']}:"
            f"measured_thresh={a['input_thresh']}:linear=false:print_format=summary")
    r = run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", src, "-af", filt,
             "-ar", "44100", "-ac", "1", "-c:a", "pcm_s16le", dst])
    return r.returncode == 0 and os.path.exists(dst)


def strategy_compress_gain_limit(src, dst, passes=4):
    """Compress -> gain to target -> brickwall limit; iterate on measured LUFS."""
    cur = src
    tmp = dst + ".iter.wav"
    for _ in range(passes):
        a = loudnorm_json(cur)
        if not a:
            return False
        try:
            cur_i = float(a["input_i"])
        except (TypeError, ValueError):
            return False
        gain = -16.0 - cur_i
        if abs(gain) < 0.15:
            break
        # gentle compression to cut crest factor, then gain, then TP limit
        chain = (f"acompressor=threshold=-24dB:ratio=3:attack=5:release=120:makeup=1:"
                 f"alimiter=limit=0.891:attack=5:release=50:level=disabled:"
                 f"volume={gain:.2f}dB:alimiter=limit=0.891:attack=2:release=50:level=disabled")
        r = run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", cur, "-af", chain,
                 "-ar", "44100", "-ac", "1", "-c:a", "pcm_s16le", tmp])
        if r.returncode != 0:
            return False
        cur = tmp
    if cur != dst:
        if os.path.exists(dst):
            os.remove(dst)
        os.replace(cur, dst)
    return True


def report(name, path):
    ln = loudnorm_json(path) or {}
    i, tp = ebur(path)
    print(f"{name:22s} LUFS={i}  TP={tp}  (loudnorm out_i={ln.get('output_i')})")


for strat, fn in (("dynamic", strategy_dynamic), ("compress+limit", strategy_compress_gain_limit)):
    dst = os.path.join(OUTDIR, f"{strat}.wav")
    if fn(F, dst):
        report(strat, dst)
    else:
        print(f"{strat:22s} FAILED")
