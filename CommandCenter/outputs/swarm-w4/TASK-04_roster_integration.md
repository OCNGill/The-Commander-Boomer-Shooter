# TASK-04 — X-COM Enemy Roster Integration vs `weapons_enemies_v1.json`

- **Slot:** swarm-w4 (W4 / "main-b" lane per `CommandCenter/SWARM_LAUNCH_PACKETS.md`)
- **Model:** minimax/minimax-m3.1-flash:free
- **Start:** 2026-10-21T03:00:16-04:00
- **Artifact:** `CommandCenter/outputs/swarm-w4/TASK-04_roster_integration.md`
- **Status:** ANALYSIS ONLY — no source file was edited. `Docs/generated/weapons_enemies_v1.json` was read, never written.

---

## 0. What was read (evidence)

| Path | Used for |
|---|---|
| `Docs/generated/weapons_enemies_v1.json` | **the roster under integration** — 6 weapons (`w_01`…`w_06`), 6 enemies (`e_01`…`e_06`) |
| `CommandCenter/briefs/XCOM_ENEMY_DESIGN_BRIEF.md` | X-COM roster + 1994 roles, materials, build output |
| `CommandCenter/briefs/XCOM_ENEMY_V2_FIXLIST.md` | v2 acceptance criteria, material families |
| `Tools/blender/out_xcom/xcom_manifest.json` | current (v3) mesh truth: tris, heights, `has_weapon`, `has_ground_contact` |
| `Docs/generated/xcom_ue_import_report.md` | UE import truth for `/Game/Enemies/XCOM/` |
| `Docs/generated/weapon_stats_table.md` | HP / TTK / ammo economy (the only place enemy HP exists) |
| `Docs/generated/level1_bible.md`, `level_stats.json`, `level_transforms.json` | encounter slots, placement roles |
| `Docs/generated/sound_design_list.md` | enemy audio rows keyed by the old names |
| `Docs/generated/blueprint_build_spec.md` | `BP_Enemy` + `BP_LobsterBrute` (§4) |
| `Tools/python/populate_encounters.py` | spawn script: mesh paths, labels, `target_height()` |
| `Docs/DESIGN.md` | hard locks (no hitscan feel-weapons, telegraphed enemy projectiles, pickups-only health) |

### 0.1 The roster under integration — verbatim

`Docs/generated/weapons_enemies_v1.json` → `enemies[]`, 6 entries. Field set is exactly
`id, name, plymouth_theme, attack_telegraph, gib_style, aggression` — **there is no `hp`,
no `weapon`, no `speed`, no `mesh`, no `boss` field.** HP lives in a *different* file
(`weapon_stats_table.md`, §3 "Base HP Values"), and mesh/level wiring lives in a *third*
(`populate_encounters.py` + `Content/Weapons/E_*.uasset`).

| id | name | plymouth_theme | attack_telegraph | gib_style | aggression |
|---|---|---|---|---|---|
| `e_01` | Barnacle Drone | Waterfront | "Red light pulse before spit attack" | "Spray of barnacles and circuitry" | Medium |
| `e_02` | Pilgrim Zealot | Pilgrim | "Raises musket, slow wind-up" | "Feathers and red ruffs exploding outward" | High |
| `e_03` | Mayflower Phantom | Mayflower | "Sails glow blue, materializes from fog" | "Dissolves into sea mist and wood splinters" | Low |
| `e_04` | Lobster Brute | Lobster | "Claws charge with static, loud crack" | "Shell fragments and internal organs fly" | Very High |
| `e_05` | Rock Golem | Plymouth Rock | "Cracks glow orange, stomps ground" | "Shatters into jagged granite pieces" | High |
| `e_06` | Nor-Easter Titan | Nor-easter Storm | "Sky darkens, lightning strikes before charge" | "Disintegrates into rain and wind" | Extreme |

Weapons (`weapons[]`, 6 entries, field set `id, name, archetype, projectile_speed_uu_s,
damage, special, pickup_line, kill_one_liner`):

| id | name | archetype | projectile_speed_uu_s | damage | special |
|---|---|---|---|---|---|
| `w_01` | Pilgrim Puckle | Sidearm | 3000 | 15 | "Infinite ammo, rapid fire" |
| `w_02` | Lobster Claw SMG | SMG | 3200 | 22 | "Splitting shells on impact" |
| `w_03` | Mayflower Cannon | Shotgun | 3500 | 45 | "Pellet spread ignites targets" |
| `w_04` | Nor-Easter Rail | Railgun | 3800 | 80 | "Pierces all cover, chain lightning" |
| `w_05` | Plymouth Rock Launcher | Grenade Launcher | 4000 | 120 | "Bouncing explosive rocks" |
| `w_06` | Harbor Wreck Rocket | Rocket | 4500 | 200 | "Homing, massive blast radius" |

### 0.2 The five X-COM originals to integrate (from the brief + current mesh manifest)

Brief `XCOM_ENEMY_DESIGN_BRIEF.md` "ROSTER (base pass - 5 built)": Sectoid (psychic
infiltrator), Viper (the marquee alien, plasma rifle), Floater (psychic hover, mind
control), Muton (armored heavy, terror-showstopper), Chryssalid (terror from the deep,
skitters). Second wave, **not modeled**: Ethereal, Borg, Dreadnought, Celestial, Chosen,
Retinoid.

Current `Tools/blender/out_xcom/xcom_manifest.json` (v3, working tree):

| Enemy | tris | height_m | width_m | has_weapon | has_ground_contact |
|---|---|---|---|---|---|
| XCOM_Sectoid | 5636 | 1.44 | 0.46 | false | true |
| XCOM_Viper | 5764 | 2.06 | 0.64 | true | true |
| XCOM_Floater | 2732 | 0.33 | 2.48 | false | **false** |
| XCOM_Muton | 5216 | 2.07 | 1.15 | true | true |
| XCOM_Chryssalid | 6252 | 1.03 | 0.82 | false | true |

---

## 1. Recommended mapping (X-COM five → the six roster slots)

**Headline:** the six existing entries are **Plymouth-themed eldritch creatures, not X-COM
aliens at all**. Under the hard lock *"Original X-COM enemies only (Sectoid, Viper, Floater,
Muton, Chryssalid + bosses) — modernized, not re-invented"*, all six names must be
replaced. The `id` spine `e_01`…`e_06` should be **kept** (it is the join key to the level
map and to every downstream table) and the `name`/`plymouth_theme`/`attack_telegraph`/
`gib_style`/`aggression` payloads re-authored for the aliens.

| id | current name | **mapped X-COM** | 1994 role | proposed aggression | rationale / mapping fit |
|---|---|---|---|---|---|
| `e_01` | Barnacle Drone | **XCOM_Sectoid** | psychic infiltrator | Medium | Sectoids are numerous and frail; the 3-spawn "trash mob" budget (`ENC_Drone_01/02/03`) maps to Sectoid packs. |
| `e_02` | Pilgrim Zealot | **XCOM_Viper** | the marquee alien, plasma rifle | High | Both are the mid-tier **ranged shooter**; `has_weapon: true` on Viper fits the Zealot's musket slot and the 2-spawn budget (`ENC_Zealot_01/02`). |
| `e_03` | Mayflower Phantom | **XCOM_Floater** | psychic hover, mind control | Low | Both are the **ethereal / "materializes out of nowhere"** encounter; `has_ground_contact: false` on the Floater matches a non-walking presence near the drop zone (`ENC_Phantom_01`, `in_immediate_drop_sight: true`). |
| `e_04` | Lobster Brute | **XCOM_Chryssalid** | terror from the deep, skitters | Very High | Both are the **melee lunger** guarding the risk pocket (`ENC_Brute_Pit`); scythe forelimbs replace the claws. See note (b) below. |
| `e_05` | Rock Golem | **XCOM_Muton** | armored heavy, terror-showstopper | High | Both are the **armored heavy** (`ENC_Golem_Platform`). Strongest visual match (oxblood chest plate vs granite mass) but weakest *role* match — see conflict **C-09**. |
| `e_06` | Nor-Easter Titan | **UNFILLED — boss slot** | (Ethereal / Celestial / Dreadnought) | Extreme | The five built X-COM enemies are **all non-boss** in 1994 canon. The slot must stay reserved. See conflict **C-03**. |

Notes:
- **(a) Alternate swap to consider:** `e_01` ↔ `e_04` (Chryssalid into the 3-spawn trash
  slot, Sectoid into the pit-guardian slot). **Rejected:** a Sectoid as the 450-HP
  pocket guardian reads as a weak tank. Keep the primary mapping.
- **(b)** Chryssalid is the *fast* one, Brute was the *heavy* one — the HP tier is
  re-assigned, see §2.
- **(c)** Keep `e_06` open rather than filling it with a non-X-COM boss. A Plymouth Titan
  next to five aliens breaks the lock; promoting Muton to boss breaks 1994 canon (Muton is
  a terror-showstopper, Celestial is the boss) and empties the heavy slot.

---

## 2. Proposed stat re-authoring (values are PROPOSED — not written to any file)

The JSON carries no HP. The only enemy HP in the project is
`Docs/generated/weapon_stats_table.md` §3 ("Base HP Values (Neutral Difficulty)"):
Barnacle Drone 36, Pilgrim Zealot 120, Mayflower Phantom 200, Lobster Brute 450,
Rock Golem 600, Nor-Easter Titan 2000. The X-COM five therefore need their HP written
into that table (and only there), plus the roster's `attack_telegraph` / `gib_style`
strings rewritten — see conflicts **C-07** and **C-11**.

| id | X-COM | proposed HP | proposed attack_telegraph (alien) | proposed gib_style (alien) | proposed aggression |
|---|---|---|---|---|---|
| `e_01` | Sectoid | 40 | "Cranium flares violet, thin psychic whine" | "Bone dust and violet ichor" | Medium |
| `e_02` | Viper | 120 | "Plasma pistol coil overcharges, violet flare" | "Chitin shards and plasma scorch" | High |
| `e_03` | Floater | 90 | "Dorsal core blooms, hover lock tone" | "Manta cartilage and vapor bloom" | Low |
| `e_04` | Chryssalid | 60 | "Scythe forelimbs rise, venom sac glows" | "Shell shards and burning venom" | Very High |
| `e_05` | Muton | 450 | "Heavy rifle spins up, visor slit reddens" | "Armor plate, bolts and dark blood" | High |
| `e_06` | (boss TBD) | TBD | TBD | TBD | Extreme |

HP caveat: these tiers are **not final** while conflict **C-07** is open, because the
player's damage numbers are themselves ambiguous between `weapons_enemies_v1.json` and
`weapon_stats_table.md`. Fix C-07 first, then re-derive TTK against the boss slot.

Placement mapping (for whoever re-wires `populate_encounters.py`):

| current label | current mesh | proposed mesh | proposed label |
|---|---|---|---|
| `ENC_Drone_01/02/03` | `/Game/Weapons/E_BarnacleDrone` | `/Game/Enemies/XCOM/XCOM_Sectoid` | `ENC_Sectoid_01/02/03` |
| `ENC_Zealot_01/02` | `/Game/Weapons/E_PilgrimZealot` | `/Game/Enemies/XCOM/XCOM_Viper` | `ENC_Viper_01/02` |
| `ENC_Phantom_01` | `/Game/Weapons/E_MayflowerPhantom` | `/Game/Enemies/XCOM/XCOM_Floater` | `ENC_Floater_01` |
| `ENC_Brute_Pit` | `/Game/Weapons/E_LobsterBrute` | `/Game/Enemies/XCOM/XCOM_Chryssalid` | `ENC_Chryssalid_Pit` |
| `ENC_Golem_Platform` | `/Game/Weapons/E_RockGolem` | `/Game/Enemies/XCOM/XCOM_Muton` | `ENC_Muton_Platform` |
| `ENC_Boss_NorEaster` | `/Game/Weapons/E_NorEasterTitan` | **none yet** | `ENC_Boss_TBD` |

---

## 3. Conflict register

Severity: **CRITICAL** = blocks the roster swap; **HIGH** = forces a rewrite of a second
file; **MEDIUM** = will surface as a bug at implementation; **LOW** = bookkeeping/ruling.

### C-01 — CRITICAL — All six roster entries violate the "original X-COM enemies only" lock

`"name": "Barnacle Drone"` … `"Nor-Easter Titan"` are Plymouth MA eldritch creatures
(`"plymouth_theme": "Waterfront" | "Pilgrim" | "Mayflower" | "Lobster" | "Plymouth Rock" |
"Nor-easter Storm"`). The lock reads *"Original X-COM enemies only (Sectoid, Viper,
Floater, Muton, Chryssalid + bosses) — modernized, not re-invented."* Zero of six entries
satisfy it. **Every one of the six names must change.** This is not a patch — it is a
roster replacement. Flagging, not editing.

### C-02 — CRITICAL — Five X-COM enemies have no roster entry; six old entries become surplus

The `enemies[]` array has no Sectoid, Viper, Floater, Muton or Chryssalid. The X-COM
pass and the JSON roster are **disjoint sets** — there is no overlap to reconcile, only to
replace. Count: 5 in, 6 out → **1 slot surplus**, which is precisely the boss slot
(C-03).

### C-03 — CRITICAL — The boss slot has no X-COM occupant

`e_06` Nor-Easter Titan is the level-1 boss (`level1_bible.md` beat 6: *"Boss: Nor-Easter
Titan"*, `weapon_stats_table.md`: 2000 HP, 2 phases, shield regen). None of the five built
enemies is a 1994 boss; the bosses (Ethereal, Celestial, Dreadnought) are listed in the
brief under *"Second wave (not yet modeled)"*. **Missing entry.** Options: (a) leave
`e_06` empty and model Ethereal/Celestial next; (b) keep the Titan — breaks the lock;
(c) promote Muton — breaks canon *and* empties `e_05`. **Recommended: (a).**

### C-04 — HIGH — Naming mismatch breaks every downstream consumer keyed on the old names

Renaming is not confined to the JSON. These all key on the six current names and must be
re-authored in the same change:

- `Docs/generated/sound_design_list.md` §2 "Enemy Vocal/Aggro Telegraph Table" — 6 rows
  (`Barnacle Drone` … `Nor-Easter Titan`) and 6 SFX folder names
  (`ENM_BarnacleDrone/` … `ENM_NorEasterTitan/`), each with Idle / Telegraph / Attack /
  Death / Gib variants.
- `Docs/generated/level1_bible.md` §2 "Enemy Placement Logic" — placement reasoning is
  written against *"Rock Golem (NE Platform/Rock Ramp)"*, *"Lobster Brute (SW Hazard Pit)"*.
- `Tools/python/populate_encounters.py` `ENCOUNTERS` — 9 tuples keyed
  `'/Game/Weapons/E_BarnacleDrone'` … `'/Game/Weapons/E_NorEasterTitan'`, and labels
  `ENC_Drone_01` … `ENC_Boss_NorEaster`.
- `Content/Weapons/E_BarnacleDrone.uasset` … `E_NorEasterTitan.uasset` — 6 committed
  proxy meshes that become orphans.
- `Content/Maps/M_Blockout01.umap` — 9 actors labelled `ENC_Drone_01` …
  `ENC_Boss_NorEaster` (see `level_transforms.json`).
- `Docs/generated/level_stats.json` — encounter list keyed by the same 9 labels.

### C-05 — HIGH — Duplicate roles across the two sets

Every X-COM enemy has a *functional twin* in the current Plymouth roster, which is why
"just add the aliens" fails:

| X-COM | existing twin | shared role | resolution |
|---|---|---|---|
| Viper | `e_02` Pilgrim Zealot | mid-tier ranged shooter | **merge** — Viper replaces the Zealot |
| Muton | `e_04` Lobster Brute / `e_05` Rock Golem | armored heavy / terrace blocker | **merge** — Muton replaces the Golem, Brute slot becomes Chryssalid |
| Floater | `e_03` Mayflower Phantom | ethereal, "materializes from fog" | **merge** — Floater replaces the Phantom |
| Sectoid | `e_01` Barnacle Drone | numerous trash mob | **merge** — Sectoid replaces the Drone |
| Chryssalid | *none* | fast melee stalker | **no twin** — genuinely new; takes the Brute slot |
| (boss) | `e_06` Nor-Easter Titan | boss | **no twin** — see C-03 |

### C-06 — HIGH — Schema gap: the roster cannot express what the X-COM set needs

`enemies[]` fields are exactly `id, name, plymouth_theme, attack_telegraph, gib_style,
aggression`. The X-COM five need at minimum:

1. **HP** — absent. Lives in `weapon_stats_table.md` §3 instead (split source of truth).
2. **Enemy weapon** — absent, but `xcom_manifest.json` says Viper and Muton have
   `has_weapon: true` (plasma pistol / heavy plasma rifle). The roster cannot say so.
3. **Hover / no ground contact** — absent; Floater is `has_ground_contact: false`.
4. **Mesh path** — absent; the only link is the `ENCOUNTERS` table in a Python script.
5. **Boss flag / phases** — absent; the boss's two phases and 10 HP/s shield regen are
   prose in `weapon_stats_table.md`.
6. **`plymouth_theme`** — a field literally named for the Plymouth theme. There is no
   honest alien value for it (see C-12).

### C-07 — HIGH — Weapon-side stat mismatch between the two "authoritative" files

The roster's own `weapons[]` disagrees with `weapon_stats_table.md` §1 on names and
damage, and `sound_design_list.md` §1 introduces a *third* naming set:

| slot | `weapons_enemies_v1.json` | `weapon_stats_table.md` | `sound_design_list.md` |
|---|---|---|---|
| 1 | Pilgrim Puckle — `damage: 15`, `projectile_speed_uu_s: 3000` | Pilgrim Puckle — **12**, **Hitscan / ∞** | Pilgrim Puckle |
| 2 | Lobster Claw SMG — **22** | **Sextant Scattergun** — 14, Hitscan / ∞ | **Dockside Dynamite** |
| 3 | Mayflower Cannon — **45**, 3500 | Mayflower Cannon — **250**, 4000 | Mayflower Cannon |
| 4 | Nor-Easter Rail — **80**, 3800 | **Rockhopper Rail** — **85**, 5000 | **Gulper's Gnawer** |
| 5 | Plymouth Rock Launcher — 120, 4000 | **Barnacle Blunderbuss** — 22, 3000 | **Titan's Anchor** |
| 6 | Harbor Wreck Rocket — **200**, 4500 | Harbor Wreck Rocket — **120**, 3500 | Harbor Wreck Rocket |

Only 3 of 6 names agree across all three documents. Damage disagrees on 4 of 6. This
matters for roster integration because enemy HP/TTK is expressed *against player
weapons* — every HP number in §2 above inherits this ambiguity until one file is
declared canonical. **Recommendation: declare `weapon_stats_table.md` canonical (it is
the only one with fire rates, ammo economy and a TTK table) and re-stamp
`weapons_enemies_v1.json`'s `weapons[]` from it — then re-derive §2 HP.**

Note also: `weapon_stats_table.md` marks Pilgrim Puckle and Sextant Scattergun as
**Hitscan / ∞**, while `weapons_enemies_v1.json` gives Pilgrim Puckle
`"projectile_speed_uu_s": 3000` and `Docs/DESIGN.md` states *"NO hitscan for the player's
'feel' weapons (projectile speeds high)"*. That contradiction is pre-existing and
independent of this pass, but it must be settled before any enemy TTK is signed off.

### C-08 — HIGH — The UE assets the roster would bind to are two rebuilds stale

- `Docs/generated/xcom_ue_import_report.md` records the import of the **v1** FBX:
  tris 2864 / 3712 / 1980 / 2520 / 2536; UE heights 197.0 / 198.5 / 114.37 / 202.0 /
  93.66 cm; its own cross-check table lists manifest heights 1.95 / 2.10 / 1.85 / 2.05 /
  1.35 m. Files: `Content/Enemies/XCOM/XCOM_*.uasset`, mtime 2026-10-21 01:13.
- The **current** `Tools/blender/out_xcom/xcom_manifest.json` (working tree, v3) says
  tris 5636 / 5764 / 2732 / 5216 / 6252 and heights 1.44 / 2.06 / **0.33** / 2.07 / 1.03 m.
  FBX mtimes 03:00–03:03.

Those are two different geometries. The Floater differs by ~3.5× in height (114.37 cm vs
33 cm — v1 was a standing biped, v3 is a flat manta). **Binding the roster to
`/Game/Enemies/XCOM/` today binds it to geometry Ebert already rejected (3.33/7.0).**
The import must be re-run from the current FBX before any roster wiring.

### C-09 — MEDIUM — The Muton cannot perform the Rock Golem's level role

`level1_bible.md` places the Rock Golem as *"a static obstacle and early verticality
gate… Forces player to approach from the side or jump over"* on the NE platform. The
Muton is a mobile heavy shooter (`has_weapon: true`, heavy plasma rifle). Mapping Muton
onto `e_05` **keeps the silhouette but breaks the level design**: a static blocker becomes
a patrolling heavy that shoots. `level1_bible.md` §4 "Key Traversal Paths" path 2
("Pillar to NE Platform … Rock Golem blocks direct jump") and
`level_stats.json` `blocked_cells: 300` both assume a hard blocker. **Recommendation:
either build the Muton as a stationary garrison (no pathing, anchored to the platform) or
move the verticality gate to level geometry and free the Muton to roam.**

### C-10 — MEDIUM — Aggression ladder collision

The JSON uses five values: `Low, Medium, High, Very High, Extreme` — `Extreme` is
currently occupied *only* by the Titan. The five X-COM enemies need five values **plus**
the boss's `Extreme`, i.e. six values from a five-value scale, with the boss holding
`Extreme`. Concretely: Chryssalid (relentless, in 1994 it never stops) and Muton (terror
showstopper) both want the top of the ladder, and the original Floater — which in 1994
**panicked and retreated** when hurt — has no value below `Low` to express that. Either
add a `Very Low` tier, or accept that "Low" now means "Floater retreats".

### C-11 — MEDIUM — `attack_telegraph` and `gib_style` strings are Plymouth props and cannot be edited into alien ones

Current values: *"Raises musket, slow wind-up"*, *"Claws charge with static, loud crack"*,
*"Cracks glow orange, stomps ground"*, *"Dissolves into sea mist and wood splinters"*,
*"Feathers and red ruffs exploding outward"*. These reference Plymouth props (musket,
claws, rock, sails, feathers). Rewriting them to *"Plasma pistol coil overcharges"* etc.
is a **wholesale replacement of all 12 strings**, not a tweak — and any half-measure
would leave a musket-wielding alien in the roster. §2 proposes replacements for all of
them.

### C-12 — MEDIUM — `plymouth_theme` is a field that has no honest value for an alien

The key is literally `plymouth_theme` and its six values are all Plymouth settings.
There is no "Alien" value. Options: (a) re-purpose the key to a neutral `theme` with
values like `"X-COM / Deep Space"` — a **schema change** that any consumer reading
`plymouth_theme` must be updated for; (b) keep the key and set it to the *encounter
setting* instead (e.g. Floater → "Harbor", Viper → "Dry Dock"), which preserves the
field's meaning for the level designer while the enemy itself is alien. **(b) is
recommended** — it keeps the field useful for level dressing without renaming keys, but
it needs a one-line definition change so nobody reads `plymouth_theme` as "what creature
this is".

### C-13 — MEDIUM — Blueprint coverage: one generic enemy BP for five distinct alien behaviours

`blueprint_build_spec.md` §4 defines `BP_Enemy` (generic: Idle → Telegraph → Attack →
Dead, Sight 2000, FOV 120, 0.5 s telegraph timer, `BP_GibChunk` ×12 with radial impulse
5000 / radius 500) and exactly **one** child, `BP_LobsterBrute` (Damage 50, GibCount 15,
Telegraph 0.8 s, melee < 200 uu). The X-COM five need five children with genuinely
different behaviour: hover (Floater — no ground contact), psi (Sectoid), scythe melee
(Chryssalid), heavy rifle at range (Muton), plasma pistol (Viper). **A single generic BP
cannot express a hovering enemy.** This is blueprint work outside this artifact's scope
but it is on the critical path for the roster swap.

### C-14 — MEDIUM — Three of the five aliens lose their defining mechanic because the player is out of scope

The player character is explicitly **not in scope** for this pass. That removes the
signature mechanic of three X-COM enemies: Sectoid's psychic attack, Floater's mind
control, and Chryssalid's player-conversion (turning a human into a Chryssalid). Without
them, Sectoid/Floater/Chryssalid collapse toward generic shooters — exactly the "generic
biped" failure Ebert already flagged on the v1 kit. Mitigation to carry into the player
pass: implement them now as damage-plus-telegraph only, and record the three deferred
mechanics explicitly rather than silently dropping them.

### C-15 — LOW — Zero-reload lock reaches enemy weapons; the roster has no field for it

The lock is *"Zero reload animations (weapons contract) — applies to enemy weapons too."*
Viper and Muton carry weapons (`has_weapon: true`). A plasma rifle with finite ammo
would need a reload — forbidden. The roster has no ammo/ammo-type field, so the safe
reading must be recorded explicitly: **enemy plasma weapons are infinite-ammo with a
cooldown**, never a reload animation, never an ammo pickup prompt. The player's
side is already unambiguous (`w_01` special: `"Infinite ammo, rapid fire"`; the stats
table note: *"All weapons use instant hold-to-refire. No reload mechanic."*).

### C-16 — LOW — Level-data drift found while mapping (adjacent to the roster)

- `level_stats.json` places `ENC_Brute_Pit` at `z: 50` with
  `"access": "drop-in over the 0.25m rim"`, while `level_transforms.json` lists the same
  label at `z: -100.0`; and the same file's own findings say the rim is **0.50 m**,
  not 0.25 m. The Chryssalid that replaces the Brute inherits a 0.5–1.5 m ambiguity about
  where it stands.
- All 9 encounters carry `"access": "walk"`. A hovering Floater (`has_ground_contact:
  false`) does not walk — the traversal/verification model needs a hover case.
- `sound_design_list.md` §1 contains a stray `<think>\n\n</think>` block inside the
  `AMB_` folder listing.

### C-17 — LOW — Boss shield regen vs the "no regeneration" lock needs a ruling

`weapon_stats_table.md`: *"Phase 2 … shield regenerates 10 HP/s if not hit."*
`Docs/DESIGN.md` locks *"Health: Classic pickups only. No regeneration."* If the lock is
player-scoped, the boss shield is fine; if it is global, the boss must be re-specified.
**Ruling needed from the Commander** — it changes what a future Ethereal/Celestial boss
is allowed to do. (This task does not assume either reading.)

---

## 4. Integration order (dependency chain for whoever executes)

1. **Re-import the current FBX** into `/Game/Enemies/XCOM/` (fixes **C-08**) — the roster
   must not bind to v1 geometry.
2. **Settle C-07** (which weapon table is canonical) and **C-17** (regen ruling).
3. **Rewrite `weapons_enemies_v1.json` `enemies[]`** with the §1 names/roles and §2
   telegraphs/gibs — and, if C-12 option (b) is taken, redefine `plymouth_theme` as the
   encounter setting. Add the missing fields the X-COM set needs (**C-06**): at minimum
   `hp`, `weapon`, `hover`, `mesh`, and a `boss` flag for `e_06`.
4. **Rewrite `weapon_stats_table.md` §3** HP rows for the five X-COM enemies; leave
   `e_06` as a placeholder boss row until the boss is modeled.
5. **Re-author `sound_design_list.md` §2** (6 enemy rows + 6 `ENM_*` folder names) and
   **`level1_bible.md` §2** placement prose for the new names.
6. **Re-wire `populate_encounters.py`**: `ENCOUNTERS` mesh paths → `/Game/Enemies/XCOM/…`,
   labels → `ENC_Sectoid_*` / `ENC_Viper_*` / `ENC_Floater_*` / `ENC_Chryssalid_Pit` /
   `ENC_Muton_Platform` / `ENC_Boss_TBD`, **and** rewrite `target_height()` — it
   normalises by label prefix (`ENC_NorEaster` 300 uu, `ENC_Brute` 160, `ENC_Golem` 150,
   `ENC_Drone` 60, fallback `ENC_` 180), numbers tuned for the primitive proxies, not for
   aliens authored at 1.44 / 2.06 / 0.33 / 2.07 / 1.03 m. Naively re-pointing the meshes
   would scale a 2.06 m Viper to 1.8 m and a 1.44 m Sectoid to 1.8 m.
7. **Re-place the 9 map actors** in `Content/Maps/M_Blockout01.umap` (labels only; the
   positions and the `E_*` proxy meshes are unaffected by naming).
8. **Build the five enemy Blueprints** (C-13) before the boss pass.

---

## 5. Open decisions for the Commander

| # | Decision | Default if no ruling |
|---|---|---|
| D-1 | Which file is canonical for player weapon stats? (**C-07**) | `weapon_stats_table.md` (only source with fire rates + TTK) |
| D-2 | Boss slot: model Ethereal/Celestial, or keep the Titan? (**C-03**) | Leave `e_06` empty and reserved |
| D-3 | `plymouth_theme`: keep the key as encounter setting, or rename to `theme`? (**C-12**) | Keep the key, redefine as encounter setting |
| D-4 | Is the "no regeneration" lock player-scoped? (**C-17**) | Player-scoped (boss shield regen allowed) |
| D-5 | Muton: static garrison on the NE platform, or roaming heavy? (**C-09**) | Static garrison (preserves the verticality gate) |
| D-6 | Add a `Very Low` aggression tier for the retreating Floater? (**C-10**) | No new tier; "Low" covers it |

---

## 6. Boundary statement

- **Files written by this task:** `CommandCenter/outputs/swarm-w4/CLAIM_TASK-04.md`,
  `CommandCenter/outputs/swarm-w4/TASK-04_roster_integration.md`,
  `CommandCenter/outputs/swarm-w4/LEDGER_LINE.md`. Nothing else.
- **Files read but NOT modified:** `Docs/generated/weapons_enemies_v1.json`,
  `Docs/DESIGN.md`, `The_Commander_Boomer_Shooter.md`, `conductor/**`,
  `CommandCenter/outputs/LEDGER.md`, `Tools/blender/**`, `Content/**`,
  `Docs/generated/blueprint_build_spec.md`, `Docs/generated/level1_bible.md`,
  `Docs/generated/level_stats.json`, `Docs/generated/level_transforms.json`,
  `Docs/generated/sound_design_list.md`, `Docs/generated/weapon_stats_table.md`,
  `Docs/generated/xcom_ue_import_report.md`, `Tools/python/populate_encounters.py`,
  `CommandCenter/briefs/XCOM_ENEMY_DESIGN_BRIEF.md`,
  `CommandCenter/briefs/XCOM_ENEMY_V2_FIXLIST.md`.
- **No roster entry was invented.** Every `id`, `name`, `plymouth_theme`,
  `attack_telegraph`, `gib_style`, `aggression`, `projectile_speed_uu_s` and `damage`
  quoted above is verbatim from `Docs/generated/weapons_enemies_v1.json`; every mesh
  number is verbatim from `Tools/blender/out_xcom/xcom_manifest.json` or
  `Docs/generated/xcom_ue_import_report.md`. Proposed values are labelled PROPOSED and
  live only in §2 of this document.
