; Private device-testing installer. Consume the audited app folder without rebuilding it.
#ifndef PayloadDir
  #error PayloadDir must point to the audited Violilt folder.
#endif
#ifndef PackageVersion
  #define PackageVersion "1.0.4.0"
#endif

[Setup]
AppId=Violilt.PrivateDeviceTest
AppName=Violilt Test
AppVersion={#PackageVersion}
AppVerName=Violilt Test {#PackageVersion}
AppPublisherURL=https://velourvolute.com/violilt
AppSupportURL=https://velourvolute.com/violilt/support
DefaultDirName={localappdata}\Programs\VioliltTest
DefaultGroupName=Violilt Test
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.22000
OutputBaseFilename=Violilt-Test-{#PackageVersion}-x64-Setup
SetupIconFile=..\..\assets\violilt.ico
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
VersionInfoDescription=Violilt private device-test installer
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
WelcomeLabel2=This installs Violilt Test for your Windows account.%n%nCPU voices, models and the optional NVIDIA runtime are included. Microsoft Edge WebView2 is required.%n%nThis test build uses a separate test library. Uninstalling keeps your documents and recordings.
FinishedLabel=Violilt Test is installed. Open it from the Start menu when you are ready.

; No automatic app launch, services, drivers, certificates, associations, or app-data deletion.
