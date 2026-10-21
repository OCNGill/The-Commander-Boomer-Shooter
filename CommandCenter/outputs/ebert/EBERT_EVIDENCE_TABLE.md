# EBERT — EVIDENCE TABLE (UNSCORED)

**Status: NO SCORE IS ASSIGNED IN THIS DOCUMENT. NO VERDICT IS ISSUED.**
**`EBERT_ENEMY_VERDICT.md` (v1, 3.33/7.0) remains the only verdict on disk. `EBERT_LIGHTING_VERDICT.md` does not exist.**

Written per the Commander's HOLD: the v2/v3 sets were being rebuilt while this review ran, so the
v2 frames named in the original dispatch are **superseded**. This file is the map for the
re-dispatch, not a verdict.

- Rubric (law for the scoring run): `Agents/Ebert/designs/zero_trust_likert_rubric.md`
- Axes: Visual Craft 25 | Truthfulness 20 | Clarity & Communication 20 | Technical Quality 15 |
  Interaction & Depth 10 | Brand Fit 5 | First-Impression Impact 5
- PASS threshold 6.2. No rounding. Any axis at 1.0 forces ITERATE regardless of total.
- Evidence base: every file below was opened and looked at with `vision_analyze`; every number
  was measured independently with numpy/PIL rather than taken from the rig's own JSON.

## ⚠ Read this first: the evidence set was rewritten three times under this review

| Window | What changed | Status of my observations |
|---|---|---|
| 01:33–02:56 | v2 enemy renders; v2 lighting (`out_lighting`) | **SUPERSEDED.** Not cited below. |
| 03:19–03:48 | Enemy v3 rebuild (03:22–03:32), lighting v3 rebuild (03:19–03:48) | **SUPERSEDED.** Not cited below. |
| 04:08–04:18 | Lighting v4 generation — `CommandCenter/outputs/lighting/` (04:08 Sectoid → 04:17 Floater) | **MIXED GENERATION.** Cited below, flagged per row. |
| 04:24–04:32 | Enemy v3 final rebuild (Sectoid 04:24:47 → Chryssalid 04:27:50) | **CURRENT.** Cited below. |
| 04:11–04:21 | Textures (04:08 wood → 03:48 concrete), Level (04:21:58) | **CURRENT.** Cited below. |

**The lighting set on disk is a mix of three different rig generations** and the rig's own
verifier only measured one of the five. `Tools/blender/out_lighting/lighting_rig_spec.md` and
`CommandCenter/outputs/lighting/LIGHTING_EVIDENCE.md` (04:18:21) state it plainly:

> **Skipped:** XCOM_Chryssalid (render error: bad operand type for unary ~: 'NoneType');
> XCOM_Muton (render error: bad operand type for unary ~: 'NoneType');
> XCOM_Viper (render error: operands could not be broadcast together with shapes (0,0) (675,540));
> XCOM_Sectoid (render error: bad operand type for unary ~: 'NoneType')

**Only XCOM_Floater was measured by the rig in the 04:18 generation.** The other four PNGs in
that folder are the previous generation's images, carried forward. Any "v3 lighting" score written
today would be scoring four unmeasured leftovers plus one current frame.

---

# CATEGORY 1 — ENEMIES

Current set: `Tools/blender/out_xcom/XCOM_*.png`, 04:24:47–04:27:50, mirrored byte-identical to
`CommandCenter/outputs/enemy_models/`. Manifest: `out_xcom/xcom_manifest.json` (04:28:45).
Builder's own disclosure: `out_xcom/ENEMY_V2_BUILD_REPORT.md` (04:32:22).

| Axis | Image file actually opened | What I SAW (observation, not score) | Evidence that would settle the axis in v3 | Superseded? |
|---|---|---|---|---|
| **Visual Craft** (25%) | `out_xcom/XCOM_Sectoid.png` (04:24:47, 993c9fcd35), `XCOM_Viper.png` (04:25:29, 1088fc0f71), `XCOM_Floater.png` (04:26:15, eb386e5e0c), `XCOM_Muton.png` (04:26:56, d0f0bf73a1), `XCOM_Chryssalid.png` (04:27:50, 4244b2cce6) — all five opened as one 5-panel contact sheet | Silhouettes are now **mutually distinct**: Sectoid squat/oversized smooth oval head, Viper tall thin stilt-legged, Floater flat delta/saucer, Muton boxy broad-shouldered with red chest plate, Chryssalid low many-legged insect. This is a **real change from v1**, where all five read as copies of one generic biped. Model craft is still blocky: the Viper's head is a tiny barrel on a long neck, the Muton's chest is a flat red rectangle, the Floater's hull is a smooth blank delta. | v3 = all five rebuilt to a shared proportional/matcap standard (consistent texel density, matching edge treatment, shared detail language) at 1:1 in-engine. I would settle this axis on a 5-up in-engine lineup at final resolution, not on isolated turntable renders. | No — current. |
| **Truthfulness** (20%) | `out_xcom/ENEMY_V2_BUILD_REPORT.md` "What I could NOT fix" (04:32:22) + `out_xcom/xcom_manifest.json` (04:28:45) | The builder **discloses its own shortcuts**, which is honest: (1) "Procedural materials do not survive the FBX… the FBX ships flat base colours… this is a pipeline task… and it is NOT done"; (2) "FBX files are static meshes with no rig and no animation"; (3) the scale reference "uses a neutral grey capsule… It proves scale, not anatomy"; (4) "**Three extra lights were added beyond the brief**" (220 W anchor, 640 W cast spot, 260 W floor wash) — "This is a deviation from the specified three-light rig and is disclosed here." But the manifest contradicts the render on weapon counts: manifest says `has_weapon: true` for Viper and Muton, and in the current PNGs the Viper holds nothing and the Muton's hands hold only "a small indistinct green element" — a weapon the manifest asserts and the image does not show. | The v3 run settles this on three artifacts, all in the same render: (a) the FBX opened in UE showing the **same** material the PNG shows, (b) a rigged + animated preview, and (c) the manifest's `has_weapon` field made to agree with the pixels — or the field removed. A mismatch between a manifest field and the shipped image is the exact failure this axis is written to catch. | No — current. |
| **Clarity & Communication** (20%) | `out_xcom/XCOM_Sectoid.png` 04:24:47, `XCOM_Muton.png` 04:26:56, `XCOM_Chryssalid.png` 04:27:50, `XCOM_Viper.png` 04:25:29, `XCOM_Floater.png` 04:26:15 | Faces read unevenly. Sectoid: two bright green eyes, no mouth/jaw. Muton: green horizontal visor, no mouth. Chryssalid: two yellow eyes plus mandibles, no open mouth. Viper: "weakly readable… a small green horizontal eye/visor-like slit on the tiny barrel-shaped head, but no clear eye shape, mouth, or jaw opening." Floater: correctly **no face** — it is a flying craft, and the cyan top emitter must not be read as an eye. Weapons: Sectoid's long rifle reads clearly; Viper and Muton have none that read; Floater's cyan barrel reads as a cannon but is ambiguous with an engine. | v3 settles it on a **face-forward crop sheet** at 1:1 — one cropped head per creature, big enough to judge the eye, at least one non-pupil facial landmark (mouth line, mandible gap, visor shape) on each of the four humanoids, plus a weapon that reads as a weapon in the hands of every humanoid. A "can I tell what I'm looking at in five seconds" test on the unlabelled lineup. | No — current. |
| **Technical Quality** (15%) | `out_xcom/xcom_manifest.json` 04:28:45 + all five hero PNGs at 04:24–04:28 | Mesh budgets are real and modest: 7,308 / 5,764 / 2,184 / 5,216 / 6,252 tris; heights 1.39 / 2.06 / 0.29 / 2.07 / 1.03 m. FBX export present for all five. **Floater `has_ground_contact: false`** — correct, it flies. Real defects visible: Chryssalid is cropped at the **left edge** by a long pointed appendage and at the **bottom edge** by a foreground blade-like limb; the Floater's right wing tip touches the frame border. FBX ships flat base colours (build report limit #1) and no rig (limit #2). | v3 settles it on: (a) every hero frame composed so no geometry is cut by the frame edge, (b) UE import of the FBX showing textured materials and a skeleton, (c) tri/height budgets held, (d) a scale reference against a **rigged human**, not a grey capsule. | No — current. |
| **Interaction & Depth** (10%) | `out_xcom/XCOM_*.png` (all five, current) + `ENEMY_V2_BUILD_REPORT.md` known-limits 2 | The single biggest interaction fact: **"The FBX files are static meshes with no rig and no animation."** All asymmetry is "baked into the rest pose." A turntable (`_turn.png` 04:25–04:28) and a scale plate (`_scale.png`) exist per creature, so there is *some* staged variety, but no locomotion, no idle, no attack, no hit reaction. Chryssalid's scythe limbs and the Sectoid's shouldered rifle are poses, not behaviours. | v3 settles it on **an in-engine animation preview** — idle loop + one attack + one hit reaction per creature, at 30 fps, in the level with the reveal rig live. Static silhouettes cannot score above the bottom of this axis; the v3 run should not score this axis from PNGs at all. | No — current. |
| **Brand Fit** (5%) | `out_xcom/XCOM_Muton.png` 04:26:56, `XCOM_Floater.png` 04:26:15, `XCOM_Chryssalid.png` 04:27:50 | The palette is on-brand: cold slate/steel bodies, one saturated X-COM green on every eye and visor, a single red chest plate on the Muton as the one warm accent, yellow eyes on the Chryssalid. Restrained, not garish. The one miss is the Muton's red chest, which is a large flat rectangle with no material detail or wear — it reads as a decal on a blockout rather than a deliberate accent. | v3 settles it on the same in-engine lineup with materials live: verify the red chest is a material with wear and specular response, and that the green emissive is the only saturated hue on any body. | No — current. |
| **First-Impression Impact** (5%) | All five current hero PNGs, viewed as one 5-panel sheet | Strongest single image in the set is the **Muton** — boxy, red chest, green visor, clearly a heavy soldier. The **Floater** is the weakest: "a low black oval or dome, two small green eyes" in the lighting reveal — in its own hero render it is a smooth blank delta with a cyan emitter, i.e. the least communicative model. First contact with the kit as a set reads as a real roster, not five copies. | v3 settles it on a **first-contact lineup in the level**, lit by the reveal rig, as a stranger would first see it. Until the Floater's hull has surface and the kit is seen in context, the 5% axis is decided by the Muton, not by the set. | No — current. |

**Geometry note (required attribution).** The v1 enemy verdict found the five models read as five
copies of one generic biped — a Floater with legs, a Viper with no snout or ribs, a visorless Muton,
detached parts, nothing on the ground. **Three of those five v1 geometry defects are now visibly
corrected in these renders**: the Floater is genuinely legless (I confirmed at 1.4× on
`XCOM_Floater.png` 04:26:15 — no legs, no glowing spheres, no detached pieces), the Muton has a
green visor, and the five silhouettes are now mutually distinct. **Two remain**: no creature has a
mouth or jaw aperture, and the Muton/Viper still do not carry a readable weapon. These are
**GEOMETRY** findings. They are not attributable to the lighting rig and must not be charged to it.

**The Floater defect named in the hold is CONFIRMED FIXED in the current file.** The v2 render
showed five legs ending in rounded glowing cyan orbs. `XCOM_Floater.png` at 04:26:15 (eb386e5e0c)
shows none. A Floater score written against the v2 file would have been stale on arrival; it is not
needed, because the file has been replaced.

---

# CATEGORY 2 — LIGHTING

Evidence: `CommandCenter/outputs/lighting/` (04:08–04:18, **mixed generations**),
`Docs/generated/lighting_rig_spec.md` (04:18:21, 8,479 chars — the UE5 handoff spec, now present;
it did not exist when this review started).

**This is the weakest evidence base of the four categories.** The rig's own evidence document says
four of five enemies were **skipped with render errors** in the current generation, and the folder
therefore mixes a 04:17 Floater with a 03:45 Viper, a 04:08 Sectoid, a 04:15 Muton and a 04:14
Chryssalid. Rows below state which generation each file came from.

| Axis | Image file actually opened | What I SAW (observation, not score) | Evidence that would settle the axis in v3 | Superseded? |
|---|---|---|---|---|
| **Visual Craft** (25%) | `CommandCenter/outputs/lighting/XCOM_Muton_reveal.png` (04:15:39), `XCOM_Sectoid_reveal.png` (04:08:37), `XCOM_Chryssalid_reveal.png` (04:14:03), `XCOM_Viper_reveal.png` (03:45:25), `XCOM_Floater_reveal.png` (04:17:10) — all five opened as one 5-panel contact sheet | The rig is now **legible**, which was the v1 failure. Cold key and green rim read on **opposite** sides for Sectoid (key screen-left, green screen-right) and Muton (key front-left, narrow green edge screen-right). The Muton is the best frame in the set: hard-edged cast shadow to screen-right, red chest and green visor unclipped, graded cool-white floor pool with clear falloff, pure black background, unambiguously three-dimensional. **Floater remains near-invisible** — "a low black oval or dome, two small green eyes… the body has no readable volume"; my own floor-band measurement gives it mean lum 1.58 and 0.0% of floor pixels above 80, and body p99 of 2.3 against a bar of 25. Dimensional-read ranking: Muton → Sectoid → Chryssalid → Viper → Floater. | v3 settles it on a **single-generation** 5-up where all five pass the same floor-pool and body-readability thresholds, and where the Floater is legible as a creature rather than two eyes in a void. The current per-frame inconsistency (green pool for Sectoid, cool reflective for Viper, flat gray strip for Floater, cool ellipse for Muton, cool pool with clipped core for Chryssalid) is the thing to close. | **Partly.** Muton 04:15, Floater 04:17 are current-gen; Sectoid 04:08, Viper 03:45, Chryssalid 04:14 are **earlier generations**. The folder is a mix. |
| **Truthfulness** (20%) | `CommandCenter/outputs/lighting/LIGHTING_EVIDENCE.md` (04:18:21) + `verification.json` (04:18:21) + my own numpy re-measurement of all five PNGs | The rig's evidence file **states its own skips** — Sectoid, Muton, Chryssalid, Viper all "render error," only Floater measured. That disclosure is the honest behaviour this axis rewards. But there is a second, harder problem: `verification.json` (04:18:21) carries a Floater-only measurement while the folder presents five frames, and the five PNGs are not one generation. **The verification does not cover the images it is filed next to.** The rig's own numbers for the one enemy it did measure: rim bright pixels 207 = **0.013 of the body** (bar ≥ 0.03), rim band mean 13 (bar ≥ 120), torso p99 = 7 (bar ≥ 25), floor zones 43/51/41 (min diff 4%, bar 15%). Five of its own criteria fail. My independent measurement agrees on direction: Viper rim = 0.17% of body, Muton 0.71% — both far under the 3% bar; Viper 20,242 clipped px, Muton 1,638, Chryssalid 4,247. | v3 settles it when **every** enemy is measured with **no skips**, and the verifier's `generated` timestamp is inside the same minute as every PNG it certifies. A one-enemy verification filed beside a five-enemy folder is the same defect class as a manifest field that disagrees with the pixels: the paperwork claims coverage the artifacts do not have. | No for the doc itself; the **files it describes are mixed-generation**. |
| **Clarity & Communication** (20%) | `CommandCenter/outputs/lighting/XCOM_Sectoid_emissive_only.png` (04:09:06), `XCOM_Viper_emissive_only.png` (03:45:35), `XCOM_Floater_emissive_only.png` (04:17:18), `XCOM_Muton_emissive_only.png` (04:15:47), `XCOM_Chryssalid_emissive_only.png` (04:14:13) + the 5 studio-vs-reveal composites (04:09:31 / 03:45:46 / 04:17:28 / 04:16:00 / 04:14:25) | The **emissive proof shots do not uniformly prove emission**. Sectoid: two eye emitters with white-hot cores and a broad mottled green floor pool — proves it. Chryssalid: two eyes plus a crescent mouth, strongest glow in the set, large green floor pool — proves it. Muton: one bright horizontal bar plus two weak slits, "bloom is clear evidence of a bright emissive material, not of light casting… inconclusive." Floater: narrow visor strip and two dim points, spill too ambiguous to count. **Viper: a small comma-shaped slash and one tiny point, with NO discernible floor or background spill — this does not prove emission at all.** Studio-vs-reveal composites are labelled and the difference between the two rigs is obvious at a glance, but the studio half is a flat lit render and the reveal half is much more dramatic for Muton and Chryssalid, underlit for Viper, and failed for Floater. | v3 settles it on **one proof shot per enemy with a visible neutral receiver** — a lit floor card or wall in frame — so each emissive demonstrably throws light onto another surface. Only 2 of 5 currently meet that. A composite that fails to distinguish studio from reveal in the same frame is a communication failure, not a lighting failure. | **Mixed**: Viper 03:45 is an earlier generation; the other four are current. |
| **Technical Quality** (15%) | `CommandCenter/outputs/lighting/XCOM_Viper_reveal.png` (03:45:25) + `XCOM_Chryssalid_reveal.png` (04:14:03) + `XCOM_Muton_reveal.png` (04:15:39) + `XCOM_Floater_reveal.png` (04:17:10) | Blown highlights are present and measurable: **Viper 20,242 clipped white px and 19,796 clipped body px on the subject** — the vision read is "much of the robot is clipped to featureless white… the overexposed body reads as a glowing silhouette rather than a modeled figure." Muton 1,638 and Chryssalid 4,247 clipped px. The v1 bar required zero blown highlights on the body; Viper fails it by a wide margin. Floor pools also blow locally: Chryssalid's lower foreground core is near-clipped. Background is near-black for Sectoid/Muton/Chryssalid but Viper shows a **visible rear-wall rectangle** and the Floater a gray floor strip and a right-side block. The Floater's own `verification.json` reports `torso_p99_ge_25` failing. | v3 settles it on a **per-enemy clipped-pixel count on the subject silhouette = 0** and `torso p99 ≥ 25` for all five, plus a background measurement confirming nothing but the subject is lit. `Docs/generated/lighting_rig_spec.md` (04:18:21) is now a real UE5 handoff — five elements with cd intensities, actor-space transforms, cone angles, and the 7.96× Blender→cd conversion — so the rig is now portable; that spec did not exist when this review began. | **Mixed**: Viper 03:45 is an earlier generation. |
| **Interaction & Depth** (10%) | `CommandCenter/outputs/lighting/XCOM_Chryssalid_reveal.png` (04:14:03) floor band, `XCOM_Muton_reveal.png` (04:15:39) floor band, `XCOM_Sectoid_reveal.png` (04:08:37) floor band, `XCOM_Viper_reveal.png` (03:45:25) floor band, `XCOM_Floater_reveal.png` (04:17:10) floor band — all five floor bands opened as one 2×3 sheet | This is the axis where the rig is most visibly incomplete. Floor treatment is not a **pool** in three of five: Sectoid's floor band is a broad even green wash with "no clear localized pool"; Viper's is smoky with no definite pool; the Floater's is **almost completely black**. Readable cast shadows exist in only **two of five** — Muton (screen-right, near-horizontal) and Chryssalid (screen-right, upper-right diagonal). "There is only a two-render rightward consistency, not an all-five match." The v1 bar asked for one consistent shadow direction across the set; **that is not met.** Under-glow is inconsistent too: strong on Viper, small on Muton, broad green on Sectoid, none on Floater, no distinct foot source on Chryssalid. The rig spec does describe `reveal_under` as 7.4 cd enabled only during the rise, and `reveal_pool` as the element that produces the bounded ground pool and the contact shadow — so the mechanism exists, but it is not landing consistently. | v3 settles it on **all five** showing: a bounded graded floor pool, a readable cast shadow, and a single agreed shadow azimuth across the set — measured by flooding the floor region and taking the shadow centroid, which is the test I ran. It also settles the *temporal* half: `reveal_under` is only on during the rise, so the rig must be **rendered as a sequence** (rise → idle) to be judged. A still cannot show a light that turns off. | **Mixed**: Viper 03:45 and Sectoid 04:08 predate the 04:14–04:17 frames. |
| **Brand Fit** (5%) | `CommandCenter/outputs/lighting/XCOM_Muton_reveal.png` (04:15:39) + `XCOM_Chryssalid_reveal.png` (04:14:03) + `XCOM_Floater_reveal.png` (04:17:10) | Restrained and on-brand where it lands: near-black backdrop, one cold key, one alien-green rim, no coloured gels, no magenta, no HUD. The green rim is the only saturated hue in frame on Sectoid, Muton and Floater. The risk is the opposite of garish — **absence**. The Floater and Chryssalid frames are so dark that most of the body merges into the background, and Chryssalid's foreground hotspot is a white core rather than a coloured one. | v3 settles it on the same 5-up, judged for *restraint plus legibility*: a frame should be dark and minimal, and still show the creature. Darkness that hides the subject is not restraint. | No — current. |
| **First-Impression Impact** (5%) | `CommandCenter/outputs/lighting/XCOM_Muton_reveal.png` (04:15:39) + `XCOM_Floater_reveal.png` (04:17:10) + `XCOM_Viper_reveal.png` (03:45:25) | The Muton reveal is genuinely arresting: red chest, green visor, hard shadow, a spotlit ellipse on wet ground. The Floater reveal is close to empty — "the actual body cannot be separated from the background." The Viper reveal is a white blob. First contact with the rig, in any order, is dominated by how dark the frame is; the sequence of five does not read as a deliberate reveal set. | v3 settles it on the set viewed as a set, in order, at the size a designer would first see it — with a floor pool present on every frame so the eye has somewhere to land. | **Mixed**: Viper 03:45. |

### What moved since my v1 lighting finding (measured, not asserted)

| v1 finding | v1 state | Now | Movement |
|---|---|---|---|
| reveal_key legible | absent — studio key + green fill on black | cold key on screen-left, clearly separated from the green rim, in 4 of 5 frames | **Largely fixed** |
| reveal_rim legible | absent | opposite-side green edge in Sectoid and Muton; weak/merged in Viper; absent as a *side* rim in Chryssalid (its green is face-centre); near-absent in Floater | **Partially fixed** — 2 of 5 clean |
| reveal_under legible | absent | under-glow on Viper (strong), Muton (small), Sectoid (broad green wash); none on Floater or Chryssalid | **Partially fixed** — 3 of 5, inconsistent in character |
| reveal_pool / floor | absent | graded pools on Muton, Chryssalid, Viper; broad flat green wash on Sectoid; black on Floater | **Partially fixed** |
| Emissive proof | absent | real emissive-only frames exist; **2 of 5 (Sectoid, Chryssalid) actually prove cast light**; Muton weak, Floater ambiguous, Viper does not | **Frames exist; proof incomplete** |
| Zero blown highlights on body | n/a | Viper 19,796 clipped body px, Chryssalid 4,247, Muton 1,638 | **Not met** |
| One consistent shadow direction | n/a | readable in 2 of 5; those 2 agree rightward; the other 3 have no readable shadow | **Not met** |
| UE5-implementable rig spec | **file did not exist** | `Docs/generated/lighting_rig_spec.md`, 04:18:21, 8,479 chars: 5 elements, cd intensities, actor-space X/Y/Z + pitch/yaw/roll, cone angles, 7.96× unit conversion, per-element enable conditions | **Fixed** |

**The rig is no longer "a studio key + green fill on black."** That was the v1 verdict and it is
wrong for the current set. What is now true is narrower and more specific: the rig is built and
half-calibrated, but it is inconsistent between enemies, it blows out on the Viper, and the
verifier skipped four of five frames in the current generation.

---

# CATEGORY 3 — TEXTURES

Evidence: `CommandCenter/outputs/textures/` (03:48–04:11, current), `textures_manifest.json`,
plus my own independent wrap-edge tileability test and crop-identity test.

| Axis | Image file actually opened | What I SAW (observation, not score) | Evidence that would settle the axis in v3 | Superseded? |
|---|---|---|---|---|
| **Visual Craft** (25%) | `outputs/textures/T_Wall_Brick_Old.png` (03:50:15), `T_Wood_Plank_Dock.png` (04:08:32), `T_Wall_Steel_Rusted.png` (03:52:03), `T_Floor_Concrete_Wet.png` (03:48:15), `T_Ground_Gravel.png` (03:54:45), `T_Roof_Tar.png` (03:57:35) — all six opened as one 2×3 sheet | **Two materials are genuinely good now**: brick is "unequivocal" — running bond, pale mortar joints, per-brick colour variation, soot; wood is "very clearly" a weathered dock — horizontal boards, dense linear grain, dark gaps, algae staining. Steel reads as plate with panel divisions, seams and rust runs, but **rivet heads are not consistently legible** at preview size. Concrete reads as concrete (aggregate speckling, pitting, cloudy staining) but "wet" is only suggested by a dark cool tone. **Gravel is the weak one** — pebble boundaries are soft, so it "could also be read as gritty soil, asphalt, or procedural noise." **Roof tar is the weakest** — a "broad blotchy pattern" that "can read as generic dark grunge, camouflage, or lichen-like noise"; its material identity is not immediate. | v3 settles it on a **material-ID sheet at 1:1**: for each of the six, a viewer must name the material from the albedo alone, plus a close crop proving the promised detail (concrete aggregate, distinct gravel stones, steel rivets, wood gaps, roofing laps). Roof tar and gravel are the two that must visibly improve. | No — current. |
| **Truthfulness** (20%) | `outputs/textures/T_Roof_Tar_rough.png` (03:57:37), `T_Wall_Steel_Rusted_rough.png` (03:52:04), `T_Wood_Plank_Dock_rough.png` (04:08:40) + `T_Roof_Tar_normal.png` (03:57:37) | Five of the six material sets are internally coherent: the steel normal encodes real plate seams and rivet dimples, the wood normal encodes plank gaps and grain, the roof normal encodes granular tar and horizontal lap bands, and the steel/wood roughness maps vary along their own structure. **One map is not coherent: `T_Roof_Tar_rough.png`** — "extremely high-contrast black, charcoal, gray, and white patches with hard, block-like boundaries… posterized… it does not form especially convincing smooth wet pools, worn paths, or physically coherent roughness transitions… looks more like generic cellular/random noise than a placeholder." It also **does not align with its own normal map's lap bands.** That is an internal contradiction between two shipped maps of the same asset. Separately: the roughness maps are flat, ambient-lit image previews, so nothing here proves the material *responds* correctly to a light. | v3 settles it on a **roughness/normal coherence test per material** — the roughness variation must track the normal map's structure (laps in roof tar, plate panels in steel, grain in wood) — and on a lit preview showing specular/roughness response, not an albedo-lit flat. | No — current. |
| **Clarity & Communication** (20%) | `outputs/textures/T_Floor_Concrete_Wet_contact.png`, `T_Wall_Brick_Old_contact.png`, `T_Wood_Plank_Dock_contact.png` (2×2 tiling contact sheets) + `T_Floor_Concrete_Wet_crop1/2/3.png`, `T_Wall_Brick_Old_crop1/2/3.png`, `T_Wood_Plank_Dock_crop1/2/3.png` (9 crops, 3×3 sheet) | The contact sheets make repetition visible, which is the honest way to present a tiling material. **Ranking of visible repeat, worst first: WOOD_PLANK_DOCK (worst) — WALL_BRICK_OLD — FLOOR_CONCRETE_WET (best disguised).** Wood's teal patina marks and long grain features act as fingerprints; its vertical join is "especially apparent when matching the teal marks." Brick's exact brick-colour sequence repeats across the join. Concrete's high-frequency speckle hides it well. Separately, the nine "in-scene" crops are **not in-scene**: they are flat front-on renders with no perspective, no scene lighting, no exposed surface edge, no corner, no cast shadow. My own pixel test confirms the three crops of each material are genuinely distinct samples (mean absolute difference 17.6–28.5, not near-duplicates) — so they are different regions, but "crop" is the wrong word for them. | v3 settles it on: (a) contact sheets for **all six** materials, not three; (b) crops re-shot as real 1:1 engine captures with perspective, a visible edge, and scene lighting; (c) the wood texture re-tiled so the teal patina stops being a fingerprint. | No — current. |
| **Technical Quality** (15%) | `outputs/textures/textures_manifest.json` + `render_level.py` source + my edge-energy measurement across the 6 gameplay renders and 4 albedos | The maps are technically sound: 2048×2048 albedos with matching `_normal` and `_rough` (1024×1024), 6 materials + a trim sheet, and a manifest recording per-material `tile_m` and seam ratios. My independent wrap-edge test shows the albedos tile without an obvious hard seam. **The critical defect is downstream, and it is severe: the textures are not applied to the level.** `render_level.py` builds flat `Base Color` materials with **no image texture nodes at all**. I confirmed this numerically — edge energy in the six gameplay renders is 1.3–2.1 against 10–24 in the texture albedos, an order of magnitude apart, which is what untextured flat colour looks like. The vision read on the current renders agrees: "None of the playable floors or walls has convincing material detail." Six good materials are shipping into a level that does not use them. | v3 settles it on the **level render itself**: edge energy in the gameplay frames must land in the same band as the source albedos, and `render_level.py` must contain image-texture nodes. This is the single highest-leverage technical fix in the whole set and it is currently unaddressed. | No — current. |
| **Interaction & Depth** (10%) | `outputs/textures/T_Set_TrimSheet.png` (04:11:45) + the six albedos (03:48–04:08) | A trim sheet exists, so the set is meant to be assembled into a real environment rather than used as six loose swatches. But the albedos are surface maps only — no trim, no trim-sheet region indices, no decals, no grime overlays, no damage variants, no wet/dry states in the set. "Wet" is a filename, not a variable; the concrete's wetness cannot be driven because the roughness map is flat-lit. There is no material authoring depth visible in the shipped assets. | v3 settles it on the **trim sheet actually being used in the level**, with visible trim/moulding against the wall materials, and at least one material with a parameterised second state (wet/dry, clean/dirty) that the level visibly toggles. | No — current. |
| **Brand Fit** (5%) | Six albedos (03:48–04:08) + six current level gameplay renders (04:21:58) | The material palette is disciplined and correct for the brief: wet concrete, gravel, old brick, rusted steel, dock timber, tar roofing — an industrial, grubby, grounded palette. It is restrained and reads as "Gillsystems industrial" rather than sci-fi chrome. The mismatch is that the level renders use a **completely different palette** — flat forest green, teal, burgundy and near-black — so the authored material set and the shipped look do not belong to the same world. | v3 settles it on the level renders adopting the material palette: if the level uses the six authored materials, the brand reads as one world; if it keeps flat green-and-burgundy blocks, the six textures are a separate project. | No — current. |
| **First-Impression Impact** (5%) | `outputs/textures/T_Wall_Brick_Old.png` 03:50:15 + `T_Wood_Plank_Dock.png` 04:08:32 + current level gameplay sheet (6 panels, 04:21:58) | On its own the brick and wood albedos are the most immediately convincing art in the whole review — they are what a texture set should look like. But the first impression a viewer actually gets of "the textures" is the level, and the level shows none of them. The textures are invisible where they are supposed to be doing their job. | v3 settles it on a single level screenshot: if the material detail is on screen, this axis moves on its own; if the textures remain off the walls, the best texture set in the project still scores as invisible. | No — current. |

---

# CATEGORY 4 — LEVEL

Evidence: `CommandCenter/outputs/level/` (all 9 files 04:21:58), including a new
`gameplay_06_pitramp.png` that was not in the earlier set.

| Axis | Image file actually opened | What I SAW (observation, not score) | Evidence that would settle the axis in v3 | Superseded? |
|---|---|---|---|---|
| **Visual Craft** (25%) | `outputs/level/gameplay_01_drop.png` 04:21:58, `gameplay_02_duel.png`, `gameplay_03_pit.png`, `gameplay_04_platform.png`, `gameplay_05_dropzone.png`, `gameplay_06_pitramp.png` — all six opened as one 3×2 sheet | The **lighting is well designed and the geometry is not dressed**. Mint-green and magenta emissive pools, coloured floor bounce and bloom give a coherent moody sci-fi look in every frame, strongest in GP02 (duel) and GP05/GP06. Against that: architecture is cuboids, ramps and blocks; "in-engine greybox or prototype gameplay, not final-environment art." GP03 is the sparsest — a bare floor, a wall, a wedge ramp. The "liquid/marbled" gray backdrop in GP01/02/04 is an abstract swirl, not a material. Materials are flat solid colour throughout (see Technical Quality). | v3 settles it on **dressed geometry** — trim, edge detail, greebles, signage, debris — plus the material set actually applied, in the same frame. Lighting is not the limiter here. | No — current (04:21:58), and **one frame is new**: `gameplay_06_pitramp.png` did not exist in the earlier set. |
| **Truthfulness** (20%) | `outputs/level/blueprint_topdown.png` 04:21:58, `outputs/level/path_diagram.png` 04:21:58, `outputs/level/level_perspective.png` 04:21:58 | The level's own documentation is **honest about its own state**: the blueprint is titled "M_BLOKOUT01 – **UE5 ARENA BLOCKOUT**" and its info box reads "ACTORS 51 \| BASE 33 \| SPAWN 18." It labels its own constraints out loud — "RAMP INSIDE PLATFORM – NO CLIMB", "DROP ON CLEAR GROUND – 18M FROM PILLAR", a red no-access edge, a 2 m tile grid, a scale bar, per-actor IDs (`ENC_Drone_01`, `ENC_Drop_01`, `ENC_Sees_Hardcover`), and a legend. The path diagram states its source: "SOURCE: level_transforms.json (51 ACTORS)." Nothing is oversold. **One inconsistency**: `level_perspective.png` is the only panel with no legend and no key for its glowing markers, so the coloured points in it are unidentifiable. | v3 settles it on the **blueprint and the 3D agreeing actor-for-actor** — every label resolvable in the perspective view, or the perspective panel given a legend. A blockout documented as a blockout is truthful; a blockout documented as a finished arena is not. | No — current. |
| **Clarity & Communication** (20%) | `outputs/level/path_diagram.png` 04:21:58 + `blueprint_topdown.png` 04:21:58 + `level_perspective.png` 04:21:58 — all three opened as one 3-panel strip | The **documentation set is genuinely good and the gameplay frames are not.** `path_diagram.png` communicates the whole level in one image: "DROP → COVER → PIT → PILLAR → OBJECTIVE", two red kill zones, an "OBJECTIVE – BOSS" circle, numbered "COVER 03 / 04 / 05", the no-climb and no-access notes, the 2 m grid and the scale bar. `blueprint_topdown.png` is a complete inventory with a legend and actor IDs. `level_perspective.png` shows massing and verticality but no route, no dimensions, no zone names. In the **gameplay frames** the objective is inferred rather than communicated: "no HUD, objective text, health bars, minimaps, scores, or player markers" in any of the six; GP05 and GP06 have the clearest staging but still only an implied goal. | v3 settles it on the six gameplay frames each having a **readable objective** — a marker, a HUD element, or a strong visual terminus — and on `level_perspective.png` gaining the legend the other two panels have. | No — current. |
| **Technical Quality** (15%) | Six gameplay renders (04:21:58) + `render_level.py` source + my edge-energy measurement | **No broken geometry in any of the six.** The pit and ramp work was fixed — GP03 and GP06 show a real recess with a flush exit ramp, GP04's ramp is one continuous slope with both landings, and GP06 shows the flight with real thickness. The defects that remain are surface-level: GP04's oversized ramp "enters or overlaps the box without a finished joint, trim, or detail"; GP05/GP06 units overlap ambiguously; GP03 has a block cropped at the right edge. The heavy technical sin is the same one as the textures row: **`render_level.py` uses flat `Base Color` materials with no image texture nodes** — the six authored materials are not in the level at all. | v3 settles it on: (a) the ramp/platform joint dressed and closed, (b) no frame-edge crops of scene geometry, (c) image texture nodes present in the level materials with edge energy matching the source albedos, (d) the same 51-actor manifest reconciles against the built map. | No — current. |
| **Interaction & Depth** (10%) | `gameplay_02_duel.png` 04:21:58, `gameplay_05_dropzone.png` 04:21:58, `gameplay_06_pitramp.png` 04:21:58, `gameplay_03_pit.png` 04:21:58 | There is real playable structure: a drop-in, a pit with a flush exit ramp, a climbable platform, a drop zone with a recessed bay, and cover to break line of sight. Units are present in five of six frames (GP03 has only an ambiguous green disc). But **the interactivity is a diagram, not a build**: there is no player character, no weapon, no HUD, no objective marker, and the enemies are primitive proxies. "The objective must be inferred." The path diagram says where a player should go; the gameplay frames do not show a player who can. | v3 settles it on a **playable first-person or third-person frame with a visible player, a visible weapon, and at least one live enemy engaging** — plus the three traversal mechanics (drop, pit exit, ramp climb) shown being traversed. | No — current. |
| **Brand Fit** (5%) | Six gameplay renders (04:21:58) + `path_diagram.png` 04:21:58 | The level reads as disciplined industrial sci-fi: dark teal/olive ground, mint-green and magenta practicals, clean orthographic documentation, a proper 2 m grid. Restraint, not garish. The one brand drift is the **abstract liquid-marble backdrop** in GP01/02/04, which belongs to no material set and reads as a stock shader test. | v3 settles it on the backdrop being either a real environment (sky, haze, distant structure) or one of the six authored materials, rather than an abstract swirl. | No — current. |
| **First-Impression Impact** (5%) | `gameplay_02_duel.png` 04:21:58 + `gameplay_05_dropzone.png` 04:21:58 + `gameplay_06_pitramp.png` 04:21:58 | GP02 is the strongest first frame in the project: layered platforms, an implied red-vs-green duel staging, a foreground turret, coloured floor bounce. GP05 and GP06 are strong encounters. The set as a whole reads as an intentional mood. The limiting factor on first impression is that the frames are visibly blockout — the lighting promises a finished game and the geometry does not deliver, which reads as unfinished rather than stylish. | v3 settles it on a single hero frame from the level with the textures applied and the geometry dressed — at which point the lighting that already works carries the impression. | No — current. |

---

# CROSS-CATEGORY FINDINGS THE SCORING RUN MUST NOT MISS

1. **The textures are not in the level.** `render_level.py` builds flat `Base Color` materials with no
   image texture nodes. Six authored materials (03:48–04:11) do not appear in any of the six
   gameplay renders (04:21:58). Edge energy 1.3–2.1 in the level against 10–24 in the albedos. This
   is a **cross-category** defect: it depresses the level's Visual Craft, Technical Quality and
   First Impression simultaneously, and it makes the texture category invisible in situ.

2. **The lighting verification covers one enemy of five.** `LIGHTING_EVIDENCE.md` (04:18:21) lists
   four render errors and measures only the Floater. The folder mixes three rig generations
   (03:45 / 04:08 / 04:14–04:18). A lighting score written on this folder scores a mixture.

3. **The manifest and the pixels disagree on weapons.** `xcom_manifest.json` (04:28:45) says
   `has_weapon: true` for Viper and Muton. The 04:25:29 and 04:26:56 renders show no readable
   weapon in either set of hands.

4. **The v2 Floater defect is fixed in the current file.** `XCOM_Floater.png` 04:26:15 (eb386e5e0c)
   is legless with no glowing orbs. Verified at 1.4×.

5. **Geometry, not lighting, owns the remaining enemy defects.** No mouth or jaw on any of the four
   humanoids; no readable weapon on Viper or Muton; Chryssalid cropped at the left and bottom frame
   edges. These must not be charged to the lighting rig.

6. **`Docs/generated/lighting_rig_spec.md` now exists** (04:18:21, 8,479 chars) with a full UE5
   handoff — five elements, cd intensities, actor-space transforms and rotations, cone angles, the
   7.96× unit conversion, and per-element enable conditions including `reveal_under` being
   reveal-window-only. The spec's own `reveal_pool` note says it "is what puts a bounded pool of
   light on the ground and the contact shadow under the feet" — and the Floater, whose own
   verification failed `torso_p99_ge_25`, has a black floor. The mechanism is specified; it is not
   landing.

---

# WHAT I COULD NOT VERIFY

- **No axis is scored.** Nothing here is a number I am willing to stand behind until the v3 set is
  frozen and the lighting folder contains one generation with zero skips.
- I did not open any image I have not looked at; where a file was superseded it is flagged in the
  row rather than silently cited.
- The enemy rig used for the 04:24–04:28 hero renders carries **three extra lights beyond the
  brief** (220 W anchor, 640 W cast spot, 260 W floor wash), disclosed in
  `ENEMY_V2_BUILD_REPORT.md`. I judged the enemy images, not the rig.
- **FBX material transfer was not tested in UE** — I read the builder's disclosure that procedural
  materials do not survive the export, but I did not open the FBX in an engine.
- `render_level.py`'s lack of image texture nodes was established by source grep and corroborated
  by edge-energy measurement, **not** by opening the level in UE.
- No credentials or secrets appear in any artifact I read or wrote.

---

# NEXT DISPATCH — WHAT THE SCORING RUN NEEDS

1. **Freeze the set.** No score is meaningful until `out_lighting/`, `out_xcom/`, `outputs/textures/`
   and `outputs/level/` stop changing. During this review all four changed three to four times.
2. **Re-run the lighting rig to a clean generation with zero skips** and confirm
   `verification.json`'s `generated` timestamp falls inside the same minute as every PNG it certifies.
3. **The three fixes that move the most score**, in order:
   - **Apply the six textures to the level** (`render_level.py`: image texture nodes + UV scaling).
     Unlocks level Visual Craft, Technical Quality and First Impression, and makes the whole
     texture category visible. Nothing else in the project has this leverage.
   - **Make the Floater legible in the reveal rig** (its own `torso_p99_ge_25` fails at 7; floor
     mean lum 1.58 against a bar of 25; body p99 2.3). The rig is specified; it is not landing on
     this enemy.
   - **Stop the Viper blowing out** (19,796 clipped body px, 19,796 on the subject) and **get a
     readable cast shadow into all five frames** with one agreed azimuth — currently readable in
     2 of 5.
4. **Then** score all four categories in one run against the frozen set, using this table as the
   axis-to-evidence map.

---

*Written by EBERT, Zero Trust Critic. No score assigned. No verdict issued.
Evidence pinned by SHA-256 prefix and mtime at 2026-10-21T04:41:52-04:00.*
