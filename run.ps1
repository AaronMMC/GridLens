<#
.SYNOPSIS
    Build GridLens if needed, then run the built exe.
.PARAMETER Build
    Force-rebuild the exe before running.
.PARAMETER Rebuild
    Alias for -Build.
#>
param(
    [switch]$Build,
    [switch]$Rebuild
)

$needBuild = $Build -or $Rebuild -or -not (Test-Path -LiteralPath "dist\GridLens.exe")

if ($needBuild) {
    Write-Host "Building GridLens..." -ForegroundColor Cyan
    & .\build.ps1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Build failed — starting from source instead."
        Start-Process python -ArgumentList "main.py"
        exit 1
    }
}

Write-Host "Launching GridLens..." -ForegroundColor Green
Start-Process -FilePath "dist\GridLens.exe"
