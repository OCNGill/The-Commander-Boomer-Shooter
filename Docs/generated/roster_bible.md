# The Commander Boomer Shooter — Roster, Story, Art Direction & Boss Bible

**Version:** 1.0 · **Date:** 2026-10-21 · **Owner:** Hermes (design lane)
**Machine-readable companion:** `Docs/generated/roster_bible.json` — every number in this
document is defined there and read verbatim by the Rust runtime. Where this prose and the JSON
disagree, **the JSON is correct and this document is stale** (and must be fixed, not the JSON).
**Scored by:** Ebert, `Agents/Ebert/designs/zero_trust_likert_rubric.md` v1.0 — bar **6.2/7.0**,
no rounding, any axis at 1.0 = automatic fail, **screenshots are mandatory evidence**.

---

## 0. How this document is judged, and what that changes about how it is written

Ebert's rubric is not a vibe check. Three of its properties dictate the shape of everything below:

1. **Evidence or nothing.** "Submitting fewer than the required screenshots yields INCOMPLETE —
   no score is issued until the evidence exists." Every entity in this bible therefore carries a
   **photograph plan** (§7) naming the exact renders that must exist before it can be scored. A
   spec for a thing nobody can photograph is a spec for a thing that will fail the Clarity axis.
2. **Truthfulness is 20% and a fabricated number sets the axis to 1.0.** So every number in this
   document is either (a) **measured** from a file in the repo, (b) **specified as a target** and
   labelled as such, or (c) **absent**. There is no third category. Where a value is a design
   target rather than a measurement, it says so in the same sentence.
3. **Visual Craft is 25% and Clarity is 20%** — 45% of the weight is on whether the thing reads
   and looks good. Hence the hard silhouette rule in §4: *every* entity is specified first as a
   black shape against a background, because that is the cheapest way to guarantee both axes and
   the only thing Ebert's v1 report actually complained about (five generic bipedal robots wearing
   five different names — 3.0 on both Clarity and Truthfulness).

**What this document is not.** It is not the build. It is the contract the build is measured
against. It does not claim the game exists, and it does not claim any render that has not been
produced has been produced.

---

## 1. The game in one paragraph

*The Commander Boomer Shooter* is a fast retro FPS set in **Plymouth, Massachusetts, 1926** — a
harbour town being eaten by something that came over the water. You are the last officer of a
coastal artillery battery that was left running when the town evacuated. The battery's guns
still work. The things in the fog are **X-COM aliens** (1994's *UFO: Enemy Unknown* roster,
rebuilt in true 3D) that have been here longer than anyone thought, and the reason they never
leave is that the harbour is their **larder**. You are not here to win a war. You are here to
find the keycard, climb the pillar, and get out before the tide comes in.

**Design pillars, in priority order** (from `Docs/DESIGN.md`, locked):

| Pillar | Concrete rule | Where it lives in this bible |
|---|---|---|
| Speed is the fantasy | ≥600 uu/s base, raw unsmoothed mouse, 1.2 s dash at 1.5× | §3, `roster_bible.json → global_rules` |
| Guns are overpowered | No reloads, ever. Instant switching. Every gun overpowered. | §6, §11 (taunt contract) |
| Enemies telegraph | Every attack has a visible + audible pre-roll. No hitscan for the player's feel-weapons. | §5, per-entity `attack.telegraph_s` |
| No RPG, no stamina, no cover mechanic | Cover is geometry. Health is pickups only. | §3, §6 |
| Every kill is loud | Screen shake, blood, gibs, one-liner | §6, `global_rules.one_liners` |

**What this game is NOT:** not a tactics game, not a survival-horror game, not a roguelite, not a
X-COM tactics remake. The X-COM material is the **monster set**, not the system. We stole the
silhouettes and the terror reveal; we did not steal the isometric grid or the soldier roster.

---

## 2. Story

### 2.1 Premise

**Plymouth, Massachusetts. November 1926.**

The town evacuated eight days ago. Not in a panic — in a **schedule**. Buses at 04:00, boats
leaving the pier at 06:00, the last of it gone by noon. The official line, from a pamphlet left
on a car windscreen, is that the **harbour lights went bad** and the fog came in wrong.

The fog came in wrong because something came in with it.

You are the **Battery Commander**. The Plymouth coastal artillery battery — four 12-inch guns
on the north point, built to kill things that came out of the sea — was never decommissioned,
because the guns are cheaper to keep than to replace, and because *you* are still here. The
battery has no crew. You have the guns, a telephone, and a bay of shells.

On the fourth night the telephone rings. It is not a voice. It is a **sound**: a wet, cheerful
clicking, like a barnacle opening and closing on a hull plate, playing in a rhythm that is
almost speech. Then it stops, and the fog thins, and you can see the pier is **full of things**.

They are not ghosts and they are not a navy. They are the crew of a **salvage operation** that
has been running for a very long time, and the "town" is not a town — it is a **crane yard**.
Every building is a container. Every container has a shipping label. The aliens on the pier are
**not invading**; they are **loading**.

### 2.2 The three-act structure

| Act | Level | Beat | The turn |
|---|---|---|---|
| **I — THE BATTERY** | `M_Blockout01` "Plymouth Dark" | Player enters from the south, crosses the arena, climbs the pillar to the green keycard, drops into the pit for the red one | The player learns the fog lies: the way *out* is through the thing that looks like a wall |
| **II — THE YARD** | `M_Yard02` (unbuilt) | The crane yard: a maze of stacked containers, the loading gantry overhead, the aliens working | The player learns the aliens are **workers**, and the boss is **management** |
| **III — THE ROLL** | `M_Harbor03` (unbuilt) | The **Harvester** arrives — a boss that eats the arena | The player learns it is not here to conquer; it is here to **collect**, and the level is a shipping manifest |

### 2.3 The antagonist

**The Harvester** is a *Lattice*-class organism: a thing that eats structures the way a bulldozer
eats a fence, converting them into **spore-mass** it can carry. It is not malicious and it is not
a general. It is **logistics**. It came here because Plymouth was on a manifest.

Its signature behaviour — the thing that makes it a boss and not a big enemy — is that it
**eats the arena while you fight it**. It is Pac-Man's mouth with Sonic's legs. It is the only
enemy in the game that changes the level geometry.

And it **talks**. Through the battery's telephone, and through the fog itself, it speaks in the
cheerful half-finished fragments of a thing that learned language from shipping manifests
(§11). It is not taunting you. It is **filling in a form**.

### 2.4 Tone rules (binding on all writers)

- **Military maritime, not sci-fi military.** The vocabulary is *harbour*: pier, yawl, foghorn,
  quay, gantry, bilge, manifest, tide table, breezeguard. No "energy", no "plasma containment",
  no "tactical insertion". The aliens get to be alien; **the humans get to be 1926 dockworkers
  and coast artillerymen**.
- **The horror is administrative.** The scariest thing in this game is a manifest with the
  Commander's name on it. Creatures are frightening because they are *indifferent*, not because
  they are fierce.
- **Gallows in the one-liners, never in the world.** The HUD quips ("Noobs Detected", "Commander
  STOMPED") are the game's comic register; the level itself is straight. Do not write jokes into
  signage.
- **The Council is absent.** In 1994 X-COM you had a Council funding you and a monthly report to
  file. Here there is no Council. There is a battery, a phone, and no answer from anyone. This is
  what makes the X-COM material land: the roster without the institution.

### 2.5 Named characters

| Name | Role | Where they appear |
|---|---|---|
| **The Commander** (player) | Last officer of the Plymouth battery. Unnamed, unvoiced. | Everywhere |
| **The Voice on the Phone** | The Harvester, as heard. Speaks the insult bank. | Act I (distant, unintelligible), Act III (clear) |
| **"Bell"** | The foghorn. Kills nine men in 1926 by being *on*. The only "character" the player meets who talks back. | Act I, audio only |

---

## 3. Mechanics contract (the non-negotiables)

From `Docs/DESIGN.md` and `Docs/generated/level1_bible.md` §4, restated here because every
entity below assumes them:

| Rule | Value | Notes |
|---|---|---|
| Base movement | **600 uu/s** (15 units/s floor) | Doom 2016, not Doom Eternal |
| Jump | 250 uu | ~2.5 m |
| Double jump | +150 uu | from the "Fog Strider" pickup, Secret 1 |
| Dash | 1.5× for 0.5 s, 1.2 s cooldown | the only i-frame in the game (0.5 s) |
| Wall jump | 1.8× jump height at 45° | |
| Mouse input | raw, no smoothing, no acceleration | |
| Reloads | **none.** No animation, no sound, no delay. | `sound_design_list.md` says "None — instant hold-refire per contract" for all 6 weapons |
| Weapon switching | instant | |
| Health | pickups only, no regen | |
| Stamina | does not exist | |
| Cover | geometry only, never a mechanic | |
| ADS | allowed | |
| Player hitscan | **never** — min projectile speed 3000 uu/s | the "feel" of the gun is the projectile travel |
| Enemy hitscan | permitted for rifle-type enemies (Zealot musket) | telegraphed 1.5 s first |
| Frame rate | 144+ target on dev hardware; **60 FPS locked on Steam Deck 'low'** | |

**The Deck rule.** Every number in this document is chosen so the game runs at 60 FPS on a
Steam Deck at the 'low' preset with a **100 k-triangle visible budget**, **≤2000 draw calls**,
**≤5 dynamic lights per sector**, and **Lumen disabled** (baked + real-time limited). Any entity
whose budget would break that is not shippable, and this document says so at the entity.

---

## 4. The silhouette law

**Rule S1.** Every entity is specified as a **black shape on a grey field** first, and only
then as a lit render. If it does not read as a distinct shape at 40 px tall in pure black, it
does not ship.

**Rule S2.** No two entities in the same encounter share a silhouette family. The kit is
already five bipeds' worth of failure once; the fix is *posture*, not colour. Concretely: at
most **two bipeds**, at most **two quadrupeds**, at most **one hoverer**, and **one boss with
no legs at all** may appear in any single encounter.

**Rule S3.** The accent colour is on **one part** of the body, not the whole body. Ebert's v1
report credited the palette discipline and then punished the "abrupt gray↔green splits that follow
arbitrary intersections rather than structure" — so the accent follows *anatomical* boundaries
(chest plate, visor, core), never a mesh seam.

**Rule S4.** Zero detached geometry. Any floating part in any submitted frame is a defect, and
the kit already failed this once (Sectoid's hand, Muton's white shard, Viper's floating prongs).
This is now a **build-time assertion**, not a review-time catch: the Blender build script must
assert that every mesh part is connected to the body or is a *declared* emissive sub-part.

**Rule S5.** Every entity gets a **contact shadow**. Feet on the floor get a tight dark patch
plus a real cast shadow; hoverers get a body-shaped ellipse and **no** contact at all. A model
with neither is floating in dead space, which is exactly what Ebert saw.

---

## 5. The roster

### 5.1 Two bloodlines, one world

The game carries **two** monster lines and they must not blur into each other:

| Line | Members | Language | Reads as |
|---|---|---|---|
| **X-COM 1994 originals** | Sectoid, Viper, Floater, Muton, Chryssalid | Original *UFO: Enemy Unknown* designs, modernized | Aliens: biomechanical, chitin + plasma, emissive eyes and cores |
| **Plymouth natives** | Barnacle Drone, Pilgrim Zealot, Mayflower Phantom, Lobster Brute, Rock Golem, Nor-Easter Titan | Original designs (1926 maritime + rock + fog) | Working gear of the yard: barnacle, canvas, sail-cloth, shell, granite |

**The naming rule that keeps them apart:** X-COM enemies are named for what they *are*
(Sectoid, Viper, Floater). Plymouth enemies are named for what they are *made of or wear*
(Barnacle, Pilgrim, Mayflower, Lobster, Rock). A player who has never seen the game should be
able to guess which is which from the name alone, and never be wrong.

### 5.2 Full roster

> Numbers below are **measured** from `Tools/blender/out_xcom/xcom_manifest.json` (the five built
> X-COM enemies) or **specified targets** (everything else, labelled `[target]`). HP and damage
> are design values cross-checked against `Docs/generated/weapon_stats_table.md` §3.

#### X-COM 1994 originals

##### SECTOID — *the small one*
| | |
|---|---|
| **Lineage** | 1994 original. Psychic infiltrator. |
| **Height / tris** | 1.39 m · 7,308 tris (measured, v2 mesh) |
| **Silhouette** | Small + gaunt, oversized smooth cranium, symmetric glowing eyes, **no mouth**. Stands 22° forward-pitched, weight on the right leg, hands clasped outboard so the gesture breaks the torso outline. |
| **Reads as** | A praying thing with nothing under the hood. |
| **HP / speed** | 30 · 320 uu/s |
| **Attack** | `psi-lance` — telegraph 1.2 s → 12 dmg projectile at 2,200 uu/s |
| **Budget** | ≤9,000 tris · 1024px · 4 materials · 24 bones · 1 vfx |
| **Signature** | The only creature in the kit with **no mouth at all** and the only one whose eyes are the light source. |

##### VIPER — *the line infantry*
| | |
|---|---|
| **Lineage** | 1994 original. The marquee alien. Plasma rifle. |
| **Height / tris** | 2.06 m · 5,764 tris (measured) |
| **Silhouette** | Tall + narrow reptilian hunter. **45 cm forward-projecting tapered snout** with a plated nasal ridge, six bone teeth in a recessed jaw seam, **raised five-rib dorsal spine**. Plasma pistol held out front. |
| **Reads as** | A hunting dog on two legs, nose down. |
| **HP / speed** | 90 · 300 uu/s |
| **Attack** | `plasma-burst` — telegraph 1.0 s → 3 × 18 dmg at 2,500 uu/s |
| **Budget** | ≤7,500 tris · 1024px · 5 materials · 26 bones · 2 vfx |
| **Signature** | The snout and the rib spine are the two features that make it a Viper **in one glance**. |

##### FLOATER — *the one that flies*
| | |
|---|---|
| **Lineage** | 1994 original. Aerial ambusher. |
| **Height / tris** | 0.29 m body, 2.48 m span · 2,184 tris (measured) — **cheapest asset in the kit** |
| **Silhouette** | **LEGLESS.** One continuous swept manta planform, tip to tip, no separate wing parts, no notches, no rounded tips under the body. Low segmented glowing dorsal core. Two hair-fine filaments trail off the **rear, angled upward** so they can never read as limbs. |
| **Reads as** | A kite with a light in it. |
| **HP / speed** | 45 · 380 uu/s · hovers 0.9 m clear |
| **Attack** | `psi-drain` — telegraph 1.4 s → 9 dmg beam, 1,200 uu range |
| **Budget** | ≤3,200 tris · 1024px · 3 materials · 18 bones · 2 vfx |
| **Signature** | **Nothing is under the body.** The only thing beneath it is a body-shaped hover ellipse. The absence of legs is the whole design. |
| **Deck note** | No legs = no leg animation cost. The hover ellipse is a decal, not geometry. |

##### MUTON — *the heavy*
| | |
|---|---|
| **Lineage** | 1994 original. Terror-mission elite. |
| **Height / tris** | 2.07 m · 5,216 tris (measured) |
| **Silhouette** | Heavy + wide armoured slab, **horizontal emissive visor slit** in a dark recess, huge angled pauldrons, two-handed heavy plasma rifle with a foregrip, **oxblood chest plate** with panel seams, a 3-slat vent grille and a rank insignia. |
| **Reads as** | A walking tank with a letterbox for a face. |
| **HP / speed** | 220 · 260 uu/s |
| **Attack** | `heavy-plasma` — telegraph 1.6 s → 2 × 34 dmg at 1,800 uu/s |
| **Budget** | ≤7,000 tris · 1024px · 6 materials · 28 bones · 2 vfx |
| **Signature** | The **only warm hue in the alien set** — the oxblood chest plate. One material instance, one accent, on the chest only (Rule S3). |

##### CHRYSSALID — *the fast one*
| | |
|---|---|
| **Lineage** | 1994 original. Fast terror, leaper, infector. |
| **Height / tris** | 1.03 m · 6,252 tris (measured) |
| **Silhouette** | Low + wide forward-pitched stalker on **four long digitigrade legs** (femur, tibia, tarsus, clawed foot). **Two real scythe forelimbs** sweeping forward with a bone cutting edge. Dorsal ridge of bone spurs. Low head, mandibles, mouth seam, glowing venom sac. |
| **Reads as** | A fast crouch. Legible in pure silhouette at 40 px. |
| **HP / speed** | 70 · 520 uu/s (fastest thing in the game short of a boss) |
| **Attack** | `scythe-leap` — telegraph 0.7 s → 40 dmg melee, 900 uu leap range |
| **Budget** | ≤8,000 tris · 1024px · 4 materials · 30 bones · 1 vfx |
| **Deck note** | 4 legs + 2 scythes = the highest bone count per triangle in the kit. Animate 2 bones at a time. |

#### Plymouth natives

##### BARNACLE DRONE — *the swarm trash* `[target]`
1,200 HP-class trash unit · 0.60 m · ≤3,500 tris · 512px · 3 materials · 12 bones.
A clustered shell cone on three stubby legs with a single red eye-lens. Idle is a **wet
shell-clicking**; the eye-lens pulses red 0.6 s before the `shell-spit` (8 dmg, 2,600 uu/s).
Spawns in threes. LOD0 only, 512px textures — this is the unit that decides the Deck frame time.

##### PILGRIM ZEALOT — *the rifleman* `[target]`
1.85 m · ≤7,000 tris · 1024px · 5 materials · 26 bones. Hunched pilgrim in a ruffed collar, long
musket held across the body. Telegraph 1.5 s → 26 dmg hitscan ray, 3,000 uu range. Attacks
shout **"FOR THE KING!"** (distorted). Dies with the red ruffs exploding outward. Cloth is one
material, baked to the mesh — **no cloth sim, ever**.

##### MAYFLOWER PHANTOM — *the sniper* `[target]`
1.75 m · ≤6,000 tris · 1024px · 4 materials · 20 bones. Translucent tattered sail-cloak, hollow
hood, no visible feet. Materialises out of fog on a glass-shatter precursor. Telegraph 2.0 s →
45 dmg beam, 5,000 uu range. **Low aggression** — it punishes standing still, it does not
chase. Translucency is a **dithered mask, not a blend** — the cheapest honest ghost on a Deck.

##### LOBSTER BRUTE — *the pit gate* `[target]`
2.30 m · ≤9,000 tris · 1024px · 5 materials · 24 bones. Armoured lobster torso, two huge
asymmetric claws. Idle is sub-bass rumble; claws charge with static and **snap audibly 1.0 s**
before the `claw-snap` (55 dmg, 400 uu). Very high aggression. Hard shell = high roughness,
cheap specular — **no clearcoat**.

##### ROCK GOLEM — *the platform gate* `[target]`
2.60 m · ≤10,000 tris · 1024px · 4 materials · 16 bones. Blocky granite mass, no neck, glowing
orange cracks in the shoulders. `ground-slam`: 1.5 s telegraph → 60 dmg, 700 uu radius, then a
0.8 s recovery window. **16 bones — the least animation cost of any heavy.** Acts as a static
obstacle: jump it or kill it.

##### NOR-EASTER TITAN — *Act I boss* `[target]`
3.00 m · ≤18,000 tris · **2048px** · 6 materials · 28 bones · 4 vfx. Storm-front mass, cloud
skirt, lightning-forked arms. Idle is a hum below hearing; telegraph is a **foghorn blare** and
the sky darkens with lightning **1.8 s before the charge**. `storm-surge` spawns 45 dmg
projectiles at 2,000 uu/s every 2.0 s.
- **Phase 1 (100–50% HP):** standard. Mayflower Cannon, ~3.2 s TTK.
- **Phase 2 (50–0%):** **shield regenerates 10 HP/s if not hit.** Rocket splash clears the
  projectile storm. Adjusted TTK ~5.0 s. Ammo cost ≈ 4 rockets + 4 cannons.
- **Deck note:** the only 2048px asset in the game. At 'low' it drops to 1024 with a 4th-mip bias.

---

## 6. Weapons and the kill loop

> Sources: `Docs/generated/weapon_stats_table.md` §1 and `Docs/generated/weapons_enemies_v1.json`.
> Note the two documents use **different weapon names** for the same slots (e.g. "Mayflower
> Cannon" appears as both a shotgun and a heavy cannon). **This bible uses the
> `weapon_stats_table.md` set**, which is the tuned one and matches the TTK table.

| Weapon | rps | Speed (uu/s) | Dmg | Pellets | Spread | Ammo | Carry | Role |
|---|---|---|---|---|---|---|---|---|
| **Pilgrim Puckle** | 12.0 | 3,000 | 12 | 1 | 0° | Light | 300 | Primary. Drones, Zealots, Sectoids. |
| **Sextant Scattergun** | 1.8 | 3,000 | 14 | 10 | 4.5° | Heavy | 24 | Close range. Brutes. |
| **Barnacle Blunderbuss** | 0.9 | 3,000 | 22 | 12 | 8.0° | Heavy | 12 | Mid range. Zealots, Phantom. |
| **Rockhopper Rail** | 0.5 | 5,000 | 85 | 1 | 0° | Rail | 10 | Brute, Golem. |
| **Harbor Wreck Rocket** | 0.8 | 3,500 | 120 (+60 splash) | 1 | 0° | Rocket | 8 | Boss, groups. |
| **Mayflower Cannon** | 0.4 | 4,000 | 250 | 1 | 0° | Heavy | 6 | Boss. Titan phase 1/2. |

**Ammo economy (measured against a full arena clear):** the player carries ≈**1.5× the ammo a
standard clear consumes**, which permits "spray and pray" early but **forces weapon switching**
against Brute/Golem and puts the player at risk of being dry for the Titan if they miss 50% of
shots. Pickups restore **full max carry** for that ammo type — no partial refills, no reserve
pools, no reloads.

**The kill loop (per kill, every time):** screen shake + blood + gibs + a one-liner. One-liner
pool in `roster_bible.json → global_rules.one_liners`. These are the game's entire comic
register and they must be **short** — under 12 characters is ideal so they read in a corner
overlay at 144 FPS.

---

## 7. Art direction

### 7.1 The two-line pitch

> **1920s industrial decay meets Eldritch horror.**
> *(from `Docs/generated/level1_bible.md`)*

Expanded into three rules that everything visual obeys:

1. **Everything is wet, and everything is old.** Concrete, brick, rusted steel, tar, gravel, dock
   planking. Nothing is clean. Nothing is new. If a surface has no grime gradient, it is wrong.
2. **Light is scarce and therefore a weapon.** The enemies' emissives are the brightest pixels
   in frame. The player's own visibility is the fog's job. This is the 1994 *UFO* grammar
   honestly understood (see `CommandCenter/outputs/swarm-w1/TASK-01_xcom1994_roster.md` §0:
   the 1994 reveal was **pop-in from black**, not a light flash, and the "flash" people remember
   was plasma fire being the only light source on a night map).
3. **The palette is a marine one.** Cold blue-green greys, wet black, rusted orange, bone, and
   exactly one warm accent per scene.

### 7.2 Palette (locked)

| Role | Colour | Where |
|---|---|---|
| Base 1 — wet concrete | `#3A3F3D` cool grey-green | floors, battery mass |
| Base 2 — old brick | `#4A3A33` warm-dark brown | interior walls, ramp faces |
| Base 3 — rusted steel | `#6B4A32` desaturated orange-brown | gantry, containers, rails |
| Base 4 — black water | `#12161A` | pit, harbour, negative space |
| Accent A — sodium lamp | `#E8A54B` | the only warm light in Act I |
| Accent B — keycard green | `#4CE0A0` | green keycard glow, pillar light |
| Accent C — keycard red | `#E0484A` | red keycard glow, pit light |
| Accent D — alien green rim | `#33FF6B` | `reveal_rim` only, never as albedo |
| Accent E — plasma cyan | `#73E6FF` | `reveal_under`, emissive cores |
| Accent F — plasma violet | `#B07CFF` | weapon coils, boss only |
| **Oxblood** | `#7A2B2B` | Muton chest plate — the single warm hue in the alien set |

**Rule:** no more than **three** of these are on screen in one frame. Accents D–F are *light*
colours, not paint. There is no purple/blue SaaS gradient anywhere in this game and there never
will be.

### 7.3 Materials (locked names, `Content/Enemies/XCOM/`)

`XCOM_Chitin_Dark` · `_Mid` · `_Pale` — matte-to-satin carapace
`XCOM_Armor_Plate` (metalness 0.65) · `XCOM_Armor_Accent` (oxblood) — Muton only
`XCOM_Eye_Emissive` (emission 14) — every alien reads in the dark
`XCOM_Core_Emissive` (emission 22) — dorsal/neck power core, cyan
`XCOM_Plasma_Emissive` (emission 16) — weapon coils, violet
`XCOM_Gunmetal` — enemy weapon bodies

Level materials: `T_Floor_Concrete_Wet` · `T_Wall_Brick_Old` · `T_Wall_Steel_Rusted` ·
`T_Ground_Gravel` · `T_Roof_Tar` · `T_Wood_Plank_Dock` — all **2048²** with normal + roughness
maps, all in the palette above, all **seamless** (verified by 50%-offset 2×2 contact sheet).

### 7.4 The reveal rig (the signature look)

Authored in Blender as `reveal_key` / `reveal_rim` / `reveal_under` (+ optional `reveal_pool`,
`reveal_wash`), replicated as lights on the spawn actor. **Full measured parameters in
`Docs/generated/lighting_rig_spec.md`.** The shape of it:

| Element | Type | Colour | What it does |
|---|---|---|---|
| `reveal_key` | Spot, shadow-casting | cold `(0.62, 0.78, 1.00)` | the only shadow direction that matters — front-left, above, aimed at the chest |
| `reveal_rim` | Rect Area / wide Spot, shadow-casting | alien green `(0.20, 1.00, 0.42)` | **the separation light.** With a near-black backdrop this is the only thing drawing the outline. Never cull it, never replace it with a fill. |
| `reveal_under` | Point, no shadow, 2 cm radius | cyan `(0.45, 0.90, 1.00)` | tight local uplight at the feet. **Raise intensity, never radius** — a wide version turns "creature in the dark" into "product shot on a white light box". |
| `reveal_pool` | Spot, no shadow | cold blue | the bounded pool of light on the floor = the contact shadow |
| `reveal_wash` | Point, dim | blue-grey | keeps the shadow side of the floor readable without flattening it |

**The reveal is audio-first.** The sting plays on the *same frame* the light snaps on, so the
light confirms a sound the player has already heard. That is the 1994 grammar, honestly rebuilt.

### 7.5 Camera and framing

- First-person, eye height **1.6 m**, 90° horizontal FOV at 16:9.
- Weapon at the lower-right, canted 4–6° — the 1994 Doom-adjacent look.
- **No camera obstruction**: the camera never collides with world geometry in a way that hides
  an enemy silhouette. Ebert's level bar names camera-blocking geometry as a hard fail.
- Every submitted gameplay frame is shot **at 1.6 m**, from a real in-game position, at the
  real FOV. Beauty renders at 30° do not count as evidence of gameplay.

### 7.6 Motion

| Thing | Rule |
|---|---|
| Player | Acceleration is **instant**. There is no turn ramp. Doom 2016 movement means the gun is where the mouse is *now*. |
| Enemies | **Telegraph-first.** The tell is visible AND audible, and the tell duration scales with the attack's damage: 0.6 s (≤10 dmg) → 1.8 s (≥45 dmg). |
| Deaths | 0.15 s of gib-then-settle, never a ragdoll on a Deck |
| Screen shake | Per weapon, hardcoded amplitude table. Rocket 0.5, Cannon 0.4, everything else ≤0.15. |
| Boss (Harvester) | The only entity allowed to change the level. It eats at a **visible, constant rate** so the player can predict it. |

---

## 8. The bosses

### 8.1 BOSS I — **NOR-EASTER TITAN** (Act I, the harbour storm)

Full spec in §5.2. The design intent in one line: *it is weather that has opinions.*

- **Encounter.** Fights in the open north bay of `M_Blockout01` at the boss's cold-blue light.
  Fog density 40%. The arena is **open by design** — this is the tutorial boss, the player must
  learn to strafe and switch weapons here.
- **Phase 1 → 2 transition.** At 50% HP the sky blacks out, the foghorn sustains, and the Titan
  *stops moving* for 1.2 s while the phase-2 storm starts. The silence is the tell.
- **The lesson it teaches:** *hit it or it heals*. 10 HP/s shield regen is the game's first
  "damage you did not do" and it teaches the switch-weapon economy that the Harvester will then
  exploit much harder.
- **Kill.** ~5 s of sustained fire at ~250 dmg per cannon shot, with rocket splash clearing the
  projectile storm. Ammo cost ≈ 4 rockets + 4 cannons — that is the whole fight budget, and it
  is deliberately tight enough that running dry is a real possibility if the player wastes shells.

### 8.2 BOSS II — **THE HARVESTER** (Act III, the Pac-Man/Sonic hybrid)

**The full design is in `Docs/generated/boss_bible.md`.** Summary of the hybrid:

> Pac-Man's mouth — a grid-locked, node-eating pursuit that **consumes the level geometry** —
> welded to Sonic's legs — it *rolls*, and when it rolls it is fast, and when it is fast it is
> on rails, and the rails are the arena's own edges.

**What makes it a boss and not a big enemy:**

1. **It eats the arena.** Every 20 s it consumes one **power node** (a pillar, a crane leg, a
   container stack) and that geometry stops existing. The floor it walks on shrinks. The player
   is not fighting a creature in a room; the room is being consumed.
2. **It has a roll state and the roll state is the vulnerability.** Rolling is fast and lethal
   but it *cannot turn* — it travels the arena's outer rail, and the only way to hurt it is to
   get behind it or to bait it into a rail it cannot leave. This is the "telegraphed attack"
   contract inverted: the boss's own offence is its exposed back.
3. **The player can also feed it.** Nodes dropped by destroyed enemies are edible. Eating one
   **heals** it. Shooting a node before it reaches the mouth **denies the heal** but costs the
   player the node's own pickup. This is the only boss in the game with a **resource the player
   chooses to withhold** and it is the whole fight.

**Phases:**

| Phase | HP | Behaviour |
|---|---|---|
| **I — GRAZE** | 100–66% | Grid-locked, 1 node per 20 s, slow (200 uu/s). Telegraphed 1.4 s bite. Telegraphed 1.8 s roll along the outer rail. |
| **II — SWALLOW** | 66–33% | 1 node per 12 s. Spawns 2 Chryssalids per node consumed. Adds a **famine lunge** — a straight-line charge across the grid, 1.0 s telegraph, 700 uu/s, hits for 55. |
| **III — ROLL** | 33–0% | Node consumption **halts** (the arena is already mostly eaten — the HUD shows the manifest filling). It rolls continuously, 1,100 uu/s, and *cannot stop*. The player must survive the roll and hit the exposed back. Adds a **shriek** — the foghorn again, this time the one from 1926 that killed nine men. |

**Anti-frustration guarantees** (binding):
- The roll always has a **visible rail** — a glowing seam on the arena floor shows the track
  0.8 s before the roll begins. The player is never hit by an un-telegraphed roll.
- The mouth is **always open** for 1.2 s after a bite, and the mouth is where it is most
  vulnerable.
- **No instant death.** Every hit the Harvester deals is survivable, and the arena never
  reduces below a 12×12 uu safe island at the centre. If the arena cannot be reduced further,
  the boss stops eating and the fight becomes pure DPS.

---

## 9. Engine / Rust boundary

The shipped game is a **Rust executable** (cargo 1.92.0). The current build is UE5 + Blender.
The split is not negotiable and it is not fuzzy:

| Belongs in **Rust** (pure logic, ports cleanly) | Belongs in **UE5 / Blender** (engine-side content) |
|---|---|
| Damage math, hit resolution, resistance scalars | Meshes, skeletons, FBX import, LODs |
| AI state machines, telegraph timers, aggro, pathing costs | Materials, textures, material instances |
| Encounter scripting, wave timing, spawn tables | Lighting rigs, level geometry, fog, post-process |
| Weapon stats, ammo economy, pickup rules | Particles, decals, gib meshes, audio *assets* |
| Audio **scheduling** (when, at what volume, with what priority) | Audio playback (the mixer) |
| Taunt/insult selection, cooldowns, phase gating | The rendered insult WAVs themselves |
| Difficulty scalar application | |
| Score, one-liner selection, gib-request dispatch | |

**The contract file is `Docs/generated/roster_bible.json`.** The Rust side reads it verbatim at
build time and generates its stat tables from it. No value in that JSON is re-typed into Rust by
hand — a generator consumes it, so the two can never drift. The same is true of the boss spec
and the insult-bank spec.

**Linux note.** The game must build and run on Linux (fleet nodes develop it; the Deck runs it
under Proton). Therefore:
- All paths in tooling are POSIX-normalised and relative; no Windows-only path assumptions.
- All asset names are lowercase-with-underscores for the Rust side's asset manifest, even though
  the UE assets keep their display casing.
- The headless Blender and UE commandlet invocations in `Tools/blender/` and `Tools/python/` are
  written to run on both; the Windows equivalents use `flock` equivalents via
  `Tools/blender/blender_turn_htpc.sh`.
- No Windows-only audio or filesystem API in the Rust port. The WAV reader is written against
  `std::fs` + a hand-rolled RIFF parser (the TTS service emits plain RIFF/PCM — see §11.3).

---

## 10. Photograph plan (the Ebert evidence contract)

Nothing in this bible is scoreable until these exist. Ebert's rule: **fewer than the required
screenshots = INCOMPLETE, no score issued.** For a game artifact the required set is
**idle state, mid-action, and one score-or-failure state** (rubric §3), and the enemy/level/
lighting/main-character bars in `CommandCenter/outputs/ebert/EBERT_ENEMY_VERDICT.md` §4 specify
the exact frames per category.

### 10.1 Per-entity minimum (every enemy, every boss)

| # | Frame | Requirement |
|---|---|---|
| 1 | **Hero** | 3/4 view, lit under the reveal rig, 720×900+, full body, **nothing cropped**, model filling the frame, on a ground plane with a real contact shadow |
| 2 | **Turnaround** | 3 views (front / 3-4 / profile) in one image |
| 3 | **Scale** | 1.8 m human reference in frame |
| 4 | **Silhouette plate** | pure black shape on flat mid-grey, no ground, no lights — the Rule S1 proof |
| 5 | **In-engine** | the same entity at gameplay camera distance in `M_Blockout01`, with a second entity for scale |

Plus, for the entity to pass on *content* rather than only form:
| # | Frame | Requirement |
|---|---|---|
| 6 | **Emissive proof** | lit by nothing but its own emissives — proves the glow actually emits |
| 7 | **Studio vs reveal** | side-by-side, same pose, same camera |

### 10.2 Per-category extras

- **Roster sheet.** All 12 entities in one orthographic line-up at true relative scale, on the
  same ground plane, with a 1.8 m human. This is the single most useful image for Clarity and
  it is cheap to produce.
- **Level.** Top-down orthographic with tile grid + legend; ≥3 ground-level gameplay frames;
  annotated path diagram; one frame with ≥2 entity types at gameplay distance.
- **Textures.** 2048² sources; 2×2 contact sheet at 50% offset (seam proof); three native-res
  1:1 in-scene crops each; one trim sheet.
- **Lighting.** The rig's parameters as a screenshot (not a prose description); one reveal-rig
  frame per entity; the studio-vs-reveal comparison; the emissive-only proof.
- **Main character.** Front ortho, 3/4 hero, profile, back, **and one in-engine gameplay shot
  at real camera distance with an enemy for scale**; one animation clip at first/mid/settle; a
  scale comparison; a rig/wireframe capture.

### 10.3 The rule that keeps this honest

**Do not render a frame you cannot photograph the subject of.** Every entity above has a
specified silhouette, a specified palette, a specified budget and a specified light rig — which
means every entity is buildable and shootable. If a frame is missing at submission, the honest
move is to mark the category **UNSCORED** rather than to submit a stand-in. Ebert's rubric §7
is explicit: *"If you cannot see an image, say so and mark that axis UNSCORED — never score
what you did not look at."* The same discipline applies to the builder: **a substitute image
is worse than a missing one**, because a substitute is a fabricated result.

---

## 11. The TTS insult-bank contract

**Full contract:** `Docs/generated/insult_bank_contract.md`
**Data:** `Tools/python/taunt_lines.py` (40 lines, 3 phases, validator passing)
**Renderer:** `Tools/python/render_taunts.py`

The Harvester speaks. What it says is the "insult bank" — 40 lines of cheerful, half-finished,
glitchy-repetitive non-sequiturs in three phases, delivered by **F5-TTS on the HTPC**
(`http://10.0.0.42:8020/synth`). The contract fixes: the line schema, the safety rules, the
selection algorithm, the timing/cooldown, the render pipeline, the WAV format the Rust side
parses, and the **exact defect** in the current renderer (the payload key) that has to be fixed
before a single line lands.

---

## 12. Definition of done for this bible

- [x] Full roster with silhouette, HP, speed, attack, telegraph, and **per-entity budget**
- [x] Story: premise, three acts, antagonist, tone rules, named characters
- [x] Art direction: palette, materials, reveal rig, camera, motion
- [x] Both bosses specified, including the **Pac-Man/Sonic hybrid** (full spec in its own file)
- [x] Rust/engine boundary with a single machine-readable contract file
- [x] TTS insult-bank contract with the render defect identified
- [x] Photograph plan mapped to Ebert's exact evidence requirements
- [ ] **The renders.** Every frame in §10 exists. Until then nothing here is scoreable.
- [ ] **Level 2 and 3 exist.** Acts II and III are specified but unbuilt.

*Every figure in this document is either measured from a file in this repo or labelled a
design target. Nothing here is a claim about work that has not been done.*
