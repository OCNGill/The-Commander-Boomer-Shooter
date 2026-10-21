"""Repair a single normalised file that missed the loudness target.

WHY THIS EXISTS
---------------
One taunt, insult_p3_04, came out of the two-pass loudnorm at -16.80 LUFS
against a -16.0 target -- 0.8 LU under -- while its true peak was already
sitting at -1.9 dBTP. That combination is the signature of a GAIN CEILING:
the file's crest factor is 14.9 dB, wider than the 14.5 dB budget that
-16.0 LUFS at -1.5 dBTP allows, so the limiter stopped the pass from
reaching the loudness target.

The audio itself is fine. The SOURCE is fine. This is purely a gain
problem, and it is fixed WITHOUT RE-RENDERING: the TTS render is the
expensive artefact (130-165 s per utterance on a CPU-only F5-TTS service)
and there is no reason to spend that again over a decibel.

THE FIX
-------
Two stages, in this order:

  1. MAKEUP GAIN. The measured shortfall is (target - measured) LUFS, which
     for this file is +0.80 dB. A flat gain moves the whole file toward the
     target and takes the true peak along with it.

  2. TRUE-PEAK LIMIT. The makeup gain pushes the peak up by the same
     amount, so a true-peak limiter is applied afterwards at a ceiling of
     -1.9 dBFS. This restores the peak headroom without touching the
     body, because the limiter only acts on the samples that exceed the
     ceiling.

The order matters. Limiting first and then gaining would just push the
peak back over the ceiling; gaining first and then limiting is the correct
sequence and it lands the file exactly like the other 39.

Measured on insult_p3_04, starting from the loudnorm output (-16.80 LUFS,
-1.9 dBTP):

    +0.8 dB makeup  ->  -16.00 LUFS, -1.10 dBTP
    limit @ -1.9    ->  -16.10 LUFS, -1.60 dBTP, 0 clipped samples

which is inside the delivery spec (true peak < -1.0 dBTP) and matches the
-1.5 dBTP band the other 39 files occupy.

This tool is idempotent and safe to re-run: it re-measures first and does
nothing if the file is already within tolerance.
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audiomeasure as am  # noqa: E402
import normalizer as nz  # noqa: E402

TARGET_LUFS = -16.0
LUFS_TOL = 0.6
TP_CEILING = -1.5          # the band the other 39 files sit in
LIMIT_DBFS = -1.9          # true-peak limiter ceiling for the makeup stage
ALIMITER = ("alimiter=level_in=1:level_out=1:limit=%.6f:attack=5:release=50"
            ":level=false")


def _ff(src, dst, chain):
    r = subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", src,
         "-af", chain, "-ar", "44100", "-ac", "1", "-c:a", "pcm_s16le", dst],
        capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("ffmpeg failed: %s\n%s" % (chain, r.stderr[:400]))


def repair(path, workdir, force=False):
    """Bring one already-normalised file onto the loudness target.

    Returns (measured, actions) where measured is the final measurement
    dict and actions is a list of strings describing what was done.
    """
    os.makedirs(workdir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(path))[0]
    pre = os.path.join(workdir, "_repair_%s_pre.wav" % stem)
    post = os.path.join(workdir, "_repair_%s_post.wav" % stem)
    actions = []

    m = am.measure_all(path)
    shortfall = TARGET_LUFS - m["integrated_lufs"]
    if abs(shortfall) <= LUFS_TOL and not force:
        actions.append("already on target (%.2f LUFS) - no action"
                       % m["integrated_lufs"])
        return m, actions

    if shortfall > 0:
        gain = shortfall
        actions.append("makeup gain %+.2f dB (measured %.2f LUFS, target "
                       "%.1f, shortfall %.2f LU)"
                       % (gain, m["integrated_lufs"], TARGET_LUFS, shortfall))
    else:
        gain = shortfall
        actions.append("trim gain %+.2f dB (measured %.2f LUFS over target)"
                       % (gain, m["integrated_lufs"]))

    # stage 1: makeup gain
    _ff(path, pre, "volume=%.4fdB" % gain)
    m1 = am.measure_all(pre)

    # stage 2: true-peak limit, to restore the headroom the gain consumed
    lim = 10 ** (LIMIT_DBFS / 20.0)
    _ff(pre, post, ALIMITER % lim)
    m2 = am.measure_all(post)

    if m2["clipped_samples"] == 0 and abs(
            m2["integrated_lufs"] - TARGET_LUFS) <= LUFS_TOL \
            and m2["true_peak_dbtp"] < -1.0:
        os.replace(post, path)
        actions.append("limit @ %.1f dBFS -> TP %.2f dBTP, LUFS %.2f"
                       % (LIMIT_DBFS, m2["true_peak_dbtp"],
                          m2["integrated_lufs"]))
        final = am.measure_all(path)
    else:
        # the limit was not enough; fall back to gain-only, which still
        # satisfies the hard spec (< -1.0 dBTP) as long as the peak allows
        if m1["clipped_samples"] == 0 and m1["true_peak_dbtp"] < -1.0:
            os.replace(pre, path)
            actions.append("limit rejected (peak budget); applied gain-only "
                           "-> TP %.2f dBTP, LUFS %.2f"
                           % (m1["true_peak_dbtp"], m1["integrated_lufs"]))
            final = am.measure_all(path)
        else:
            actions.append("REPAIR FAILED: gain-only would exceed the "
                           "true-peak spec (TP %.2f dBTP)"
                           % m1["true_peak_dbtp"])
            final = m
    return final, actions


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else \
        "Content/Audio/Insults/insult_p3_04.wav"
    work = sys.argv[2] if len(sys.argv) > 2 else ".audio_work/norm"
    force = "--force" in sys.argv
    m, acts = repair(target, work, force=force)
    print("FILE: %s" % target)
    for a in acts:
        print("  - %s" % a)
    print("  FINAL: dur=%.3fs LUFS=%.2f TP=%.2f clip=%d sr=%d ch=%d"
          % (m["duration_s"], m["integrated_lufs"], m["true_peak_dbtp"],
             m["clipped_samples"], m["sample_rate"], m["channels"]))
    probs = nz.check(m, 1.5, 6.0, is_taunt=True)
    print("  CHECK: %s" % (probs if probs else "OK - no problems"))
    if probs:
        sys.exit(1)
    print("REPAIR_OK")
