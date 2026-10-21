# SWARM TASK QUEUE — The Commander Boomer Shooter / X-COM enemy pipeline

Commander-directive: swarm of agents researches characters + does the backend grunt work,
takes turns on Blender, and writes every artifact into `CommandCenter/outputs/<your-slot>/`
so the Command Center dashboard (http://10.0.0.93:8899/) shows ALL of it together.

## HOW TO CLAIM A TASK
1. Pick an UNCLAIMED task (no `.claim` file next to it).
2. Create the claim marker BEFORE you start:
   `CommandCenter/outputs/<your-slot>/CLAIM_<TASK-ID>.md` containing: agent, node, model, start time.
3. Do the work. Write your artifact into `CommandCenter/outputs/<your-slot>/<TASK-ID>_<slug>.md`.
4. When done, append a line to `CommandCenter/outputs/LEDGER.md`:
   `TASK-ID | <slot> | <artifact path> | <one-line result> | <iso timestamp>`
5. Never write outside `CommandCenter/outputs/<your-slot>/` and `Docs/generated/`.
6. NEVER edit `The_Commander_Boomer_Shooter.md`, `Docs/DESIGN.md`, or `conductor/` — those are locked
   design + the session owner's. Report conflicts instead of editing.

## BLENDER TURN-TAKING (RAM discipline — HTPC has 11.3GB total, ~5GB free)
- One Blender process at a time on a node. Use the lock:
  `flock /home/gillsystems-htpc/.blender.lock -c '<your blender command>'`
  (HTPC) or `flock %TEMP%\.blender.lock -c '<cmd>'` (Windows nodes).
- If the lock is held, WAIT — do not run a second Blender. Poll every 20s, max 5 attempts,
  then take a different task and note the deferral in the ledger.
- Keep each render <= 3 models, 720x900, EEVEE, 48 samples. Cycles only if asked.
- Copy results to the repo (`Tools/blender/out_xcom/`) only when the lock is yours.

## TASK INDEX
| Task | Slot hint | Deliverable |
|---|---|---|
| TASK-01 | HTPC-A | X-COM 1994 enemy research: exact roster, silhouettes, reveal-lighting behaviour in the 1994 game, what each looked like on the Battlescape |
| TASK-02 | HTPC-B | Modernization spec per enemy: polycount budget, texture approach (procedural vs baked), material breakdown, UE import settings |
| TASK-03 | MAIN-A | "Creepy reveal" effect spec: spawn light rig, emissive channels, sound cue, camera treatment — for enemies appearing out of nowhere |
| TASK-04 | MAIN-B | Enemy roster integration vs existing `Docs/generated/weapons_enemies_v1.json` (6 enemies already specced) — map X-COM originals onto them, flag conflicts |
| TASK-05 | MAIN-C | Textures: author a procedural texture recipe (chitin, bone, armor plate, plasma) + a UV/uniform layout convention |
| TASK-06 | HTPC-A | Rig plan: skeleton, bone list, animation set needed for each enemy (idle, telegraph, attack, death, gib) |
| TASK-07 | HTPC-B | UE5 import pipeline for the new enemy FBX kit: naming, collision, LOD, material instances, and the UE-side spawn script |
| TASK-08 | MAIN-A | Naming/asset-tracking sheet (FBX -> UE asset path) + the DoD checklist for the enemy pass |

## HARD DESIGN LOCKS (do not violate)
- True 3D only. NO sprites, NO billboard impostors for enemies.
- Original X-COM enemies only (Sectoid, Viper, Floater, Muton, Chryssalid + bosses) — modernized, not re-invented.
- Main character/player: NOT in scope this pass.
- Zero reload animations (weapons contract) — applies to enemy weapons too.
