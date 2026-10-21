// The Commander - player character.
//
// A real, code-owned character pawn. The packaged build used to fall back to
// GameModeBase + ADefaultPawn (a flyable pawn with no camera and no weapon),
// so the demo .exe launched a player who could not move, look or shoot.
//
// The input axis and action names bound here are the ones declared in
// Config/DefaultInput.ini:
//   MoveForward / MoveRight / Turn / LookUp  (axis mappings)
//   Fire / Jump / Dash                       (action mappings)
// They are the stock Unreal character names, so the bindings are the same
// names the engine's own character templates use.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "CommanderCharacter.generated.h"

class UCameraComponent;
class UStaticMeshComponent;

/**
 * The Commander's player character.
 *
 * Camera is parented to the capsule and driven by the controller's control
 * rotation (pitch included), which is what makes the Turn / LookUp axis
 * mappings visible in the world.
 */
UCLASS()
class ACommanderCharacter : public ACharacter
{
    GENERATED_BODY()

public:
    ACommanderCharacter();

    virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;
    virtual void Tick(float DeltaSeconds) override;

    /** Axis handlers - bound to the MoveForward / MoveRight / Turn / LookUp axis mappings. */
    void MoveForward(float Value);
    void MoveRight(float Value);
    void Turn(float Value);
    void LookUp(float Value);

    /** Action handlers - bound to the Fire / Jump / Dash action mappings. */
    void OnFirePressed();
    void OnJumpPressed();
    void OnDashPressed();

protected:
    /** First person camera. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Commander")
    TObjectPtr<UCameraComponent> CommanderCamera;

    /** Visible body (engine basic shape) so the pawn is not an invisible capsule. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Commander")
    TObjectPtr<UStaticMeshComponent> CommanderBody;

private:
    /** Seconds remaining before the next dash is allowed. */
    float DashCooldown = 0.0f;
};
