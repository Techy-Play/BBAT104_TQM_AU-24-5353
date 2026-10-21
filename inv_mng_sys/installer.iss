; Script generated for Inno Setup 6
; Inventory Management System (IMS) - Offline Desktop Application (Q13)

#define MyAppName "Inventory Management System"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "BBAT104 TQM Course Project"
#define MyAppExeName "InventoryManagementSystem.exe"
#define MyAppAssocName "IMS Inventory"
#define MyAppAssocExt ".ims"
#define MyAppAssocKey StringChange(MyAppAssocName, " ", "") + MyAppAssocExt

[Setup]
; App identification
AppId={{8B1A02E4-3A4E-4FD7-A77C-0C59D960B8E1}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppVerName={#MyAppName} {#MyAppVersion}

; Installation directories
DefaultDirName={autopf}\Inventory Management System
DefaultGroupName={#MyAppName}
AllowNoIcons=yes

; Output settings
OutputDir=dist_installer
OutputBaseFilename=setup
SetupIconFile=app_icon.ico

; Compression & visual styling
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

; Permissions and multi-user support
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog commandline

; Uninstall styling
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Copy complete bundled application directory
Source: "dist\InventoryManagementSystem\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app_icon.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app_icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
// Optional custom Pascal script hooks if needed
