using UnrealBuildTool;

public class TheCommanderGameEditorTarget : TargetRules
{
    public TheCommanderGameEditorTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Editor;
        // D:/Unreal_Engine/UE_5.8 is an INSTALLED engine, so a unique build
        // environment is not available. See TheCommanderGame.Target.cs.
        bOverrideBuildEnvironment = true;
        DefaultBuildSettings = BuildSettingsVersion.V7;
        IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_8;

        ExtraModuleNames.Add("TheCommanderGame");
    }
}
