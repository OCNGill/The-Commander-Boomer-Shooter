#include "CommanderCharacter.h"

#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/Controller.h"
#include "Math/RotationMatrix.h"
#include "TheCommanderGame.h"
#include "UObject/ConstructorHelpers.h"

ACommanderCharacter::ACommanderCharacter()
{
    PrimaryActorTick.bCanEverTick = true;

    GetCapsuleComponent()->InitCapsuleSize(34.0f, 88.0f);

    // Yaw comes from the controller (mouse), pitch from the camera only.
    bUseControllerRotationPitch = false;
    bUseControllerRotationYaw = true;
    bUseControllerRotationRoll = false;

    if (UCharacterMovementComponent* Movement = GetCharacterMovement())
    {
        Movement->bOrientRotationToMovement = false;
        Movement->MaxWalkSpeed = 600.0f;
        Movement->JumpZVelocity = 500.0f;
        Movement->AirControl = 0.35f;
    }

    // A visible body. The project has no player skeletal mesh yet, so use the
    // engine's basic capsule shape - it is always cooked and always loads.
    CommanderBody = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("CommanderBody"));
    if (CommanderBody)
    {
        CommanderBody->SetupAttachment(GetCapsuleComponent());
        CommanderBody->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        CommanderBody->SetRelativeLocation(FVector(0.0f, 0.0f, 8.0f));
        CommanderBody->SetRelativeScale3D(FVector(0.8f, 0.8f, 0.9f));

        // UE 5.8 does not ship /Engine/BasicShapes/Capsule.uasset - the folder
        // holds only Cone, Cube, Cube1, Cylinder, Plane and Sphere. Pointing
        // FObjectFinder at the missing asset made the CDO constructor fail and
        // left the player with no visible body. Use the cylinder instead; it is
        // always cooked and reads as a torso under the capsule collision.
        static ConstructorHelpers::FObjectFinder<UStaticMesh> BodyMesh(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
        if (BodyMesh.Succeeded())
        {
            CommanderBody->SetStaticMesh(BodyMesh.Object);
        }
    }

    CommanderCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("CommanderCamera"));
    if (CommanderCamera)
    {
        CommanderCamera->SetupAttachment(GetCapsuleComponent());
        CommanderCamera->SetRelativeLocation(FVector(0.0f, 0.0f, 64.0f));
        CommanderCamera->bUsePawnControlRotation = true;
    }
}

void ACommanderCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
    Super::SetupPlayerInputComponent(PlayerInputComponent);

    if (!PlayerInputComponent)
    {
        return;
    }

    // Axis mappings - names must match Config/DefaultInput.ini exactly.
    PlayerInputComponent->BindAxis(TEXT("MoveForward"), this, &ACommanderCharacter::MoveForward);
    PlayerInputComponent->BindAxis(TEXT("MoveRight"), this, &ACommanderCharacter::MoveRight);
    PlayerInputComponent->BindAxis(TEXT("Turn"), this, &ACommanderCharacter::Turn);
    PlayerInputComponent->BindAxis(TEXT("LookUp"), this, &ACommanderCharacter::LookUp);

    // Action mappings - names must match Config/DefaultInput.ini exactly.
    PlayerInputComponent->BindAction(TEXT("Fire"), IE_Pressed, this, &ACommanderCharacter::OnFirePressed);
    PlayerInputComponent->BindAction(TEXT("Jump"), IE_Pressed, this, &ACommanderCharacter::OnJumpPressed);
    PlayerInputComponent->BindAction(TEXT("Dash"), IE_Pressed, this, &ACommanderCharacter::OnDashPressed);
}

void ACommanderCharacter::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);

    if (DashCooldown > 0.0f)
    {
        DashCooldown = FMath::Max(0.0f, DashCooldown - DeltaSeconds);
    }
}

void ACommanderCharacter::MoveForward(float Value)
{
    if (Controller == nullptr || Value == 0.0f)
    {
        return;
    }

    const FRotator YawRotation(0.0f, Controller->GetControlRotation().Yaw, 0.0f);
    AddMovementInput(FRotationMatrix(YawRotation).GetUnitAxis(EAxis::X), Value);
}

void ACommanderCharacter::MoveRight(float Value)
{
    if (Controller == nullptr || Value == 0.0f)
    {
        return;
    }

    const FRotator YawRotation(0.0f, Controller->GetControlRotation().Yaw, 0.0f);
    AddMovementInput(FRotationMatrix(YawRotation).GetUnitAxis(EAxis::Y), Value);
}

void ACommanderCharacter::Turn(float Value)
{
    if (Value != 0.0f)
    {
        AddControllerYawInput(Value);
    }
}

void ACommanderCharacter::LookUp(float Value)
{
    if (Value != 0.0f)
    {
        AddControllerPitchInput(Value);
    }
}

void ACommanderCharacter::OnFirePressed()
{
    UWorld* World = GetWorld();
    if (World == nullptr)
    {
        return;
    }

    const FVector Start = CommanderCamera ? CommanderCamera->GetComponentLocation() : GetActorLocation();
    const FVector End = Start + GetActorForwardVector() * 10000.0f;

    FHitResult Hit;
    FCollisionQueryParams Params(SCENE_QUERY_STAT(CommanderFire), true, this);
    if (World->LineTraceSingleByChannel(Hit, Start, End, ECC_Visibility, Params))
    {
        UE_LOG(LogCommander, Log, TEXT("Fire: hit %s at %s"), *Hit.GetActor()->GetName(), *Hit.ImpactPoint.ToCompactString());
    }
    else
    {
        UE_LOG(LogCommander, Verbose, TEXT("Fire: no hit along %s"), *End.ToCompactString());
    }
}

void ACommanderCharacter::OnJumpPressed()
{
    Jump();
}

void ACommanderCharacter::OnDashPressed()
{
    if (DashCooldown > 0.0f)
    {
        return;
    }

    DashCooldown = 1.0f;

    if (UCharacterMovementComponent* Movement = GetCharacterMovement())
    {
        Movement->Launch(GetActorForwardVector() * 900.0f);
        UE_LOG(LogCommander, Log, TEXT("Dash: launched forward"));
    }
}
