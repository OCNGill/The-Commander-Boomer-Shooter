# The Commander: Combat Tuning & Economy

## 1. Weapon Statistics Table

| Weapon | Fire Rate (rps) | Type / Speed (uu/s) | Damage (per hit/pellet) | Pellets / Spread (deg) | Ammo Type | Max Carry | Pickup Refill | Primary Role / Target |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Pilgrim Puckle** | 12.0 | Hitscan / ∞ | 12 | 1 / 0.0 | Light | 300 | 30 | Primary; Drills, Zealots |
| **Sextant Scattergun** | 1.8 | Hitscan / ∞ | 14 | 10 / 4.5 | Heavy | 24 | 24 | Close-Range; Brutes, Golems |
| **Barnacle Blunderbuss** | 0.9 | Projectile / 3000 | 22 | 12 / 8.0 | Heavy | 12 | 12 | Mid-Range; Anti-Zealot, Phantom |
| **Rockhopper Rail** | 0.5 | Projectile / 5000 | 85 | 1 / 0.0 | Rail | 10 | 10 | Anti-Brute, Anti-Golem |
| **Harbor Wreck Rocket** | 0.8 | Projectile / 3500 | 120 (direct) / 60 (splash) | 1 / 0.0 | Rocket | 8 | 8 | AoE; Boss, Groups |
| **Mayflower Cannon** | 0.4 | Projectile / 4000 | 250 | 1 / 0.0 | Heavy | 6 | 6 | Boss; Titan Phase 1/2 |

*Note: All weapons use instant hold-to-refire. No reload mechanic. Pickups restore full max carry for that ammo type.*

## 2. Ammo Economy Math

**Assumptions:**
*   **Pace:** 144 FPS target, 600 uu/s movement.
*   **Arena Size:** 4000uu x 4000uu.
*   **Enemy Count:** 9 Total (3 Barnacle, 2 Zealot, 1 Phantom, 1 Brute, 1 Golem, 1 Titan).
*   **Wave Interval:** 15 seconds between encounter markers.
*   **Ammo Box Spawn:** Every 30 seconds (2 boxes per wave interval).
*   **Box Yield:** 1 box = 20% of total ammo pool for all types.

**Total Ammo Pool Calculation (Full Clear):**
*   **Light (Puckle):** 300 max. Estimated usage: 150 rounds (12.5% of pool).
*   **Heavy (Scatter/Blunder/Cannon):** 24+12+6 = 42 max. Estimated usage: 20 rounds (47% of pool).
*   **Rail:** 10 max. Estimated usage: 4 rounds (40% of pool).
*   **Rocket:** 8 max. Estimated usage: 3 rounds (37% of pool).

**Sustainability Check:**
*   **Time to Clear:** ~90 seconds (9 enemies * ~10s TTK avg).
*   **Boxes Spawned:** 3 boxes (at 0s, 30s, 60s).
*   **Total Ammo Available:**
    *   Light: 300 (start) + 3*60 (boxes) = 480.
    *   Heavy: 42 (start) + 3*8 (boxes) = 66.
    *   Rail: 10 (start) + 3*2 (boxes) = 16.
    *   Rocket: 8 (start) + 3*1.6 (boxes) = 12.8.
*   **Verdict:** Player has ~1.5x the ammo required for a standard clear. This allows for "spray and pray" early on, but forces weapon switching for efficiency against Brutes/Golems. If player misses 50% of shots, they will run dry by the Titan fight, requiring careful ammo management.

## 3. Damage-per-Enemy TTK Table

**Base HP Values (Neutral Difficulty):**

| Enemy | HP | Recommended Weapon | TTK (sec) | Notes |
| :--- | :---: | :--- | :---: | :--- |
| **Barnacle Drone** | 36 | Pilgrim Puckle | 0.30 | 3 hits. Fast kill. |
| **Pilgrim Zealot** | 120 | Pilgrim Puckle | 1.00 | 10 hits. Use scatter if swarmed. |
| **Mayflower Phantom** | 200 | Barnacle Blunderbuss | 1.11 | 9 hits (blunder) or 17 hits (puckle). Blunder preferred for range. |
| **Lobster Brute** | 450 | Rockhopper Rail | 0.53 | 5 hits. Scatter (32 hits) is too slow. |
| **Rock Golem** | 600 | Rockhopper Rail | 0.71 | 7 hits. Cannon (2.4s) is alternative. |
| **Nor-Easter Titan** | 2000 | Mayflower Cannon | 3.20 | 8 hits. Phase 2 requires Rocket support. |

**Boss: Nor-Easter Titan Multi-Phase Note:**
*   **Phase 1 (0-50% HP):** Standard 2000 HP. Use Mayflower Cannon. TTK ~3.2s.
*   **Phase 2 (Storm Surge, 50-0% HP):** HP does not reset, but shield regenerates 10 HP/s if not hit. Storm surge projectiles (speed 2000 uu/s) spawn every 2s.
    *   *Strategy:* Switch to Harbor Wreck Rocket for splash damage to clear projectiles and chip shield. Use Mayflower Cannon for direct hits.
    *   *Adjusted TTK:* ~5.0s (due to shield regen and projectile dodging).
    *   *Ammo Cost:* 4 Rockets + 4 Cannons.

## 4. Difficulty Knobs (Variables)

Expose these as float variables in `GameplaySettings.ini` or Blueprint:

1.  **`EnemyHPScalar`** (Default: 1.0)
    *   *Effect:* Multiplies all enemy HP.
    *   *Easy:* 0.75 | *Hard:* 1.5 | *Nightmare:* 2.0
    *   *Impact:* Directly increases TTK. At 2.0, Puckle TTK vs Drone becomes 0.6s.

2.  **`ProjectileSpeedScalar`** (Default: 1.0)
    *   *Effect:* Multiplies projectile speed for Blunderbuss, Rail, Rocket, Cannon.
    *   *Easy:* 1.2 (faster travel, easier to hit) | *Hard:* 0.8 (slower travel, lead shots required)
    *   *Impact:* Affects hit detection accuracy for projectiles. Hitscan unaffected.

3.  **`PickupSpawnMultiplier`** (Default: 1.0)
    *   *Effect:* Multiplies the amount of ammo restored per pickup.
    *   *Easy:* 1.5 (30% refill per box) | *Hard:* 0.75 (15% refill per box)
    *   *Impact:* Controls ammo scarcity. At 0.75, player must conserve ammo or face weapon switch exhaustion during Titan fight.

4.  **`EnemyFireRateScalar`** (Default: 1.0)
    *   *Effect:* Multiplies enemy attack speed.
    *   *Easy:* 0.8 | *Hard:* 1.2
    *   *Impact:* Affects player dodge windows. Higher scalar reduces reaction time for projectile dodges (e.g., Titan's storm surge).

5.  **`DamageResistanceScalar`** (Default: 1.0)
    *   *Effect:* Multiplies enemy damage resistance to specific weapon types.
    *   *Usage:* Set to 0.5 for Brute against Scattergun (halves damage) to force Rail usage.
    *   *Impact:* Enforces weapon variety. Without this, players may over-rely on one weapon.

**Implementation Note:**
*   Apply `EnemyHPScalar` and `DamageResistanceScalar` in `EnemyHealthComponent`.
*   Apply `ProjectileSpeedScalar` in `ProjectileMovementComponent` initialization.
*   Apply `PickupSpawnMultiplier` in `AmmoPickup::OnBeginOverlap`.
*   Apply `EnemyFireRateScalar` in `EnemyAIController::FireWeapon`.