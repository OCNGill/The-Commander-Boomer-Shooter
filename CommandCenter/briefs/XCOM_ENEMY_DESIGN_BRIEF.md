# X-COM ENEMY PASS - DESIGN BRIEF (Commander, 2026-10-21)

**Mandate.** Original *UFO: Enemy Unknown* (Mythos Games / MicroProse, 1994) enemies,
modernized into true 3D for *The Commander*. Not Doom sprites, not re-invented originals -
the 1994 roster, rebuilt for a 2020s engine.

**The creeping part.** In 1994 the terror missions worked because the Battlescape was dark
and aliens appeared in a hard flash of light - you saw them *arrive*, lit from nowhere.
Every enemy here ships with: a hard cold key, a colored alien rim, a low under-glow, and
emissive eyes/core, so the reveal reads even in total darkness. In UE this becomes a spawn
light rig driven by the spawn event - authored in Blender as `reveal_key` / `reveal_rim` /
`reveal_under`, replicated as point/spot lights on the spawn actor.

## ROSTER (base pass - 5 built)
| Enemy | 1994 role | Modern read | Signature |
|---|---|---|---|
| **Sectoid** | psychic infiltrator | gaunt infiltrator, oversized cranium | luminous eyes, no mouth, bare skull |
| **Viper** | the marquee alien, plasma rifle | tall reptilian hunter, ribbed spine | elongated snout, back ribs, plasma pistol |
| **Floater** | psychic hover, mind control | manta-like floater, no legs | glowing dorsal core, trailing tendrils, hover |
| **Muton** | armored heavy, terror-showstopper | armored heavy, visor slit, heavy rifle | shoulder plates, oxblood chest accent, heavy plasma rifle |
| **Chryssalid** | terror from the deep, skitters | insectoid stalker, scythe arms | scythe forelimbs, venom glow, low fast silhouette |

Second wave (not yet modeled): **Ethereal** (mind-control leader), **Borg**, **Dreadnought**,
**Celestial**, **Chosen**, **Retinoid** (Orion).

## MATERIALS
- `XCOM_Chitin_Dark` / `_Mid` / `_Pale` - matte-to-satin carapace
- `XCOM_Armor_Plate` (metal 0.65) + `XCOM_Armor_Accent` (oxblood) - Muton only
- `XCOM_Eye_Emissive` (emission 14) - every enemy reads in the dark
- `XCOM_Core_Emissive` (emission 22) - dorsal/neck power core, cyan
- `XCOM_Plasma_Emissive` (emission 16) - weapon coils, violet
- `XCOM_Gunmetal` - enemy weapon bodies

## BUILD OUTPUT
`Tools/blender/xcom_enemies.py` -> `Tools/blender/out_xcom/`
- 5 FBX (one per enemy, joined mesh, Y-up, FBX_SCALE_ALL)
- 5 lit preview PNGs (720x900, EEVEE, 48 samples) for review + Ebert scoring
- `xcom_manifest.json` (tris, kb, height per enemy)
