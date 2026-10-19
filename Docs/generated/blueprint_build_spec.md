# THE COMMANDER: Blueprint Build Specification
**Engine:** Unreal Engine 5.8 (Blueprint-Only)
**Target:** 144+ FPS, Doom 2016 Movement, Plymouth MA Horror
**Status:** Locked Design / Execution Ready

## 1. BP_Player (Parent: Character)

### Component Tree
1.  **Capsule Component** (Collision Preset: Character, Capsule Half Height: 90.0, Radius: 34.0).
2.  **Camera Component** (Spring Arm attached, Target Arm Length: 0.0, Location Offset: (0, 0, 40.0)).
3.  **PlayerCameraManager** (Default).
4.  **Weapon Socket** (Bone/Socket on Mesh, not Component, for attachment).

### CharacterMovement Settings Table
*Access via `Character Movement` component in BP_Player.*

| Property | Value | Notes |
| :--- | :--- | :--- |
| **Max Walk Speed** | `600.0` | Locked floor speed. |
| **Ground Friction** | `0.0` | Set to 0. Friction is handled by `AirControl` and `GroundFriction` override in Event Tick if needed, but for Doom-style, set **Ground Friction** to `0.0` and rely on **Air Control** and **Max Acceleration**. *Correction:* For instant stop/start, set **Ground Friction** to `0.0` and **Air Control** to `1.0`. |
| **Air Control** | `1.0` | High air control. |
| **Jump Z Velocity** | `500.0` | Standard jump height. |
| **Gravity Scale** | `1.0` | Standard gravity. |
| **Max Acceleration** | `2000.0` | Snappy acceleration. |
| **Braking Deceleration** | `2000.0` | Instant stop. |
| **Use Controller Rotation** | `True` | Standard. |
| **bOrientRotationToMovement** | `False` | Character mesh rotates via input, not movement. |
| **bConstrainRotation** | `False` | Free look. |

*Note: To achieve "Doom 2016" feel, ensure `Air Control` is high. If movement feels floaty, increase `Gravity Scale` to `1.5` and `Jump Z Velocity` to `550.0`. Start with above values.*

### Enhanced Input Setup (Project Settings)
Create Input Actions (IA) in Project Settings > Input:
1.  **IA_Move** (Vector2D)
2.  **IA_Look** (Vector2D)
3.  **IA_Jump** (Digital)
4.  **IA_Dash** (Digital)
5.  **IA_Fire** (Digital)
6.  **IA_WeaponSwap1** through **IA_WeaponSwap6** (Digital)

**Bindings (BP_Player > Event Graph):**
*   **IA_Move**: `Move Input` -> `Add Movement Input` (World Direction).
*   **IA_Look**: `Add Controller Yaw Input` (X) + `Add Controller Pitch Input` (Y).
*   **IA_Jump**: `Jump` node.
*   **IA_Dash**: `Dash` function (custom, see below).
*   **IA_Fire**: `Fire` function.
*   **IA_WeaponSwap1-6**: `SwapWeapon` function (Index 1-6).

**Dash Implementation:**
*   Node: `Get Actor Forward Vector` -> `Multiply` (by `1000.0`) -> `Add Impulse` (on Character Movement).
*   *Constraint:* Dash has no cooldown in this spec (no stamina), but add a `0.5s` cooldown timer to prevent spam if desired. Spec says "no stamina", so allow continuous dash? *Correction:* Doom 2016 dash is a burst. Implement `0.5s` internal cooldown.

---

## 2. BP_Weapon Base + 6 Children

### BP_Weapon Base (Parent: Actor)
**Components:**
1.  **Static Mesh Component** (Weapon Model).
2.  **Point Light Component** (Optional, for muzzle flash).
3.  **Socket** (Muzzle Socket on Mesh).

**Variables (Instance):**
*   `FireRate` (Float, default `0.1`)
*   `Damage` (Float, default `10.0`)
*   `Spread` (Float, default `0.0`)
*   `ProjectileSpeed` (Float, default `3000.0`)
*   `IsHitscan` (Bool, default `True`)
*   `CurrentAmmo` (Int, default `0`)
*   `MaxAmmo` (Int, default `0`)
*   `WeaponIndex` (Int, 1-6)

**Logic: Fire (Event Graph)**
1.  **Check Game Time**: `Get Game Time Since Creation` (Store in `LastFireTime` variable).
2.  **Gate**: `If (CurrentTime - LastFireTime) > FireRate`:
    *   **Ammo Check**: `If CurrentAmmo > 0`:
        *   `Decrement CurrentAmmo`.
        *   **Branch on IsHitscan**:
            *   **True (Hitscan)**:
                *   `Line Trace Single by Channel` (Channel: `Visibility`, Start: Muzzle Location, End: Muzzle Location + Forward * 10000).
                *   `If Hit`:
                    *   `Apply Damage` (Hit Actor, `Damage`, `PlayerController`, `Hit Location`, `Hit Normal`).
                    *   `Spawn Particle` (Blood/Impact) at Hit Location.
            *   **False (Projectile)**:
                *   `Spawn Actor` (BP_Projectile, at Muzzle Location, Rotation: Muzzle Rotation).
                *   *Projectile BP*: Set `Initial Velocity` to `Forward * ProjectileSpeed`.
        *   **Audio**: `Play Sound 2D` (Fire Sound).
        *   **Update LastFireTime**: `Set LastFireTime = CurrentTime`.

**Why NO Reload Nodes Exist:**
*   Design Lock: "No reloads ever (instant, holding refires)".
*   Implementation: `CurrentAmmo` is only decremented. It is never reset to `MaxAmmo` via a reload action. Ammo is replenished solely via `BP_Pickup` overlap.
*   *Note:* If `CurrentAmmo` hits 0, weapon stops firing until pickup. No `Reload` input action exists.

### Weapon Children (Create 6 Blueprints inheriting BP_Weapon)
1.  **BP_Pistol** (Index 1): `FireRate` 0.2, `Damage` 15, `Spread` 0.5, `IsHitscan` True.
2.  **BP_Shotgun** (Index 2): `FireRate` 0.8, `Damage` 5 (per pellet), `Spread` 2.0, `IsHitscan` False (Spawn 8 pellets), `ProjectileSpeed` 2000.
3.  **BP_SMG** (Index 3): `FireRate` 0.05, `Damage` 8, `Spread` 1.0, `IsHitscan` True.
4.  **BP_Rifle** (Index 4): `FireRate` 0.15, `Damage` 25, `Spread` 0.1, `IsHitscan` True.
5.  **BP_Launcher** (Index 5): `FireRate` 1.2, `Damage` 100, `Spread` 0.0, `IsHitscan` False, `ProjectileSpeed` 1500.
6.  **BP_Plasmacaster** (Index 6): `FireRate` 0.1, `Damage` 40, `Spread` 0.0, `IsHitscan` False, `ProjectileSpeed` 3000.

*Note: Shotgun/Launcher/Plasma require `BP_Projectile` child classes with specific damage/radial impulse values.*

---

## 3. BP_Pickup Base + Children

### BP_Pickup Base (Parent: Actor)
**Components:**
1.  **Static Mesh Component** (Pickup Model).
2.  **Sphere Component** (Collision Preset: Overlap Only, Radius: 50.0).

**Variables:**
*   `PickupType` (Enum: Ammo, Health, Keycard_Green, Keycard_Red)
*   `Amount` (Int, default 1)

**Logic: Event BeginOverlap**
1.  `Get Overlapping Actor` -> `Cast to BP_Player`.
2.  `If Cast Success`:
    *   **Branch on PickupType**:
        *   **Ammo**: `Add to Player's Current Weapon Ammo` (Call Function on Player).
        *   **Health**: `Add Health` (Call Function on Player, `Amount`).
        *   **Keycard**: `Add Keycard` (Call Function on Player, `PickupType`).
    *   **Audio**: `Play Sound 2D` (Pickup Sound).
    *   **Destroy**: `Destroy Actor` (this).

### Children
1.  **BP_Ammo_Small** (Type: Ammo, Amount: 10)
2.  **BP_Ammo_Large** (Type: Ammo, Amount: 50)
3.  **BP_Health_Small** (Type: Health, Amount: 25)
4.  **BP_Health_Large** (Type: Health, Amount: 100)
5.  **BP_Keycard_Green** (Type: Keycard_Green, Amount: 1)
6.  **BP_Keycard_Red** (Type: Keycard_Red, Amount: 1)

*No Inventory UI. HUD reads Player variables directly.*

---

## 4. BP_Enemy Base + Lobster Brute

### BP_Enemy Base (Parent: Character)
**Components:**
1.  **Capsule Component** (Collision: Character).
2.  **Skeletal Mesh Component** (Enemy Model).
3.  **Perception Component** (Sight, Hearing).

**Perception Config:**
*   **Sight**: Range 2000, FOV 120, Loss Sight 2000.
*   **Hearing**: Range 1500.
*   **On Target Seen**: `Set State = Idle` -> `Set State = Telegraph`.

**State Machine (Variables: `CurrentState` Enum: Idle, Telegraph, Attack, Dead)**
*   **Idle**: Patrol/Stand. Wait for Perception.
*   **Telegraph**: `Set State = Telegraph`. Play `Telegraph Animation`. `Set Timer` (0.5s) -> `Set State = Attack`.
*   **Attack**: `Set State = Attack`. `Apply Damage` to Player (if in range) or `Fire Projectile`. `Set Timer` (1.0s) -> `Set State = Idle`.
*   **Dead**: `Disable Collision`, `Play Death Animation`, `Set Timer` (1.0s) -> `Gib`.

**Gib Function (Event Gib):**
1.  `Get Actor Location`.
2.  `Spawn Actor` (BP_GibChunk) x `GibCount` (e.g., 12).
3.  For each Gib:
    *   `Set Location` = Enemy Location.
    *   `Set Rotation` = Random Rotation.
    *   `Add Impulse At Location` (Radial: `Location` = Enemy Location, `Impulse Strength` = 5000, `Radius` = 500, `Falloff` = 1.0).
    *   *Note:* Use `Add Impulse` on Gib's `Physics Asset`.
4.  `Destroy Actor` (Enemy).

### BP_Lobster Brute (Child)
*   **Mesh**: Lobster Brute Skeletal Mesh.
*   **Damage**: 50.
*   **GibCount**: 15.
*   **Telegraph Time**: 0.8s.
*   **Attack Type**: Melee (Apply Damage if distance < 200).

---

## 5. BP_GibChunk (Parent: Actor)

**Components:**
1.  **Static Mesh Component** (Bone/Chunk Mesh).
2.  **Physics Asset** (Enabled, Simulate Physics: True).

**Variables:**
*   `Lifetime` (Float, default `4.0`)

**Logic:**
1.  **Event BeginPlay**: `Set Timer` (`Lifetime`) -> `FadeOut`.
2.  **FadeOut**: `Set Material Parameter` (Opacity) to `0.0` over `0.5s`.
3.  **End Fade**: `Destroy Actor`.

**Pooling Note (144 FPS):**
*   *Do NOT* destroy and spawn gibs constantly.
*   **Implementation**: Use `BP_GibPool` (Actor with `TArray<BP_GibChunk>`).
*   `Gib` function calls `Pool.GetGib()` -> `Reset Gib` (Location, Velocity, Opacity

<think>

</think>

**Gib function calls Pool.GetGib() -> Reset Gib (Location, Velocity, Opacity) -> Set Visibility (Visible) -> Add to World (via SpawnActorFromPool or direct reference if pre-spawned) -> Play Particle (Impact FX) -> Set Life Span (2.5s) -> On Life Span Ended: Set Visibility (Hidden) -> Return Gib to Pool (Push to Array).**

## 6. HUD Widget (WBP_HUD)

**Widget Tree Structure:**
*   **Canvas Panel** (Root)
    *   **Image** (Crosshair): Centered. Brush: Solid Color (White, Opacity 0.8). Size: 10x10.
    *   **Horizontal Box** (Bottom Left):
        *   **Text Block** (Health): Font: Roboto, Size 24, Color: Red (if <25), else White. Binding: `PlayerRef->GetHealth()`.
        *   **Spacer** (Width: 10).
        *   **Text Block** (Ammo): Font: Roboto, Size 24, Color: Cyan. Binding: `PlayerRef->GetAmmoCount()`.
    *   **Vertical Box** (Top Right):
        *   **Text Block** (Secret Counter): Font: Roboto, Size 18, Color: Gold. Binding: `PlayerRef->GetSecretCount() / 2`.
        *   **Image** (Secret Icon): Size: 20x20. Brush: Texture `T_Secret_Icon`.

**Event Graph Bindings:**
*   **Construct**:
    *   Get Player Controller -> Cast to BP_PlayerController -> Get Player Character (BP_Player) -> Store in Variable `PlayerRef`.
    *   Bind Text Block (Health) to `PlayerRef->GetHealth()`.
    *   Bind Text Block (Ammo) to `PlayerRef->GetAmmoCount()`.
    *   Bind Text Block (Secret Counter) to `PlayerRef->GetSecretCount()`.
*   **Tick**:
    *   *(No logic needed; bindings update automatically via Blueprint Variables if marked "Instance Editable" or using Dynamic Binding. For performance, ensure `GetHealth` etc. are simple getter functions, not complex calculations.)*
*   **PreConstruct**:
    *   Set Visibility (Crosshair) to Visible.
    *   Set Visibility (Bottom Left) to Visible.
    *   Set Visibility (Top Right) to Visible.

**Input Mapping Note:**
*   Ensure `BP_PlayerController` has Input Action "Fire" mapped to Left Mouse Button.
*   Ensure `BP_PlayerController` has Input Action "Move" mapped to WASD.
*   Ensure `BP_PlayerController` has Input Action "Jump" mapped to Space.

## 7. GameMode + Level Wiring

**BP_GameMode (Child of GameModeBase):**
*   **Class Defaults**:
    *   `DefaultPawnClass`: Set to `BP_Player`.
    *   `HUDClass`: Set to `WBP_HUD`.
    *   `PlayerControllerClass`: Set to `BP_PlayerController`.
    *   `EnemyClass`: Set to `BP_Enemy` (for generic spawning).
    *   `BruteClass`: Set to `BP_LobsterBrute` (for specific spawning).
*   **Event BeginPlay**:
    *   *(Optional: Initial spawn logic if not using Level Placed actors. Prefer Level Placed for blockout.)*

**Project Settings:**
*   **Maps & Modes**:
    *   `Game Default Map`: `M_Blockout01`.
    *   `Editor Startup Map`: `M_Blockout01`.
    *   `Game Mode Class`: `BP_GameMode`.

**Level Wiring (M_Blockout01):**
*   **Player Start**: Place `PlayerStart` actor at origin (0, 0, 100).
*   **Pickups**:
    *   Place 3 `BP_Pickup` (Health) actors in distinct corners.
    *   Place 2 `BP_Pickup` (Ammo) actors near weapon spawns.
    *   Place 1 `BP_Pickup` (Secret) actor hidden behind a wall (requires clipping or jump).
*   **Weapons**:
    *   Place 1 `BP_Weapon_Rifle` at spawn point.
    *   Place 1 `BP_Weapon_Shotgun` in mid-map room.
    *   Place 1 `BP_Weapon_Pistol` in back room.
*   **Enemies**:
    *   Place 5 `BP_Enemy` (Grunt) actors in mid-map corridors.
    *   Place 1 `BP_LobsterBrute` actor in the final room.
    *   *(Note: Enemies should be set to "Start Asleep" or use AI Controller to activate on sight. For blockout, manual activation via `BeginPlay` or Trigger Volume is acceptable.)*

**Spawn Rules (if dynamic spawning required later):**
*   Create `BP_Spawner` actor.
*   **BeginPlay**:
    *   Set Timer (5s) -> Call `SpawnEnemy` function.
    *   `SpawnEnemy`:
        *   Get Random Point from `NavMeshBoundsQuery`.
        *   Spawn Actor of Class `BP_Enemy` at Location.
        *   Set AI Controller.
        *   Set Target to Player.

## 8. Build Order Checklist

*   [ ] **Input Setup**:
    *   Create Input Actions: Move, Jump, Fire, Aim.
    *   Create Input Mapping Context: Default.
    *   Map Keys: WASD -> Move, Space -> Jump, LMB -> Fire, RMB -> Aim.
    *   Assign Context to `BP_PlayerController`.
*   [ ] **Player (BP_Player)**:
    *   Add Character Movement Component.
    *   Set Max Walk Speed: 600 uu/s.
    *   Add Mesh Component (Capsule or Character).
    *   Add Health Variable (Int, 100).
    *   Add Ammo Variable (Int, 30).
    *   Add Secret Count Variable (Int, 0).
    *   Implement `TakeDamage` event to reduce Health.
    *   Implement `GetHealth`, `GetAmmoCount`, `GetSecretCount` functions.
*   [ ] **Weapon (BP_Weapon + Children)**:
    *   Create `BP_Weapon` base class (Actor).
    *   Add Static Mesh Component.
    *   Add `Fire` function:
        *   Get Player Location.
        *   Get Player Forward Vector.
        *   Spawn Projectile (or TraceHit for hitscan).
        *   Decrement Ammo.
    *   Create 6 Children: Rifle, Shotgun, Pistol, SMG, Launcher, Minigun.
    *   Set distinct Fire Rates and Damage values.
    *   **No Reload Nodes**: Ensure `Fire` does not check for reload state; only checks Ammo > 0.
*   [ ] **Pickup (BP_Pickup)**:
    *   Create `BP_Pickup` (Actor).
    *   Add Static Mesh Component.
    *   Add Overlap Event (Player Character).
    *   On Overlap:
        *   Check Pickup Type (Enum: Health, Ammo, Secret).
        *   If Health: Increase Player Health (max 100).
        *   If Ammo: Increase Player Ammo.
        *   If Secret: Increase Player Secret Count.
        *   Destroy Self.
*   [ ] **Enemy (BP_Enemy + Lobster Brute)**:
    *   Create `BP_Enemy` (Character).
    *   Add AI Controller.
    *   Set Movement Speed: 400 uu/s.
    *   Add Health Variable (50).
    *   Implement `TakeDamage`:
        *   Reduce Health.
        *   If Health <= 0:
            *   Call `Gib` function.
            *   Destroy Self.
    *   Create `BP_LobsterBrute` (Child of BP_Enemy).
    *   Set Health: 200.
    *   Set Movement Speed: 300 uu/s.
    *   Scale Mesh: 1.5x.
*   [ ] **Gib (BP_GibChunk + Pooling)**:
    *   Create `BP_GibChunk` (Actor).
    *   Add Static Mesh Component (small fragment).
    *   Add Physics Asset.
    *   Set Life Span: 2.5s.
    *   Create `BP_GibPool` (Actor or Static Class).
    *   Initialize Pool with 20 `BP_GibChunk` actors (Hidden).
    *   Implement `GetGib` function:
        *   Pop from Array.
        *   If Empty: Spawn New.
        *   Reset Location/Velocity.
        *   Set Visible.
        *   Return Reference.
    *   Implement `ReturnGib` function:
        *   Set Hidden.
        *   Push to Array.
*   [ ] **HUD (WBP_HUD)**:
    *   Create Widget Blueprint.
    *   Add Crosshair Image.
    *   Add Health Text Block.
    *   Add Ammo Text Block.
    *   Add Secret Counter Text Block.
    *   Bind Text Blocks to Player Functions.
*   [ ] **GameMode (BP_GameMode)**:
    *   Set Default Pawn: `BP_Player`.
    *   Set HUD Class: `WBP_HUD`.
    *   Set Player Controller: `BP_PlayerController`.
*   [ ] **Level Wiring (M_Blockout01)**:
    *   Place Player Start.
    *   Place Pickups (3 Health, 2 Ammo, 1 Secret).
    *   Place
- Place Enemy Spawns
 (9 Proxies): Distribute 9 `BP_SpawnMarker_Proxy` actors across the map. Ensure 3 are in the main corridor, 2 in the side room, 2 near the pit, and 2 guarding the secret area. Set `bStartAsleep` to true for all.
- Place Keycard-Gated Secret Doors:
  - **Green Pillar Door**: Place `BP_Door_Green` at the pillar-top exit. Link `OnOpened` to `BP_Keycard_Reader_Green`. Set `bRequiresKeycard` to true.
  - **Red Pit Door**: Place `BP_Door_Red` at the pit edge. Link `OnOpened` to `BP_Keycard_Reader_Red`. Set `bRequiresKeycard` to true.
  - **Secret Counter**: Place `BP_Secret_Counter` in the HUD layer. Bind `OnSecretFound` from both doors to increment `CurrentSecrets`.
- **HUD Wiring**:
  - Add `Widget_HUD_Main` to `PlayerStart` via `PlayerController`.
  - Bind `BP_Pickup_Health` and `BP_Pickup_Ammo` `OnOverlap` events to HUD `AddHealth` and `AddAmmo` functions.
  - Bind `BP_Secret_Counter` `OnSecretFound` to HUD `UpdateSecretCount`.
  - Ensure `Widget_HUD_Main` is set to `Visibility: Visible` and `bIsFocusable: false`.
- **PIE Smoke Test**:
  - **Move Speed**: Verify player moves at exactly 600 uu/s. Check `CharacterMovement` `Max Walk Speed` in `BP_Player`.
  - **No Reload**: Confirm weapon does not stop firing when ammo runs out. Check `bAutoReload` is false and `bCanFire` remains true until empty.
  - **Instant Fire**: Verify `Fire` event triggers immediately on input. No cooldown delay. Check `FireRate` is 0.0s.
  - **Gibs Fly**: Spawn enemy, kill it. Verify gibs receive `RadialImpulse` (Force: 5000, Falloff: 0.5). Check `BP_Gib` `bSimulatePhysics` is true.
  - **Pickup Overlap**: Walk over Health/Ammo pickups. Verify HUD updates and pickup disappears. Check `bDestroyOnPickup` is true.
  - **Secret Counter**: Open Green Door. Verify HUD secret count increments to 1. Open Red Door. Verify count increments to 2.
- **Final Build Check**:
  - Run `Build` in Editor. Ensure no compile errors.
  - Check `Project Settings` > `Maps & Modes` > `Default Map` is `M_Blockout01`.
  - Verify `GameMode` is `GM_Blockout`.
  - Confirm `PlayerController` is `PC_Default`.
  - Ensure all `BP_` assets are saved and compiled.
  - Check `Level Instance` references are valid.
  - Verify `Lighting` is baked (if using Lumen, ensure `bUseLumen` is true).
  - Confirm `Audio` assets are linked correctly.
  - Ensure `Input` mappings are set in `Project Settings` > `Input`.
  - Verify `Game Instance` is `GI_Default`.
  - Check `Save Game` settings if applicable.
  - Ensure `Network` settings are correct for local play.
  - Confirm `Console Commands` are enabled for debugging.
  - Verify `Profiling` tools are accessible.
  - Check `Memory` usage is within limits.
  - Ensure `Performance` is acceptable on target hardware.
  - Confirm `Compatibility` with target platform.
  - Verify `Security` settings are appropriate.
  - Ensure `Legal` compliance is met.

- [ ] **Definition of Done**:
  - [ ] Character moves at **600 uu/s** floor with no stamina/sprint buttons
  - [ ] `grep -ri "reload" Content/` finds **zero** reload nodes — instant, hold-to-refire only
  - [ ] All **6 weapon children** fire: projectile speed **>= 3000 uu/s**
  - [ ] Pickups: overlap grants ammo/health/keycard, then destroys itself (no regen anywhere)
  - [ ] Lobster Brute gib test: radial impulse sends chunks flying, pool reuses them at 144 FPS budget
  - [ ] HUD shows crosshair, health, ammo counts, secret counter **0/2**
  - [ ] GameDefaultMap = **M_Blockout01**, PIE boots straight into the arena at PlayerStart south
