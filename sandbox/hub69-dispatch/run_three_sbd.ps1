param(
    [Parameter(Mandatory=$true)][string]$OfficeSource,
    [Parameter(Mandatory=$true)][string]$OutputDirectory,
    [string]$Python = 'python',
    [string]$DependencyPath = ''
)
$ErrorActionPreference = 'Stop'
$previousSource = $env:HUB69_OFFICE_SRC
$previousPath = $env:PYTHONPATH
$previousUtf8 = $env:PYTHONUTF8
try {
    $env:HUB69_OFFICE_SRC = (Resolve-Path -LiteralPath $OfficeSource).Path
    $env:PYTHONUTF8 = '1'
    if ($DependencyPath) { $env:PYTHONPATH = $DependencyPath }
    & $Python (Join-Path $PSScriptRoot 'three_sbd_pilot.py') --out $OutputDirectory
    if ($LASTEXITCODE -ne 0) { throw "Sandbox pilot failed with exit code $LASTEXITCODE" }
} finally {
    $env:HUB69_OFFICE_SRC = $previousSource
    $env:PYTHONPATH = $previousPath
    $env:PYTHONUTF8 = $previousUtf8
}
