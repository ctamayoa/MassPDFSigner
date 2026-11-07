; Instalador de Firmador Masivo PDF (Inno Setup 6). Se compila con:
;   ISCC.exe /DAppVersion=1.0.1 packaging\instalador.iss
; Requiere haber generado antes dist\FirmadorPDF\ con PyInstaller (modo carpeta).
#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

[Setup]
AppId={{B1D8A2C4-6E0F-4B7A-9C55-3F2A1D7E8B90}
AppName=Firmador Masivo PDF
AppVersion={#AppVersion}
AppPublisher=ctamayoa
AppPublisherURL=https://github.com/ctamayoa/MassPDFSigner
AppSupportURL=https://github.com/ctamayoa/MassPDFSigner/issues
DefaultDirName={autopf}\FirmadorPDF
DefaultGroupName=Firmador Masivo PDF
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename=FirmadorPDF-Setup-{#AppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern
LicenseFile=..\LICENSE
UninstallDisplayIcon={app}\FirmadorPDF.exe

[Languages]
Name: "es"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"
Name: "pt"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\FirmadorPDF\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{autoprograms}\Firmador Masivo PDF"; Filename: "{app}\FirmadorPDF.exe"
Name: "{autodesktop}\Firmador Masivo PDF"; Filename: "{app}\FirmadorPDF.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\FirmadorPDF.exe"; Description: "{cm:LaunchProgram,Firmador Masivo PDF}"; Flags: nowait postinstall skipifsilent
