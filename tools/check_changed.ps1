param(
    [string[]]$Path,
    [switch]$LintLegacy
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root '.venv\Scripts\python.exe'
$logRoot = Join-Path $root '.tool-logs'
New-Item -ItemType Directory -Force -Path $logRoot | Out-Null

if (-not (Test-Path -LiteralPath $python)) {
    throw 'Missing .venv. Run tools\bootstrap_dev.ps1 first.'
}

if ($Path) {
    $relativeFiles = @($Path)
} else {
    $tracked = @(git -C $root diff --name-only --diff-filter=ACM HEAD -- '*.py')
    $untracked = @(git -C $root ls-files --others --exclude-standard -- '*.py')
    $relativeFiles = @($tracked + $untracked | Sort-Object -Unique)
}

$files = @(
    $relativeFiles |
        ForEach-Object { Join-Path $root $_ } |
        Where-Object { Test-Path -LiteralPath $_ -PathType Leaf }
)

if (-not $files) {
    Write-Output 'CHECK_CHANGED no-python-files'
    exit 0
}

function Invoke-LoggedCheck {
    param([string]$Name, [string[]]$Arguments)
    $log = Join-Path $logRoot ($Name + '.log')
    & $python @Arguments *> $log
    if ($LASTEXITCODE -ne 0) {
        Write-Output ("FAILED {0}" -f $Name)
        Get-Content -LiteralPath $log -Tail 40
        exit $LASTEXITCODE
    }
    Write-Output ("PASS {0}" -f $Name)
}

Invoke-LoggedCheck 'compile' (@('-m', 'py_compile') + $files)

$newFiles = @(
    git -C $root ls-files --others --exclude-standard -- '*.py' |
        ForEach-Object { Join-Path $root $_ } |
        Where-Object { Test-Path -LiteralPath $_ -PathType Leaf }
)
$cleanModules = @(
    $files | Where-Object {
        $relative = [System.IO.Path]::GetRelativePath($root, $_)
        $LintLegacy -or
        $_ -in $newFiles -or
        $_ -match 'compact_query\.py$' -or
        $_ -match 'cli[\\/]commands[\\/]query\.py$' -or
        $_ -match 'tests[\\/]test_compact_query\.py$' -or
        $relative -match '^tools[\\/]'
    }
)

if ($cleanModules) {
    Invoke-LoggedCheck 'black' (@('-m', 'black', '--check') + $cleanModules)
    Invoke-LoggedCheck 'ruff' (@('-m', 'ruff', 'check') + $cleanModules)
}

$compactChanged = $files | Where-Object {
    $_ -match 'compact_query\.py$' -or $_ -match 'test_compact_query\.py$'
}
if ($compactChanged) {
    $testPath = Join-Path $root 'blender-remote-1.3.3\tests\test_compact_query.py'
    Invoke-LoggedCheck 'pytest-compact' @('-m', 'pytest', '-q', '--noconftest', $testPath)
}

$installerChanged = $files | Where-Object {
    $_ -match 'tools[\\/](blender_addons|test_blender_addons)\.py$'
}
if ($installerChanged) {
    $testPath = Join-Path $root 'tools\test_blender_addons.py'
    Invoke-LoggedCheck 'pytest-installer' @('-m', 'pytest', '-q', '--noconftest', $testPath)
}

Write-Output ("CHECK_CHANGED ok files={0} linted={1}" -f $files.Count, $cleanModules.Count)
