# WinGet Python app

Simple GUI to search for and install packages using winget.

## Build (create EXE)

PyInstaller is used to create a single-file executable.

From PowerShell, run (PowerShell-safe invocation):

& "C:/Program Files/Python314/python.exe" -m PyInstaller --onefile --noconsole --icon "c:\Users\Nikki Caspar\Documents\WinGet Python app\app_icon.ico" "c:\Users\Nikki Caspar\Documents\WinGet Python app\main.py"

Notes:
- Icon path used: `app_icon.ico` (created and included in project root)
- Resulting EXE: `dist/main.exe`
- The EXE is unsigned; code signing is recommended for distribution to avoid SmartScreen warnings.
- To rebuild with a console for debugging, remove `--noconsole`.

## Installer (NSIS)

An NSIS installer script is available in the `installer/` folder. After installing NSIS (makensis), build the installer from PowerShell in `installer/` with:

    ./build_installer.ps1

Or run directly:

    makensis win_installer.nsi

The script will embed `dist/main.exe` and `app_icon.ico` into the installer and place the resulting installer at `installer/out/WinGet-Package-Installer-Setup.exe`.

