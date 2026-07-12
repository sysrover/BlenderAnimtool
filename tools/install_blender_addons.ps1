param(
    [int]$Port = 6688,
    [switch]$NoHotReload
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    throw 'Missing .venv. Run tools\bootstrap_dev.ps1 first.'
}

$arguments = @((Join-Path $PSScriptRoot 'blender_addons.py'), 'install', '--port', "$Port")
if ($NoHotReload) { $arguments += '--no-hot-reload' }
& $python @arguments
if ($LASTEXITCODE -ne 0) { throw 'Blender addon installation or hot reload failed.' }
