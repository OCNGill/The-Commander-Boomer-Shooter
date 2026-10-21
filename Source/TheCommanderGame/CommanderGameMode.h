// The Commander - game mode.
//
// The packaged build ran on the engine's GameModeBase, whose default pawn is
// ADefaultPawn: a flyable sphere with no camera, no weapon and no character
// movement. This game mode names the real controller and the real character
// pawn instead, so a packaged .exe spawns a player that can move, look and
// shoot.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "CommanderGameMode.generated.h"

/**
 * Game mode for The Commander.
 *
 * PlayerControllerClass -> ACommanderPlayerController
 * DefaultPawnClass     -> ACommanderCharacter
 */
UCLASS()
class ACommanderGameMode : public AGameModeBase
{
    GENERATED_BODY()

public:
    ACommanderGameMode();

    virtual void InitGame(const FString& MapName, const FString& Options, FString& ErrorMessage) override;
};
