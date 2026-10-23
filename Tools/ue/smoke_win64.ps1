<#
    smoke_win64.ps1 - boot the packaged game and report what happened.

    The batch lane used to do this with 'start "" /b cmd /c "..."' and a
    tasklist poll. Both were fragile: nested cmd quoting fails with
    "The filename, directory name, or volume label syntax is incorrect", and
    '2^>nul' inside a for /f is passed to the program as a literal argument.
    This script does the process work in one language, with a real timeout,
    and no quote nesting at all.

    Exit codes:
      0  the run completed (read the MARKER lines for the detail)
      2  the executable is missing
      3  a game instance is already running - refusing to touch it
      4  the previous log is locked by a live process
#>
param(
  [Parameter(Mandatory = $true)][string]$Exe,
  [Parameter(Mandatory = $true)][string]$Log,
  [string]$Savedir = '',
  [int]$TimeoutSec = 120,
  [switch]$GracefulExit,
  [switch]$LogPso,
  [string[]]$ExtraArgs = @()
)
$ErrorActionPreference = 'Stop'
$ProcName = 'TheCommanderGame'

if (-not (Test-Path $Exe)) { Write-Output 'SMOKE_RESULT=NO_EXE'; exit 2 }

$pre = @(Get-Process -Name $ProcName -ErrorAction SilentlyContinue)
if ($pre.Count -gt 0) {
  Write-Output ('SMOKE_RESULT=PREEXISTING pid=' + $pre[0].Id)
  exit 3
}

if (Test-Path $Log) { Remove-Item $Log -Force -ErrorAction SilentlyContinue }
if (Test-Path $Log) { Write-Output 'SMOKE_RESULT=LOG_LOCKED'; exit 4 }

$argList = @('-log', "-abslog=$Log")
if ($Savedir)   { $argList += "-savedir=$Savedir" }
if ($GracefulExit) { $argList += '-CommanderExitAfterAudit' }
if ($LogPso)    { $argList += '-logpso' }
$argList += @('-CommanderInputAudit', '-windowed', '-ResX=1280', '-ResY=720',
              '-nosplash', '-unattended', '-nopause')
if ($ExtraArgs.Count -gt 0) { $argList += $ExtraArgs }

Write-Output ('SMOKE_LAUNCH=' + ($argList -join ' '))
$p = Start-Process -FilePath $Exe -ArgumentList $argList -PassThru
Write-Output ('SMOKE_PID=' + $p.Id)

$exited = $p.WaitForExit($TimeoutSec * 1000)
if (-not $exited) {
  Write-Output 'SMOKE_TIMEOUT=1'
  Write-Output 'SMOKE_SELF_EXIT=0'
  try { $p.Kill(); $p.WaitForExit(10000) } catch { }
  Write-Output ('SMOKE_EXITCODE=TIMEOUT')
} else {
  Write-Output 'SMOKE_SELF_EXIT=1'
  Write-Output ('SMOKE_EXITCODE=' + $p.ExitCode)
}

$markers = @(
  'Engine is initialized',
  'COMMANDER INPUT AUDIT BEGIN',
  'COMMANDER INPUT AUDIT END',
  'COMMANDER GRACEFUL EXIT: RequestExit',
  'Successfully initialized FSR Upscaling provider',
  'Successfully initialized FSR FrameInterpolation',
  'PSOPrecacheState: Missed',
  'Fatal error'
)
if (Test-Path $Log) {
  $text = Get-Content $Log -Raw
  foreach ($m in $markers) {
    $c = ([regex]::Matches($text, [regex]::Escape($m))).Count
    Write-Output ('MARKER [' + $m + '] = ' + $c)
  }
  Write-Output ('SMOKE_LOG_BYTES=' + (Get-Item $Log).Length)
  Write-Output 'SMOKE_CACHE_LINES:'
  ($text -split "`n") | Where-Object { $_ -match 'PipelineCache|upipelinecache|ShaderPipelineCache|PSOPrecache|Saved pipeline|logpso|CollectedPSOs' } |
    Select-Object -First 25 | ForEach-Object { Write-Output ('  ' + $_.Trim().Substring(0,[Math]::Min(170,$_.Trim().Length))) }
} else {
  Write-Output 'SMOKE_LOG=NONE'
}
exit 0
