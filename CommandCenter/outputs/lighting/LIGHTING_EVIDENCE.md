# Lighting Evidence (v4 reveal rig)

Generated 2026-10-21 06:40 by `Tools/blender/rig_evidence.py`.

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
clipped_colour_pixels_non_emissive = **0**, emissive_pixels = **0**,
rim_pixels = **75676**, background_darkness = **29.3**.

**Rig elements legible in this frame:** reveal_key.

**Detail:** floor zones front/shadow-side/outer = 76 / 36 / 66
(min difference 12%), contact shadow ratio 0.67, face p99 245,
torso p99 65, under-glow low-body/torso 0.95x and feet/torso 1.36x,
rim band mean 23 (hot 0), rim bright pixels 0 = 0.000 of the body.

**Did not meet the bar:** floor_zones_in_window, floor_zones_differ_15pct, rim_3pct_of_body, rim_band_mean_ge_120, under_lowbody_1_3x_torso.

**Emissive proof frame** (`XCOM_Chryssalid_emissive_only.png`, no scene lights,
emission x6.0, Fog Glow only): 0 bright pixels, 0 clipped.

## XCOM_Muton

**Numbers:** clipped_white_pixels = **0**, clipped_body_pixels = **0**,
clipped_colour_pixels_non_emissive = **0**, emissive_pixels = **3533**,
rim_pixels = **215826**, background_darkness = **38.1**.

**Rig elements legible in this frame:** reveal_key, reveal_pool + contact shadow, emissives.

**Detail:** floor zones front/shadow-side/outer = 131 / 122 / 106
(min difference 7%), contact shadow ratio 0.32, face p99 212,
torso p99 236, under-glow low-body/torso 0.16x and feet/torso 0.44x,
rim band mean 39 (hot 211), rim bright pixels 246 = 0.004 of the body.

**Did not meet the bar:** floor_zones_differ_15pct, rim_3pct_of_body, rim_band_mean_ge_120, under_lowbody_1_3x_torso, under_feet_1_3x_torso.

**Emissive proof frame** (`XCOM_Muton_emissive_only.png`, no scene lights,
emission x6.0, Fog Glow only): 0 bright pixels, 0 clipped.

## XCOM_Floater

**Numbers:** clipped_white_pixels = **268**, clipped_body_pixels = **268**,
clipped_colour_pixels_non_emissive = **0**, emissive_pixels = **1116**,
rim_pixels = **664**, background_darkness = **0.7**.

**Rig elements legible in this frame:** reveal_rim, reveal_under, emissives.

**Detail:** floor zones front/shadow-side/outer = 131 / 1 / 3
(min difference 50%), contact shadow ratio 0.19, face p99 0,
torso p99 252, under-glow low-body/torso 8.35x and feet/torso 7.87x,
rim band mean 29 (hot 207), rim bright pixels 374 = 0.032 of the body.

**Did not meet the bar:** no_clipped_white, no_clipped_body, floor_zones_in_window, face_p99_ge_25, rim_band_mean_ge_120.

**Emissive proof frame** (`XCOM_Floater_emissive_only.png`, no scene lights,
emission x6.0, Fog Glow only): 0 bright pixels, 0 clipped.

## XCOM_Viper

**Numbers:** clipped_white_pixels = **0**, clipped_body_pixels = **0**,
clipped_colour_pixels_non_emissive = **0**, emissive_pixels = **0**,
rim_pixels = **239336**, background_darkness = **49.8**.

**Rig elements legible in this frame:** reveal_key, reveal_pool + contact shadow.

**Detail:** floor zones front/shadow-side/outer = 135 / 133 / 114
(min difference 2%), contact shadow ratio 0.54, face p99 209,
torso p99 232, under-glow low-body/torso 0.74x and feet/torso 0.32x,
rim band mean 55 (hot 207), rim bright pixels 507 = 0.012 of the body.

**Did not meet the bar:** floor_zones_differ_15pct, background_darkness_le_40, rim_3pct_of_body, rim_band_mean_ge_120, under_lowbody_1_3x_torso, under_feet_1_3x_torso.

**Emissive proof frame** (`XCOM_Viper_emissive_only.png`, no scene lights,
emission x6.0, Fog Glow only): 0 bright pixels, 0 clipped.

## XCOM_Sectoid

**Numbers:** clipped_white_pixels = **491**, clipped_body_pixels = **491**,
clipped_colour_pixels_non_emissive = **0**, emissive_pixels = **2288**,
rim_pixels = **232960**, background_darkness = **47.0**.

**Rig elements legible in this frame:** reveal_pool + contact shadow, emissives.

**Detail:** floor zones front/shadow-side/outer = 137 / 126 / 114
(min difference 8%), contact shadow ratio 0.53, face p99 20,
torso p99 233, under-glow low-body/torso 0.94x and feet/torso 0.74x,
rim band mean 44 (hot 201), rim bright pixels 412 = 0.006 of the body.

**Did not meet the bar:** no_clipped_white, no_clipped_body, floor_zones_differ_15pct, background_darkness_le_40, face_p99_ge_25, rim_3pct_of_body, rim_band_mean_ge_120, under_lowbody_1_3x_torso, under_feet_1_3x_torso.

**Emissive proof frame** (`XCOM_Sectoid_emissive_only.png`, no scene lights,
emission x6.0, Fog Glow only): 0 bright pixels, 0 clipped.

