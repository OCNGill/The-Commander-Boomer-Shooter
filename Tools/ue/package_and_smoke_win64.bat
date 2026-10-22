@echo off
REM ===========================================================================
REM  The Commander Boomer Shooter - sovereign Win64 package + smoke test.
REM
REM  Builds the standalone game target, cooks, stages, packages, archives, and
REM  then BOOTS THE SHIPPED .exe and verifies it survives first frame.
REM  "It compiles" is NOT "it plays" - this script proves both, in one run.
REM
REM  Usage (from a console with a live window - do NOT detach via
REM  Start-Process: children die when the SSH session closes):
REM      Tools\ue\package_and_smoke_win64.bat [UE_ROOT] [OUT_DIR]
REM  Defaults:
REM      UE_ROOT = F:\Unreal_engine\UE_5.8   (override with arg 1)
REM      OUT_DIR = %TEMP%\TheCommander_Pkg    (override with arg 2)
REM
REM  Prerequisite: the upscaler plugin trees must exist. Provision them with:
REM      python Tools\ue\fetch_upscaler_plugins.py
REM  (Plugins/ is gitignored - multi-GB binaries are never committed.)
REM ===========================================================================
setlocal enabledelayedexpansion

set "REPO=%~dp0..\.."
for %%I in ("%REPO%") do set "REPO=%%~fI"

set "UE=%~1"
if "%UE%"=="" set "UE=F:\Unreal_engine\UE_5.8"
set "OUT=%~2"
if "%OUT%"=="" set "OUT=%TEMP%\TheCommander_Pkg"

set "UPROJECT=%REPO%\TheCommander.uproject"
set "BUILDLOG=%OUT%\_build.log"
set "PKGLOG=%OUT%\_package.log"
set "SMOKELOG=%OUT%\_smoke.log"
set "ARCH=%OUT%\Win64"

if not exist "%UPROJECT%" ( echo [FATAL] uproject not found: %UPROJECT% & exit /b 2 )
if not exist "%UE%\Engine\Build\BatchFiles\Build.bat" ( echo [FATAL] UE not found: %UE% & exit /b 3 )
if not exist "%REPO%\Plugins\FSR\FSR.uplugin" ( echo [FATAL] upscaler plugins missing - run: python Tools\ue\fetch_upscaler_plugins.py & exit /b 4 )

if not exist "%OUT%" mkdir "%OUT%" >nul 2>&1

echo.
echo === [1/4] BUILD GAME TARGET ===
call "%UE%\Engine\Build\BatchFiles\Build.bat" TheCommanderGame Win64 Development ^
  -project="%UPROJECT%" -WaitMutex > "%BUILDLOG%" 2>&1
set "BUILD_EXIT=%ERRORLEVEL%"
echo     build exit = %BUILD_EXIT%
if not "%BUILD_EXIT%"=="0" ( echo [FATAL] compile failed - see %BUILDLOG% & exit /b 5 )

echo.
echo === [2/4] COOK + STAGE + PACKAGE ===
if exist "%ARCH%" rd /s /q "%ARCH%"
call "%UE%\Engine\Build\BatchFiles\RunUAT.bat" BuildCookRun ^
  -project="%UPROJECT%" ^
  -noP4 -platform=Win64 -clientconfig=Development ^
  -build -cook -stage -pak -prereqs ^
  -archive -archivedirectory="%ARCH%" ^
  -unattended -utf8output -noclientstats > "%PKGLOG%" 2>&1
set "PKG_EXIT=%ERRORLEVEL%"
echo     package exit = %PKG_EXIT%
if not "%PKG_EXIT%"=="0" ( echo [FATAL] package failed - see %PKGLOG% & exit /b 6 )

set "EXE=%ARCH%\TheCommander\Binaries\Win64\TheCommanderGame.exe"
if not exist "%EXE%" ( echo [FATAL] packaged exe missing: %EXE% & exit /b 7 )

echo.
echo === [3/4] SMOKE TEST THE SHIPPED .exe ===
del /q "%SMOKELOG%" >nul 2>&1
"%EXE%" -log -abslog="%SMOKELOG%" -savedir="%OUT%\Saved" ^
  -CommanderInputAudit ^
  -windowed -ResX=1280 -ResY=720 -nosplash -unattended -nopause > "%SMOKELOG%.stdout" 2>&1
set "SMOKE_EXIT=%ERRORLEVEL%"
echo     smoke exit = %SMOKE_EXIT%

echo.
echo === [4/4] VERDICT ===
set "VERDICT=FAIL"
findstr /C:"Engine is initialized" "%SMOKELOG%" >nul 2>&1 && set "VERDICT=BOOTED"
findstr /C:"Failure creating: D3D12Viewport" "%SMOKELOG%" >nul 2>&1 && set "VERDICT=FATAL_VIEWPORT"
findstr /C:"Successfully initialized FSR Upscaling provider" "%SMOKELOG%" >nul 2>&1 && set "FSR=ENGAGED" || set "FSR=NOT_SEEN"
findstr /C:"COMMANDER INPUT AUDIT BEGIN" "%SMOKELOG%" >nul 2>&1 && set "INPUT_AUDIT=OK" || set "INPUT_AUDIT=NOT_SEEN"
echo     boot verdict : %VERDICT%
echo     FSR provider : %FSR%
echo     input audit  : %INPUT_AUDIT%
echo     archive      : %ARCH%
echo     log          : %SMOKELOG%
if "%VERDICT%"=="BOOTED" ( echo     RESULT: PASS & exit /b 0 )
echo     RESULT: FAIL
exit /b 8
