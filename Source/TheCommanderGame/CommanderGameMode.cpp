#include "CommanderGameMode.h"

#include "CommanderCharacter.h"
#include "CommanderPlayerController.h"
#include "TheCommanderGame.h"

ACommanderGameMode::ACommanderGameMode()
{
    PlayerControllerClass = ACommanderPlayerController::StaticClass();
    DefaultPawnClass = ACommanderCharacter::StaticClass();

    bStartPlayersAsSpectators = false;
}

void ACommanderGameMode::InitGame(const FString& MapName, const FString& Options, FString& ErrorMessage)
{
    Super::InitGame(MapName, Options, ErrorMessage);

    UE_LOG(LogCommander, Log, TEXT("ACommanderGameMode::InitGame map=%s controller=%s pawn=%s"),
        *MapName,
        *GetNameSafe(PlayerControllerClass),
        *GetNameSafe(DefaultPawnClass));
}
