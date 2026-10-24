# The Commander — Product Definition

> **A BOOMER SHOOTER with a story on top.** The backbone never changes: Doom 2016
> movement (≥600 UU/s, raw mouse, no smoothing), overpowered instant-swap guns,
> telegraphed enemies, gibs + screen shake on every kill, 144+ FPS, keycards/secrets/
> verticality. `Docs/DESIGN.md` is locked and carries over untouched.
>
> **The story is a layer, not a genre swap** (Commander 2026-10-24 correction): real-world
> (Plymouth MA, the fleet nodes) + cyber-world (the Grid), RPG elements, story, choices,
> cutscenes, and a modeled crew. Deus Ex / Bioshock / Mass Effect as DNA. The enemy is
> the **real-world System** — shadow govt, big corps (insurance cartels), AI companies,
> captured institutions. Ground zero: Plymouth MA. See `Docs/SYSTEM_FRAMEWORK.md`.

## What
A boomer shooter in Unreal Engine 5.8 that *has* a story, a crew, and choices. You run
fast, you shoot hard, you stomp — and the world has a why.

## Why
"Think bigger" — but "still a boomer shooter." The shooter is the game; the story is the
reason you keep running. Demonstrates the sovereign pipeline at story scale — not AI-slop
test prompts. 7D + Conductor + LearnREA.

## Pillars
| Pillar | Meaning |
|---|---|
| **Boomer core (unchanged)** | Doom 2016 feel, 144+ FPS, gibs, overpowered guns. DESIGN.md is the backbone. |
| **Story layer on top** | Real world + the Grid, the System, choices, cutscenes — wrapped *around* the shooter. |
| **The enemy is real** | Shadow govt, big corps (insurance), AI companies, captured institutions. Plymouth MA ground zero. |
| **Modeled crew** | Every Gillsystems agent is a character with a face, body, station, voice. Liara semi-liara + cyberpunk, no head attachments. Companions, not co-players. |
| **Sovereign pipeline** | UE5.8 + Blender (headless) + Mixamo (free anims) + local inference + Ebert ≥8.5 gate. No paid pipelines. |
| **Choices carry** | Deus Ex / Mass Effect — choices persist across acts and decide who is saved. No XP/stat screens. |

## Architecture
```
The_Commander_Boomer_Shooter/
├── UE5 project (blueprints + C++)
├── Content/Characters/{Player,Crew,Enemies}   <- modeled crew + the System's faces
├── Content/{Maps,Environments,Effects,UI}     <- boomer levels + the Grid + the real world
├── Tools/blender/                              <- crew_build.py + crew_specs/ + out_crew/
├── Docs/
│   ├── DESIGN.md            (boomer-shooter core — the backbone, locked)
│   ├── SYSTEM_FRAMEWORK.md  (the story layer: the System, factions, acts, mechanics)
│   ├── CREW_CHARACTERS.md   (the 16 modeled characters + build order)
│   ├── CREW_PIPELINE.md     (Blender→FBX→UE→Mixamo→Ebert pipeline)
│   └── generated/           (bibles, specs, handoffs)
├── conductor/                                  (7D + Conductor)
└── CHANGELOG.md
```

## Node Map
| Host | Role |
|------|------|
| Main (7900 XTX, 24 GB) | UE5 dev + local inference (Qwen3.8-27B) |
| HTPC (RX 7600) | Blender rendering, ZFS, cold storage |
| Deck (16 GB) | test chamber, quiet builds |
| Laptop (10.0.0.93) | command post, always on |
| Oracle (129.213.114.55) | the relay — the only door the System can see |
| GitHub | version control |

## Quick Start
1. Open `TheCommander.uproject` in UE 5.8 (the boomer core builds as before).
2. Build a crew character: `"D:\Blender\blender.exe" -b -P Tools/blender/crew_build.py -- --char HERMES`
3. Import the FBX → `/Game/Characters/Crew/`. Ebert gates it (≥8.5 to ship).
4. Local inference for NPC dialogue: Qwen3.8-27B on Main (sovereign, no cloud).
5. The story layer (dialogue/choices/crew) is bolted on *between* boomer levels — it never
   slows a firefight.
