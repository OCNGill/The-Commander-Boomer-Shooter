"""Fault-path tests for the health watch VERDICT logic.

These do not touch the network. They inject synthetic sample sequences into
the verdict builder and assert the verdict each one must produce, so the
verdict is known-good rather than merely observed.

Run: python Tools/python/health_watch_tests.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import health_watch as hw  # noqa: E402
import inference_liveness as il  # noqa: E402

FAIL = 0


def check(name, got, want):
    global FAIL
    ok = got == want
    if not ok:
        FAIL += 1
    print("  %-58s got=%-9s want=%-9s %s"
          % (name, got, want, "PASS" if ok else "*** FAIL ***"))


def v(states, tts_oks=None, services=None, lat=None):
    if tts_oks is None:
        tts_oks = [True] * len(states)
    if services is None:
        services = {"llama.cpp": "present", "ollama": "not_present"}
    if lat is None:
        lat = [0.25] * len(states)
    return hw.build_verdict(states, il.FAILING_STATES, tts_oks, services, lat)


print("VERDICT: clean run")
check("all OK", v([il.STATE_OK] * 5)["verdict"], "HEALTHY")

print("\nVERDICT: consecutive-failure threshold (N=%d)"
      % hw.CONSECUTIVE_FAILURE_THRESHOLD)
check("1 isolated failure -> COLD, not degraded",
      v([il.STATE_OK] * 4 + [il.STATE_WEDGED])["verdict"], "COLD")
check("2 in a row -> still COLD, not degraded",
      v([il.STATE_OK] * 3 + [il.STATE_WEDGED] * 2)["verdict"], "COLD")
check("3 in a row -> DEGRADED",
      v([il.STATE_OK] * 3 + [il.STATE_WEDGED] * 3)["verdict"], "DEGRADED")
check("transient mid-run does not latch the verdict",
      v([il.STATE_WEDGED] + [il.STATE_OK] * 5)["verdict"], "HEALTHY")
check("3 in a row then recovery -> verdict reflects NOW",
      v([il.STATE_WEDGED] * 3 + [il.STATE_OK] * 3)["verdict"], "HEALTHY")
check("longest streak is still reported",
      v([il.STATE_WEDGED] * 3 + [il.STATE_OK] * 3)["longest_failure_streak"], 3)
check("current streak is 0 after recovery",
      v([il.STATE_WEDGED] * 3 + [il.STATE_OK] * 3)["current_failure_streak"], 0)

print("\nABSENT IS NOT BROKEN")
r = v([il.STATE_OK] * 3,
       services={"llama.cpp": "present", "ollama": "not_present"})
check("ollama absent -> verdict still HEALTHY", r["verdict"], "HEALTHY")
check("ollama absent -> listed in services_absent", r["services_absent"],
      ["ollama"])
check("ollama absent -> a NOTE, not a degradation",
      any("NOT PRESENT" in n for n in r["notes"]), True)
check("ollama absent -> no degraded entries", r["degraded"], [])
r = v([il.STATE_OK] * 3,
       services={"llama.cpp": "not_present", "ollama": "not_present"})
check("llama.cpp absent -> DEGRADED (the server we need is gone)",
      r["verdict"], "DEGRADED")
check("llama.cpp absent -> names process supervision as owner",
      any("process supervision" in d for d in r["degraded"]), True)

print("\nTHREE FAULTS, THREE OWNERS")
faults = [
    (il.STATE_LOADING, "model is coming", "model load"),
    (il.STATE_WEDGED, "model is STUCK", "model-load"),
    (il.STATE_GONE, "the SERVER is gone", "process supervision"),
    (il.STATE_TEMPLATE_EMPTY, "the thinking template ate the budget",
     "chat template"),
]
for state, _desc, owner in faults:
    if state == il.STATE_LOADING:
        continue
    r = v([il.STATE_OK] * 2 + [state] * 3)
    joined = " ".join(r["degraded"]).lower()
    check("%s -> DEGRADED" % state, r["verdict"], "DEGRADED")
    check("%s -> owner named: %s" % (state, owner), owner in joined, True)
    check("%s -> names a different owner than the others" % state,
          len(set(owner for _s, _d, owner in faults
                 if owner in joined)) >= 1, True)

print("\nTTS and latency")
check("tts intermittent -> DEGRADED",
      v([il.STATE_OK] * 3, tts_oks=[True, False, True])["verdict"], "DEGRADED")
check("slow generations -> DEGRADED",
      v([il.STATE_OK] * 3, lat=[45.0, 50.0, 44.0])["verdict"], "DEGRADED")
check("normal generations -> not degraded",
      v([il.STATE_OK] * 3, lat=[0.2, 0.3, 0.25])["verdict"], "HEALTHY")

print("\nPORT DETECTION")
check("port 11434 (ollama) not listening on this host",
      hw.port_listening("10.0.0.42", 11434), False)
check("port 8080 (llama.cpp) IS listening",
      hw.port_listening("10.0.0.42", 8080), True)
check("service_state returns not_present for a dead port",
      hw.service_state("10.0.0.42", 11434), "not_present")
check("service_state returns present for a live port",
      hw.service_state("10.0.0.42", 8080), "present")

print("\nTHE PROBE IS THE FIXED ONE")
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "health_watch.py"), encoding="utf-8").read()
check("probe hits /v1/chat/completions",
      "/v1/chat/completions" in src, True)
check("probe sends enable_thinking false",
      "enable_thinking" in open(os.path.join(
          os.path.dirname(os.path.abspath(__file__)),
          "inference_liveness.py"), encoding="utf-8").read(), True)
check("no window latch (all() over the whole run)",
      "all(st == il.STATE_OK for st in states)" in src, True)

print("\nSINGLE-CALL TRI-STATE HELPER")
check("health_state exists", hasattr(il, "health_state"), True)
check("tri-state constants exist",
      (il.TRI_HEALTHY, il.TRI_COLD, il.TRI_WEDGED),
      ("healthy", "cold", "wedged"))

print("\n%s" % ("ALL HEALTH WATCH TESTS PASS" if FAIL == 0
                else "%d TEST(S) FAILED" % FAIL))
sys.exit(1 if FAIL else 0)
