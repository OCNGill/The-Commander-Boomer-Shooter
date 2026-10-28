@echo off
setlocal
set D=C:\Users\steph\source\repos\OCNGill\The_Commander_Boomer_Shooter\Tools\blender
echo ===DIR===
dir "%D%\out_crew_edi"
echo ===LOGTAIL===
if exist "%D%\edi_build_run.log" (
  powershell -NoProfile -Command "Get-Content -Path '%D%\edi_build_run.log' | Select-Object -Last 60"
) else (
  echo NO_LOG_FILE
)
echo ===END===
