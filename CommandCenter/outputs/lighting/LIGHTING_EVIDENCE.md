# Lighting Evidence (v4 reveal rig)

Generated 2026-10-21 09:34 by `Tools/blender/rig_evidence.py`.

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
clipped_colour_pixels_non_emissive = **24**, emissive_pixels = **16060**,
rim_pixels = **5324**, background_darkness = **5.2**.

**Rig elements legible in this frame:** reveal_key, reveal_rim, emissives.

**Detail:** floor zones front/shadow-side/outer = 61 / 9 / 87
(min difference 30%), contact shadow ratio 0.24, face p99 252,
torso p99 216, under-glow low-body/torso 0.86x and feet/torso 1.02x,
rim band mean 57 (hot 214), rim bright pixels 1349 = 0.030 of the body.

**Did not meet the bar:** no_colour_clip_off_emissive, floor_zones_in_window, rim_band_mean_ge_120, under_lowbody_1_3x_torso, under_feet_1_3x_torso.

**Emissive proof frame** (`XCOM_Chryssalid_emissive_only.png`, no scene lights,
emission x2.0, Fog Glow only): 0 bright pixels, 0 clipped.

## XCOM_Muton

**Numbers:** clipped_white_pixels = **0**, clipped_body_pixels = **0**,
clipped_colour_pixels_non_emissive = **0**, emissive_pixels = **38523**,
rim_pixels = **13474**, background_darkness = **16.8**.

**Rig elements legible in this frame:** reveal_key, reveal_rim, reveal_pool + contact shadow, emissives.

**Detail:** floor zones front/shadow-side/outer = 71 / 60 / 171
(min difference 16%), contact shadow ratio 0.25, face p99 233,
torso p99 231, under-glow low-body/torso 1.01x and feet/torso 0.29x,
rim band mean 96 (hot 214), rim bright pixels 2471 = 0.038 of the body.

**Did not meet the bar:** rim_band_mean_ge_120, under_lowbody_1_3x_torso, under_feet_1_3x_torso.

**Emissive proof frame** (`XCOM_Muton_emissive_only.png`, no scene lights,
emission x2.0, Fog Glow only): 0 bright pixels, 0 clipped.

## XCOM_Floater

**Numbers:** clipped_white_pixels = **0**, clipped_body_pixels = **0**,
clipped_colour_pixels_non_emissive = **0**, emissive_pixels = **66673**,
rim_pixels = **121091**, background_darkness = **28.9**.

**Rig elements legible in this frame:** reveal_pool + contact shadow, emissives.

**Detail:** floor zones front/shadow-side/outer = 129 / 56 / 141
(min difference 8%), contact shadow ratio 0.38, face p99 0,
torso p99 56, under-glow low-body/torso 0.62x and feet/torso 1.12x,
rim band mean 26 (hot 200), rim bright pixels 39 = 0.004 of the body.

**Did not meet the bar:** floor_zones_differ_15pct, face_p99_ge_25, rim_3pct_of_body, rim_band_mean_ge_120, under_lowbody_1_3x_torso, under_feet_1_3x_torso.

**Emissive proof frame** (`XCOM_Floater_emissive_only.png`, no scene lights,
emission x2.0, Fog Glow only): 0 bright pixels, 0 clipped.

## XCOM_Viper

**Numbers:** clipped_white_pixels = **0**, clipped_body_pixels = **0**,
clipped_colour_pixels_non_emissive = **0**, emissive_pixels = **40212**,
rim_pixels = **14525**, background_darkness = **16.3**.

**Rig elements legible in this frame:** reveal_key, reveal_rim, reveal_pool + contact shadow, emissives.

**Detail:** floor zones front/shadow-side/outer = 74 / 54 / 171
(min difference 27%), contact shadow ratio 0.45, face p99 218,
torso p99 223, under-glow low-body/torso 1.11x and feet/torso 0.21x,
rim band mean 104 (hot 212), rim bright pixels 2774 = 0.067 of the body.

**Did not meet the bar:** rim_band_mean_ge_120, under_lowbody_1_3x_torso, under_feet_1_3x_torso.

**Emissive proof frame** (`XCOM_Viper_emissive_only.png`, no scene lights,
emission x2.0, Fog Glow only): 0 bright pixels, 0 clipped.

## XCOM_Sectoid

**Numbers:** clipped_white_pixels = **313**, clipped_body_pixels = **313**,
clipped_colour_pixels_non_emissive = **0**, emissive_pixels = **37998**,
rim_pixels = **14305**, background_darkness = **15.7**.

**Rig elements legible in this frame:** reveal_key, reveal_under, emissives.

**Detail:** floor zones front/shadow-side/outer = 89 / 24 / 206
(min difference 57%), contact shadow ratio 0.41, face p99 236,
torso p99 227, under-glow low-body/torso 1.43x and feet/torso 1.15x,
rim band mean 86 (hot 218), rim bright pixels 2099 = 0.029 of the body.

**Did not meet the bar:** no_clipped_white, no_clipped_body, floor_zones_in_window, rim_3pct_of_body, rim_band_mean_ge_120, under_feet_1_3x_torso.

**Emissive proof frame** (`XCOM_Sectoid_emissive_only.png`, no scene lights,
emission x2.0, Fog Glow only): 0 bright pixels, 0 clipped.

