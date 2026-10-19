; Build with Inno Setup 6; paths are relative to this script, not the shell CWD.
#ifndef AppVersion
  #define AppVersion "0.2.0"
#endif
#define RepoRoot AddBackslash(SourcePath) + ".."

[Setup]
AppId=org.visor.desktop
AppName=VISOR
AppVersion={#AppVersion}
DefaultDirName={localappdata}\Programs\VISOR
DefaultGroupName=VISOR
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir={#RepoRoot}\dist\installers
OutputBaseFilename=VISOR-{#AppVersion}-windows-setup
SetupIconFile={#RepoRoot}\src\visor\assets\visor.ico
UninstallDisplayIcon={app}\VISOR.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked

[Files]
Source: "{#RepoRoot}\dist\VISOR\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\VISOR"; Filename: "{app}\VISOR.exe"
Name: "{autodesktop}\VISOR"; Filename: "{app}\VISOR.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\VISOR.exe"; Description: "Launch VISOR"; Flags: nowait postinstall skipifsilent
