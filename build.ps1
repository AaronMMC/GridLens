<#
.SYNOPSIS
    Build GridLens.exe using the PyInstaller spec file.

.DESCRIPTION
    Uses GridLens.spec which auto-generates version_info.txt from
    core/version.py, ensuring the .exe file properties (right-click ->
    Details) always reflect the current application version.

    Poppler (for PDF) and Google OAuth credentials are bundled
    automatically by the spec file when present.

    Requires:
        pyinstaller  (pip install pyinstaller)
        Poppler in poppler/bin/  (optional)

.EXAMPLE
    .\build.ps1
#>

$ErrorActionPreference = "Stop"

$pyinstaller = Get-Command pyinstaller -ErrorAction SilentlyContinue
if (-not $pyinstaller) {
    Write-Error "PyInstaller not found. Activate your venv or install with: pip install pyinstaller"
    exit 1
}

Write-Host "=== Building GridLens via spec file (GridLens.spec) ===" -ForegroundColor Cyan
Write-Host "The spec auto-generates Windows version metadata from core/version.py." -ForegroundColor Gray
Write-Host ""

pyinstaller GridLens.spec --noconfirm

if ($LASTEXITCODE -ne 0) {
    Write-Error "PyInstaller failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Build complete." -ForegroundColor Green
Write-Host "Executable: dist\GridLens.exe" -ForegroundColor Green
