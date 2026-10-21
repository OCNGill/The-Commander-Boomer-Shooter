using UnrealBuildTool;

public class TheCommanderGameTarget : TargetRules
{
    public TheCommanderGameTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Game;
        // D:/Unreal_Engine/UE_5.8 is an INSTALLED engine, so a unique build
        // environment is not available ("Targets with a unique build environment
        // cannot be built with an installed engine"). This target sets its own
        // DefaultBuildSettings / IncludeOrderVersion, which trips UBT's guard
        // against a project target modifying shared build settings, so the guard
        // is overridden here.
        bOverrideBuildEnvironment = true;
        DefaultBuildSettings = BuildSettingsVersion.V7;
        IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_8;

        ExtraModuleNames.Add("TheCommanderGame");
    }
}
