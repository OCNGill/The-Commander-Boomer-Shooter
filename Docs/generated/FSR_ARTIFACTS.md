# AMD FSR & Upscaler Artifact Registry

Generated 2026-10-22. Source of truth for the pinned upscaler artifacts:
`Tools/ue/fetch_upscaler_plugins.py`.

Every SHA-256 below was computed from a real downloaded file on this machine
(`sha256` over the complete archive) — none are transcribed from a vendor page.

---

## 1. Pinned artifact set

| Artifact | Version | Archive | Bytes | SHA-256 | Hash verified |
|---|---|---|---|---|---|
| AMD FSR Upscaling (Unreal 5.3–5.8 bundle, tree `FSR-580`) | FSR Upscaling **4.1.1** | `UE-FSR-4_1_1.zip` | 2,007,843,138 | `9ce745e25c4b86bbc0974258045690c9c80d4e524cd48359e20005528ee722c5` | 2026-10-22 — full re-download + SHA-256 |
| NVIDIA DLSS plugin bundle (Unreal 5.8) | DLSS-SR **8.9.0** / NGX **310.9.16** | `2026.10.16_ue5.8_dlss4.5plugin_v8.9.0.zip` | 1,166,608,575 | `adeeb59b9635794e05252438bf01307bf8a629769e8f0517237363f690bb380c` | 2026-10-22 — re-hashed from cached archive |
| Intel XeSS (Unreal 5.8) | XeSS **3.2.0** | `XeSS_UE5.8_Plugin_v3.2.0.zip` | 251,334,143 | `f0bb482102f245b452a13f9e899708f0af86710667eb180cac4eb6d007bd80af` | 2026-10-22 — re-hashed from cached archive |

The FSR bundle ships three upscaler providers inside one
`amd_fidelityfx_upscaler_dx12.dll`: `ffxProvider_FSR4` (4.1.1),
`ffxProvider_FSR3Upscale` (3.1.5), `ffxProvider_FSR2` (2.3.4). The FidelityFX
loader picks the provider the running hardware supports, so an RDNA 2 device
lands on FSR 3.1.5 and never 4.1.1 (which needs Shader Model 6.6 / RDNA 3+).

Component versions inside the pinned FSR 4.1.1 bundle:

| Component | Version |
|---|---|
| AMD FSR Upscaling "Redstone" | 4.1.1 |
| AMD FSR Frame Generation "Redstone" | 4.0.1 |
| AMD FSR (analytical upscaling) | 3.1.5 |
| AMD FSR (legacy upscaling) | 2.3.4 |
| Analytical Frame Generation | 3.1.6 |
| Frame Generation SwapChain | 3.1.7 |
| FSR Ray Regeneration | 1.2.0 |
| FSR Radiance Caching | 0.9.0 (technical preview) |

Plugin descriptor versions confirmed in the installed tree:
`Plugins/FSR/FSR.uplugin` → `"VersionName": "4.1.1"`;
`Plugins/XeSS/XeSS.uplugin` → `"VersionName": "3.2.0"`;
`Plugins/DLSS/DLSS.uplugin` → `"VersionName": "8.9.0-NGX310.9.16"`.

---

## 2. FSR 4.1.2 availability verdict

**VERDICT: FSR 4.1.2 is NOT obtainable as a redistributable artifact.**
It is a **driver-side** upscaler shipped inside AMD Software: Adrenalin Edition
26.10.1 (2026-10-20). No SDK package, no Unreal plugin bundle, and no
standalone redistributable `amd_fidelityfx_upscaler_dx12.dll` at 4.1.2 exist.

Evidence (all URLs live-checked 2026-10-22):

| Check | Result | Source |
|---|---|---|
| GPUOpen UE FSR plugin download redirect | `302` → `/download/UE-FSR-4_1_1.zip` → `200`, `Content-Length: 2007843138` — still 4.1.1 | https://gpuopen.com/download-ue-fsr-plugin/ |
| GPUOpen plugin version listing | "Download v4.1.1 … Last updated August 2026 – supports UE 5.3 up to UE 5.8" | https://gpuopen.com/learn/ue-fsr |
| `UE-FSR-4_1_2.zip` | `404 Not Found` | https://gpuopen.com/download/UE-FSR-4_1_2.zip |
| `UE-FSR-4_1_2a.zip` / `FSR-4_1_2.zip` / `AMD-FSR-4_1_2.zip` / `UE-FSR-4.1.2.zip` / `FSR-SDK-2_4_0.zip` | all `404 Not Found` | gpuopen.com/download/… |
| FidelityFX-SDK latest release | `FSR SDK v2.3.0`, published 2026-06-24 | https://github.com/GPUOpen-LibrariesAndSDKs/FidelityFX-SDK/releases |
| FidelityFX-SDK tags (`git ls-remote --tags`) | newest is `v2.3.0` (`60f4ea8`); **no `v2.4.0` tag** | GitHub remote refs |
| FidelityFX-SDK branches | `main` = `60f4ea8` (= v2.3.0); only `release-FSR3-3.0.3/3.0.4` besides | GitHub remote refs |
| FidelityFX-SDK `releases.atom` / `tags.atom` | newest entry `FSR SDK v2.3.0` — **no pre-release, no 2.4** | GitHub Atom feeds |
| GPUOpen FSR SDK page | "Download the latest version - v2.3" → `FidelityFX-Samples-v2.3.0-prebuilt.zip` | https://gpuopen.com/amd-fsr-sdk/ |
| Adrenalin 26.10.1 release notes | "AMD FSR Upscaling 4.1 support for: Radeon RX 6000 Series, Ryzen AI Max 300 Series, Ryzen AI Max 400 Series" — a driver feature, not an SDK/plugin release | https://www.amd.com/en/resources/support-articles/release-notes/rn-rad-win-26-10-1.html |
| Installed driver tree | Adrenalin 26.10.1 contains **no** 4.1.2 redistributable upscaler DLL; only the legacy 6,667,280-byte monolithic `amd_fidelityfx_dx12.dll` in the driver store | local driver-store scan |

Consequences, in one line each:

- **4.1.2 is driver-side only.** It is injected/selected by the Adrenalin
  driver for DX12 titles; nothing to download, license, or redistribute.
- **RDNA 3.5 APU support for FSR 4.1 is UNDECIDED by AMD.** McAfee:
  "not planned"; Ye: "no decision has been made". Do not build against it.
- **FSR 4.1 Vulkan support is NOT shipped.** It is slated for FSR SDK 2.4,
  which is unreleased. DX12 only for now.
- The pinned FSR 4.1.1 bundle stays the newest **redistributable** FSR
  artifact and remains the correct pin. Its SHA-256 was re-verified against a
  fresh download on 2026-10-22.

---

## 3. RDNA support matrix

| Hardware | ML FSR 4.1 via pinned plugin 4.1.1 | ML FSR 4.1 via Adrenalin 26.10.1 | Analytical fallback in plugin | Frame generation |
|---|---|---|---|---|
| Radeon RX 9000 (RDNA 4) | Yes — FSR 4.1 native | Yes | FSR 3.1.5 | FG 4.0.1 (ML, Win 11) |
| Radeon RX 7000 (RDNA 3) | Yes — FSR 4.1 INT8 | Yes | FSR 3.1.5 | Analytical FG 3.1.6 |
| Radeon RX 6000 (RDNA 2) | No — 4.1.1 needs SM 6.6 / RDNA 3+ | **Yes — driver-side FSR 4.1** | FSR 3.1.5 | Analytical FG 3.1.6 |
| RDNA 3.5 desktop APU | No | **Undecided by AMD** | FSR 3.1.5 | Analytical FG 3.1.6 |
| Ryzen AI Max 300 / 400 | No | Yes | FSR 3.1.5 | Analytical FG 3.1.6 |
| Z2 Extreme / Z2A handhelds | No | Yes | FSR 3.1.5 | Analytical FG 3.1.6 |
| Older than RDNA 2 | No | No | FSR 2.3.4 | Analytical FG 3.1.6 |

Notes:

- RDNA 3 (RX 7000) FSR 4.1 support arrived with FSR SDK 2.3 / plugin 4.1.1
  via an INT8 path: https://gpuopen.com/learn/amd-fsr-sdk-2-3-blog/
- The 26.10.1 driver-side FSR 4.1 path for RDNA 2 relies on the driver's
  global FSR 4 injection for signed-DLL DX12 titles (the Adrenalin
  "AMD FSR4 Upscaling" toggle, available since the 25.9.1 drivers).
  See https://github.com/optiscaler/OptiScaler/wiki/FSR4-Compatibility-List/
- The Commander's Steam Deck (RDNA 2) therefore gets **FSR 3.1.5** from the
  plugin, with driver-side FSR 4.1 as an opportunistic upgrade on 26.10.1 —
  not a guaranteed one, and not something this repo pins.

---

## 4. Maintenance rule

When a new FSR SDK ships, add a new pinned entry to
`Tools/ue/fetch_upscaler_plugins.py` with the archive's real SHA-256
(computed locally from the downloaded file), and record the availability
verdict here. Never pin a URL or hash that has not been downloaded and hashed
on this machine. A driver-only release never gets a pin.
