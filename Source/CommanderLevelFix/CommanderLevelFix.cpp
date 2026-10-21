#include "CommanderLevelFix.h"

DEFINE_LOG_CATEGORY(LogCommanderLevelFix);

void FCommanderLevelFixModule::StartupModule()
{
    UE_LOG(LogCommanderLevelFix, Log, TEXT("CommanderLevelFix module started"));
}

void FCommanderLevelFixModule::ShutdownModule()
{
    UE_LOG(LogCommanderLevelFix, Log, TEXT("CommanderLevelFix module shut down"));
}

IMPLEMENT_MODULE(FCommanderLevelFixModule, CommanderLevelFix);
