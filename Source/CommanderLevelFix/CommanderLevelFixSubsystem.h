// The Commander - runtime application of the level fixes.
//
// Content/Maps/M_Blockout01.umap is FROZEN: other lanes read it and it must
// stay byte-identical to HEAD. The level defects the design needs fixed are
// therefore applied at RUNTIME, here, by actor FName (labels do not survive a
// Shipping cook).
//
// Gameplay only - no editor-only APIs - so this runs in a packaged build.
//
// The fix values live in CommanderLevelFixValues.h and are mirrored in
// Tools/blender/render_level.py so the offline renders and the shipped game
// agree. Tools/python/check_level_fixes.py compares the two.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "CommanderLevelFixSubsystem.generated.h"

class AActor;
class UMaterialInterface;
class UStaticMeshComponent;
class UStaticMesh;

/**
 * Applies the level fixes to the blockout map at world begin play:
 *
 *  - the five BO_PitRim segments stop walling the pit in and become a 0.25 m lip
 *  - BO_Ramp_Pit is sunk so its top face is flush with the arena floor
 *  - the three BO_PillarStep ledges are re-spaced into a traversable spiral
 *  - two cover blocks are added within 8 m of the pillar axis
 *  - a lit beacon column is added beside the keycard on the pillar top
 */
UCLASS()
class UCommanderLevelFixSubsystem : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	UCommanderLevelFixSubsystem(const FObjectInitializer& ObjectInitializer);

	virtual bool ShouldCreateSubsystem(UObject* Outer) const override;
	virtual void OnWorldBeginPlay(UWorld& InWorld) override;

	/**
	 * Re-applies the fixes to this subsystem's world. Exposed so a game mode can
	 * call it after a level load. Takes no arguments: a Blueprint-callable
	 * function cannot take a UWorld reference, and UWorldSubsystem already
	 * carries the world it belongs to.
	 */
	UFUNCTION(BlueprintCallable, Category = "Commander|Level")
	void ApplyFixes();

private:
	/** Applies the fixes to a specific world. */
	void ApplyFixesToWorld(UWorld& World);

	/** Engine primitives, hard-referenced so they are cooked into the package. */
	UPROPERTY()
	TObjectPtr<UStaticMesh> CubeMesh;

	UPROPERTY()
	TObjectPtr<UStaticMesh> CylinderMesh;


	/** Finds an actor by its always-serialized FName. */
	static AActor* FindByName(UWorld& World, const TCHAR* Name);

	/** Sets the world-space bounds of an actor's root component to a target height band. */
	static bool SetHeightBand(AActor& Actor, double BottomZ, double TopZ);

	/** Copies the material of a map actor onto a spawned one, so runtime props match the map. */
	static UMaterialInterface* GrabMapMaterial(UWorld& World, const TCHAR* Name);
};
