# Lighting Evidence (v4 reveal rig)

Generated 2026-10-21 06:22 by `Tools/blender/rig_evidence.py`.

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
clipped_colour_pixels_non_emissive = **0**, emissive_pixels = **173**,
rim_pixels = **38389**, background_darkness = **55.3**.

**Rig elements legible in this frame:** reveal_key, reveal_pool + contact shadow, emissives.

**Detail:** floor zones front/shadow-side/outer = 118 / 101 / 106
(min difference 5%), contact shadow ratio 0.50, face p99 251,
torso p99 163, under-glow low-body/torso 1.07x and feet/torso 0.92x,
rim band mean 56 (hot 208), rim bright pixels 37 = 0.000 of the body.

**Did not meet the bar:** floor_zones_differ_15pct, background_darkness_le_40, rim_3pct_of_body, rim_band_mean_ge_120, under_lowbody_1_3x_torso, under_feet_1_3x_torso.

**Emissive proof frame** (`XCOM_Chryssalid_emissive_only.png`, no scene lights,
emission x6.0, Fog Glow only): 1290 bright pixels, 0 clipped.

## XCOM_Muton

**Numbers:** clipped_white_pixels = **0**, clipped_body_pixels = **0**,
clipped_colour_pixels_non_emissive = **0**, emissive_pixels = **13915**,
rim_pixels = **59712**, background_darkness = **66.0**.

**Rig elements legible in this frame:** reveal_key, reveal_pool + contact shadow, emissives.

**Detail:** floor zones front/shadow-side/outer = 159 / 132 / 117
(min difference 11%), contact shadow ratio 0.35, face p99 213,
torso p99 237, under-glow low-body/torso 0.98x and feet/torso 0.50x,
rim band mean 97 (hot 215), rim bright pixels 764 = 0.012 of the body.

**Did not meet the bar:** floor_zones_differ_15pct, background_darkness_le_40, rim_3pct_of_body, rim_band_mean_ge_120, under_lowbody_1_3x_torso, under_feet_1_3x_torso.

**Emissive proof frame** (`XCOM_Muton_emissive_only.png`, no scene lights,
emission x6.0, Fog Glow only): 758 bright pixels, 0 clipped.

## XCOM_Floater

**Numbers:** clipped_white_pixels = **0**, clipped_body_pixels = **0**,
clipped_colour_pixels_non_emissive = **0**, emissive_pixels = **30**,
rim_pixels = **603**, background_darkness = **0.7**.

**Rig elements legible in this frame:** reveal_under, reveal_pool + contact shadow, emissives.

**Detail:** floor zones front/shadow-side/outer = 53 / 83 / 62
(min difference 14%), contact shadow ratio 0.16, face p99 0,
torso p99 74, under-glow low-body/torso 8.77x and feet/torso 0.80x,
rim band mean 7 (hot 167), rim bright pixels 13 = 0.001 of the body.

**Did not meet the bar:** floor_zones_differ_15pct, face_p99_ge_25, rim_3pct_of_body, rim_band_mean_ge_120, under_feet_1_3x_torso.

**Emissive proof frame** (`XCOM_Floater_emissive_only.png`, no scene lights,
emission x6.0, Fog Glow only): 513 bright pixels, 0 clipped.

## XCOM_Viper

**Numbers:** clipped_white_pixels = **344**, clipped_body_pixels = **344**,
clipped_colour_pixels_non_emissive = **0**, emissive_pixels = **75**,
rim_pixels = **84051**, background_darkness = **57.2**.

**Rig elements legible in this frame:** reveal_key, reveal_rim, reveal_pool + contact shadow, emissives.

**Detail:** floor zones front/shadow-side/outer = 151 / 122 / 127
(min difference 4%), contact shadow ratio 0.59, face p99 210,
torso p99 239, under-glow low-body/torso 1.26x and feet/torso 0.40x,
rim band mean 103 (hot 215), rim bright pixels 1333 = 0.032 of the body.

**Did not meet the bar:** no_clipped_white, no_clipped_body, floor_zones_differ_15pct, background_darkness_le_40, rim_band_mean_ge_120, under_lowbody_1_3x_torso, under_feet_1_3x_torso.

**Emissive proof frame** (`XCOM_Viper_emissive_only.png`, no scene lights,
emission x6.0, Fog Glow only): 48 bright pixels, 0 clipped.

## XCOM_Sectoid

**Numbers:** clipped_white_pixels = **895**, clipped_body_pixels = **895**,
clipped_colour_pixels_non_emissive = **0**, emissive_pixels = **10426**,
rim_pixels = **73563**, background_darkness = **54.2**.

**Rig elements legible in this frame:** reveal_key, reveal_pool + contact shadow, emissives.

**Detail:** floor zones front/shadow-side/outer = 152 / 114 / 109
(min difference 4%), contact shadow ratio 0.52, face p99 82,
torso p99 230, under-glow low-body/torso 0.63x and feet/torso 0.63x,
rim band mean 80 (hot 208), rim bright pixels 1269 = 0.018 of the body.

**Did not meet the bar:** no_clipped_white, no_clipped_body, floor_zones_differ_15pct, background_darkness_le_40, rim_3pct_of_body, rim_band_mean_ge_120, under_lowbody_1_3x_torso, under_feet_1_3x_torso.

**Emissive proof frame** (`XCOM_Sectoid_emissive_only.png`, no scene lights,
emission x6.0, Fog Glow only): 544 bright pixels, 0 clipped.

