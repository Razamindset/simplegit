param(
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$IconPng = Join-Path $Root "icon.png"
$AssetsDir = Join-Path $Root "assets"
$IconIco = Join-Path $AssetsDir "icon.ico"
$BuildVenv = Join-Path $Root ".venv-build"
$BuildPython = Join-Path $BuildVenv "Scripts\python.exe"
$WebsiteDownloads = Join-Path $Root "website\downloads"
$ExePath = Join-Path $Root "dist\SimpleGit.exe"

Set-Location $Root

if (-not (Test-Path $IconPng)) {
    throw "icon.png was not found in the project root."
}

if (-not (Test-Path $BuildPython)) {
    python -m venv $BuildVenv
}

if (-not $SkipInstall) {
    & $BuildPython -m pip install --upgrade pip
    & $BuildPython -m pip install -r requirements.txt
}

New-Item -ItemType Directory -Force -Path $AssetsDir | Out-Null

& $BuildPython -c "from PIL import Image; from pathlib import Path; src=Path('icon.png'); dst=Path('assets/icon.ico'); im=Image.open(src).convert('RGBA'); im.save(dst, sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])"

& $BuildPython -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name SimpleGit `
    --icon $IconIco `
    --add-data "$IconPng;." `
    --specpath "build" `
    main.py

New-Item -ItemType Directory -Force -Path $WebsiteDownloads | Out-Null

if (-not (Test-Path $ExePath)) {
    throw "Build failed because $ExePath was not created."
}

Copy-Item -Force $ExePath (Join-Path $WebsiteDownloads "SimpleGit.exe")

Write-Host ""
Write-Host "Build complete:"
Write-Host "  App:     $ExePath"
Write-Host "  Website: $Root\website\index.html"
Write-Host "  Web exe: $WebsiteDownloads\SimpleGit.exe"
