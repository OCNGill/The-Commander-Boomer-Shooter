@echo off
REM ===========================================================================
REM  The Commander Boomer Shooter - sovereign Win64 package + smoke + PSO cache.
REM
REM  Builds the standalone game target, cooks, stages, packages, archives, then
REM  BOOTS THE SHIPPED .exe twice:
REM    pass 1  with -CommanderExitAfterAudit, so the engine shuts down normally
REM            and writes the stable PSO cache that a force-kill never produces;
REM    pass 2  with that cache installed, to measure whether the runtime PSO
REM            misses are gone.
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
set "SMOKELOG2=%OUT%\_smoke2.log"
set "ARCH=%OUT%\Win64"
set "EXE=%ARCH%\TheCommander\Binaries\Win64\TheCommanderGame.exe"
REM The shipped .exe does not self-exit on its own. With -CommanderExitAfterAudit
REM it asks the engine to shut down normally after the input audit, which is
REM what lets the engine write the stable PSO cache. The wait is still bounded:
REM a lane that can hang is a lane that never reports.
set "SMOKE_TIMEOUT=240"
set "CACHEDIR=%ARCH%\TheCommander\Content\PipelineCaches\Windows"
set "GAMEPROC=TheCommanderGame.exe"

if not exist "%UPROJECT%" ( echo [FATAL] uproject not found: %UPROJECT% & exit /b 2 )
if not exist "%UE%\Engine\Build\BatchFiles\Build.bat" ( echo [FATAL] UE not found: %UE% & exit /b 3 )
if not exist "%REPO%\Plugins\FSR\FSR.uplugin" ( echo [FATAL] upscaler plugins missing - run: python Tools\ue\fetch_upscaler_plugins.py & exit /b 4 )

if not exist "%OUT%" mkdir "%OUT%" >nul 2>&1

REM ---------------------------------------------------------------------------
REM  A running instance check that cannot be fooled.
REM  tasklist /FI ... /NH prints "INFO: No tasks are running which match the
REM  specified criteria." when nothing matches - and "tokens=2" of that line is
REM  the word "tasks", not a PID. Match on the image name instead.
REM ---------------------------------------------------------------------------
echo.
echo === [1/5] BUILD GAME TARGET ===
call "%UE%\Engine\Build\BatchFiles\Build.bat" TheCommanderGame Win64 Development ^
  -project="%UPROJECT%" -WaitMutex > "%BUILDLOG%" 2>&1
set "BUILD_EXIT=%ERRORLEVEL%"
echo     build exit = %BUILD_EXIT%
if not "%BUILD_EXIT%"=="0" ( echo [FATAL] compile failed - see %BUILDLOG% & exit /b 5 )

echo.
echo === [2/5] COOK + STAGE + PACKAGE ===
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

if not exist "%EXE%" ( echo [FATAL] packaged exe missing: %EXE% & exit /b 7 )

REM ---------------------------------------------------------------------------
REM  Pass 1: boot the shipped exe and let it exit on its own.
REM ---------------------------------------------------------------------------
echo.
echo === [3/5] SMOKE PASS 1 (graceful exit, writes the PSO cache) ===
del /q "%SMOKELOG%" >nul 2>&1
REM A stale log from a previous run whose game is still alive CANNOT be deleted, and
REM the marker poll below would then match it and report a FALSE PASS. Refuse to run.
if exist "%SMOKELOG%" (
  echo     [FAIL] previous smoke log is locked by a running game - refusing a stale-log smoke
  set "SMOKE_EXIT=-2"
  goto smoke_verdict
)
call :find_game
if defined PREEXIST goto smoke_skip

start "" /b cmd /c ""%EXE%" -log -abslog="%SMOKELOG%" -savedir="%OUT%\Saved" -CommanderInputAudit -CommanderExitAfterAudit -windowed -ResX=1280 -ResY=720 -nosplash -unattended -nopause > "%SMOKELOG%.stdout" 2>&1"

set "OURPID="
set /a "WAITED=0"
:smoke_spawn
timeout /t 1 /nobreak >nul 2>&1
for /f "tokens=2" %%P in ('tasklist /FI "IMAGENAME eq %GAMEPROC%" /NH 2^>nul ^| find /i "%GAMEPROC%"') do set "OURPID=%%P"
if defined OURPID goto smoke_alive
set /a "WAITED+=1"
if !WAITED! GEQ %SMOKE_TIMEOUT% goto smoke_stop
goto smoke_spawn

:smoke_alive
set /a "WAITED=0"
:smoke_wait
timeout /t 3 /nobreak >nul 2>&1
set /a "WAITED+=3"
tasklist /FI "PID eq !OURPID!" 2^>nul | find "!OURPID!" >nul 2>&1 || goto smoke_stop
if !WAITED! GEQ %SMOKE_TIMEOUT% goto smoke_kill
goto smoke_wait

:smoke_kill
echo     [WARN] the game did not exit on its own within %SMOKE_TIMEOUT%s - killing PID !OURPID!
taskkill /F /PID !OURPID! >nul 2>&1
echo     [WARN] the PSO cache may be incomplete - a killed run writes nothing
goto smoke_stop

:smoke_stop
taskkill /F /IM %GAMEPROC% >nul 2>&1
echo     pass 1 finished after !WAITED!s
set "SMOKE_EXIT=0"
goto smoke_verdict

:smoke_skip
echo     [SKIP] a %GAMEPROC% instance is already running (PID !PREEXIST!) - not touching it
set "SMOKE_EXIT=-1"
set "SKIPSMOKE=1"
:smoke_verdict

echo.
echo === [4/5] COLLECT + INSTALL THE STABLE PSO CACHE ===
set "CACHEFILE="
for /r "%ARCH%" %%F in (*.upipelinecache) do (
  if not defined CACHEFILE set "CACHEFILE=%%F"
)
if defined CACHEFILE (
  echo     found : %CACHEFILE%
  for %%F in ("%CACHEFILE%") do echo     size  : %%~zF bytes
  if not exist "%CACHEDIR%" mkdir "%CACHEDIR%" >nul 2>&1
  copy /y "%CACHEFILE%" "%CACHEDIR%\" >nul 2>&1
  echo     installed to %CACHEDIR%
) else (
  echo     [WARN] no .upipelinecache was written - the run did not exit gracefully
  set "CACHEFILE=NONE"
)
set "MISS1=0"
if exist "%SMOKELOG%" (
  for /f "tokens=*" %%L in ('findstr /c:"PSOPrecacheState: Missed" "%SMOKELOG%" 2^>nul') do set /a MISS1+=1
)
echo     pass 1 runtime PSO misses : %MISS1%

REM ---------------------------------------------------------------------------
REM  Pass 2: boot again with the cache installed and count the misses again.
REM ---------------------------------------------------------------------------
echo.
echo === [5/5] SMOKE PASS 2 (cache installed) ===
del /q "%SMOKELOG2%" >nul 2>&1
call :find_game
if defined PREEXIST2 goto smoke2_skip
if defined PREEXIST goto smoke2_skip
start "" /b cmd /c ""%EXE%" -log -abslog="%SMOKELOG2%" -savedir="%OUT%\Saved2" -CommanderInputAudit -windowed -ResX=1280 -ResY=720 -nosplash -unattended -nopause > "%SMOKELOG2%.stdout" 2>&1"
set "OURPID2="
set /a "WAITED2=0"
:smoke2_spawn
timeout /t 1 /nobreak >nul 2>&1
for /f "tokens=2" %%P in ('tasklist /FI "IMAGENAME eq %GAMEPROC%" /NH 2^>nul ^| find /i "%GAMEPROC%"') do set "OURPID2=%%P"
if defined OURPID2 goto smoke2_alive
set /a "WAITED2+=1"
if !WAITED2! GEQ 60 goto smoke2_stop
goto smoke2_spawn
:smoke2_alive
set /a "WAITED2=0"
:smoke2_wait
timeout /t 3 /nobreak >nul 2>&1
set /a "WAITED2+=3"
tasklist /FI "PID eq !OURPID2!" 2^>nul | find "!OURPID2!" >nul 2>&1 || goto smoke2_stop
if !WAITED2! GEQ %SMOKE_TIMEOUT% goto smoke2_kill
goto smoke2_wait
:smoke2_kill
taskkill /F /PID !OURPID2! >nul 2>&1
goto smoke2_stop
:smoke2_stop
taskkill /F /IM %GAMEPROC% >nul 2>&1
echo     pass 2 finished after !WAITED2!s
goto smoke2_done
:smoke2_skip
echo     [SKIP] a %GAMEPROC% instance is already running - not touching it
:smoke2_done
set "MISS2=0"
if exist "%SMOKELOG2%" (
  for /f "tokens=*" %%L in ('findstr /c:"PSOPrecacheState: Missed" "%SMOKELOG2%" 2^>nul') do set /a MISS2+=1
)
echo     pass 2 runtime PSO misses : %MISS2%

echo.
echo === VERDICT ===
set "VERDICT=FAIL"
findstr /C:"Engine is initialized" "%SMOKELOG%" >nul 2>&1 && set "VERDICT=BOOTED"
findstr /C:"Failure creating: D3D12Viewport" "%SMOKELOG%" >nul 2>&1 && set "VERDICT=FATAL_VIEWPORT"
findstr /C:"Successfully initialized FSR Upscaling provider" "%SMOKELOG%" >nul 2>&1 && set "FSR=ENGAGED" || set "FSR=NOT_SEEN"
findstr /C:"COMMANDER INPUT AUDIT BEGIN" "%SMOKELOG%" >nul 2>&1 && set "INPUT_AUDIT=OK" || set "INPUT_AUDIT=NOT_SEEN"
findstr /C:"COMMANDER GRACEFUL EXIT: RequestExit" "%SMOKELOG%" >nul 2>&1 && set "GRACEFUL=YES" || set "GRACEFUL=NO"
echo     boot verdict        : %VERDICT%
echo     FSR provider        : %FSR%
echo     input audit         : %INPUT_AUDIT%
echo     graceful exit       : %GRACEFUL%
echo     pso cache           : %CACHEFILE%
echo     pso misses pass1/2  : %MISS1% / %MISS2%
echo     archive             : %ARCH%
echo     log                 : %SMOKELOG%
if "%SMOKE_EXIT%"=="-2" ( echo     RESULT: FAIL & exit /b 8 )
if defined SKIPSMOKE ( echo     RESULT: SKIPPED & exit /b 0 )
if "%VERDICT%"=="BOOTED" ( echo     RESULT: PASS & exit /b 0 )
echo     RESULT: FAIL
exit /b 8

REM ---------------------------------------------------------------------------
REM  Subroutine: find a running instance of the game. MUST STAY AT THE END OF THIS
REM  FILE - a label in the middle of the main flow is fallen into, and the
REM  'goto :eof' below would end the whole lane before it ever builds anything.
REM ---------------------------------------------------------------------------
:find_game
set "PREEXIST="
for /f "tokens=1" %%P in ('tasklist /FI "IMAGENAME eq %GAMEPROC%" /NH 2^>nul ^| find /i "%GAMEPROC%"') do set "PREEXIST=%%P"
goto :eof
