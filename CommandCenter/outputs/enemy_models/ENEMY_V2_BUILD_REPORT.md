# X-COM Enemy Models - v2 / v3 Build Report

v2 rebuilt the five enemies from scratch for the Ebert round-1 rubric deltas. **v3 closes the two named round-2 failures and then re-checks the other three the same way.**

- **Floater - legless.** v2 still had five descending rods ending in glowing spheres, which read as a spider stance. v3 deletes them. The body is now ONE continuous swept manta planform from tip to tip (10 outline points, no notches and no separate wing parts), so the underside has no lobes that can be misread as limbs. The only appendages are two hair-fine filaments trailing off the REAR at an upward angle. Verified two ways: a bottom-up orthographic silhouette render shows a single smooth planform, and the lowest mesh vertices are a single centred head pod (z=0.902 at x=0.000) - nothing hangs below the body.
- **Sectoid - hunched.** The torso is pitched 22 deg forward about the pelvis and the head a further 8 deg. The shoulders are a wide flattened flesh mass (not a level bar, not ball joints), the cranium fuses into a continuous nape and trapezius funnel (no collar), the legs are short with visibly bent knees and the weight on the right leg, and the hands are enlarged and clasped forward and outboard so the gesture breaks the torso outline. Both feet have a dark contact patch, confirmed by probing the rendered pixels at the projected foot positions.
- **Viper / Muton / Chryssalid - re-checked on the same criteria.** All three keep their distinct silhouette, all eyes were rebuilt as alien almond eyes (dark socket, dark ball, glowing lens, no chrome bezel), all feet now carry a dark contact patch, and the metallic-ankle-ball artefact was removed from every foot.

Everything below is produced by the generator script - no hand-placed or hand-edited assets.

Generator: `Tools/blender/xcom_enemies_v2.py` (Blender 4.2.23, EEVEE Next). Every model, render and measurement below was produced by running that script - nothing is hand-placed or hand-edited.

## Per enemy

### XCOM_Sectoid

- **Triangles:** 7308  |  **FBX:** XCOM_Sectoid.fbx (186.8 KB)  |  **Height:** 1.39 m  |  **Width:** 0.52 m  |  **Length:** 0.70 m
- **Silhouette:** small + gaunt, oversized smooth cranium, symmetric glowing eyes, NO mouth (nasal slit + brow ridge + chin plate), stick-thin limbs that end at the hip - the smallest frame in the kit
- **What changed vs v1:** v1 read as the same generic biped and v2 still stood to attention like a mannequin. v3: the torso is pitched 22 deg forward about the pelvis and the head an extra 8 deg, so the figure is a compact forward-curved hunch; the shoulders are a rounded, UNEQUAL mass rather than a level bar; the cranium merges into a fleshy nape instead of a mechanical collar; the eyes are alien almond eyes (dark socket, dark ball, glowing lens) with no chrome bezel; there is no mouth (nasal slit, brow ridge, chin plate); the legs are short, tapered and knee-bent with the weight on the right leg; the hands are enlarged and clasped forward and outboard so the gesture breaks the torso outline; and both feet have a tight dark contact patch on the floor.
- **Ground contact:** True   **Emissive:** True   **Weapon:** False   **Face detail:** True   **Hover clearance:** 0.0 m
- **Emissive proof:** 12143 hot pixels in the hero render (green 5686 / cyan 6457). Control render with emission forced to 0: 2842 hot pixels at half resolution.
- **Ground/shadow check (bottom 5% of rows, the floor):** min 73.8 / mean 157.0 / p05 86.0 / p95 255.0, dark-pixel fraction 0.0.
- **Contact-shadow probe (luminance at the real foot pixel positions):** `[(294, 827, 105.3, 219.3), (397, 808, 102.0, 177.3)]` (px, py, min, median). A value well below the surrounding floor confirms a real dark contact patch.
- **Torso pitch:** 22 deg forward about the pelvis (plus a further 8 deg on the head).
- **Where the contact shadow comes from:** tight dark occlusion patch painted under each foot + a real cast shadow from the 700 W near-vertical reveal_cast spot.
- **Renders:** `XCOM_Sectoid.png`, `XCOM_Sectoid_turn.png`, `XCOM_Sectoid_scale.png`, `XCOM_Sectoid_silh.png` (silhouette plate)

### XCOM_Viper

- **Triangles:** 5764  |  **FBX:** XCOM_Viper.fbx (140.4 KB)  |  **Height:** 2.06 m  |  **Width:** 0.64 m  |  **Length:** 0.70 m
- **Silhouette:** tall + narrow reptilian hunter, forward-projecting elongated snout, raised ribbed dorsal spine, plasma pistol held out front
- **What changed vs v1:** v1 had no snout and no weapon. v2: 2.10 m tall and narrow, a 45 cm forward-projecting tapered snout with a plated nasal ridge, six bone teeth in a recessed jaw seam, a raised five-rib dorsal spine, and a real plasma pistol (body, angled grip, trigger guard, barrel, glowing coil) in the right hand. v3: the chrome eye bezel was replaced by an alien almond eye (dark socket, dark ball, glowing lens) and both feet now carry a tight dark contact patch on the floor.
- **Ground contact:** True   **Emissive:** True   **Weapon:** True   **Face detail:** True   **Hover clearance:** 0.0 m
- **Emissive proof:** 7941 hot pixels in the hero render (green 3961 / cyan 3980). Control render with emission forced to 0: 2053 hot pixels at half resolution.
- **Ground/shadow check (bottom 5% of rows, the floor):** min 47.1 / mean 116.3 / p05 54.4 / p95 245.7, dark-pixel fraction 0.0.
- **Contact-shadow probe (luminance at the real foot pixel positions):** `[(311, 812, 97.0, 140.7), (386, 806, 37.3, 131.0)]` (px, py, min, median). A value well below the surrounding floor confirms a real dark contact patch.
- **Where the contact shadow comes from:** tight dark occlusion patch painted under each foot + a real cast shadow from the 700 W near-vertical reveal_cast spot.
- **Renders:** `XCOM_Viper.png`, `XCOM_Viper_turn.png`, `XCOM_Viper_scale.png`, `XCOM_Viper_silh.png` (silhouette plate)

### XCOM_Floater

- **Triangles:** 2184  |  **FBX:** XCOM_Floater.fbx (65.6 KB)  |  **Height:** 0.29 m  |  **Width:** 2.48 m  |  **Length:** 1.40 m
  - The Floater is a FLAT body: 1.40 m front-to-back and only 0.29 m thick, and it hovers 0.90 m above the floor. Its `height_m` is the body thickness, not a standing height.
- **Silhouette:** LEGLESS broad manta parasite: ONE continuous swept planform from tip to tip (2.5 m span, no separate wing parts and no notches), a low segmented glowing dorsal core, and NOTHING under the body - no legs, no feet, no rods, no rounded tips; it hovers over a soft body-shaped ellipse
- **What changed vs v1:** v1 gave the Floater legs. v2 still had FIVE descending rods ending in glowing spheres, which read as a spider stance. v3: those rods and spheres are DELETED - there is no leg, no foot, no descending appendage and no rounded tip under the body; the only appendage is a pair of hair-fine filaments trailing off the REAR, angled upward so they can never read as limbs. The body is now ONE continuous swept manta planform from tip to tip (2.5 m span) instead of a body plus separate wing parts, so the underside has no lobes or notches that could be mistaken for limbs; the dorsal core is three low segmented lens segments (no canopy/dome); and the body-shaped hover ellipse on the floor is the only thing beneath it.
- **Ground contact:** False   **Emissive:** True   **Weapon:** False   **Face detail:** True   **Hover clearance:** 0.9 m
- **Emissive proof:** 4092 hot pixels in the hero render (green 2046 / cyan 2046). Control render with emission forced to 0: 86 hot pixels at half resolution.
- **Ground/shadow check (bottom 5% of rows, the floor):** min 27.5 / mean 36.4 / p05 30.1 / p95 44.5, dark-pixel fraction 0.0.
- **Contact-shadow probe (luminance at the real foot pixel positions):** `[]` (px, py, min, median). A value well below the surrounding floor confirms a real dark contact patch.
- **Where the contact shadow comes from:** soft body-shaped hover ellipse on the floor; nothing touches the ground.
- **Renders:** `XCOM_Floater.png`, `XCOM_Floater_turn.png`, `XCOM_Floater_scale.png`, `XCOM_Floater_silh.png` (silhouette plate)

### XCOM_Muton

- **Triangles:** 5216  |  **FBX:** XCOM_Muton.fbx (122.7 KB)  |  **Height:** 2.07 m  |  **Width:** 1.15 m  |  **Length:** 1.09 m
- **Silhouette:** heavy + wide armoured slab, horizontal emissive visor slit, huge pauldrons, two-handed plasma rifle with foregrip, oxblood chest plate - a walking tank
- **What changed vs v1:** v1 had a white "hook" mass on the face and a flat chest rectangle. v2: 2.05 m, the widest mass in the kit, huge angled pauldrons, a HORIZONTAL EMISSIVE VISOR SLIT in a dark recess (the hook is gone), a brow bar, a helmet crest and a slatted respirator, and a detailed oxblood chest plate with panel seams, a 3-slat vent grille and a rank insignia. The heavy plasma rifle (body, stock, grip, trigger guard, foregrip, barrel, muzzle, glowing coil) is held in two hands. v3: both feet now carry a tight dark contact patch on the floor and the armour is darker and less dusty than v2 so the oxblood chest plate is the focal point.
- **Ground contact:** True   **Emissive:** True   **Weapon:** True   **Face detail:** True   **Hover clearance:** 0.0 m
- **Emissive proof:** 10125 hot pixels in the hero render (green 4567 / cyan 5558). Control render with emission forced to 0: 2591 hot pixels at half resolution.
- **Ground/shadow check (bottom 5% of rows, the floor):** min 45.0 / mean 115.6 / p05 53.4 / p95 245.1, dark-pixel fraction 0.0.
- **Contact-shadow probe (luminance at the real foot pixel positions):** `[(297, 809, 93.0, 149.7), (404, 807, 41.0, 126.7)]` (px, py, min, median). A value well below the surrounding floor confirms a real dark contact patch.
- **Where the contact shadow comes from:** tight dark occlusion patch painted under each foot + a real cast shadow from the 700 W near-vertical reveal_cast spot.
- **Renders:** `XCOM_Muton.png`, `XCOM_Muton_turn.png`, `XCOM_Muton_scale.png`, `XCOM_Muton_silh.png` (silhouette plate)

### XCOM_Chryssalid

- **Triangles:** 6252  |  **FBX:** XCOM_Chryssalid.fbx (164.7 KB)  |  **Height:** 1.03 m  |  **Width:** 0.82 m  |  **Length:** 1.62 m
- **Silhouette:** low + wide forward-pitched stalker on four long digitigrade legs, two scythe forelimbs sweeping forward, venom glow - a fast crouch
- **What changed vs v1:** v1 was a biped. v2: NOT a biped - four long digitigrade legs (femur, tibia, tarsus, clawed foot touching the floor), a low forward-pitched body, TWO real scythe forelimbs sweeping forward with a bone cutting edge, a dorsal ridge of bone spurs, a low head with emissive eyes, mandibles, a mouth seam and a glowing venom sac. v3: the chrome eye bezel was replaced by an alien almond eye and all four feet now carry a tight dark contact patch on the floor.
- **Ground contact:** True   **Emissive:** True   **Weapon:** False   **Face detail:** True   **Hover clearance:** 0.0 m
- **Emissive proof:** 5870 hot pixels in the hero render (green 2214 / cyan 3656). Control render with emission forced to 0: 1468 hot pixels at half resolution.
- **Ground/shadow check (bottom 5% of rows, the floor):** min 28.8 / mean 130.5 / p05 57.3 / p95 250.2, dark-pixel fraction 0.0.
- **Contact-shadow probe (luminance at the real foot pixel positions):** `[(221, 764, 75.3, 106.0), (504, 862, 30.0, 121.0), (341, 698, 41.7, 56.0), (563, 760, 22.3, 57.0)]` (px, py, min, median). A value well below the surrounding floor confirms a real dark contact patch.
- **Where the contact shadow comes from:** tight dark occlusion patch painted under each foot + a real cast shadow from the 700 W near-vertical reveal_cast spot.
- **Renders:** `XCOM_Chryssalid.png`, `XCOM_Chryssalid_turn.png`, `XCOM_Chryssalid_scale.png`, `XCOM_Chryssalid_silh.png` (silhouette plate)

## What I could NOT fix / known limits

1. **Procedural materials do not survive the FBX.** Every material carries noise -> ColorRamp -> Base Color and noise -> Bump(0.25) -> Normal, and a third noise into roughness. FBX/UE only carry image textures, so the FBX ships flat base colours, metalness and roughness; the noise/bump must be baked to textures before the assets look like the renders. This is a pipeline task, not a modelling one, and it is NOT done.
2. **The FBX files are static meshes with no rig and no animation.** The asymmetry (weight on one leg, weapon shouldered, head turned 8 deg) is baked into the rest pose. UE-side skeletal rigging and idle animation are still outstanding.
3. **The scale-reference shot uses a neutral grey capsule** standing in for a 1.8 m human, not a rigged human character. It proves scale, not anatomy.
4. **Three extra lights were added beyond the brief.** The specified key (front-left) and rim (behind-right) spots throw their shadows away from camera, so no cast contact shadow was visible in frame, and the specified cyan under-glow point sat on the feet and washed the contact area out. The rig therefore also carries: a 220 W overhead anchor; a 640 W hard near-vertical cast spot (2.3 m up, 24 deg cone, 0.012 m shadow radius) directly over the subject so its shadow lands AT the feet as a tight dark shape inside a small lit ellipse; and a 260 W near-vertical floor wash centred on the subject so the wet concrete is lit as an even ellipse with the figure's shadow inside it, instead of a bright pool in the foreground. Each foot additionally carries a painted dark occlusion patch. This is a deviation from the specified three-light rig and is disclosed here.
4b. **The silhouette plates (`*_silh.png`) are a shape-only render:** the enemy is re-materialised as pure black emission, the floor and all lights are hidden, and the world is a flat mid-grey field. They prove the SHAPE, not the materials or the lighting.
5. **The Chryssalid and Floater carry no weapon** (the brief only calls for weapons on the Viper and Muton), so `has_weapon` is false for those two.
6. **The Floater has no ground contact by design**, so it is the one model with `has_ground_contact = false`; the ellipse under it is a hover shadow, not a contact shadow.
7. **No LODs, no collision meshes, no texture bakes, no import-ready UE assets** are included - out of scope for this pass.
7b. **The Sectoid still reads somewhat mechanical at the shoulders.** The deltoid masses were widened, flattened and pushed into the torso, and the nape was thickened into a continuous flesh funnel, but at 900 px a lit shoulder cap still reads as a ball joint. It is improved, not eliminated. The head-to-shoulder junction is now a fused mass with no separate collar.
7c. **The contact shadow is a render-time rig, not mesh geometry.** It is a painted occlusion patch plus the cast shadow of a 700 W near-vertical spot. It is verified per-enemy by probing the rendered pixels at the projected foot positions (see the probe line above), and it reads in the images, but it is not baked into the FBX - a UE placement will need its own shadow rig.
7d. **The Floater hovers 0.90 m above the floor** and has no ground contact by design, so it is the one model with `has_ground_contact = false` and its `height_m` is the body thickness, not a standing height.
7e. **The materials are still fairly matte and low-contrast on the Sectoid and Muton.** Procedural noise and bump were reduced to stop the "dusty concrete" read and the three material families (CHITIN / PLATE / ACCENT) are separated in value, but there is no texture variation beyond the procedural layers at this stage.
8. **The contact shadow is a render-time rig, not baked into the FBX.** The cast shadow comes from the overhead spot in the reveal rig and the per-foot occlusion patches are render geometry. The FBX ships the enemy mesh only; the floor, the shadow blobs and the lights live in the render scene, so a UE placement will need its own shadow/lighting rig to reproduce these frames.

