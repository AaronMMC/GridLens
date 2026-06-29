@echo off
REM GridLens — installer build script
REM ========================================
REM
REM 1. Builds GridLens.exe (if needed) via build.bat
REM 2. Compiles the NSIS installer with the version from core/version.py
REM
REM Requires:
REM   NSIS (makensis) installed and in PATH  ->  https://nsis.sourceforge.io
REM   Python to extract the version string
REM

setlocal enabledelayedexpansion

REM ── Read version from core/version.py ─────────────────────────────────────
set "VERSION_FILE=core\version.py"
if not exist "%VERSION_FILE%" (
    echo [ERROR] %VERSION_FILE% not found.
    echo        Run this script from the project root.
    exit /b 1
)

for /f "tokens=2 delims==" %%a in ('findstr /b "__version__" "%VERSION_FILE%" 2^>nul') do (
    set RAW=%%a
)
if not defined RAW (
    echo [ERROR] Could not read __version__ from %VERSION_FILE%.
    exit /b 1
)

REM Strip quotes and whitespace
set VERSION=!RAW:"=!
set VERSION=!VERSION: =!

if not defined VERSION (
    echo [ERROR] Version string is empty.
    exit /b 1
)

echo === GridLens Installer Builder v%VERSION% ===
echo.

REM ── Ensure the executable exists ──────────────────────────────────────────
if not exist "dist\GridLens.exe" (
    echo GridLens.exe not found — building first...
    call build.bat
    if errorlevel 1 (
        echo [ERROR] PyInstaller build failed. Cannot create installer.
        exit /b 1
    )
)

REM ── Check for NSIS ────────────────────────────────────────────────────────
where makensis >nul 2>nul
if errorlevel 1 (
    echo [ERROR] makensis not found in PATH.
    echo        Install NSIS from https://nsis.sourceforge.io and ensure
    echo        makensis.exe is in your PATH.
    exit /b 1
)

REM ── Build the installer ───────────────────────────────────────────────────
echo Compiling installer with version v%VERSION%...
makensis /DVERSION="%VERSION%" installer.nsi

if errorlevel 1 (
    echo [ERROR] NSIS compilation failed.
    exit /b 1
)

echo.
echo Installer built successfully!
echo Output: dist\GridLens_Setup_v%VERSION%.exe
echo.
