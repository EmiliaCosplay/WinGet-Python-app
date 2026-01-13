<#
Flexible installer builder supporting NSIS and Inno Setup.
Usage:
  ./build_installer.ps1 -Method inno
  ./build_installer.ps1 -Method nsis

Requirements:
  - NSIS: makensis on PATH (if using -Method nsis)
  - Inno Setup: ISCC.exe on PATH (if using -Method inno)
#>

param(
    [ValidateSet('nsis','inno')]
    [string]$Method = 'inno'
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$outDir = Join-Path $scriptDir 'out'
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir | Out-Null }

# Ensure the built application exists
$expectedExe = (Join-Path $scriptDir '..\dist\main.exe') -replace '\\','\'
if (-not (Test-Path $expectedExe)) {
    Write-Error "Expected application binary not found: $expectedExe. Build the app with PyInstaller (see README) before building the installer."
    exit 1
}

if ($Method -eq 'nsis') {
    $nsis = (Get-Command makensis -ErrorAction SilentlyContinue).Source
    if (-not $nsis) {
        Write-Error "makensis not found in PATH. Install NSIS (https://nsis.sourceforge.io/Download) and ensure makensis.exe is on PATH."
        exit 1
    }

    Write-Host "Building NSIS installer..."
    & $nsis (Join-Path $scriptDir 'win_installer.nsi')
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Installer built: $(Resolve-Path (Join-Path $outDir 'WinGet-Package-Installer-Setup.exe'))"
        exit 0
    } else {
        Write-Error "makensis failed with exit code $LASTEXITCODE"
        exit $LASTEXITCODE
    }
} elseif ($Method -eq 'inno') {
    $iscc = (Get-Command ISCC -ErrorAction SilentlyContinue).Source
    if (-not $iscc) {
        Write-Error "ISCC (Inno Setup Compiler) not found in PATH. Install Inno Setup (https://jrsoftware.org/isinfo.php) and ensure ISCC.exe is on PATH."
        exit 1
    }

    Write-Host "Building Inno Setup installer..."
    & $iscc (Join-Path $scriptDir 'win_installer.iss')
    if ($LASTEXITCODE -eq 0) {
        # Inno will put the output executable in 'out' directory per script
        $outfile = Join-Path $outDir 'WinGet-Package-Installer-Setup.exe'
        if (Test-Path $outfile) {
            Write-Host "Installer built: $(Resolve-Path $outfile)"
            exit 0
        } else {
            Write-Host "ISCC finished but expected output not found. There may have been a different output filename. Check $scriptDir/out"
            exit 0
        }
    } else {
        Write-Error "ISCC failed with exit code $LASTEXITCODE"
        exit $LASTEXITCODE
    }
} else {
    Write-Error "Unknown method: $Method"
    exit 1
}