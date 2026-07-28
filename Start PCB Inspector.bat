@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\launch_app.ps1"
if errorlevel 1 (
  echo.
  echo The app could not start. Read the message above, then press any key.
  pause >nul
)
