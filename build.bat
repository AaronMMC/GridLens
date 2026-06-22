@echo off
REM SpreadsheetScanner build script
REM Requires: pip install pyinstaller  +  Poppler in poppler\bin (optional, for PDF support)

IF EXIST "poppler\bin" (
    echo Poppler found — PDF support will be bundled.
    pyinstaller --onefile ^
        --windowed ^
        --icon=assets\icon.ico ^
        --name=SpreadsheetScanner ^
        --add-data ".env.example;." ^
        --add-binary "poppler\bin\*;poppler\bin" ^
        --noconfirm ^
        main.py
) ELSE (
    echo Poppler not found — PDF support will not be available.
    pyinstaller --onefile ^
        --windowed ^
        --icon=assets\icon.ico ^
        --name=SpreadsheetScanner ^
        --add-data ".env.example;." ^
        --noconfirm ^
        main.py
)

echo.
echo Done. Check the dist\ folder for SpreadsheetScanner.exe