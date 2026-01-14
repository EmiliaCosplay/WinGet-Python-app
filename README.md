# WinGet - Chocolatey Python app

Simple GUI to search for and install packages using winget and chocolatey.

## Build (create EXE)

PyInstaller is used to create a single-file executable.

From PowerShell (recommended), using the project's virtual environment:

    & ".\.venv\Scripts\python.exe" -m PyInstaller --onefile --noconsole --icon "app_icon.ico" "main.py"

Notes:
- Icon path used: `app_icon.ico` (included in project root)
- Resulting EXE: `dist/main.exe`
- The EXE is unsigned; code signing is recommended for distribution to avoid SmartScreen warnings.
- To rebuild with a console for debugging, remove `--noconsole`.
- The application "About" dialog displays the version (e.g., `0.2 beta`) and copyright; update `main.py` to change it.

---

## Installer (Inno Setup)

This project uses **Inno Setup** as the primary installer format. You can build the installer using the included PowerShell helper or by invoking the Inno compiler directly.

From PowerShell (recommended):

    # From the project root
    ./installer/build_installer.ps1 -Method inno

Or directly with Inno Setup Compiler (ISCC) if installed:

    ISCC.exe installer\win_installer.iss

The script and Inno script will embed `dist/main.exe` and `app_icon.ico` into the installer and place the resulting installer at `installer/out/WinGet-Package-Installer-Setup.exe`.

Notes:
- Ensure `dist/main.exe` exists before running the installer build (build the EXE first).
- Inno Setup (ISCC) is required to compile with `-Method inno` (download from https://jrsoftware.org/isinfo.php).
- The installer uses the `AppVersion`/`DisplayVersion` fields from `installer/win_installer.iss` (currently `0.2 beta`).
- NSIS is still supported via the `-Method nsis` option in `build_installer.ps1`, but Inno is the default and recommended workflow for this repository.

