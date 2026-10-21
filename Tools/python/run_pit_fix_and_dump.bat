@echo off
setlocal
set REPO=C:\Users\Gillsystems Laptop\source\repos\OCNGill\The_Commander_Boomer_Shooter
set UE=D:\Unreal_Engine\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe
cd /d "%REPO%"

REM --- exclusivity guard: one UnrealEditor-Cmd at a time ---
tasklist /FI "IMAGENAME eq UnrealEditor-Cmd.exe" | find /I "UnrealEditor-Cmd.exe" >nul
if %errorlevel%==0 (
  echo [GUARD] UnrealEditor-Cmd.exe already running - refusing to start. Aborting.
  exit /b 9
)

echo [PIT] adding pit access...
"%UE%" "%REPO%\TheCommander.uproject" -run=pythonscript -script="%REPO%\Tools\python\add_pit_access.py" -unattended -nosplash -stdout -FullStdOutLogOutput -NoSound -abslog="%REPO%\Saved\Logs\pit_access_run.log"
echo [PIT] exit=%errorlevel%

tasklist /FI "IMAGENAME eq UnrealEditor-Cmd.exe" | find /I "UnrealEditor-Cmd.exe" >nul
if %errorlevel%==0 (
  echo [GUARD] an editor survived the pit boot - not running the dump. Stop it first.
  exit /b 8
)

echo [DUMP] regenerating level_transforms.json...
"%UE%" "%REPO%\TheCommander.uproject" -run=pythonscript -script="%REPO%\Tools\python\dump_level_transforms.py" -unattended -nosplash -stdout -FullStdOutLogOutput -NoSound -abslog="%REPO%\Saved\Logs\leveldump_run2.log"
echo [DUMP] exit=%errorlevel%
echo [DONE] pit access + dump complete
