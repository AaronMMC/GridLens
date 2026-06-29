@echo off
REM GridLens — build script
REM ==========================
REM Uses the PyInstaller spec file (GridLens.spec) which auto-generates
REM version_info.txt from core/version.py so the .exe file properties
REM always match the application version.
REM
REM Requires:
REM   pip install pyinstaller
REM   Poppler in poppler\bin\  (optional — for PDF support)
REM
REM Usage:
REM   build.bat
REM

setlocal

echo === Building GridLens via spec file (GridLens.spec) ===
echo.
echo The spec auto-generates Windows version metadata from core/version.py.
echo.

pyinstaller GridLens.spec --noconfirm

if errorlevel 1 (
    echo.
    echo [ERROR] PyInstaller failed. See output above.
    exit /b 1
)

echo.
echo Build complete.
echo Executable: dist\GridLens.exe
echo.
