; Inno Setup Script for CyberRFP Maroc
; Company: DataProtech company (DPA) - ICE 003102490000030
; Domain: @dpg-cyber.com

#define MyAppName "CyberRFP Maroc - DPA"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "DataProtech company"
#define MyAppURL "https://www.dataprotech.ma"
#define MyAppExeName "CyberRFP-Maroc.exe"

[Setup]
AppId={{DPA-CYBERRFP-MAROC-2026}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\DataProtech\CyberRFP Maroc
DefaultGroupName=DataProtech\CyberRFP Maroc
AllowNoIcons=yes
OutputDir=..\dist
OutputBaseFilename=CyberRFP_Maroc_Setup_v2.0
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startupicon"; Description: "Démarrer automatiquement en tâche de fond (Veille alertes temps réel PMMP)"; GroupDescription: "Options d'exécution:"; Flags: checkedonce

[Files]
Source: "..\dist\CyberRFP-Maroc.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\cyberrfp.db"; DestDir: "{app}"; Flags: onlyifdoesntexist
Source: "..\src\static\dpa_logo.png"; DestDir: "{app}\static"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: startupicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
