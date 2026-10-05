@echo off
setlocal EnableExtensions EnableDelayedExpansion
title pulse — AI Command Center
color 0B

cls
echo.
echo   ========================================
echo     pulse  —  AI Command Center
echo   ========================================
echo.
echo   Preparing your system, please wait...
echo.

REM ═══════════════════════════════════════════════════
REM   1. Check pulse.pyw is here
REM ═══════════════════════════════════════════════════
if not exist "%~dp0pulse.pyw" (
    color 0C
    echo   [X] pulse.pyw was not found in this folder.
    echo       Make sure run.bat and pulse.pyw sit together.
    echo.
    pause
    exit /b 1
)

REM ═══════════════════════════════════════════════════
REM   2. Find a working Python
REM ═══════════════════════════════════════════════════
set "PYTHON_EXE="

REM -- Try 1: py launcher --
py -3 -c "import sys" >nul 2>&1
if not errorlevel 1 (
    for /f "delims=" %%i in ('py -3 -c "import sys; print(sys.executable)" 2^>nul') do set "PYTHON_EXE=%%i"
)

REM -- Try 2: python on PATH --
if not defined PYTHON_EXE (
    for /f "delims=" %%i in ('where python 2^>nul') do (
        if not defined PYTHON_EXE set "PYTHON_EXE=%%i"
    )
)

REM -- Try 3: common install folders --
if not defined PYTHON_EXE (
    for %%P in (
        "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python39\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python38\python.exe"
        "C:\Program Files\Python313\python.exe"
        "C:\Program Files\Python312\python.exe"
        "C:\Program Files\Python311\python.exe"
        "C:\Program Files\Python310\python.exe"
        "C:\Python313\python.exe"
        "C:\Python312\python.exe"
        "C:\Python311\python.exe"
        "C:\Python310\python.exe"
    ) do (
        if not defined PYTHON_EXE if exist %%P set "PYTHON_EXE=%%~P"
    )
)

REM -- Nothing found --
if not defined PYTHON_EXE (
    color 0C
    echo   [X] Python is not installed on this computer.
    echo.
    echo       Download and install Python 3.8 or newer:
    echo         https://www.python.org/downloads/
    echo.
    echo       IMPORTANT: During install, tick the box
    echo       "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

REM -- Sanity check --
"!PYTHON_EXE!" --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo   [X] Found Python at:
    echo         !PYTHON_EXE!
    echo       but it refuses to run. Try reinstalling Python.
    echo.
    pause
    exit /b 1
)

echo   [OK]  Python found:
echo         !PYTHON_EXE!
echo.

REM ═══════════════════════════════════════════════════
REM   3. Ensure pip exists
REM ═══════════════════════════════════════════════════
"!PYTHON_EXE!" -m pip --version >nul 2>&1
if errorlevel 1 (
    echo   [..] pip is missing - installing it...
    "!PYTHON_EXE!" -m ensurepip --default-pip
    if errorlevel 1 (
        color 0C
        echo   [X] Could not install pip automatically.
        echo.
        pause
        exit /b 1
    )
    echo   [OK]  pip installed.
    echo.
)

REM ═══════════════════════════════════════════════════
REM   4. Ensure PyQt5 is installed (visible progress!)
REM ═══════════════════════════════════════════════════
"!PYTHON_EXE!" -c "import PyQt5" >nul 2>&1
if errorlevel 1 (
    echo   [..] PyQt5 is not installed for this Python.
    echo        Installing it now - this can take 1-2 minutes.
    echo        Please do not close this window.
    echo.
    echo   ----------------------------------------
    "!PYTHON_EXE!" -m pip install PyQt5
    set "PIP_EXIT=!errorlevel!"
    echo   ----------------------------------------
    echo.
    if !PIP_EXIT! neq 0 (
        color 0C
        echo   [X] PyQt5 install failed.
        echo.
        echo       Try running this manually:
        echo         "!PYTHON_EXE!" -m pip install PyQt5
        echo.
        pause
        exit /b 1
    )
    REM verify it actually imports now
    "!PYTHON_EXE!" -c "import PyQt5" >nul 2>&1
    if errorlevel 1 (
        color 0C
        echo   [X] PyQt5 still will not import after install.
        echo       Something is wrong with this Python installation.
        echo.
        pause
        exit /b 1
    )
    echo   [OK]  PyQt5 installed successfully.
    echo.
) else (
    echo   [OK]  PyQt5 already installed.
    echo.
)

REM ═══════════════════════════════════════════════════
REM   5. Prefer pythonw.exe (silent launch, no console)
REM ═══════════════════════════════════════════════════
set "PYTHONW_EXE=!PYTHON_EXE:python.exe=pythonw.exe!"
if not exist "!PYTHONW_EXE!" set "PYTHONW_EXE=!PYTHON_EXE!"

REM ═══════════════════════════════════════════════════
REM   6. Launch!
REM ═══════════════════════════════════════════════════
echo   [OK]  All checks passed.
echo.
echo   ⚡  Launching pulse...
echo.
timeout /t 2 /nobreak >nul

start "" "!PYTHONW_EXE!" "%~dp0pulse.pyw"

exit /b 0
