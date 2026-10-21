"""Concurrency + real-line-duration probe against the F5 service."""
import json
import os
import sys
import time
import urllib.request
import wave
from concurrent.futures import ThreadPoolExecutor

URL = "http://10.0.0.42:8020/synth"
LINES = [
    "Hello! Would you like to file a complaint about the weather inside my mouth?",
    "Good morning! Your mother called. She is a subroutine. She says hello. She keeps saying hello.",
    "The pizza is very late. That is not a joke. That is a schedule. You are on the schedule too.",
]
OUT = sys.argv[1] if len(sys.argv) > 1 else "."
N = int(sys.argv[2]) if len(sys.argv) > 2 else 3


def go(i):
    t0 = time.time()
    payload = json.dumps({"text": LINES[i % len(LINES)], "voice": "spokesman"}).encode()
    req = urllib.request.Request(URL, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        data = r.read()
    p = os.path.join(OUT, f"conc_{i}.wav")
    with open(p, "wb") as f:
        f.write(data)
    w = wave.open(p, "rb")
    dur = w.getnframes() / w.getframerate()
    w.close()
    return i, round(time.time() - t0, 1), round(dur, 2), w.getframerate(), len(data)


t_start = time.time()
with ThreadPoolExecutor(max_workers=N) as ex:
    for res in ex.map(go, range(N)):
        print(f"idx={res[0]} elapsed={res[1]}s dur={res[2]}s sr={res[3]} bytes={res[4]}", flush=True)
print(f"TOTAL_WALL {round(time.time() - t_start, 1)}s for {N} concurrent renders")
