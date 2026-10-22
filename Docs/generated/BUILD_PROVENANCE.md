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

### Second validation: LAPTOP (integrated AMD Radeon — the "I'll try it on the laptop" case)

| Field | Value |
|---|---|
| Host | Laptop — Windows 10, AMD Ryzen 5 4500U, 19.4 GB physical RAM, 15.3 GB free |
| GPU | **AMD Radeon(TM) Graphics** (integrated) — driver 31.0.21923.11000 |
| Reported capability | **Feature Level 12_1 · shader model 6.7** · binding tier 3 · wave ops · atomic64 — all supported |
| RHI decision | `LogRHI: RHI D3D12 with Feature Level SM6 is supported and will be used.` |
| Boot | **PASS** — `LogInit: Display: Engine is initialized` |
| Map | **PASS** — `LoadMap: /Game/Maps/M_Blockout01` |
| Player | **PASS** — `ACommanderGameMode::InitGame map=M_Blockout01 … pawn=CommanderCharacter` → `PlayerController … ready` |
| FSR | **PASS** — `LogFSR: FSR swapchain provider registered` |
| DLSS | Correctly skipped — `LogStreamlineD3D12RHI: Skip registering IDXGISwapchainProvider (kFeatureDLSS_G)` (no NVIDIA GPU) |
| **Fatals** | **NONE** |
| Exit | Clean — `LogExit: Exiting.` |
| Cost | ~187 s wall, dominated by SM6 PSO compilation on a CPU iGPU (`PSOPrecacheState: Missed` — the package ships **no pipeline cache**) |

**What this proves:** the shipped `.exe` is not a MAIN-only artefact. It runs on a second, much weaker
AMD machine with no dedicated GPU, selects SM6 correctly, initialises FSR, loads the map, spawns the
player and exits clean. The XeFG fix is not machine-specific.

**Known gap:** the package contains no `TheCommander_PCD3D_SM6.stable.upipelinecache`, so every first
run pays a full SM6 shader compile. On a desktop GPU that is a few seconds; on a CPU iGPU or a
Steam Deck APU it is minutes. **Shipping a cooked PSO/pipeline cache is the next build-lane
improvement**, and it matters most for the Deck.

### Third target: STEAM DECK — this artefact is not the Deck deliverable, and here is why

| Finding | Evidence |
|---|---|
| Package transferred | **1.5 GB** → `/home/deck/AI/TheCommander_Win64` (both `TheCommanderGame.exe` and `TheCommander/Binaries/Win64/TheCommanderGame.exe` present) |
| Deck GPU | `AMD Custom GPU 0405 (RADV VANGOGH)` = **RDNA 2, Vulkan/RADV live** |
| Proton available | `Proton 11.0` and `GE-Proton7-28` both installed |
| X/Wayland | **SOLVED** — `DISPLAY=:0`, `WAYLAND_DISPLAY=wayland-0`, `XAUTHORITY=/run/user/1000/xauth_iabMRX` (99 bytes) |
| **BLOCKER 1 — prefix** | `Proton: Error while copying to ".../pfx/drive_c/windows/system32/amdxcffx64.dll": No such file or directory` — Proton 11.0-100 cannot build a fresh prefix on this Deck |
| **BLOCKER 2 — memory** | Deck total 14,804 MB; **only ~1,360 MB available**; **4,866 MB already swapped**. Consumers: `llama-server` 1.0 GB RSS, python 187 MB, konsole 102 MB, kwin 77 MB |
| **BLOCKER 3 — the decisive one** | This build is **D3D12**. Under Proton that means **vkd3d-proton** — and UE5 + vkd3d is the known-broken class: Proton supports D3D9–D11 well, D3D12 via vkd3d is experimental and is **not a supported UE5 target** |

**Verdict: the Windows D3D12 build is not the Steam Deck deliverable.** The Deck needs a **native
Linux/Vulkan build** of the same C++ project, cooked and packaged for Linux, run natively.

**What that requires — and which half is not mine to execute:**

| # | Requirement | Owner |
|---|---|---|
| 1 | **UE 5.8 for Linux** — Epic Games Launcher install, or the GitHub engine source (GitHub account linked to Epic). Both require an Epic login. | **Commander** — I cannot authenticate to Epic |
| 2 | **A Linux build box with RAM headroom.** The Deck has 16 GB unified but ~1.4 GB free with inference live. The HTPC has 11 GB total / ~1 GB available and 706 GB free on ZFS — disk is fine, RAM is not. A UE Linux cook+package wants 16 GB+. Stopping the Deck inference window is a human action under the window-owns-inference rule. | **Commander** (kill the window) |
| 3 | Linux/Vulkan cook + package on the chosen box, ship to the Deck, run natively, re-run the same smoke gate. | **Hermes** — fully autonomous once 1 and 2 clear |

**Required on every target regardless:** ship a cooked **PSO / pipeline cache**. The package contains
no `TheCommander_PCD3D_SM6.stable.upipelinecache`, so the first run on any CPU iGPU/APU pays a full
shader compile (measured **~187 s** on the laptop). On a Steam Deck APU that is minutes *per launch*
until the cache exists.

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
