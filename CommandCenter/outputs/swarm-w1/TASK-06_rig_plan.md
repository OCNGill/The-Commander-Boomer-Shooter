# TASK-06 — Rig Plan: Skeletons, Animation Sets, and 1994 Behaviour Support

**Slot:** swarm-w1 · **Model:** minimax/minimax-m3.1-flash:free · **Node:** Gillsystems-Laptop
**Written:** 2026-10-21T03:04:40-04:00
**Companion artifact:** `CommandCenter/outputs/swarm-w1/TASK-01_xcom1994_roster.md` (silhouettes, 1994
appearance, reveal grammar). This document assumes the roster and silhouettes from TASK-01 and does not
restate them.
**Engine:** Unreal Engine 5.8 (Blender authoring → FBX → UE import, per `Docs/DESIGN.md` pipeline).
**Hard locks honoured throughout:** true 3D only (no sprites, no billboards); original X-COM enemies
only, modernized not re-invented; **zero reload animations ever, including enemy weapons**; pickups
are the only health system; **no regeneration** (nothing in this plan revives, heals, or respawns an
enemy in place).

---

## 0. Two things the rig plan inherits that change the job

**0.1 The 1994 game was turn-based on a grid. The Commander is a real-time shooter.** `[repo]`
`Docs/DESIGN.md` specifies Doom-2016-style movement, 144+ FPS, telegraphed attacks, gibs. The 1994
aliens moved in discrete tile steps and attacked once per turn. So a rig that faithfully ports 1994
*animation* (a 1-frame step, a single-shot attack) would produce a game where enemies teleport-step
and feel dead. **The rig therefore has to carry a continuous locomotion layer that the 1994 game
never had, while preserving the 1994 *timing grammar* (a hard, readable, long telegraph before every
committed action).** This is the single biggest departure from the source material and it is
deliberate.

**0.2 The five enemies currently in the repo are STATIC meshes, not skeletal meshes.** `[repo]`
`CommandCenter/outputs/ue_import/xcom_ue_import_report.md` records all five assets imported as
`StaticMesh` with `CTF_USE_COMPLEX_AS_SIMPLE` collision, and `Content/Enemies/XCOM/` contains
`.uasset` files for the meshes and materials only — no `Skeleton`, no `Skeleton Mesh`, no
`PhysicsAsset`, no AnimBlueprint. **Rigging cannot start from those assets.** It requires the
Blender sources to be re-exported with an armature. `Tools/blender/` and `Content/` are locked to
other owners, so this plan *specifies* the export contract rather than performing it, and hands the
executable work to the Blender lane. See §7 (Handoff) and §8 (Open questions).

---

## 1. Global rig conventions (all five + boss tier)

| Rule | Value | Why |
|---|---|---|
| Bone naming | UE5 convention, lowercase with `_l` / `_r` suffix: `upperarm_l`, `spine_02` | Must survive FBX → UE import without rename churn; keeps AnimBP nodes readable |
| Root | Exactly one `root` bone at world origin, **Z = 0 = ground plane** | The v2 fixlist requires feet touching the floor and a tight contact shadow; a non-zero root origin makes contact impossible to author |
| Up axis | FBX exported **Y-up**, root at floor, verified by re-import measurement | Matches the existing FBX contract (`Tools/blender/out_xcom/` FBX_SCALE_ALL) and the UE import report's measured bounds |
| Max bone influences | 4 per vertex | UE hard limit; keeps shader cost flat for the 144 FPS budget |
| Joints | Every articulation carries a **sphere inside the adjoining limb volume** | `[repo, XCOM_ENEMY_V2_FIXLIST §D]` — the rig must not author a "gap" the v2 geometry fixed |
| Ground-facing | Foot bone's sole plane sits at Z = 0; sole contact patch authored as a tight dark decal strip in the sole material | Contact shadow is a graded acceptance item in `LIGHTING_V2_FIXLIST §4` |
| Bone budget | ≤ 45 bones per enemy, ≤ 200 total for the five | `[repo]` five enemies can be on screen at once on a 144 FPS target |
| Root motion | **Off for locomotion** (in-place cycles + capsule movement), **on for two committed actions only**: the Chryssalid leap and the Floater's descent | Turn-based 1994 had no continuous motion; in-place cycles keep AI responsive and keep the enemies' feet from sliding on the UE navmesh |
| Additive layers | Exactly one: a head/neck "look-at" additive | `[repo, XCOM_ENEMY_V2_FIXLIST §H]` the head must turn ~8° toward camera; one additive node is the cheapest way to make an enemy feel aware of the player without a full upper-body stack |
| Physics | One `PhysicsAsset` per enemy, bodies mirroring the bone list, used for **ragdoll-on-death only** | Death → ragdoll is the cheapest high-impact "satisfying gib" and needs no new art |
| Gib chunks | **Static** chunk meshes from a `BP_GibChunk` pool, spawned by the blueprint | `[repo, Docs/generated/blueprint_build_spec.md §5]` already specifies a pooled `BP_GibChunk` with `Add Impulse` and radial impulse 5000 / radius 500. The rig does not need to model gibs; the mesh silhouette does |
| Reloads | **FORBIDDEN.** No `*_Reload` clip may exist for any enemy or enemy weapon. | Hard lock. See §4.6 for the legal substitute (coil charge as a material parameter, not a bone animation) |

### 1.1 The animation naming contract

`A_<Enemy>_<Action>` — e.g. `A_Viper_Idle_Combat`, `A_Chryssalid_Telegraph_Leap`.
This matters mechanically, not cosmetically: the reload ban is enforced by a **name ban** so a
future pass cannot quietly add one. A review script should fail the build if any clip name matches
`(?i)reload|magazine|ammo` **and** if any animation asset for an X-COM enemy exceeds the clip count
in §3. One line of Python, run in CI. Recommend adding it to the same place the byte-check for fleet
files already runs.

---

## 2. Per-enemy skeleton plans

Bone lists are the **minimum** rig; extra bones are permitted only with a stated reason. Counts in
parentheses.

---

### 2.1 SECTOID — `SKEL_XCOM_Sectoid` (32 bones)

Small, gaunt, forward-pitched biped. `[repo, TASK-01 §2.1]` The hunch is the pose, so the spine
must be able to hold ~22° of permanent forward pitch without the animation fighting the rest pose.

```
root
└─ pelvis
   ├─ spine_01
   │  └─ spine_02
   │     └─ chest
   │        ├─ neck_01
   │        │  └─ head                      (no jaw bone: canonically mouthless)
   │        │  ├─ clavicle_l ─ upperarm_l ─ lowerarm_l ─ hand_l ─ digit_l_1..3
   │        │  └─ clavicle_r ─ upperarm_r ─ lowerarm_r ─ hand_r ─ digit_r_1..3
   │        └─ (chest → arm chains as above)
   ├─ thigh_l ─ calf_l ─ foot_l ─ toe_l
   └─ thigh_r ─ calf_r ─ foot_r ─ toe_r
```

**Notable choices.**
- **No jaw bone, and no mouth geometry.** `[repo, XCOM_ENEMY_V2_FIXLIST §C]` The Sectoid is
  canonically mouthless; a jaw bone would invite an animator to open a mouth that must not exist.
- **No eye bones.** The eyes are emissive geometry, and 1994's read was a static 32×32 sprite
  `[recall, TASK-01 §0]`; animated eyes would fight the "no face" design. The look-at additive
  rotates the *head*, and the emissive lens tracks.
- **Three digits per hand, one phalanx each.** The v2 geometry uses a palm block + 3 tapered digits
  of different lengths `[repo, manifest]`; one bone per digit is enough to splay them.
- **Two-bone IK on both legs** (`IK_Foot_L`, `IK_Foot_R`) targeting the ground: the Sectoid is the
  smallest creature and its thin legs are the most likely to read as "hovering" if the soles slip.
- **Permanently pitched spine.** The rest pose stores ~18–22° of forward pitch at the pelvis and
  ~8° extra at the head `[repo, manifest v3]` so every clip inherits the hunch rather than
  re-creating it per clip.

---

### 2.2 VIPER — `SKEL_XCOM_Viper` (44 bones)

Tall, narrow reptilian hunter. `[repo, TASK-01 §2.2]` Needs a jaw (the six bone teeth in a recessed
seam `[repo, manifest v2]`) and a tail (a 1994-recognisable silhouette element in profile and the
counterweight for the forward-pitched head).

```
root
└─ pelvis
   ├─ spine_01 ─ spine_02 ─ spine_03 ─ chest
   │  ├─ neck_01 ─ neck_02 ─ head ─ jaw
   │  ├─ clavicle_l ─ upperarm_l ─ lowerarm_l ─ hand_l ─ digit_l_1..3 ─ claw_l
   │  └─ clavicle_r ─ upperarm_r ─ lowerarm_r ─ hand_r ─ digit_r_1..3 ─ claw_r
   ├─ tail_01 ─ tail_02 ─ tail_03 ─ tail_04
   ├─ thigh_l ─ calf_l ─ foot_l ─ toe_l
   └─ thigh_r ─ calf_r ─ foot_r ─ toe_r
```

**Notable choices.**
- **Two neck bones.** A 45 cm forward-projecting snout `[repo, manifest v2]` puts a lot of mass
  ahead of the neck; one neck bone makes the head swing, two let the skull *lead* the motion and
  the neck follow — which is exactly the reptilian read.
- **`jaw` bone, 6 teeth** — the jaw must open for the attack and for the "hiss" telegraph.
- **Four tail bones** — the tail is the counterweight for the forward-pitched head. On the 1994
  read, a Viper in motion is a question-mark: head forward, ribs up, tail down `[recall, TASK-01]`.
  The tail must lag the hips by ~1/4 cycle.
- **Dorsal rib ridge is NOT rigged.** The five-rib ridge `[repo, manifest v2]` is modelled into the
  mesh and weighted to `spine_02`/`spine_03` as rigid segments. It reads as a silhouette element;
  making it flex would cost bones and buy nothing.
- **Two-bone leg IK** as with the Sectoid.

---

### 2.3 FLOATER — `SKEL_XCOM_Floater` (24 bones)

The legless hoverer. `[repo, TASK-01 §2.3]` **This is the rig where "no legs" is a hard structural
requirement, not a style note** — the v3 build deleted every descending rod and sphere and left
"the body-shaped hover ellipse on the floor is the only thing beneath it" `[repo, manifest v3]`.

```
root
└─ hover_root                        (bob + bank; the only thing that moves the whole body)
   └─ pelvis
      ├─ spine_01 ─ spine_02 ─ chest
      │  ├─ neck_01 ─ head
      │  ├─ wing_l_01 ─ wing_l_02 ─ wing_l_03
      │  └─ wing_r_01 ─ wing_r_02 ─ wing_r_03
      ├─ tendril_l_01 ─ tendril_l_02
      ├─ tendril_r_01 ─ tendril_r_02
      └─ core                          (dorsal power core; emissive, 3 lens segments)
```

**Notable choices.**
- **`hover_root` exists to make "no legs" riggable.** The whole body bobs, banks, and yaws from a
  single parent bone, so no animator can ever accidentally key a leg. The Floater's silhouette
  guarantee ("nothing underneath") is a **rig-level invariant**, enforced by the absence of leg
  bones, and it is testable: a script can assert the Floater's bone list contains no bone whose
  name matches `thigh|calf|foot|toe|leg`.
- **Three wing bones per side** — enough to sweep, tip-flap and curl. A single wing bone would give
  a paper-plane flap and lose the manta read.
- **The two rear tendrils** (v3: "a pair of short hair-fine filaments trailing off the REAR of the
  shell" `[repo, manifest v3]`) get 2 bones each for a trailing drag.
- **`core` bone** so the emissive core can pulse and, more importantly, so the designer has an anchor
  for the psi/levitation VFX that a 1994 Floater's abduction would use.
- **No ground-contact requirement, and that is deliberate.** The Floater gets a hover shadow
  ellipse, not a contact seam `[repo, LIGHTING_V2_FIXLIST §3, §4]`. The rig must not add a "ground
  IK" to this creature.

---

### 2.4 MUTON — `SKEL_XCOM_Muton` (40 bones)

The heavy. `[repo, TASK-01 §2.4]` Heaviest silhouette (1:1.8 width:height `[repo, manifest]`), needs
the most convincing weight shift of the five, and carries a two-handed heavy plasma rifle `[repo]`.

```
root
└─ pelvis
   ├─ spine_01 ─ spine_02 ─ spine_03 ─ chest
   │  ├─ neck_01 ─ head
   │  ├─ clavicle_l ─ upperarm_l ─ lowerarm_l ─ hand_l ─ digit_l_1..3
   │  └─ clavicle_r ─ upperarm_r ─ lowerarm_r ─ hand_r ─ digit_r_1..3
   ├─ thigh_l ─ calf_l ─ foot_l ─ toe_l
   └─ thigh_r ─ calf_r ─ foot_r ─ toe_r
```

**Notable choices.**
- **No separate pauldron bones.** The huge angled pauldrons `[repo, manifest v2]` are weighted to
  `clavicle_l/r` and `upperarm_l/r`. They must move *with* the shoulder, not independently, or the
  armour will shear against the torso in a 360° turn.
- **No visor bone.** The horizontal emissive visor slit `[repo, manifest v2]` is emissive material
  on the head. It gets its animation from a **material emissive parameter** (idle dim → telegraph
  hot → attack flare), not from bones. This is the single cheapest way to make the Muton read as
  *aggressive* without a facial rig, and it costs zero bones.
- **Two-handed weapon → both hands on the rifle.** The heavy plasma rifle is held two-handed with a
  foregrip `[repo, manifest v2]`. The rig must therefore place the weapon on a **socket on
  `hand_r`** with the left hand **IK-constrained to the foregrip** during the attack clip. This is
  the only two-handed grip in the kit, and it is the reason the Muton needs the most attention in
  the weapon-hand-off animation.
- **Two-bone leg IK** and a **deliberately heavy foot-plant**: the Muton's contact shadow is the
  strongest of the five and the floor pool problem in `LIGHTING_V2_FIXLIST §1` was worst on the
  Muton's feet.

---

### 2.5 CHRYSSALID — `SKEL_XCOM_Chryssalid` (46 bones)

Low, long, forward-pitched, four-legged stalker with two scythe forelimbs. `[repo, TASK-01 §2.5]`
**The only quadruped in the kit and the only enemy with a genuine ballistic attack.**

```
root
└─ pelvis
   ├─ spine_01 ─ spine_02 ─ spine_03 ─ thorax
   │  ├─ neck_01 ─ head ─ jaw
   │  ├─ scythe_l_01 ─ scythe_l_02
   │  └─ scythe_r_01 ─ scythe_r_02
   ├─ leg_fl femur_fl ─ tibia_fl ─ tarsus_fl ─ claw_fl
   ├─ leg_fr femur_fr ─ tibia_fr ─ tarsus_fr ─ claw_fr
   ├─ leg_bl femur_bl ─ tibia_bl ─ tarsus_bl ─ claw_bl
   ├─ leg_br femur_br ─ tibia_br ─ tarsus_br ─ claw_br
   ├─ tail_01 ─ tail_02 ─ tail_03
   └─ venom_sac
```

**Notable choices.**
- **Digitigrade leg chains: femur → tibia → tarsus → claw** (four bones per leg, 16 total). The
  v3 model is explicitly four long digitigrade legs with a clawed foot touching the floor
  `[repo, manifest v3]`. A plantigrade two-bone leg would destroy the "fast crouch" silhouette.
- **The scythes are two-bone chains with NO hand/wrist** — they are blades, not arms. They must not
  be able to grip, and giving them a `hand` bone would invite exactly that.
- **`venom_sac` bone** so the sac can squash on the wind-up and the venom glow can spike. This is
  the Chryssalid's "first contact" read in the dark — two small green points `[repo, TASK-01 §2.5]`.
- **No IK on the legs.** The tarsus geometry already touches the floor `[repo, manifest v3]`, and
  IK on a digitigrade leg chain fights the authored crouch. Instead: the four feet are the contact
  anchors and the gait is authored in-place with a **root-motion leap clip** for the pounce.
- **The only enemy whose root motion is used for a committed action** (see §3.5).

---

### 2.6 Boss tier — skeletons, abbreviated

Not modelled yet `[repo, XCOM_ENEMY_DESIGN_BRIEF §ROSTER]`, but the rig should be designed so they
slot in without a re-work of the shared conventions.

- **ETHEREAL** (`SKEL_XCOM_Ethereal`, ~30 bones) — tall gaunt floater. Shares the `hover_root`
  pattern with the Floater, but with **two long arms and long finger chains** and a
  `mask_visor` bone for the vertical face slit. The mind-control beam is VFX driven from `head`.
- **SILICOID** (`SKEL_XCOM_Silicoid`, ~36 bones) — humanoid robot. Same biped layout as the Muton
  but with **no fingers** (three rigid digits) and a `lens` bone for the red eye-lens. The 1994
  Silicoid's defining property is that it moves like a person but *too smoothly* `[recall,
  TASK-01 §3.2]` — the rig must permit **no idle fidget whatsoever**, which is a rig *constraint*
  (no secondary motion bones) as much as an animation direction.
- **DREADNOUGHT** (`SKEL_XCOM_Dreadnought`) — not a character rig. If built, it is a **vehicle**: a
  spine of ~20 segments + four wing booms, animated as a single rigid body with a slow bank, and
  it never uses the enemy AnimBP, the look-at additive, or the gib system. It is a level actor.

---

## 3. The animation set

### 3.0 Shared required clips (every enemy, unless excluded in §3.5)

| Clip | Length (30 fps) | Loop | Purpose |
|---|---|---|---|
| `A_<E>_Idle_Combat` | 90 f (3 s) | yes | Standing combat idle. Weight shifts, breathing, weapon settle. |
| `A_<E>_Idle_Alert` | 60 f (2 s) | yes | Has noticed the player. Head up, body squared. |
| `A_<E>_Walk` | 40 f | yes | Ground locomotion, in-place, no root motion. |
| `A_<E>_Run` | 24 f | yes | Chase locomotion, in-place. |
| `A_<E>_Turn` | 20 f | no | 90° turn in place, blends locomotion. Prevents foot-slide on the navmesh. |
| `A_<E>_Telegraph` | 20–26 f (0.66–0.86 s) | no | **The commit point.** See §3.1. |
| `A_<E>_Attack` | 14–22 f | no | The strike. Damage applied at a fixed notify frame. |
| `A_<E>_HitReact` | 14 f | no | Flinch, additive-friendly, no hitstop baked in. |
| `A_<E>_Death` | 60 f (2 s) | no | Collapse, then blends into the ragdoll. |
| `A_<E>_Death_Gib` | 45 f (1.5 s) | no | Alternate death used when the enemy dies inside the gib radius — the body bursts into chunks instead of ragdolling. |
| `A_<E>_Reveal` | 8 f (0.27 s) | no | The emergence pose for the reveal: braced, coming up into the key light. See §3.4. |
| `A_<E>_LookAt` (additive) | 30 f | yes | Head/neck additive layer, ±20° yaw, ±10° pitch, clamped so the neck never tears. |

**No `*_Reload` clip, ever, on any enemy or enemy weapon.** See §4.6.

### 3.1 The telegraph is the product

`Docs/DESIGN.md` and `blueprint_build_spec.md` both specify a telegraph-first enemy:
`Telegraph → timer 0.5 s → Attack → timer 1.0 s → Idle` `[repo, blueprint_build_spec.md §4]`.

**Recommendation to the owning session: raise the telegraph to 0.8 s for the heavy enemies and keep
0.5 s for the fast ones, and encode the telegraph duration in the enemy blueprint as a per-enemy
value rather than a global constant.** The current global 0.5 s does not fit a Muton (heavy,
telegraphed attacks) and a Chryssalid (fast) equally, and the roster's whole identity is speed
contrast. This is a report, not an edit — `blueprint_build_spec.md` is not in my writable scope.

The 1994 grammar that we are preserving: an alien in 1994 committed to exactly one thing per turn
and told you what it was going to do with a *stance* before it did. The modern version keeps the
stance and extends the tell into 0.5–0.8 seconds of readable, unmissable motion.

### 3.2 Locomotion — the 1994 gap, filled deliberately

1994 aliens did not walk continuously `[recall, TASK-01 §0]`. The Commander needs them to. The
solution that keeps the 1994 feel:

- **Locomotion is slow and readable.** The Viper and Muton walk with a deliberate, weighty cadence —
  a heavy enemy should look like it is *committing* to a position, not skating. This is where the
  1994 "one step per turn" feel survives: each step is legible and separated.
- **Locomotion never attacks.** The enemy stops, plants, telegraphs, and attacks. A run cycle that
  includes a weapon swing is the fastest way to make an enemy feel unfair.
- **The Chryssalid is the exception** and gets a real run, because a fast crouching stalker that
  moves slowly reads as a prop.

### 3.3 The attack contract

Every attack clip carries an explicit notify so the blueprint applies damage at a fixed frame:

- `Notify_Impact` — the frame the weapon/limb connects. Placed on the contact pose, not on the
  first frame of the swing.
- `Notify_Ember` — the frame the plasma coil flares, so VFX can sync to the weapon light.
- `Notify_Abduct` — Floater only: the frame the human is lifted.

**No hitscan for the enemy either.** `Docs/DESIGN.md` bans hitscan for the player's feel weapons
`[repo]`; the same rule is applied to enemies, which is why the Viper's plasma is a **projectile
with a visible bolt** and the telegraph has to be long enough to dodge. This is a *design* rule
with a *rig* consequence: the Viper and Muton need a visible weapon in the frame, which is why the
weapon is a separate mesh bound to `hand_r` with a socket, and why the telegraph must bring the
weapon up into the key light.

### 3.4 The reveal clip

This is where TASK-01's research feeds directly into the rig.

The 1994 reveal was a **pop from black**: the unit was not drawn at all until a soldier had line of
sight, and then it was simply there `[recall, TASK-01 §0]`. The modern version must not fade in.
So:

- `A_<E>_Reveal` is **8 frames** and is played with the enemy already at full silhouette, emerging
  *upward into* the reveal key — an 8-frame rise, not an 8-frame fade. The light does the work.
- The clip's job is to sell that the creature was *already crouched there in the dark*, waiting.
  Each enemy gets a different version of that crouch: the Sectoid's hunch deepens, the Viper's head
  comes up off its coil, the Muton rises from a low stance, the Chryssalid uncoils, the Floater
  descends *into* frame.
- The reveal is driven by the spawn event in UE and replicated as the `reveal_key` / `reveal_rim` /
  `reveal_under` point/spot light set on the spawn actor `[repo, XCOM_ENEMY_DESIGN_BRIEF §THE
  CREEPING PART]`. The **rig owns the pose**, the **light rig owns the flash**, and the **audio owns
  the sting** — because in 1994 the contact was announced by sound before it was announced by sight
  `[recall, TASK-01 §0]`. The audio must land on the same frame as the light snap.

### 3.5 Per-enemy animation set, with the 1994 behaviour each one carries

| Enemy | Extra clips beyond §3.0 | The 1994 behaviour the rig carries | 1994 source |
|---|---|---|---|
| **Sectoid** | `A_Sectoid_Telegraph_Psi` (arms raise, head tilts back, eyes brighten), `A_Sectoid_Attack_Psi` (a psychic pulse — *no* melee), `A_Sectoid_Panic` (the 1994 civilian-panic behaviour) | 1994 Sectoids were unarmed psychic infiltrators whose weapon was **panic/berserk in nearby humans** and who fought as small squads. The rig gives the Sectoid **no weapon mesh and no weapon socket** — a hard structural statement, testable by asserting `hand_r` has no socket. The "pulse" is VFX from the chest/head. | `[recall, TASK-01 §2.1]` |
| **Viper** | `A_Viper_Telegraph_Spit` (jaw opens, head cocks), `A_Viper_Attack_Plasma` (two-handed bolt, `Notify_Ember` on the coil flare), `A_Viper_Hiss` | 1994 Viper = the standard terror-mission line unit, plasma rifle, **no melee**. Rig consequence: the "attack" is always a ranged bolt, so the weapon must be prominent, the telegraph must raise it, and the Viper must never close to contact range. | `[recall, TASK-01 §2.2]` |
| **Floater** | `A_Floater_Telegraph_Descend` (the body tips and drops), `A_Floater_Attack_Levitate` (tendrils reach, `Notify_Abduct`), `A_Floater_Idle_Hover` (continuous bob, replacing the ground idle) | 1994 Floater = aerial ambusher, **no weapon**, abducts a human off the map by levitation. Rig consequence: `hover_root` carries the descent with **root motion enabled for the descent only**; the attack is a *grab*, not a shot; and there is no ground-contact requirement. | `[recall, TASK-01 §2.3]` |
| **Muton** | `A_Muton_Telegraph_Rifle` (rifle comes up two-handed, visor emissive goes hot), `A_Muton_Attack_Plasma` (heavy cannon, one big shot, `Notify_Ember` + `Notify_Impact`), `A_Muton_Idle_Stance` (wide, planted, weapon across the chest) | 1994 Muton = armoured heavy with a heavy plasma cannon, the terror-mission showstopper, and the unit that ended missions by weight of fire. Rig consequence: **the heaviest, slowest locomotion in the kit**, a long telegraph, a single devastating committed shot, and the only two-handed weapon hold (left hand IK'd to the foregrip). | `[recall, TASK-01 §2.4]` |
| **Chryssalid** | `A_Chryssalid_Telegraph_Coil` (rear arches, scythes cross, venom sac swells), `A_Chryssalid_Attack_Leap` (**root motion**, ballistic arc, scythes sweep on landing), `A_Chryssalid_Run` (a real fast run, not a walk cycle) | 1994 Chryssalid = fast, leaping terror that crossed the map in a single bound and struck a human down. Rig consequence: it is the **only enemy with a root-motion attack** and the only one with a genuine sprint; its attack ends in a *landing* with the scythes forward, and its reveal read is "two small green points moving across a dark tile" — so the venom/eye emissives must be visible before the body resolves. | `[recall, TASK-01 §2.5]` |
| **Ethereal** | `A_Ethereal_Telegraph_Beam`, `A_Ethereal_Attack_MindControl`, `A_Ethereal_Idle_Hover` | 1994 Ethereal = psi apex that turns one of *your* soldiers against you. Rig consequence: the beam telegraph, and the affected soldier needs a **faction/hostility marker flip** — a gameplay-visual state, but the rig must leave the head free so the beam has a readable origin. | `[recall, TASK-01 §3.1]` |
| **Silicoid** | `A_Silicoid_Telegraph_Aim`, `A_Silicoid_Attack_Plasma`, `A_Silicoid_Idle_Static` | 1994 Silicoid = cybernetic raid soldier, featureless steel face, one red lens, **mechanically smooth** movement. Rig consequence: **zero idle fidget, zero secondary motion** — the rig is deliberately austere so the animation can be too. | `[recall, TASK-01 §3.2]` |

### 3.6 Death and gib

- 1994 X-COM had **no gore at all** — aliens simply stopped and were removed `[recall, TASK-01 §0]`.
  The Commander's `Docs/DESIGN.md` requires "screen shake + blood + gibs on every kill" `[repo]`.
  **This is an intentional, declared departure from the 1994 source**, and it should be labelled as
  one in the art bible so a later reader does not think the 1994 game had gibs.
- **Death flow:** `A_<E>_Death` plays for 0.35 s (a collapse with a specific final pose), then the
  PhysicsAsset ragdoll takes over for the remaining 1.65 s while the chunk burst fires.
- **Gib flow:** on death, spawn 12–15 `BP_GibChunk` static meshes `[repo, blueprint_build_spec.md
  §5, 12 chunks for the base enemy / 15 for the heavy]` from a pool, apply the specified radial
  impulse (strength 5000, radius 500, falloff 1.0) at the death location, and fade them over
  0.5 s. **The chunk meshes are cut from the same silhouette as the skeletal mesh** so the kill reads
  as *this* creature coming apart, not as generic debris.
- **No respawn, no regeneration, no health pickup from enemies.** `Docs/DESIGN.md` states pickups are
  the only health system and there is no regeneration `[repo]`. A dead enemy stays dead; the
  rig/animation pipeline must not include any "re-form" or "reconstitute" clip, and the gib pool
  must return chunks to the pool rather than respawning enemies.
- **The reveal light must die with the enemy.** When an enemy dies, its `reveal_rim` / `reveal_under`
  lights ramp to zero over the death clip, so the corpse is not lit like a live creature. That ramp
  is driven from the death notify, not from the animation.

---

## 4. Constraint compliance

### 4.1 True 3D only
Every skeleton above is a 3D armature on a 3D mesh. No sprite frames, no billboard planes, no
cross-quads. The 1994 game was sprite-based `[recall, TASK-01 §0]`; that is exactly what this pass
replaces, and the 1994 *design* (silhouette-first) is preserved while the 1994 *technology* is
discarded.

### 4.2 Original X-COM enemies only
Section 2 rigs exactly the five built enemies plus the 1994 boss tier. Note for the session owner:
TASK-01 §1.1 flags that the brief's second wave also lists 1997/2012-lineage names (Borg, Chosen,
Celestial, Retinoid) — **no rigs are proposed for those** until the roster question is answered.

### 4.3 Zero reload animations
- No reload clip appears in any set above, and no reload clip may be authored.
- **Legal substitute for the plasma weapons:** the emitter coil is a **material emissive parameter**,
  not an animation. After N shots the coil dims (`CoilCharge` 1.0 → 0.0 over the cooldown), the
  Viper/Muton holds its aim at idle while it recovers, and the coil re-brightens. This is a *firing
  cycle*, not a reload: nothing is inserted, nothing is ejected, no hand goes to a magazine.
- **Enforcement:** CI check on animation asset names — any X-COM enemy animation matching
  `(?i)reload|magazine|bolt_cyc|pump` fails the build. Add the same pattern to the enemy *weapon*
  meshes so a "reload part" can never be authored onto a gun.
- Note that 1994 aliens had no ammunition economy to reload from `[recall]`, so the ban costs the
  project nothing historically.

### 4.4 Pickups-only health, no regeneration
Nothing in this plan adds healing, regeneration, respawn-in-place, or revival. Enemies are
terminal on death (§3.6). The only "recovery" in the kit is a *weapon* cooldown, which is an ammo
state, not a health state, and does not touch the health system.

### 4.5 No re-invention
Every bone exists to serve a documented 1994 feature: the Viper's jaw and tail for the reptilian
silhouette, the Chryssalid's four digitigrade chains for the fast crouch, the Floater's
leglessness for the hover read, the Sectoid's missing jaw for the mouthless skull, the Muton's
visor-as-material for the featureless helm. Nothing is added for "modern" reasons alone.

### 4.6 Where the plan deliberately departs from 1994 (declared, so it is not mistaken for fidelity)
1. Continuous locomotion (§0.1, §3.2) — the 1994 game had none.
2. Gibs and blood (§3.6) — the 1994 game had none.
3. The reveal rig and reveal clip (§3.4) — the 1994 game had a pop from black and a plasma glow, not
   a designed light rig. TASK-01 §0 explains the reconciliation; this rig plan implements the
   reconciled version.
4. Real-time telegraph durations (§3.1) — 1994 telegraphs were one turn, and infinite by comparison.

---

## 5. Performance budget (144 FPS target)

| Item | Budget |
|---|---|
| Bones on screen (worst case: 2 Mutons + 2 Vipers + 1 Floater) | 44·2 + 44·2 + 24 = 200 bones |
| Anim BP instances | 1 per enemy; one state machine, one additive slot, no anim stacks |
| Look-at additive | 1 node, clamped, may be disabled per-enemy on the cheapest AI tier |
| IK solvers | 2-bone IK, 2 legs, on Sectoid/Viper/Muton only. Off by default; enabled only for the enemies actually visible in a fight |
| Physics | Ragdoll only, and only after death. Active ragdolls capped at 4 (oldest culled) |
| Gib chunks | 12–15 per death, pooled, 2.5 s life `[repo, blueprint_build_spec.md §5]` |
| Bone influences | ≤ 4 per vertex (UE limit) |

**Recommendation:** build the AnimBP with a **distance-based LOD** — the cheapest enemy tier (Sectoid)
runs without IK and without the look-at additive beyond 25 m. The heavy Muton is the one the player
will be closest to and must be the most expensive; the Chryssalid is the fastest and must have the
shortest telegraph.

---

## 6. DoD for the rig pass (checkable)

- [ ] Each of the five enemies has a UE5 Skeleton, Skeletal Mesh, PhysicsAsset, and AnimBP, and the
      Skeletal Mesh **replaces** the current static mesh at the same path — or a new path, with the
      static mesh deleted to avoid two copies in the game. `[repo, currently static meshes only]`
- [ ] Bone names follow §1 exactly and match the FBX export 1:1.
- [ ] FBX re-exported Y-up with the root at Z=0, verified by re-import measurement against the
      existing manifest heights (1.44 / 2.06 / 0.33 / 2.07 / 1.03 m `[repo, manifest v3]`).
- [ ] Foot soles verified at Z=0 in the UE viewport for all four grounded enemies.
- [ ] Every clip in §3 exists and plays; the clip count per enemy is not exceeded (§1 naming ban).
- [ ] **No clip or mesh name matching `(?i)reload|magazine` exists in the enemy asset tree.**
- [ ] `A_<E>_Reveal` plays with the enemy already at full silhouette; **no fade material is used on
      any enemy** (a fade would be a billboard-era cheat and would soften the pop-from-black).
- [ ] The Floater's bone list contains **no** bone matching `thigh|calf|foot|toe|leg`.
- [ ] The Sectoid has **no jaw bone** and **no weapon socket**.
- [ ] The Chryssalid's attack clip has root motion; every other attack clip has none.
- [ ] The Muton's left hand is IK-constrained to the rifle foregrip for the whole attack clip.
- [ ] Death → ragdoll handoff is clean (no snap) on all five; chunk burst fires at the death notify.
- [ ] The reveal lights ramp to zero with the death clip.
- [ ] No respawn-in-place, no regeneration, no health pickup drops from enemies.
- [ ] Full pass at 144 FPS with 5 enemies + 15 gib chunks live.

---

## 7. Handoff — what this pass needs from other lanes

| Owner | What is needed | Blocking? |
|---|---|---|
| Blender lane | Re-export all five FBX **with an armature** (this is the current hard blocker: the repo has meshes only, no rigs), matching the §2 bone lists | **Yes — nothing can be rigged in UE until this lands** |
| Blender lane | Cut the §3.6 gib chunk meshes (12–15 per enemy) from the same silhouette as the skeletal mesh | Yes, for the gib acceptance item |
| UE lane | Skeletal Mesh + Skeleton + PhysicsAsset import settings, AnimBlueprint state machine, and the `reveal_*` light spawn rig (that rig is specified in TASK-01 §5 and in `XCOM_ENEMY_DESIGN_BRIEF`; TASK-03 owns the reveal *effect* spec) | Yes |
| Session owner | Decide the 1994 vs 1997-linenage roster question (TASK-01 §1.1) before boss-tier rigs are budgeted | No — the five are unaffected |
| Session owner | Rule on the per-enemy telegraph duration (§3.1) — the current global 0.5 s in `blueprint_build_spec.md` | No, but it changes clip lengths |

**Note on the Blender lock:** this pass did not run Blender and did not touch `Tools/blender/` or
`Content/` (both owned by other sessions). The rig plan is deliberately written so that the Blender
lane can implement it from the bone lists alone, without needing to re-read this document.

---

## 8. Open questions for the session owner

1. **Roster lineage** (TASK-01 §1.1) — Chosen / Celestial / Borg / Retinoid are 1997/2012 designs.
   Do they get rigs, and if so are they labelled as later-linenage?
2. **Per-enemy telegraph duration** (§3.1) — propose 0.5 s (Sectoid, Viper, Floater, Chryssalid)
   and 0.8 s (Muton), encoded per-enemy rather than globally.
3. **Ragdoll vs chunks** (§3.6) — the blueprint's `BP_GibChunk` pool is specified for 12–15 chunks.
   Should the death be a full ragdoll *plus* chunks, or chunks only with a short scripted collapse?
   (Recommendation: chunks only with a scripted collapse — a ragdoll *and* chunks is double the
   physics cost for a busier image.)
4. **Chryssalid infection** (TASK-01 §6.4) — if the 1994 Chryssalid-turned-human mechanic is
   adopted, it needs a spawner the rig does not cover, and it is a *spawn* not a regen, so it does
   not violate the no-regeneration lock.
5. **Skeletal vs static asset paths** — the five enemies currently occupy
   `/Game/Enemies/XCOM/XCOM_<Name>` as StaticMeshes `[repo, xcom_ue_import_report.md]`. Should the
   skeletal meshes take those exact paths (and the statics be deleted), or should the statics be
   retained as gib-chunk sources under a new `/Game/Enemies/XCOM/Gibs/` path? This needs a decision
   before import, and it touches `Content/`, which this session does not own.

---

> Psalm 33:6 (ESV) - "By the word of the LORD were the heavens made; and all the host of them by the
> breath of his mouth." Chosen because a rig is a skeleton for a body that already existed in 1994 —
> this pass builds the bones under the creature the roster already named, and adds nothing to it.
