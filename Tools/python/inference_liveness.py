"""Is the model ACTUALLY ANSWERING? -- a reusable liveness probe for llama.cpp.

This module is the canonical "is the model actually answering" test for the
fleet's local inference server (llama.cpp, OpenAI-compatible API, port 8080).
It exists because the obvious checks are all wrong in different ways, and each
one has already cost the fleet a false diagnosis.

    check                                  result
    ------------------------------------   --------------------------------
    pgrep -x llama-server                  PASSES FOREVER on a wedged model
    ss -ltn | grep :8080                   PASSES FOREVER while the model loads
    POST /api/generate  (Ollama path)      404 in ~0.02s -- llama.cpp has no
                                           such route; looks like instant death
    GET  /health, 200 implied              503 "Loading model" while loading --
                                           must be TRIED and RETRIED, not failed
    POST /v1/chat/completions, no flags    200 with content:"" and
                                           finish_reason:"length" -- the
                                           Qwen3.5 thinking template ate the
                                           whole token budget

THE FAULT TAXONOMY (three faults, three owners)
-----------------------------------------------
    STATE_OK              200 + parseable choices + non-empty content.
                          The model is loaded AND answering. This is the only
                          state that means "alive".

    STATE_LOADING         503 whose body says "Loading model". The server is
                          UP and the model is COMING. Transient for the first
                          minute or two of a reload. NOT a failure.

    STATE_WEDGED          503 that PERSISTS for the whole retry window. The
                          server is up, the model is STUCK. This is a genuine
                          DEGRADED verdict and it means something different
                          from STATE_LOADING: the model is stuck, not absent.

    STATE_GONE            connection refused, timeout, DNS failure, reset. The
                          SERVER is gone -- a different owner entirely from
                          a wedged model.

    STATE_TEMPLATE_EMPTY  200 with an empty content field. The model answered
                          but the thinking template ate the budget. The model
                          is HEALTHY; the template is broken. Third owner.

    STATE_NO_CHOICES      200 but the body has no parseable choices array.
                          Protocol fault.

    STATE_HTTP_ERROR      any other non-200 status.

RETRY SEMANTICS
---------------
A 503 "Loading model" is retried for up to `retry_budget_s` seconds at
`retry_interval_s` intervals BEFORE it is called a failure, so that a single
unlucky probe during a cold reload is not reported as a dead node. If the
model comes up inside that window the probe reports OK and records how long
the cold start took (`cold_start_s`). If the window expires with the 503
still present, the verdict escalates from LOADING to WEDGED.

Only 503 is retried. A refused connection, a timeout, a 200 with empty
content and a 200 with no choices are all definitive answers -- retrying them
only delays the report of a fault that is already known.

THE THINKING FLAG
-----------------
Every request body carries `chat_template_kwargs: {"enable_thinking": false}`.
Qwen3.5's default template spends the entire max_tokens budget on
`reasoning_content` and returns an empty `content` string, which would make a
healthy model look dead. Measured on the HTPC: without the flag, content=""
and finish_reason="length"; with it, the same request returns "PONG" in
~0.3 s. A probe that asks for one word should never need a thinking block.

GUARDIAN USE
------------
The HTPC's inference guardian (start-inference-guardian-htpc.sh) currently
defines liveness as:

    inference_up() {
        ss -ltn | grep -q ":8080 " && pgrep -x llama-server >/dev/null
    }

Both halves are true while the model is wedged in "Loading model", so the
guardian reports UP and never revives anything -- a process-existence check
passes forever on a wedged model. The replacement it needs is
`probe_once()` / `probe()` from this module: a request that must come back
with real content, or a persistent 503 that escalates to STATE_WEDGED.

CLI
---
    python Tools/python/inference_liveness.py                 # full probe (240s retry)
    python Tools/python/inference_liveness.py --once          # single attempt, no retry
    python Tools/python/inference_liveness.py --strikes 3 --interval 20
                                                          # guardian mode: declare
                                                          # DEAD only after N
                                                          # consecutive failures
Exit code 0 = answering, 1 = not answering. Stdout is one JSON object.
"""

from __future__ import annotations

import json
import socket
import sys
import time
import urllib.error
import urllib.request

INFER_HOST = "10.0.0.42"
INFER_PORT = 8080
INFER_BASE = "http://%s:%d" % (INFER_HOST, INFER_PORT)
INFER_MODEL = "qwen3.5-9b-it"

STATE_OK = "OK"
STATE_LOADING = "LOADING"
STATE_WEDGED = "WEDGED"
STATE_GONE = "GONE"
STATE_TEMPLATE_EMPTY = "TEMPLATE_EMPTY"
STATE_NO_CHOICES = "NO_CHOICES"
STATE_HTTP_ERROR = "HTTP_ERROR"

#: States that mean "the model is not answering right now".
FAILING_STATES = (STATE_WEDGED, STATE_GONE, STATE_TEMPLATE_EMPTY,
                   STATE_NO_CHOICES, STATE_HTTP_ERROR)

#: States that mean "the server is up but the model has not finished loading".
LOADING_STATES = (STATE_LOADING,)

DEFAULT_RETRY_BUDGET_S = 240.0
DEFAULT_RETRY_INTERVAL_S = 10.0
DEFAULT_TIMEOUT_S = 20.0


def _is_loading_body(body: str) -> bool:
    """Does this error body say the model is still loading?

    llama.cpp answers 503 with {"error":{"message":"Loading model",
    "type":"unavailable_error","code":503}}. The marker is the message text;
    the status alone is not enough, because a 503 can also mean "model
    failed to load" -- which is a wedged model, not a cold one.
    """
    low = (body or "").lower()
    return "loading model" in low or "loading" in low and "model" in low


def _classify_error_body(status: int, body: str) -> str:
    if status == 503 and _is_loading_body(body):
        return STATE_LOADING
    if status == 503:
        # 503 that is not a load-in-progress: the server is up but the model
        # is not coming. Same practical verdict as a wedged model.
        return STATE_WEDGED
    return STATE_HTTP_ERROR


def probe_once(timeout: float = DEFAULT_TIMEOUT_S) -> dict:
    """ONE request. Never retries. Never sleeps.

    Returns a dict with:
        state        one of the STATE_* constants
        http_status  int or None
        error_body   the raw response body (truncated) when not OK
        elapsed_s    wall time of this single attempt
        detail       human-readable one-liner
    """
    payload = {
        "model": INFER_MODEL,
        "messages": [{"role": "user", "content": "Reply with exactly: PONG"}],
        "max_tokens": 32,
        "stream": False,
        # Without this, Qwen3.5 returns content="" and finish_reason="length".
        "chat_template_kwargs": {"enable_thinking": False},
    }
    req = urllib.request.Request(
        INFER_BASE + "/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            status = r.status
            raw = r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        status = e.code
        try:
            raw = e.read().decode("utf-8", "replace")
        except Exception:  # noqa: BLE001
            raw = ""
    except socket.timeout:
        return {"state": STATE_GONE, "http_status": None, "error_body": "",
                "elapsed_s": round(time.time() - t0, 3),
                "detail": "timeout after %.1fs (no answer from server)" % timeout}
    except urllib.error.URLError as e:
        reason = getattr(e, "reason", e)
        return {"state": STATE_GONE, "http_status": None, "error_body": "",
                "elapsed_s": round(time.time() - t0, 3),
                "detail": "connection refused / unreachable: %s" % (reason,)}
    except Exception as e:  # noqa: BLE001
        return {"state": STATE_GONE, "http_status": None, "error_body": "",
                "elapsed_s": round(time.time() - t0, 3),
                "detail": "transport failure: %s" % (e,)}

    dt = round(time.time() - t0, 3)

    if status != 200:
        state = _classify_error_body(status, raw)
        return {"state": state, "http_status": status, "error_body": raw[:400],
                "elapsed_s": dt,
                "detail": "HTTP %d %s: %s" % (status, state, raw[:200])}

    try:
        body = json.loads(raw)
    except Exception:  # noqa: BLE001
        return {"state": STATE_NO_CHOICES, "http_status": status,
                "error_body": raw[:400], "elapsed_s": dt,
                "detail": "HTTP 200 but body is not JSON: %s" % raw[:160]}

    ch = body.get("choices") or []
    if not ch:
        return {"state": STATE_NO_CHOICES, "http_status": status,
                "error_body": raw[:400], "elapsed_s": dt,
                "detail": "HTTP 200 but no choices array in response"}

    msg = ch[0].get("message") or {}
    content = (msg.get("content") or "").strip()
    if not content:
        return {"state": STATE_TEMPLATE_EMPTY, "http_status": status,
                "error_body": raw[:400], "elapsed_s": dt,
                "detail": "HTTP 200 but empty content (thinking template ate "
                          "the budget? finish_reason=%s, reasoning_len=%d)"
                          % (ch[0].get("finish_reason"),
                             len(msg.get("reasoning_content") or ""))}

    return {"state": STATE_OK, "http_status": status, "error_body": "",
            "elapsed_s": dt, "content": content[:40],
            "finish_reason": ch[0].get("finish_reason"),
            "detail": "HTTP 200, model answered in %.2fs: %r"
                      % (dt, content[:40])}


def probe(retry_budget_s: float = DEFAULT_RETRY_BUDGET_S,
          retry_interval_s: float = DEFAULT_RETRY_INTERVAL_S,
          timeout: float = DEFAULT_TIMEOUT_S,
          sleep=time.sleep) -> dict:
    """Probe with 503-retry. This is the honest "is it answering" test.

    A 503 "Loading model" is retried for up to `retry_budget_s` seconds. If
    the model comes up inside the window the result is STATE_OK and
    `cold_start_s` records how long the cold start took. If the window
    expires with the 503 still present the state escalates to STATE_WEDGED
    -- a persistent 503 is a different verdict from a brief one.

    Only 503 is retried. Every other failure is a definitive answer.
    """
    t_start = time.time()
    deadline = t_start + retry_budget_s
    attempts = 0
    loading_seen = 0
    first_loading_at = None
    last = None

    while True:
        attempts += 1
        last = probe_once(timeout=timeout)
        if last["state"] == STATE_OK:
            out = dict(last)
            out["attempts"] = attempts
            out["total_elapsed_s"] = round(time.time() - t_start, 3)
            out["loading_503_seen"] = loading_seen
            if first_loading_at is not None:
                out["cold_start_s"] = round(time.time() - first_loading_at, 1)
            return out
        if last["state"] != STATE_LOADING:
            # Definitive failure -- refuse to retry it.
            out = dict(last)
            out["attempts"] = attempts
            out["total_elapsed_s"] = round(time.time() - t_start, 3)
            out["loading_503_seen"] = loading_seen
            return out

        loading_seen += 1
        if first_loading_at is None:
            first_loading_at = time.time()
        remaining = deadline - time.time()
        if remaining <= 0:
            out = dict(last)
            out["state"] = STATE_WEDGED
            out["attempts"] = attempts
            out["total_elapsed_s"] = round(time.time() - t_start, 3)
            out["loading_503_seen"] = loading_seen
            out["detail"] = ("HTTP %s 503 persisted for %.0fs across %d attempts "
                             "(model wedged, not absent): %s"
                             % (last.get("http_status"), retry_budget_s,
                                attempts, (last.get("error_body") or "")[:160]))
            return out
        sleep(min(retry_interval_s, remaining))


def is_answering(retry_budget_s: float = DEFAULT_RETRY_BUDGET_S,
                 retry_interval_s: float = DEFAULT_RETRY_INTERVAL_S,
                 timeout: float = DEFAULT_TIMEOUT_S) -> bool:
    """True only if the model actually produced content."""
    return probe(retry_budget_s, retry_interval_s, timeout)["state"] == STATE_OK


def guardian_check(strikes_required: int = 3, interval_s: float = 20.0,
                   timeout: float = DEFAULT_TIMEOUT_S, sleep=time.sleep) -> dict:
    """Guardian-shaped check: declare DEAD only after N consecutive failures.

    The existing HTPC guardian uses a process-existence check, which passes
    forever on a wedged model. This replaces it: a single 503 is a cold
    model, but N consecutive 503s (or one refused connection, or N
    consecutive empty-content answers) means the model is not answering and
    the guardian should act.
    """
    failures = []
    strikes = 0
    t0 = time.time()
    while strikes < strikes_required:
        r = probe_once(timeout=timeout)
        if r["state"] == STATE_OK:
            return {"alive": True, "strikes": 0, "attempts": len(failures) + 1,
                    "elapsed_s": round(time.time() - t0, 1),
                    "verdict": "ALIVE - model answering (%s)" % r.get("detail", ""),
                    "last": r, "history": failures}
        failures.append(r)
        if r["state"] in (STATE_GONE, STATE_NO_CHOICES, STATE_HTTP_ERROR):
            # Definitive: the server itself is gone. No need to keep striking.
            return {"alive": False, "strikes": len(failures),
                    "attempts": len(failures), "elapsed_s": round(time.time() - t0, 1),
                    "verdict": "DEAD - %s" % r.get("detail", ""),
                    "last": r, "history": failures}
        strikes += 1
        if strikes < strikes_required:
            sleep(interval_s)
    return {"alive": False, "strikes": strikes, "attempts": len(failures),
            "elapsed_s": round(time.time() - t0, 1),
            "verdict": "DEAD - %d consecutive failures, last: %s"
                       % (strikes, failures[-1].get("detail", "")),
            "last": failures[-1], "history": failures}


#: Tri-state contract for the inference guardian lane. The guardian needs
#: one clean value per call, so this collapses the detailed taxonomy onto the
#: three answers that map to three different actions.
TRI_HEALTHY = "healthy"
TRI_COLD = "cold"
TRI_WEDGED = "wedged"


def health_state(retry_budget_s: float = DEFAULT_RETRY_BUDGET_S,
                 retry_interval_s: float = DEFAULT_RETRY_INTERVAL_S,
                 timeout: float = DEFAULT_TIMEOUT_S) -> dict:
    """SINGLE-CALL guardian helper: is the model healthy, cold, or wedged?

    This is the check the HTPC inference guardian should call instead of its
    current process-existence test. The guardian's `inference_up()` asks two
    questions -- "is port 8080 listening?" and "does pgrep find llama-server?"
    -- and both of those stay TRUE while the model is wedged inside a load.
    That is exactly how the HTPC sat hung for over eleven minutes with a
    guardian running and reporting UP. A port and a process say the SERVER is
    alive; they say nothing about whether the MODEL is answering.

    This helper asks the question that matters: send a real generation
    request and see whether content comes back.

    Returns a dict:
        state    "healthy" | "cold" | "wedged"   <- the guardian's contract
        cause    the precise fault behind that state
        action   what the guardian should do: none | wait | restart
        healthy  / cold / wedged                 boolean convenience flags
        http_status, elapsed_s, detail           the underlying measurement

    The mapping, and why:
        healthy  200 + content. The model answers. action=none.
        cold     503 whose body says "Loading model". The server is UP and
                 the model is COMING. action=wait -- restarting a model that
                 is 30 seconds into a load is how you turn a cold start into
                 a wedge.
        wedged   a 503 that PERSISTS for the whole retry window, or a
                 refused/timeout connection. The model is not coming, or the
                 server is gone. action=restart.

    A 200 with an empty content field is reported as state="healthy" with
    cause="template_empty": the model IS loaded and IS answering at the HTTP
    layer, so a guardian must not restart the process over a chat-template
    bug. The cause and action fields make that distinguishable, and the
    health watch applies its own stricter taxonomy on top of this.
    """
    r = probe(retry_budget_s=retry_budget_s,
              retry_interval_s=retry_interval_s,
              timeout=timeout)
    st = r.get("state")
    body = (r.get("error_body") or "").lower()
    if st == STATE_OK:
        state, cause, action = TRI_HEALTHY, "ok", "none"
    elif st == STATE_LOADING:
        state, cause, action = TRI_COLD, "loading", "wait"
    elif st == STATE_WEDGED:
        if "loading model" in body:
            # Still says "Loading model" after the whole budget: the load is
            # stalled, not merely slow. That is a wedge.
            state, cause, action = TRI_WEDGED, "load_stalled", "restart"
        else:
            state, cause, action = TRI_WEDGED, "wedged", "restart"
    elif st == STATE_GONE:
        state, cause, action = TRI_WEDGED, "gone", "restart"
    elif st == STATE_TEMPLATE_EMPTY:
        state, cause, action = TRI_HEALTHY, "template_empty", "fix_template"
    elif st == STATE_NO_CHOICES:
        state, cause, action = TRI_WEDGED, "no_choices", "restart"
    else:
        state, cause, action = TRI_WEDGED, "http_error", "restart"
    return {
        "state": state,
        "cause": cause,
        "action": action,
        "healthy": state == TRI_HEALTHY,
        "cold": state == TRI_COLD,
        "wedged": state == TRI_WEDGED,
        "http_status": r.get("http_status"),
        "elapsed_s": r.get("elapsed_s"),
        "total_elapsed_s": r.get("total_elapsed_s"),
        "attempts": r.get("attempts"),
        "detail": r.get("detail"),
    }


def _main(argv) -> int:
    args = list(argv[1:])
    once = "--once" in args
    strikes = None
    if "--strikes" in args:
        strikes = int(args[args.index("--strikes") + 1])
    interval = 20.0
    if "--interval" in args:
        interval = float(args[args.index("--interval") + 1])
    budget = DEFAULT_RETRY_BUDGET_S
    if "--retry-budget" in args:
        budget = float(args[args.index("--retry-budget") + 1])

    if "--health" in args:
        r = health_state(retry_budget_s=budget)
        r["mode"] = "health"
    elif once:
        r = probe_once()
        r["mode"] = "once"
    elif strikes is not None:
        r = guardian_check(strikes_required=strikes, interval_s=interval)
        r["mode"] = "guardian"
    else:
        r = probe(retry_budget_s=budget)
        r["mode"] = "probe"

    print(json.dumps(r, indent=2))
    if r.get("mode") == "guardian":
        return 0 if r.get("alive") else 1
    if r.get("mode") == "health":
        # 0 = healthy, 1 = cold (wait), 2 = wedged (restart)
        return {"healthy": 0, "cold": 1, "wedged": 2}.get(r.get("state"), 2)
    return 0 if r["state"] == STATE_OK else 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
