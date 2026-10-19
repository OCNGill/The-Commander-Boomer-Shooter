# Level 1 Bible: Plymouth Dark

**Project:** The Commander
**Engine:** Unreal Engine 5.8 (Lumen + Nanite)
**Target FPS:** 144+
**Core Mechanics:** Doom 2016 Movement (600 uu/s base), No Reloads, No Stamina, Pickup-Only Ammo.
**Theme:** Plymouth, MA. 1920s industrial decay meets Eldritch horror.

## 1. Beat Sheet

| Beat | Phase | Purpose | Lighting/Ambience |
| :--- | :--- | :--- | :--- |
| **1** | **Entry** | Establish scale, introduce movement feel. Player enters from South. | Dim industrial floodlights (20% intensity). Wet concrete floor reflections. Sound: Distant foghorns, dripping water. |
| **2** | **Horror Beat** | Tension building. Isolate player. Force caution. | Single flickering bulb (10% intensity) near central pillar. Fog density 40%. Sound: Low-frequency drone (30Hz), wet breathing. |
| **3** | **Arena Eruption** | High-octane combat. Introduce enemy variety. Clear space for mobility. | Sudden bright strobe (100% intensity, 15Hz pulse) on activation. Red emergency lights. Sound: Heavy metal riff, industrial machinery clanking. |
| **4** | **Keycard Hunt** | Vertical traversal challenge. Reward risk-taking. | Neon green glow (Green Keycard) on pillar. Red glow (Red Keycard) in SW pit. Sound: Electrical hum, lobster clicking. |
| **5** | **Escalation** | Transition to boss arena. Clear remaining trash mobs. | Lights dim to 50%. Blue tint. Sound: Deep rumble, stone cracking. |
| **6** | **Boss: Nor-Easter Titan** | Finale. Test all mechanics. Massive scale. | Dynamic lighting based on boss attacks (fire/ice). High contrast. Sound: Thunderous roars, shattering glass. |

## 2. Encounter Rationale

### Enemy Placement Logic
*   **Rock Golem (NE Platform/Rock Ramp):**
    *   **Why:** Acts as a static obstacle and early verticality gate. Forces player to approach from the side or jump over.
    *   **Aggro Telegraph:** 1.5s wind-up (glowing orange veins) before slam. 0.8s recovery window.
    *   **Placement:** Blocks direct path to NE platform. Must be jumped over or killed.
*   **Lobster Brute (SW Hazard Pit):**
    *   **Why:** High-risk/high-reward. Pit is 5m deep. Brute sits on a 2m ledge.
    *   **Aggro Telegraph:** 1.0s claw raise, emitting a loud *snap*.
    *   **Placement:** Red Keycard is on a crate 3m behind the Brute. Player must engage or bypass via narrow 1.5m gap on the side.
*   **Trash Mobs (Arena Center/Cover Blocks):**
    *   **Why:** Keep player moving. Prevent camping.
    *   **Aggro:** Instant on sight (15m range). Fast, low HP.
    *   **Placement:** Spawn in pairs near cover blocks.

### Aggro System
*   **Visual:** Enemy eyes glow white (neutral) -> red (aggro).
*   **Audio:** Unique "alert" sound for each type (Golem: stone grind; Brute: claw snap).
*   **Range:** 15m visual, 20m audio.

## 3. Secret Design

### Secret 1: The Loose Brick
*   **Location:** Behind the Central Pillar, North face.
*   **Geometry Hint:** A single brick is slightly protruding (2uu offset). Hovering near it changes cursor to "Interact."
*   **Interaction:** Press E. Brick pops out, revealing a 1x1m alcove.
*   **Reward:** 100 Health, 100 Armor, 1 Rocket.
*   **Gating:** None. Available from Beat 1.

### Secret 2: The Pit Bottom
*   **Location:** SW Hazard Pit, bottom center.
*   **Geometry Hint:** A subtle green light pulse (0.5s cycle) visible from the pit edge if looking down.
*   **Interaction:** Jump into pit (no damage from fall). Navigate to a 1x1m platform behind the Brute’s spawn point.
*   **Reward:** Green Keycard (Alternative route to pillar) OR 200 Health (if Green already taken).
*   **Gating:** Requires Red Keycard to open the side door if player wants to exit via NE, but pit is open. *Correction:* Pit is open. Secret is purely traversal. Reward: 2 Rockets + 1 BFG Cell.

## 4. Verticality + Mobility Notes

*   **Base Speed:** 600 uu/s.
*   **Jump Height:** 250 uu (approx 2.5m).
*   **Double Jump:** 150 uu additional (if equipped with "Fog Strider" pickup, found in Secret 1).
*   **Dash:** 1.2s cooldown, 1.5x speed for 0.5s.
*   **Wall Jump:** 1.8x jump height when hitting wall at 45-degree angle.

### Key Traversal Paths
1.  **PlayerStart to Central Pillar:** 15m straight. No obstacles.
2.  **Pillar to NE Platform:** 8m gap. Requires double jump or dash+jump. Rock Golem blocks direct jump.
3.  **NE Platform to Red Keycard (SW Pit):** 20m diagonal. Requires wall-running along NE wall (1.5m height) to reach pit edge.
4.  **Pit to Green Keycard (Pillar Top):** 5m drop. Requires wall jump off pit wall (1.8m) to reach pillar base, then climb 2m pillar.

## 5. Metrics Checklist for UE Blockout Pass

### Dimensions
*   **Door Widths:** Minimum 120 uu (1.2m) for player. 150 uu (1.5m) for Golem.
*   **Corridor Heights:** Minimum 200 uu (2m) for standard corridors. 250 uu (2.5m) for arenas.
*   **Cover Heights:** 60-110 uu (0.6-1.1m). Must allow player to peek over (eye level 80 uu).
*   **Pillar Dimensions:** 4x4x4m (400x400x400 uu).
*   **Pit Depth:** 5m (500 uu). Walls 1m (100 uu) thick.

### Performance Targets
*   **Draw Calls:** < 2000 per frame.
*   **Triangle Count:** < 100k visible.
*   **Lighting:** Lumen GI enabled. Max 5 dynamic lights per sector.
*   **Collision:** Use simplified convex hulls for cover blocks. No complex mesh collision for static geometry.

### Validation Checks
1.  Can player jump from PlayerStart to first cover block? (Yes, 2m jump).
2.  Can player see Green Keycard from PlayerStart? (Yes, 15m line of sight).
3.  Does Rock Golem block the jump to NE platform? (Yes, 8m gap, Golem at 4m mark).
4.  Is the pit exit clear? (Yes, 1.5m gap on side).
5.  Are all secrets accessible without breaking level geometry? (Yes).

## Appendix: Asset List
*   **Floor:** Wet concrete, reflective.
*   **Walls:** Brick + metal grating.
*   **Cover:** Wooden crates, metal barrels.
*   **Props:** Fog machine, industrial pipes, rusty chains.
*   **VFX:** Green/Red keycard glows, Golem fire, Lobster ice.