@echo off
REM Include Poppler binaries for PDF support (if available)
IF EXIST "poppler\bin" (
    pyinstaller --onefile --windowed --icon=assets/icon.ico --name=SpreadsheetScanner --add-data ".env.example;." --add-binary "poppler/bin/*;poppler/bin" --noconfirm main.py
) ELSE (
    pyinstaller --onefile --windowed --icon=assets/icon.ico --name=SpreadsheetScanner --add-data ".env.example;." --noconfirm main.py
)
echo Done. Check /dist.
