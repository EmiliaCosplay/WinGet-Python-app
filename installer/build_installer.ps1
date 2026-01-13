# Build the NSIS installer (PowerShell helper)
# Requires: NSIS (makensis) available on PATH

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$nsis = (Get-Command makensis -ErrorAction SilentlyContinue).Source
if (-not $nsis) {
    Write-Error "makensis not found in PATH. Install NSIS (https://nsis.sourceforge.io/Download) and ensure makensis.exe is on PATH."
    exit 1
}

# Ensure 'out' directory exists
$outDir = Join-Path $scriptDir 'out'
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir | Out-Null }

# Run makensis
& $nsis (Join-Path $scriptDir 'win_installer.nsi')
if ($LASTEXITCODE -eq 0) {
    Write-Host "Installer built: $(Resolve-Path (Join-Path $outDir 'WinGet-Package-Installer-Setup.exe'))"
} else {
    Write-Error "makensis failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}