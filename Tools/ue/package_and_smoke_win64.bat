@echo off
REM ===========================================================================
REM  The Commander Boomer Shooter - sovereign Win64 package + smoke + PSO cache.
REM
REM  Builds the standalone game target, cooks, stages, packages, archives, then
REM  BOOTS THE SHIPPED .exe twice:
REM    pass 1  with -logpso, which makes the engine record every PSO it needs
REM            into Saved\CollectedPSOs\*.rec.upipelinecache
REM    pass 2  with the merged stable cache installed under
REM            Content\PipelineCaches\Windows\  to measure whether the runtime
REM            misses are gone.
REM  "It compiles" is NOT "it plays" - this script proves both, in one run.
REM
REM  IMPORTANT: graceful exit does NOT write the stable PSO cache (the engine
REM  only writes it when told via -logpso / r.ShaderPipelineCache.SaveOnExit).
REM  We therefore use -logpso for pass 1 and the MergeShaderPipelineCaches
REM  commandlet to turn the recorded cache into the file the engine actually
REM  reads, then install it for pass 2.
REM
REM  Usage (from a console with a live window - do NOT detach via
REM  Start-Process: children die when the SSH session closes):
REM      Tools\ue\package_and_smoke_win64.bat [UE_ROOT] [OUT_DIR]
REM  Defaults:
REM      UE_ROOT = F:\Unreal_engine\UE_5.8   (override with arg 1)
REM      OUT_DIR = %TEMP%\TheCommander_Pkg   (override with arg 2)
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
set "SMOKE_TIMEOUT=240"
set "CACHEDIR=%ARCH%\TheCommander\Content\PipelineCaches\Windows"
set "GAMEPROC=TheCommanderGame.exe"
set "PS1=%REPO%\Tools\ue\smoke_win64.ps1"

REM collected cache + merged stable cache (locations derived from the merge step)
set "COLLECTED_DIR=%ARCH%\TheCommander\Saved\CollectedPSOs"
set "MERGED_CACHE=%OUT%\merged\TheCommander_PCD3D_SM6.stable.upipelinecache"
set "MERGELOG=%OUT%\_merge.log"

if not exist "%UPROJECT%" ( echo [FATAL] uproject not found: %UPROJECT% & exit /b 2 )
if not exist "%UE%\Engine\Build\BatchFiles\Build.bat" ( echo [FATAL] UE not found: %UE% & exit /b 3 )
if not exist "%REPO%\Plugins\FSR\FSR.uplugin" ( echo [FATAL] upscaler plugins missing - run: python Tools\ue\fetch_upscaler_plugins.py & exit /b 4 )
if not exist "%PS1%" ( echo [FATAL] smoke script missing: %PS1% & exit /b 9 )

if not exist "%OUT%" mkdir "%OUT%" >nul 2>&1

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
REM  Pass 1: boot the shipped exe with -logpso to record every PSO the game
REM  needs into Saved\CollectedPSOs\*.rec.upipelinecache
REM ---------------------------------------------------------------------------
echo.
echo === [3/5] SMOKE PASS 1 (-logpso, records the PSO cache) ===
del /q "%SMOKELOG%" >nul 2>&1
REM Stale-log guard: if the previous log is locked by a live game instance,
REM refusing to run prevents a false pass from stale content.
if exist "%SMOKELOG%" (
  echo     [FAIL] previous smoke log is locked by a running game - refusing a stale-log smoke
  set "SMOKE_EXIT=-2"
  goto smoke_verdict
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%PS1%" -Exe "%EXE%" -Log "%SMOKELOG%" -Savedir "%OUT%\Saved" -TimeoutSec %SMOKE_TIMEOUT% -GracefulExit -LogPso -CommanderInputAudit -windowed -ResX=1280 -ResY=720 -nosplash -unattended -nopause > "%SMOKELOG%.pwsh" 2>&1
set "PS1_EXIT1=%ERRORLEVEL%"
echo     powershell exit (pass1) = %PS1_EXIT1%

REM collect the recorded cache
set "CACHEFILE="
set "COLLECTED_COUNT=0"
for /r "%COLLECTED_DIR%" %%F in (*.rec.upipelinecache) do (
  if not defined CACHEFILE set "CACHEFILE=%%F"
  set /a COLLECTED_COUNT+=1
)
echo     collected .rec.upipelinecache files : %COLLECTED_COUNT%
if defined CACHEFILE (
  for %%F in ("%CACHEFILE%") do echo     cache file : %%~nxF (%%~zF bytes)
) else (
  echo     [WARN] no .rec.upipelinecache was written - -logpso did not record anything
  set "CACHEFILE=NONE"
)

set "MISS1=0"
if exist "%SMOKELOG%" (
  for /f "tokens=*" %%L in ('findstr /c:"PSOPrecacheState: Missed" "%SMOKELOG%" 2^>nul') do set /a MISS1+=1
)
echo     pass 1 runtime PSO misses : %MISS1%

REM ---------------------------------------------------------------------------
REM  Merge the collected cache into the single stable .upipelinecache the engine
REM  reads at startup via FPipelineFileCacheManager.
REM ---------------------------------------------------------------------------
echo.
echo === [4/5] MERGE COLLECTED PSO CACHE INTO STABLE CACHE ===
if not exist "%OUT%\merged" mkdir "%OUT%\merged"
set "MERGE_EXIT="
if "%CACHEFILE%"=="NONE" (
  echo     [SKIP] nothing to merge - no collected cache
  set "MERGE_EXIT=-1"
) else (
  REM Invoke the UnrealEditor-Cmd commandlet: ProjectPath -run=MergeShaderPipelineCaches
  REM   FilePathA FilePathB -Sort=<Order> OutputPath
  set "PROJECT=%REPO%\TheCommander.uproject"
  set "EDITOR=%UE%\Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
  if exist "%EDITOR%" (
    "%EDITOR%" "%PROJECT%" -run=MergeShaderPipelineCaches "%CACHEFILE%" "%CACHEFILE%" -Sort=Default "%MERGED_CACHE%" -unattended -nopause -nosplash > "%MERGELOG%" 2>&1
    set "MERGE_EXIT=%ERRORLEVEL%"
    echo     merge exit = %MERGE_EXIT%
  ) else (
    echo     [FATAL] UnrealEditor-Cmd.exe not found: %EDITOR%
    set "MERGE_EXIT=-2"
  )
)

REM ---------------------------------------------------------------------------
REM  Pass 2: boot again with the merged stable cache installed where the engine
REM  reads it, and count the misses again.
REM ---------------------------------------------------------------------------
echo.
echo === [5/5] SMOKE PASS 2 (stable cache installed) ===
set "SMOKE_EXIT2=0"
set "MISS2=0"
set "SKIP2="
if not "%MERGE_EXIT%"=="0" (
  echo     [SKIP] merge did not succeed - cannot install stable cache for pass 2
  set "SKIP2=1"
) else (
  del /q "%SMOKELOG2%" >nul 2>&1
  if exist "%SMOKELOG2%" (
    echo     [FAIL] previous smoke2 log is locked by a running game - refusing a stale-log smoke
    set "SMOKE_EXIT2=-2"
    set "SKIP2=1"
  )
)
if not defined SKIP2 (
  if not exist "%CACHEDIR%" mkdir "%CACHEDIR%" >nul 2>&1
  copy /y "%MERGED_CACHE%" "%CACHEDIR%\TheCommander_PCD3D_SM6.stable.upipelinecache" >nul 2>&1
  echo     installed stable cache to %CACHEDIR%
  powershell -NoProfile -ExecutionPolicy Bypass -File "%PS1%" -Exe "%EXE%" -Log "%SMOKELOG2%" -Savedir "%OUT%\Saved2" -TimeoutSec %SMOKE_TIMEOUT% -CommanderInputAudit -windowed -ResX=1280 -ResY=720 -nosplash -unattended -nopause > "%SMOKELOG2%.pwsh" 2>&1
  set "PS1_EXIT2=%ERRORLEVEL%"
  echo     powershell exit (pass2) = %PS1_EXIT2%
)
if exist "%SMOKELOG2%" (
  for /f "tokens=*" %%L in ('findstr /c:"PSOPrecacheState: Missed" "%SMOKELOG2%" 2^>nul') do set /a MISS2+=1
)
echo     pass 2 runtime PSO misses : %MISS2%

REM ---------------------------------------------------------------------------
echo.
echo === VERDICT ===
set "VERDICT=FAIL"
findstr /C:"Engine is initialized" "%SMOKELOG%" >nul 2>&1 && set "VERDICT=BOOTED"
findstr /C:"Failure creating: D3D12Viewport" "%SMOKELOG%" >nul 2>&1 && set "VERDICT=FATAL_VIEWPORT"
findstr /C:"Successfully initialized FSR Upscaling provider" "%SMOKELOG%" >nul 2>&1 && set "FSR=ENGAGED" || set "FSR=NOT_SEEN"
findstr /C:"COMMANDER INPUT AUDIT BEGIN" "%SMOKELOG%" >nul 2>&1 && set "INPUT_AUDIT=OK" || set "INPUT_AUDIT=NOT_SEEN"
echo     boot verdict        : %VERDICT%
echo     FSR provider        : %FSR%
echo     input audit         : %INPUT_AUDIT%
echo     collected cache     : %CACHEFILE%
echo     merged cache        : %MERGED_CACHE%
echo     pso misses pass1/2  : %MISS1% / %MISS2%
echo     archive             : %ARCH%
echo     log                 : %SMOKELOG%
if "%SMOKE_EXIT%"=="-2" ( echo     RESULT: FAIL & exit /b 8 )
if "%SMOKE_EXIT2%"=="-2" ( echo     RESULT: FAIL & exit /b 8 )
if "%VERDICT%"=="BOOTED" (
  if "%MISS2%"=="0" ( echo     RESULT: PASS & exit /b 0 ) else ( echo     RESULT: PASS_BUT_MISSES_REMAIN & exit /b 0 )
)
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
