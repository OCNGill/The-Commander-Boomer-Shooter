# EBERT CRITIQUE REPORT — X-COM Enemy Asset Kit (5-model base pass)

**Artifact:** `The_Commander_Boomer_Shooter` X-COM enemy kit — 5 FBX + 5 preview PNGs
**Artifact type:** 3D game assets (character models) with lit preview renders
**Reviewed:** 2026-10-21 · Ebert round 1 · Rubric: `Agents/Ebert/designs/zero_trust_likert_rubric.md` v1.0
**Claimed intent (from brief, not self-assessment):** 1994 *UFO: Enemy Unknown* roster modernized to true 3D — Sectoid, Viper, Floater, Muton, Chryssalid — each with hard cold key + colored alien rim + low under-glow + emissive eyes/core so the reveal reads in darkness.

**EVIDENCE (all five viewed with `vision_analyze`, 2026-10-21):**
- `Tools/blender/out_xcom/XCOM_Sectoid.png` (720×900, EEVEE)
- `Tools/blender/out_xcom/XCOM_Viper.png`
- `Tools/blender/out_xcom/XCOM_Floater.png`
- `Tools/blender/out_xcom/XCOM_Muton.png`
- `Tools/blender/out_xcom/XCOM_Chryssalid.png`
- `Tools/blender/out_xcom/xcom_manifest.json` (tris: 2864 / 3712 / 1980 / 2520 / 2536; fbx 72.8 / 91.0 / 60.9 / 68.8 / 70.0 KB; heights 1.95 / 2.10 / 1.85 / 2.05 / 1.35 m)

**EVIDENCE GAP (disclosed, caps Technical Quality):** one render per model. No turntable, no alternate angle, no in-engine/UE import shot, no scale reference, no topology/wireframe capture, no console. The rubric's 5-screenshot minimum is met in *count* (5 PNGs) but not in *coverage* — each is a single view of a different asset, so no axis above was scored on alternate states, in-engine behavior, or runtime output.

---

## VERDICT

**VERDICT: ITERATE** — total **3.33 / 7.0** against a 6.2 bar. (REJECT.)
No axis is at 1.0, so this is not a categorical failure; it is a bad number, which is the cheaper kind of bad to fix.

| # | Axis | Weight | Score | Contribution |
|---|---|---|---|---|
| 1 | Visual Craft | 0.25 | 3.5 | 0.875 |
| 2 | Truthfulness | 0.20 | 3.0 | 0.600 |
| 3 | Clarity & Communication | 0.20 | 3.0 | 0.600 |
| 4 | Technical Quality | 0.15 | 3.5 | 0.525 |
| 5 | Interaction & Depth | 0.10 | 3.0 | 0.300 |
| 6 | Brand Fit | 0.05 | 5.0 | 0.250 |
| 7 | First-Impression Impact | 0.05 | 3.5 | 0.175 |
| | **TOTAL** | **1.00** | | **3.325 → 3.33** |

Threshold 6.2. Gap: **2.87 points**.

---

## 1. PER-AXIS TABLE

| # | Axis | Score | Evidence (one line, anchored) | What would raise it |
|---|---|---|---|---|
| 1 | **Visual Craft** (25%) | **3.5** | All five are primitive-stack blockouts with visible assembly failures: Sectoid's left hand floats free of the wrist, Floater has a detached white box and ribbed tile beside the left limb, Muton has a fully detached white shard beside the left leg, and Viper/Muton right appendages are cropped by the frame with the top of the head cut off. | Kill every detached part; add a ground plane with contact shadow (nothing stands on anything); reframe so no model is cropped and no model floats in dead space; bevel/chamfer consistency across all 5; controlled highlights (whites are currently clipping to pure white on Muton, Floater, Viper). |
| 2 | **Truthfulness** (20%) | **3.0** | The renders do not show the entities the manifest names: the brief specifies Floater as "manta-like floater, **no legs**" and it is rendered standing on two legs; the brief specifies Viper with "elongated snout, back ribs, plasma pistol" and it has neither a snout, ribs, nor a weapon; Chryssalid has no scythe forelimbs; the claimed `XCOM_Eye_Emissive` / `XCOM_Core_Emissive` / `XCOM_Plasma_Emissive` and the `reveal_key`/`reveal_rim`/`reveal_under` rig are absent from every render (no emissive glow, no rim, no under-glow — just a studio key + green fill on black). | Render the assets as specified or change the labels. A Viper must be recognizably a Viper, a Floater must not have feet, and the emissive/reveal rig must actually be in the picture. If the brief is what changed, amend it and re-issue. |
| 3 | **Clarity & Communication** (20%) | **3.0** | A stranger cannot tell the five apart: Viper, Muton, Floater and Chryssalid all read as the same boxy biped in the same mint/green/white palette with a similar T- or rod-spread silhouette; the only differentiators are a helmet cap and a pink chest tile. | One unmistakable silhouette each: Floater = manta, no ground contact, trailing tendrils; Chryssalid = low, wide, forward-pitched, scythe forelimbs; Muton = heavy, wide, armored, visor slit; Viper = tall, narrow, snouted, ribbed; Sectoid = small, gaunt, oversized cranium, no mouth. Then stage them at gameplay camera distance against a real background. |
| 4 | **Technical Quality** (15%) | **3.5** | Mesh exports are clean and lightweight (1,980–3,712 tris, 61–91 KB, manifest present, joined-mesh Y-up), but the renders expose geometry-level defects a real viewport would too — a detached shard, disconnected hands, unresolved intersections at every joint — and no evidence of in-engine import, scale, or a valid ground contact was submitted. | Prove the asset in-engine: one UE/Blender viewport screenshot per enemy at 1:1 with a 1.8 m human reference, plus a clean import with no auto-merge warnings and no non-manifold islands. Fix the floating parts at the source, not in the render. |
| 5 | **Interaction & Depth** (10%) | **3.0** | Static assets, scored on inherent depth per rubric §2.5. Each model has a chamfer-and-panel second layer and one deliberate accent (oxblood chest plate on Muton, pinkish plate on Chryssalid) but **zero** surface story: no textures, no decals, no wear, no roughness variation, no rigged/posed variants, no emissive detail. The only visible "depth" is a stray white shard, which is a bug. | Deliver a turnaround (front/3-4/profile/back) per enemy, a rigged/posed variant, and at least one material break-up layer (decal, wear, or texture) per asset. Depth should be designed, not accidental. |
| 6 | **Brand Fit** (5%) | **5.0** | Palette is disciplined and on-tone (mint, sage, forest green, off-white, one oxblood/salmon accent) — no purple gradients, no emoji, no slop; reads as deliberate game art rather than generated filler. | Fix the abrupt gray↔green splits that follow arbitrary intersections rather than structure; that alone drops the set toward generic blockout. |
| 7 | **First-Impression Impact** (5%) | **3.5** | The Sectoid is genuinely unsettling (oversized smooth cranium, blank cream eyes, no mouth) and the intent is legible — but the set is delivered as five near-identical floating robots on black with visible assembly errors, which reads as a blockout test, not a shippable kit. | Ship one hero-grade enemy first (Floater, because the reveal is the game's signature moment), staged on a lit ground plane in a dark scene, and let the other four be visibly less finished — or fix all five to the same standard. |

**Weakest axes:** Clarity & Communication (3.0) and Truthfulness (3.0). The two are the same defect seen from two sides: these models are generic bipedal robots wearing five different names.

**Strengths, specifically:** the palette is genuinely restrained and consistent across the set; the bevel/chamfer language is consistent; the FBX pipeline is lean and sane (2k–3.7k tris each, 61–91 KB, manifest with heights); the Sectoid's oversized-cranium + blank-eye design is the one moment in the kit with real identity. The bones are fine. The anatomy and the presentation are not.

---

## 2. PER-ENEMY NOTES

**Sectoid** — The only enemy that partially earns its name. The oversized smooth cranium, blank ivory eyes, no mouth, and gaunt frame land the "psychic infiltrator" read, and the head's smooth-shaded organic mass against a faceted body is a good idea executed inconsistently at the neck. Off: the image-left hand floats free of the wrist with a visible gap; the image-left eye is swallowed to a crescent by the head contour; the collar assembly under the head reads as two displaced parts rather than a mechanism; feet are oversized and splayed with no ground plane, so the stance is a guess. **Highest-leverage fix:** join the hand to the wrist, re-space the eyes symmetrically, and add a contact shadow — this is the model closest to 6.2 and it is one hour of work away from showing it.

**Viper** — Does not read as a Viper. The brief's "tall reptilian hunter, elongated snout, back ribs, plasma pistol" resolves to a boxy biped with a snub helmet cap; the marquee alien of the 1994 game has no snout, no ribbed spine, no weapon, and no scale distinction from the Muton. The image-left arm is a thin gray tube with a white box and a three-pronged hand floating beside it, unconnected; the right side is buried under a large dark slab and a cluster of pale fragments that overlap the leg and read as an extra limb. **Highest-leverage fix:** rebuild the silhouette around a forward-projecting elongated snout and a raised ribbed dorsal spine — the two features that make a Viper a Viper in one glance — and clear the hand/arm debris.

**Floater** — The brief's hard requirement is "manta-like floater, **no legs**" and "glowing dorsal core, trailing tendrils, hover." The render is a biped standing on two block boots with a cyan-white specular hotspot on the chest and a long blade-like appendage on the right that is cropped by the frame. It is the least X-COM thing in the kit: a 1994 Floater hovers, is manta-shaped, and has no feet. It also has the worst clipping in the set (right appendage leaves frame) and a blown-out chest. **Highest-leverage fix:** rebuild it as a legless, wide, hovering manta with a visible emissive dorsal core and trailing tendrils, and give it a hover shadow rather than a stance — that alone moves Clarity and Truthfulness for the whole kit.

**Muton** — The strongest silhouette of the five and the only one with a coherent read (heavy, armored, oxblood chest plate). But the head is ambiguous: a white curled form crossing the face reads as a misplaced moustache or pipe rather than a visor slit, and the dark head recess appears on one side only, so there is no bilateral facial structure. The long right appendage is cropped, a small white block and a ribbed white fragment float near the left limb, and the large green block crossing the right hip has a pale circular cap at the end facing the body with no hand attached. A detached white shard floats beside the left leg. **Highest-leverage fix:** replace the white facial mass with a single horizontal visor slit, add the heavy plasma rifle the brief specifies, and delete the three floating fragments.

**Chryssalid** — Reads as a heavy biped robot, not a "low fast silhouette" stalker. The brief's scythe forelimbs are absent — instead a long bar crosses the figure at head height, thin on the left and a broad plank on the right, cropped by the frame, which is neither bilateral nor legible. The head is the most confusing in the kit: a dark recessed cavity, a green cowl, and a large white curled object with no anatomical function, plus tiny white specular dots on the spherical abdomen that accidentally form a second face. Small pipes and brackets form an unreadable knot at the hips. **Highest-leverage fix:** invert the body plan — low, forward-pitched, wide, on long digitigrade legs with two real scythe forelimbs — and clear the hip tangle. A Chryssalid must be recognizable in pure silhouette at 40 pixels tall.

---

## 3. CATEGORICAL CHECK

My rubric's categorical-fail rule: **any axis at 1.0 forces ITERATE regardless of the weighted total; a fabricated metric, testimonial, citation, or result sets Truthfulness to 1.0; an artifact that will not load or render sets Technical Quality to 1.0.**

| Rule | Result | Finding |
|---|---|---|
| Any axis at 1.0? | **NOT TRIGGERED** | Lowest axis is 3.0. No catastrophic failure. |
| Fabricated metric / testimonial / citation / result? | **NOT TRIGGERED** | No numbers, claims, testimonials, or citations in the artifact. The manifest reports only measurable quantities (tris, KB, height) and they are internally consistent with the listed files. |
| Artifact will not load or render? | **NOT TRIGGERED** | All five PNGs render. FBX files exist for all five per the manifest. |
| Fewer than 5 screenshots? | **NOT TRIGGERED** (with caveat) | 5 PNGs submitted, all viewed. Coverage caveat disclosed above (one view per model, no turntable, no in-engine shot) — this caveat is reflected in Technical Quality 3.5 and Interaction 3.0, not in a categorical fail. |

**Categorical result: no automatic ITERATE from a 1.0.** The ITERATE verdict stands on the 3.33 total alone. 2.87 points must be earned back.

---

## 4. THE BAR FOR THE REST

The Commander is commissioning level design, background textures, lighting, and the main character. Those are separate submissions, each scored by this rubric against the same 6.2. Here is exactly what I will require and what "pass" means, so a builder can hit it without asking.

### (a) LEVEL DESIGN

**Evidence I will require (nothing less scores):**
1. One top-down orthographic layout PNG of the entire map with the tile grid visible and a legend.
2. ≥3 in-engine ground-level gameplay screenshots at the game's real camera, from different points on the map.
3. ≥5 additional frames (or a turntable/flythrough clip: first frame, mid-clip, settle frame).
4. One annotated path diagram: drop zone → cover → objective, with the route drawn.
5. One screenshot showing at least two different enemy types placed on the map, in-frame, at gameplay distance.

**What I look for:** a traversable path with no dead end and no impossible geometry; cover that actually breaks line of sight from the drop zone; spawn points that are not in immediate LOS of the drop; 1 unit = 1 tile consistency; no floating props, no clipping through floors, no z-fighting — I will specifically look for the detached-geometry failure this enemy kit has, and it counts against level polish as well; elevation variety; a readable "kill zone" progression; props that are either cover or scenery and read as one thing, not as scattered primitives.

**Minimum bar to pass:** no unreachable objective and no camera-blocking geometry; ≥3 distinct tactical spaces with different sightlines; zero visible clipping/floating props in any submitted frame; and a weighted total of ≥6.2 on this rubric with Clarity ≥5.5 — a level nobody can navigate fails on Clarity regardless of how it looks.

### (b) BACKGROUND TEXTURES

**Evidence I will require:**
1. The actual source files (PNG/TGA, 2048×2048 minimum) submitted with the package, not just the applied result.
2. A contact sheet: 2×2 tiling of each texture with a 50% offset, so repetition is visible.
3. In-scene 1:1 pixel crops of each material at native resolution — **not** downscaled screenshots — at three different locations each.
4. One 4096² or 2048² trim sheet for the set.

**What I look for:** seamless tiling, proven by the offset contact sheet with no visible seam or obvious repeat; non-uniform, hand-authored-looking surfaces rather than a photo of a dirt wall stretched across a box; correct texel density (no stretched UVs on floors and walls); a real normal map and roughness variation, not a flat color; grime and wear breakup at edges; the palette matching the existing mint/sage/green/oxblood set so the game reads as one world; and any two materials distinguishable at a glance, not only by hue.

**Minimum bar to pass:** zero visible seam or repeat in the offset contact sheet for every texture; 2048² source on every wall/floor; in-scene 1:1 crops showing resolvable surface detail (grime, panel lines, wear — not flat gradients); and a weighted total of ≥6.2 with Visual Craft ≥6.0.

### (c) LIGHTING

**Evidence I will require:**
1. The actual light rig from the scene file, plus a screenshot of the rig's parameters (name, type, color, power, position) — I will not accept a verbal description of the rig.
2. One render of each enemy under the **brief's** reveal rig (`reveal_key` cold hard key, `reveal_rim` colored alien rim, `reveal_under` low under-glow) against a fully black scene.
3. A side-by-side of the same enemy under (a) the current flat studio rig and (b) the reveal rig.
4. One screenshot of a scene lit by nothing but the enemy's own emissives, to prove the emissives actually emit.

**What I look for:** all four rig elements present and legible in a single frame; emissive eyes and core visibly self-lit and bleeding into adjacent surfaces; the enemy reading as a distinct silhouette against black using rim light alone; a single consistent shadow direction across the whole set; no clipped white pixels anywhere on the body; no fill light strong enough to fake green material (the current renders' dominant failure); clean shadow falloff, no acne, no banding; value separation between the model and its background so the outline never disappears.

**Minimum bar to pass:** the four rig elements visible in one frame per enemy; emissives demonstrably emitting (proof shot required); zero blown highlights; a consistent shadow direction across all assets and all future scenes; and a weighted total of ≥6.2 with Visual Craft ≥6.0 and First-Impression ≥5.5. Lighting is the highest-leverage multiplier in this whole project — it is the one submission where a 6.2 can lift a 5.5 set, and it is also the one where a cheap rig can sink a good set.

### (d) MAIN CHARACTER (the Commander)

**Evidence I will require:**
1. ≥5 screenshots: front orthographic, 3/4 hero, profile, back, and **one in-engine gameplay shot at the real camera distance with an enemy present for scale**.
2. One animation clip sampled at first frame, mid-cycle, and settle frame.
3. One scale-comparison shot against a 1.8 m human reference.
4. A viewport/wireframe capture showing the rig and topology.

**What I look for:** the character is the most-looked-at asset in the game and carries the highest bar; immediate separation from the enemy silhouettes by color, proportion, and motion; **zero detached geometry** — the failure mode this kit already has; differentiated materials (skin vs cloth vs metal vs leather, not one plastic); a face that reads at camera distance; the character holding up in the actual gameplay camera, not only in a beauty render; a rig that deforms without collapsing at the joints; and detail density that rewards a close look without exploding the tri budget.

**Minimum bar to pass:** ≥6.2 weighted on this rubric **and** Visual Craft ≥6.0, Clarity ≥6.0, Truthfulness ≥6.0; zero detached or floating parts in any frame; a turnaround identifiable from every angle; an in-engine shot at gameplay distance in which the character is not a silhouette lost against the background; and a scale reference proving correct human proportions. A character that scores 5.8 does not ship, no matter how it renders in isolation.

---

## 5. TOP 5 FIXES (ranked by score impact)

1. **Rebuild each enemy around one unmistakable silhouette** (Floater legless manta, Chryssalid low scythe-armed stalker, Viper snouted and ribbed, Muton heavy armored, Sectoid small and gaunt) — **+0.50 total** (Clarity +1.5, Truthfulness +1.0) — all five PNGs; the current set is five copies of one robot with different helmets.
2. **Eliminate every detached and floating part** (Sectoid hand, Floater white box + ribbed tile, Muton white shard + green hip block, Viper's floating prongs, Chryssalid's hip fragments) — **+0.33 total** (Visual Craft +1.0, Technical +0.5) — all five PNGs; these are geometry bugs, and they are the single most embarrassing thing in the kit.
3. **Add the specified reveal rig and emissives** (cold hard key, colored alien rim, low under-glow, `XCOM_Eye_Emissive` / `XCOM_Core_Emissive` / `XCOM_Plasma_Emissive`) and add a ground plane with contact shadow to every render — **+0.31 total** (Truthfulness +0.5, Visual Craft +0.5, Technical +0.5, Impact +0.5) — the brief's signature reveal is currently absent from all five images.
4. **Reframe and rescale the renders** (no cropped appendages, no cut-off head, no dead space under the feet, consistent 3/4 camera, model filling frame, 1.8 m reference) — **+0.25 total** (Visual Craft +0.5, Clarity +0.5, Technical +0.5) — Viper and Muton are cropped on the right, Muton is cropped at the top, and all five waste the lower third.
5. **Add the missing weapons and a second layer of surface depth** (Viper plasma pistol, Muton heavy plasma rifle, per-enemy decals/wear/texture, plus a turnaround and one rigged pose per asset) — **+0.20 total** (Interaction +1.0, Visual Craft +0.5, Technical +0.5) — the brief names a weapon for two enemies and neither render shows one.

**Cheapest path to 6.2 is not a redesign.** Fixes 2, 3 and 4 alone are about a day's work and land roughly 5.4. Fix 1 is the one that makes it a game asset instead of a blockout, and it must be done. Expect to be back.

---

**VERDICT: ITERATE**
