NSIS Installer

This folder contains an NSIS script and a PowerShell helper to build a Windows installer for the app.

Build (after installing NSIS):

1. Install NSIS: https://nsis.sourceforge.io/Download
2. Open PowerShell in this folder and run:

   ./build_installer.ps1

Or run makensis directly:

   makensis win_installer.nsi

The resulting installer will be placed at `installer/out/WinGet-Package-Installer-Setup.exe` (when built).

Notes:
- The script embeds `dist/main.exe` and `app_icon.ico` into the installer.
- Administrator privileges are required to install into Program Files.
- The installer creates Start Menu and Desktop shortcuts and an uninstaller.
- The installer registers the app in Windows "Apps & Features" / Add or remove programs so it can be uninstalled from Settings.

