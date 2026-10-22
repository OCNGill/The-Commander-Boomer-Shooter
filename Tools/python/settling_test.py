"""Centroid settling test: does timbre separation between references SETTLE?

Why centroid and not f0
-----------------------
F5-TTS regenerates the output fundamental from its own prosody model, so the
reference's pitch does NOT transfer to the rendered output (the reference
ordering by f0 comes out REVERSED in the output). What transfers is timbre,
and the repo's own estimator for timbre is the power-weighted spectral
centroid (Tools/python/voiceprint.py). So the settling test measures
centroid. See Docs/generated/voice_contract_handover.md section 3.2.

What "settling" means here
--------------------------
The alias group is the control: `spokesman`, `commander` and `hermes` share
one BYTE-IDENTICAL ref.wav, so any spread between their centroid means is
pure sampler noise, not a voice difference. That spread is the ALIAS FLOOR.
A reference is only usefully separable if its centroid mean sits further
from the alias group than the alias group sits from itself.

The test renders N replicates per registered reference of ONE fixed line and
reports, in Hz:
  * the alias floor (spread of the three alias names' means),
  * each distinct reference's distance to the nearest alias mean,
  * the MINIMUM such separation, and whether it clears the floor,
  * the settling curve: floor and separation as replicates are added,
  * the per-render centroid SD, so the floor can be read against the noise
    it is drawn from (a floor far below that SD is a small-sample fluke,
    not a stable floor),
  * the transfer check (brightness transfers, pitch does not), with an
    exact permutation p,
  * a control on the repo's other timbre metric, the log-mel profile
    distance, which is what the manifest's own fingerprint table uses.

All pools are kept WITHIN one session. The service's output for one voice
and one line shifts by tens of Hz between sessions, so pooling renders from
different sessions would fold a session-level offset into the within-name
variance. The earlier n=2 session is therefore reported alongside, as an
independent draw from the same noise, not merged into it.

Nothing here re-renders or alters the delivered bank: the renders go to
.audio_work/settling/ and are scratch measurements of a fixed probe line.

Outputs: .audio_work/settling/settling_verdict.json
Usage:    python Tools/python/settling_test.py [reps] [concurrency]
"""
import itertools
import json
import os
import statistics
import sys
import threading
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import voiceprint as sa  # noqa: E402

URL = "http://10.0.0.42:8020/synth"
REPS = int(sys.argv[1]) if len(sys.argv) > 1 else 6
CONCURRENCY = int(sys.argv[2]) if len(sys.argv) > 2 else 4
TEXT = "Bring him the specimen."
OUT = os.path.join(".audio_work", "settling")
RENDER_DIR = os.path.join(OUT, "renders")
POOL_DIR = os.path.join(".audio_work", "voices")       # an EARLIER session
SWEEP_DIR = os.path.join(".audio_work", "conc_sweep")  # 24 reps, one voice
REFS_DIR = os.path.join(".audio_work", "refs")

REFERENCES = [
    ("spokesman", "machine / default register"),
    ("commander", "pre-existing alias (same ref as spokesman)"),
    ("hermes", "pre-existing alias (same ref as spokesman)"),
    ("harvester", "THE BOSS - phase 1-2"),
    ("harvester_low", "THE BOSS - phase 3, voice coming apart"),
    ("settlement_human", "settlement human voices"),
]
# The three names that share one ref.wav are the noise control, not voices.
ALIAS_GROUP = ("spokesman", "commander", "hermes")
DISTINCT = ("harvester", "harvester_low", "settlement_human")
# The 4 refs with their own audio; the 3 aliases are one audio.
FOUR_REFS = ("spokesman", "harvester", "harvester_low", "settlement_human")
# Recorded on the 2-replicate pool: the alias-floor figure the design lane
# published. The re-measurement is reported alongside it.
HISTORICAL_ALIAS_FLOOR_HZ = 13.05

_lock = threading.Lock()
_next = [0]


def synth(text, ref):
    payload = json.dumps({"text": text, "ref": ref}).encode()
    req = urllib.request.Request(
        URL, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=1800) as r:
        return r.read()


def render_all():
    """Render the missing replicates. Existing files are never re-rendered."""
    os.makedirs(RENDER_DIR, exist_ok=True)
    jobs = [(f"{ref}_r{k}", ref, k) for ref, _ in REFERENCES for k in range(REPS)]

    def worker():
        while True:
            with _lock:
                if _next[0] >= len(jobs):
                    return
                i = _next[0]
                _next[0] += 1
            name, ref, k = jobs[i]
            path = os.path.join(RENDER_DIR, name + ".wav")
            if os.path.exists(path) and os.path.getsize(path) > 1000:
                print(f"SKIP {name} (already rendered)", flush=True)
                continue
            t0 = time.time()
            try:
                data = synth(TEXT, ref)
                with open(path, "wb") as f:
                    f.write(data)
                print(f"OK   {name} wall={time.time()-t0:.1f}s bytes={len(data)}",
                      flush=True)
            except Exception as e:  # noqa: BLE001
                print(f"ERR  {name}: {e}", flush=True)

    ts = [threading.Thread(target=worker) for _ in range(CONCURRENCY)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()


def centroid_of(path):
    return sa.analyse(path).get("spectral_centroid_hz")


def measure_pool(directory, reps):
    """{ref: [centroid, ...]} from files named <ref>_r<k>.wav."""
    out = {}
    if not os.path.isdir(directory):
        return out
    for ref, _role in REFERENCES:
        vals = []
        for k in range(reps):
            p = os.path.join(directory, f"{ref}_r{k}.wav")
            if not os.path.exists(p):
                continue
            c = centroid_of(p)
            if c is not None:
                vals.append(c)
        if vals:
            out[ref] = vals
    return out


def spearman_rho(a, b):
    """Rank correlation, ties averaged; returns (rho, exact one-sided p).

    The one-sided p is P(rho_perm >= rho_observed) over all n! permutations
    of b -- the convention used for the transfer check on record.
    """
    n = len(a)
    if n < 2:
        return None, None

    def ranks(xs):
        order = sorted(range(n), key=lambda i: xs[i])
        r = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and xs[order[j + 1]] == xs[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for t in range(i, j + 1):
                r[order[t]] = avg
            i = j + 1
        return r

    ra, rb = ranks(a), ranks(b)
    d2 = sum((ra[i] - rb[i]) ** 2 for i in range(n))
    rho = 1.0 - 6.0 * d2 / (n * (n * n - 1))
    hits = 0
    total = 0
    for perm in itertools.permutations(range(n)):
        rp = ranks([b[p] for p in perm])
        d2p = sum((ra[i] - rp[i]) ** 2 for i in range(n))
        rho_p = 1.0 - 6.0 * d2p / (n * (n * n - 1))
        total += 1
        if rho_p >= rho - 1e-9:
            hits += 1
    return rho, hits / total if total else None


def pooled_stats(pool):
    """Alias floor, pooled within-name SD, and per-name means."""
    means = {r: statistics.mean(v) for r, v in pool.items()}
    alias_means = [means[a] for a in ALIAS_GROUP if a in means]
    floor = (max(alias_means) - min(alias_means)) if len(alias_means) > 1 else None
    num = 0.0
    df = 0
    for _ref, vals in pool.items():
        if len(vals) > 1:
            sd = statistics.stdev(vals)
            num += sd * sd * (len(vals) - 1)
            df += len(vals) - 1
    pooled_sd = (num / df) ** 0.5 if df else None
    return means, floor, pooled_sd, df


def separations(means):
    """{distinct ref: distance to nearest alias mean}."""
    out = {}
    for ref in DISTINCT:
        if ref not in means:
            continue
        near = [means[a] for a in ALIAS_GROUP if a in means]
        if near:
            out[ref] = min(abs(means[ref] - m) for m in near)
    return out


def mel_control(directory, reps):
    """Control: the repo's own timbre metric (log-mel profile distance).

    The manifest's fingerprint table uses this metric, not the centroid.
    It measures the SHAPE of the spectrum, so it is insensitive to the
    per-render spectral-tilt lottery that makes the scalar centroid jumpy.
    """
    bands = {}

    def prof(ref, k):
        p = os.path.join(directory, f"{ref}_r{k}.wav")
        if not os.path.exists(p):
            return None
        if p not in bands:
            x, sr = sa.load_wav(p)
            bands[p] = sa.mel_bands(x, sr)
        return bands[p]

    within = []
    for ref, _ in REFERENCES:
        for k1, k2 in itertools.combinations(range(reps), 2):
            a, b = prof(ref, k1), prof(ref, k2)
            if a is not None and b is not None:
                within.append(sa.mel_distance(a, b))
    between = {}
    for r1, r2 in itertools.combinations([r for r, _ in REFERENCES], 2):
        ds = []
        for k1 in range(reps):
            for k2 in range(reps):
                a, b = prof(r1, k1), prof(r2, k2)
                if a is not None and b is not None:
                    ds.append(sa.mel_distance(a, b))
        if ds:
            between[f"{r1}|{r2}"] = {"min": round(min(ds), 3),
                                       "mean": round(statistics.mean(ds), 3)}
    return {
        "within_name": {"n": len(within),
                        "min": round(min(within), 3) if within else None,
                        "mean": round(statistics.mean(within), 3) if within else None,
                        "max": round(max(within), 3) if within else None},
        "between_name": between,
        "note": ("the log-mel profile distance is the metric the manifest's "
                 "own fingerprint table uses; it separates voices where the "
                 "scalar centroid does not"),
    }


def main():
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    print(f"=== RENDER PHASE: {REPS} reps x {len(REFERENCES)} refs "
          f"at concurrency {CONCURRENCY} ===", flush=True)
    render_all()
    wall = time.time() - t0

    # --- the session under test: the fresh renders, one session ----------
    new = measure_pool(RENDER_DIR, REPS)
    means, floor, pooled_sd, df = pooled_stats(new)
    sep = separations(means)
    min_sep = min(sep.values()) if sep else None
    n_per = {r: len(v) for r, v in new.items()}

    # --- the earlier n=2 session, as an INDEPENDENT draw from the noise ---
    old = measure_pool(POOL_DIR, 2)
    hist_means, hist_floor, hist_sd, _ = (pooled_stats(old) if old
                                          else ({}, None, None, 0))
    hist_sep = separations(hist_means)
    hist_min_sep = min(hist_sep.values()) if hist_sep else None

    # --- the largest same-voice, same-line pool on disk: the noise scale ---
    sweep = []
    if os.path.isdir(SWEEP_DIR):
        for p in sorted(os.listdir(SWEEP_DIR)):
            if p.endswith(".wav"):
                c = centroid_of(os.path.join(SWEEP_DIR, p))
                if c is not None:
                    sweep.append(c)
    sweep_sd = statistics.stdev(sweep) if len(sweep) > 1 else None

    # --- settling curve: floor and separation as replicates are added ----
    settling = []
    for k in range(1, max(n_per.values()) + 1):
        sub = {r: v[:k] for r, v in new.items() if len(v) >= k}
        if not sub:
            continue
        m, f, sd, _d = pooled_stats(sub)
        s = separations(m)
        settling.append({
            "reps_used": k,
            "alias_floor_hz": round(f, 2) if f is not None else None,
            "min_separation_hz": round(min(s.values()), 2) if s else None,
            "separation_hz": {r: round(v, 2) for r, v in s.items()},
            "separation_over_floor": (round(min(s.values()) / f, 2)
                                      if s and f else None),
            "clears_floor": bool(s and f and min(s.values()) > f),
            "pooled_within_name_sd_hz": round(sd, 2) if sd is not None else None,
        })

    # --- transfer check: reference clip order vs output mean order -------
    transfer = None
    ref_clips = {}
    for ref in FOUR_REFS:
        p = os.path.join(REFS_DIR, f"{ref}.wav")
        if os.path.exists(p):
            ref_clips[ref] = sa.analyse(p)
    if len(ref_clips) == 4 and all(r in means for r in FOUR_REFS):
        keys = list(FOUR_REFS)
        ref_cen = [ref_clips[k]["spectral_centroid_hz"] for k in keys]
        out_cen = [means[k] for k in keys]
        ref_f0 = [ref_clips[k]["f0_median_hz"] for k in keys]
        out_f0 = []
        for k in keys:
            vals = []
            for r in range(REPS):
                p = os.path.join(RENDER_DIR, f"{k}_r{r}.wav")
                if os.path.exists(p):
                    a = sa.analyse(p)
                    if a.get("f0_median_hz"):
                        vals.append(a["f0_median_hz"])
            out_f0.append(statistics.mean(vals) if vals else 0.0)
        rho_c, p_c = spearman_rho(ref_cen, out_cen)
        rho_f, p_f = spearman_rho(ref_f0, out_f0)
        transfer = {
            "n": len(keys),
            "reference_centroid_order": [k for _, k in sorted(zip(ref_cen, keys))],
            "output_centroid_order": [k for _, k in sorted(zip(out_cen, keys))],
            "brightness_rho": round(rho_c, 3) if rho_c is not None else None,
            "brightness_exact_p_one_sided": round(p_c, 4) if p_c is not None else None,
            "pitch_rho": round(rho_f, 3) if rho_f is not None else None,
            "pitch_exact_p_one_sided": round(p_f, 4) if p_f is not None else None,
            "note": ("brightness (centroid) is the statistic that transfers; f0 "
                     "does not transfer because F5-TTS regenerates the "
                     "fundamental"),
        }

    mel = mel_control(RENDER_DIR, REPS)

    verdict = {
        "text": TEXT,
        "statistic": "power-weighted spectral centroid (voiceprint.analyse)",
        "new_replicates_rendered": REPS,
        "concurrency": CONCURRENCY,
        "render_wall_s": round(wall, 1),
        "session_under_test": "this run (.audio_work/settling/renders)",
        "replicates_per_reference": n_per,
        "alias_floor_hz": round(floor, 2) if floor is not None else None,
        "historical_alias_floor_hz_n2": HISTORICAL_ALIAS_FLOOR_HZ,
        "pooled_within_name_sd_hz": round(pooled_sd, 2) if pooled_sd is not None else None,
        "pooled_df": df,
        "se_of_a_mean_hz": (round(pooled_sd / (REPS ** 0.5), 2)
                            if pooled_sd is not None else None),
        "per_reference": {
            r: {
                "centroid_values_hz": [round(c, 2) for c in v],
                "centroid_mean_hz": round(means[r], 2),
                "within_name_sd_hz": (round(statistics.stdev(v), 2)
                                      if len(v) > 1 else None),
            } for r, v in new.items()
        },
        "separation_from_alias_group_hz": {r: round(v, 2) for r, v in sep.items()},
        "min_separation_hz": round(min_sep, 2) if min_sep is not None else None,
        "min_separation_over_alias_floor": (round(min_sep / floor, 2)
                                            if min_sep and floor else None),
        "min_separation_over_historical_floor": (
            round(min_sep / HISTORICAL_ALIAS_FLOOR_HZ, 2) if min_sep else None),
        "settles_above_alias_floor": bool(min_sep and floor and min_sep > floor),
        "settling_curve": settling,
        "independent_earlier_session_n2": {
            "alias_floor_hz": round(hist_floor, 2) if hist_floor else None,
            "pooled_within_name_sd_hz": round(hist_sd, 2) if hist_sd else None,
            "min_separation_hz": (round(hist_min_sep, 2) if hist_min_sep else None),
            "per_reference_mean_hz": {r: round(v, 2) for r, v in hist_means.items()},
            "note": ("same probe line, earlier session; a separate draw from the "
                     "same noise, so the floor is not a fixed constant"),
        },
        "noise_scale": {
            "same_voice_same_line_pool": SWEEP_DIR,
            "n": len(sweep),
            "per_render_centroid_sd_hz": (round(sweep_sd, 2)
                                          if sweep_sd else None),
            "note": ("the per-render centroid SD is the scale the alias floor "
                     "is drawn from; a floor far below it is a small-sample "
                     "fluke"),
        },
        "mel_profile_control": mel,
        "transfer_check": transfer,
    }

    # ------------------------------------------------------------------ print
    print(f"\n=== RENDERED {REPS} reps x {len(REFERENCES)} refs in {wall:.1f}s ===")
    print("\n=== PER REFERENCE (centroid Hz, THIS session) ===")
    for ref, _role in REFERENCES:
        if ref in new:
            vals = [round(c, 2) for c in new[ref]]
            sd = (statistics.stdev(new[ref]) if len(new[ref]) > 1 else 0)
            print(f"  {ref:18s} n={len(vals)} mean={means[ref]:8.2f} "
                  f"sd={sd:6.2f} vals={vals}")
    print("\n=== ALIAS FLOOR (the three names that share one ref.wav) ===")
    print(f"  alias means: "
          f"{[round(means[a], 2) for a in ALIAS_GROUP if a in means]}")
    print(f"  alias floor THIS session  = {round(floor, 2) if floor else None} Hz")
    print(f"  alias floor earlier n=2    = "
          f"{round(hist_floor, 2) if hist_floor else None} Hz "
          f"(on record: {HISTORICAL_ALIAS_FLOOR_HZ} Hz)")
    print(f"  per-render centroid SD     = "
          f"{round(pooled_sd, 2) if pooled_sd else None} Hz (df={df})")
    print(f"  per-render SD, 24-rep pool = "
          f"{round(sweep_sd, 2) if sweep_sd else None} Hz (n={len(sweep)})")
    print("\n=== SEPARATION FROM THE ALIAS GROUP ===")
    for ref in DISTINCT:
        if ref in sep:
            print(f"  {ref:18s} mean={means[ref]:8.2f} "
                  f"nearest alias dist={sep[ref]:7.2f} Hz "
                  f"({round(sep[ref] / floor, 2) if floor else 0}x floor)")
    print(f"\n  MINIMUM SEPARATION = {round(min_sep, 2) if min_sep else None} Hz")
    print(f"  ALIAS FLOOR        = {round(floor, 2) if floor else None} Hz")
    print(f"  SETTLES ABOVE FLOOR = {verdict['settles_above_alias_floor']}")
    print("\n=== SETTLING CURVE (this session) ===")
    for s in settling:
        print(f"  reps={s['reps_used']} floor={s['alias_floor_hz']} "
              f"min_sep={s['min_separation_hz']} "
              f"({s['separation_over_floor']}x) {s['separation_hz']}")
    if transfer:
        print("\n=== TRANSFER CHECK ===")
        print(f"  brightness rho={transfer['brightness_rho']} "
              f"p={transfer['brightness_exact_p_one_sided']} "
              f"(n={transfer['n']}, floor p=1/24=0.0417)")
        print(f"  pitch      rho={transfer['pitch_rho']} "
              f"p={transfer['pitch_exact_p_one_sided']}")
    if mel:
        print("\n=== MEL-PROFILE CONTROL (the manifest's own timbre metric) ===")
        w = mel["within_name"]
        print(f"  within-name  : n={w['n']} min={w['min']} "
              f"mean={w['mean']} max={w['max']}")
        print(f"  between-name :")
        for k, v in sorted(mel["between_name"].items()):
            print(f"     {k:38s} min={v['min']:6.3f} mean={v['mean']:6.3f}")
    with open(os.path.join(OUT, "settling_verdict.json"), "w",
              encoding="utf-8") as f:
        json.dump(verdict, f, indent=2)
    print("\nSETTLING_TEST_DONE", flush=True)


if __name__ == "__main__":
    main()
