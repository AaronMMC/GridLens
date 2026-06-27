@echo off
REM Build GridLens if needed, then run the built exe.
REM Usage: run.bat [--build] [--rebuild]

if /I "%1"=="--build" goto build
if /I "%1"=="--rebuild" goto build
if not exist "dist\GridLens.exe" goto build

:run
start "" "dist\GridLens.exe"
exit /b

:build
call build.bat
if errorlevel 1 (
    echo Build failed — starting from source instead.
    start "" python main.py
    exit /b 1
)
goto run
