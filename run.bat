@echo off
REM ============================================================
REM  Banking Transaction Analysis - launcher
REM  Double-click this file to start the dashboard.
REM  Press Ctrl+C in this window (or close it) to stop.
REM ============================================================
title Banking Transaction Analysis
cd /d "%~dp0"

set "PYTHON=python"
if exist ".venv\Scripts\python.exe" set "PYTHON=.venv\Scripts\python.exe"
if exist "venv\Scripts\python.exe" set "PYTHON=venv\Scripts\python.exe"

where "%PYTHON%" >nul 2>nul
if errorlevel 1 (
    echo.
    echo  ERROR: Python was not found.
    echo  Create a virtual environment and install requirements first:
    echo    python -m venv venv
    echo    venv\Scripts\activate
    echo    pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo.
echo  Starting dashboard from:
echo    %CD%
echo.
echo  The landing page opens at http://localhost:8501.
echo  Sign in with admin / banking2026 or another demo account.
echo  Press Ctrl+C to stop.
echo.

"%PYTHON%" -m streamlit run "dashboard\app.py"

echo.
echo  Server stopped.
pause
