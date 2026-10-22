CRITIQUE REPORT — M_Blockout01 Level Design (9-frame level render set)
Artifact type: game level (in-engine renders + 2D blockout diagrams)
Reviewed: 2026-10-21   Ebert round: 1
EVIDENCE:
  The_Commander_Boomer_Shooter/Tools/blender/out_level/blueprint_topdown.png
  The_Commander_Boomer_Shooter/Tools/blender/out_level/path_diagram.png
  The_Commander_Boomer_Shooter/Tools/blender/out_level/level_perspective.png
  The_Commander_Boomer_Shooter/Tools/blender/out_level/gameplay_01_drop.png
  The_Commander_Boomer_Shooter/Tools/blender/out_level/gameplay_02_duel.png
  The_Commander_Boomer_Shooter/Tools/blender/out_level/gameplay_03_pit.png
  The_Commander_Boomer_Shooter/Tools/blender/out_level/gameplay_04_platform.png
  The_Commander_Boomer_Shooter/Tools/blender/out_level/gameplay_05_dropzone.png
  The_Commander_Boomer_Shooter/Tools/blender/out_level/gameplay_06_pitramp.png

OVERALL: 3.6 / 7.0
THRESHOLD: 6.2
VERDICT: ITERATE

SCORED SET — FRAME PROVENANCE
  All nine frames were re-verified by mtime and SHA-256 before scoring. The scored set is the
  05:29-05:34 textured re-render, NOT the 04:19-04:22 set named in my brief. Every evidence note
  below was written against these files. All nine are byte-identical to the copies in
  CommandCenter/outputs/level/.

    blueprint_topdown.png    2026-10-21 05:31:57  1504115 B  sha256:7c416d3d99e00493
    path_diagram.png         2026-10-21 05:32:15  1551492 B  sha256:8378bed8bf3e6719
    gameplay_01_drop.png     2026-10-21 05:32:39  1185556 B  sha256:86689e2ceac72603
    gameplay_05_dropzone.png 2026-10-21 05:32:55  1426488 B  sha256:63ffac951bc1c6a6
    gameplay_02_duel.png     2026-10-21 05:33:10  1114212 B  sha256:22f4f1733e533476
    gameplay_03_pit.png      2026-10-21 05:33:37  1602430 B  sha256:30c0391381b5833d
    gameplay_04_platform.png 2026-10-21 05:33:53  1165123 B  sha256:eabbc51c154982ba
    gameplay_06_pitramp.png  2026-10-21 05:34:26  1700942 B  sha256:8733326c5a57c295
    level_perspective.png    2026-10-21 05:34:53  1745087 B  sha256:e829e7ceb9a4819c

  Scope note: this is the LEVEL DESIGN lane only. Enemies, materials/texturing and lighting are
  other lanes' scores and are not penalized here, except where a level-design claim is falsified
  by them.

SUB-SCORES
 1. Visual Craft ............. 4.5  (25%) — Real material work and a coherent teal/oxblood palette
    read well in level_perspective.png, but the level's vertical vocabulary is visually inert: the
    pit is a curb pen on a flat floor (gameplay_03_pit.png) and the platform reads as a bare slab.
 2. Truthfulness .............. 2.0  (20%) — The frames contradict the map they document, and the
    render's own report says "The renders cut the floor open so the intent is visible" when the
    3D build draws one unbroken slab (render_level.py:1027-1030).
 3. Clarity & Communication ... 3.0  (20%) — Both diagrams carry hardcoded callouts ("PIT 10x10 -
    NO FLOOR CUT, NO ACCESS", "RAMP INSIDE PLATFORM - NO CLIMB", render_level.py:646,650) that
    the map contradicts, and path_diagram.png draws a route straight through the "NO ACCESS" pit.
 4. Technical Quality ......... 3.5  (15%) — All nine frames render clean at full res with textures
    wired, but build_game has no 'floor' branch so the 4 BO_Floor pieces that leave the real pit
    hole are never drawn, and 'cut' is computed then discarded.
 5. Interaction & Depth ....... 4.0  (10%) — Substituted for a static artifact per rubric 5: the
    arena has genuine tactical depth (cover field, drop zone, kill zones, high ground), but the
    three-step pillar climb is not traversable and the pit is not enterable.
 6. Brand Fit ................. 6.0  ( 5%) — Restrained, engineered, no decoration; the orthographic
    grid, scale bar and cyan geometry edges read as a real blockout tool.
 7. First-Impression Impact ... 4.5  ( 5%) — level_perspective.png is genuinely handsome; six of
    nine frames are ground-level and near-monotone, so the set's opening impression is muted.

  TOTAL 3.575 -> 3.6 / 7.0   (bar 6.20)

THE THREE CLAIMS, CHECKED AGAINST THE IMAGES
  Method: I read the three claims as claims about what a player can SEE, and tested them three
  ways — (a) a from-scratch ray-cast of the exact scene build_game() builds, sampled across every
  frame and validated against actual pixel colours; (b) projected on-screen pixel footprints of
  each feature per frame; (c) direct vision reads of full frames and of magnified crops.
  The ray-cast was validated before use: pixels it labels SKY average rgb(39,47,43) and pixels it
  labels SLAB average rgb(79,94,100) in the same frame, and PIT_FLOOR is never hit at all.

  CLAIM 1 — "A player can see the way out of the pit."
    VERDICT: FALSE IN THE RENDERS. TRUE IN THE MAP, UNSUPPORTED IN THE IMAGES.
    Map data: the hole is real. The four BO_Floor pieces cover N/S/E/W and leave X -15.25..-8.75,
    Y -15.25..-10.75 open — a 6.50 x 4.50 m opening. BO_Ramp_Pit runs (-10.55,-13,-1.00) to
    (-8.75,-13,0.00) and the east rim is split (BO_PitRim_E1 Y -15.25..-14.00, BO_PitRim_E2
    Y -12.00..-10.75) leaving a 2.00 m gap the ramp passes through. So the level is built right.
    What the frames show: the renderer never draws those four floor pieces. build_game has no
    'floor' branch; it draws one 40x40x0.12 slab at z=-0.06 and computes a `cut` rectangle at
    line 1027 that is never used. The pit floor cube therefore sits at z -1.80..-1.30, entirely
    under that slab. My ray-cast returns zero PIT_FLOOR hits in gameplay_03_pit and
    gameplay_06_pitramp, and every sampled pixel over the pit footprint in both frames is
    grey/olive concrete (e.g. rgb(62,60,40), rgb(43,45,29)) — 0 of 1543 and 0 of 1342 samples are
    red-dominant, though the G_Pit material is (0.095,0.028,0.026) with a red emission. The pit's
    three occupants (PU_KeyRed_Pit, PU_Health_Pit, ENC_Brute_Pit, all z=-1.00) are invisible.
    BO_Ramp_Pit is visible but reads as a 0.25 m lip: the ramp box top runs z=-0.75 to z=+0.25, so
    it pokes 0.25 m above the slab and 75 cm of it is buried. It covers 0.3% of gameplay_06.
    Vision on the crop agrees: "no dark red or maroon floor surface", "no coherent ramp-shaped
    plane", "this image alone would not let a player identify a pit with a usable ramp."
    One more thing the frames get wrong about the pit: the 5 rim blocks are 1x1x2 m posts whose
    tops stand 1.00 m above the floor, so from gameplay_03_pit.png the pit reads as a walled PEN
    on flat ground, not a hole. That is the most damaging possible failure — a hazard the player
    reads as a prop.

  CLAIM 2 — "The platform ramp reads as one continuous slope with both landings visible."
    VERDICT: SLOPE TRUE, BOTH LANDINGS FALSE.
    The ramp does read as one continuous incline: gameplay_04_platform.png shows an unbroken
    sloped surface with three pale longitudinal stripes running its full length and no break.
    The lower landing IS visible — the ramp's foot meets the arena floor with a clear dark fascia
    edge. The upper landing is NOT visible. BO_Platform_NE's deck top is z=5.00; the CAM_PLAT eye
    is at z=2.40, so the deck's top face is back-facing and geometrically cannot be seen from
    that camera. My projection puts the deck's top corners inside the frame, but what is visible
    there is the platform's vertical face, not its floor. Vision on the re-crop that included both
    ramp ends: "There is no clearly visible flat platform surface at the upper end... The viewer
    cannot tell where the climber is meant to step off." So the ramp visibly goes somewhere
    unknown. Note the platform is not missed by the framing alone — the wide frame
    level_perspective.png (eye z=12.50, above the deck) does show the deck, but it is 39 m away and
    the ramp-to-deck junction is a few dozen pixels.
    Also worth recording: the map's ramp is fine. BO_Ramp_NE's measured ends are low (11.20,-7.00,
    0.00) and high (11.20,8.00,5.00), and the platform deck spans X 8.00..16.00, Y 8.00..16.00
    with top z=5.00 — the high end is coincident with the deck's south edge at deck height, exactly
    as LEDGER LEVEL-03 states. This claim is true in the map and true-in-part in the renders.

  CLAIM 3 — "The pillar climb and its keycard read on screen."
    VERDICT: FALSE ON BOTH HALVES.
    The keycard does not read in any ground-level frame. PU_KeyGreen_PillarTop is at z=6.20,
    0.20 m above the pillar's top face. Across the six gameplay frames it is OFF-FRAME in four
    (gameplay_01_drop, gameplay_02_duel, gameplay_04_platform, gameplay_05_dropzone) and BEHIND
    CAMERA in the other two. It appears only in level_perspective.png, at 6.8 x 9.0 px — 61 px^2,
    0.005% of frame, 37.9 m from the camera. It is a 7-pixel speck.
    The ledges do not read as a climb. In level_perspective.png the three steps project to
    18.1x4.7, 15.8x4.5 and 17.5x5.1 px. Vision on the magnified crop: "there are no clearly
    distinguishable intermediate step boxes... they do not form a countable spiral staircase", and
    "no continuous, clearly traversable staircase, ladder, or connected ledge sequence is visible."
    Worse, the climb is not merely unreadable, it is not traversable. The pillar is a solid 4.00 m
    cylinder 6.00 m tall, and the three ledges sit at 30, 150 and 270 degrees around it. Consecutive
    ledges are 120 degrees apart, 3.28 m edge-to-edge, with the pillar body directly between them.
    A jump is a ballistic arc, so no straight jump crosses it, and going around means leaving the
    ledge with no landing surface anywhere at radius 3.40-6.00 m at heights 2.00-5.80 m. I scanned
    every actor in the map for an intermediate landing: the only surfaces with a top between
    z=1.00 and z=6.00 anywhere within 8 m of the pillar axis are the three ledges themselves, and
    there are ZERO BO_Cover actors within 8 m of the pillar axis at all. The first hop (ground to
    step1, 2.00 m) is within the 2.50 m budget; the second and third (1.90 m each) are not
    reachable. The LEDGER's "rises 200/190/190uu vs the 250uu jump budget" checks the vertical
    component only; the horizontal component of the same claim is not satisfiable.

  LEDGER LEVEL-02, CHECKED
    LEVEL-02 claims the nine renders were "vision-verified (pit recess with flush exit ramp,
    platform ramp one continuous slope with both landings, new gameplay_06_pitramp.png showing the
    flight with real thickness)". One of three sub-claims holds. The continuous slope holds. The
    pit recess with a flush exit ramp does not — the flight's top surface is 0.25 m proud of the
    slab and the pit beneath it is sealed by the slab. Both landings do not — the upper one is
    back-facing. "The flight with real thickness" is true of the map, but the render shows 0.3% of
    frame. Separately, render_level.py's own audit text at line 994 asserts "The renders cut the
    floor open so the intent is visible" — they do not, and `cut` is dead code at both line 576
    (2D blueprint) and line 1027 (3D scene). The report also sets
    st['pit_sealed_by_floor_plane'] = bool(PITF) at line 868, which is true whenever a pit actor
    exists, so that finding is asserted rather than tested. The 2D blueprint does draw the pit as
    a red disc with the annotation "PIT 10x10 - NO FLOOR CUT, NO ACCESS" — a statement that
    describes the renderer's own bug as a property of the level.

STRENGTHS (be specific — a real critic can name what works)
  - level_perspective.png is a genuinely handsome arena: restrained teal/green with a single
    oxblood accent, real material response, and a pillar that reads as architecture.
  - The blueprint is a professional drafting artifact — 2 m tile grid, X/Y axes with ticks, scale
    bar, legend with eleven swatches, title block with actor counts, cyan geometry outlines.
  - The map's level design is sound where it can be read: the east-rim gap lines up exactly with
    the pit ramp's exit, the platform ramp lands on the deck edge at deck height, and the drop
    zone sits 15 m clear of the pillar with cover between.
  - The 2D path diagram's route (drop -> cover -> pit -> pillar -> objective) and its two red
    kill-zone rings are a clear, legible statement of intended play.

DELTA TO 6.2 (prioritized: points per effort)
 1. [ ] Draw the map's real floor pieces in build_game instead of one 40x40 slab, and honour the
        `cut` rectangle that is already computed at render_level.py:1027 — +1.2 pts (Truthfulness
        and Technical Quality both move) — render_level.py:1027-1030.
 2. [ ] Replace the two hardcoded callouts at render_level.py:646 and :650 with text derived from
        the actual geometry, and fix path_diagram.png's route so it does not run through a pit
        annotated "NO ACCESS" — +1.0 pt (Truthfulness, Clarity).
 3. [ ] Reposition the pit ledges so consecutive steps are within one jump of each other, or
        reduce their angular separation and the pillar radius — +0.6 pt (Interaction & Depth) —
        BO_PillarStep_1/2/3 in level_transforms.json.
 4. [ ] Raise CAM_PLAT above z=5.00, or add a second shot from the deck side, so the platform's
        upper landing is actually visible — +0.5 pt (Visual Craft, Clarity) — render_level.py:1246.
 5. [ ] Bring the keycard's visual read up: a 0.55 m emissive cube at 6.8x9.0 px from 38 m is
        invisible, so add a landmark or a light column at the pillar top — +0.4 pt (Visual Craft,
        First-Impression) — BO_Pillar_Center, PU_KeyGreen_PillarTop.
 6. [ ] Re-aim CAM_PIT and CAM_PITRAMP so the pit occupies the frame rather than 27% of sky, and
        re-run the render so the new set replaces 05:31-05:34 — +0.3 pt (Visual Craft).

NOTES ON EVIDENCE
  - Every visual claim in this report cites a frame in the 05:31:57-05:34:53 set. I did not score
    any frame from the earlier 04:19-04:22 set, and I did not carry over any evidence note written
    against it.
  - The three ground-level frames are dominated by unlit vertical faces (walls and cover read flat
    in gameplay_02_duel, gameplay_05_dropzone and gameplay_04_platform). The user states a level
    fill-light pass is queued for the next build; I have not penalized it here since lighting is
    another lane, but I have not let it inflate Visual Craft either.
  - Pit elevation in gameplay_03_pit.png and gameplay_06_pitramp.png is genuinely ambiguous to the
    eye: two independent vision reads of the same crop returned opposite answers on whether the
    floor is recessed. That ambiguity is itself the finding. The pixel and ray-cast evidence is
    unambiguous, and I have reported the images as a failure to communicate rather than as a
    definitive hole, because a player reading them cannot tell which it is.
  - The build team's own claim set is the map data, and the map data is good on claims 1 and 2. I
    am reporting the gap between map and image, in both directions, and I have credited the map
    where the map is right. Nothing here says the level design is bad; it says these nine frames
    do not show it.
  - No metric, testimonial, citation or fabricated result appears in the artifact, so the
    Truthfulness hard rule (score 1.0) is not triggered. The axis is at 2.0 for a different
    reason: the artifact's own report text and the diagram's own callouts assert things the
    artifacts contradict, which is misrepresentation rather than invention.
  - Levels of confidence: the pit occlusion, the ramp lip geometry, the keycard and ledge pixel
    footprints, and the ledge angular separation are all measured, not judged, and I would defend
    them. The precise visual-craft sub-score is the softest number in this report.

VERDICT: ITERATE
