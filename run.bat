@echo off
setlocal EnableDelayedExpansion
title pulse — AI Command Center

echo.
echo   ⚡  pulse  —  AI Command Center
echo   ───────────────────────────────────────
echo.

REM ─── Verify pulse.pyw exists next to this .bat ───
set "SCRIPT=%~dp0pulse.pyw"
if not exist "%SCRIPT%" (
    echo   ❌  Could not find pulse.pyw next to this launcher.
    echo       Make sure run.bat and pulse.pyw are in the same folder.
    echo.
    pause
    exit /b 1
)

set "PYTHON_EXE="

REM ═══════════════════════════════════════════════════
REM   CANDIDATE 1 — py launcher (python.org installer)
REM ═══════════════════════════════════════════════════
where py >nul 2>&1
if !errorlevel!==0 (
    for /f "delims=" %%i in ('py -3 -c "import sys; print(sys.executable)" 2^>nul') do (
        set "PYTHON_EXE=%%i"
    )
)

REM ═══════════════════════════════════════════════════
REM   CANDIDATE 2 — python in PATH
REM ═══════════════════════════════════════════════════
if not defined PYTHON_EXE (
    for /f "delims=" %%i in ('where python 2^>nul') do (
        if not defined PYTHON_EXE set "PYTHON_EXE=%%i"
    )
)

REM ═══════════════════════════════════════════════════
REM   CANDIDATE 3 — pythonw in PATH
REM ═══════════════════════════════════════════════════
if not defined PYTHON_EXE (
    for /f "delims=" %%i in ('where pythonw 2^>nul') do (
        if not defined PYTHON_EXE set "PYTHON_EXE=%%i"
    )
)

REM ═══════════════════════════════════════════════════
REM   CANDIDATE 4 — %LocalAppData%\Programs\Python\Python3*
REM ═══════════════════════════════════════════════════
if not defined PYTHON_EXE (
    for /d %%d in ("%LocalAppData%\Programs\Python\Python3*") do (
        if not defined PYTHON_EXE (
            if exist "%%d\python.exe" set "PYTHON_EXE=%%d\python.exe"
        )
    )
)

REM ═══════════════════════════════════════════════════
REM   CANDIDATE 5 — C:\Program Files\Python3*
REM ═══════════════════════════════════════════════════
if not defined PYTHON_EXE (
    for /d %%d in ("C:\Program Files\Python3*") do (
        if not defined PYTHON_EXE (
            if exist "%%d\python.exe" set "PYTHON_EXE=%%d\python.exe"
        )
    )
)

REM ═══════════════════════════════════════════════════
REM   CANDIDATE 6 — C:\Program Files (x86)\Python3*
REM ═══════════════════════════════════════════════════
if not defined PYTHON_EXE (
    for /d %%d in ("C:\Program Files (x86)\Python3*") do (
        if not defined PYTHON_EXE (
            if exist "%%d\python.exe" set "PYTHON_EXE=%%d\python.exe"
        )
    )
)

REM ═══════════════════════════════════════════════════
REM   CANDIDATE 7 — C:\Python3*
REM ═══════════════════════════════════════════════════
if not defined PYTHON_EXE (
    for /d %%d in ("C:\Python3*") do (
        if not defined PYTHON_EXE (
            if exist "%%d\python.exe" set "PYTHON_EXE=%%d\python.exe"
        )
    )
)

REM ═══════════════════════════════════════════════════
REM   NOTHING FOUND — show friendly instructions
REM ═══════════════════════════════════════════════════
if not defined PYTHON_EXE (
    echo   ❌  Python not found on your system.
    echo.
    echo   Please install Python 3.8 or newer from:
    echo       https://www.python.org/downloads/
    echo.
    echo   ⚠  IMPORTANT: During installation, check the box
    echo      that says "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

REM ═══════════════════════════════════════════════════
REM   Prefer pythonw.exe (no black console window)
REM ═══════════════════════════════════════════════════
set "PYTHONW_EXE=%PYTHON_EXE:python.exe=pythonw.exe%"
if not exist "%PYTHONW_EXE%" set "PYTHONW_EXE=%PYTHON_EXE%"

REM ═══════════════════════════════════════════════════
REM   Verify PyQt5 is installed — auto-install if missing
REM ═══════════════════════════════════════════════════
"%PYTHONW_EXE%" -c "import PyQt5" >nul 2>&1
if !errorlevel! neq 0 (
    echo   ⚠  PyQt5 is not installed for this Python.
    echo      Installing it now (this may take a minute)...
    echo.
    "%PYTHON_EXE%" -m pip install --quiet PyQt5
    if !errorlevel! neq 0 (
        echo.
        echo   ❌  Could not install PyQt5 automatically.
        echo      Please run this manually:
        echo.
        echo        "%PYTHON_EXE%" -m pip install PyQt5
        echo.
        pause
        exit /b 1
    )
    echo   ✅  PyQt5 installed successfully.
    echo.
)

REM ═══════════════════════════════════════════════════
REM   LAUNCH
REM ═══════════════════════════════════════════════════
echo   ✅  Python found:
echo      !PYTHONW_EXE!
echo.
echo   ⚡  Launching pulse...
echo.

start "" "!PYTHONW_EXE!" "%SCRIPT%"

exit /b 0
