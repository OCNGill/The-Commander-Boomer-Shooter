// The Commander - runtime level-fix module.
//
// Content/Maps/M_Blockout01.umap is FROZEN (other lanes read it, and it must stay
// byte-identical to HEAD). The level defects the design needs fixed - the pit
// rim that walls the hole in, the pit ramp that leaves a 0.25 m lip, the
// pillar climb whose ledges are 120 degrees apart around a solid post, the
// missing cover around the pillar, and the keycard that is a 7-pixel speck -
// are therefore applied AT RUNTIME by this module, not by editing the map.
//
// Gameplay only: no editor-only APIs, so the module cooks and runs in a
// packaged build.
//
// The fix values are mirrored in Tools/blender/render_level.py so the offline
// renders and the shipped game agree. Tools/python/check_level_fixes.py
// compares the two so they cannot silently drift.

using UnrealBuildTool;

public class CommanderLevelFix : ModuleRules
{
    public CommanderLevelFix(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

        // Let the module's own headers resolve by short name from this
        // module's root, not only from Public/ and Classes/.
        PublicIncludePaths.Add(ModuleDirectory);

        PublicDependencyModuleNames.AddRange(new string[]
        {
            "Core",
            "CoreUObject",
            "Engine",
        });
    }
}
