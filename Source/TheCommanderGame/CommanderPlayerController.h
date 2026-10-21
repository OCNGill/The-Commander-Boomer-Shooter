// The Commander - player controller.
//
// The packaged build used to run with the engine's default APlayerController
// and the legacy UPlayerInput class, which is what produced the engine log
// warning:
//   "UEnhancedInputLocalPlayerSubsystem for Local Player 'LocalPlayer_0' does
//    not have a valid PlayerInput object."
//
// The fix has two halves:
//   1. Config/DefaultInput.ini sets DefaultPlayerInputClass to
//      /Script/EnhancedInput.EnhancedPlayerInput, so the local player owns a
//      real EnhancedPlayerInput and the subsystem warning disappears.
//   2. This controller sets the gameplay input mode (mouse captured, no
//      cursor) so the mouse axes in DefaultInput.ini actually reach the pawn.
//
// The axis and action BINDINGS live on the pawn
// (ACommanderCharacter::SetupPlayerInputComponent), because that is where
// the engine expects a character's movement bindings to be.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "TimerManager.h"
#include "CommanderPlayerController.generated.h"

/**
 * Player controller for The Commander.
 *
 * Owns the input mode for the game and hosts the in-engine input audit
 * (enabled with the -CommanderInputAudit command line switch) which prints
 * the resolved mappings and the pawn's real response to a simulated input.
 */
UCLASS()
class ACommanderPlayerController : public APlayerController
{
    GENERATED_BODY()

public:
    ACommanderPlayerController();

    virtual void BeginPlay() override;

    /** Print the live input state, then simulate a real key press and re-read it. */
    void RunInputAudit();

    /** Second half of the audit: read the pawn after the simulated input ticked. */
    void RunInputAuditAfterTick();

protected:
    /** True once the audit has been kicked off. */
    bool bInputAuditStarted = false;

    /** Handle for the audit's follow-up timer. */
    FTimerHandle InputAuditTimerHandle;
};
