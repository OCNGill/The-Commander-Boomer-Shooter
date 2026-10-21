"""
GILLSYSTEMS COMMAND CENTER — one URL, all outputs.

    python CommandCenter/serve_outputs.py [--port 8899] [--host 0.0.0.0]

Serves a live dashboard aggregating every artifact the fleet produces for
The Commander Boomer Shooter:
  * fleet node status (on/off board)
  * swarm task queue + swarm ledger (who did what, when)
  * agent outputs (per-slot folders) with live file listings
  * renders / screenshots / preview images (gallery)
  * Blender kit inventory (FBX + manifest)
  * UE asset + map inventory
  * git log + working-tree state
  * design docs (Docs/generated)

Everything is read from disk on every /api/manifest call, so it is always current.
LAN URL: http://10.0.0.93:8899/   (laptop).  Local: http://127.0.0.1:8899/
"""
import argparse
import glob
import json
import os
import re
import subprocess
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CC = os.path.join(REPO, "CommandCenter")
OUT = os.path.join(CC, "outputs")
HERMES = os.path.join(os.environ.get("LOCALAPPDATA", ""), "hermes")

IMG_EXT = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp")
DOC_EXT = (".md", ".txt", ".json", ".csv")


def sh(args, timeout=20, cwd=REPO):
    try:
        r = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                           timeout=timeout, errors="replace")
        return r.stdout.strip()
    except Exception as e:
        return "ERR: %s" % str(e)[:120]


def read(path, limit=4000):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read(limit)
    except Exception:
        return ""


def build_manifest():
    m = {"generated": time.strftime("%Y-%m-%d %H:%M:%S"), "repo": REPO}

    # ---- fleet node status ----
    fn = os.path.join(HERMES, "fleet_node_status.json")
    m["fleet"] = {}
    if os.path.exists(fn):
        try:
            d = json.loads(read(fn, 20000))
            nodes = d.get("nodes", d)
            for k, v in (nodes.items() if isinstance(nodes, dict) else []):
                m["fleet"][k] = v.get("status", "?")
        except Exception:
            pass

    # ---- swarm: queue + ledger ----
    q = os.path.join(CC, "SWARM_TASK_QUEUE.md")
    m["queue"] = {"exists": os.path.exists(q), "bytes": 0, "tasks": []}
    if os.path.exists(q):
        t = read(q, 200000)
        m["queue"]["bytes"] = len(t)
        m["queue"]["tasks"] = re.findall(r"^\|\s*(TASK-\d+)\s*\|([^|]*)\|([^|]*)\|", t, re.M)
    led = os.path.join(OUT, "LEDGER.md")
    m["ledger"] = [l for l in read(led, 100000).splitlines() if l.strip() and "TASK-" in l]

    # ---- agent output slots ----
    slots = []
    if os.path.isdir(OUT):
        for d in sorted(os.listdir(OUT)):
            p = os.path.join(OUT, d)
            if not os.path.isdir(p):
                continue
            files = []
            for root, _dirs, fs in os.walk(p):
                for f in fs:
                    fp = os.path.join(root, f)
                    try:
                        st = os.stat(fp)
                    except Exception:
                        continue
                    files.append({"path": os.path.relpath(fp, REPO).replace("\\", "/"),
                                  "name": f, "kb": round(st.st_size / 1024, 1),
                                  "mtime": time.strftime("%H:%M", time.localtime(st.st_mtime))})
            files.sort(key=lambda x: -x["kb"])
            if files:
                slots.append({"slot": d, "n": len(files),
                              "total_kb": round(sum(f["kb"] for f in files), 1),
                              "files": files[:40]})
    m["slots"] = slots

    # ---- images gallery ----
    imgs = []
    for root in (OUT, os.path.join(REPO, "Docs"), os.path.join(REPO, "Tools", "blender")):
        if not os.path.isdir(root):
            continue
        for dp, _d, fs in os.walk(root):
            for f in fs:
                if f.lower().endswith(IMG_EXT):
                    fp = os.path.join(dp, f)
                    try:
                        st = os.stat(fp)
                    except Exception:
                        continue
                    imgs.append({"path": os.path.relpath(fp, REPO).replace("\\", "/"),
                                 "name": f, "kb": round(st.st_size / 1024, 1),
                                 "mtime": time.strftime("%H:%M", time.localtime(st.st_mtime))})
    imgs.sort(key=lambda x: x["mtime"], reverse=True)
    m["images"] = imgs[:80]

    # ---- blender kit ----
    kit = []
    for fp in glob.glob(os.path.join(REPO, "Tools", "blender", "out_xcom", "*.fbx")):
        kit.append({"name": os.path.basename(fp), "kb": round(os.path.getsize(fp) / 1024, 1)})
    m["blender_fbx"] = sorted(kit, key=lambda x: x["name"])
    m["blender_manifest"] = read(os.path.join(REPO, "Tools", "blender", "out_xcom",
                                              "xcom_manifest.json"), 20000)

    # ---- UE assets ----
    assets = []
    for root, _d, fs in os.walk(os.path.join(REPO, "Content")):
        for f in fs:
            if f.endswith((".uasset", ".umap")):
                fp = os.path.join(root, f)
                assets.append({"path": os.path.relpath(fp, REPO).replace("\\", "/"),
                               "kb": round(os.path.getsize(fp) / 1024, 1)})
    m["ue_assets"] = sorted(assets, key=lambda x: x["path"])
    m["ue_counts"] = {
        "uasset": len([a for a in assets if a["path"].endswith(".uasset")]),
        "umap": len([a for a in assets if a["path"].endswith(".umap")]),
    }

    # ---- design docs ----
    docs = []
    for fp in glob.glob(os.path.join(REPO, "Docs", "**", "*"), recursive=True):
        if os.path.isfile(fp) and fp.lower().endswith(DOC_EXT):
            try:
                st = os.stat(fp)
            except Exception:
                continue
            docs.append({"path": os.path.relpath(fp, REPO).replace("\\", "/"),
                         "kb": round(st.st_size / 1024, 1),
                         "mtime": time.strftime("%m-%d %H:%M", time.localtime(st.st_mtime))})
    docs.sort(key=lambda x: x["mtime"], reverse=True)
    m["docs"] = docs[:60]

    # ---- git ----
    m["commits"] = [l for l in sh(["git", "log", "--oneline", "-12"]).splitlines() if l.strip()]
    m["dirty"] = [l for l in sh(["git", "status", "--porcelain"]).splitlines() if l.strip()][:40]
    return m


PAGE = r"""<!doctype html>
<html><head><meta charset="utf-8"><title>Gillsystems Command Center</title>
<meta http-equiv="refresh" content="20">
<style>
:root{color-scheme:dark}
body{background:#0b0e13;color:#d9e4ee;font:14px/1.55 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;margin:0;padding:26px 22px 60px}
h1{font-size:21px;letter-spacing:.14em;color:#5fd4ff;margin:0 0 4px;text-transform:uppercase}
.sub{color:#66788a;font-size:12px;margin-bottom:22px}
h2{font-size:12px;letter-spacing:.16em;color:#8fa9bd;margin:26px 0 10px;border-bottom:1px solid #1c2733;padding-bottom:6px;text-transform:uppercase}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(310px,1fr));gap:13px}
.card{background:#111821;border:1px solid #1c2733;border-radius:7px;padding:12px 14px}
.k{color:#6d8296;font-size:11px;letter-spacing:.1em;text-transform:uppercase}
.v{font-size:26px;color:#eaf3fb;margin:2px 0 6px}
.ok{color:#5fe08a}.warn{color:#ffc75f}.bad{color:#ff7b72}.dim{color:#6d8296}
ul{margin:5px 0 0;padding:0;list-style:none}
li{padding:1px 0;font-size:12.5px;word-break:break-all}
table{border-collapse:collapse;width:100%;font-size:12.5px}
td,th{padding:4px 9px;border-bottom:1px solid #18222d;text-align:left}
th{color:#7f97aa;font-weight:500;font-size:11px;letter-spacing:.08em;text-transform:uppercase}
a{color:#5fd4ff;text-decoration:none}a:hover{text-decoration:underline}
.pill{display:inline-block;padding:1px 8px;border-radius:11px;font-size:11px;border:1px solid #24313e}
.pill.on{color:#5fe08a;border-color:#1e4a33}.pill.off{color:#ff7b72;border-color:#4a2220}
.imgs{display:grid;grid-template-columns:repeat(auto-fill,minmax(168px,1fr));gap:11px}
.imgs figure{margin:0}
.imgs img{width:100%;border:1px solid #1c2733;border-radius:5px;background:#0d1319;display:block}
.imgs figcaption{font-size:11px;color:#6d8296;margin-top:4px}
code{color:#9ad6a0}
</style></head><body>
<h1>Gillsystems Command Center</h1>
<div class="sub" id="sub">loading…</div>
<div id="root"></div>
<script>
const esc=s=>String(s==null?'':s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
const card=(k,v)=>`<div class="card"><div class="k">${esc(k)}</div><div class="v">${v}</div></div>`;
async function go(){
  let m; try{ m=await (await fetch('/api/manifest?x='+Date.now())).json(); }
  catch(e){ document.getElementById('sub').textContent='manifest fetch failed: '+e; return; }
  const fleet=Object.entries(m.fleet||{}).map(([k,v])=>`<li>${esc(k)} <span class="pill ${v==='on'?'on':'off'}">${esc(v)}</span></li>`).join('')||'<li class="dim">no node board</li>';
  const led=(m.ledger||[]).map(l=>`<li>${esc(l)}</li>`).join('')||'<li class="dim">ledger empty — swarm has not reported yet</li>';
  const tasks=(m.queue.tasks||[]).map(t=>`<tr><td>${esc(t[0])}</td><td>${esc(t[1])}</td><td>${esc(t[2])}</td></tr>`).join('');
  const slots=(m.slots||[]).map(s=>`<div class="card"><div class="k">${esc(s.slot)}</div><div class="v">${s.n} <span class="dim" style="font-size:13px">files / ${s.total_kb} KB</span></div><ul>`+
      s.files.slice(0,14).map(f=>`<li><a href="/file/${encodeURI(f.path)}">${esc(f.name)}</a> <span class="dim">${f.kb}KB ${esc(f.mtime)}</span></li>`).join('')+`</ul></div>`).join('');
  const imgs=(m.images||[]).map(i=>`<figure><a href="/file/${encodeURI(i.path)}" target="_blank"><img src="/file/${encodeURI(i.path)}?v=${Date.now()}" loading="lazy"></a><figcaption>${esc(i.name)} · ${i.kb}KB</figcaption></figure>`).join('');
  const commits=(m.commits||[]).map(c=>`<li>${esc(c)}</li>`).join('');
  const dirty=(m.dirty||[]).map(c=>`<li class="warn">${esc(c)}</li>`).join('')||'<li class="dim">clean tree</li>';
  const fbx=(m.blender_fbx||[]).map(f=>`<li>${esc(f.name)} <span class="dim">${f.kb}KB</span></li>`).join('')||'<li class="dim">no FBX yet</li>';
  const ue=(m.ue_assets||[]).map(a=>`<li>${esc(a.path)} <span class="dim">${a.kb}KB</span></li>`).join('')||'<li class="dim">none</li>';
  const docs=(m.docs||[]).map(d=>`<li><a href="/file/${encodeURI(d.path)}">${esc(d.path.split('/').pop())}</a> <span class="dim">${d.kb}KB ${esc(d.mtime)}</span></li>`).join('');
  document.getElementById('sub').innerHTML='updated '+esc(m.generated)+' · repo <code>'+esc(m.repo.split('/').pop())+'</code> · '+
    'queue '+(m.queue.tasks||[]).length+' tasks · ledger '+(m.ledger||[]).length+' · images '+(m.images||[]).length+' · UE '+(m.ue_counts.uasset||0)+' assets / '+(m.ue_counts.umap||0)+' maps';
  document.getElementById('root').innerHTML=`
  <div class="grid">
    ${card('Fleet nodes', Object.keys(m.fleet||{}).length||'—')}
    ${card('Blender FBX', (m.blender_fbx||[]).length)}
    ${card('UE assets', (m.ue_counts.uasset||0)+' / '+(m.ue_counts.umap||0)+' maps')}
    ${card('Renders', (m.images||[]).length)}
    ${card('Swarm slots', (m.slots||[]).length)}
    ${card('Commits', (m.commits||[]).length)}
  </div>
  <h2>Fleet</h2><ul>${fleet}</ul>
  <h2>Swarm ledger</h2><ul>${led}</ul>
  <h2>Task queue</h2><table><tr><th>Task</th><th>Slot</th><th>Deliverable</th></tr>${tasks||'<tr><td colspan=3 class=dim>queue file not present</td></tr>'}</table>
  <h2>Agent output slots</h2><div class="grid">${slots||'<div class="card dim">no agent output yet</div>'}</div>
  <h2>Renders &amp; screenshots</h2><div class="imgs">${imgs||'<span class="dim">none yet</span>'}</div>
  <h2>Blender kit</h2><ul>${fbx}</ul>
  <h2>UE content</h2><ul>${ue}</ul>
  <h2>Design docs</h2><ul>${docs}</ul>
  <h2>Git</h2><ul>${commits}</ul><h2>Uncommitted</h2><ul>${dirty}</ul>`;
}
go(); setInterval(go,15000);
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/":
            return self._send(200, PAGE, "text/html; charset=utf-8")
        if path == "/api/manifest":
            return self._send(200, json.dumps(build_manifest(), indent=1), "application/json")
        if path.startswith("/file/"):
            rel = path[len("/file/"):]
            target = os.path.normpath(os.path.join(REPO, rel.replace("/", os.sep)))
            if not target.startswith(REPO) or not os.path.isfile(target):
                return self._send(404, "not found", "text/plain")
            ctype = "application/octet-stream"
            if target.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
                ctype = "image/" + target.rsplit(".", 1)[1].replace("jpg", "jpeg")
            elif target.lower().endswith((".md", ".txt")):
                ctype = "text/plain; charset=utf-8"
            elif target.lower().endswith(".json"):
                ctype = "application/json"
            with open(target, "rb") as f:
                return self._send(200, f.read(), ctype)
        return self._send(404, "not found", "text/plain")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8899)
    ap.add_argument("--host", default="0.0.0.0")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    srv = ThreadingHTTPServer((a.host, a.port), Handler)
    print("Command Center LIVE on http://%s:%d" % (a.host, a.port), flush=True)
    print("  repo:", REPO, flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
