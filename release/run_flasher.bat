@echo off
REM Run this batch to execute flasher.exe and keep the console open so you can read output.
REM Edit PORT variable below if your device uses a different COM port.
set PORT=COM42
cd /d "%~dp0"
echo Running flasher with port %PORT%...
flasher.exe --port %PORT%
echo.
necho Press any key to close...
pause >nul
