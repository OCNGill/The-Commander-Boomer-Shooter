# Build Provenance — The Commander Boomer Shooter (Win64 Standalone)

Append-only ledger of sovereign packaged builds. The 1.5 GB package itself is
**never committed** (`Packaged/` is gitignored) — this file is the receipt.

---

## BUILD-2026-10-22-01 — Win64 Development standalone (AMD / FSR verified)

| Field | Value |
|---|---|
| Build host | **MAIN** — `GillsystemsMain@10.0.0.164` |
| CPU | AMD Ryzen 9 5900X (12C/24T) |
| GPU | AMD Radeon RX 7900 XTX (RDNA 3) |
| RAM | 47.9 GB |
| OS | Windows 11 |
| Engine | `F:\Unreal_engine\UE_5.8` (MAIN-local, sovereign — no GitHub Actions) |
| Source commit | `0a82700` (game repo `main`, pushed to `github.com/OCNGill/The-Commander-Boomer-Shooter`) |
| Upscaler plugins | FSR (UE-FSR 4_1_1), DLSS, XeSS — installed and SHA-256 verified, `Tools/ue/fetch_upscaler_plugins.py` |
| Game target | `TheCommanderGame` Win64 Development |
| Cook | 543 packages · 0 errors · 1 warning (device-profile gate by design) |
| Package | `BUILD SUCCESSFUL` · `AutomationTool exiting with ExitCode=0` · 34.85 s `BuildCookRun` |
| Editor compile | 218 actions · 108 s · **0 errors / 0 warnings** |
| Game compile | 79.57 s · `Result: Succeeded` |
| Package size | 1,515.6 MB (82 files) |
| `TheCommanderGame.exe` | 344,881,152 bytes (328.9 MB) |
| **exe sha256** | `ba51d650993ea82bf8e91d61d62d9988c1f731e2ccce56284a3adf1fb8602f38` |
| Content pak | `TheCommander/Content/Paks/TheCommander-Windows.pak` — 10.7 MB |
| Local path | `The_Commander_Boomer_Shooter\Packaged\Win64\` (repo, gitignored) |
| Review path | `C:\Users\Gillsystems Laptop\Desktop\TheCommander_Win64_v0.1.0` (junction → same bytes, one physical copy) |

### Runtime verdict (smoke test of the **shipped** `.exe`, no workarounds)

| Check | Result |
|---|---|
| Boot | **PASS** — `LogInit: Display: Engine is initialized` |
| Map load | **PASS** — `LogLoad: LoadMap: /Game/Maps/M_Blockout01?Name=Player` |
| Game mode | **PASS** — `ACommanderGameMode::InitGame map=M_Blockout01 controller=CommanderPlayerController pawn=CommanderCharacter` |
| Player | **PASS** — `PlayerController ... ready: pawn=CommanderCharacter playerinput=EnhancedPlayerInput` |
| Level fixes | **PASS** — 12 runtime changes applied (pit rim × 5, ramp, pillar ledges × 3, cover blocks × 2, keycard beacon) |
| **FSR on AMD** | **PASS** — `LogFSR: Successfully initialized FSR Upscaling provider using version '4.1.2 *'` |
| XeFG | **DISABLED BY DESIGN** — `r.XeFG.OverrideSwapChain=0`; XeSS *upscaling* unaffected |
| Input audit | **PASS** — `-CommanderInputAudit` prints map, game mode, controller, pawn, `PlayerInput`, `InputComponent`, `PlayerStart V(Y=-1500.00, Z=100.00)`, pawn transform, 8 axis + 5 action mappings |
| Exit | Clean — `LogExit: Exiting` (exit code 0) |

### Notes

- **FSR 4.1.2 is live; the UE plugin stays pinned at 4.1.1.** The 4.1.2 implementation is supplied by
  the **Adrenalin driver (26.10.1)** — driver-side, exactly as the FSR research concluded. No 4.1.2 plugin
  pin was added and none is needed.
- **The one cook warning is correct behaviour**, not a defect: `r.Shadow.MaxCSMResolution` set by
  `SetByScalability` is outranked by `SetByProjectSetting` — that is the per-node device-profile gate
  (`Config/DefaultDeviceProfiles.ini`, commit `45b3030`) doing its job.
- **`Plugins/` is gitignored.** A fresh clone has no upscaler payload and cannot build. Provision first:
  `python Tools/ue/fetch_upscaler_plugins.py` (SHA-256 verified; runs from a warm local cache).
- **Detached builds die.** `Start-Process` children are killed when the SSH session closes — run the
  build lane over a **live** SSH session.
- Reproduce with: `Tools\ue\package_and_smoke_win64.bat` (builds, cooks, packages, boots the shipped
  `.exe`, and prints a machine-readable verdict).

---

*"Test everything; hold fast what is good."* — 1 Thessalonians 5:21 (ESV)

Reason for the verse: this build compiled clean — `BUILD SUCCESSFUL`, zero errors, zero warnings — and
the shipped binary still died on the first frame. Only booting the actual packaged `.exe` exposed it.
This ledger exists so that the receipt of every build is a *tested* fact, not a compiler's opinion.
