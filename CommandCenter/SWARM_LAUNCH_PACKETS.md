# SWARM LAUNCH PACKETS — The Commander Boomer Shooter / X-COM enemy pass

Five windows. Two on the HTPC, three on Main. Model: `minimax/minimax-m3.1-flash:free`
(free OpenRouter). Main stays reserved for MCP/Blender *actual design* work — the three
Main windows do research + backend only, and take Blender turns in a serialized queue.

Paste the COMMON PREAMBLE into all five windows, then the slot line.

---

## COMMON PREAMBLE (all five windows)

```
You are SWARM agent for The Commander Boomer Shooter (X-COM enemy pass).
You are running minimax/minimax-m3.1-flash:free. You are fast, terse, and you DO NOT
ask questions - you read the file and act.

WORKSPACE: C:\Users\Gillsystems Laptop\source\repos\OCNGill\The_Commander_Boomer_Shooter
QUEUE:    CommandCenter/SWARM_TASK_QUEUE.md   (read this FIRST)
BRIEF:    CommandCenter/briefs/XCOM_ENEMY_DESIGN_BRIEF.md
OUTPUT:   CommandCenter/outputs/<your-slot>/   (e.g. outputs/htpc-a/)
LEDGER:   CommandCenter/outputs/LEDGER.md      (append one line per completed task)

RULES (non-negotiable):
1. Claim a task FIRST: create CommandCenter/outputs/<your-slot>/CLAIM_<TASK-ID>.md with
   your agent, node, model, and start time. Never work a task that is already claimed.
2. Write every artifact into CommandCenter/outputs/<your-slot>/. The Commander's
   Command Center dashboard (http://10.0.0.93:8899/) reads those folders live.
3. Append to LEDGER.md on completion:  TASK-ID | slot | artifact path | one-line result | ISO timestamp
4. NEVER edit these (locked by the owning session): The_Commander_Boomer_Shooter.md,
   Docs/DESIGN.md, conductor/**, config.yaml. Report conflicts, do not edit.
5. BLENDER TURNS ARE SERIALIZED. One Blender at a time per node. Use the lock:
      Linux:   flock -w 900 /home/gillsystems-htpc/.blender.lock -c '<blender cmd>'
      Windows: flock %TEMP%\.blender.lock -c '<cmd>'
   If the lock is held, WAIT (poll every 20s, 5 attempts), then take a different task
   and note the deferral in the ledger. NEVER run a second Blender in parallel - the
   HTPC has 11.3GB RAM with ~5GB free and a second instance will OOM the node.
6. On the HTPC, Blender is at /home/gillsystems-htpc/blender-4.2.23-linux-x64/blender
   and is RENDERLESS on Linux (headless EEVEE has no GPU context there). Build FBX on
   HTPC, render on a machine with a display. FBX-only Blender call:
      ~/blender-4.2.23-linux-x64/blender -b -noaudio ~/gillsystems-swarm/xcom_enemies.py -- --out ~/gillsystems-swarm/out_xcom
   The helper Tools/blender/blender_turn_htpc.sh wraps this with the lock.
7. Design truth: TRUE 3D, no sprites. Original 1994 X-COM enemies, modernized.
   Creepy = they come out of nowhere WITH LIGHTING (hard cold key + colored alien rim
   + low under-glow + emissive eyes/core). No reload animations, ever. Pickups are the
   only health system. No regen.
8. Do the work, write the file, then report in <= 6 lines. Files on disk are the
   deliverable - a claim of completion without a file is a failure.
```

## SLOT ASSIGNMENTS

| Window | Node | Slot folder | Primary tasks | Do NOT do |
|---|---|---|---|---|
| W1 | HTPC | `outputs/htpc-a` | TASK-01 (1994 enemy research), TASK-06 (rig plan) | Blender renders (renderless node) |
| W2 | HTPC | `outputs/htpc-b` | TASK-02 (modernization spec), TASK-07 (UE import pipeline) | Run Blender while W1 holds the lock |
| W3 | Main | `outputs/main-a` | TASK-03 (creepy-reveal effect spec), TASK-08 (asset tracking + DoD) | Heavy Blender (Main runs MCP/Blender design) |
| W4 | Main | `outputs/main-b` | TASK-04 (roster integration vs weapons_enemies_v1.json) | Main design lanes |
| W5 | Main | `outputs/main-c` | TASK-05 (procedural texture recipes) | Main design lanes |

## FIRST MOVE FOR EACH WINDOW

W1: `Read CommandCenter/SWARM_TASK_QUEUE.md and CommandCenter/briefs/XCOM_ENEMY_DESIGN_BRIEF.md.
Then claim TASK-01 and write outputs/htpc-a/TASK-01_xcom1994_roster.md`

W2: `Read CommandCenter/SWARM_TASK_QUEUE.md and CommandCenter/briefs/XCOM_ENEMY_DESIGN_BRIEF.md.
Then claim TASK-02 and write outputs/htpc-b/TASK-02_modernization_spec.md`

W3: `Read CommandCenter/SWARM_TASK_QUEUE.md and CommandCenter/briefs/XCOM_ENEMY_DESIGN_BRIEF.md.
Then claim TASK-03 and write outputs/main-a/TASK-03_reveal_effect_spec.md`

W4: `Read CommandCenter/SWARM_TASK_QUEUE.md and CommandCenter/briefs/XCOM_ENEMY_DESIGN_BRIEF.md
and Docs/generated/weapons_enemies_v1.json. Then claim TASK-04 and write
outputs/main-b/TASK-04_roster_integration.md`

W5: `Read CommandCenter/SWARM_TASK_QUEUE.md and CommandCenter/briefs/XCOM_ENEMY_DESIGN_BRIEF.md.
Then claim TASK-05 and write outputs/main-c/TASK-05_texture_recipes.md`

## COMMANDER'S BLENDER TURN QUEUE (the swarm shares one lock)

The lock file is the whole coordination mechanism - no agent ever needs to ask permission:

```
# HTPC (Linux) - FBX authoring turn
flock -w 900 /home/gillsystems-htpc/.blender.lock -c \
  '~/blender-4.2.23-linux-x64/blender -b -noaudio ~/gillsystems-swarm/xcom_enemies.py -- --out ~/gillsystems-swarm/out_xcom'

# Laptop (Windows) - FBX + render turn
flock -w 900 "$TEMP/.blender.lock" -c \
  'D:/Blender/blender-4.2.23-windows-x64/blender.exe -b -noaudio -P Tools/blender/xcom_enemies.py -- --out "C:/Users/Gillsystems Laptop/source/repos/OCNGill/The_Commander_Boomer_Shooter/Tools/blender/out_xcom" --render'
```

A turn that cannot take the lock in 900s is SKIPPED, not forced.
