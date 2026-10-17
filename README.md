<p align="center">
  <img src="https://raw.githubusercontent.com/OCNGill/Gillsystems-AMD-Radeon-llama-cpp-Update-AI-Stack/main/Gillsystems_logo_stuff/Gill%20Systems%20Logo.png" alt="Gill Systems Logo" width="800">
</p>

# The Commander — Boomer Shooter

> *"Duke Nukem meets Doom meets Mass Effect."*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Engine](https://img.shields.io/badge/Engine-Unreal%205.8-blue?logo=unrealengine)](TheCommander.uproject)
[![Assets](https://img.shields.io/badge/Assets-Blender%204.x-orange?logo=blender)](Docs/DESIGN.md)
[![Status](https://img.shields.io/badge/Status-project%20initialized-brightgreen)](CHANGELOG.md)
[![Target](https://img.shields.io/badge/Target-itch.io%20%7C%20Steam-lightgrey)](conductor/tracks.md)
[![Docs](https://img.shields.io/badge/7D-Documented-lightgrey)](conductor/)

**The Commander** is a fast-paced retro FPS — a boomer shooter built in **Unreal Engine
5.8** with a **Blender** asset pipeline. It is the Commander's personal project: Doom 2016
movement, overpowered guns, telegraphed enemies with satisfying gibs, keycards and secrets,
and a hard 144+ FPS target at 1440p. No stamina bars, no tactical reloads, no balance over fun.

The project is currently at **stage: UE 5.8 project initialized** — the `.uproject`,
engine config, and the authoritative design brief are in place; gameplay tracks are next.

## Contents

- [Overview](#overview)
- [Design Contract](#design-contract)
- [Hard Performance Targets](#hard-performance-targets)
- [Never Suggest](#never-suggest)
- [Architecture](#architecture)
- [Project Layout](#project-layout)
- [Quick Start](#quick-start)
- [Asset Pipeline](#asset-pipeline)
- [Development Rules](#development-rules)
- [Roadmap](#roadmap)
- [Documentation & 7D](#documentation--7d)
- [Agent Roster](#agent-roster)
- [License](#license)
- [Support / Donate](#support--donate)

---

## Overview

| | |
|---|---|
| **Genre** | Retro FPS / boomer shooter |
| **Engine** | Unreal Engine 5.8 (Blueprints-first) |
| **Asset tooling** | Blender 4.x via the blender-mcp skill |
| **AI assist** | Local llama.cpp (Qwen3.8-27B) — sovereign, no cloud |
| **Targets** | itch.io / Steam |
| **Status** | UE 5.8 project initialized (commit `cef143e`) |

Two design documents drive the build:

- [`Docs/DESIGN.md`](Docs/DESIGN.md) — **authoritative** design brief, Unreal edition. Ported
  from the original prompt and re-pointed from Unity to Unreal Engine 5.8 + Blender by
  Commander directive (2026-08-12).
- [`The_Commander_Boomer_Shooter.md`](The_Commander_Boomer_Shooter.md) — the original LLM
  assistant prompt the brief was ported from.

## Design Contract

| Area | Rule |
|---|---|
| **Movement** | Doom 2016, *not* Doom Eternal — with a hint of Rise of the Triad meets 007 GoldenEye. ≥ 15 units/sec (600 UU/s in Unreal terms) treated as a floor. Raw mouse input: no smoothing, no acceleration. |
| **Weapons** | Instant weapon switching, every gun overpowered, high projectile speeds. Fire is immediate — no coroutine/delay on the trigger pull. |
| **Health** | Classic pickups only. No regeneration. |
| **Enemies** | Telegraphed attacks, satisfying gibs, no hitscan for the player's "feel" weapons. Enemy projectiles are telegraphed. |
| **Level design** | Keycards, secrets, verticality. Some linearity plus some side mazes. Hazards in the spirit of Pitfall and Tomb Raider. Plymouth, MA themed levels. |
| **Flavor** | One-liners: "Sudo kill -9", "Noobs Detected", "Commander STOMPED", "ROBOT". |
| **ADS / cover** | Aim down sights allowed. Cover allowed **only as geometry to hide behind** — never as a game mechanic. |

## Hard Performance Targets

| Target | Value |
|---|---|
| Frame rate | 144+ FPS at 1440p |
| Movement speed | ≥ 600 UU/s |
| Mouse input | Raw, unsmoothed |
| Feedback | Screen shake + blood + gibs on every kill |

## Never Suggest

Hard "no" list from the design brief — these do not belong in this game:

- Cover systems as mechanics
- Stamina bars
- Realistic reload times
- RPG elements (XP, skill trees, stat screens)
- Tactical gameplay
- "Balance" over fun

```
WRONG:  StartCoroutine(ReloadAnimation());   // any delay on firing
RIGHT:  FireRocket();                        // instant, overpowered, shake + BOOM
```

## Architecture

```
            THE COMMANDER — SOVEREIGN GAME PIPELINE

  Blender 4.x (blender-mcp)          Local llama.cpp (Qwen3.8-27B)
   models → retopo → UV → rig              code / Blueprint assist
             │ FBX export                          │
             ▼                                     ▼
        ┌────────────────────────────────────────────────┐
        │  Unreal Engine 5.8  (TheCommander.uproject)   │
        │  Blueprints-first · C++ only if 144+ FPS      │
        │  demands it · Config/ engine settings         │
        └───────────────────────┬────────────────────────┘
                                │
             local build only (no CI for game builds)
                                │
                                ▼
                       itch.io / Steam release
```

## Project Layout

```
The_Commander_Boomer_Shooter/
├── TheCommander.uproject            # UE 5.8 project descriptor (Blueprints-only, no modules)
├── Config/
│   ├── DefaultEngine.ini            # Engine settings
│   └── DefaultGame.ini              # Project settings
├── Docs/
│   └── DESIGN.md                    # Authoritative design brief (Unreal edition)
├── The_Commander_Boomer_Shooter.md  # Original LLM design prompt (porting source)
├── Content/                         # Unreal content folders (editor-created; not tracked yet)
├── conductor/                       # Product definition, tracks, workflow, tech stack
│   └── CHANGELOG.md                 # Symlink to the repo-root CHANGELOG.md
├── CHANGELOG.md                     # 7D change log, ESV verse per milestone
├── ROSTER.md                        # Agents on this project
├── LICENSE                          # MIT
└── .gitignore                       # UE build artifacts (Binaries/, Intermediate/, Saved/, *.sln)
```

## Quick Start

1. Install **Unreal Engine 5.8** (Epic Games Launcher) and **Blender 4.x** on the dev machine.
2. Clone the repository: `git clone git@github.com:OCNGill/The-Commander-Boomer-Shooter.git`
3. Double-click `TheCommander.uproject` to open the project in the UE 5.8 editor.
4. Read [`Docs/DESIGN.md`](Docs/DESIGN.md) **before** touching a Blueprint — it is the contract.
5. Author assets in Blender via the blender-mcp skill, export FBX, import into `Content/`, then start the first gameplay track in [`conductor/tracks.md`](conductor/tracks.md).

## Asset Pipeline

1. **Blender** (blender-mcp) authors all assets — models → retopo → UV → rig → FBX.
2. **Unreal 5.8** is the runtime.
3. **Blueprints-first**; C++ only if Blueprints cannot hit the 144+ FPS budget cleanly.
4. **Sovereign local builds only** — no GitHub Actions for game builds.

## Development Rules

- Code assist runs on the local llama.cpp stack (Qwen3.8-27B) — no cloud inference in the loop.
- Git LFS is the plan for binary assets (see [`conductor/tech-stack.md`](conductor/tech-stack.md)).
- Every milestone lands with a `CHANGELOG.md` entry in `## [YYYY-MM-DD]` format plus an ESV verse.

## Roadmap

From [`conductor/tracks.md`](conductor/tracks.md):

| # | Track | Status |
|---|---|---|
| 1 | UE5 project initialization (brief + `.uproject`) | **Complete** — Deploy ✓ |
| 2 | Blender asset pipeline (blender-mcp): weapons, enemies, levels | Future |
| 3 | Core combat loop: movement, shooting, enemy AI | Future |
| 4 | Level design: Plymouth, MA themed levels | Future |
| 5 | Local AI integration: Qwen3.8-27B Blueprint assist | Future |
| 6 | itch.io / Steam release (sovereign deployment) | Future |

## Documentation & 7D

- [`Docs/DESIGN.md`](Docs/DESIGN.md) — the design contract.
- [`CHANGELOG.md`](CHANGELOG.md) — 7D change log, newest first, verse per milestone.
- [`ROSTER.md`](ROSTER.md) — agents on this project.
- `conductor/` — product definition, track registry, workflow, tech stack.
- Fleet governance: `MASTER_CHARTER.md` in [Gillsystems-Commanders-Hermes](https://github.com/OCNGill/Gillsystems-Commanders-Hermes).

## Agent Roster

| Agent Name | Role |
|---|---|
| Commander Hermes | Commander's primary interface |
| Geordi | UE5 architecture, Blueprint design |
| Coder | Blueprint logic, C++ if needed |
| Liara | Asset research, Blender-MCP workflows |
| Scribe | 7D docs (CHANGELOG + conductor) |
| Major-Gaben | Hardware validation (main rig) |

Full detail lives in [`ROSTER.md`](ROSTER.md).

## License

MIT — © 2026 Stephen Gill / Gillsystems. See [`LICENSE`](LICENSE).

## Support / Donate

Back the Commander's personal project:

**[paypal.me/gillsystems](https://paypal.me/gillsystems)**