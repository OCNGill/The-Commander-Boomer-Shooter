@echo off
setlocal
set D=C:\Users\steph\source\repos\OCNGill\The_Commander_Boomer_Shooter\Tools\blender
set B=F:\blender-4.2.23-windows-x64\blender.exe
echo ===EDI DETERMINISTIC AUDIT===
"%B%" -b -P "%D%\edi_build.py" -P "%D%\edi_audit.py" -- --look BLACKICE --no-render --no-export
echo ===AUDIT_END rc=%ERRORLEVEL%===
