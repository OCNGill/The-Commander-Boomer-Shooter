#include "TheCommanderGame.h"

DEFINE_LOG_CATEGORY(LogCommander);

void FTheCommanderGameModule::StartupModule()
{
    UE_LOG(LogCommander, Log, TEXT("TheCommanderGame module started"));
}

void FTheCommanderGameModule::ShutdownModule()
{
    UE_LOG(LogCommander, Log, TEXT("TheCommanderGame module shut down"));
}

IMPLEMENT_PRIMARY_GAME_MODULE(FTheCommanderGameModule, TheCommanderGame, "TheCommanderGame");
