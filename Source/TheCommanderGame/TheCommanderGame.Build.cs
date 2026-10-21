// The Commander - runtime game module.
// Kept deliberately small: gameplay only (character, weapon, enemy, game mode, HUD).
// No editor-only APIs, so the module cooks and runs in a packaged build.

using UnrealBuildTool;

public class TheCommanderGame : ModuleRules
{
    public TheCommanderGame(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

        // Let the module's own headers resolve by short name (e.g. "TheCommanderGame.h")
        // from this module's root, not only from Public/ and Classes/.
        PublicIncludePaths.Add(ModuleDirectory);

        PublicDependencyModuleNames.AddRange(new string[]
        {
            "Core",
            "CoreUObject",
            "Engine",
            "InputCore",
        });

        PrivateDependencyModuleNames.AddRange(new string[]
        {
            "Slate",
            "SlateCore",
        });
    }
}
