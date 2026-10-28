# 7D PLAN — THE COMMANDER: PLYMOUTH
### Document ID: `PLAN-PLY-003` · Version **v03** · 2026-10-28
### Supersedes v02 → v01. Only the most recent artifact is kept (standing order #3).
### Owner: Commander Stephen Gill · Executor: Commander Hermes

---

## STATUS: **PLAN ONLY — NO BUILD AUTHORIZED**

Two standing orders absorbed into this version: **TTS off unless actively in use**, and **HTPC swap optimized**.

---

## §0 — DELTA FROM v02

| v02 | v03 |
|---|---|
| TTS service running permanently (2,246 MB resident) | **TTS OFF by default, on demand only** — `~/bin/tts-on` / `~/bin/tts-off`. Disabled at boot, no autostart |
| HTPC: 473 MB free, swap 100% full | **HTPC: 2.7 GB free, swap 62% used** — zram + sysctl tuned, zero-trust verified |
| Laptop did CPU Cycles / UE commandlets | **Laptop = control plane, zero compute** (v02 already corrected; carried forward) |

---

## §1 — HARDWARE TRUTH (measured 2026-10-28)

| Node | CPU | Threads | RAM | Free RAM | GPU | Swap | Verdict |
|---|---|---:|---|---|---|---|---|
| **Main** `10.0.0.164` | Ryzen 9 5900X | **12c / 24t** | 47.9 GB | **18.1 GB** | RX 7900 XTX 24 GB | — | **THE WORKHORSE** |
| **HTPC** `10.0.0.42` | Ryzen 5 5600G | 6c / 12t | 11.3 GB | **2.7 GB** | RX 7600 8 GB | 6.0 GB (62 % used) | Appliance — now has headroom |
| **Deck** `10.0.0.139` | Zen 2 | 4c / 8t | 14.8 GB | 0.66 GB | 16 GB unified | — | **Test rig, not compute** |
| **Laptop** `10.0.0.93` | Ryzen 5 4500U | **6c / 6t** no SMT | 19.4 GB | 8.4 GB | Vega 6 iGPU | — | **CONTROL PLANE, zero compute** |

### HTPC memory reality after remediation

| Process | RSS |
|---|---:|
| `llama-server` Qwen3.5-9B @ 131072 ctx, mmap | **5,958 MB** |
| ~~`f5-tts` python~~ | ~~2,246 MB~~ → **STOPPED, on demand** |
| plasma / kwin / dolphin / konsole / smbd | ~500 MB |

**Freed: 2.18 GB.** Notifier daemons masked. Swap now has 2.3 GB free instead of 12 kB.

---

## §2 — HTPC SWAP REMEDIATION (zero-trust verified)

### What was wrong
`/dev/nvme1n1p3` (4.0 GB) sat at **99.97 % used — 12 kB free**. Swap had no headroom left, which is the condition immediately preceding an OOM kill.

Root causes, in order of size:
| Holder | Swapped |
|---|---:|
| `llama-server` — idle anonymous pages | **2,622 MB** |
| `plasmashell` | 145 MB |
| `DiscoverNotifier` + `plasma-discover` | 222 MB |
| `kwin_wayland` | 60 MB |

### What was done

| # | Action | Effect |
|---|---|---|
| 1 | `systemctl stop + disable gillsystems-tts.service` | **−2.18 GB RSS**; cannot autostart at boot |
| 2 | Masked `plasma-discover.service` | −222 MB, cannot respawn |
| 3 | `/etc/sysctl.d/99-gillsystems-swap.conf`: `vm.swappiness=10`, `vm.vfs_cache_pressure=50`, `vm.page-cluster=0` | stops premature swap-out of live processes; page-cluster 0 is zram-optimal |
| 4 | `/etc/systemd/system/gillsystems-zram.service` — `/dev/zram0`, **2 GB, zstd, priority 100** | compressed RAM-speed swap tier ahead of the disk |
| 5 | Abandoned a swapfile attempt | **HTPC root is ZFS** — swapfiles on ZFS risk deadlock; `fallocate` also produced a sparse file that `swapon` rejects as *"appears to have holes"*. Removed cleanly, `fstab` verified free of the line |

### Verification — 22 checks, run independently

| Check | Result |
|---|---|
| Swap has headroom | **PASS** — 62.1 % used, 37.9 % free (was 99.97 %) |
| zram present, zstd, priority 100 | **PASS** |
| Disk partition still primary and intact | **PASS** — UUID `565350ad…` in `fstab` |
| zram unit **enabled** (survives reboot) | **PASS** |
| zram unit **active** | **PASS** |
| Boot-journal evidence of zram start | **PASS** — `Finished gillsystems-zram.service` 02:30:57 |
| Unit syntax | **PASS** — `systemd-analyze verify` clean |
| TTS inactive | **PASS** |
| TTS **disabled** (survives reboot) | **PASS** |
| TTS wants-symlink removed | **PASS** — 0 |
| TTS processes | **PASS** — 0 |
| TTS port 8020 | **PASS** — closed |
| No stale `/swapfile2` on disk | **PASS** — ABSENT |
| `fstab` free of swapfile2 | **PASS** — 0 matches |
| sysctl persisted + effective | **PASS** — 10 / 50 / 0 |
| `tts-on` + `tts-off` exist and are executable | **PASS** |
| Inference endpoint responding | **PASS** |
| **Inference functionally working** (real completion) | **PASS** — `POST_SWAP_OK`, `finish=stop`, 240 tokens |
| Guardian active | **PASS** |
| OOM kills since boot | **PASS** — 0 |
| HTPC Hermes alive | **PASS** |
| dmesg shows zram attach | **PASS** — `Adding 2097148k swap on /dev/zram0. Priority:100` |

**Two checks failed on the first pass and both were my own test bugs, not system faults** — an `awk` division against `/proc/meminfo` (fatal: division by zero) and a `grep -c | echo` pipe that emitted `"0 | 0"` and broke a `^0$` anchor. Both were re-run correctly and pass. Recorded here rather than quietly dropped.

### The one thing that cannot be reclaimed by automation
`llama-server`'s **2,622 MB** stays in disk swap until that process restarts. Window-owns-inference means **only the Commander restarts it** — no agent may resurrect or restart a llama-server. On its next natural restart, that swap returns to RAM and HTPC will show ~5 GB free.

---

## §3 — STANDING ORDER: TTS OFF UNLESS ACTIVE

**Rule:** the F5-TTS service runs only while work is actually being generated. It is not a resident daemon.

| | |
|---|---|
| Unit | `gillsystems-tts.service` — **stopped + disabled** |
| Autostart | **Impossible** — no `wants` symlink, `is-enabled` = disabled |
| Bring up | `ssh gillsystems-htpc@10.0.0.42 ~/bin/tts-on` |
| Shut down | `ssh gillsystems-htpc@10.0.0.42 ~/bin/tts-off` |
| Cost while up | **~2.2 GB RSS** |
| Port | **8020** (not 5000/7860/7861) |
| Cold start | model load ~20–40 s before first request succeeds |

**Generation pattern:** `tts-on` → batch the whole night's lines → `tts-off`. Never leave it up between batches. Never point a game engine at it at runtime.

---

## §4 — THE INCENTIVE

| Field | Value |
|---|---|
| Hook | **Epic Games AI MegaJam** |
| Window | **November 12–15, 2026** (theme revealed Nov 11) |
| Days from today (Oct 28) | **15** |
| Angles we win | **Render Royalty** (visual craft) · **Glass Box** (honest AI-native dev log) |
| Re-verify at D1 | Submission, originality, AI-disclosure rules — read verbatim |

The jam is the forcing function, not the goal.

---

## §5 — GOOGLE GENIE 4 (researched 2026-10-28)

Real. Launched **October 27, 2026** — one day before this plan.

| Fact | Detail |
|---|---|
| Announced | Oct 27, 2026 — Google DeepMind |
| Nature | Natively multimodal **world model** — explorable worlds from text |
| New in 4 | **Native audio** (ambient, music, *interactive dialogue*) · aerodynamics + collisions · humans that move, react, speak |
| Control | Natural language in real time — weather, camera, add a person or object mid-simulation; keyboard navigation |
| Stack | Gemini Omni + **Gemini 3.8 Flash** as in-loop guiding agent for multi-step coherence |
| Availability | **Research preview, trusted testers only.** Waitlist → Google AI Ultra + early access via Gemini API / AI Studio. No published pricing |
| Their stated use case | *"Game developers are testing Genie 4 to go from an initial idea to an explorable prototype in seconds… before writing a single line of engine code."* |

**Is:** previs and art-direction instrument. Walk a Plymouth zone before building it.
**Is not:** a shipping engine. Cannot package, cannot own assets, no consistency control, not generally available. **Not a dependency.**
**Action (Commander):** join the waitlist. One form, free, needs your Google identity.

---

## §6 — THE VOICE CAST (19 cloned voices, on demand)

Registry at `voices/<key>/{ref.wav, ref.txt}` — drop a folder to add a voice.

| Voice key | Game role |
|---|---|
| **`commander`** | **THE PLAYER — the Commander's own cloned voice** |
| `geordi` → **RIGGER** | Engineer |
| `liara` → **SABLE** | Infiltrator |
| `medic` → **PARSON** | Field Medic |
| `hermes`, `theo`, `adam`, `scribe` | 4 command crew |
| `herald`, `courier` | dispatch / radio chatter |
| `gaben`, `spark`, `scout`, `sentinel`, `lamp`, `architect`, `ebert`, `orchestrator` | vendors, NPCs, mission givers |
| `spokesman` | base for GRAYTIDE + enemy vocals, pitched and processed |

**Rules**
- ~11× realtime is **normal** (130–165 s per utterance). Never treat as a hang, never retry.
- Generate **offline to WAV**, batch overnight. Never at runtime.
- IP-named keys (`geordi`, `liara`, `edi`) never ship as filenames — export as `VO_RIGGER_*`, `VO_SABLE_*`.
- Target **~2,000 lines** across barks, missions, banter, radio, vendors, enemy vocals.
- One instance only. `tts-on` once, batch, `tts-off`.

---

## §7 — CUTSCENES & VIDEO

| Job | Engine | Why |
|---|---|---|
| In-engine story beats | **UE 5.8 Sequencer** (Main) | our assets, perfect consistency, ships in build, free |
| Intro / establishing / backstory | **MiniMax H3 local** via ComfyUI (Main) | sovereign, no per-clip cost |
| Hero trailer / jam reel | **Seedance 2.5** via OpenRouter | best quality — **needs explicit authorization, costs money** |
| Art-direction previs | **Genie 4** (if waitlist lands) | walk a zone before building it |

**Verified now:** ComfyUI on Main is **DOWN** (`127.0.0.1:8188` no response). Must be started window-owned before any H3 work.

---

## §8 — WHY NOT THE LAPTOP

- **6 cores / 6 threads, no SMT** — fewer threads than the Deck
- **36 % CPU at idle, 77 Chrome processes**
- It is the control plane: **Hermes and RustDesk both run there.** A stall costs the Commander his agent and his remote hands at the same instant
- Any render here trades ~2 % throughput for risking command of the entire fleet

**Locked:** OSM/Overpass/USGS pulls (network-bound), PIL map composition (seconds), lane board, docs, git, dispatch. **Nothing that spins a core past ~30 seconds.** No Blender. No UE commandlets. No renders. Ever.

---

## §9 — THE MAP

### 9a. Bounds (all 18 anchors inside)

| Bound | Lat / Lon |
|---|---|
| South | `41.8850` |
| North | `42.0650` |
| West | `-70.7550` |
| East | `-70.5950` |

| Dimension | Miles | km |
|---|---:|---:|
| N–S | **12.43** | 20.0 |
| E–W | **8.21** | 13.2 |
| **Area** | **102.1 sq mi** | **264 km²** |

**MILES everywhere** — mph, feet, yards. No metric in UI.
World Partition at 1 km cells → **21 × 14 ≈ 294 cells**, streaming.

### 9b. Twelve zones

| # | Zone | Role |
|---|---|---|
| A | **Home / Bettencourt** | hub, save |
| B | **Federal Furnace spine** (2.35 mi) | high-speed, ambush |
| C | **Seven Hills / South Meadow** | arena — traffic + enemies |
| D | **Summer St hill** (1.57 mi, 13 → 177 ft) | speed physics showcase |
| E | **Downtown waterfront** — Carver Inn, Rock, Mayflower II, rotary, Town Wharf | tourist corridor, hero shot |
| F | **Samoset retail strip** — Cumby's, McGovern, McDonald's, CVS, Walgreens | **major combat zone** |
| G | **Pilgrim Hill / Marc Dr** + Building 4 | explorable, side content |
| H | **Carver Rd / Faith Community Church** | landmark |
| I | **Airport / Ward St / Village Way** | open circuit |
| J | **Plimoth Patuxet** — Wampanoag Homesite + 1627 English Village | explorable, story |
| K | **Long Beach / Duxbury Beach** (3 mi spit) | open water, beach combat |
| L | **Forests & bogs** | wildlife, snakes, atmosphere |

### 9c. Verified anchors

| Landmark | Coordinates |
|---|---|
| House (7 Bettencourt) | `41.9119664, -70.7043577` |
| Alex (225 Lincoln St, Duxbury) | `42.0512648, -70.7216577` |
| Lobster Hut | `41.9626927, -70.6673676` |
| Plymouth Rock | `41.9580867, -70.6621119` |
| Mayflower II | `41.9597978, -70.6619409` |
| John Carver Inn | `41.9547458, -70.6650086` |
| Plimoth Patuxet Museums | `41.9393938, -70.6257860` |
| Cumberland Farms | `41.9514770, -70.6869342` |
| McGovern Chevrolet | `41.9529716, -70.6863874` |
| McDonald's | `41.9529716, -70.6863874` |
| Oak St | `41.9551634, -70.6723710` |
| Pilgrim Hill Rd | `41.9487227, -70.6858998` |
| Marc Dr | `41.9480424, -70.6917343` |
| Seven Hills / South Meadow Jct | `41.9414, -70.7033` |
| Plymouth Municipal Airport | `41.9074662, -70.7316853` |
| Ward St (Carver) | `41.8947303, -70.7436772` |
| Village Way | `41.8978129, -70.7188807` |
| Long Beach S (Eel River) | `41.9350, -70.6389` |
| Duxbury Beach | `42.0371544, -70.6336021` |
| Faith Community Church | **confirm at P0 via Street View — will not guess** |

---

## §10 — THE ROUTES

### 10a. Measured geometry — **5.16 mi / 14.2 min**

| Segment | Meters | Miles |
|---|---:|---:|
| Bettencourt Rd | 411 | 0.26 |
| **Federal Furnace Rd** | 3,775 | **2.35** |
| **Summer St** | 2,525 | **1.57** |
| Market St | 127 | 0.08 |
| Court St | 477 | 0.30 |
| Chilton St | 235 | 0.15 |
| Water St | 300 | 0.19 |
| → Lobster Hut | 146 | 0.09 |
| **Total** | **8,296** | **5.16 mi** |

### 10b. Two variants

**R1 — "The Commute"**
`Bettencourt → Federal Furnace → Summer St → Oak St (hazardous) → Samoset St → Rotary → Lobster Hut`

**R2 — "The Run Home" — canonical mission spine**
`Lobster Hut → Rotary → Samoset St → Cumberland Farms → Pilgrim Hill Rd → Summer St → Federal Furnace → Bettencourt`

### 10c. Elevation — USGS EPQS, 23 points

| Reading | Feet |
|---|---:|
| Waterfront / Lobster Hut | **13** |
| Route minimum | 13 |
| **Summer St high point** | **177** |
| Relief | **164** |

### 10d. Scooter physics

| Condition | Speed |
|---|---:|
| Flat | **22 mph** (motor cap) |
| Downhill 3 % | 24 |
| Downhill 6 % | 27 |
| Downhill 9 %+ | **30** (gravity cap) |
| Uphill 4 % | 16 |
| Uphill 8 %+ | 11 |
| Off-road | 65 % of current |

`v = clamp(22 + 1.1·grade, 22, 30)` down · `v = 22 − 1.4·|grade|` up. Grades every **30 m** from baked heightmap.

---

## §11 — ASSET INVENTORY

### 11a. HAVE

| Asset | State | Tris | UE-ready |
|---|---|:---:|:---:|
| 5 enemy meshes | render-quality PBR | 2,184–7,308 | ❌ no bake |
| 4 crew meshes | **placeholder** | **74–76** | ❌ |
| Plymouth blockout | OSM ground + 690 roads + water + buildings | — | ❌ |
| UE project shell | 71 uassets, `M_Blockout01`, `Packaged/Win64` | — | ✅ |
| 15 insult WAVs | audio | — | ✅ |
| **19 cloned TTS voices** | on disk, **service off** | — | ✅ |
| Reference photos | 7 Lobster Hut + scooter + Commander ×3 | — | — |

### 11b. NEED — characters
4 command crew + 3 squad + Commander player rig (black helmet, jacket, pants, gloves, on/off bike) — **25k–35k tris**, **baked 2K PBR**.

### 11c. NEED — props
48 oz iced coffees ×2 · **zip-tied Styrofoam cup holder** (your build, from your photos) · Laped scooter → cyber-kitbash · Lobster Hut · Carver Inn · Plymouth Rock + portico · Mayflower II · Plimoth Patuxet (wetus + 1627 village) · Faith Community Church · Marc Dr Building 4 · substation + transmission towers · McGovern lot · Cumby's forecourt · McDonald's · CVS · Walgreens · Route 3 furniture · rotary signage · traffic lights

### 11d. NEED — environment
USGS 3DEP heightmap 1 m / 264 km² · OSM roads **with name tags** (re-pull — street signs impossible without) · coastline + bathymetry · forest scattering (pine/oak) · wetland/bog materials · footprints with `building:levels`

---

## §12 — BESTIARY (16 units, IP-safe)

### 12a. Flesh — 5

| Code | Name | Threat | Read |
|---|---|---|---|
| `BST_GRAYTIDE` | **GRAYTIDE** | low | pale psionic swarm |
| `BST_RATLINE` | **RATLINE** | mid | serpentine constrictor |
| `BST_DRIFTER` | **DRIFTER** | mid | levitating eye-platform |
| `BST_BULWARK` | **BULWARK** | high | armored brute |
| `BST_HARROWER` | **HARROWER** | high | burrower, implanter |

### 12b. Machine — 11

| Code | Name | Analogue | Behaviour |
|---|---|---|---|
| `BST_MITE` | **MITE** | FPV kamikaze quad | swarms, dives, detonates |
| `BST_LANCE` | **LANCE** | loitering munition | circles high, dives on lock |
| `BST_SENTRY` | **SENTRY** | fixed-wing recon UAV | marks you, calls reinforcements |
| `BST_SPINNER` | **SPINNER** | fibre-optic tethered drone | **jam-immune**, relentless |
| `BST_HOUND` | **HOUND** | armed quadruped | packs of 3, flanking |
| `BST_PACKMASTER` | **PACKMASTER** | heavy quad carrier | spawns HOUNDs, missile pods |
| `BST_WOLFPACK` | **WOLFPACK** | drone-deployed mini-quads | dropped from altitude |
| `BST_GOLIATH` | **GOLIATH** | heavy biped | rockets, area denial |
| `BST_CARRIER` | **CARRIER** | mothership drone | launches MITEs |
| `BST_WARDEN` | **WARDEN** | counter-UAS node | jams *your* gear, forces dismount |
| `BST_ANVIL` | **ANVIL** | static turret | power-station defense |

**Ladder:** MARK I → II → III → IV — armour, sensors, aggression escalate.

### 12c. Wildlife — 13
Coyote · white-tailed deer (road hazard) · raccoon · squirrel (black/gray/brown) · fisher cat · red-tailed hawk · **bald eagle (protected, unkillable)** · herring + great black-backed gull · cormorant / egret / tern · garter snake · northern water snake · rat · spiders
Snakes in zone L (bogs), rats in zone F (retail). Ecology, not scenery.

---

## §13 — THE CREW IN THE FIELD

**2 deploy, 3 total.**

| Slot | Callsign | Role | Power set | Voice key |
|---|---|---|---|---|
| 1 | **RIGGER** | Engineer | turrets, repairs the scooter mid-ride, hacks drones | `geordi` *(internal)* |
| 2 | **SABLE** | Infiltrator | suppressed, cloak, marks targets | `liara` *(internal)* |
| 3 | **PARSON** | Field Medic | heals, revives, buffs; carries the coffee | `medic` |

2 active / 1 reserve, swapped at safehouses (home, the Hut, Marc Dr Bldg 4) · combos (SABLE marks → RIGGER overloads → PARSON revives) · loyalty missions per zone · no permadeath — downed squad bleeds out on a timer.

**Art bar:** 30k+ tris, real hands with fingers, sculpted faces, layered clothing, fabric/leather, baked 2K PBR. Blockouts **deleted, not upgraded.**
**Voice bar:** every squad-mate fully voiced. No silent characters.

---

## §14 — NODES & ALLOCATION

### 14a. Lane assignment

| Lane | Node | Concurrency | Notes |
|---|---|---|---|
| **Crew hero assets (7)** | **Main** | 2 | GPU + 18 GB headroom |
| **Scooter + rider + cyber-kit** | **Main** | 1 | hero assembly |
| **Bestiary (16 × 4 MARKs)** | **Main** | 2–3 | HTPC can't take these at scale |
| **Texture bakes (2K PBR)** | **Main** (Cycles GPU) | 1–2 | GPU-bound, no contention with CPU |
| **UE import / cook / WP / lighting / package** | **Main** (24t) | 1 UE proc | CPU-bound, overlaps GPU renders |
| **Wildlife (13)** | **HTPC** *with inference window closed* | 1 small | low-poly, low RSS |
| **Voice (~2,000 lines)** | **HTPC :8020** — **tts-on, batch, tts-off** | serial | 2.2 GB only while active |
| **Cutscene render (H3)** | **Main** ComfyUI | **DOWN — must start** | window-owned |
| **Playable validation, FSR, controller** | **Deck** | serial | the only real proof |
| **Orchestration, geodata, docs, git** | **Laptop** | — | **zero compute, <30 s** |

### 14b. The one real bottleneck, stated plainly

**Main is a single machine.** 24 threads and one GPU cannot absorb 23 characters + 16 wildlife + 304 UE cells + 2,000 VO lines without serialization. Honest schedule assumes **Main runs 14–18 h/day**, parallelizing CPU vs GPU *inside* it — not across nodes.

**If that's not fast enough, the fix is memory on a second node, not another plan.** With TTS now off by default, **HTPC has reclaimed 2.18 GB** — that alone makes it a usable second lane for low-poly work whenever its inference window is closed. Beyond that the options are: keep the window closed during the asset sprint, or add RAM to the 11.3 GB box.

### 14c. Render config — FSR NEWEST ONLY

- `FSR` **enabled** (Win64)
- **`DLSS`, `StreamlineNGXCommon`, `XeSS` → DISABLED** — all-AMD fleet, ~10 vendored NGX DLLs of dead weight
- FSR **4.1.1** on Main (RDNA3) · **3.1.5** forced on Deck (RDNA2) via `r.FidelityFX.FSR.RequestProvider=3`
- Preserved: `DefaultFeatureAntiAliasing=2`, `r.FidelityFX.FSR.Enabled=1`, `r.TemporalAA.Upscaler=1`
- `PythonScriptPlugin` enabled → **294-cell World Partition gets scripted, not hand-placed**

---

## §15 — IP CLEANSE (BLOCKING — D1)

| Current | New | Code |
|---|---|---|
| Sectoid | **GRAYTIDE** | `BST_GRAYTIDE` |
| Viper | **RATLINE** | `BST_RATLINE` |
| Floater | **DRIFTER** | `BST_DRIFTER` |
| Muton | **BULWARK** | `BST_BULWARK` |
| Chryssalid | **HARROWER** | `BST_HARROWER` |

**Renames:** `out_xcom/` → `out_bestiary/` · `xcom_enemies_v2.py` → `bestiary_build.py` · `xcom_manifest.json` → `MANIFEST_bestiary_v01.json` · `ENEMY_V2_BUILD_REPORT.md` → `REPORT_bestiary_v01.md`
**Internal only, never ships:** `geordi`, `liara`, `edi`
**Gate:** `grep -ri "xcom|sectoid|viper|floater|muton|chryssalid"` → zero hits outside the rename map
**Caution:** Generation Zero / H1Z1 are inspirations. Take the grammar, build our own vocabulary. No class names, silhouettes, or UI conventions copied.

---

## §16 — 7D EXECUTION

### D1 — DEFINE (½ day)
| Step | Output |
|---|---|
| D1.1 Re-read MegaJam rules verbatim (AI-asset + disclosure) | `MEGAJAM_RULES_NOTES_v01.md` |
| D1.2 **IP cleanse** — sweep + grep gate | commit |
| D1.3 Confirm Faith Community Church via Street View | anchor |
| D1.4 **Disable DLSS/StreamlineNGXCommon/XeSS — FSR only** | commit |
| D1.5 Verify both UE seats launch | console logs |
| D1.6 Commander signs off on callsigns, bestiary, bounds | signed plan |

### D2 — DESIGN (1 day)
| Step | Output |
|---|---|
| D2.1 Art bible — palette, night lighting, machine language | `ART_BIBLE_v01.md` |
| D2.2 Bestiary spec — 16 units, silhouette, scale, moveset | `BESTIARY_SPEC_v01.md` |
| D2.3 Squad spec — 3 callsigns, powers, banter | `SQUAD_SPEC_v01.md` |
| D2.4 Tech architecture — WP, streaming, LOD, budgets | `TECH_ARCH_v01.md` |
| D2.5 **VO script** — ~2,000 lines | `VO_SCRIPT_v01.md` |
| D2.6 **Cutscene breakdown** — intro + beats, engine per beat | `CUTSCENE_PLAN_v01.md` |
| D2.7 Sourcing dossier — Fab / Megascans / PolyHaven / Sketchfab / Kenney / Mixamo | `SOURCING_DOSSIER_v01.md` |

### D3 — DEVELOP

| Pass | Produces | Node | Gate |
|---|---|---|---|
| **P0** | Ground truth: Street View anchors, USGS 3DEP, OSM **with names**, UE seat verify | Laptop data · Main UE | all anchors photo-confirmed |
| **P1** | **Crew rebuilt** — 4 command + 3 squad, 25–35k tris | Main | hero + turnaround each |
| **P2** | **Texture bake** — 2K PBR, FBX embedded | Main | UE import correct |
| **P3** | **Bestiary** — 16 units × MARK I–IV, rigs, anims | Main | render sheet per unit |
| **P4** | **Scooter + rider** — Laped, cyber-kitbash, mount/dismount | Main | on/off-bike renders |
| **P5** | **Plymouth geo** — terrain, roads, coast, 12 zones, buildings, power | Main UE | flythrough |
| **P6** | **VOICE** — `tts-on` → ~2,000 lines → `tts-off` | HTPC :8020 | spot-check 20, no clipping, RAM released |
| **P7** | **Wildlife** — 13 species, behaviour trees, ambience | HTPC (window closed) → Main | in-level capture |
| **P8** | **Level assembly** — WP, R1/R2, hooks, fight zones, squad AI | Main | playable in editor |
| **P9** | **CUTSCENES** — intro (H3/Seedance) + Sequencer beats | Main | capture review |
| **P10** | **Package** — Win64, run the real exe | Main → Deck | runs on Deck at target fps |

**Fight zones:**

| Zone | Enemies |
|---|---|
| **Pilgrim Hill — CVS / Walgreens** | massed MITEs + HOUND packs |
| **McGovern Chevrolet** | **named heavy** (TBD) + BULWARK escort |
| **McDonald's / Samoset strip** | mixed flesh + SENTRY overwatch |
| **Seven Hills / South Meadow** | traffic hazard + WARDEN jamming your scooter |
| **Power station + transmission lines** | ANVIL turrets, DRIFTERs on the lines |
| **Oak St** | ambush corridor, SPINNER (no easy out) |

### D4 — DEBUG (1 day)
Ebert gate: **≥ 6.2 weighted, no rounding, any axis at 1.0 = categorical fail**, min 5 screenshots + console audit per artifact. Run the real packaged exe. Test on Deck.

### D5 — DOCUMENT (continuous)
Conductor files every fix. `CHANGELOG.md` at root with an **ESV verse** per entry. `REPORT_*.md` per asset. `ITERLOG_*` per batch.

### D6 — DELIVER (Nov 11–15)
Build + dev log + capture reel. **Glass Box** = the honest pipeline: one workstation, three appliances, a cloned-voice cast, a 102 sq mi corridor built from public geodata.

### D7 — DEPLOY
Package to Main, mirror to Deck, push all nodes locally **then** GitHub. **Local File Explorer path** before anything publishes.

---

## §17 — FILE NAMING

**`<CAT>_<Asset>_<Variant>_v<NN>.<ext>`**

| Prefix | Domain |
|---|---|
| `MAP_` | maps, bounds, routes |
| `CRW_` | crew |
| `BST_` | bestiary |
| `WLD_` | wildlife |
| `VEH_` | scooter, vehicles |
| `BLD_` | buildings |
| `PRP_` | props |
| `TEX_` | textures |
| `VO_` | voice lines |
| `SFX_` | audio effects |
| `CUT_` | cutscenes |

`CRW_RIGGER_v03.fbx` · `CRW_RIGGER_view-hero_v03.png` · `VO_RIGGER_bark_reload_01_v01.wav` · `CUT_INTRO_v01.mp4` · `MANIFEST_crew_v03.json` · `ITERLOG_crew_v03.md`

Two-digit versions · never reuse · every iteration ships its renders.

---

## §18 — CONDUCTOR

| Track | Title | State |
|---|---|---|
| 10 | Plymouth level blockout | **done** — superseded |
| 11 | IP cleanse + FSR-only config | **ready** — D1, blocking |
| 12 | Crew high-poly rebuild | **ready** — P1 |
| 13 | Texture bake pipeline | blocked on 12 |
| 14 | Bestiary expansion + rename | blocked on 11 |
| 15 | Scooter + rider | **ready** — P4 |
| 16 | Plymouth geo rebuild (12 zones) | **ready** — P5 |
| 17 | Voice cast (~2,000 lines, on-demand TTS) | **ready** — P6, HTPC |
| 18 | Wildlife system | blocked on 16, HTPC window |
| 19 | Level assembly + routes R1/R2 | blocked on 15,16 |
| 20 | Squad system | blocked on 12 |
| 21 | Cutscenes + intro (H3 / Sequencer) | blocked on 19 |
| 22 | Packaging + Deck validation | blocked on 19 |
| 23 | MegaJam submission | blocked on 22 |

---

## §19 — RISKS

| Risk | Mitigation |
|---|---|
| HTPC memory | **Mitigated** — TTS off by default (−2.18 GB), zram 2 GB, swap 62 %. Upgrade is the structural fix |
| llama-server holds 2.6 GB in swap until restarted | Human-only restart (window-owns-inference). Not an agent action |
| **Main is the only compute node** | CPU (24t) vs GPU (Cycles/Lumen) inside it; 14–18 h/day |
| Deck RAM 660 MB free | Validation only, never asset work |
| Laptop overload kills command | **Zero compute, locked** |
| Overpass down / rate-limited | Retry kumi.systems; Geofabrik MA offline fallback |
| Procedural materials don't survive FBX | P2 bake mandatory |
| TTS ~11× realtime | Batch overnight; `tts-off` after; never runtime |
| ComfyUI on Main is DOWN | Start window-owned before any H3 work |
| Seedance costs money | Explicit Commander authorization |
| Genie 4 unavailable | Waitlist only — previs accelerator, never a dependency |
| 15 days to jam | D1+D2 = 1.5 d; P7/P9 compress first |
| Callsign + voice-key IP | Internal only, renamed on export |
| Your GPU is sacred | Check game launchers before every Main dispatch |

---

## §20 — DECISIONS NEEDED

1. **Crew scope** — 4 command crew, or all 21? *(Recommend 4 + 3 squad = 7, done properly, all voiced)*
2. **Bestiary names** — approve GRAYTIDE / RATLINE / DRIFTER / BULWARK / HARROWER + 11 machines?
3. **Squad callsigns** — RIGGER / SABLE / PARSON?
4. **Named heavyweight at McGovern Chevrolet** — who or what?
5. **HTPC during the asset sprint** — inference window closed, or add RAM?
6. **Seedance** — authorize paid cloud for the trailer, or local H3 only?
7. **Genie 4** — want me to prep the waitlist + a Plymouth prompt sheet?
8. **MegaJam** — submitting, or purely our game?

---

*Next action on your word: D1.2 (IP cleanse) + D1.4 (FSR-only) are the first commits.*
