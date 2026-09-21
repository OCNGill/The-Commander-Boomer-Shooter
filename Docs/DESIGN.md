# The Commander — Boomer Shooter Design Brief (Unreal Edition)

> Ported from `The_Commander_Boomer_Shooter.md` (2026-02-09). Engine target overridden
> from Unity to **Unreal Engine 5.8 + Blender** by Commander directive (2026-08-12,
> locked in via Liara's research: `Gillsystems-Commanders-Hermes/research/mcp-blender-gameengine.md`).

## Core Design

- **Movement**: Doom 2016, NOT Doom Eternal. A hint of Rise of the Triad meets 007 GoldenEye.
  - ≥ 15 units/sec (600 UU/s in Unreal terms) base movement — treat as a floor.
  - Raw mouse input, no smoothing, no acceleration.
- **Weapons**: No reload animations. Instant weapon switching. Every gun overpowered.
- **Health**: Classic pickups only. No regeneration.
- **Enemies**: Telegraphed attacks, satisfying gibs, NO hitscan for the player's "feel" weapons
  (projectile speeds high). Enemies may use telegraphed projectiles.
- **Level Design**: Keycards, secrets, verticality. Some linearity, some side mazes.
  Hazards in the spirit of Pitfall and Tomb Raider.
- **One-liners**: "Sudo kill -9", "Noobs Detected", "Commander STOMPED", "ROBOT".
- Aim Down Sights: allowed. Cover: allowed ONLY as geometry to hide behind — never a game mechanic.

## Hard Performance Targets

| Target | Value |
|---|---|
| Frame rate | 144+ FPS |
| Movement speed | ≥ 600 UU/s |
| Mouse input | Raw, unsmoothed |
| Feedback | Screen shake + blood + gibs on every kill |

## What We Generate

- Movement controllers with strafing (Blueprint `BP_CommanderCharacter`)
- Weapon scripts (Blueprint or C++) with high projectile speeds
- Enemy AI that is aggressive but fair (Behavior Trees, telegraph-first)
- Level blockouts with multiple routes
- Blender asset pipeline: models → retopo → UV → rig → FBX → Unreal import

## NEVER Suggest

- Cover systems (as mechanics)
- Stamina bars
- Realistic reload times
- RPG elements (XP, skill trees, stats screens)
- Tactical gameplay
- "Balance" over fun

## Anti-pattern example (from the original brief)

```
WRONG:  StartCoroutine(ReloadAnimation()); // any delay on firing
RIGHT:  FireRocket(); // instant, overpowered, shake + BOOM
```

## Pipeline (locked in)

1. **Blender** (blender-mcp) authors all assets.
2. **Unreal 5.8** (`D:\Unreal_Engine\UE_5.8`) is the runtime.
3. Blueprints-first; C++ only if Blueprints cannot hit the 144+ FPS budget cleanly.
4. Sovereign local builds only — no GitHub Actions for game builds.
