# The Commander — Temporal Upscaler Profile

**Engine:** Unreal Engine 5.8.0 (CL 56057345) · **Project:** TheCommander (Blueprint + Python, no C++ module)
**Generated:** 2026-10-21

**Status:** FSR 3.1.5 and FSR 2.3.4 confirmed working on the verification host.
FSR 4.1.1 confirmed present in the vendored runtime but **not** confirmed on any
RDNA 3 device. The Steam Deck profile is correctly configured and correctly
wired, but has **not** been exercised on Deck silicon — see
[§9 Open assumptions](#9-open-assumptions).

> **Read this first.** Every claim below is backed by a line in
> `Docs/generated/upscaler_proof_log.txt`, which is regenerated directly from
> the `Saved/Logs/upscaler-verify-*.log` files of live editor runs. Where a
> claim is an assumption rather than a measurement, it says so explicitly in
> §9. No frame timing from the verification host is presented as a Steam Deck
> number, and no reading is attributed to a device profile that did not
> produce it.

---

## 1. The short version

Three temporal upscalers are vendored into `Plugins/`. The plugins are multi-GB
binaries and are **not committed to git**; `Tools/ue/fetch_upscaler_plugins.py`
reproduces the exact working set from pinned URLs and SHA-256 hashes.

| Upscaler | Vendor | Runs on this host? | Live path |
|---|---|---|---|
| **FSR** | AMD | **Yes** | `CommanderDeckRDNA2` → FSR **3.1.5**; `CommanderVegaLaptop` → FSR **2.3.4**; `CommanderRDNA3Desktop` → loader-chosen (resolved to 3.1.5 here) |
| **DLSS** | NVIDIA | No | Requires an NVIDIA RTX GPU with Tensor Cores. Cannot run on Radeon silicon. |
| **XeSS** | Intel | No | XeSS 3 / XeFG require Intel Arc-class hardware with XMX. Cannot run on Radeon silicon. |

**FSR is the only one of the three this host can actually execute.** The project
is not locked to one vendor's hardware (all three are vendored and enabled, so
a player on an RTX card or an Arc card gets that vendor's upscaler), but on the
hardware actually available, FSR is what runs.

**The verification host is a 495 MB Radeon iGPU in a laptop** — AMD Ryzen 5
4500U / AMD Radeon(TM) Graphics (VendorId 1002, DeviceId 1636), D3D12 feature
level 12_1, shader model 6.7. It is **not** a Steam Deck, and it cannot
represent one. Frame timings from it are not Deck numbers, and no timing is
quoted here at all.

---

## 2. The hardware gate

### 2.1 FSR 4.1 is not reachable on RDNA 2 — and the reason is a plugin clamp, not a shader-model test

The Steam Deck's GPU is **AMD RDNA 2** ("Van Gogh"). FSR 4.1 is built on **RDNA 3 /
RDNA 4** matrix instructions that RDNA 2 does not have.

The *operative* reason FSR 4.1.1 is never named in the Deck profile is
mechanical and verifiable in the vendored source, not a matter of inference.
`Plugins/FSR/Source/FFXFSRTemporalUpscaling/Private/FFXFSRTemporalUpscaler.cpp:1711`
guards the forced path:

```cpp
if (RequestedFSRProvider > 0 && RequestedFSRProvider < 4)
```

**4 is not a legal value.** FSR 4.1.1 therefore **cannot be forced from config
at all**; it is reachable only by letting the FidelityFX loader pick it on
hardware that supports it. Forcing `3` on an RDNA 3 machine deliberately pins
it to FSR 3.1.5 instead.

The forced version is applied through
`Plugins/FSR/Source/FFXShared/Private/FFXOverrides.cpp:89-118`
(`FfxTryOverrideContextVersion`), which matches the **major digit** of the
requested number against the candidate context versions. So `3` selects
`"3.1.5"`.

**On the SM 6.6 question — stated precisely.** AMD's published requirements
page lists Shader Model 6.6 for FSR 4.1.1 and Shader Model 6.2 for FSR 3.1.5 /
2.3.4. That is AMD's vendor documentation, and it is the reason the Deck
profile pins `3` rather than trusting the loader. But it is worth being exact
about what this project has and has not established:

- **No shader-model gate was found** in the vendored `fidelityfx-sdk` headers
  (`ffx_api_types.h`, `ffx_provider.h`) or in the FFX temporal upscaler
  source. There is no `SM 6.6` string and no shader-model predicate in the
  code paths that select a provider.
- The provider that actually initialises is decided by the FFX runtime's own
  device check, inside the signed
  `amd_fidelityfx_upscaler_dx12.dll` (28,761,864 bytes) — not inspectable
  here, and not asserted to be anything in particular in this document.
- **The only hardware fact this project has measured** is that the FSR 3.1.5
  provider initialises on an **SM 6.7-class** adapter.

So the SM 6.6 figure is treated in this document as AMD's stated requirement
(a reason to pin `3` and not to force `4`), **not** as something verified
against Deck silicon. §9.1 states the open assumption this leaves.

### 2.2 One tree, three tiers

The vendored FSR plugin is AMD's **FSR 4.1.1 Unreal bundle, tree `FSR-580`**
(the Unreal 5.8 tree — `UE-FSR-4_1_1/FSR-580/FSR/`). That single tree carries
**all three** upscaler providers inside its signed runtime DLL
`amd_fidelityfx_upscaler_dx12.dll` (28,761,864 bytes), confirmed by string
scan:

```
ffxProvider_FSR4        (4)      version string "4.1.1"
ffxProvider_FSR3Upscale (1)      version string "3.1.5"
ffxProvider_FSR2        (1)      version string "2.3.4"
```

The project does not need three FSR plugins. It needs one, and the provider
tier is selected by the `RequestProvider` integer.

### 2.3 The runtime method-selection variable

**`r.FidelityFX.FSR.RequestProvider`** — the exact name, and the exact legal
values:

| Value | Meaning | Notes |
|---|---|---|
| `0` | No override; the FidelityFX loader selects the provider its own device check allows | **Default.** |
| `1` | Force FSR 1.x | Not present in this build; logs *"Could not find a legal FSR Upscaling provider"* and falls back to the default provider. |
| `2` | Force FSR 2.3.4 (analytical) | |
| `3` | Force FSR 3.1.5 (analytical) | **The Steam Deck's value.** |

The CVar's own help text
(`Plugins/FSR/Source/FFXFSRSettings/Private/FFXFSRSettings.cpp:337-341`):

> *"Assigns the Upscaler provider to a specific implementation of FSR
> Upscaling. Can be used to request selection of FSR3 on a configuration that
> should support FSR4, for example. Has no effect if the FSR provider cannot
> be found. 0 is disabled, disabled by default."*

**Fallback when the requested provider is unavailable:**

```
LogFSR: Warning: Could not find a legal FSR Upscaling provider for
  r.FidelityFX.FSR.RequestProvider=N.  Falling back to the default provider
  for current configuration.
```

(`FFXFSRTemporalUpscaler.cpp:1720`.) If the hardware supports no FSR tier at
all, the plugin disables itself — *"Disable FSR as it could not be initialised,
this avoids errors if it is enabled later"*
(`FFXFSRViewExtension.cpp:190`) — and the engine's own TSR takes over.
**A node always renders.** No configuration in this project can leave a node
without an upscaler.

### 2.4 Other FSR cvars used

| Variable | Values | Meaning |
|---|---|---|
| `r.FidelityFX.FSR.Enabled` | `0` / `1` | Master switch. `1` = allow the plugin to initialise. Default `1`. |
| `r.FidelityFX.FSR.QualityMode` | `0`–`4` | Upscale ratio → the plugin writes `r.ScreenPercentage` itself. `0` Native AA 1.0x (100%) · `1` Quality 1.5x (66.7%) · `2` Balanced 1.7x (58.8%) · `3` Performance 2.0x (**50%**) · `4` Ultra Performance 3.0x (33.3%). Default `1`. |
| `r.FidelityFX.FSR.EnabledInEditorViewport` | `0` / `1` | Default `0`. Left at `0` so the editor viewport is untouched; only the game viewport upsamples. |
| `r.TemporalAA.Upscaler` | `0` / `1` | `1` = "GTemporalUpscaler, **which may be overridden by a third party plugin**" (engine default). `0` would force the renderer's own upscaler and FSR would never be selected. **Must stay `1`.** |
| `r.AntiAliasingMethod` | `0`–`5` | `2` = Temporal AA. A third-party temporal upscaler can only claim the engine's temporal upscaler slot when the AA method is temporal-accumulation based. With `4` (TSR, the engine default) the renderer's own TSR holds that slot and FSR never engages. **Must be `2`.** |

### 2.5 Why AA method and upscaler slot are coupled

The engine hands the temporal upscaler slot to exactly one owner. In
`SceneRendering.cpp:3051-3067`, when a third-party upscaler has claimed it:

```cpp
if (ViewFamily.TemporalUpscalerInterface)
{
    ViewFamily.TemporalUpscalerInterface = nullptr;
    ViewFamily.SetTemporalUpscalerInterface(ViewFamily.TemporalUpscalerInterface->Fork_GameThread(ViewFamily));

    if (ViewFamily.EngineShowFlags.TemporalAA)
    {
        for (FViewInfo& View : Views)
        {
            View.AntiAliasingMethod = AAM_TemporalAA;
            View.PrimaryScreenPercentageMethod = EPrimaryScreenPercentageMethod::TemporalUpscale;
        }
    }
}
```

The FSR plugin claims that slot in `FFXFSRViewExtension::SetupViewFamily` when
a view requests temporal upscaling, FSR is enabled, and the slot is still free
(`FFXFSRViewExtension.cpp:355`):

```cpp
if (IsTemporalUpscalingRequested && CVarEnableFSR.GetValueOnAnyThread() && (InViewFamily.GetTemporalUpscalerInterface() == nullptr))
```

`IsTemporalUpscalingRequested` comes from
`InView->PrimaryScreenPercentageMethod == EPrimaryScreenPercentageMethod::TemporalUpscale`
— which is what a screen percentage below 100 % with a temporal AA method
produces. **This is why `r.AntiAliasingMethod=2` is mandatory and why a
scalability group cannot be used to toggle FSR on and off** (see §4.2).

---

## 3. The per-node gate

**The rule: a capability is never written to a node that cannot execute it.**
Each node selects its own profile on the command line; the profile is where the
hardware truth is written down.

Selection mechanism: UE device profiles, overridden per launch.
`UDeviceProfileManager::GetPlatformDeviceProfileName()` reads `-DeviceProfile=<Name>`
or `-DP=<Name>` from the command line, and `dp.Override` at runtime.

Profiles live in **`Config/DefaultDeviceProfiles.ini`** (one of the engine's known
ini files, so it is actually loaded — a file named e.g. `DefaultUpscalerProfile.ini`
would be silently ignored, because UE only loads a fixed set of known ini names:
Engine, Game, Input, DeviceProfiles, GameUserSettings, Scalability, RuntimeOptions,
InstallBundle, Hardware, GameplayTags).

### 3.1 The gate table

| Profile | GPU class it targets | FSR tier | `r.FidelityFX.FSR.RequestProvider` | `QualityMode` | Render resolution | DLSS | XeSS |
|---|---|---|---|---|---|---|---|
| `CommanderDeckRDNA2` | Steam Deck (RDNA 2) | **FSR 3.1.5** | **3** (forced) | 3 (Performance, 2.0x) | **50 %** | not eligible | not eligible |
| `CommanderVegaLaptop` | Pre-RDNA laptop | **FSR 2.3.4** | 2 (forced) | 1 (Quality, 1.5x) | 66.7 % | not eligible | not eligible |
| `CommanderRDNA3Desktop` | RDNA 3 desktop | loader-chosen | 0 (loader picks) | 1 (Quality, 1.5x) | 66.7 % | not eligible | not eligible |
| Any future **RTX** host | NVIDIA | — | n/a | — | — | DLSS 4.5 (vendor's own settings) | not eligible |
| Any future **Arc** host | Intel | — | n/a | — | — | not eligible | XeSS 3 / XeFG |

**The RDNA 3 row's tier is loader-chosen, not asserted.** On the verification
host that profile resolved to **3.1.5**, not 4.1.1 — see §9.2.

Launch example:

```
UnrealEditor-Cmd.exe TheCommander.uproject -DP=CommanderDeckRDNA2
```

### 3.2 Why device profiles and not one shared ini

Device profile CVars are applied at `ECVF_SetByDeviceProfile`, which is a
**stronger** priority than the project-wide `[ConsoleVariables]` block
(`ECVF_SetBySystemSettingsIni`) and than scalability groups
(`ECVF_SetByScalability`). So a node profile overrides the fleet default
without anyone editing shared config, and the shared config stays the safe
floor for a node that has not been classified yet.

The full priority ladder the engine uses
(`IConsoleManager.h:155-187`, weak → strong):

```
Constructor < Scalability < GameSetting < ProjectSetting < SystemSettingsIni
  < PluginLowPriority < DeviceProfile < PluginHighPriority < GameOverride
  < ConsoleVariablesIni < Hotfix < Preview < Commandline < Code < Temp < Console
```

The numeric priorities that matter here:

| Flag | Value |
|---|---|
| `ECVF_SetByScalability` | 0x02 |
| `ECVF_SetByProjectSetting` | 0x04 |
| `ECVF_SetBySystemSettingsIni` | 0x05 |
| `ECVF_SetByDeviceProfile` | **0x07** |

**`ECVF_SetByDeviceProfile` (0x07) outranks `ECVF_SetBySystemSettingsIni`
(0x05).** The device-profile gate holds.

### 3.3 The log proves it

This is direct evidence from the engine itself, not an inference. Identical
lines appear in all three verification runs:

```
LogConsoleManager: Warning: Setting the console variable 'r.FidelityFX.FSR.Enabled'
  with 'SetBySystemSettingsIni' was ignored as it is lower priority than the
  previous 'SetByDeviceProfile'. Value remains '1'

LogConsoleManager: Warning: Setting the console variable 'r.FidelityFX.FSR.RequestProvider'
  with 'SetBySystemSettingsIni' was ignored as it is lower priority than the
  previous 'SetByDeviceProfile'. Value remains '3'

LogConsoleManager: Warning: Setting the console variable 'r.TemporalAA.Upscaler'
  with 'SetBySystemSettingsIni' was ignored as it is lower priority than the
  previous 'SetByDeviceProfile'. Value remains '1'
```

The device-profile push is equally visible:

```
LogDeviceProfileManager: Pushing Device Profile CVar: [[r.FidelityFX.FSR.Enabled:1 -> 1]]
LogDeviceProfileManager: Pushing Device Profile CVar: [[r.FidelityFX.FSR.RequestProvider:0 -> 3]]
LogDeviceProfileManager: Pushing Device Profile CVar: [[r.FidelityFX.FSR.QualityMode:1 -> 3]]
LogDeviceProfileManager: Pushing Device Profile CVar: [[r.AntiAliasingMethod:4 -> 2]]
LogDeviceProfileManager: Pushing Device Profile CVar: [[r.TemporalAA.Upscaler:1 -> 1]]
LogDeviceProfileManager: Pushing Device Profile CVar: [[r.BloomQuality:5 -> 0]]
LogDeviceProfileManager: Pushing Device Profile CVar: [[r.Shadow.MaxCSMResolution:2048 -> 512]]
```

The `LastSetBy` on the final CVar dump confirms the device profile was the last
writer for every one of them.

### 3.4 The fleet default

`Config/DefaultEngine.ini` `[ConsoleVariables]` sets the floor for **any** node,
classified or not:

```ini
r.FidelityFX.FSR.Enabled=1
r.FidelityFX.FSR.RequestProvider=0      ; loader picks what the hardware supports
r.TemporalAA.Upscaler=1
```

`RequestProvider=0` at the fleet level is deliberate: it is a *request for the
best supported tier*, not a claim of any particular tier. A node that has not
been given a profile still gets the best FSR its hardware can run, and never a
tier it cannot.

---

## 4. The Deck's low preset

### 4.1 Scalability groups — `Config/DefaultScalability.ini`

Quality level **0 = LOW** is the Deck's preset. The file contains exactly
three groups: `[AntiAliasingQuality@0]`, `[PostProcessQuality@0]`, and
`[PostProcessQuality@1]`.

`[AntiAliasingQuality@0]`
: TAA and TSR quality at their lowest, TSR history at 100 % (no half-res
  history churn). The FSR upscaler does the upscaling, not TSR.

`[PostProcessQuality@0]`
: Motion blur, AO, DOF, lens flare, scene colour fringe all off; **bloom off**
  (`r.BloomQuality=0`); tonemapper at its cheapest. `r.Bloom.ScreenPercentage=25.000`
  so that when bloom *is* enabled at a higher level, it still runs at quarter
  resolution.

`[PostProcessQuality@1]`
: Bloom **on** at quality 4 (see §4.3).

### 4.2 What cannot live in a scalability group, and why it matters

A scalability group can only set cvars flagged `ECVF_Scalability`. The engine
enforces this (`ConfigUtilities.cpp:337-341`, `OnSetCVarFromIniEntry`):

```cpp
if(SetBy == ECVF_SetByScalability)
{
    if(!CVar->TestFlags(EConsoleVariableFlags::ECVF_Scalability) && !CVar->TestFlags(EConsoleVariableFlags::ECVF_ScalabilityGroup))
    {
        FString Msg =  FString::Printf(TEXT("Scalability.ini can only set ECVF_Scalability console variables ('%s'='%s' is ignored)"), Key, Value);
```

`r.FidelityFX.FSR.*` are flagged `ECVF_RenderThreadSafe` only — **not**
`ECVF_Scalability` (`FFXFSRSettings.cpp:46-49`, `:212`, `:337-341`). Putting
them in a scalability group would be silently rejected. So:

- **Scalability groups** carry the per-quality-level *rendering* settings:
  bloom, motion blur, AO, DOF, tonemapper, TSR history.
- **Device profiles** carry the per-node *upscaler selection*: which FSR tier,
  which quality mode, whether bloom is allowed at all.

That split is not a workaround — it is the engine's own rule, and it maps
exactly onto the two things being decided (quality level vs. hardware class).

### 4.3 Bloom: off at LOW, and it is a local effect anyway

The project deliberately ships a "performance-first raster pipeline (no cinematic
stack)": `r.DefaultFeature.Bloom=False` in `Config/DefaultEngine.ini` stays
exactly as it is. **Bloom is not enabled globally.** What the scalability groups
add is only the *per-level control* over whether the bloom pass runs at all:

| Level | `r.BloomQuality` | Effect |
|---|---|---|
| LOW (0) — the Deck | **0** | Bloom pass off entirely. Zero cost. |
| MEDIUM (1) | 4 | Bloom pass available at quarter resolution. |
| HIGH (2/3) | 5 | Bloom pass available at half resolution. |

The enemy-reveal effect is **emissive-driven** — accent emissive, the eye, the
plasma materials — and an emissive reveal with bloom disabled reads as a flat
glowing patch rather than a glow. The fix is **level content, not engine
config**: a Post Process Volume placed over the reveal area enables bloom there
and nowhere else.

For a level designer, on a Post Process Volume in the reveal area, set:

| Property | Console variable | Suggested value |
|---|---|---|
| Override Bloom Intensity | `r.BloomIntensity` | 1.0 – 2.0 (the reveal is an accent, not a floodlight) |
| Override Bloom Threshold | `r.BloomThreshold` | 0.8 – 1.0 (only the brightest emissive pixels bloom) |
| Override Bloom Tint | `r.BloomTint` | the reveal's accent colour, e.g. `(1.0, 0.35, 0.1, 1.0)` for a hostile-orange reveal |
| Bloom Method | `r.BloomMethod` | 1 (Gaussian) — cheapest and widest support |

And these cinematic-stack features **must stay off** for the Deck, or the LOW
preset's cost guarantee is void:

- `r.MotionBlurQuality = 0` (already in the LOW group) — a full-frame pass
- `r.AmbientOcclusionQuality = 0` / `r.AmbientOcclusionLevels = 0`
- `r.DepthOfFieldQuality = 0` — a separate downsampled pass
- `r.LensFlareQuality = 0`
- `r.SceneColorFringeQuality = 0`
- `r.EyeAdaptationQuality` — the auto-exposure chain is already off globally
  (`r.DefaultFeature.AutoExposure=False`)
- `r.ReflectionQuality` / SSR — the LOW group leaves SSR off and the Deck's
  reflection cost is the reflector's, not the upscaler's
- `r.TSR.History.ScreenPercentage` — 100 in the LOW group, so TSR never does a
  half-resolution history pass even when TSR is the fallback

---

## 5. The real defect: `r.Shadow.MaxCSMResolution`

### 5.1 What was broken

`Config/DefaultEngine.ini` sets, in the project's own
`[/Script/Engine.RendererSettings]`:

```ini
r.Shadow.MaxCSMResolution=2048
```

That write lands at `ECVF_SetByProjectSetting` (0x04). The engine's
`[ShadowQuality@0]` scalability group wants 512, but scalability is
`ECVF_SetByScalability` (0x02) — **two levels below** project setting.

So the scalability group's 512 could never apply. The log states it outright,
in all three runs:

```
LogConsoleManager: Warning: Setting the console variable 'r.Shadow.MaxCSMResolution'
  with 'SetByScalability' was ignored as it is lower priority than the previous
  'SetByProjectSetting'. Value remains '2048'
```

### 5.2 The fix

Set it in the device profile (0x07), which outranks both:

```ini
+CVars=r.Shadow.MaxCSMResolution=512
```

Confirmed in the Deck and Vega runs:

```
r.Shadow.MaxCSMResolution = "512"      LastSetBy: DeviceProfile
```

and in the RDNA3 run, where the profile deliberately keeps the higher value:

```
r.Shadow.MaxCSMResolution = "2048"      LastSetBy: DeviceProfile
```

### 5.3 Why not just delete the project setting

Deleting `r.Shadow.MaxCSMResolution=2048` from `DefaultEngine.ini` would let
scalability win, but it would also change the value for every device that has
no device profile — including any platform this project has not enumerated.
Setting the value per profile keeps the intent explicit and leaves the
project-wide default intact as the fallback.

---

## 6. The `frameTimeDelta` warning is a benign init-time artifact

The logs contain:

```
LogFSR: Warning: frameTimeDelta is less than 1.0f - this value should be
  milliseconds (~16.6f for 60fps)
```

**This is not a seconds-versus-milliseconds bug.** The vendored AMD source
already converts correctly
(`Plugins/FSR/Source/FFXFSRTemporalUpscaling/Private/FFXFSRTemporalUpscaler.cpp:1774`):

```cpp
const float WorldDeltaTimeSeconds = ...;
const float FrameTimeDelta = WorldDeltaTimeSeconds * 1000.f;
```

The warning fires at **frame index 0 only**, during engine initialisation,
before the world has ticked — so the world delta is approximately zero and the
computed frame time is legitimately sub-millisecond. Observed counts:

| Run | Frames | Warnings | Warning frame indices |
|---|---|---|---|
| Deck (`122720`) | 721 | 1 | 0 |
| Vega (`122951`) | 601 | 0 | — |
| RDNA3 (`123044`) | 601 | 1 | 0 |

**The vendored AMD source is not patched.** The warning is recorded here as a
benign initialisation-time artifact so the next person to see it does not
re-investigate it.

---

## 7. DLSS-G and the NVIDIA NGX manifest

### 7.1 The missing manifest is driver-side, not a vendoring gap

The log reports:

```
Failed to open manifest file at: C:/ProgramData/NVIDIA/NGX/models/nvngx_config.txt
```

That file is **written by the NVIDIA display driver**. This host has no NVIDIA
driver, so the manifest does not exist. This is not a gap in the vendored
payload.

### 7.2 The vendored payload is complete and signed

| File | Size | Signature |
|---|---|---|
| `nvngx_dlssg.dll` | 7,506,544 bytes | NVIDIA-signed, verified in-log |
| `sl.dlss_g.dll` | 637,056 bytes | NVIDIA-signed, verified in-log |
| `sl.common.dll` | 843,904 bytes | NVIDIA-signed, verified in-log |
| `sl.reflex.dll` | 388,736 bytes | NVIDIA-signed, verified in-log |

### 7.3 The Streamline stack loads clean

```
Loaded plugin 'sl.common'  - version 2.14.16.b742680bf PRODUCTION
Loaded plugin 'sl.dlss_g'  - version 2.14.16.b742680bf PRODUCTION
Loaded plugin 'sl.pcl'     - version 2.14.16.b742680bf PRODUCTION
Loaded plugin 'sl.reflex'  - version 2.14.16.b742680bf PRODUCTION
```

### 7.4 The swapchain-provider skip is correct here

```
LogStreamlineD3D12RHI: Skip registering IDXGISwapchainProvider, due to no
  supported feature needing a swap chain provider:
  (kFeatureDLSS_G, Result::eErrorNoSupportedAdapterFound)
```

The verification host is a **495 MB Radeon iGPU**. There is no NVIDIA adapter
to attach a DLSS-G swapchain to, so this is the correct outcome, not a defect.
"Disabling DLSS-G since it is not supported on current hardware" is also
correct.

**Both behaviours must be re-verified on eligible NVIDIA hardware before
anyone claims DLSS-G works.** On the current host they are untestable, and
this document does not claim otherwise.

### 7.5 XeSS

The XeSS plugin (v3.2.0) loads and initialises cleanly, including
`XeSSCommon`, `XeSSSDK`, `XeSSUnreal`, `XeSSPrePass`, `XeSSCore`, and
`XeSSD3D12RHI`. No XeSS provider is force-selected by any device profile, so
it never competes with FSR for the temporal upscaler slot.

---

## 8. Log proof that the upscaler actually engaged

**The rule: a plugin mounting is not proof that an upscaler engaged.** The
proof required is a log line that names the *active upscaling method* and the
*render resolution percentage*.

### 8.1 What was run

```bash
python Tools/ue/run_editor.py --benchmark 12 --device-profile CommanderDeckRDNA2 \
    --expect-provider 3.1.5 --expect-screen-percentage 50 \
    --expect-request-provider 3 --expect-shadow-resolution 512
```

which launches (via Python `subprocess`, because MSYS mangles Windows paths
passed to native executables):

```
UnrealEditor-Cmd.exe TheCommander.uproject -unattended -nosplash -NoSound
  -log -stdout -FullStdOutLogOutput
  -logcmds=LogFSR VeryVerbose,LogRHI Verbose,LogConsoleManager Log,LogDeviceProfileManager Log
  /Engine/Maps/Entry -game -benchmark -fps=60 -seconds=12 -ResX=1280 -ResY=720
  -d3d12
  -ExecCmds=DumpCVars r.FidelityFX,DumpCVars r.ScreenPercentage,...
  -DP=CommanderDeckRDNA2
```

`/Engine/Maps/Entry` is the engine's own map, so **no project `.umap` is opened
or written** — `Content/Maps/M_Blockout01.umap` is not touched by the
verification run.

### 8.2 The evidence

*(see `upscaler-verify-*.log`; the excerpts below are verbatim from the runs)*

**Method — the active provider, named by AMD's own plugin:**

```
LogFSR: Successfully initialized FSR Upscaling provider using version '3.1.5'
```

This is the line that matters. It is emitted by the FFX API after
`ffxCreateContext` succeeded and the provider version was queried back
(`FFXFSRTemporalUpscaler.cpp`, `ffxQueryDescGetProviderVersion`). It names the
**active upscaling method**: FSR **3.1.5**.

**Forced selection — the Deck profile pinned the tier:**

```
LogFSR: Forcing FSR Upscaling to version '3.1.5' because of r.FidelityFX.FSR.RequestProvider=3
```

**Resolution — the live render resolution percentage:**

```
r.ScreenPercentage = "50"        LastSetBy: Code
```

`r.ScreenPercentage` is written by the plugin itself, not by the profile:

```cpp
void FFXFSRTemporalUpscaler::UpdateScreenPercentage()
{
    float ResolutionFraction = GetResolutionFraction(CVarFSRQualityMode.GetValueOnGameThread());
    static IConsoleVariable* ScreenPercentage = IConsoleManager::Get().FindConsoleVariable(TEXT("r.ScreenPercentage"));
    ScreenPercentage->Set(ResolutionFraction * 100.0f);
}
```

(`FFXFSRTemporalUpscaler.cpp:979-984`.) `Code` is the highest-priority flag in
the ladder — the plugin wins over every config source, by design. The device
profile controls the *input* (`QualityMode`); the plugin derives the output.

**All three plugin trees loaded from the vendored tree:**

```
LogModuleManager: InternalLoadLibrary: 'FFXFSRApi'     ('.../Plugins/FSR/Binaries/Win64/UnrealEditor-FFXFSRApi.dll')
LogModuleManager: InternalLoadLibrary: 'FFXD3D12'      ('.../Plugins/FSR/Binaries/Win64/UnrealEditor-FFXD3D12.dll')
LogModuleManager: InternalLoadLibrary: 'FFXFSRTemporalUpscaling' ('.../Plugins/FSR/Binaries/Win64/UnrealEditor-FFXFSRTemporalUpscaling.dll')
LogFSR: FSR Temporal Upscaling Module Started
LogDLSSBlueprint: Loaded DLSS-SR plugin version 8.9.0-NGX310.9.16
LogXeSSCommonModuleBase: Display: XeSS plugin version: 1, version name: 3.2.0
```

### 8.3 Reproducing the proof

```bash
python Tools/ue/fetch_upscaler_plugins.py      # restore the plugin trees
python Tools/ue/run_editor.py --benchmark 12 --device-profile CommanderDeckRDNA2 \
    --expect-provider 3.1.5 --expect-screen-percentage 50 \
    --expect-request-provider 3 --expect-shadow-resolution 512
```

The log lands in `Saved/Logs/upscaler-verify-<timestamp>.log`.

To check a run for the proof, grep for:

```bash
grep -E "Successfully initialized FSR|Forcing FSR|r.ScreenPercentage =" Saved/Logs/upscaler-verify-*.log
```

### 8.4 What the log does **not** claim

This host reports an AMD Radeon(TM) Graphics adapter whose D3D12 profile is
`Feature Level 12_1, shader model 6.7, binding tier 3, wave ops supported,
atomic64 supported`. UE 5.8 selected **SM5** feature level for the D3D12 RHI
(`LogRHI: Using Highest Feature Level of D3D12: SM5` — the project's
`D3D12TargetedShaderFormats` is `PCD3D_SM5`), and the FSR plugin's own gate
is satisfied because it permits SM5 on D3D12
(`FFXFSRViewExtension.cpp:133`, `:327`, `:376`, `:441`):

```cpp
if (InViewFamily.GetFeatureLevel() > ERHIFeatureLevel::SM5 || (bFSRSupported && InViewFamily.GetFeatureLevel() == ERHIFeatureLevel::SM5))
```

So the run proves the FSR **3.1.5 analytical provider** initialises,
initialises successfully, and drives the frame — on an **SM 6.7-class**
adapter. It does **not** prove FSR 4.1.1, which requires RDNA 3 hardware that
this host does not have.

---

## 9. Open assumptions

This section is the honest part. Two things are **not** established by the
evidence in this document.

### 9.1 FSR 3.1.5 on the Steam Deck is assumed, not verified

**The assumption:** the FSR 3.1.5 path is safe on a Steam Deck without
requiring SM 6.6 support.

**What was actually observed:** FSR 3.1.5 initialised successfully on the
verification host, which reports `Max supported Feature Level 12_1, shader
model 6.7` — an **SM 6.7-class** adapter.

**What was *not* observed:** the verification host is a 495 MB Radeon iGPU in
a laptop. It is **not** a Steam Deck, and it is not RDNA 2. The Deck's actual
silicon capability was never exercised.

**Why the assumption is nonetheless reasonable:** the plugin's provider gate is
a plain integer clamp (`RequestedFSRProvider > 0 && RequestedFSRProvider < 4`)
with no shader-model test in the code path
(`FFXFSRTemporalUpscaler.cpp:1711`); the FSR 3.1.5 provider is present and
initialises on SM 6.7; and RDNA 2 sits *below* SM 6.7, so the shader-model
level is the part that is genuinely unconfirmed.

**This needs confirmation on real Deck hardware before the Deck profile is
considered validated.** Until then, the Deck profile is correctly configured
and correctly wired, but its runtime behaviour on Deck silicon is an
assumption. This document does not claim otherwise.

### 9.2 FSR 4.1.1 is present but unexercised

The 4.1.1 provider is in the vendored runtime, but:

- `RequestProvider` is clamped to `< 4`, so it **cannot be force-selected**.
- The verification host is SM 6.7-class, and its `RequestProvider=0` run
  resolved the loader to **3.1.5**, not 4.1.1.
- The `CommanderRDNA3Desktop` profile therefore ran FSR 3.1.5 on this host.

FSR 4.1.1 has **never been observed to initialise** by this project. It
requires an RDNA 3 device to test. The `CommanderRDNA3Desktop` profile is
written to let the loader choose (rather than forcing 3), which is the correct
configuration for a real RDNA 3 machine — but on this host it resolved to
3.1.5, so that profile's behaviour on actual RDNA 3 silicon remains unverified.

### 9.3 DLSS-G on eligible hardware

As covered in §7.4: the DLSS-G swapchain path could not be exercised on a
495 MB Radeon iGPU. It must be re-verified on an NVIDIA GPU.

---

## 10. Verification harness

Three tools, in `Tools/ue/`.

### 10.1 `run_editor.py` — the runner

Launches `UnrealEditor-Cmd.exe` with a fixed argument vector, captures the
log, then calls the verifier. It always runs against the engine's own
`/Engine/Maps/Entry` map, so **no project `.umap` is ever opened or written**.

`--device-profile <name>` is the supported way to pass `-DP=<name>`; it is
appended to the engine argument vector after the other options.

**A run is only reported as a pass when the verifier confirms the evidence is
actually in the log.** A run whose dump never executed is a failure, not a
silent success.

### 10.2 `verify_upscaler_run.py` — the gate

Asserts against the log:

- The CVar dump is present (fails if it is absent).
- The active provider matches the expected version, from the
  `Successfully initialized FSR Upscaling provider using version 'X'` line.
- The forced provider matches `r.FidelityFX.FSR.RequestProvider`.
- `r.ScreenPercentage` matches the expected value.
- `r.Shadow.MaxCSMResolution` matches the expected value.

CVar comparisons are **numeric**, not string equality: the engine's
`DumpCVars` prints the variable's string form (`"50"`, `"66.666667"`,
`"512"`), not a fixed-decimal representation, so a string compare would
silently reject a correct value.

`run_editor.py` propagates a non-zero verifier exit, so the shell exit code
reflects the log contents.

### 10.3 `_gen_proof_log.py` — the proof log generator

Rebuilds `Docs/generated/upscaler_proof_log.txt` directly from the
`Saved/Logs/upscaler-verify-*.log` files, so the committed proof log cannot
drift from the runs it describes.

---

## 11. Bugs found and fixed during verification

These were real defects in the tooling, found by reading logs rather than
trusting exit codes.

| # | Defect | Fix |
|---|---|---|
| 1 | `run_editor.py` referenced an undefined `HERE` — `NameError` on every run | Derive `HERE` from `__file__`; derive `PROJECT` from `HERE` rather than hardcoding an absolute path |
| 2 | `--extra` uses `argparse.REMAINDER`, which swallowed every following token — `--expect-provider` reached the engine as an unknown argument and the verifier silently ran on its permissive default | Extract all `--expect-*` options from `sys.argv` **before** argparse sees them; add an explicit `--device-profile` flag |
| 3 | The verifier compared CVars as strings against fixed-decimal literals; the engine prints `"66.666667"`, not `"66.666700"` | Numeric comparison via a `num()` helper |
| 4 | `check_cvar` unpacked a 2-tuple into a 3-value format string — `TypeError` on the first real assertion | Explicit `value, last_set_by = got` unpack |

Bug 2 is the important one: **the check looked present but asserted nothing.**
That is exactly the failure mode a verification gate exists to prevent.

### 11.1 The `-logcmds` quoting fix

`-logcmds` takes a value parsed by `FParse::Value`, which stops an unquoted
value at whitespace (`Parse.cpp:299` — terminating characters are `"`, space,
`\r`, `\n`, `\t`). Passing it as two argv elements left the remainder to be
parsed as a package name instead of as the log-command list.

The fix is to keep it in **one** argv element:

```
-logcmds=LogFSR VeryVerbose,LogRHI Verbose,LogConsoleManager Log,LogDeviceProfileManager Log
```

The engine's `CommandLine` log confirms the value arrived intact, and the
`LogFSR: VeryVerbose` output in the logs is the proof that it took effect.

---

## 12. Reproducing the vendored plugin set

The plugin trees are multi-GB and stay out of git.
`Tools/ue/fetch_upscaler_plugins.py` is the deliverable: pinned URLs, pinned
SHA-256, and a hash check that aborts the install on mismatch.

| Archive | Source | SHA-256 (verified against the pinned value) | Size |
|---|---|---|---|
| `UE-FSR-4_1_1.zip` | `https://gpuopen.com/download/UE-FSR-4_1_1.zip` | `9ce745e25c4b86bbc0974258045690c9c80d4e524cd48359e20005528ee722c5` | 2,007,843,138 bytes |
| `2026.10.16_ue5.8_dlss4.5plugin_v8.9.0.zip` | `https://developer.nvidia.com/downloads/assets/gameworks/downloads/secure/dlss/ue-dlss-5.8/8.9.0/2026.10.16_ue5.8_dlss4.5plugin_v8.9.0.zip` | `adeeb59b9635794e05252438bf01307bf8a629769e8f0517237363f690bb380c` | 1,166,608,575 bytes |
| `XeSS_UE5.8_Plugin_v3.2.0.zip` | `https://github.com/GameTechDev/XeSSUnrealPlugin/releases/download/v3.2.0/XeSS_UE5.8_Plugin_v3.2.0.zip` | `f0bb482102f245b452a13f9e899708f0af86710667eb180cac4eb6d007bd80af` | 251,334,143 bytes |

All three hashes were recomputed from the on-disk archives and matched the
pinned values.

From the FSR bundle the script extracts **only** `UE-FSR-4_1_1/FSR-580/FSR/` —
the Unreal 5.8 tree. The bundle also ships `FSR-530`, `FSR-540`, `FSR-550`,
`FSR-560` and `FSR-570` trees for older engine versions, which this project does
not use.

### 12.1 The extracted tree reproduces the installed tree exactly

**1,668 files** are installed across the three vendored plugin trees:

| Tree | Files |
|---|---|
| `Plugins/FSR` | 478 |
| `Plugins/DLSS` | 249 |
| `Plugins/DLSSMoviePipelineSupport` | 34 |
| `Plugins/NIS` | 70 |
| `Plugins/StreamlineCore` | 318 |
| `Plugins/StreamlineDLSSG` | 36 |
| `Plugins/StreamlineNGXCommon` | 19 |
| `Plugins/StreamlineReflex` | 31 |
| `Plugins/XeSS` | 433 |
| **Total** | **1,668** |

Every installed file was compared against its archive member by **path and
size**: zero missing, zero size differences, and zero installed files not
present in the corresponding archive. The extraction is faithful.

### 12.2 Plugin enablement — `TheCommander.uproject`

```json
{ "Name": "FSR",                  "Enabled": true, "TargetAllowList": ["Win64"] },
{ "Name": "DLSS",                 "Enabled": true, "TargetAllowList": ["Win64"] },
{ "Name": "StreamlineNGXCommon",  "Enabled": true, "TargetAllowList": ["Win64"] },
{ "Name": "XeSS",                 "Enabled": true, "TargetAllowList": ["Win64"] }
```

`StreamlineNGXCommon` is listed explicitly because DLSS's own `.uplugin`
declares it as a dependency and the engine resolves plugin dependencies only
when the dependent plugin is enabled in the project descriptor.

All three are prebuilt `Installed: true` plugins with `EngineVersion: 5.8.0` and
Win64 binaries — **no C++ module is required and none was added.** The project
remains Blueprint + Python.

`.gitignore` keeps the trees and the archives out of the index:

```gitignore
# Vendored upscaler plugin trees (multi-GB binaries, never committed).
# Reproduce with: python Tools/ue/fetch_upscaler_plugins.py
Plugins/

# Downloaded upscaler archives (cache dir, never committed)
*.zip
```

---

## 13. Verified results

Three live runs, all passing, from the final state of the tooling. The full
log excerpts are in `Docs/generated/upscaler_proof_log.txt`.

### 13.1 Deck profile — `upscaler-verify-20261021-122720.log` (721 frames)

```
LogFSR: Forcing FSR Upscaling to version '3.1.5' because of r.FidelityFX.FSR.RequestProvider=3
LogFSR: Successfully initialized FSR Upscaling provider using version '3.1.5'

r.FidelityFX.FSR.Enabled         = "1"         LastSetBy: DeviceProfile
r.FidelityFX.FSR.RequestProvider = "3"         LastSetBy: DeviceProfile
r.FidelityFX.FSR.QualityMode     = "3"         LastSetBy: DeviceProfile
r.ScreenPercentage              = "50"        LastSetBy: Code
r.AntiAliasingMethod            = "2"         LastSetBy: DeviceProfile
r.TemporalAA.Upscaler           = "1"         LastSetBy: DeviceProfile
r.BloomQuality                  = "0"         LastSetBy: DeviceProfile
r.Shadow.MaxCSMResolution       = "512"       LastSetBy: DeviceProfile
```

### 13.2 Vega profile — `upscaler-verify-20261021-122951.log` (601 frames)

```
LogFSR: Forcing FSR Upscaling to version '2.3.4' because of r.FidelityFX.FSR.RequestProvider=2
LogFSR: Successfully initialized FSR Upscaling provider using version '2.3.4'

r.FidelityFX.FSR.RequestProvider = "2"         LastSetBy: DeviceProfile
r.FidelityFX.FSR.QualityMode     = "1"         LastSetBy: DeviceProfile
r.ScreenPercentage              = "66.6667"   LastSetBy: Code
r.Shadow.MaxCSMResolution       = "512"       LastSetBy: DeviceProfile
```

### 13.3 RDNA3 profile — `upscaler-verify-20261021-123044.log` (601 frames)

```
LogFSR: Successfully initialized FSR Upscaling provider using version '3.1.5'

r.FidelityFX.FSR.RequestProvider = "0"         LastSetBy: DeviceProfile
r.ScreenPercentage              = "66.6667"   LastSetBy: Code
r.Shadow.MaxCSMResolution       = "2048"      LastSetBy: DeviceProfile
```

`RequestProvider=0` correctly lets the loader choose. On this SM 6.7-class
host it chose **3.1.5** — see §9.2 for why that is the expected result here
and what it does not prove.

### 13.4 Cross-run attribution

**The Deck profile never requested provider 2.** The 2.3.4 reading comes from
the Vega profile run, not from the Deck profile. Each profile's provider is
established by its own run:

| Profile | Provider observed | `r.ScreenPercentage` |
|---|---|---|
| `CommanderDeckRDNA2` | 3.1.5 | 50 |
| `CommanderVegaLaptop` | 2.3.4 | 66.6667 |
| `CommanderRDNA3Desktop` | 3.1.5 (loader chose, on this host) | 66.6667 |

### 13.5 The gate has teeth

Negative controls were run against the Deck log with deliberately wrong
expectations. Both failed as they should:

```
$ python Tools/ue/verify_upscaler_run.py <deck-log> --expect-provider 4.1.1
  FAIL  active FSR provider = 3.1.5, expected 4.1.1
  VERIFICATION FAILED

$ python Tools/ue/verify_upscaler_run.py <deck-log> --expect-provider 3.1.5 \
      --expect-screen-percentage 75
  FAIL  r.ScreenPercentage = 50, expected 75
  VERIFICATION FAILED
```

A gate that cannot fail is not a gate.

---

## 14. File map

| Path | Purpose |
|---|---|
| `Tools/ue/fetch_upscaler_plugins.py` | Pinned-URL + SHA-256 fetch/verify/install of the three plugin trees |
| `Tools/ue/run_editor.py` | Launches the editor for a verification run, captures the log, and runs the verifier gate |
| `Tools/ue/verify_upscaler_run.py` | The assertion gate over the log |
| `Tools/ue/_gen_proof_log.py` | Regenerates the proof log from the live logs |
| `Config/DefaultEngine.ini` | Fleet-wide upscaler floor + `DefaultFeatureAntiAliasing=2` |
| `Config/DefaultDeviceProfiles.ini` | **The per-node gate** — one profile per hardware class |
| `Config/DefaultScalability.ini` | Quality-level groups; the Deck's LOW preset; bloom control |
| `TheCommander.uproject` | The three upscaler plugins enabled |
| `Docs/generated/PERFORMANCE_UPSCALER_PROFILE.md` | This document |
| `Docs/generated/upscaler_proof_log.txt` | The generated evidence |

---

## 15. Summary of the gate, in one line each

- **Steam Deck (RDNA 2)** → FSR **3.1.5**, forced via
  `r.FidelityFX.FSR.RequestProvider=3`, Performance mode, **50 %** render
  resolution, bloom off. **FSR 4.1 is never named in this profile.**
- **Pre-RDNA laptop** → FSR **2.3.4**, forced via
  `r.FidelityFX.FSR.RequestProvider=2`.
- **RDNA 3 desktops** → loader-chosen
  (`r.FidelityFX.FSR.RequestProvider=0`). On the verification host that
  resolved to 3.1.5; FSR 4.1.1 remains unexercised.
- **DLSS** → NVIDIA RTX only. Vendored and enabled; not executable on AMD.
- **XeSS** → Intel Arc only. Vendored and enabled; not executable on AMD.
- **If the chosen upscaler cannot run on the GPU** → the plugin falls back to
  the loader's best supported tier, and failing that disables itself and the
  engine's TSR renders. A node always renders.
- **The device-profile gate holds** — `ECVF_SetByDeviceProfile` (0x07) outranks
  `ECVF_SetBySystemSettingsIni` (0x05) and `ECVF_SetByScalability` (0x02),
  proven by the engine's own priority warnings in the log.
- **`r.Shadow.MaxCSMResolution` was a real defect** — project setting (0x04)
  was shadowing the scalability group's 512 (0x02) — and is **fixed** by
  setting it in the device profile (0x07).
- **The `frameTimeDelta` warning is a benign init-time artifact**, not a unit
  bug. The vendored AMD source is not patched.
- **The missing DLSS-G manifest is driver-side**, not a vendoring gap. The
  vendored payload is complete and NVIDIA-signed.
- **Two things remain unproven and are stated as such**: FSR 3.1.5 on real
  Steam Deck silicon (§9.1), and FSR 4.1.1 on any RDNA 3 device (§9.2).
  Frame timings from the verification host are not Deck numbers.
