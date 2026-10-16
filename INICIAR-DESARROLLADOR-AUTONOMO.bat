@echo off
setlocal DisableDelayedExpansion
powershell.exe -NoProfile -STA -File "%~dp0scripts\project-launcher.ps1" -ProjectRoot "%~1"
set "LAUNCHER_EXIT=%errorlevel%"
if not "%LAUNCHER_EXIT%"=="0" pause
exit /b %LAUNCHER_EXIT%
