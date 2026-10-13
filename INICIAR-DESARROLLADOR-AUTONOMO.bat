@echo off
setlocal
if "%~1"=="" (
  echo Uso: INICIAR-DESARROLLADOR-AUTONOMO.bat PROJECT_ROOT
  exit /b 2
)
powershell.exe -NoProfile -File "%~dp0runner\launch.ps1" -ProjectRoot "%~1"
exit /b %errorlevel%
