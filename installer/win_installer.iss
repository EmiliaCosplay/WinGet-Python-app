; Inno Setup script for WinGet Package Installer
; Generated for repository by GitHub Copilot

[Setup]
AppName=WinGet Package Installer
AppVersion=0.2 beta
AppPublisher=Nikki
DefaultDirName={pf}\WinGet Package Installer
DefaultGroupName=WinGet Package Installer
OutputDir=out
OutputBaseFilename=WinGet-Package-Installer-Setup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64
SetupIconFile=..\app_icon.ico
Uninstallable=yes
UninstallDisplayIcon={app}\app_icon.ico

[Files]
Source: "..\dist\main.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\app_icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\WinGet Package Installer"; Filename: "{app}\main.exe"; IconFilename: "{app}\app_icon.ico"
Name: "{commondesktop}\WinGet Package Installer"; Filename: "{app}\main.exe"; IconFilename: "{app}\app_icon.ico"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Run]
Filename: "{app}\main.exe"; Description: "Launch WinGet Package Installer"; Flags: nowait postinstall skipifsilent

[Registry]
; Register the app in Add/Remove Programs (ARP) for both 64-bit and 32-bit registry views
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\WinGet Package Installer"; ValueType: string; ValueName: "DisplayName"; ValueData: "WinGet Package Installer"; Flags: uninsdeletekey
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\WinGet Package Installer"; ValueType: string; ValueName: "DisplayVersion"; ValueData: "0.2 beta"; Flags: uninsdeletevalue
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\WinGet Package Installer"; ValueType: string; ValueName: "Publisher"; ValueData: "Nikki"; Flags: uninsdeletevalue
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\WinGet Package Installer"; ValueType: string; ValueName: "InstallLocation"; ValueData: "{app}"; Flags: uninsdeletevalue
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\WinGet Package Installer"; ValueType: string; ValueName: "UninstallString"; ValueData: "{uninstallexe}"; Flags: uninsdeletevalue
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\WinGet Package Installer"; ValueType: string; ValueName: "DisplayIcon"; ValueData: "{app}\app_icon.ico"; Flags: uninsdeletevalue

; Additionally write the same values to the 32-bit view on 64-bit systems
Root: HKLM; Subkey: "SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\WinGet Package Installer"; ValueType: string; ValueName: "DisplayName"; ValueData: "WinGet Package Installer"; Flags: uninsdeletekey
Root: HKLM; Subkey: "SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\WinGet Package Installer"; ValueType: string; ValueName: "DisplayVersion"; ValueData: "0.2 beta"; Flags: uninsdeletevalue
Root: HKLM; Subkey: "SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\WinGet Package Installer"; ValueType: string; ValueName: "Publisher"; ValueData: "Nikki"; Flags: uninsdeletevalue
Root: HKLM; Subkey: "SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\WinGet Package Installer"; ValueType: string; ValueName: "InstallLocation"; ValueData: "{app}"; Flags: uninsdeletevalue
Root: HKLM; Subkey: "SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\WinGet Package Installer"; ValueType: string; ValueName: "UninstallString"; ValueData: "{uninstallexe}"; Flags: uninsdeletevalue
Root: HKLM; Subkey: "SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\WinGet Package Installer"; ValueType: string; ValueName: "DisplayIcon"; ValueData: "{app}\app_icon.ico"; Flags: uninsdeletevalue
