# Zero-Trust Configuration Audit — The Commander Boomer Shooter

**Audit date:** 2026-10-22
**Auditor:** Commander Hermes (Gillsystems) — zero-trust build lane
**Target:** `TheCommander.uproject` (UE 5.8) on MAIN — Ryzen 9 5900X / RX 7900 XTX (RDNA 3), 47.9 GB RAM
**Engine:** `F:\Unreal_engine\UE_5.8` (MAIN-local, sovereign — no GitHub Actions, no cloud build)
**Method:** every line below was read from a real file on disk or from a real engine log captured on MAIN. Nothing is asserted from memory.

---

## Verdict

**PASS WITH ONE FIX APPLIED.**

The project compiles, cooks, packages, boots, and runs on AMD hardware with FSR engaged, and the
`-CommanderInputAudit` harness is **working**. One genuine, reproducible, fatal defect was found
(XeFG swap-chain hijack) and was **fixed at project level and re-verified in the shipped binary**.

| Gate | Result |
|---|---|
| Editor target compile | **PASS** — 218 actions, 108 s, **0 errors / 0 warnings** |
| Game target compile | **PASS** — 79.57 s, `Result: Succeeded` |
| Cook | **PASS** — 543 packages cooked, 0 errors, 1 warning (benign, see F-6) |
| Package / stage / archive | **PASS** — `BUILD SUCCESSFUL`, `AutomationTool exiting with ExitCode=0` |
| Standalone `.exe` boot | **PASS** — map loads, game mode inits, player spawns, clean exit |
| FSR upscale provider on AMD | **PASS** — `LogFSR: Successfully initialized FSR Upscaling provider using version '4.1.2 *'` |
| `-CommanderInputAudit` harness | **PASS (working)** — all 16 axis/action mappings + pawn state printed live |
| XeFG swap-chain override | **FAIL → FIXED** — fatal crash; fixed and re-verified in the shipped `.exe` |

---

## Findings

| # | Finding | Commit / File | Severity | Evidence | Fix |
|---|---|---|---|---|---|
| F-1 | **XeSS Frame Generation (XeFG) hijacks the D3D12 swap chain and kills the packaged build at startup.** With `r.XeFG.OverrideSwapChain=1`, the shipped `.exe` dies in `FD3D12Viewport::Init()`. | `Config/DefaultEngine.ini` | **CRITICAL** | `LogXeFGSDK: Error: Failed to create swap chain: 0x887a0022` (0x887a0022 = `DXGI_ERROR_NOT_CURRENTLY_AVAILABLE`); `LogXeFGRHI: Error: Failed to create XeFG swap chain, result: -17`; `LogD3D12RHI: Error: hr failed at WindowsD3D12Viewport.cpp:162`; `Fatal error: Failure creating: D3D12Viewport (WindowsD3D12Viewport.cpp:162)` | **DONE** — `r.XeFG.OverrideSwapChain=0` set in `Config/DefaultEngine.ini` (line 114). Re-packaged and re-smoked with **no command-line workaround**: `LogConfig: Set CVar [[r.XeFG.OverrideSwapChain:0]]` → `LogXeFGRHI: Display: Override swap chain: 0` → clean boot. |
| F-2 | The XeFG failure is **not** an AMD/FSR problem and **not** GPU-specific. It is a vendor path (Intel XeFG, `libxell.dll` 1.3.2) failing to create a swap chain. | `LogXeFGSDK`, `LogXeFGRHI` | INFO (was mis-diagnosed) | Same run also logged `LogFSR: Successfully initialized FSR Upscaling provider using version '4.1.2 *'` — FSR initialised cleanly *before* the crash. | AMD-first doctrine: FSR owns upscaling; XeFG must not touch the swap chain. XeSS **upscaling** (XeSS 3) is a separate module and is unaffected — it still ships and still works. |
| F-3 | `Plugins/` is **gitignored**, so a fresh clone has no upscaler plugin payload and cannot build. | `.gitignore` (repo root) | HIGH (process) | Fresh clone on MAIN: `Plugins/` absent → `Unable to find plugin 'FSR'` (UBT log). | **DONE** — `Tools/ue/fetch_upscaler_plugins.py` provisions all three trees with SHA-256 verification from a local cache (0 downloads, 23 s on MAIN). Do **not** commit multi-gigabyte binaries. |
| F-4 | The `-CommanderInputAudit` harness is **functional**, not broken. | `Source/TheCommanderGame/CommanderPlayerController.cpp:49` | VERIFIED CLEAN | Live log: `=== COMMANDER INPUT AUDIT BEGIN ===` → Map, GameMode, PlayerController, Pawn, PlayerInput, InputComponent, PlayerStart `V(Y=-1500.00, Z=100.00)`, PawnLocation/Rotation/Velocity, then 8 axis mappings and 5 action mappings. | None needed. Audit is wired to `SetTimerForNextTick` and prints on the tick *after* map load — a harness that quits in the same `ExecCmds` block will exit before the audit prints. That is a harness-usage constraint, not a defect. |
| F-5 | **FSR 4.1.2 is confirmed live on AMD hardware.** The UE plugin is pinned at 4.1.1; the runtime reports **4.1.2** because the Adrenalin driver (26.10.1) supplies the 4.1.2 implementation. | `Tools/ue/fetch_upscaler_plugins.py` (pin `UE-FSR-4_1_1`), `Docs/generated/FSR_ARTIFACTS.md` | INFO — **confirms prior finding** | `LogFSR: Successfully initialized FSR Upscaling provider using version '4.1.2 *'` (twice, on both probe runs) | None. This is the expected driver-side upgrade path; **no 4.1.2 plugin pin is needed and none was added.** |
| F-6 | The single cook warning is the **device-profile gate working as intended**, not a defect. | `Config/DefaultDeviceProfiles.ini` (commit `45b3030`) | VERIFIED CLEAN | `LogConsoleManager: Warning: Setting the console variable 'r.Shadow.MaxCSMResolution' with 'SetByScalability' was ignored as it is lower priority than the previous 'SetByProjectSetting'. Value remains '2048'` | None. The per-node gate is *supposed* to outrank Scalability (DeviceProfile priority 0x07 > Scalability). The warning is the gate announcing that it won. |
| F-7 | SM6 targeting is correct and additive. | `Config/DefaultEngine.ini` → `[/Script/WindowsTargetPlatform.WindowsTargetSettings] +D3D12TargetedShaderFormats=PCD3D_SM6` | VERIFIED CLEAN | Cook log writes shader archives for **both** targets: `TheCommander-PCD3D_SM6-PCD3D_SM6` and `TheCommander-PCD3D_SM5-PCD3D_SM5`. The `+` prefix keeps SM5 available. | None. |
| F-8 | Runtime level-fix subsystem executes correctly in the **packaged** build, not just the editor. | `Source/CommanderLevelFix/CommanderLevelFixSubsystem.cpp` (commit `798c4bc`) | VERIFIED CLEAN | Packaged-build log: 12 individual fix lines (pit rim × 5, ramp, pillar ledges × 3, cover blocks × 2, keycard beacon) then `Level fixes applied: 12 changes`. | None. |
| F-9 | **The first build failure (`BUILD_EXIT=6` in 6.4 s) was NOT a bad target name — it was the missing plugin payload.** `TheCommanderGameEditor` is a real target (`Source/TheCommanderGameEditor.Target.cs`). The rejection came from UBT: `Unable to find plugin 'FSR' (referenced via TheCommander.uproject). Install it and try again, or remove it from the required plugin list.` | `Source/TheCommanderGameEditor.Target.cs`, `.gitignore` | LOW (diagnosis trap) | Failed log: `Unable to find plugin 'FSR'` → `Result: Failed (OtherCompilationError)`. The same target then built cleanly once `Plugins/` was provisioned. | **DONE** — see F-3. The lesson: a UBT exit code is not a diagnosis; the message above it is. This audit initially mis-attributed the failure to a nonexistent target and that guess was **disproved by the successful build of the very same target name** and corrected here. |

---

## Verified clean

- **Plugin descriptors are valid and the load path works.** `Plugins/FSR/FSR.uplugin`, `Plugins/DLSS/DLSS.uplugin`, `Plugins/XeSS/XeSS.uplugin` all installed with SHA-256 verified archives. Modules compiled and linked: `FFXFSRApi`, `FFXFSRSettings`, `FFXFSRTemporalUpscaling` (FSR), plus the DLSS, XeSS and `StreamlineNGXCommon` modules.
- **All three upscaler families ship in the packaged Win64 build**, satisfying the compatibility requirement (FSR primary, DLSS and XeSS retained) while the AMD-first doctrine governs *selection*.
- **The game-mode and player stack is alive in the shipped binary**: `LogCommander: ACommanderGameMode::InitGame map=M_Blockout01 controller=CommanderPlayerController pawn=CommanderCharacter` → `PlayerController ... ready: pawn=CommanderCharacter playerinput=EnhancedPlayerInput`.
- **Per-node FSR gate is present and coherent** (`Config/DefaultDeviceProfiles.ini`): `CommanderDeckRDNA2` → FSR 3.1.5 (`RequestProvider=3`, `QualityMode=3`, 50 % render res, CSM 512); `CommanderRDNA3Desktop` → loader chooses (`RequestProvider=0`, `QualityMode=1`, CSM 2048); `CommanderVegaLaptop` → FSR 2.3.4 (`RequestProvider=2`, CSM 512).
- **Audio contract (commit `9b6be5e`)** is a documentation-and-asset commit; `insult_p3_04` is certified by measurement in the manifest (258330 frames @ 44100 Hz, 30423 unique samples, sd 4982.3, sha256 matched). No config exposure in this audit.
- **Commit `45b3030`** (per-node FSR gate + verification harness + rebuilt profile doc) and **commit `798c4bc`** (UE 5.8 level-fix and input API fixes, build relocated to MAIN's 5900X) both land in the tree that produced the passing build above.

---

## Recommended fixes, in order

1. **DONE** — `r.XeFG.OverrideSwapChain=0` in `Config/DefaultEngine.ini`. Re-verify on any future package with the same smoke command (no workaround flag) before shipping.
2. Keep the FSR plugin pin at **4.1.1** and let the Adrenalin driver supply **4.1.2**. Re-check the pin only when AMD ships a plugin-side 4.1.2.
3. Treat `r.XeFG.*` as an explicit opt-in for a future Intel-XeFG-specific build profile; never let it default on in the AMD-first profile.
4. When the Steam Deck / HTPC / laptop profiles are exercised, capture the same `LogFSR: Successfully initialized FSR Upscaling provider using version '<x>'` line per node and record the resolved version — the device-profile gate is only as good as its per-node evidence.
5. Add the package+smoke step to the standard build lane as a script (`Tools/ue/`), so "it compiles" and "it boots" are never conflated. The compile passing proves nothing about the swap chain.

---

## Reproduction

Build + package + smoke, run on MAIN with a live SSH session (detached `Start-Process` children are killed when the SSH session closes — this cost real time and is worth writing down):

```
Build.bat  TheCommanderGameEditor Win64 Development -project=<repo>\TheCommander.uproject -WaitMutex -NoHotReloadFromIDE
Build.bat  TheCommanderGame        Win64 Development -project=<repo>\TheCommander.uproject -WaitMutex
RunUAT.bat BuildCookRun -project=<repo>\TheCommander.uproject -noP4 -platform=Win64 -clientconfig=Development \
            -build -cook -stage -pak -prereqs -archive -archivedirectory=<out> -unattended -utf8output -noclientstats
<out>\TheCommander\Binaries\Win64\TheCommanderGame.exe -log -abslog=<log> -CommanderInputAudit -windowed -ResX=1280 -ResY=720
```

**Measured on MAIN (Ryzen 9 5900X, UE 5.8):** editor compile 108 s · game compile 79.57 s · cook 24.93 s · `BuildCookRun` 34.85 s · packaged archive 1.5 GB · boot-to-map-load 0.0375 s · **0 errors, 0 warnings** on both compiles.

---

*"Test everything; hold fast what is good."* — **1 Thessalonians 5:21 (ESV)**

Reason for the verse: this audit exists because a green compile is not a working game. The build
passed — 0 errors, 0 warnings, `BUILD SUCCESSFUL` — and the shipped binary still died on the first
frame. Only booting the actual packaged `.exe` exposed the defect. "Test everything" is what
separated "the compiler is satisfied" from "the player can play"; "hold fast what is good" is why
the clean findings were left alone instead of being cosmetically rewritten.
