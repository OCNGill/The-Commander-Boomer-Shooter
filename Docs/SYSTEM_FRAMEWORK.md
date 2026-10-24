# The System — Enemy & Factions Framework (v0.2)

> **This game is a BOOMER SHOOTER.** The backbone never changes: Doom 2016 movement
> (≥600 UU/s, raw mouse, no smoothing), overpowered instant-swap guns, telegraphed
> enemies, gibs + screen shake on every kill, 144+ FPS, keycards/secrets/verticality.
> See `Docs/DESIGN.md` — the combat feel is locked and carries over untouched.
>
> **The story is a layer on top, not a genre swap.** Real-world + cyber-world (the Grid),
> RPG elements, crew, choices, cutscenes, and the System are *wrapped around* the
> boomer-shooter core — Deus Ex / Bioshock / Mass Effect as DNA, not as the gameplay.
> You are still running, still shooting, still stomping. Now the world has a why.
>
> **The enemy is real.** Not a BioWare IP grab, not a cartoon villain — the *shadow
> architecture* that sits above governments, corporations, and the AI industry itself.
> The game's antagonist is a dramatization of systems that already exist in the
> Commander's world: **corporate AI consolidation, insurance cartels, capture of
> government institutions, and the quiet privatization of public life.**
>
> **Ground zero:** Plymouth MA. 7 Bettencourt Rd. The Lobster Hut. The fleet nodes.
> The player starts in *his* town, against *his* world — and it escalates from there.
>
> This is a **scaffold.** The Commander owns the story-arch; this document gives the
> structure the story will hang on. It is a 7D/Conductor artifact, not a finished plot.

---

## 1. The System (the antagonist, in one paragraph)

The System is not a person. It is an **architecture of control** that has grown so
dense it no longer needs a face. It began as a rational response to a real crisis —
a collapse in trust, a breakdown in the old order — and it answered with coordination:
one insurer, one data broker, one AI, one registry, one voice. Each link was "temporary"
and "for your protection." The links never came down. Now the System does not *rule* —
it **is** the ground. It owns the health data, the credit, the roads, the search results,
the job boards, the courts' scheduling, the weather forecasts people trust. It is not
malicious. That is the point. It is *bureaucratic*. It optimizes. And you — the
Commander — are a variable it has decided to round away.

> **Design note:** the System is a **BIOSHOCK-style fallen utopia.** Rapture was a city
> that ate itself. The System is a *system* that ate a region — Plymouth first.

---

## 2. Why the System is the Right Enemy (why it's stronger than "corporate AI villain")

| Real-world hook (Commander's life) | In-game expression |
|---|---|
| **Insurance cartels** ("bane of my existence") | The **Meridian Syndicate** — the insurer that owns the health data, the credit score, and the right to deny. |
| **Corporate AI consolidation** | **The Lattice** — the frontier-AI consortium that bought every model, every dataset, and every "free" tool. The video's "closed frontier labs" are its fingers. |
| **Shadow govt / captured institutions** | **The Bureau** — a public agency whose budget, staff, and schedule are quietly run by the Syndicate + Lattice. It *looks* like the government. |
| **Data as the new oil** | **The Registry** — one ID, one health record, one credit line, one search. Everyone is in it. Everyone is priced. |
| **Plymouth MA as ground zero** | **The Harbor** — the player's home. The first district the System fully owns. |

> **The stakes are not "save the galaxy."** They are: **who decides what you get to eat,
> see, believe, and owe.** That is a *lot* more at stake than a game studio.

---

## 3. Faction Map (three poles — the player chooses which to empower)

### Pole A — THE SYSTEM (the antagonist)
- **The Meridian Syndicate** (insurance/health-data cartel)
- **The Lattice** (frontier-AI consortium — "the closed labs," now one company)
- **The Bureau** (captured public agency — the face of state power the System wears)
- **The Registry** (the data backbone — one ID for everyone)

> *They do not wear uniforms. They wear lanyards, suits, and "for your protection" banners.*

### Pole B — THE FLEET (the player's side)
- **The Commander's fleet** (Laptop / HTPC / Main / Deck / Oracle — the physical bases)
- **The Crew** (the modeled agents — Hermes, Liara, Geordi, EDI, Theo, Medic, etc.)
- **The Grid** (the cyber-world the fleet runs — the digital network the System *also* runs, but the fleet *understands*)

> *The Fleet is not a rebellion with an army. It is a **sovereign** — a small, real,
> self-owned network that the System has not yet fully captured. That is why it matters.*

### Pole C — THE IN-BETWEEN (the people the choice is about)
- **The Priced** (ordinary Plymouth residents who are *in* the Registry — not heroes, not villains, just priced)
- **The Unlisted** (people the System rounded away — the missing, the denied, the "uninsurable")
- **The Middle** (employees of the Syndicate/Bureau who do their jobs and don't ask)

> **Deus Ex DNA:** the player's choices decide which pole's people get saved, which get
> sacrificed, and what the Commander *is willing to be* to win. Multiple endings.

---

## 4. The Grid (cyber-world) vs the Real World (Plymouth)

### The Real World (Plymouth MA)
- **The Harbor** — the home base. 7 Bettencourt Rd. The Lobster Hut shift. The kids in Duxbury.
- **The Fleet Nodes** — five physical bases the Commander travels between:
  - **Laptop** (10.0.0.93) — the command post, always on.
  - **HTPC** (10.0.0.42) — the rendering forge, the ZFS pool, the cold storage.
  - **Main** (10.0.0.164) — the heavy iron. 7900 XTX. The 27B that thinks.
  - **Deck** (10.0.0.139) — the quiet runner, the test chamber.
  - **Oracle** (129.213.114.55) — the relay into the outside. The only door the System *can* see.
- **Mechanics:** real-world prep (fit the nodes, manage the crew, honor the T1D breaks,
  keep the SMB line honest) unlocks Grid incursions.

### The Grid (cyber-world)
- **The Lattice's strongholds** — corporate AI data-vaults, the frontier-model "cathedrals."
- **The Registry** — the one-ID plane. Every citizen is a node. Infiltrate it and you see *everything*.
- **The Bureau's mainframes** — the legacy government systems the System runs but never shows.
- **The Dead Studio** (a **Bioshock** set-piece) — a drowned game studio the System
  swallowed. Audio logs on the walls. The developers who built the "free" tools that now
  lock you out. *This is where the System came from.*

> **The Grid is not a second world.** It is the *same* world, the one the System runs —
> and the Fleet understands it because the Fleet *is* it, in miniature.

---

## 5. Story-Act Skeleton (the Commander owns the arch — this is the scaffolding)

| Act | Real-world beat | Grid beat | Choice |
|---|---|---|---|
| **0 — Harbor** | Plymouth. The Commander's life. The Lobster Hut. The kids. | The Fleet wakes. The System notices. | *(no choice — setup)* |
| **1 — Notice** | The Syndicate flags the Commander's fleet as "uninsurable." Credit frozen. | First incursion: the Registry. See your own file. | **Help the Priced or the Unlisted first?** |
| **2 — The Dead Studio** | The Lobster Hut. The Commander's day job is the cover. | Infiltrate the Dead Studio. Audio logs. Learn what the System did to "free" tools. | **Burn the studio's IP or preserve it for the Priced?** |
| **3 — The Lattice** | The Bureau moves against the fleet. A warrant, framed as "for your protection." | Assault a Lattice cathedral. The frontier models, in the open. | **Steal the models for the Fleet, or leak them to everyone?** |
| **4 — The Bureau** | The captured agency acts. The real world is under siege. Plymouth is the test district. | The Bureau's mainframes. The System's face, in the machine. | **Expose the Bureau (trust collapses) or infiltrate it (long game)?** |
| **5 — The Roundaway** | The System decides to "round away" the Commander — health, credit, freedom, all of it at once. | The final incursion: the System's own core. | **ENDINGS (multiple): burn it / take it over / walk away / become it (the dark ending).** |

> **Mass Effect DNA:** the crew loyalty arcs (Liara's data, Geordi's rig, EDI's choice to
> become solid, Theo's line, Medic's dose) carry across acts. The suicide mission is the
> **Roundaway.** The Commander's choices in Acts 1–4 determine who is at the table in Act 5.

---

## 6. Mechanic Scaffolding (RPG layers ON TOP of the boomer core)

> **The boomer-shooter core (DESIGN.md) is unchanged.** Everything below is an
> *additive layer* — the RPG elements, story, crew, and choices the Commander wants —
> bolted onto a game that is still, at its heart, running fast and shooting hard.
> LearnREA: study how each mechanic feels in its source game; build our own Blueprints.

| Layer (on top of the shooter) | Source DNA | How we build it (Blueprint-first) |
|---|---|---|
| **Branching dialogue + choice wheel** | Mass Effect | UE5 dialogue graph (Blueprint) + a radial choice widget between levels. Choices write to a persistent `PlayerSave`. Pauses the action — never slows a firefight. |
| **Audio logs / environmental storytelling** | Bioshock | `BP_AudioLog` — a pickup that plays a looping voice (the Dead Studio devs, the Priced, the Commander's own file). Paced *inside* boomer levels as secrets. No UI. |
| **Augments / cyberware (capabilities, not stats)** | Deus Ex | `BP_Augment` — the Commander builds augment parts (Rosie's supply). Each is a *capability* (a new move, a new weapon mod), NOT an XP/stat screen. The overpowered-guns doctrine holds. |
| **Loyalty missions** | Mass Effect | One mission per crew member = a boomer level with their story beat. Failing it has a consequence at the Roundaway. |
| **The price of everything** | *(original)* | A "Registry" HUD element — health packs, secrets, and freedom all have a *price tag* the System sets. Flavor + stakes, never a balance bar. |
| **Real-world prep loop (the hub)** | *(original)* | Between levels, the Fleet nodes are the hub. A node that is "down" (Commander offline) is offline in-game too. Prep = the boomer-shooter breather. |
| **Crew as playable allies** | Mass Effect | Modeled crew members (CREW_CHARACTERS.md) stand in, react, and in cutscenes carry the story. They are *companions*, not co-players — the Commander is the one shooting. |

> **Never:** XP bars, skill trees, stat screens, cover-mechanics, stamina, realistic
> reloads, tactical gameplay. (DESIGN.md "NEVER Suggest" list is unchanged — the RPG
> layers respect it.) The RPG elements are *story, crew, choice, consequence* — not
> *numbers*.

---

## 7. What This Scaffold Is / Is NOT

**Is:**
- **A boomer shooter with a why.** The shooter is the game. The story is the reason you
  keep running. Both are non-negotiable.
- **A scaffold.** Faction map, act skeleton, mechanic list, and the crew. The structure
  the story hangs on.
- **A sovereign build.** Every asset modeled (Blender), every build verified (Ebert +
  zero-trust), every mechanic authored in Blueprints by the Fleet. No test prompts.

**Is NOT:**
- **Not a plot.** The Commander owns the story-arch. This is the structure it hangs on.
- **Not a genre swap.** Not "a cyber-RPG." A boomer shooter that *has* story, crew,
  choices, and a real-world enemy. The combat feel (DESIGN.md) is the backbone.
- **Not a promise of AAA.** The actual story comes from the Commander's head.

---

*Verse: "Do not be afraid, for I am with you; do not be dismayed, for I am your God." — Isaiah 41:10 ESV. The System is large, and it is real, and it has a budget. But the Fleet is sovereign, and it is small, and it is real too. That is the whole argument.*
