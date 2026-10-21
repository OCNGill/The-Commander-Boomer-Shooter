// The Commander - the single source of truth for the runtime level fixes.
//
// These values are mirrored in Tools/blender/render_level.py (LEVEL_FIXES) so
// the offline renders and the shipped game agree. Tools/python/check_level_fixes.py
// parses the LEVEL_FIXES block below and compares it with the Python dict, so
// the two cannot silently drift.
//
// Units: metres unless a name says otherwise. The map dump (Docs/generated/
// level_transforms.json) stores Unreal units (cm); 1 m = 100 uu.

#pragma once

#include "CoreMinimal.h"

namespace CommanderLevelFixValues
{
	// ---------------------------------------------------------------------
	// LEVEL_FIXES_BEGIN
	// (parsed by Tools/python/check_level_fixes.py - keep this block in
	//  "Key=Value" form, one per line, no units in the value)
	// ---------------------------------------------------------------------

	// Arena floor surface height, and the pit floor surface height. The pit
	// is a real 1.00 m recess: BO_Floor_N/S/E/W leave X -15.25..-8.75,
	// Y -15.25..-10.75 open and BO_PitFloor tops out 1.00 m below grade.
	// Ebert: the map is right here; the renderer drew one unbroken slab.
	ArenaFloorTopM = 0.00
	PitFloorTopM = -1.00

	// The five BO_PitRim blocks are 1x1x2 m posts whose tops stand 1.00 m
	// above the floor, so the pit reads as a walled pen on flat ground
	// instead of a hole. Lower them to a lip: the post still reaches the pit
	// floor, but only 0.25 m of it stands above grade.
	PitRimHeightAboveFloorM = 0.25

	// BO_Ramp_Pit is a 0.50 m thick slab rolled 29.055 degrees. Its top face
	// stands 0.25 m proud of the arena floor, so the exit is a lip rather
	// than a flush landing. Sink it by half its thickness: the top face then
	// lands exactly on the flight line, flush with the arena floor at the
	// east rim and flush with the pit floor at the bottom.
	PitRampLowerM = 0.25

	// The pillar climb. BO_Pillar_Center is a solid 4.00 m cylinder 6.00 m
	// tall and the three ledges sit at 30, 150 and 270 degrees around it,
	// 3.28 m edge to edge, with the pillar body between them - not
	// traversable. Re-space them to a 60 degree spiral on a 3.20 m radius:
	// consecutive ledges are 1.80 m apart edge to edge and the jump arc
	// clears the pillar body. Ledge top heights are unchanged (2.00, 3.90,
	// 5.80 m), so the vertical rises stay inside the 2.50 m jump budget and
	// the last hop onto the pillar top is 0.20 m.
	PillarLedgeRadiusM = 3.20
	PillarLedgeAngle1Deg = 30
	PillarLedgeAngle2Deg = 90
	PillarLedgeAngle3Deg = 150

	// There are ZERO BO_Cover actors within 8 m of the pillar axis, so the
	// fight at the pillar has no cover. Add two blocks on the east/west
	// tangent lines, 7.50 m out - inside 8 m of the axis, clear of the
	// ledge spiral and of the drop-to-pillar sight line.
	PillarCoverX = 7.50
	PillarCoverY = 0.00
	PillarCoverSizeM = 3.00
	PillarCoverHeightM = 1.00

	// The keycard is a 0.55 m emissive cube 6.80 x 9.00 px at 38 m: a
	// 7-pixel speck, off-frame in four of six ground frames. Give the
	// pillar top a landmark: a light column beside the keycard, lit, so the
	// objective reads from anywhere on the arena floor.
	PillarTopZ = 6.00
	BeaconHeightM = 2.60
	BeaconRadiusM = 0.18
	BeaconOffsetX = 1.40
	BeaconOffsetY = 1.40
	BeaconLightIntensity = 4000.00

	// ---------------------------------------------------------------------
	// LEVEL_FIXES_END
	// ---------------------------------------------------------------------

	// Convenience values derived from the block above.
	// The rim posts keep their feet on the pit floor and their heads just
	// above the arena floor, so the hole reads as a hole.
	inline constexpr float PitRimTopZ = PitRimHeightAboveFloorM;
	inline constexpr float PitRimBottomZ = PitFloorTopM;
	inline constexpr float PitRimHeightM = PitRimTopZ - PitRimBottomZ;
}
