# Crew Character Pipeline — Spec (v0.2)

> **Goal:** turn the 16 modeled characters (see `Docs/CREW_CHARACTERS.md`) into UE 5.8
> assets. **The game is a boomer shooter** (DESIGN.md) — these are the *companions and
> the System's faces* that the story layer (SYSTEM_FRAMEWORK.md) puts in the world.
> **Sovereign pipeline:** Blender 4.2.23 (D:\Blender, headless) → FBX → UE `/Game/Characters/`.
> No paid pipelines. Animations: Mixamo (free) or Blender-authored. Quality gate: **Ebert** ≥8.5.

---

## 1. Pipeline (locked)

```
1. Blender (headless, D:\Blender\blender.exe -b)
     - build the body/face/gear per CREW_CHARACTERS.md spec
     - apply the emissive "conduit" materials (cyan/violet per character)
     - export FBX (UE 5.8 preset: forward axis -Z, up Y)
2. UE 5.8 import
     - FBX → Static Mesh (or Skeletal Mesh if rigged)
     - → /Game/Characters/Player/  (The Commander)
     - → /Game/Characters/Crew/    (the agents)
     - → /Game/Characters/Enemies/ (the System)
3. Mixamo (free)
     - upload the FBX, rig to the Mixamo skeleton
     - download the animation FBX (idle, walk, run, emote)
     - import as UE Skeletal Animations on the UE mannequin skeleton
4. Ebert gate
     - Ebert scores the asset 0–10 from 5+ screenshots + console audit
     - < 8.5 → send back to Blender with the ranked issue list
     - ≥ 8.5 → GATED, ship it
```

> **Why Blender headless (no MCP needed):** the XCOM kit proved it — `Tools/blender/*.py`
> scripts build models, export FBX, and emit the reveal/silhouette PNGs. We reuse that
> exact pattern for the crew.

---

## 2. Output Contract (per character)

Each character produces, under `Tools/blender/out_crew/`:

| File | Purpose |
|---|---|
| `CREW_<Name>.fbx` | The model, UE-preset, ready to import. |
| `CREW_<Name>.png` | Reveal render (the "reveal_cast" spot, overhead). |
| `CREW_<Name>_turn.png` | Turn-table (4 views). |
| `CREW_<Name>_silh.png` | Silhouette plate (shape check). |
| `CREW_<Name>_scale.png` | Scale plate (with a 1.8 m human ref). |
| `crew_manifest.json` | The metadata (tris, height, emissive px, silhouette note, changed_vs_v1). |

> The manifest shape is the **XCOM manifest** (`Tools/blender/out_xcom/xcom_manifest.json`)
> — we copy its exact schema so the Ebert gate + UE import can consume it without changes.

---

## 3. Character Spec → Blender Parameters

Each `CREW_CHARACTERS.md` entry maps to a Blender build parameter. The build script
(`Tools/blender/crew_build.py`) reads a JSON spec per character:

```json
{
  "name": "HERMES",
  "height_m": 1.85,
  "body": "tall_lean",
  "face": "calm_authoritative",
  "palette": { "primary": "#2B3A42", "accent": "#19E3FF", "trim": "#B08D57" },
  "conduits": [ {"from": "neck", "to": "left_temple", "color": "#19E3FF"} ],
  "distinguishing": ["brass_compass_pins", "neural_port_left_temple"],
  "emissive": true,
  "rig": "humanoid"
}
```

> **LIARA LOCK (Commander 2026-10-23):** `hair: "up_swept_bun"`, `antennae: false`,
> `tentacles: false`, `head_attachments: ["neural_fiber_left", "data_jack_left_ear"]`,
> `palette: { "primary": "#101014", "accent": "#B319FF", "iris": "#B319FF" }`.
> **No things hanging off the head.** Cyberpunk: asymmetric violet pauldron.

---

## 4. Animation (Mixamo, free)

- Upload each crew FBX to **Mixamo** (free, Adobe).
- Rig to the **Mixamo Humanoid** skeleton.
- Download: `idle`, `walk`, `run`, `emote_gesture`, `sit`.
- Import into UE as `AnimBP_Crew` skeletal animations on the UE mannequin skeleton.
- The **Commander** (player) gets the full combat set (the existing boomer-shooter
  animations carry over).

> **Why not Blender-authored anims for everyone:** Mixamo is free, rigged to a standard
> skeleton, and UE-native. We author in Blender only the *emote gestures* that are
> character-specific (Hermes' "telemetry acknowledged" nod, Liara's data-jack flick).

---

## 5. Quality Gate (Ebert)

- **Ebert** (the brutal art-director critic, 7-axis Likert, PASS ≥ 6.2 / AAA ≥ 8.5)
  scores every crew asset.
- **Evidence required:** 5+ screenshots (reveal, turn, silh, scale, in-UE) + console audit.
- **Below gate:** Ebert returns a ranked issue list → back to Blender → re-score.
- **Above gate:** the asset is `GATED` and ships. No asset ships on a "should be fine."

> **Zero-trust:** every FBX is byte-verified (sha256) after export and after UE import.
> The manifest's `tris` / `height_m` / `emissive_px` are re-checked against the UE import.

---

## 6. Build Order (Act 1)

1. **HERMES** (the first face) — the Fleet's commander, the player's right hand.
2. **LIARA** — Commander-locked spec (semi-liara, cyberpunk, no head attachments).
3. **GEORDI** — the engineer, the warmth.
4. **EDI** — the light-form (cheapest: a hologram, not a full body).
5. **THEO, MEDIC, SCOUT** — Act 1 support.
6. **The rest** — Act 2+.

---

*Verse: "Whatever your hand finds to do, do it with your might." — Ecclesiastes 9:10 ESV. The crew is who we are. We model them, we rig them, we ship them. No test prompts.*
