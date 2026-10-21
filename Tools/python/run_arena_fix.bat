@echo off
setlocal
set UE=D:\Unreal_Engine\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe
set SL=C:/Users/Gillsystems Laptop/source/repos/OCNGill/The_Commander_Boomer_Shooter
cd /d "%SL%"

if not exist "%SL%\Tools\python\fix_pit_and_ramp.py" (
  echo [PREFLIGHT] fix_pit_and_ramp.py missing - aborting
  exit /b 8
)

rem [STEP 1] ensure_base_geometry.py is NOT run - the base arena is already restored and committed
rem (commit 13362ed, blob 80,624 bytes, 46 actors). Running it again is a wasted 10-minute boot.
call :guard FIX || exit /b 9
echo [STEP 2] fix_pit_and_ramp.py
"%UE%" "%SL%/TheCommander.uproject" -run=pythonscript -script="%SL%/Tools/python/fix_pit_and_ramp.py" -unattended -nosplash -NoSound -stdout -FullStdOutLogOutput -abslog="%SL%/Saved/Logs/fix_pit_run3.log"
echo [STEP 2] exit=%errorlevel%

echo [FILE] map on disk:
for %%F in ("%SL%\Content\Maps\M_Blockout01.umap") do echo   %%~zF bytes  %%~tF
echo [DONE]
exit /b 0

:guard
tasklist /FI "IMAGENAME eq UnrealEditor-Cmd.exe" | findstr /I "UnrealEditor-Cmd.exe" >nul
if %errorlevel%==0 (
  echo [GUARD] an UnrealEditor-Cmd.exe is already running - refusing to start %1
  exit /b 1
)
exit /b 0
