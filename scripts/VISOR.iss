; Inno Setup Script for VISOR
; Build on Windows with: iscc scripts\VISOR.iss

[Setup]
AppName=VISOR
AppVersion=0.1.0
DefaultDirName={userpf}\VISOR
DefaultGroupName=VISOR
OutputDir=dist
OutputBaseFilename=VISOR-setup
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\VISOR\VISOR.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\VISOR\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\VISOR"; Filename: "{app}\VISOR.exe"

[Run]
Filename: "{app}\VISOR.exe"; Description: "Launch VISOR"; Flags: nowait postinstall skipifsilent
