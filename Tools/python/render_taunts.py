"""Batch-render the taunt bank from the fleet F5-TTS service.

Concurrency-safe: a small thread pool of workers pulls from the line list,
each POSTing to http://10.0.0.42:8020/synth and saving the raw WAV.
Retries on transient failure. Skips files that already exist (resumable).
"""
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from taunt_lines import TAUNTS, validate  # noqa: E402

SYNTH_URL = "http://10.0.0.42:8020/synth"
VOICE = "spokesman"
OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else "."
WORKERS = int(sys.argv[2]) if len(sys.argv) > 2 else 3
RETRIES = 3
TIMEOUT = 600

_lock = threading.Lock()
_state = {"done": 0, "fail": 0, "total": len(TAUNTS)}


def render(line):
    tid = line["id"]
    path = os.path.join(OUT_DIR, tid + ".wav")
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        with _lock:
            _state["done"] += 1
            print(f"[skip] {tid}", flush=True)
        return True

    payload = json.dumps({"text": line["text"], "voice": VOICE}).encode()
    for attempt in range(1, RETRIES + 1):
        t0 = time.time()
        try:
            req = urllib.request.Request(
                SYNTH_URL, data=payload, headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                data = r.read()
            if not data.startswith(b"RIFF"):
                raise RuntimeError(f"not a wav: {data[:80]!r}")
            tmp = path + ".part"
            with open(tmp, "wb") as f:
                f.write(data)
            os.replace(tmp, path)
            with _lock:
                _state["done"] += 1
                print(
                    f"[ok {_state['done']}/{_state['total']}] {tid} "
                    f"{len(data)}B {time.time() - t0:.0f}s",
                    flush=True,
                )
            return True
        except Exception as e:  # noqa: BLE001
            with _lock:
                print(f"[retry {attempt}/{RETRIES}] {tid}: {e}", flush=True)
            time.sleep(5 * attempt)
    with _lock:
        _state["fail"] += 1
        print(f"[FAIL] {tid}", flush=True)
    return False


def main():
    issues = validate()
    if issues:
        for i in issues:
            print("BANK PROBLEM:", i)
        sys.exit(2)
    os.makedirs(OUT_DIR, exist_ok=True)

    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        list(ex.map(render, TAUNTS))
    print(f"COMPLETE done={_state['done']} fail={_state['fail']} total={_state['total']}")
    sys.exit(1 if _state["fail"] else 0)


if __name__ == "__main__":
    main()
