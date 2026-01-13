Installers

This folder contains installer scripts and a PowerShell helper to build a Windows installer for the app. Two installer backends are included: **NSIS** and **Inno Setup**.

Prerequisites
- For NSIS builds: install NSIS and have `makensis.exe` on your PATH (https://nsis.sourceforge.io/Download)
- For Inno Setup builds: install Inno Setup and have `ISCC.exe` on your PATH (https://jrsoftware.org/isinfo.php)

Build (default uses Inno Setup):

- Build with Inno Setup:

  ./build_installer.ps1 -Method inno

- Build with NSIS:

  ./build_installer.ps1 -Method nsis

Notes
- The scripts embed `dist/main.exe` and `app_icon.ico` into the installer; ensure you've built the app (PyInstaller output) before running the build script.
- Administrator privileges are required to install into Program Files (default per-machine install).
- The installer creates Start Menu and Desktop shortcuts and an uninstaller.
- The installer registers the app in Windows "Apps & Features" / Add or remove programs so it can be uninstalled from Settings.
- Output: `installer/out/WinGet-Package-Installer-Setup.exe` (Inno uses the same filename as the NSIS script).

If you'd like, I can wire this into CI to produce signed installers automatically — do you want that next?
