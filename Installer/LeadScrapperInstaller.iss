; LeadScrapper Installer Script
; AppVersion wird beim Build automatisch aktualisiert

[Setup]
AppName=LeadScrapper
AppVersion=1.0.0
DefaultDirName={pf}\LeadScrapper
DefaultGroupName=LeadScrapper
OutputDir=Installer
OutputBaseFilename=LeadScrapperInstaller
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
SetupIconFile=Installer\scraper.ico
DisableWelcomePage=no
ShowLanguageDialog=no

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Files]
Source: "dist\leadscrapper.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "output\*";                     DestDir: "{app}\output"; Flags: ignoreversion recursesubdirs
Source: "app\logs\*";                   DestDir: "{app}\logs";   Flags: ignoreversion recursesubdirs
Source: "app\static\*";                 DestDir: "{app}\static"; Flags: ignoreversion recursesubdirs
Source: "app\templates\*";              DestDir: "{app}\templates"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\LeadScrapper starten"; Filename: "{app}\leadscrapper.exe"; IconFilename: "{app}\scraper.ico"
Name: "{commondesktop}\LeadScrapper";  Filename: "{app}\leadscrapper.exe"; Tasks: desktopicon
Name: "{group}\{cm:UninstallProgram,LeadScrapper}"; Filename: "{uninstallexe}"

[Tasks]
Name: "desktopicon"; Description: "Desktop-Verknüpfung erstellen"; GroupDescription: "Zusätzliche Icons:"; Flags: unchecked

[UninstallDelete]
Type: files;      Name: "{app}\*.*"
Type: dirifempty; Name: "{app}"

[Run]
Filename: "{app}\leadscrapper.exe"; Description: "LeadScrapper jetzt starten"; Flags: nowait postinstall skipifsilent
