param(
    [switch]$Recreate
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $root '.venv'
$python = Join-Path $venv 'Scripts\python.exe'

if ($Recreate -and (Test-Path -LiteralPath $venv)) {
    $resolvedRoot = [System.IO.Path]::GetFullPath($root).TrimEnd('\\') + '\\'
    $resolvedVenv = [System.IO.Path]::GetFullPath($venv).TrimEnd('\\') + '\\'
    if (-not $resolvedVenv.StartsWith($resolvedRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove path outside workspace: $resolvedVenv"
    }
    Remove-Item -LiteralPath $venv -Recurse -Force
}

if (-not (Test-Path -LiteralPath $python)) {
    $py312 = & py -3.12 -c "import sys; print(sys.executable)"
    if ($LASTEXITCODE -ne 0 -or -not $py312) {
        throw 'Python 3.12 is required but was not found through py -3.12.'
    }
    & $py312 -m venv $venv
    if ($LASTEXITCODE -ne 0) { throw 'Failed to create .venv.' }
}

& $python -m pip install --disable-pip-version-check --quiet --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'Failed to update pip in .venv.' }

& $python -m pip install --disable-pip-version-check --quiet -r (Join-Path $root 'requirements-dev.lock')
if ($LASTEXITCODE -ne 0) { throw 'Failed to install locked development dependencies.' }

& $python -c "import importlib.metadata as m, sys; print('READY python=' + sys.version.split()[0] + ' pytest=' + m.version('pytest') + ' black=' + m.version('black') + ' ruff=' + m.version('ruff'))"
if ($LASTEXITCODE -ne 0) { throw 'Development environment verification failed.' }
