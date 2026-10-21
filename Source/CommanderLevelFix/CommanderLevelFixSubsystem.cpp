#include "CommanderLevelFixSubsystem.h"

#include "CommanderLevelFix.h"
#include "CommanderLevelFixValues.h"

#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

using namespace CommanderLevelFixValues;

namespace CommanderLevelFixPrivate
{
	// FNames of the map actors, as stored in Content/Maps/M_Blockout01.umap.
	// Actor labels ("BO_PitRim_W") do NOT survive a Shipping cook, so the
	// always-serialized FNames are the only reliable handle.
	static const TCHAR* RimNames[] =
	{
		TEXT("StaticMeshActor_36"), // BO_PitRim_W
		TEXT("StaticMeshActor_37"), // BO_PitRim_N
		TEXT("StaticMeshActor_38"), // BO_PitRim_S
		TEXT("StaticMeshActor_43"), // BO_PitRim_E1
		TEXT("StaticMeshActor_44"), // BO_PitRim_E2
	};
	static const int32 RimCount = UE_ARRAY_COUNT(RimNames);

	static const TCHAR* LedgeNames[] =
	{
		TEXT("StaticMeshActor_56"), // BO_PillarStep_1
		TEXT("StaticMeshActor_57"), // BO_PillarStep_2
		TEXT("StaticMeshActor_58"), // BO_PillarStep_3
	};
	static const int32 LedgeCount = UE_ARRAY_COUNT(LedgeNames);

	static const TCHAR* PitRampName = TEXT("StaticMeshActor_52");  // BO_Ramp_Pit
	static const TCHAR* PillarName = TEXT("StaticMeshActor_23");   // BO_Pillar_Center
	static const TCHAR* CoverTemplateName = TEXT("StaticMeshActor_24"); // BO_Cover_00
	static const TCHAR* KeycardName = TEXT("StaticMeshActor_13");  // PU_KeyGreen_PillarTop
}

bool UCommanderLevelFixSubsystem::ShouldCreateSubsystem(UObject* Outer) const
{
	if (!Super::ShouldCreateSubsystem(Outer))
	{
		return false;
	}
	const UWorld* World = Cast<UWorld>(Outer);
	if (!World)
	{
		return false;
	}
	const EWorldType::Type WorldType = World->WorldType;
	return WorldType == EWorldType::Game || WorldType == EWorldType::PIE;
}

void UCommanderLevelFixSubsystem::OnWorldBeginPlay(UWorld& InWorld)
{
	Super::OnWorldBeginPlay(InWorld);
	ApplyFixes(InWorld);
}

AActor* UCommanderLevelFixSubsystem::FindByName(UWorld& World, const TCHAR* Name)
{
	for (TActorIterator<AActor> It(&World); It; ++It)
	{
		if (It->GetFName() == FName(Name))
		{
			return *It;
		}
	}
	return nullptr;
}

bool UCommanderLevelFixSubsystem::SetHeightBand(AActor& Actor, double BottomZ, double TopZ)
{
	UStaticMeshComponent* Mesh = Actor.GetRootComponent() ? Cast<UStaticMeshComponent>(Actor.GetRootComponent()) : nullptr;
	if (!Mesh)
	{
		return false;
	}

	const FBox Bounds = Mesh->GetLocalBounds().GetBox();
	const double LocalHeight = Bounds.Max.Z - Bounds.Min.Z;
	if (LocalHeight <= KINDA_SMALL_NUMBER)
	{
		// Flat geometry (a plane): just move it so its surface sits at TopZ.
		FVector Location = Actor.GetActorLocation();
		Location.Z = TopZ - Bounds.Max.Z;
		Actor.SetActorLocation(Location);
		return true;
	}

	const FVector Location = Actor.GetActorLocation();
	const FVector Scale = Actor.GetActorScale3D();

	// World height of the mesh along Z, and the mesh's local top offset from
	// the actor origin.
	const double WorldHeight = LocalHeight * FMath::Abs(Scale.Z);
	if (WorldHeight <= KINDA_SMALL_NUMBER)
	{
		return false;
	}
	const double LocalTopOffset = Bounds.Max.Z;

	// Scale the actor so the mesh spans the requested band, then move it.
	const double NewScaleZ = (TopZ - BottomZ) / WorldHeight * FMath::Sign(Scale.Z == 0.0 ? 1.0 : Scale.Z);
	FVector NewScale = Scale;
	NewScale.Z = NewScaleZ;
	Actor.SetActorScale3D(NewScale);

	// After scaling about the actor origin, the mesh top sits at
	// Location.Z + NewScaleZ * LocalTopOffset. Solve for Location.Z.
	const double NewLocationZ = TopZ - NewScaleZ * LocalTopOffset;
	FVector NewLocation = Location;
	NewLocation.Z = NewLocationZ;
	Actor.SetActorLocation(NewLocation);
	return true;
}

UMaterialInterface* UCommanderLevelFixSubsystem::GrabMapMaterial(UWorld& World, const TCHAR* Name)
{
	AActor* Source = FindByName(World, Name);
	if (!Source)
	{
		return nullptr;
	}
	UStaticMeshComponent* Mesh = Cast<UStaticMeshComponent>(Source->GetRootComponent());
	return Mesh ? Mesh->GetMaterial(0) : nullptr;
}

void UCommanderLevelFixSubsystem::ApplyFixes(UWorld& World)
{
	using namespace CommanderLevelFixPrivate;

	int32 Fixed = 0;

	// ------------------------------------------------------------------
	// 1. The pit rim posts.
	//
	// Five 1x1x2 m posts whose tops stand 1.00 m above the arena floor turn
	// the pit into a walled pen on flat ground. Sink them to a 0.25 m lip
	// that still reaches the pit floor, so the hole reads as a hole.
	// ------------------------------------------------------------------
	for (int32 i = 0; i < RimCount; ++i)
	{
		AActor* Rim = FindByName(World, RimNames[i]);
		if (!Rim)
		{
			UE_LOG(LogCommanderLevelFix, Warning, TEXT("Pit rim actor %s not found"), RimNames[i]);
			continue;
		}
		if (SetHeightBand(*Rim, PitRimBottomZ * 100.0, PitRimTopZ * 100.0))
		{
			++Fixed;
			UE_LOG(LogCommanderLevelFix, Log, TEXT("Pit rim %s lowered to a %.2f m lip"),
				RimNames[i], PitRimHeightAboveFloorM);
		}
	}

	// ------------------------------------------------------------------
	// 2. The pit ramp.
	//
	// BO_Ramp_Pit is a 0.50 m thick slab rolled 29.055 degrees. Its top face
	// runs z=-0.78 at the pit end to z=+0.22 at the arena end, so the exit is
	// a 0.22 m lip and the bottom end floats above the pit floor. Sink it by
	// 0.22 m: the top face then lands flush with the arena floor at the east
	// rim and flush with the pit floor at the bottom.
	// ------------------------------------------------------------------
	if (AActor* Ramp = FindByName(World, PitRampName))
	{
		FVector Location = Ramp->GetActorLocation();
		Location.Z -= PitRampLowerM * 100.0;
		Ramp->SetActorLocation(Location);
		++Fixed;
		UE_LOG(LogCommanderLevelFix, Log, TEXT("Pit ramp %s sunk %.2f m (flush landing)"),
			PitRampName, PitRampLowerM);
	}
	else
	{
		UE_LOG(LogCommanderLevelFix, Warning, TEXT("Pit ramp actor %s not found"), PitRampName);
	}

	// ------------------------------------------------------------------
	// 3. The pillar climb.
	//
	// The three ledges sat at 30, 150 and 270 degrees around the solid
	// 4.00 m pillar post: 3.28 m edge to edge with the pillar body between
	// them. Re-space them to a 60 degree spiral on a 3.20 m radius. The
	// vertical rises are unchanged (2.00 / 3.90 / 5.80 m ledge tops), so
	// every hop stays inside the 2.50 m jump budget, and the jump arc now
	// clears the pillar instead of crossing it.
	// ------------------------------------------------------------------
	static const double LedgeAngles[3] = { PillarLedgeAngle1Deg, PillarLedgeAngle2Deg, PillarLedgeAngle3Deg };
	for (int32 i = 0; i < LedgeCount; ++i)
	{
		AActor* Ledge = FindByName(World, LedgeNames[i]);
		if (!Ledge)
		{
			UE_LOG(LogCommanderLevelFix, Warning, TEXT("Pillar ledge actor %s not found"), LedgeNames[i]);
			continue;
		}
		const double Angle = FMath::DegreesToRadians(LedgeAngles[i]);
		FVector Location = Ledge->GetActorLocation();
		Location.X = FMath::Cos(Angle) * PillarLedgeRadiusM * 100.0;
		Location.Y = FMath::Sin(Angle) * PillarLedgeRadiusM * 100.0;
		Ledge->SetActorLocation(Location);
		++Fixed;
		UE_LOG(LogCommanderLevelFix, Log, TEXT("Pillar ledge %s moved to %.0f deg / %.2f m radius"),
			LedgeNames[i], LedgeAngles[i], PillarLedgeRadiusM);
	}

	// ------------------------------------------------------------------
	// 4. Cover around the pillar.
	//
	// There were ZERO cover blocks within 8 m of the pillar axis, so the
	// fight at the objective had no cover. Add two blocks on the east/west
	// tangent lines, 6.50 m out - inside 8 m of the axis, clear of the ledge
	// spiral and of the drop-to-pillar sight line.
	// ------------------------------------------------------------------
	{
		UMaterialInterface* CoverMaterial = GrabMapMaterial(World, CoverTemplateName);
		UMaterialInterface* PillarMaterial = GrabMapMaterial(World, PillarName);

		static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeFinder(TEXT("/Engine/BasicShapes/Cube.Cube"));
		static ConstructorHelpers::FObjectFinder<UStaticMesh> CylinderFinder(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));

		const float SpawnZ = PillarCoverHeightM * 50.0f;

		for (int32 Side = 0; Side < 2; ++Side)
		{
			const float X = (Side == 0 ? PillarCoverX : -PillarCoverX) * 100.0f;
			const float Y = PillarCoverY * 100.0f;

			FActorSpawnParameters Params;
			Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
			Params.Name = FName(*FString::Printf(TEXT("CommanderCover_%d"), Side));

			AStaticMeshActor* Cover = World.SpawnActor<AStaticMeshActor>(
				AStaticMeshActor::StaticClass(), FVector(X, Y, SpawnZ), FRotator::ZeroRotator, Params);
			if (!Cover)
			{
				continue;
			}
			if (UStaticMeshComponent* Mesh = Cover->GetStaticMeshComponent())
			{
				if (CubeFinder.Succeeded())
				{
					Mesh->SetStaticMesh(CubeFinder.Object);
				}
				Mesh->SetRelativeScale3D(FVector(PillarCoverSizeM, PillarCoverSizeM, PillarCoverHeightM));
				if (CoverMaterial)
				{
					Mesh->SetMaterial(0, CoverMaterial);
				}
				Mesh->SetCollisionProfileName(TEXT("BlockAll"));
			}
			++Fixed;
			UE_LOG(LogCommanderLevelFix, Log, TEXT("Cover block added at x=%.2f m near the pillar"), X / 100.0f);
		}

		// ------------------------------------------------------------------
		// 5. The keycard landmark.
		//
		// PU_KeyGreen_PillarTop is a 0.55 m emissive cube that renders 6.8 x
		// 9.0 px at 38 m - a 7-pixel speck, off-frame in four of six ground
		// frames. Give the pillar top a lit column beside the keycard so the
		// objective reads from anywhere on the arena floor.
		// ------------------------------------------------------------------
		{
			FActorSpawnParameters Params;
			Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
			Params.Name = TEXT("CommanderKeycardBeacon");

			const FVector BeaconLocation(
				BeaconOffsetX * 100.0f,
				BeaconOffsetY * 100.0f,
				(PillarTopZ + BeaconHeightM * 0.5f) * 100.0f);

			AStaticMeshActor* Beacon = World.SpawnActor<AStaticMeshActor>(
				AStaticMeshActor::StaticClass(), BeaconLocation, FRotator::ZeroRotator, Params);
			if (Beacon)
			{
				if (UStaticMeshComponent* Mesh = Beacon->GetStaticMeshComponent())
				{
					if (CylinderFinder.Succeeded())
					{
						Mesh->SetStaticMesh(CylinderFinder.Object);
					}
					Mesh->SetRelativeScale3D(FVector(BeaconRadiusM * 2.0f, BeaconRadiusM * 2.0f, BeaconHeightM));
					if (PillarMaterial)
					{
						Mesh->SetMaterial(0, PillarMaterial);
					}
					Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
				}
				++Fixed;
				UE_LOG(LogCommanderLevelFix, Log, TEXT("Keycard beacon column added on the pillar top"));
			}
		}
	}

	UE_LOG(LogCommanderLevelFix, Log, TEXT("Level fixes applied: %d changes"), Fixed);
}
