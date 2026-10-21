# EBERT RE-SCORE PACKET — 4-category submission

All paths relative to: `C:\Users\Gillsystems Laptop\source\repos\OCNGill\The_Commander_Boomer_Shooter`

Ebert: apply your own rubric (`Agents/Ebert/designs/zero_trust_likert_rubric.md`) to the
four categories below, in one pass, using the SAME weighted axes, the SAME 6.2 pass bar, the
SAME categorical-fail rule, and the SAME no-rounding rule as your v1 verdict. Look at every
image with the vision tool before scoring it. If you cannot see an image, say so and mark
that axis UNSCORED — never score what you did not look at.

Your v1 verdict (`CommandCenter/outputs/ebert/EBERT_ENEMY_VERDICT.md`, 3.33/7.0 ITERATE) is
the baseline. The v1 delta list you authored is what the builders were given. This packet is
the re-score of the CLOSED delta plus the three categories that were still empty.

---

## (a) ENEMIES — v2 rebuild (re-score of the deltas)

Evidence: `Tools/blender/out_xcom/` — for each of the five enemies:
- `XCOM_<Name>.png` — hero render under the reveal rig
- `XCOM_<Name>_turn.png` — turnaround (3 views)
- `XCOM_<Name>_scale.png` — 1.8 m human reference
- `XCOM_<Name>.fbx` — the mesh
- `xcom_manifest.json` — tris, height, and the per-enemy booleans (ground contact, emissive,
  weapon, face detail)

Your v1 asks, in your own words, were: unmistakable silhouette per enemy, zero detached parts,
the reveal rig plus emissives plus a ground plane with contact shadow, reframed/rescaled renders,
and the missing weapons. Check each one of those five by name against the new renders.

Also check the lighting bar you set (four rig elements in one frame, emissive proof shot, zero
blown highlights, one consistent shadow direction) against `CommandCenter/outputs/lighting/`.

## (b) LEVEL DESIGN

Evidence: `Tools/blender/out_level/` and `CommandCenter/outputs/level/`
- `blueprint_topdown.png` — orthographic, tile grid, legend, real actor names
- `level_perspective.png` — arena in perspective, solid geometry
- `level_shot_*.png` — three ground-level gameplay-perspective frames at ~1.6 m camera height
- `level_path.png` — annotated path diagram (drop zone → cover → objective, route drawn)
- `level_stats.json` / `level_report.md` — actor counts, tactical spaces, objective reachability

Your bar: tile grid + legend, ≥3 ground-level shots, ≥5 total frames, annotated path diagram,
one frame with two or more enemy types at gameplay distance, no unreachable objective, no
camera-blocking geometry, ≥3 distinct tactical spaces, zero floating/clipping props.

## (c) BACKGROUND TEXTURES

Evidence: `Tools/blender/out_textures/` and `CommandCenter/outputs/textures/`
- 6 diffuse sources at 2048², named `T_Floor_Concrete_Wet`, `T_Wall_Brick_Old`,
  `T_Wall_Steel_Rusted`, `T_Ground_Gravel`, `T_Roof_Tar`, `T_Wood_Plank_Dock`
- normal maps + roughness maps
- `*_contact.png` — 2×2 tiling at 50 % offset (seam proof)
- `*_crop1/2/3.png` — native-resolution 1:1 in-scene crops
- `T_Set_TrimSheet.png` — the set trim sheet
- `textures_manifest.json`

Your bar: zero visible seam or repeat in the offset contact sheet for every texture, 2048²
source on every wall/floor, in-scene 1:1 crops with resolvable detail, palette matching the
existing set, distinguishable at a glance, ≥6.2 with Visual Craft ≥6.0.

## (d) LIGHTING

Evidence: `Tools/blender/out_lighting/` and `CommandCenter/outputs/lighting/`
- `*_reveal.png` — reveal rig (cold key / alien rim / under-glow) against a black scene
- `*_emissive_only.png` — proof shot: emissives only, no scene light
- `*_studio_vs_reveal.png` — v1 studio rig vs the reveal rig, same enemy
- `rig_params.json` + `rig_params.png` — captured rig parameters, not prose
- `LIGHTING_EVIDENCE.md` — the measured numbers
- `Docs/generated/lighting_rig_spec.md` — the UE5-implementable rig

Your bar: the four rig elements legible in one frame per enemy, emissives demonstrably emitting
(the proof shot), zero blown highlights on the body, one consistent shadow direction across the
set, ≥6.2 with Visual Craft ≥6.0 and First-Impression ≥5.5.

---

## (e) MAIN CHARACTER — not submitted this pass

The Commander deferred the main character ("we'll worry main character later"). Score it
**NOT SUBMITTED / DEFERRED**, not zero, and do not penalise the other categories for it.
Your v1 bar for the character (≥5 screenshots, animation samples, scale reference, wireframe,
zero detached geometry) is already on record in your verdict and is the spec for the next pass.

---

## OUTPUT

Write `CommandCenter/outputs/ebert/EBERT_V2_VERDICT.md` with:
1. A per-category table: category, weighted total, PASS/REJECT/DEFERRED, and the 7 axes
   (Visual Craft, Truthfulness, Clarity, Technical Quality, Interaction, Brand Fit,
   First-Impression) with one line of evidence each.
2. An overall weighted total for the SET and a single verdict.
3. The categorical-fail check, applied explicitly.
4. A "what moved" list: which of your v1 deltas are now closed, which are still open, with
   the specific evidence that proves it closed (or the exact image and pixel that shows it open).
5. The next top 5 fixes, ranked by score impact — these become the next build brief.

Then append one line to `CommandCenter/outputs/LEDGER.md`:
`EBERT-02 | Hermes-session | CommandCenter/outputs/ebert/EBERT_V2_VERDICT.md | <total> <verdict> | <iso-timestamp>`

If any category's evidence is missing or unreadable, score it as INCOMPLETE and say exactly what
is missing. Ebert scores truthfulness at 20 % — a confident score on evidence that is not there
is the worst possible outcome.

> Psalm 33:6 (ESV) - "By the word of the LORD were the heavens made; and all the host of them by the
> breath of his mouth." Chosen because every asset here is made by command, and the swarm only
> executes what is spoken to it.
