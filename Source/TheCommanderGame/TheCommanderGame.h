// The Commander - runtime game module.
//
// Scope: gameplay only. Everything here must cook and run in a PACKAGED build,
// so no editor-only APIs (no GEditor, no UnrealEd, no AssetRegistry editor
// modules). The level fixes that the design needs (pillar climb, keycard
// legibility) are applied at RUNTIME by ACommanderLevelFix, because
// Content/Maps/M_Blockout01.umap is frozen and must stay byte-identical.
//
// The same fix values are mirrored in Tools/blender/render_level.py so the
// offline renders and the shipped game agree. Tools/python/check_level_fixes.py
// compares the two so they cannot silently drift.

#pragma once

#include "CoreMinimal.h"
#include "Misc/Build.h"
#include "Logging/LogMacros.h"
#include "Logging/LogCategory.h"
#include "Modules/ModuleManager.h"

// Log category for this module.
//
// The API export macro (THE_COMMANDER_GAME_API) is deliberately NOT used here:
// that macro is only required when a category has to be visible across a module
// boundary, and nothing outside this module uses LogCommander. The engine's own
// Core/Public/Templates/Task.h declares its category the same way - with no API
// prefix at all.

DECLARE_LOG_CATEGORY_EXTERN(LogCommander, Log, All);

class FTheCommanderGameModule : public IModuleInterface
{
public:
    virtual void StartupModule() override;
    virtual void ShutdownModule() override;
};
