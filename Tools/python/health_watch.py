"""Watch the HTPC's inference server while the TTS bank burns.

The TTS service and the fleet's local inference share the HTPC's CPU and RAM.
The instruction is explicit: if inference health degrades, back the render
concurrency down rather than starve the fleet for a sound bank.

This samples, on a fixed interval, for the life of the process:
  - TTS /health                (is the TTS service alive)
  - inference /health          (is the llama.cpp server up)
  - inference /v1/models       (is the model registered)
  - a real generation request  (is the model ACTUALLY ANSWERING, and how fast)

THE PROBE IS FIXED AND IS NOT TO BE TOUCHED
-------------------------------------------
The generation probe hits /v1/chat/completions, the endpoint the server
actually implements, and sends `chat_template_kwargs: {"enable_thinking":
false}` so it measures the MODEL rather than the chat template. Success is
HTTP 200 with a parseable `choices` array and non-empty content. Measured
live: generations return in 0.18 s with `models` true. That shape is correct
and is preserved here unchanged.

THE VERDICT IS WHAT THIS MODULE FIXES
--------------------------------------
Two defects made the verdict untrustworthy, and both are fixed here.

DEFECT 1 -- A PROBE AIMED AT A SERVICE THAT DOES NOT EXIST
The watch used to probe an "ollama" health endpoint and fold the result into
the verdict as a boolean. Ollama is not a service on the HTPC, so that probe
could never pass, and because it never passed it poisoned every verdict the
instrument would ever produce.

The general lesson, and the rule this module now follows: A SERVICE THAT IS
ABSENT AND A SERVICE THAT IS BROKEN ARE DIFFERENT FACTS, AND THE VERDICT HAS
TO BE ABLE TO SAY SO.

So every service is checked in two steps:

  1. DETECT THE PORT FIRST. If nothing is listening on the service's port,
     the service is NOT_PRESENT -- a distinct, neutral state that is recorded
     and reported, and that NEVER counts as a failure. There is no such thing
     as a broken service that is not there.
  2. Only if the port IS listening, probe the service's endpoint and judge
     its health.

The watch tracks the two services that matter on this node:
  - llama.cpp inference on 10.0.0.42:8080 -- present, probed for real
  - Ollama on 10.0.0.42:11434           -- absent on the HTPC, so it reports
                                           "not present" rather than "failed"

DEFECT 2 -- A SINGLE TRANSIENT 503 LATCHED ACROSS THE WHOLE WINDOW
The verdict used to be `all(state == OK for state in states)`, a latch over
the entire run. A 160-sample / 2400 s run that caught one 503 during a model
reload reported `gen_all_ok: false` for the whole forty minutes and painted
the window red, even though the tail was a clean sequence of true samples
with 0.18 s generations. The verdict did not describe the node.

The fix is a CONSECUTIVE-FAILURE THRESHOLD. The verdict reflects the CURRENT
state of the node, and a fault only counts once it is sustained:
  * three or more failures IN A ROW  -> DEGRADED
  * one isolated failure during a reload -> a COLD model, reported as COLD
The threshold is applied to the current trailing streak. The report also
carries the full per-sample history, so a transient is visible in the detail
without poisoning the verdict.

FAULT TAXONOMY (three faults, three owners)
--------------------------------------------
The generation probe is NOT a boolean. It distinguishes:

  OK              200 + parseable choices + non-empty content. The model is
                  loaded and answering. The only state that means "alive".

  LOADING         503 with "Loading model" in the body. The server is UP and
                  the model is COMING. A cold model during a reload. This is
                  retried for up to RETRY_BUDGET_S at RETRY_INTERVAL_S before
                  it is called a failure, so one unlucky probe during a
                  reload does not read as a dead node.

  WEDGED          a 503 that PERSISTS for the whole retry window. The server
                  is up, the model is STUCK. A genuine DEGRADED verdict, and
                  a different meaning from LOADING: stuck, not absent.

  GONE            connection refused / timeout / DNS failure. The SERVER is
                  gone. A different owner from a wedged model.

  TEMPLATE_EMPTY  200 with an empty content field. The model answered but the
                  Qwen3.5 thinking template ate the token budget. The model
                  is HEALTHY; the template is broken. Third owner.

  NO_CHOICES      200 with no parseable choices array. Protocol fault.

  HTTP_ERROR      any other non-200.

The shared implementation lives in inference_liveness.py, which is also the
module the HTPC's inference guardian should import -- it is the ready-made
"is the model actually answering" test. See that file's docstring for why
the guardian's current process-existence check passes forever on a wedged
model, and use `health_state()` for the single-call healthy/cold/wedged
contract the guardian lane needs.
"""
import json
import os
import socket
import statistics
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import inference_liveness as il  # noqa: E402

INFER = il.INFER_BASE
TTS = "http://10.0.0.42:8020/health"
OLLAMA_HOST = "10.0.0.42"
OLLAMA_PORT = 11434          # Ollama's canonical port
DURATION = int(sys.argv[1]) if len(sys.argv) > 1 else 900
INTERVAL = 15
LATENCY_WARN = 20.0      # seconds; a generation slower than this is starved
REPORT = sys.argv[2] if len(sys.argv) > 2 else ".audio_work/health_report.json"

# --- 503 retry policy (the probe's 503 handling) --------------------------
# A 503 "Loading model" is transient for the first minute or two of a reload.
# Retry it for up to 240 s at a 10 s interval before calling it a failure.
RETRY_BUDGET_S = 240.0
RETRY_INTERVAL_S = 10.0
PROBE_TIMEOUT_S = 20.0

# --- consecutive-failure threshold (the verdict fix) ----------------------
# A fault only degrades the verdict once it is SUSTAINED. One isolated
# failure during a model reload is a cold model, not a degraded node.
CONSECUTIVE_FAILURE_THRESHOLD = 3

# The inference server on 8080 is llama.cpp with an OpenAI-compatible API.
# Its /api/generate and /api/ps paths are NOT implemented (404), so the
# generation probe must use /v1/chat/completions or it measures nothing.


# --------------------------------------------------------- presence detection
def port_listening(host, port, timeout=1.5):
    """Is anything LISTENING on this TCP port?

    This is the FIRST step of every service check. A service that is not
    listening is NOT PRESENT -- a distinct, neutral state that must never be
    reported as a failure. Only a service that IS listening can be broken.
    """
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def service_state(host, port):
    """Detect a service's PRESENCE without judging its health.

    Returns "present" or "not_present". "not_present" is NEUTRAL: it is a
    true statement about the node, not a fault.
    """
    return "present" if port_listening(host, port) else "not_present"


def get(url, timeout=30):
    t0 = time.time()
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            body = r.read()
            status = r.status
        return {"ok": True, "status": status,
                "elapsed_s": round(time.time() - t0, 2),
                "body": body[:200].decode("utf-8", "replace")}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "elapsed_s": round(time.time() - t0, 2),
                "error": str(e)}


def gen_probe():
    """Is the model actually answering? Delegates to the shared liveness module.

    Retry policy: only a 503 is retried (up to RETRY_BUDGET_S). Every other
    failure is a definitive answer and is reported immediately.
    """
    return il.probe(retry_budget_s=RETRY_BUDGET_S,
                    retry_interval_s=RETRY_INTERVAL_S,
                    timeout=PROBE_TIMEOUT_S)


def verdict_line(sample):
    """The one-line verdict for a sample.

    The HTTP status and the error body go in the line, and the state names
    which of the three faults it is. A node whose model is LOADING is not the
    same failure as a node whose model is WEDGED, and both used to collapse
    into "generation request failed".
    """
    g = sample["generation"]
    state = g.get("state", "UNKNOWN")
    status = g.get("http_status")
    body = (g.get("error_body") or "").replace("\n", " ")[:120]
    if state == il.STATE_OK:
        return "gen=OK http=%s t=%.2fs content=%r" % (
            status, g.get("elapsed_s", 0.0), g.get("content", ""))
    return "gen=%s http=%s t=%.2fs body=%s" % (
        state, status, g.get("elapsed_s", 0.0), body or g.get("detail", ""))


# ------------------------------------------------------------ verdict logic
def trailing_failure_streak(states, failing_states):
    """Length of the CURRENT (trailing) run of failing samples.

    The verdict describes the node NOW. A single isolated failure early in a
    2400 s window is history, not the current state, and must not latch the
    verdict for the rest of the run.
    """
    streak = 0
    for st in reversed(states):
        if st in failing_states:
            streak += 1
        else:
            break
    return streak


def max_failure_streak(states, failing_states):
    """Longest run of consecutive failures anywhere in the window."""
    best = 0
    cur = 0
    for st in states:
        if st in failing_states:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def classify_fault(states, failing_states):
    """Name the fault behind the current streak: which of the three owners?

    Returns a dict with the fault state, the HTTP status, the body, and a
    human-readable reason naming the OWNER of the fault.
    """
    for st in reversed(states):
        if st in failing_states:
            reason = {
                il.STATE_WEDGED:
                    "model WEDGED: 503 persisted past the %ds retry window "
                    "(model stuck, not absent) -- owner: inference/model-load"
                    % int(RETRY_BUDGET_S),
                il.STATE_GONE:
                    "inference server GONE: connection refused or timed out "
                    "-- owner: inference process supervision",
                il.STATE_TEMPLATE_EMPTY:
                    "model answered with EMPTY content (thinking template ate "
                    "the budget) -- owner: chat template / client payload",
                il.STATE_NO_CHOICES:
                    "inference returned 200 with no choices array "
                    "-- owner: inference API compatibility",
                il.STATE_HTTP_ERROR:
                    "inference returned an unexpected HTTP status "
                    "-- owner: inference API",
                il.STATE_LOADING:
                    "model LOADING: 503 'Loading model' -- the model is "
                    "coming -- owner: model load",
            }.get(st, "generation failed (%s)" % st)
            return {"state": st, "reason": reason}
    return {"state": None, "reason": None}


def build_verdict(states, failing_states, tts_oks, service_states,
                  ok_gen_latencies):
    """Build the verdict from the CURRENT state, not from a window latch.

    Rules:
      * A service that is not listening is NOT_PRESENT: recorded, reported,
        and never counted as a failure.
      * A generation fault degrades the verdict only when it is SUSTAINED --
        CONSECUTIVE_FAILURE_THRESHOLD failures in a row. One isolated
        failure during a reload is a COLD model.
      * The verdict string names the fault and its owner.
    """
    degraded = []
    notes = []

    # --- services that are absent: neutral, not failures -------------------
    for name, st in service_states.items():
        if st == "not_present":
            notes.append("service %s: NOT PRESENT (not listening) -- "
                         "neutral, not a failure" % name)

    # --- the inference server itself must be present ------------------------
    if service_states.get("llama.cpp") == "not_present":
        degraded.append("llama.cpp inference service NOT PRESENT on "
                        "%s:%d -- owner: inference process supervision"
                        % (il.INFER_HOST, il.INFER_PORT))

    # --- TTS ----------------------------------------------------------------
    if not all(tts_oks):
        degraded.append("tts health intermittent")

    # --- generation: consecutive-failure threshold -------------------------
    streak = trailing_failure_streak(states, failing_states)
    longest = max_failure_streak(states, failing_states)
    if streak >= CONSECUTIVE_FAILURE_THRESHOLD:
        fault = classify_fault(states, failing_states)
        degraded.append("%s (%d consecutive failures, threshold %d)"
                        % (fault["reason"], streak,
                           CONSECUTIVE_FAILURE_THRESHOLD))
    elif streak > 0:
        fault = classify_fault(states, failing_states)
        notes.append("current state: %s -- %d isolated failure(s), below the "
                     "%d-consecutive threshold, so this is NOT degraded"
                     % (fault["reason"], streak,
                        CONSECUTIVE_FAILURE_THRESHOLD))

    # --- latency ------------------------------------------------------------
    if ok_gen_latencies and statistics.median(ok_gen_latencies) > LATENCY_WARN:
        degraded.append("generation median %.1fs exceeds %.1fs (starved)"
                        % (statistics.median(ok_gen_latencies), LATENCY_WARN))

    if degraded:
        verdict = "DEGRADED"
    elif streak > 0:
        verdict = "COLD"        # model coming; not a fault yet
    else:
        verdict = "HEALTHY"

    return {
        "verdict": verdict,
        "degraded": degraded,
        "notes": notes,
        "consecutive_failure_threshold": CONSECUTIVE_FAILURE_THRESHOLD,
        "current_failure_streak": streak,
        "longest_failure_streak": longest,
        "services_absent": [n for n, st in service_states.items()
                            if st == "not_present"],
    }


if __name__ == "__main__":
    samples = []
    t_end = time.time() + DURATION
    print(f"health watch for {DURATION}s, interval {INTERVAL}s", flush=True)
    print("fault taxonomy: OK / LOADING / WEDGED / GONE / TEMPLATE_EMPTY / "
          "NO_CHOICES / HTTP_ERROR", flush=True)
    print(f"consecutive-failure threshold: {CONSECUTIVE_FAILURE_THRESHOLD} "
          f"(one isolated failure = cold, not degraded)", flush=True)
    while time.time() < t_end:
        ts = time.time()
        s = {
            "ts": round(ts, 1),
            "tts_health": get(TTS, timeout=10),
            "llama_presence": service_state(il.INFER_HOST, il.INFER_PORT),
            "llama_health": get(INFER + "/health", timeout=10),
            "llama_models": get(INFER + "/v1/models", timeout=10),
            "ollama_presence": service_state(OLLAMA_HOST, OLLAMA_PORT),
            "generation": gen_probe(),
        }
        samples.append(s)
        print(f"[{len(samples):3d}] tts_ok={s['tts_health']['ok']} "
              f"llama_present={s['llama_presence']} "
              f"llama_ok={s['llama_health']['ok']} "
              f"ollama_present={s['ollama_presence']} | {verdict_line(s)}",
              flush=True)
        nap = INTERVAL - (time.time() - ts)
        if nap > 0:
            time.sleep(nap)

    states = [s["generation"].get("state") for s in samples]
    gens = [s["generation"]["elapsed_s"] for s in samples]
    ok_gens = [s["generation"]["elapsed_s"] for s in samples
               if s["generation"].get("state") == il.STATE_OK]
    tts_oks = [s["tts_health"]["ok"] for s in samples]
    counts = {}
    for st in states:
        counts[st] = counts.get(st, 0) + 1

    service_states = {
        "llama.cpp": samples[-1]["llama_presence"] if samples else "unknown",
        "ollama": samples[-1]["ollama_presence"] if samples else "unknown",
    }

    v = build_verdict(states, il.FAILING_STATES, tts_oks, service_states,
                      ok_gens)

    for n in v["notes"]:
        print("note: %s" % n, flush=True)

    report = {
        "samples": len(samples),
        "interval_s": INTERVAL,
        "retry_policy": {
            "budget_s": RETRY_BUDGET_S,
            "interval_s": RETRY_INTERVAL_S,
            "retried_states": ["503 Loading model"],
            "escalation": "503 persisting past the budget -> WEDGED",
        },
        "verdict_policy": {
            "consecutive_failure_threshold": CONSECUTIVE_FAILURE_THRESHOLD,
            "rule": "a generation fault degrades the verdict only when it is "
                    "sustained for N consecutive samples; one isolated "
                    "failure during a reload is a COLD model, not degraded",
            "window_latch": False,
            "absent_is_not_broken": True,
        },
        "service_presence": {
            "llama.cpp": {"host": il.INFER_HOST, "port": il.INFER_PORT,
                          "state": service_states["llama.cpp"]},
            "ollama": {"host": OLLAMA_HOST, "port": OLLAMA_PORT,
                       "state": service_states["ollama"]},
        },
        "tts_health_all_ok": all(tts_oks),
        "llama_health_all_ok": all(s["llama_health"]["ok"] for s in samples),
        "llama_present": service_states["llama.cpp"] == "present",
        "ollama_present": service_states["ollama"] == "present",
        "ollama_health_all_ok": (
            None if service_states["ollama"] != "present"
            else all(s["ollama_health"]["ok"] for s in samples)
            if "ollama_health" in samples[0] else None),
        "generation_all_ok": all(st == il.STATE_OK for st in states),
        "generation_state_counts": counts,
        "generation_latency_s": {
            "min": min(gens) if gens else None,
            "median": round(statistics.median(gens), 2) if gens else None,
            "max": max(gens) if gens else None,
        },
        "current_failure_streak": v["current_failure_streak"],
        "longest_failure_streak": v["longest_failure_streak"],
        "services_absent": v["services_absent"],
        "degraded": v["degraded"],
        "notes": v["notes"],
        "verdict": v["verdict"],
        "detail": samples,
    }
    os.makedirs(os.path.dirname(REPORT) or ".", exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\nVERDICT={report['verdict']} degraded={v['degraded']}", flush=True)
    print(f"STATE_COUNTS={counts}", flush=True)
    print(f"CURRENT_STREAK={v['current_failure_streak']} "
          f"LONGEST_STREAK={v['longest_failure_streak']} "
          f"THRESHOLD={CONSECUTIVE_FAILURE_THRESHOLD}", flush=True)
    print("HEALTH_WATCH_DONE", flush=True)
