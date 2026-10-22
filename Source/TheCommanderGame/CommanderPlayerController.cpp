#include "CommanderPlayerController.h"

#include "CommanderCharacter.h"
#include "Engine/GameViewportClient.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/InputSettings.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerStart.h"
#include "InputCoreTypes.h"
#include "InputKeyEventArgs.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "HAL/PlatformMisc.h"
#include "TheCommanderGame.h"
#include "TimerManager.h"

ACommanderPlayerController::ACommanderPlayerController()
{
    bShowMouseCursor = false;
    bEnableClickEvents = false;
    bEnableMouseOverEvents = false;
    DefaultMouseCursor = EMouseCursor::Default;
}

void ACommanderPlayerController::BeginPlay()
{
    Super::BeginPlay();

    // Retro FPS input: gameplay only, mouse captured and hidden.
    FInputModeGameOnly InputMode;
    SetInputMode(InputMode);
    bShowMouseCursor = false;

    // FInputModeGameOnly only locks the mouse while the button is held down.
    // A shooter wants it locked for good, so set that on the viewport client
    // directly. FInputModeGameOnly has no cursor/lock setters of its own.
    if (UGameViewportClient* ViewportClient = GetWorld() ? GetWorld()->GetGameViewport() : nullptr)
    {
        ViewportClient->SetMouseLockMode(EMouseLockMode::LockAlways);
        ViewportClient->SetHideCursorDuringCapture(true);
    }

    UE_LOG(LogCommander, Log, TEXT("PlayerController %s ready: pawn=%s playerinput=%s"),
        *GetName(),
        *GetNameSafe(GetPawn()),
        *GetNameSafe(PlayerInput));

    if (FParse::Param(FCommandLine::Get(), TEXT("CommanderInputAudit")))
    {
        bInputAuditStarted = true;
        GetWorldTimerManager().SetTimerForNextTick(this, &ACommanderPlayerController::RunInputAudit);
    }
}

void ACommanderPlayerController::RunInputAudit()
{
    UWorld* World = GetWorld();
    if (World == nullptr)
    {
        return;
    }

    UE_LOG(LogCommander, Display, TEXT("=== COMMANDER INPUT AUDIT BEGIN ==="));
    UE_LOG(LogCommander, Display, TEXT("Map: %s"), *World->GetMapName());
    UE_LOG(LogCommander, Display, TEXT("GameMode: %s"), *GetNameSafe(World->GetAuthGameMode()));
    UE_LOG(LogCommander, Display, TEXT("PlayerController: %s"), *GetNameSafe(this));
    UE_LOG(LogCommander, Display, TEXT("Pawn: %s"), *GetNameSafe(GetPawn()));
    UE_LOG(LogCommander, Display, TEXT("PlayerInput: %s"), *GetNameSafe(PlayerInput));
    UE_LOG(LogCommander, Display, TEXT("InputComponent: %s"), *GetNameSafe(InputComponent));

    // The PlayerStart the pawn was spawned at, and the pawn itself.
    for (TActorIterator<APlayerStart> It(World); It; ++It)
    {
        UE_LOG(LogCommander, Display, TEXT("PlayerStart: %s at %s"), *It->GetName(), *It->GetActorLocation().ToCompactString());
    }

    // CommandedPawn, not Pawn: AController already has a Pawn member, and
    // shadowing it is a warning (C4458).
    if (const APawn* CommandedPawn = GetPawn())
    {
        UE_LOG(LogCommander, Display, TEXT("PawnLocationBefore: %s"), *CommandedPawn->GetActorLocation().ToCompactString());
        UE_LOG(LogCommander, Display, TEXT("PawnRotationBefore: %s"), *CommandedPawn->GetActorRotation().ToCompactString());
        UE_LOG(LogCommander, Display, TEXT("PawnVelocityBefore: %s"), *CommandedPawn->GetVelocity().ToCompactString());
    }

    // The mappings the live input stack resolved.
    if (const UInputSettings* InputSettings = GetDefault<UInputSettings>())
    {
        for (const FInputAxisKeyMapping& Axis : InputSettings->GetAxisMappings())
        {
            UE_LOG(LogCommander, Display, TEXT("AxisMapping: %s -> %s (scale %.2f)"),
                *Axis.AxisName.ToString(), *Axis.Key.GetDisplayName().ToString(), Axis.Scale);
        }
        for (const FInputActionKeyMapping& Action : InputSettings->GetActionMappings())
        {
            UE_LOG(LogCommander, Display, TEXT("ActionMapping: %s -> %s"),
                *Action.ActionName.ToString(), *Action.Key.GetDisplayName().ToString());
        }
    }

    // Simulate a real key press through the live player controller, so the
    // engine's own input stack does the work.
    InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::W, IE_Pressed, 1.0f));
    InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::MouseX, IE_Axis, 1.0f));

    GetWorldTimerManager().SetTimer(
        InputAuditTimerHandle,
        FTimerDelegate::CreateUObject(this, &ACommanderPlayerController::RunInputAuditAfterTick),
        0.25f,
        false);
}

void ACommanderPlayerController::RunInputAuditAfterTick()
{
    if (const APawn* CommandedPawn = GetPawn())
    {
        UE_LOG(LogCommander, Display, TEXT("PawnLocationAfter: %s"), *CommandedPawn->GetActorLocation().ToCompactString());
        UE_LOG(LogCommander, Display, TEXT("PawnRotationAfter: %s"), *CommandedPawn->GetActorRotation().ToCompactString());
        UE_LOG(LogCommander, Display, TEXT("PawnVelocityAfter: %s"), *CommandedPawn->GetVelocity().ToCompactString());
    }

    UE_LOG(LogCommander, Display, TEXT("ControlRotationAfter: %s"), *GetControlRotation().ToCompactString());

    // Release the simulated keys so a real session is not left holding W.
    InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::W, IE_Released, 0.0f));
    InputKey(FInputKeyEventArgs::CreateSimulated(EKeys::MouseX, IE_Released, 0.0f));

    UE_LOG(LogCommander, Display, TEXT("=== COMMANDER INPUT AUDIT END ==="));

    // Optional graceful exit. The engine writes the stable PSO cache during a
    // normal shutdown, so a run that is force-killed never produces one - and
    // the Steam Deck build needs that cache because vkd3d-proton cannot create
    // the runtime PSOs the game would otherwise build on first draw.
    if (FParse::Param(FCommandLine::Get(), TEXT("CommanderExitAfterAudit")))
    {
        constexpr float GracefulExitDelay = 5.0f;
        UE_LOG(LogCommander, Display, TEXT("=== COMMANDER GRACEFUL EXIT SCHEDULED (delay %.1fs) ==="), GracefulExitDelay);
        GetWorldTimerManager().SetTimer(
            CommanderExitTimerHandle,
            FTimerDelegate::CreateUObject(this, &ACommanderPlayerController::RequestGracefulExit),
            GracefulExitDelay,
            false);
    }
}

void ACommanderPlayerController::RequestGracefulExit()
{
    UE_LOG(LogCommander, Display, TEXT("=== COMMANDER GRACEFUL EXIT: ProjectSavedDir=%s ==="), *FPaths::ProjectSavedDir());
    UE_LOG(LogCommander, Display, TEXT("=== COMMANDER GRACEFUL EXIT: RequestExit(false) ==="));
    FGenericPlatformMisc::RequestExit(false);
}
