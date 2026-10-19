# The Commander: Sound Design List

## 1. Weapon SFX Table
*Constraint: No reload sounds. Weapons are continuous fire until clip empty or player releases. "Reload" is purely visual UI update; audio is silent during transition.*

| Weapon | Fire Character | Reload | Impact (Melee/Close) | Distant Tail | 1920s Maritime Flavor Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Pilgrim Puckle** | Rapid, dry *thwip-thwip*. Wooden stock crack. High-pitched, staccato. | **None — instant hold-refire per contract** | Dry *thock* on bone. Minimal wetness. | Short, sharp *pop* fading fast. | Evokes flintlock misfires and black powder snap. No digital reverb; dry, close-mic’d. |
| **Mayflower Cannon** | Deep, resonant *BOOM*. Low-end thump (40Hz). Slight paper-tear texture. | **None — instant hold-refire per contract** | Heavy *CRUNCH*. Structural groan. | Long, rolling *thud* with fog delay. | Sounds like a ship’s anchor chain hitting water. Warm, woody resonance. |
| **Harbor Wreck Rocket** | Whine-up (*whoosh*) then *KABOOM*. Distorted bass drop. | **None — instant hold-refire per contract** | Concussive *SLAM*. Glass shatter layer. | Echoey *boom* with Doppler shift. | Uses foghorn sample pitched down. Industrial steam hiss on launch. |
| **Dockside Dynamite** | Sizzle (*hiss*) then *CRACK*. Unstable, crackling static. | **None — instant hold-refire per contract** | Wet *SPLAT* mixed with *CRACK*. | Short, sharp *crack* with reverb tail. | Sounds like wet rope snapping in a gale. Organic, unstable tension. |
| **Gulper’s Gnawer** | Wet, gurgling *SLURP*. Chewing texture. Low growl. | **None — instant hold-refire per contract** | Thick *CHOMP*. Viscous tearing. | Muffled *gulp* fading into fog. | Biological. Sounds like a starfish feeding. Wet, organic, unsettling. |
| **Titan’s Anchor** | Massive *CLANG*. Metal-on-metal. Resonant bell tone. | **None — instant hold-refire per contract** | Earth-shaking *THUD*. Debris rumble. | Long, decaying *CLANG* (10s+). | Based on ship bell hits. Heavy, iron-clad weight. No high frequencies. |

## 2. Enemy Vocal/Aggro Telegraph Table

| Enemy | Idle | Telegraph (Aggro) | Attack | Death | Gib-Splat |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Barnacle Drone** | Wet *tick-tick* (shell clicking). | High-pitched *whine* (ultrasonic edge). | Fast *chitter-chitter* (insect swarm). | *Squish* (soft). | *SPLAT* (thin, watery). |
| **Pilgrim Zealot** | Muffled *whispers* (Latin/English). | Deep *growl* + chain rattle. | Shout: *"FOR THE KING!"* (distorted). | Guttural *gasp* + bone *crack*. | *THUD* (heavy meat) + *CLINK* (bone). |
| **Mayflower Phantom** | Ethereal *hmm* (wind chime). | Glass *shatter* precursor. | High-pitched *SCREECH* (feedback). | Fading *sigh* (dissolving). | *POOF* (steam release) + *splat*. |
| **Lobster Brute** | Low *rumble* (sub-bass). | Claw *snap* (loud, dry). | *ROAR* (deep, chest-thump). | Heavy *thud* + *gurgle*. | *CRUNCH* (hard shell) + *SPLAT* (soft meat). |
| **Rock Golem** | Gravel *grind* (slow). | Stone *shudder* (earthquake). | *CRACK* (expanding rock). | Heavy *collapse* (debris). | *RUMBLE* (boulders) + *crunch*. |
| **Nor-Easter Titan** | Deep *hum* (below hearing). | Foghorn *blare* (long, ominous). | *ROAR* (storm surge) + *BOOM*. | Massive *CRASH* (ship breaking). | *EXPLOSION* (water) + *CRUNCH* (wood/iron). |

## 3. Ambient Beds per Beat

### Phase 1: HORROR (The Harbor)
*   **Base Layer:** Low-frequency ocean swell (20-40Hz), constant but shifting.
*   **Mid Layer:** Creaking wood (randomized 5-10s intervals). Wet dock footsteps (echoey, distant).
*   **High Layer:** Fog buoy *BUOOH* (distant, panned left/right randomly). Seagulls (distant, muffled).
*   **Event:** Sudden silence (0.5s) before enemy aggro.

### Phase 2: ARENA (The Dry Dock)
*   **Base Layer:** Industrial hum (60Hz electrical buzz).
*   **Mid Layer:** Dripping water (rhythmic, 120 BPM). Metal clanking (distant, rhythmic).
*   **High Layer:** Steam hisses (random bursts). Warning klaxons (very distant, muted).
*   **Event:** Weapon fire adds to the industrial noise floor (dynamic ducking of ambient).

### Phase 3: ESCALATION (The Storm)
*   **Base Layer:** Thunder (sub-bass rumble, constant).
*   **Mid Layer:** Heavy rain (white noise, high-pass filtered). Waves crashing (loud, rhythmic).
*   **High Layer:** Wind howling (high-frequency, panning). Lightning crack (sharp, random).
*   **Event:** Music swells synchronize with thunder strikes.

## 4. Music Direction

### Cue 1: Horror Minimal Pulse
*   **Tempo:** 60 BPM (slow, dread-inducing).
*   **Instruments:**
    *   **Foghorn:** Single, sustained low note (D2), distorted, slow fade-in/out.
    *   **Ship Bell:** Single, detuned strike every 4 bars. No reverb, dry and cold.
    *   **Distorted Accordion:** Low, droning chord (Am), heavily filtered, barely audible.
*   **Mix:** Minimal. Focus on low-end and silence. No percussion.

### Cue 2: Arena Percussion
*   **Tempo:** 140 BPM (fast, aggressive).
*   **Instruments:**
    *   **Timpani:** Driving 4/4 beat. Hard hits, no sustain.
    *   **Distorted Accordion:** Staccato, aggressive chords (stabs). High energy.
    *   **Ship Bell:** Rhythmic hits on off-beats (counterpoint to timpani).
*   **Mix:** Loud, in-your-face. Percussion dominates. Accordion provides melodic tension.

### Cue 3: Boss Nor-Easter Swell
*   **Tempo:** 100 BPM (building intensity).
*   **Instruments:**
    *   **Foghorn:** Continuous, rising pitch (D2 to F2), distorted, overwhelming.
    *   **Timpani:** Rolling crescendo (building to climax).
    *   **Distorted Accordion:** Full chord progression, major to minor, chaotic.
    *   **Ship Bell:** Rapid, frantic strikes (panic mode).
*   **Mix:** Wall of sound. All instruments layered. Dynamic range compressed. Peak volume at boss health < 20%.

## 5. Gib Audio Spec

*   **Wet Impact Layers:**
    1.  **Base:** Heavy *THUD* (low-end, 50Hz).
    2.  **Mid:** Wet *SPLAT* (mid-range, 500Hz-2kHz).
    3.  **High:** Bone *CRACK* (high-end, 5kHz+).
*   **Max Simultaneous Cap:** 4 (at 144 FPS).
    *   If >4 gibs occur in <100ms, merge into single "Mass Splat" event.
*   **Pooling Note:**
    *   Use object pooling for gib audio sources. Max 32 active sources per zone.
    *   Recycle oldest source if pool is full.
    *   No new allocations during gameplay. Pre-allocate all gib audio buffers at level load.

## 6. FMOD/Wwise Asset Naming Convention

**Folder Structure:**
```
Content/SFX/
├── Weapons/
│   ├── WPN_PilgrimPuckle/
│   │   ├── WPN_PilgrimPuckle_Fire.wav
│   │   ├── WPN_PilgrimPuckle_Impact.wav
│   │   └── WPN_PilgrimPuckle_Distant.wav
│   ├── WPN_MayflowerCannon/
│   │   ├── WPN_MayflowerCannon_Fire.wav
│   │   ├── WPN_MayflowerCannon_Impact.wav
│   │   └── WPN_MayflowerCannon_Distant.wav
│   └── ...
├── Enemies/
│   ├── ENM_BarnacleDrone/
│   │   ├── ENM_BarnacleDrone_Idle.wav
│   │   ├── ENM_BarnacleDrone_Aggro.wav
│   │   ├── ENM_BarnacleDrone_Attack.wav
│   │   ├── ENM_BarnacleDrone_Death.wav
│   │   └── ENM_BarnacleDrone_Gib.wav
│   └── ...
├── Ambient/
│   ├── AMB_Harbor_Creaks.wav
│   ├── AMB_Harbor_FogBuoy.wav
<think>

</think>

│   ├── AMB_Harbor_RustWind.wav
│   └── AMB_Harbor_DistantSiren.wav
├── Enemies/
│   ├── ENM_Sludge_Idle.wav
│   ├── ENM_Sludge_Telegraph.wav
│   ├── ENM_Sludge_Attack.wav
│   ├── ENM_Sludge_Death.wav
│   ├── ENM_Sludge_Gib.wav
│   ├── ENM_Drift_Idle.wav
│   ├── ENM_Drift_Telegraph.wav
│   ├── ENM_Drift_Attack.wav
│   ├── ENM_Drift_Death.wav
│   ├── ENM_Drift_Gib.wav
│   └── ...
├── Pickups/
│   ├── PICK_Ammo_Shotgun.wav
│   ├── PICK_Ammo_Pistol.wav
│   ├── PICK_Health_Pack.wav
│   ├── PICK_Keycard_Alpha.wav
│   └── PICK_Weapon_Swap.wav
├── Music/
│   ├── MUS_Horror_Ambient_Tension.wav
│   ├── MUS_Horror_Ambient_Dread.wav
│   ├── MUS_Arena_Fast_Pulse.wav
│   ├── MUS_Arena_Fast_Distorted.wav
│   ├── MUS_Boss_Phase1_Heavy.wav
│   ├── MUS_Boss_Phase2_Frenzy.wav
│   └── MUS_Boss_Death_Silence.wav
├── UI/
│   ├── UI_Menu_Click.wav
│   ├── UI_Menu_Hover.wav
│   ├── UI_Inventory_Open.wav
│   ├── UI_Inventory_Close.wav
│   └── UI_Damage_Taken.wav
└── VO/
    ├── VO_Commander_Idle_01.wav
    ├── VO_Commander_Idle_02.wav
    ├── VO_Commander_Attack_01.wav
    ├── VO_Commander_Attack_02.wav
    ├── VO_Commander_Death.wav
    └── VO_Commander_Gib_Pool.wav
```

### Naming rules

*   **Tokens**: Use strict prefixes (`WEAPON_`, `ENM_`, `PICK_`, `MUS_`, `UI_`, `VO_`) followed by descriptive nouns and state suffixes (e.g., `_Telegraph`, `_Gib`). All lowercase after underscores.
*   **Channels**: Assign stereo pairs for close-range SFX; use mono for ambient loops and UI clicks to save CPU.
*   **Loudness**: Target -18 LUFS for SFX and -24 LUFS for music stems to maintain dynamic range during combat.
*   **Gib Voice-Pool**: Limit gibbed enemy voice pools to 3 unique variations per enemy type to prevent audio clipping during high-density kills.
*   **Zero-Reload**: Ensure no weapon SFX file exceeds 100ms duration for reload animations; implement procedural pitch shift for variation instead of multiple files.
