@echo off
rem Black Spire smoke test runner for Windows (headless).
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv .venv
    ".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q -r requirements.txt
)

".venv\Scripts\python.exe" -m unittest discover -s tests -v
