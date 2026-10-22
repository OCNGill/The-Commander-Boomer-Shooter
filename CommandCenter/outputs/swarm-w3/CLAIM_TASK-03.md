# CLAIM — TASK-03

- **Slot:** swarm-w3
- **Model:** minimax/minimax-m3.1-flash:free
- **Node:** Gillsystems-Laptop (Windows 10, bash/MSYS)
- **Start time (ISO):** 2026-10-21T07:00:00-04:00
- **Deliverable:** `CommandCenter/outputs/swarm-w3/TASK-03_reveal_effect_spec.md`
- **Scope:** Creep reveal-effect spec for the X-COM enemy kit. Defines the 8-frame EMERGE pose
  (`A_<E>_Reveal`, 30fps), the five-light rig vocabulary (reveal_key / reveal_rim / reveal_under /
  reveal_pool / reveal_wash) and the normative order of introduction (key snap -> rim -> emissive
  eyes -> pool/ground anchor -> under-glow + wash), per-enemy first reads and beat offsets
  (Sectoid/Viper/Floater/Muton/Chryssalid, with the Floater's inverted order and the
  Viper/Muton late key), the five audio cue points with a same-frame sting requirement and the
  five missing `SFX_XCOM_Reveal_*` cues, the static-camera language, and 21 acceptance criteria
  (13 measured gates from `Tools/blender/out_lighting/verification.json` plus 8 reveal-specific).
  Names the current measured failures to fix, cited against the **07:33:03** verification
  generation (sha256 prefix d1f887a230, 5/5 rendered, 0 skipped, 720x900, EEVEE 48 samples,
  AgX): all five still fail (Muton 6/13, Chryssalid 7/13, Sectoid 7/13, Viper 8/13, Floater
  8/13). The 07:32 rework FIXED the floor white-out (the backdrop now passes on all five, the
  bottom border band down to 0.42-41.7 from 59-121) and the floor-zone contrast (26.86-57.86%
  against a 15% bar, all five pass) and the rim brightness ratio (3 of 5), but EXPLODED body
  clipping (Sectoid 2442 pixels, Muton 1271 including 235 off-emissive, Viper 1081, Chryssalid
  525) and left three defects open: the rim band is still short on three of five (Chryssalid
  31.08 and Floater 1.98 against a 120 floor, the Floater with rim_pixels 0), the under-glow
  still lights the floor rather than the body (under_lowbody 0.59-0.85 against a 1.3x bar on
  four of five), and the Floater is now effectively unlit (face p99 0.00, 868 visible body
  pixels, floor mean 1.38 against a 45-175 window). Also discloses the rig source drift:
  `rig_evidence.py` was modified 07:33:40, after the 07:33:03 render, and four parameter
  generations exist in one session (the rim changed from an AREA strip to a SPOT cone, and the
  energy model changed from (h/2)^2 with REF_HEIGHT 2.0 to (h/1.0)^2 with REF_HEIGHT 1.0), and
  Tools/blender/out_lighting/ is untracked by git.
