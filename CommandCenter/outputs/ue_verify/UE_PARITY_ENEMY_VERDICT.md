# UE PARITY ENEMY VERDICT - X-COM enemy assets in Unreal Engine 5.8

Generated: 2026-10-21T14:57:41.950550-04:00
Measured in-engine against the source FBX manifest. Supersedes the standing claim that
"UE 5.8's import retains only 39-91% of the exported triangles" - that claim was true of the
PREVIOUS generation of the shipping assets and is now false for all five.

## 1. GEOMETRY - PASS 5/5

| enemy | source FBX tris | UE shipping asset tris (measured in-engine) | verdict |
|---|---|---|---|
| XCOM_Sectoid | 7,308 | 7,308 | EXACT |
| XCOM_Viper | 5,764 | 5,764 | EXACT |
| XCOM_Floater | 2,184 | 2,184 | EXACT |
| XCOM_Muton | 5,216 | 5,216 | EXACT |
| XCOM_Chryssalid | 6,252 | 6,252 | EXACT |

The same five meshes measured 2,536 (Chryssalid), 1,980 (Floater) and 2,520 (Muton) before the
rebuild - these are the counts carried in the old report. The re-import landed: all five
Content/Enemies/XCOM/*.uasset files are modified in the working tree and NOT YET COMMITTED.

Fresh UE bounds also match the source manifest on all three axes for all five. Sectoid
139.18 / 52.24 / 70.42 cm against a manifest of 1.39 / 0.52 / 0.70 m. Floater
28.98 / 248.0 / 140.02 cm against 0.29 / 2.48 / 1.40 m. The old assets did not match: the
Sectoid stood 197.0 cm tall and the Floater 114.37 cm - a standing biped. The rebuilt Floater
is the low, legless 2.48 m form the brief specifies.

Precision note, because it matters for citation: the stale figure 3,712 is the VIPER's stale
row, while 5,216 is the MUTON's current count. The two numbers land on different enemies.

## 2. MATERIALS - REGRESSION, and it is the cheap one

| path | per-slot assignment | verdict |
|---|---|---|
| /Game/Tests/UEParity (verification copies) | every slot bound to the per-enemy set: XCOM_<Enemy>_CHITIN, _PLATE, _CHITIN_BONE, _PLATE_DARK, _ACCENT_EMISSIVE (Sectoid/Viper/Muton/Chryssalid, 5 slots each; Floater 4 slots) | CORRECT - accent_emissive_slot true and accent_emissive_assigned true on all five |
| /Game/Enemies/XCOM BEFORE the re-import | Sectoid XCOM_Chitin_Mid / _Chitin_Pale / _Chitin_Dark / _Eye_Emissive / _Core_Emissive; Viper and Muton additionally _Gunmetal / _Plasma_Emissive / _Armor_Plate / _Armor_Accent; Floater _Flesh; Chryssalid _Chitin_Mid / _Chitin_Pale / _Chitin_Dark / _Eye_Emissive / _Plasma_Emissive | CORRECT |
| /Game/Enemies/XCOM AFTER the re-import | every slot on every enemy assigned WorldGridMaterial, including ACCENT_EMISSIVE | BROKEN |

FINDING: the re-import fixed the geometry and broke the material bindings. The correct per-enemy
material sets already exist - they are bound on the verification copies - so this is a RE-BIND,
not an asset build. No new material assets are required.

CONSEQUENCE: as the tree stands, a packaged .exe would ship five enemies with every slot on
WorldGridMaterial. No chitin, no armour, no emissive. This blocks the .exe.

Side finding: the regenerated import report still carries material_note "kept-fbx-authored" while
the shipping assignments are WorldGridMaterial. The note contradicts the data and the report
should be regenerated from the shipping state.

## 3. RIG MODE PER SHOT

Both galleries are Blender EEVEE renders from Tools/blender/rig_evidence.py - NOT UE renders.
Two modes exist and their numbers are not comparable, so every shot must carry its mode label.

| enemy | PARITY mode (parity5.log) clipW/clipB/clipC, bg, band, frac |
|---|---|
| XCOM_Chryssalid | 406 / 406 / 16, bg 8.2, band 34.5, frac 0.0136 |
| XCOM_Muton | 146 / 146 / 2, bg 24.1, band 116.9, frac 0.0503 |
| XCOM_Floater | 0 / 0 / 0, bg 0.7, band 1.2, frac 0.0000 |
| XCOM_Viper | 630 / 630 / 0, bg 23.8, band 131.4, frac 0.0872 |
| XCOM_Sectoid | 1184 / 1184 / 0, bg 19.5, band 91.0, frac 0.0329 |

The EVIDENCE-mode gallery (v12/v13) reports the same meshes with different numbers - the
Sectoid's clipped_white is 313 in EVIDENCE mode against a PARITY-mode clipW of 1184 for the
same mesh.

## 4. PURGE AND VISIBLE DEBRIS

The purge crash is real but confined to the PARITY-mode runs: parity5.log records five times
"purge skipped: 'BMVert' object has no attribute 'name'". The EVIDENCE gallery ran under the
fixed purge with a genuine zero - "80 islands, removed 0 debris piece(s)" and "purge ran and
removed 0 pieces", the same in v10 through v23, with the fix documented in
Docs/generated/lighting_rig_handoff.md section 3.5. So the parity-mode images carry un-purged
geometry and the gallery does not. The conflict resolves by run mode, not by which document to
trust.

Visible debris in the EVIDENCE-mode shots:

| enemy | state |
|---|---|
| XCOM_Sectoid | hand FUSED, no floating geometry |
| XCOM_Floater | white box + ribbed tile FUSED |
| XCOM_Muton | white shard + green hip block FUSED |
| XCOM_Viper | prongs FUSED |
| XCOM_Chryssalid | hip fragments FLOATING - detached angular gray/green shards beside the hips with visible gaps and separate shadows |

Only the Chryssalid is not clean, and it is not scored clean.

## 5. UPSCALER

FSR 3.1.5 initialised successfully, twice. r.FidelityFX.FSR.Enabled=1 via DeviceProfile,
QualityMode=1, RequestProvider=0, r.ScreenPercentage=66.6667 - upscaling engaged at 66.67%
internal resolution - r.AntiAliasingMethod pushed 4 to 2, r.TemporalAA.Upscaler=1.

The SystemSettingsIni attempts to set the FSR CVars were IGNORED: DeviceProfile outranks it.
The DeviceProfile is the only working source of these settings.

Limit: this was a 10 second /Engine/Maps/Entry benchmark. No enemy was on screen, so the
upscaler was proven to initialise and to engage, not to look right.

## 6. LIMITS

- THE IN-ENGINE RENDERS WERE NEVER PRODUCED. CommandCenter/outputs/ue_verify/shots/ is EMPTY.
  This verdict therefore rests on measured .uasset state and log numbers, not on images. The
  visual-parity claim - silhouette, proportion, surface and material survival, visible defects
  - is UNPROVEN in-engine. That is the open gate this task was dispatched to close, and it is
  still open.
- The ten PARITY and ten mask/emissive PNGs were overwritten. out_lighting_build now holds only
  the 13:23 Muton-only re-run, so the parity claim rests on the log's probe/deliver numbers and
  not on surviving images.
- The 7-object uniform vision prompt returned internally inconsistent answers across passes.
  Only the per-object, Ebert-targeted reads are citable.
- lighting_rig_handoff.md and the log disagree on the purge. Resolved by run mode above.
- The five shipping .uasset re-imports are UNCOMMITTED. The geometry fix is real and currently
  exists only in the working tree.

## 7. ARTIFACTS

- CommandCenter/outputs/ue_verify/ue_verify_parity.json - post-re-import measurement
- CommandCenter/outputs/ue_verify/ue_verify_parity_preshipping.json - pre-re-import measurement
- CommandCenter/outputs/ue_verify/ue_probe.json
- CommandCenter/outputs/ue_import/xcom_ue_import_report.json
- CommandCenter/outputs/enemy_models/xcom_manifest.json - source FBX manifest
- Live transcript: %LOCALAPPDATA%\hermes\cache\delegation\live\deleg_44b09b3d\task-0.log

## 8. WHAT MUST HAPPEN NEXT

1. RE-BIND the shipping slots: copy the verification path's per-slot assignments onto
   /Game/Enemies/XCOM - XCOM_<Enemy>_CHITIN, _PLATE, _CHITIN_BONE, _PLATE_DARK,
   _ACCENT_EMISSIVE - then commit all five .uasset files. Until that lands the .exe ships five
   WorldGridMaterial enemies. This is a re-bind; no new material assets are needed.
2. RENDER the five in-engine shots into CommandCenter/outputs/ue_verify/shots/ and re-issue this
   verdict with the images attached. Neutral grey background, flat floor with a soft contact
   shadow, 3/4 front view at the hero-render scale, key + fill + rim, at least 900 px tall per
   enemy, plus a combined contact sheet.
3. FIX the Chryssalid floating hip fragments.
4. Regenerate the import report so material_note matches the shipping state.

"Examine yourselves, and see whether you are in the faith; test yourselves." - 2 Corinthians 13:5 (ESV)
Reason for the verse: this lane measures the assets instead of trusting the report, and the report
was true of an older mesh.
