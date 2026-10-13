@echo off
setlocal
if "%~1"=="" (
  echo Uso: DETENER-DESARROLLADOR-AUTONOMO.bat PROJECT_ROOT
  exit /b 2
)
powershell.exe -NoProfile -NonInteractive -File "%~dp0runner\stop.ps1" -ProjectRoot "%~1"
exit /b %errorlevel%
