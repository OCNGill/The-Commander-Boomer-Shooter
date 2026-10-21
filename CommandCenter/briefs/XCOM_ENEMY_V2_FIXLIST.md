# X-COM ENEMY PASS 2 — FIX LIST (derived from direct vision review of the v1 renders)

Evidence: `Tools/blender/out_xcom/*.png` reviewed with `vision_analyze` on 2026-10-21.
Verdict on v1: **legible clean blockout, not a finished creature.** The renders are
technically clean but the creature does not read as alive, and the "creepy reveal"
lighting is not landing because the scene has no darkness to reveal against.

Every item below is a concrete Blender-side change. Close ALL of them, then re-render
and re-submit to Ebert.

---

## A. GROUNDING — nothing floats
- v1 has **no floor**. Add a large ground plane (6m x 6m cube, 0.1m thick) under the model,
  dark wet concrete material (`XCOM_Ground_Wet`, base 0.03/0.035/0.04, roughness 0.35).
- Every enemy must show a **contact shadow** on that floor. If the feet do not touch the
  floor, lower them until they do.
- Without this, the model reads as a bobblehead pasted on a background.

## B. LIGHTING — the reveal is the whole point
v1's lighting is flat studio light, not a 1994 terror-mission reveal. Fix:
- World background strength: **0.60 -> 0.12** (near-black ambient). The scene must be dark.
- Key: replace the broad AREA light with a **SPOT**, energy ~1400, spot_size ~35deg,
  at (-2.2, -2.6, 3.4) aimed at the chest, with a hard shadow. Cold white-blue (0.62,0.78,1.0).
- Rim: **SPOT** from behind-right (2.8, 2.4, 2.4), energy ~900, color (0.20, 1.0, 0.42)
  (alien green), spot_size ~50deg, so the silhouette edge is separated from the black.
- Under-glow: POINT at (0, -0.5, 0.10), energy 60-90, color (0.45, 0.9, 1.0) — they come
  out of the floor. Keep it subtle; v1 had it too hot.
- **Add a compositor Glare (Fog Glow, quality HIGH, threshold ~0.85) on the render** so the
  emissive eyes and power cores bloom. EEVEE Next has no legacy bloom - the Glare node is
  how you get it. This single change does more for "creepy" than anything else.
- Optional: a faint volumetric haze plane in front of the key so the light shaft reads.

## C. FACE — this is the focal point and it is currently empty
v1 Viper/Muton: a blank cream oval for an eye, no mouth, no structure. The face must carry
the character. For EVERY enemy:
- **Eye assembly** (3 parts): socket rim (flattened torus or scaled ring) + eyeball
  (dark sphere, near-black) + emissive iris disc facing forward. Emissive strength 18-30.
- **Mouth/jaw seam**: a dark inset (thin scaled box or gap between jaw and skull) so the
  head has a real aperture. Viper and Muton get a visible jaw + 4-6 small teeth (cones).
- Viper: elongate the snout, add a nasal ridge, deepen the brow so it looks predatory.
- Muton: the helmet needs a **readable visor slit** (emissive, thin, horizontal) and a
  chin/breath apparatus. The current "cream hook" on the face is illegible - either give it
  a clear identity (mandible, respirator) or remove it.
- Sectoid: canonically mouthless - keep that, but add a nasal slit, a brow ridge, and a
  chin plate so the skull is not a bare sphere.

## D. ANATOMY - connect the parts
v1 reads as "boxes, cylinders and spheres assembled together". Fix with joints:
- Add a **joint sphere** at every articulation: shoulder, elbow, wrist, hip, knee, ankle,
  neck. Each joint sphere must be **inside** the adjoining limb volume so nothing floats.
- Taper limbs: use cones/cylinders with a non-uniform scale instead of uniform cylinders.
  Thin the arms and legs (v1 arms reach the ankles - too long; forearms should end at the hip).
- **Hands**: replace the 3-prong "fork" fingers with a palm block + 3 tapered digits of
  **different lengths**, each attached to the palm.
- Feet: give them toes/claws (2-3 small cones) or reduce their size; v1's "slippers" are
  disproportionately large. Feet must meet the floor.
- No component may be visibly detached: the v1 Viper's left arm and both hands read as
  floating beside the body.

## E. MATERIAL LOGIC - three families, no more
v1 mixes green, sage, white, mint and black with no anatomical logic. Per enemy use exactly:
1. **CHITIN** (flesh/organic) - matte, dark, subtle noise bump
2. **PLATE** (armor/hard shell) - metal 0.5-0.65, mid-value
3. **ACCENT** (emissive / weapon energy) - the only bright color
- **Retire the pale "cloth" material from flesh areas.** Pale/bone is only for bone ridges
  and teeth. The white hands and white boots in v1 were the brightest thing on screen and
  stole focus from the face - they must go dark.
- One restrained accent color per enemy (Muton keeps his oxblood chest plate, but it needs
  detail, not a flat salmon rectangle).

## F. SURFACE STORYTELLING
- Every material gets a **procedural detail pass** (no external textures needed):
  - Noise Texture (scale ~14, detail 6) -> Bump (strength 0.25) for chitin
  - A second noise -> ColorRamp -> mixed into Base Color for mottling/patina
  - Plate material gets a subtle roughness break-up so it is not uniform
- Add **panel lines / seams** on armor: thin dark inset boxes on the chest plate and
  pauldrons (2-3 per enemy). They cost nothing and instantly read as manufactured.
- Muton's chest plate needs an insignia or vent detail - a flat colored rectangle reads
  as placeholder.

## G. GEAR LEGIBILITY
- The v1 plasma pistol is an unidentifiable black box; the Muton rifle is a bar with a ball.
  Every weapon needs: body, **grip** (angled, hand-sized), **trigger guard**, **barrel or
  emitter**, and an emissive coil. Two-handed weapons need a foregrip.

## H. POSE
- v1 is symmetric and stiff. Give each enemy a **stance with intent**: weight on one leg,
  weapon shouldered or raised, head turned ~8 degrees toward camera, one shoulder forward.

## I. CAMERA
- Height 1.2-1.4m (chest height, not above), **40mm lens** for real perspective, model
  fills ~70% of frame height, headroom above the head, floor visible at the bottom so the
  contact shadow lands in frame.

---

## ACCEPTANCE CRITERIA FOR PASS 2
1. All five enemies re-rendered with a floor, contact shadows, and the 3-light reveal rig.
2. Compositor Glare applied - emissive eyes/core visibly bloom.
3. Every enemy has a readable face (eye assembly + mouth/aperture).
4. No floating parts: every limb connected via joint spheres; feet on the floor.
5. Material families: chitin / plate / accent only. No white hands or white boots.
6. Procedural surface detail on every material; panel lines on armor.
7. Weapons legible as weapons.
8. Static, asymmetric, intentional pose per enemy.
9. Re-run: `blender -b -noaudio -P Tools/blender/xcom_enemies.py -- --out <dir> --render`
   then submit the new PNGs to Ebert for re-scoring. **The v1 PNGs are not the deliverable.**

> Psalm 33:6 (ESV) - "By the word of the LORD were the heavens made; and all the host of them
> by the breath of his mouth." Chosen because every asset here is made by command, and the
> swarm only executes what is spoken to it.
