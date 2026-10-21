# TASK-01 — X-COM 1994 Enemy Roster: Silhouettes, 1994 Battlescape Appearance, and Reveal Behaviour

**Slot:** swarm-w1 · **Model:** minimax/minimax-m3.1-flash:free · **Node:** Gillsystems-Laptop
**Written:** 2026-10-21T03:04:40-04:00
**Source basis:** the author's own knowledge of *UFO: Enemy Unknown* / *X-COM: UFO Defense* (Mythos Games /
MicroProse, 1994 — the "1994" release in North America, *UFO: Enemy Unknown* in Europe), cross-checked
against the in-repo assets this swarm has already built (`Tools/blender/out_xcom/xcom_manifest.json`,
`Tools/blender/xcom_enemies_v2.py`) so the research and the models do not drift apart.
**No web search was used for this artifact** (per task instruction). Where a claim is a memory rather
than a verified citation, it is marked `[recall]`; where it is structural to the repo's own pipeline, it
is marked `[repo]`.

---

## 0. READ THIS FIRST — the 1994 reveal was NOT a lighting flash

This matters for every downstream task (TASK-02 texture, TASK-03 reveal spec, TASK-05 procedural
materials, and the UE5 side), so it goes first.

The Commander's design brief states that in 1994 "the Battlescape was dark and aliens appeared in a hard
flash of light — you saw them *arrive*, lit from nowhere" (`CommandCenter/briefs/XCOM_ENEMY_DESIGN_BRIEF.md`).
**That is a beloved myth, not what the 1994 game did.** The 1994 Battlescape had no dynamic lighting
system, no light rigs, and no spawn-flash effect. What it actually had was this:

1. **The map was pre-rendered, not lit.** The 1994 Battlescape terrain was drawn (in the DOS release,
   entirely in hand-drawn pixel art; in the later SVGA release, pre-rendered terrain art) from a
   high 3/4 overhead angle. Lighting on the terrain was *painted into the art* — day, dusk, and night
   terrain sets existed as separate artwork, and night maps were genuinely near-black in the
   unexplored regions.
2. **Units were 2D sprites, not models.** X-COM soldiers were 16×16 sprites; aliens were 32×32
   sprites, drawn at 4 or 8 facing directions and composited over the terrain art. This is the single
   most important fact for a modernizer: the 1994 alien's "silhouette" was designed to read at
   32×32 pixels, which means the silhouette is loud and the interior detail is noise.
3. **Fog of war was literal.** Unexplored terrain was rendered black. An alien standing in an
   unexplored tile was *not drawn at all*. The moment a soldier acquired line of sight, the alien
   sprite was simply **there** — no fade, no flash, no spawn animation. The reveal was a
   pop-in from black.
4. **The "first contact" cue was audio + UI, not light.** When a soldier first saw an enemy, the game
   played a distinctive rising alarm sting, the soldier's status icon flipped to a "!" reaction, and
   the tactical view highlighted the enemy. The whole battlefield got a brief red/marquee alarm
   treatment on the map edge. The player *felt* the contact before they *saw* the creature.
5. **The only real "light" in 1994 was the muzzle flash and the plasma glow.** Aliens carried plasma
   weapons whose coils glowed in the sprite, and the 1994 game drew plasma fire as a bright coloured
   streak. In a black night map, a firing alien was the brightest thing on screen. That — not a spawn
   flash — is the authentic 1994 "flash of light," and it is the thing the modern rig should honour.

**So: how do we reconcile this with the brief?** We do not delete the brief's reveal rig. We re-frame
it. The brief's rig (`reveal_key` / `reveal_rim` / `reveal_under` + emissive eyes/core) is a
*modernization* of the 1994 **pop-in-from-black**, and the 1994 grammar it must reproduce is:

| 1994 reality | Modern equivalent in this project |
|---|---|
| Map painted near-black; alien not drawn until LOS | The scene is near-black and the creature is **not visible until the reveal event fires** — the reveal is the *first frame the player can see the silhouette*, and it is a hard cut, not a fade |
| The "!" sting + alarm the instant contact happens | The reveal is **audio-first**: the sting plays on the same frame the light snaps on, so the light *confirms* a sound the player has already heard |
| Plasma fire is the only light in a night map | The emissive eyes/core and the weapon coil are the **brightest pixels in frame** (this is already an explicit acceptance rule in `LIGHTING_V2_FIXLIST.md` §1) |
| 1994 units were 32×32 sprites — silhouette carries all the information | Every enemy must be **legible as a black shape against the ground before any light hits it**. The rig's job is to define that shape |

The combat grammar we are *modernizing* is therefore: **black map → hard light snap → the shape is
there → it attacks.** The brief's rig is correct; only the 1994 attribution needed fixing. This is
also the single most important input TASK-03 (creepy reveal spec) needs, so it is stated here as
normative.

`[recall]` on all of section 0 except the "brief says X" attribution, which is `[repo]`.

---

## 1. The 1994 roster at a glance

| Enemy | 1994 battlefield role | 1994 weapon | Size class | Primary colour | The one detail you remember |
|---|---|---|---|---|---|
| **Sectoid** | Psychic infiltrator; small squads; panic/psi hybrid | Unarmed (psi) — plasma pistol only in the later re-releases | Small (shortest) | Pale putty grey-green, near-white belly | A head that is *all cranium* — enormous smooth dome, no mouth, one dark eye socket pair |
| **Viper** | The marquee alien; standard terror-mission line unit | Plasma rifle | Tall, lean | Olive-drab scaled green, yellow-cream underside | The long low reptilian snout and the raised dorsal rib-cage |
| **Floater** | Aerial ambusher; swoops in and lifts a human out of the map | Unarmed (levitation/psi) | Medium, but *flying* | Grey-green membrane, pale underside | It has no legs at all — it hovers and the ground shadow is the only thing under it |
| **Muton** | Terror-mission elite; the heavy; arrives in numbers with cover | Heavy plasma cannon | Tall, heavy, widest | Blue-grey armour, **oxblood** chest plate | The visor slit: a horizontal red eye-band across a helmeted, armoured skull |
| **Chryssalid** | Fast terror; leaps; infects/kills civilians and soldiers | Unarmed — scythe limbs | Low, long, fast | Dusk-purple / maroon chitin | The head is a huge forward-jutting wedge with scythes sweeping ahead of it |
| **Ethereal** *(boss tier)* | Psi apex; mind-control leader | Unarmed (psi) | Tall, gaunt, floating-appearing | Cold teal-black, pale mask | A face that is a featureless elongated mask with a vertical slit |
| **Silicoid** *(boss tier)* | Cybernetic raid soldier; robot infantry | Plasma rifle | Human-sized, stiff | Brushed steel, red lens | Its red eye-lens in a smooth featureless metal face |
| **Dreadnought** *(boss tier)* | The carrier; the raid; the panic source | — (vehicle) | Vast | Matte charcoal, ribbed | A wing-shaped hull of a hundred spine-ribs that *flies over the map* |

### 1.1 Boss/agent tier — roster conflict to report (not edited)

The design brief lists the second wave as "Ethereal, Borg, Dreadnought, Celestial, Chosen, Retinoid
(Orion)." **Only three of those are 1994 canon.** Flagging rather than editing the brief
(`CommandCenter/briefs/XCOM_ENEMY_DESIGN_BRIEF.md`):

- **1994 canon:** **Ethereal** (alien-base/raid psi leader), **Silicoid** (cybernetic robot soldier),
  **Dreadnought** (the flying carrier raid).
- **Not 1994:** **Borg**, **Chosen**, **Celestial**, **Retinoid**, and the "Orion" designation are
  **X-COM: Apocalypse (1997)** and **XCOM (2012 reboot)** lineage. They are excellent designs, and
  the Commander may well want them, but they are not "the 1994 roster" and must not be sold as such.
- The 1994 game *did* have the Chosen-adjacent concept of the alien **"Ethereal"** and the armoured
  elite psions in the 1994 alien base — but the named "Chosen" and "Celestial" classes, and the
  "Orion" (human-conspiracy) faction, belong to 1997+.

**Recommendation to the session owner:** split the second wave into "1994 wave" (Ethereal, Silicoid,
Dreadnought) and "later-linenage wave" (Chosen, Celestial, Borg, Retinoid), and label the latter
honestly in the asset naming if they are ever built. `[repo]` for the brief text, `[recall]` for the
lineage attribution.

---

## 2. THE FIVE BUILT ENEMIES — full dossiers

Each dossier gives: silhouette → proportions → posture → colour → the single most memorable detail →
**what it actually looked like on the 1994 Battlescape** → its 1994 reveal behaviour → what the
modernized build must keep.

---

### 2.1 SECTOID — the infiltrator

**Silhouette.** A small biped whose entire read is *top-heavy*. The outline is a smooth, unbroken dome
of a head that swells to nearly a third of the body's total height, dropping almost vertically to
narrow sloping shoulders, then to arms that hang thin and slightly too long, and to short thin legs.
The 1994 sprite's outline has no hard corners anywhere on the upper body — it is one continuous
curve from the top of the cranium to the shoulder.

**Proportions.** `[recall]` Approximately 1.0–1.2 m in the 1994 scaling; the v3 in-repo model is
**1.44 m** `[repo]`, which is a modernization but on the tall side for a "smallest frame in the kit"
read — see §4. Head is roughly 30% of total height. Shoulders are narrow (a little over head width).
No neck — the cranium sits directly on the shoulders, which is what makes it read as a *mask-shaped*
creature rather than a bald human. Hands are oversized for the body: long, thin, splayed fingers.

**Posture.** Hunched. The head is carried forward of the spine, the shoulders are raised, the arms hang
loose. The 1994 sprite shows the Sectoid with its head thrust forward and slightly down, as if
peering. It reads as *curious and wrong*, not aggressive.

**Colour.** Pale putty grey-green, almost a dirty bone colour, with a slightly warmer tan on the
flanks; the eye region is the darkest value on the creature and the only high-contrast feature. In
the modern kit this maps to `XCOM_Chitin_Pale` / `XCOM_Chitin_Mid` with the *eyes* as the only accent.

**The single most memorable detail.** **No mouth.** The 1994 Sectoid's face is a smooth, uninterrupted
expansion of cranium with two large dark eyes set low and wide, and absolutely no mouth, no jaw, no
snout. Every modernizer reaches for "add a mouth for readability" and it ruins the creature. The
repo's v2 fixlist got this right — "Sectoid: canonically mouthless — keep that, but add a nasal slit,
a brow ridge, and a chin plate so the skull is not a bare sphere" `[repo]`. **Keep the mouthlessness
forever.** The nasal slit is the correct modern addition; the chin plate is a near-miss (it starts to
suggest a jaw) — the fixlist already calls it out and it should stay subtle.

**On the 1994 Battlescape.** A 32×32 sprite seen from the game's high 3/4 overhead camera, so the
readable information is the **top-down head shape and the thin vertical dark line of the body**,
with the big eyes picking up as two dark pixels. In a night map, the Sectoid was a pale smudge
against black — the *pale* value was the read, the eyes were the punch. In a day map it was a
deceptively civilian-looking little figure, which is exactly the 1994 infiltration fantasy: the
Sectoid in daylight looked almost like a hunched civilian. That contrast is the whole character.

**1994 reveal behaviour.** A Sectoid was among the *first* alien type the player ever met, and the
1994 game taught the fog rule with it: it was typically already standing in a black tile when the
first soldier turned the corner. The contact was announced by the alarm sting and the "!" reaction,
then the Sectoid sprite simply appeared in the cleared terrain. It was not a jump-scare enemy; it
was a *surprise of scale and pallor* — you expected a person, and there was a small pale thing
with no face. In 1994 the Sectoid also **panicked**: it raised panic in nearby civilians, and the
panic spiral (civilians fleeing, doors opening) was more frightening than the Sectoid itself.

**Modernization must keep.** (a) Mouthless, permanently. (b) The head is the character — the
modernized cranium must be the largest single mass on the model, and the eyes the brightest pixels.
(c) A "pale smudge in the dark" read — the Sectoid is the one enemy whose *pale* material should be
allowed to be the brightest non-emissive thing in frame, because that was its 1994 job.
(d) The hunch: torso pitched forward, head slightly further forward still.

---

### 2.2 VIPER — the marquee alien

**Silhouette.** Tall, narrow, and reptilian. A long low head thrust forward on a short thick neck, a
body that is longer than it is wide, arms that hang past the knees, and — the element that makes it
iconic — a **raised ridge of dorsal ribs** running the length of the back, each rib standing proud of
the spine like a row of blades. The 1994 Viper outline is essentially a **standing question-mark**:
head forward, ribs up, tail down.

**Proportions.** `[recall]` About 2.0 m in the 1994 game; the in-repo v3 model is **2.06 m** `[repo]`
— very close to the source, keep it. Long torso, short legs relative to the body, arms reaching
below the knee (note: the *1994* sprite's arms reached nearly to the ankle, and the repo's v2
fixlist explicitly shortened them to end at the hip — that is a modernization, a good one, and it
improves the read at gameplay distance, but the "long-armed" quality should be preserved through
the *proportion* of the forearm, not by making the arms dangle absurdly long). Digitigrade-ish
stance with a long tail. The repo manifest calls it "tall + narrow" with a 0.64 m width against
2.06 m height `[repo]` — that 1:3.2 width-to-height ratio is right and is the number to protect.

**Posture.** A forward-leaning hunter. The head is carried low and forward, the shoulders hunched
forward over the chest, the knees slightly bent, the tail counterbalancing behind. The 1994 Viper
looked *permanently mid-pounce*, even standing still.

**Colour.** Olive-drab / army green scaled hide, mottled darker on the back and along the rib ridge,
with a paler yellow-cream belly and inner arm. The plasma rifle it carries has a distinctly
*cold-blue* glow in the 1994 art — the Viper was the alien most associated with the cold plasma
flash at night.

**The single most memorable detail.** **The elongated snout.** In 1994 it was a long, flat, almost
crocodilian muzzle with a slight downward hook and a visible nostril ridge, and it was *always*
shown in profile or near-profile. Second place: the raised rib-cage ridge. The repo v2 added a
**45 cm forward-projecting tapered snout with a plated nasal ridge and six bone teeth in a recessed
jaw seam** `[repo]` — that is a faithful and well-judged modernization of the 1994 read. **Do not
shorten the snout** for "realism"; the snout *is* the Viper.

**On the 1994 Battlescape.** At 32×32 in a 3/4 overhead view, the Viper's readable marks were: the
forward jut of the head (a distinct dark notch in the sprite's upper-left), the dorsal rib ridge (a
row of light pixels catching the painted light down the back), and the long thin arms. In daylight it
was a green biped with a rifle; in a night map it was almost entirely defined by the **faint lit
top of the rib ridge and the muzzle flash**.

**1994 reveal behaviour.** The Viper was the game's *standard terror* — it came in squads, in
groups, often with a Muton. The 1994 pattern was a **dropship**: the map starts empty, a troop
transport lands out of frame, and the aliens walk in. The 1994 game *did* have a UFO landing on
terror missions and the troops deploy from it at the map edge. But the "ambush" the player actually
experienced was: the aliens were already on the map, hidden in black, and the *first* one you saw was
the one that opened fire — the plasma rifle's glow and report announced them a beat before the
soldier had a visual. **That is the authentic 1994 "alien contact reveal": a light before a body.**
The Viper is the enemy that most needs the modern rig to reproduce that ordering — the weapon coil
should read as the first thing visible, then the silhouette behind it.

**Modernization must keep.** (a) The snout. (b) The rib ridge as a *silhouette* element — it must
break the outline, not just be a texture. (c) The plasma rifle's cold glow as the "first light"
read. (d) Height ~2.0–2.1 m and the 1:3.2 width ratio.

---

### 2.3 FLOATER — the aerial ambusher

**Silhouette.** A broad, flat, manta-like body with **no legs and no ground contact**, wings or
membranes swept out to either side, a small blunt head at the front, and trailing filaments off the
rear. The whole creature is a single wide horizontal wedge. `[repo]` The v3 model is **0.33 m tall
and 2.48 m wide** — a 1:7.5 aspect. That aspect ratio is the character, and it is the widest thing
in the kit by a factor of two.

**Proportions.** 1994: a hovering flyer of roughly human mass but a much greater wingspan than
height. The in-repo v3 build is a legitimately excellent piece of enemy design in its own right
(2.48 m span, legless, one continuous swept planform per side, three low segmented dorsal core lens
segments) `[repo]`. Keep the 1:7.5.

**Posture.** Level, flat, and *banked* — it is always slightly rolled, never upright. The 1994
Floater was always shown off the ground with a gap under it.

**Colour.** Grey-green, with a translucent-looking membrane and a paler underside, plus the one
bright thing on it: the **glowing core**. `[repo]` The v3 model puts a **low segmented glowing dorsal
core** on the back and only two hair-fine filaments trailing off the rear — no rods, no spheres, no
descending appendage of any kind. That is right, and the fix is *already* correct. Do not re-add
anything below the body.

**The single most memorable detail.** **Nothing under it.** The Floater's underside is empty space.
In 1994 it was literally the only alien that was not standing on the ground, and the ground shadow
underneath it was the tell. The repo's v3 answer — "the body-shaped hover ellipse on the floor is
the only thing beneath it" `[repo]` — is exactly the 1994 grammar, and it is the single strongest
piece of fidelity in the whole kit. **Protect this at all costs.** Every later pass must be checked
against "is there anything under the Floater that isn't a shadow."

**On the 1994 Battlescape.** `[recall]` The 1994 Floater's battlefield behaviour was a swoop-in
ambush: it descended onto an isolated human and **levitated them off the map** (the civilian was
removed from play, and X-COM paid a ransom). It also performed the "psi" role — the 1994 Floater
was a psychic; the 1997+ "Floater" became a flying gun platform with a plasma cannon, and that is
**not** the 1994 creature. The Commander's brief describes the Floater as "psychic hover, mind
control" `[repo]` — that is 1994-accurate, and the modern build correctly gives it **no weapon**
(`has_weapon: false` `[repo]`). Keep it unarmed.

**1994 reveal behaviour.** Because it flew, the Floater's reveal was the one 1994 case that was
*not* a pop-in from black: it came **down through the fog** — a shadow crossing the ground first,
then the body, then the descent. The 1994 camera was top-down enough that a descending Floater was
a *growing shadow*. The modern equivalent that must be built: **shadow first, body second, light
third.** The `reveal_under` light in the repo rig and the hover ellipse in the v3 model are the
right primitives; the ordering (ground shadow appears → body resolves → rim light snaps) is the
authored beat that has to be in the reveal spec.

**Modernization must keep.** (a) No legs. (b) The hover ellipse as the only ground element.
(c) The dorsal core as the only bright thing on the body. (d) The 1:7.5 span. (e) Unarmed, psychic.
(f) A banked, never-upright attitude.

---

### 2.4 MUTON — the terror-mission heavy

**Silhouette.** A wide, heavy, armoured biped. Enormous squared pauldrons that flare out past the
hips; a helmeted, featureless head with a single **horizontal visor slit**; a broad chest with a
prominent plate; thick, straight legs. The 1994 Muton outline is basically a **bell** — narrow head,
enormous shoulders, skirt of armour. It is the widest and the heaviest silhouette in the roster, and
it is the only enemy that reads as *made* rather than *born*.

**Proportions.** `[recall]` ~2.2 m in 1994; the in-repo v3 model is **2.07 m** with a **1.15 m
width** `[repo]` — i.e. 1:1.8 height:width. Compare the Viper at 1:3.2. **That contrast is the
whole readability strategy of the kit:** the Muton is broad and short-looking, the Viper is tall and
thin, and at gameplay distance they can never be confused. The repo's "walking tank" phrasing is
accurate. Keep the 1:1.8.

**Posture.** Square, planted, both feet wide. The 1994 Muton stood like a door — it did not lean,
it did not slouch, it *occupied space*. The repo v2/v3 notes describe huge angled pauldrons, a
horizontal emissive visor slit in a dark recess, a brow bar, a helmet crest, a slatted respirator,
and a detailed oxblood chest plate with panel seams, a 3-slat vent grille, and a rank insignia
`[repo]` — all good, all in the spirit of 1994 where the Muton had visible armour *sections*.

**Colour.** Blue-grey / gunmetal armour with a distinctly **red-oxblood** chest plate that reads as
the creature's "tie". In the 1994 sprite the Muton's single warm colour was that chest panel; the
rest was cold grey-blue. The repo keeps exactly this: `XCOM_Armor_Plate` (metal 0.65) plus
`XCOM_Armor_Accent` (oxblood) `[repo]`. Correct. The accent is the identity.

**The single most memorable detail.** **The horizontal visor slit.** A single narrow red eye-band
across a featureless armoured helm. The 1994 Muton had no visible face at all beyond that band, and
the band was *angry* — a laser line, not a pair of eyes. The repo v2 explicitly removed the
illegible "cream hook" and replaced it with "a HORIZONTAL EMISSIVE VISOR SLIT in a dark recess" and
a "brow bar, a helmet crest and a slatted respirator" `[repo]`. That is a clean, correct
modernization. **The visor must remain a single band** — do not split it into two eyes, do not give
the Muton a mouth.

**On the 1994 Battlescape.** The 1994 Muton was the *alarm* enemy — the unit that made the whole
terror mission a terror mission. The 32×32 sprite read as: wide shoulders, a bright horizontal line
at head height, a pale chest block. The red chest plate plus the red visor in a black night map gave
the player a **two-red-points-on-a-grey-mass** read that was instantly identifiable, and it is the
clearest demonstration in the original game that *colour accents carry identity in the dark*. That
is precisely the argument the modern rig makes, and the Muton is its poster child.

**1994 reveal behaviour.** Mutons arrived in numbers, under cover, and were the enemy that **ended
missions by weight of fire** rather than by a single alpha strike — the 1994 Muton's plasma cannon
was brutal. The 1994 player's experience of the Muton was: you *knew* one was on the map before you
could see it, because the first Muton you'd ever met had already killed a soldier. In the
modernized version this argues for the Muton being the enemy with the **longest, hardest read** —
its silhouette should be heavy, slow, and unmistakable, and its reveal should feel like a wall
arriving rather than a shape appearing.

**Modernization must keep.** (a) The single horizontal visor band. (b) The oxblood chest plate as
the only warm colour. (c) The 1:1.8 width:height. (d) The flare of the pauldrons past the hips.
(e) The heavy plasma cannon held two-handed with a foregrip `[repo]` — legible as a weapon per the
fixlist.

---

### 2.5 CHRYSSALID — the terror from the deep

**Silhouette.** Low, long, fast, and **forward-pitched**. A deep body carried close to the ground on
four long spindly legs, a huge head thrust forward and low, and two long **scythe arms** sweeping
forward ahead of the head like a pair of sickles. The 1994 outline is a **shark shape pointed at
you** — wedge head forward, body tapering back, legs cycling underneath.

**Proportions.** `[recall]` ~1.3 m tall in 1994, but very long front-to-back; the in-repo v3 model is
**1.03 m tall × 1.62 m long** `[repo]`. The 1:1.6 length-to-height ratio is the important one: the
Chryssalid is the longest of the five and the lowest. Do not raise it. It should never be able to
look over a waist-high crate, because the whole point of the 1994 Chryssalid was that it came in
*under* your guard and took a civilian before your rifleman turned.

**Posture.** Coiled. Head low and forward, scythes extended, rear arched. The 1994 sprite even at
rest looked like it was mid-leap.

**Colour.** Dusk-purple / maroon chitin, near-black in the shadows, with a pale cutting edge on the
scythes. In the 1994 palette the Chryssalid was one of the few enemies with a saturated *non-green*
colour, which is why it never got confused with the Viper in a night map.

**The single most memorable detail.** **The scythes.** Two long blade-arms that sweep forward and
cross ahead of the head, and the venom glow at the base of them. The repo v2 got this right and
explicitly: "TWO real scythe forelimbs sweeping forward with a bone cutting edge, a dorsal ridge of
bone spurs, a low head with emissive eyes, mandibles, a mouth seam and a glowing venom sac" `[repo]`.
**The scythes must be bone-white cutting edges against the dark chitin** — that value contrast is
what makes the creature visible in the dark, and it is the same principle as the Muton's red accents.

**On the 1994 Battlescape.** The 1994 Chryssalid was the one enemy with a *movement* identity rather
than a static one: it was **fast** (faster than a soldier could react), and critically it **leapt**,
crossing several tiles in a single bound. It also had the most unpleasant 1994 animation in the
game. And its horror function was narrative: a Chryssalid that caught a civilian would leave
something *wrong* behind — a body that was no longer entirely a body. The 1994 Chryssalid could
turn a human into a Chryssalid. That is a signature 1994 story beat, and the modernized version
should keep a version of it (spawn a Chryssalid-form rather than a corpse).

**1994 reveal behaviour.** Because it leapt, the Chryssalid's reveal was not a pop-in from black but
a **fast crossing of a lit tile** — you saw it because it moved, and then it was on top of you. The
1994 player learned to fear movement more than shapes. The modern equivalent: the Chryssalid's
emissive eyes and venom glow should be visible **at distance in a dark tile before the body
resolves** — a pair of small green points sliding across the dark, which is the 1994 "I see it
because it moved" memory, translated into 3D.

**Modernization must keep.** (a) Four digitigrade legs — never a biped. (b) The forward scythes.
(c) The low 1:1.6 length profile, head low. (d) The bone-white scythe edges against dark chitin.
(e) Fast, committed movement and a leap attack.

---

## 3. THE 1994 BOSS / AGENT TIER

### 3.1 ETHEREAL — the psi apex

Tall, gaunt, and *wrongly proportioned* — a very long narrow body, small head, long thin arms, and a
face that is a smooth vertical mask with a single slit. It reads as a robed or mummified figure.
Colour: cold teal-black with a pale mask and pale hands. Its signature is **the mind control**:
in 1994 the Ethereal's psionic attack turned one of your own soldiers against you, and the
battlefield UI made it unmistakable who was now hostile. The modernized analogue is a **psi
"attention" beam and a mind-control state that visibly flips a soldier's allegiance marker and
faction** — with a telegraph (the beam + the head turn) and no instantaneous capture. The reveal
should be the *coldest* in the kit: a slow, cold key and a very dark body, so the pale mask is the
only readable thing.

### 3.2 SILICOID — the cybernetic soldier

The 1994 raid robot. Human height, stiff, symmetrical, entirely **featureless metal** apart from a
single **red eye-lens** set in a smooth face. Brushed steel body, dark joints, plasma rifle. Its
memorable quality is that it moves like a person but *just* wrong: mechanical, too smooth, with no
hesitation. The 1994 Silicoid was the enemy that made raids frightening, because you could not read
intent from it. Modernized: a perfectly smooth gait cycle, a red lens that tracks the player, and a
*flattened* emotional read — the modern rig should give it zero idle fidget, all the other enemies
get fidget, the Silicoid does not.

### 3.3 DREADNOUGHT — the carrier

Not a character but a boss event. A vast, matte-charcoal, wing-shaped hull ribbed like a spine,
that crosses the map overhead and drops the terror mission. The 1994 Dreadnought's power was that it
was a *moving objective* — the mission was about stopping the ship, and the ship was the clock.
Modernized: it should be the only enemy asset in the kit that is not a biped, and it should be
lit the same way (hard cold key, coloured rim, under-glow) so the reveal grammar is unified.

---

## 4. Cross-checks against the assets already in the repo

The research above was checked against `Tools/blender/out_xcom/xcom_manifest.json` and the v2 build
script, so the next pass does not "fix" a deliberate choice by accident. `[repo]`

| Enemy | In-repo measured (v3 manifest) | 1994 read | Verdict |
|---|---|---|---|
| Sectoid | 1.44 m tall, 0.46 m wide, **no weapon**, luminous eyes, no mouth | smallest frame, mouthless, unarmed psi | Height is ~20% over the 1994 feel. **Recommendation:** pull the cranium scale/height toward ~1.25–1.35 m, or keep 1.44 m but raise the cranium ratio so it still reads as the *smallest* silhouette from the gameplay camera. Do not change the mouthlessness or the eye emissive. |
| Viper | 2.06 m, 0.64 m wide (1:3.2), plasma pistol, snout + 5-rib spine, teeth | tall, narrow, snouted, plasma rifle | Faithful. **One naming risk:** the manifest calls it a "plasma pistol" while the 1994 Viper carried a **plasma rifle** and the 1994 Sectoid carried no gun. If the intent is 1994 accuracy, the Viper's weapon should be the rifle, and the "pistol" naming should be checked against the weapon contract in `Docs/generated/weapons_enemies_v1.json`. |
| Floater | 0.33 m tall, 2.48 m wide (1:7.5), **legless**, no weapon, dorsal core, rear filaments only | hovering manta, legless, unarmed, 1 bright core | Excellent. **No changes.** Guard the "nothing underneath" rule. |
| Muton | 2.07 m, 1.15 m wide (1:1.8), visor slit, oxblood chest, heavy plasma rifle, two-handed | broad armoured heavy, single visor band, heavy cannon | Faithful. Weight is a bit lighter than the 1994 Muton's "door" mass, but the 1:1.8 ratio is the right discriminator against the Viper. |
| Chryssalid | 1.03 m tall, 1.62 m long, 4 digitigrade legs, 2 scythe forelimbs, venom sac, no weapon | low, long, leaping, scythes | Faithful and well-judged. |

Additional cross-referenced repo constraints these dossiers must not violate:

- `XCOM_Eye_Emissive` / `XCOM_Core_Emissive` / `XCOM_Plasma_Emissive` are the **only** emissive
  families, and the eyes must be the brightest pixels in frame `[repo, LIGHTING_V2_FIXLIST §1]`.
- Material families are exactly **CHITIN / PLATE / ACCENT** — bone/pale is reserved for bone ridges,
  teeth and spurs, never for hands or feet `[repo, XCOM_ENEMY_V2_FIXLIST §E]`.
- No enemies are to be re-invented: modernized, not redesigned. Everything above is framed as
  *protection* of a 1994 feature, never as a new feature.
- Hard locks: true 3D only, no sprites, no billboards; no reload animations **including enemy
  weapons**; pickups-only health, no regeneration.

---

## 5. The reveal grammar, stated once, for TASK-03 to inherit

If this repository builds one thing well, it should build this. The 1994 rule, restated as a modern
authored beat, per enemy:

1. **Black.** The tile the enemy is on is unlit and the enemy is not visible. (1994: unexplored
   terrain is black and the unit is not drawn.)
2. **A sound arrives first.** The contact sting plays on the same frame as the light snap — the
   player's ear knows before the eye does. (1994: the alarm sting + the "!" reaction.)
3. **A hard light snap — no fade.** A cold key with a hard shadow, off-axis, sculpting the *face* and
   dropping the lower body into black. (1994: no fade existed; a pop from black. Do not add a fade-in.)
4. **The silhouette resolves, not the body.** Only the head, the eyes, and one shoulder are fully
   readable; the rest is falloff. (1994: a 32×32 sprite could only ever carry a silhouette.)
5. **The eyes are the brightest pixels in the frame.** (1994: the only light in a night map was the
   plasma flash and the glow; the modern version keeps the *emissive-first* rule.)
6. **A ground anchor.** A tight contact-occlusion seam at the soles, and one clear cast shadow
   falling away from the camera — except the Floater, whose only ground element is its shadow.
7. **The under-glow is under the creature, not in front of it.** (Per `LIGHTING_V2_FIXLIST` §3, a
   floor pool is not an under-glow.)
8. **Enemy-specific first-read** (from the dossiers above):
   - Sectoid — a pale smudge; no mouth; the *absence* is the scare.
   - Viper — the **weapon coil glow first**, then the snout and rib ridge.
   - Floater — **ground shadow first**, body second, light third; it descends into the fog.
   - Muton — the **red visor band and oxblood chest** are the first two things in the frame; it
     arrives as a wall.
   - Chryssalid — **two small green points moving across a dark tile**; it resolves late and
     arrives first.

---

## 6. Open questions for the session owner (reported, not acted on)

1. **Roster lineage** — should the second wave be split into 1994 (Ethereal / Silicoid /
   Dreadnought) and later-linenage (Chosen / Celestial / Borg / Retinoid)? The brief currently
   lumps them. §1.1.
2. **Viper weapon naming** — 1994 Viper = plasma **rifle**; the manifest says "plasma pistol."
   Reconcile against the weapon contract.
3. **Sectoid height** — 1.44 m vs a 1994 feel of roughly 1.1–1.2 m; scale down, or raise the
   cranium ratio?
4. **Chryssalid civilian infection** — the 1994 Chryssalid turned humans into Chryssalids. Adopt as
   a modernized mechanic? (No regeneration, no health system changes implied; it is a spawn swap.)
5. **Doctrine for the 1994 myth** — the brief's "aliens appeared in a hard flash of light" is
   in-fiction-now and accurate-as-a-feel, but historically wrong. Recommendation: keep the rig,
   re-word the citation to "modernized from the 1994 pop-from-black + plasma-flash grammar"
   so the artifact does not mislead anyone reading it later.

---

> Psalm 33:6 (ESV) - "By the word of the LORD were the heavens made; and all the host of them by the
> breath of his mouth." Chosen because this roster is preserved, not invented: the modern creature is
> an argument for the 1994 creature, not a replacement for it.
