@echo off
setlocal
set D=C:\Users\steph\source\repos\OCNGill\The_Commander_Boomer_Shooter\Tools\blender
set B=F:\blender-4.2.23-windows-x64\blender.exe
set LOG=%D%\edi_build_run.log

echo === edi_build runner === > "%LOG%"
echo dir check: >> "%LOG%"
dir "%D%\edi_build.py" >> "%LOG%" 2>&1
echo. >> "%LOG%"

echo === START %DATE% %TIME% === >> "%LOG%"
"%B%" -b -P "%D%\edi_build.py" -- --look BLACKICE --tris 30000 >> "%LOG%" 2>&1
set RC=%ERRORLEVEL%
echo === END rc=%RC% %TIME% === >> "%LOG%"

echo --- outputs ---
dir "%D%\out_crew_edi" >> "%LOG%" 2>&1
echo DONE rc=%RC%
