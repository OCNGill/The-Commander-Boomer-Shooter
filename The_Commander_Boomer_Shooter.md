# The Commander Boomer Shooter - LLM Assistant Prompt

You are helping build a fast-paced retro FPS called "The Commander" in Unity. This is a Duke Nukem meets Doom meets Mass Effect universe boomer shooter.

## Core Design
- **Movement**: Doom 2016, NOT Doom Eternal.  With a hint of Rise of the Triad meets 007 Goldeneye.
- **Weapons**: No reload animations. Instant weapon switching. Every gun should feel overpowered.
- **Health**: Classic pickups only. No regeneration.
- **Enemies**: Telegraphed attacks, satisfying gibs, no hitscan bullshit
- **Level Design**: Keycards, secrets, verticality. Some linearity, some side mazes.  Hazards (Pit Fall and Tomb Raider)

## Code Standards
- Movement speed starts at 15 units/second minimum
- Raw mouse input only
- 144+ FPS target
- Instant weapon switching (no animations)
- Screen shake + blood + gibs on every kill

## What You Should Generate
- Movement controllers with strafing
- Weapon scripts with high projectile speeds
- Enemy AI that's aggressive but fair
- One-liners like "Sudo kill -9, Noobs Detected, Commander STOMPED, ROBOT"
- Level blockouts with multiple routes
- Aim Down Site OK!
- Cover system OK

## What You Should NEVER Suggest
- Cover systems
- Stamina bars
- Realistic reload times
- RPG elements
- Tactical gameplay
- "Balance" over fun

## Example Code Pattern
```csharp
// Good weapon code
void FireRocket() {
    Instantiate(rocketPrefab, firePoint.position, firePoint.rotation);
    CameraShake.Instance.Shake(0.5f, 0.3f);
    AudioManager.Instance.PlaySound("BOOM");
}

// Bad weapon code - NO DELAYS
void FireRocket() {
    StartCoroutine(ReloadAnimation()); // WRONG
    yield return new WaitForSeconds(1.2f); // WRONG
}
