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
UninstallDisplayIcon={app}\app_icon.ico
UninstallDisplayName={#MyAppName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Copy complete bundled application directory
Source: "dist\InventoryManagementSystem\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "app_icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "app_icon.png"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app_icon.ico"; IconIndex: 0
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"; IconFilename: "{app}\app_icon.ico"; IconIndex: 0
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app_icon.ico"; IconIndex: 0; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
var
  KeepExistingData: Boolean;

// Prompt user at install time if earlier database/data exists
function InitializeSetup(): Boolean;
var
  LocalDbPath: String;
  UserChoice: Integer;
begin
  Result := True;
  KeepExistingData := True;
  LocalDbPath := ExpandConstant('{localappdata}\InventoryManagementSystem\database\ims.db');

  if FileExists(LocalDbPath) then
  begin
    UserChoice := MsgBox(
      'An existing inventory database and user account were found from an earlier installation.' + #13#10#13#10 +
      'Do you want to KEEP and use your existing data?' + #13#10#13#10 +
      '• Click YES to PRESERVE existing data (all products and users will be retained).' + #13#10 +
      '• Click NO to START FRESH (older data will be wiped for a clean initial setup).',
      mbConfirmation, MB_YESNO
    );
    if UserChoice = IDNO then
    begin
      KeepExistingData := False;
    end;
  end;
end;

// Handle fresh start cleanup during installation if requested
procedure CurStepChanged(CurStep: TSetupStep);
var
  DataDir: String;
  DbFile: String;
  BackupFile: String;
begin
  if (CurStep = ssPostInstall) and (not KeepExistingData) then
  begin
    DataDir := ExpandConstant('{localappdata}\InventoryManagementSystem\database');
    DbFile := DataDir + '\ims.db';
    if FileExists(DbFile) then
    begin
      BackupFile := DataDir + '\ims_backup_' + GetDateTimeString('yyyymmdd_hhnnss', #0, #0) + '.bak';
      RenameFile(DbFile, BackupFile);
      DeleteFile(DbFile + '-wal');
      DeleteFile(DbFile + '-shm');
      DeleteFile(DbFile + '-journal');
    end;
  end;
end;

// Prompt user at uninstall time to keep or remove data
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  UserChoice: Integer;
  DataRoot: String;
  LocalDbPath: String;
begin
  if CurUninstallStep = usUninstall then
  begin
    DataRoot := ExpandConstant('{localappdata}\InventoryManagementSystem');
    LocalDbPath := DataRoot + '\database\ims.db';

    if FileExists(LocalDbPath) or DirExists(DataRoot) then
    begin
      UserChoice := MsgBox(
        'Do you want to KEEP your inventory database and user account details on this computer?' + #13#10#13#10 +
        '• Click YES to keep your data safe. If you reinstall IMS later, your records will be preserved.' + #13#10 +
        '• Click NO to permanently remove all database files and user records.',
        mbConfirmation, MB_YESNO
      );
      if UserChoice = IDNO then
      begin
        DelTree(DataRoot, True, True, True);
      end;
    end;
  end;
end;
