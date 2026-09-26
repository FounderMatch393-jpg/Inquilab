$ErrorActionPreference = "Stop"

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    $systemPython = (Get-Command python -ErrorAction Stop).Source
    & $systemPython -m venv (Join-Path $PSScriptRoot ".venv")
    if ($LASTEXITCODE -ne 0) {
        throw "Could not create the project virtual environment."
    }
}

& $python -m pip install -r (Join-Path $PSScriptRoot "requirements.txt")
if ($LASTEXITCODE -ne 0) {
    throw "Could not install backend build requirements."
}

& $python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --collect-all imageio_ffmpeg `
    --hidden-import media_generator `
    --name inquilab-backend `
    --distpath (Join-Path $PSScriptRoot "src-tauri\resources") `
    --workpath (Join-Path $PSScriptRoot "build\pyinstaller") `
    --specpath (Join-Path $PSScriptRoot "build\pyinstaller") `
    (Join-Path $PSScriptRoot "desktop_backend.py")

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed with exit code $LASTEXITCODE"
}

Write-Host "Backend created at src-tauri/resources/inquilab-backend.exe"
