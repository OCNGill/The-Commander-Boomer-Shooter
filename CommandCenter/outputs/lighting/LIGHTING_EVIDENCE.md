# Lighting Evidence (v4 reveal rig)

Generated 2026-10-21 05:58 by `Tools/blender/rig_evidence.py`.

All numbers below are MEASURED from the rendered PNGs in this folder by
the same script that rendered them, then re-measured independently by
`python Tools/blender/rig_evidence.py --verify --out <dir>`.

Metric definitions:

- `clipped_white_pixels` - r,g,b all > 248 anywhere in the frame.
- `clipped_body_pixels` - the same, restricted to the subject silhouette.
- `clipped_colour_pixels_non_emissive` - a channel at 250+ with a colour
  spread of 25+, on non-emissive pixels (emissive glow is allowed to clip).
- `emissive_pixels` - max channel > 190 with a colour spread of 25+.
- `rim_pixels` - g - r > 55 and g > 90 (the alien green rim).
- `background_darkness` - mean luminance of the outer 10% border.

## XCOM_Chryssalid

**Numbers:** clipped_white_pixels = **0**, clipped_body_pixels = **0**,
clipped_colour_pixels_non_emissive = **0**, emissive_pixels = **1150**,
rim_pixels = **191485**, background_darkness = **62.9**.

**Rig elements legible in this frame:** reveal_key, reveal_under, reveal_pool + contact shadow, emissives.

**Detail:** floor zones front/shadow-side/outer = 154 / 145 / 138
(min difference 5%), contact shadow ratio 0.57, face p99 245,
torso p99 133, under-glow low-body/torso 1.75x and feet/torso 2.20x,
rim band mean 59 (hot 0), rim bright pixels 0 = 0.000 of the body.

**Did not meet the bar:** floor_zones_differ_15pct, background_darkness_le_40, rim_3pct_of_body, rim_band_mean_ge_120.

**Emissive proof frame** (`XCOM_Chryssalid_emissive_only.png`, no scene lights,
emission x6.0, Fog Glow only): 1374 bright pixels, 0 clipped.

## XCOM_Muton

**Numbers:** clipped_white_pixels = **328**, clipped_body_pixels = **328**,
clipped_colour_pixels_non_emissive = **6**, emissive_pixels = **3836**,
rim_pixels = **200077**, background_darkness = **59.2**.

**Rig elements legible in this frame:** reveal_key, reveal_pool + contact shadow, emissives.

**Detail:** floor zones front/shadow-side/outer = 145 / 151 / 142
(min difference 2%), contact shadow ratio 0.38, face p99 183,
torso p99 248, under-glow low-body/torso 0.57x and feet/torso 0.49x,
rim band mean 65 (hot 213), rim bright pixels 427 = 0.007 of the body.

**Did not meet the bar:** no_clipped_white, no_clipped_body, no_colour_clip_off_emissive, floor_zones_differ_15pct, background_darkness_le_40, rim_3pct_of_body, rim_band_mean_ge_120, under_lowbody_1_3x_torso, under_feet_1_3x_torso.

**Emissive proof frame** (`XCOM_Muton_emissive_only.png`, no scene lights,
emission x6.0, Fog Glow only): 814 bright pixels, 0 clipped.

## XCOM_Floater

**Numbers:** clipped_white_pixels = **0**, clipped_body_pixels = **0**,
clipped_colour_pixels_non_emissive = **0**, emissive_pixels = **453**,
rim_pixels = **8308**, background_darkness = **0.8**.

**Rig elements legible in this frame:** emissives.

**Detail:** floor zones front/shadow-side/outer = 23 / 27 / 28
(min difference 3%), contact shadow ratio 0.41, face p99 0,
torso p99 33, under-glow low-body/torso 0.91x and feet/torso 0.21x,
rim band mean 8 (hot 179), rim bright pixels 124 = 0.011 of the body.

**Did not meet the bar:** floor_zones_in_window, floor_zones_differ_15pct, face_p99_ge_25, rim_3pct_of_body, rim_band_mean_ge_120, under_lowbody_1_3x_torso, under_feet_1_3x_torso.

**Emissive proof frame** (`XCOM_Floater_emissive_only.png`, no scene lights,
emission x6.0, Fog Glow only): 553 bright pixels, 0 clipped.

## XCOM_Viper

**Numbers:** clipped_white_pixels = **78**, clipped_body_pixels = **78**,
clipped_colour_pixels_non_emissive = **0**, emissive_pixels = **14**,
rim_pixels = **174107**, background_darkness = **61.6**.

**Rig elements legible in this frame:** reveal_key, reveal_pool + contact shadow, emissives.

**Detail:** floor zones front/shadow-side/outer = 146 / 152 / 148
(min difference 2%), contact shadow ratio 0.63, face p99 178,
torso p99 239, under-glow low-body/torso 0.88x and feet/torso 0.36x,
rim band mean 76 (hot 218), rim bright pixels 801 = 0.019 of the body.

**Did not meet the bar:** no_clipped_white, no_clipped_body, floor_zones_differ_15pct, background_darkness_le_40, rim_3pct_of_body, rim_band_mean_ge_120, under_lowbody_1_3x_torso, under_feet_1_3x_torso.

**Emissive proof frame** (`XCOM_Viper_emissive_only.png`, no scene lights,
emission x6.0, Fog Glow only): 61 bright pixels, 0 clipped.

## XCOM_Sectoid

**Numbers:** clipped_white_pixels = **1205**, clipped_body_pixels = **1205**,
clipped_colour_pixels_non_emissive = **0**, emissive_pixels = **2717**,
rim_pixels = **196856**, background_darkness = **60.2**.

**Rig elements legible in this frame:** reveal_key, reveal_under, reveal_pool + contact shadow, emissives.

**Detail:** floor zones front/shadow-side/outer = 145 / 148 / 143
(min difference 2%), contact shadow ratio 0.58, face p99 71,
torso p99 239, under-glow low-body/torso 1.33x and feet/torso 0.75x,
rim band mean 59 (hot 202), rim bright pixels 756 = 0.011 of the body.

**Did not meet the bar:** no_clipped_white, no_clipped_body, floor_zones_differ_15pct, background_darkness_le_40, rim_3pct_of_body, rim_band_mean_ge_120, under_feet_1_3x_torso.

**Emissive proof frame** (`XCOM_Sectoid_emissive_only.png`, no scene lights,
emission x6.0, Fog Glow only): 588 bright pixels, 0 clipped.

