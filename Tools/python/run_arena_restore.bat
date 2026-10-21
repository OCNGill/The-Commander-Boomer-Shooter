@echo off
setlocal
set REPO=C:\Users\Gillsystems Laptop\source\repos\OCNGill\The_Commander_Boomer_Shooter
set UE=D:\Unreal_Engine\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe
cd /d "%REPO%"

call :guard ENSURE || exit /b 9
echo [STEP 1] ensure_base_geometry.py
"%UE%" "%REPO%\TheCommander.uproject" -run=pythonscript -script="%REPO%\Tools\python\ensure_base_geometry.py" -unattended -nosplash -NoSound -stdout -FullStdOutLogOutput -abslog="%REPO%\Saved\Logs\ensure_base_run3.log"
echo [STEP 1] exit=%errorlevel%

call :guard PIT || exit /b 9
call :guard DUMP || exit /b 9
echo [STEP 2] dump_level_transforms.py (fresh boot, reads the file back from disk)
"%UE%" "%REPO%\TheCommander.uproject" -run=pythonscript -script="%REPO%\Tools\python\dump_level_transforms.py" -unattended -nosplash -NoSound -stdout -FullStdOutLogOutput -abslog="%REPO%\Saved\Logs\leveldump_run3.log"
echo [STEP 2] exit=%errorlevel%

echo [FINAL] map size on disk:
for %%F in ("%REPO%\Content\Maps\M_Blockout01.umap") do echo   %%~zF bytes  %%~tF
echo [DONE]
exit /b 0

:guard
tasklist /FI "IMAGENAME eq UnrealEditor-Cmd.exe" | find /I "UnrealEditor-Cmd.exe" >nul
if %errorlevel%==0 (
  echo [GUARD] an UnrealEditor-Cmd.exe is already running - refusing to start %1. Aborting.
  exit /b 1
)
exit /b 0
