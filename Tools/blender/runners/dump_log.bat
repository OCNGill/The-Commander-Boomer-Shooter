@echo off
set D=C:\Users\steph\source\repos\OCNGill\The_Commander_Boomer_Shooter\Tools\blender
echo ===LOG_TAIL===
powershell -NoProfile -Command "Get-Content -Path '%D%\edi_build.log' -Tail 45"
echo ===ERR_LINES===
powershell -NoProfile -Command "Select-String -Path '%D%\edi_build.log' -Pattern 'Error|Traceback|Exception|raise |KeyError|TypeError|ValueError|AttributeError|line ' | Select-Object -Last 30 | ForEach-Object { $_.LineNumber.ToString() + ': ' + $_.Line }"
echo ===END===
