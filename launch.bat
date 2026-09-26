@echo off
rem Black Spire one-command launcher for Windows.
rem Creates a local virtualenv (if needed), installs pygame-ce, and runs the game.
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv .venv
)

".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q -r requirements.txt
".venv\Scripts\python.exe" -m black_spire %*
