# CLAIM — TASK-08

- **Slot:** swarm-w3
- **Model:** minimax/minimax-m3.1-flash:free
- **Node:** Gillsystems-Laptop (Windows 10, bash/MSYS)
- **Start time (ISO):** 2026-10-21T07:00:00-04:00
- **Deliverable:** `CommandCenter/outputs/swarm-w3/TASK-08_asset_tracking_dod.md`
- **Scope:** Naming spine and asset-tracking system plus the Definition of Done for the X-COM
  enemy kit. Restates the Blender/UE/in-level naming patterns (`XCOM_<PascalEnemy>` mesh,
  `M_XCOM_<Family>_Master`, `MI_XCOM_<PascalEnemy>_<FAMILY>`, `T_XCOM_<Family>_<Map>`,
  `BP_XCOM_<PascalEnemy>`, `XCOM_<PascalEnemy>_<nn>`), the 24-slot material census over 6 active
  families (per-enemy counts 5/5/4/5/5), and the mandatory case/underscore family-token
  normalisation that lets `M_XCOM_PlateDark_Master` match `MI_XCOM_Muton_PLATE_DARK`. Specifies
  the tracker (`Tools/python/track_xcom_assets.py`), the machine ledger
  (`CommandCenter/outputs/asset_tracking/xcom_asset_ledger.json` + `.md`), the import receipt, the
  ledger schema, and five checks (freshness, hash link, naming, slot census, manifest agreement)
  with a `--check` exit-code contract. Defines a 30-gate Definition of Done across source, UE,
  naming, completeness and provenance. Scores the current state: all five UE meshes are stale by
  3h11m-3h14m (FBX rebuilt 04:24-04:27, uassets written 01:04-01:13) and the 04:41 import
  report still carries the v1 flat material names rather than the current per-enemy slots, so its
  `imported=5 failed=0` does not certify the current kit; 0 of 24 material instances, 0 of 7
  masters, 0 blueprints, 0 textures, 0 reveal stings, 11 legacy flat material assets to retire,
  and FBX Texture count 0 in all five (procedural graphs do not survive FBX export, so the kit
  renders flat). Reports the conflicts it depends on without editing them: the Plymouth roster
  overlap, the 17 TASK-04 conflicts, `target_height()` mis-scaling the X-COM five, the Floater
  +100cm pivot, and `r.DefaultFeature.Bloom=False` with no PostProcessVolume in Content/.
