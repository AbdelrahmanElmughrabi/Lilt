; Private device-testing installer. Consume the audited app folder without rebuilding it.
#ifndef PayloadDir
  #error PayloadDir must point to the audited Violilt folder.
#endif
#ifndef PackageVersion
  #define PackageVersion "0.2.0.0"
#endif
#ifndef BetaVersion
  #define BetaVersion "0.2"
#endif

[Setup]
AppId=Violilt.PrivateDeviceTest
AppName=Violilt Beta
AppVersion={#PackageVersion}
AppVerName=Violilt Beta v{#BetaVersion}
AppPublisherURL=https://velourvolute.com/violilt
AppSupportURL=https://velourvolute.com/violilt/support
DefaultDirName={localappdata}\Programs\VioliltTest
DefaultGroupName=Violilt Test
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.22000
OutputBaseFilename=Violilt-Beta-v{#BetaVersion}-x64-Setup
SetupIconFile=..\..\assets\violilt.ico
WizardImageFile=wizard-logo.png
WizardSmallImageFile=..\..\assets\violilt.png
UninstallDisplayIcon={app}\Violilt.exe
Compression=lzma2/normal
SolidCompression=yes
WizardStyle=modern
DisableWelcomePage=no
DisableProgramGroupPage=yes
DisableDirPage=no
UsePreviousAppDir=yes
CloseApplications=no
RestartApplications=no
Uninstallable=yes
UninstallDisplayName=Violilt Test
VersionInfoDescription=Violilt Beta installer
VersionInfoVersion={#PackageVersion}
SetupLogging=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked

[Files]
Source: "{#PayloadDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Violilt Test"; Filename: "{app}\Violilt.exe"; WorkingDir: "{app}"
Name: "{group}\Uninstall Violilt Test"; Filename: "{uninstallexe}"
Name: "{userdesktop}\Violilt Test"; Filename: "{app}\Violilt.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Messages]
WelcomeLabel2=This installs Violilt Beta v{#BetaVersion} for your Windows account.%n%nCPU voices, models and the optional NVIDIA runtime are included. Microsoft Edge WebView2 is required.%n%nThis beta uses a separate test library. Uninstalling keeps your documents and recordings.
FinishedLabel=Violilt Beta is installed. Open Violilt Test from the Start menu when you are ready.

; No automatic app launch, services, drivers, certificates, associations, or app-data deletion.
