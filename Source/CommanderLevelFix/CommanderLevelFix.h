// The Commander - runtime level-fix module (see CommanderLevelFix.Build.cs).

#pragma once

#include "CoreMinimal.h"
#include "Misc/Build.h"
#include "Logging/LogMacros.h"
#include "Logging/LogCategory.h"
#include "Modules/ModuleManager.h"

// Log category for this module. The API export macro is deliberately not used:
// nothing outside this module references it.
DECLARE_LOG_CATEGORY_EXTERN(LogCommanderLevelFix, Log, All);

class FCommanderLevelFixModule : public IModuleInterface
{
public:
    virtual void StartupModule() override;
    virtual void ShutdownModule() override;
};
