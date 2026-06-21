$ErrorActionPreference = "Stop"

$pyinstaller = Get-Command pyinstaller -ErrorAction SilentlyContinue
if (-not $pyinstaller) {
    Write-Error "PyInstaller not found. Activate your venv or install with: pip install pyinstaller"
    exit 1
}

$pyArgs = @(
    "--onefile",
    "--windowed",
    "--icon=assets/icon.ico",
    "--name=SpreadsheetScanner",
    "--add-data", ".env.example;.",
    "--noconfirm",
    "main.py"
)

if (Test-Path -LiteralPath "poppler/bin") {
    Write-Host "Poppler found - bundling..."
    $pyArgs += @("--add-binary", "poppler/bin/*;poppler/bin")
} else {
    Write-Host "Poppler not found - PDF support disabled."
}

if (Test-Path -LiteralPath "credentials/google_oauth_client.json") {
    Write-Host "Google OAuth client found - bundling..."
    $pyArgs += @("--add-data", "credentials/google_oauth_client.json;credentials")
}

Write-Host "Running PyInstaller..."
pyinstaller @pyArgs

if ($LASTEXITCODE -eq 0) {
    Write-Host "Build succeeded! Executable at: dist/SpreadsheetScanner.exe"
} else {
    Write-Error "PyInstaller failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}
