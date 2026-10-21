# LIGHTING v2 FIX LIST — what the render actually looks like

Source: my own vision pass on `Tools/blender/out_lighting/XCOM_Sectoid_reveal.png` (the other four
enemies share the rig, so every item below applies to all five). Ebert is scoring this category
right now — his verdict lands at `CommandCenter/outputs/ebert/EBERT_LIGHTING_VERDICT.md`. Fix to
his bar AND to the items below; where the two differ, his bar wins.

**The read, in one line: it is a product turntable shot, not a creature revealed out of darkness.**
The rig is no longer absent (that was v1's fatal finding) — it is present but mis-aimed, and the
brightest thing in the frame is the FLOOR, not the face.

---

## 1. The floor hotspot outranks the face — FIX FIRST

The cyan pool in front of the feet is at or near clipping and is the brightest region in the image.
It pulls the eye DOWN and AWAY from the creature. A reveal has the opposite priority.

- Move the cold key OFF-AXIS: back-left three-quarter, not front. The face should catch the key; the floor should not.
- Cut the floor spot's power and pull it behind the subject so the pool falls off the near foreground.
- Acceptance test: in the final render the **emissive eyes must be the brightest pixels in frame**. If the floor pool is brighter, the shot fails.
- Also kill the localized blowouts on the eye surfaces, the forehead specular, and the feet.

## 2. The "rim" is a broad green kicker

Green currently wraps the entire right side of the head, shoulder, arm, and foot. That reads as a
coloured studio fill, not an alien backlight.

- Narrow it: smaller radius, lower power, moved further BEHIND the subject, so only a thin edge catches.
- Keep the colour signature, lose the wash. The rim should describe the silhouette, not paint a side of it.

## 3. There is no real under-glow

What reads as "under-glow" is a floor pool. That is not the same thing — a pool in front of the feet
lights the floor, not the creature.

- Add an actual upward-facing source BELOW the creature (small area or point light under the floor plane, or an emissive ground disc) that lights the SOLES, the INNER LEGS, and the underside of the torso.
- The undersides must be visibly brighter than the surrounding floor in the render.

## 4. Contact shadow is too weak — the creature looks like a toy

There is darkening under the feet but no tight contact-occlusion seam and no clear cast shadow
anchoring both soles. The dark semi-reflective floor displaces the shadow, so the figure reads as
floating slightly.

- Tight contact occlusion at BOTH soles.
- One clear cast shadow, consistent with the key's direction, falling AWAY from the camera.
- The subject must be visibly GROUNDED, not standing on a reflection.

## 5. Crushed blacks

The front of the head and the shoulder sink to featureless black and lose surface shape. The
background blacks are fine — this is the opposite failure.

- Lift the shadow side slightly with a very dim cool bounce so the head's curvature and the shoulder read.
- Do NOT raise the background black — keep the void.

## 6. The emissive is not demonstrated

The eye slits read as bright ivory material catching the key, not as light sources. There is no halo
and no local spill.

- Add controlled bloom (Glare node, LOW threshold, small mix) and a touch of local spill onto the face around the eyes.
- The emissive-only proof shot must show the emissive as the ONLY light source in frame, with the body essentially black.

## 7. Framing — stop showing the whole body

The full torso, both arms, both legs, and both feet are all legible. That is the grammar of a
product beauty render. A creepy reveal CONCEALS most of the body and isolates the face.

- Let the falloff drop the lower body into darkness. Only the head, the eye slits, and one side of the shoulder should be fully readable.
- Drop the camera to slightly BELOW eye level. The current camera looks slightly down onto the tops of the feet — that alone reads as a turntable.
- Tighten the framing so the head carries the frame. There is currently a lot of dead negative space around a small figure.

## 8. Geometry carry-over (enemy agent's remit, but do not hide it)

- The screen-left hand/forearm still reads as DETACHED in this render. That is v1 geometry — the enemy v2 rebuild is in flight and owns it. Do not hide it with lighting: light it honestly, and let the v2 model fix it. Ebert's v1 called detached hands explicitly; if it is still visible in the final lighting pass, the category takes the hit.

## 9. Set consistency

- One shadow direction across all five enemies. Same key position, same rim position, same contact-shadow hardness.
- The same rig params for every frame — if a per-enemy tweak is needed, capture it in `rig_params.json` so the UE5 spec stays reproducible.

---

## Acceptance checklist (run against every one of the five)

| # | Check | Pass condition |
|---|---|---|
| 1 | Key aim | Off-axis, sculpts the face, does not light the floor pool |
| 2 | Floor pool | Dimmest-brightest order: eyes > face > body > floor pool |
| 3 | Rim | Thin edge only, describes the silhouette |
| 4 | Under-glow | Soles, inner legs, and underside visibly lit from below |
| 5 | Contact shadow | Tight seam at both soles + one clear cast shadow |
| 6 | Blacks | Shadow side holds surface detail; background stays black |
| 7 | Emissive | Halo + local spill; emissive-only shot is the sole light source |
| 8 | Framing | Lower body sinks into darkness; camera at or below eye height |
| 9 | Consistency | Same shadow direction in all five frames |

**Re-render targets:** `Tools/blender/out_lighting/XCOM_<Name>_reveal.png` (5),
`XCOM_<Name>_emissive_only.png` (5), `XCOM_<Name>_studio_vs_reveal.png` (5), plus
`rig_params.json` / `rig_params.png` updated with the new values, and the same set mirrored to
`CommandCenter/outputs/lighting/`.

> Psalm 33:6 (ESV) - "By the word of the LORD were the heavens made; and all the host of them by the
> breath of his mouth." Chosen because every asset here is made by command, and the swarm only
> executes what is spoken to it.
