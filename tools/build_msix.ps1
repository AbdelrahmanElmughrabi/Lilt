param(
    [switch]$CompatibilityTest,
    [switch]$BuildPayload,
    [string]$PayloadDirectory = 'dist\msix-payload\Violilt',
    [string]$OutputDirectory = 'dist\msix-compatibility',
    [string]$Version = '1.0.0.0'
)
$ErrorActionPreference = 'Stop'
if (!$CompatibilityTest) { throw 'This build supports local compatibility testing only. Pass -CompatibilityTest; do not submit this test identity to the Store.' }
$violiltWorkspace = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $violiltWorkspace
$violiltAllowedOutput = [IO.Path]::GetFullPath((Join-Path $violiltWorkspace 'dist')) + [IO.Path]::DirectorySeparatorChar
$violiltPayload = if ([IO.Path]::IsPathRooted($PayloadDirectory)) { [IO.Path]::GetFullPath($PayloadDirectory) } else { [IO.Path]::GetFullPath((Join-Path $violiltWorkspace $PayloadDirectory)) }
$violiltOutput = if ([IO.Path]::IsPathRooted($OutputDirectory)) { [IO.Path]::GetFullPath($OutputDirectory) } else { [IO.Path]::GetFullPath((Join-Path $violiltWorkspace $OutputDirectory)) }
if (!$violiltOutput.StartsWith($violiltAllowedOutput, [StringComparison]::OrdinalIgnoreCase)) { throw 'MSIX output must be inside this workspace dist folder.' }
$violiltPackagePath = Join-Path $violiltOutput ('Violilt-MsixCompatibility-' + $Version + '-x64.msix')
if (Test-Path -LiteralPath $violiltPackagePath) { throw 'This package version already exists. Use a new version/output directory; existing evidence is not overwritten.' }
if ($BuildPayload) {
    if ($PayloadDirectory -ne 'dist\msix-payload\Violilt') { throw '-BuildPayload uses only dist\msix-payload\Violilt. Omit it to package an explicit existing payload.' }
    & (Join-Path $violiltWorkspace 'build.ps1') -IncludeGpu -OutputDirectory 'dist\msix-payload'
    if ($LASTEXITCODE -ne 0) { throw 'CPU/GPU payload build failed.' }
}
$violiltBin = & (Join-Path $PSScriptRoot 'setup_msix_tools.ps1')
$violiltPython = Join-Path $violiltWorkspace '.tmp\pronunciation-env\Scripts\python.exe'
if (!(Test-Path -LiteralPath $violiltPython)) { throw 'Run setup-pronunciation.ps1 first.' }
$violiltStage = Join-Path $violiltWorkspace ('.tmp\msix-build-' + [Guid]::NewGuid().ToString('N'))
$violiltAssets = Join-Path $violiltStage 'Assets'
New-Item -ItemType Directory -Path $violiltAssets -Force | Out-Null
Add-Type -AssemblyName System.Drawing
$violiltSourceImage = [Drawing.Image]::FromFile((Join-Path $violiltWorkspace 'assets\violilt.png'))
try {
    foreach ($violiltAsset in @(@('StoreLogo.png', 50), @('Square150x150Logo.png', 150), @('Square44x44Logo.png', 44))) {
        $violiltSize = [int]$violiltAsset[1]
        $violiltBitmap = New-Object Drawing.Bitmap($violiltSize, $violiltSize)
        $violiltGraphics = [Drawing.Graphics]::FromImage($violiltBitmap)
        try {
            $violiltGraphics.Clear([Drawing.Color]::Transparent)
            $violiltGraphics.InterpolationMode = [Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
            $violiltScale = [Math]::Min($violiltSize / $violiltSourceImage.Width, $violiltSize / $violiltSourceImage.Height)
            $violiltWidth = [int][Math]::Round($violiltSourceImage.Width * $violiltScale)
            $violiltHeight = [int][Math]::Round($violiltSourceImage.Height * $violiltScale)
            $violiltGraphics.DrawImage($violiltSourceImage, [int](($violiltSize - $violiltWidth) / 2), [int](($violiltSize - $violiltHeight) / 2), $violiltWidth, $violiltHeight)
            $violiltBitmap.Save((Join-Path $violiltAssets $violiltAsset[0]), [Drawing.Imaging.ImageFormat]::Png)
        } finally { $violiltGraphics.Dispose(); $violiltBitmap.Dispose() }
    }
} finally { $violiltSourceImage.Dispose() }
& $violiltPython (Join-Path $PSScriptRoot 'msix_package.py') --payload $violiltPayload --stage $violiltStage --version $Version
if ($LASTEXITCODE -ne 0) { throw 'MSIX payload preparation failed.' }
New-Item -ItemType Directory -Path $violiltOutput -Force | Out-Null
$violiltPackLog = Join-Path $violiltStage 'makeappx.log'
& (Join-Path $violiltBin 'makeappx.exe') pack /f (Join-Path $violiltStage 'mapping.txt') /p $violiltPackagePath /h SHA256 *> $violiltPackLog
if ($LASTEXITCODE -ne 0) {
    Get-Content -LiteralPath $violiltPackLog -Tail 20
    throw 'MakeAppx packaging/manifest validation failed. Staging files remain for inspection.'
}
Get-Content -LiteralPath $violiltPackLog -Tail 3
$violiltInventory = Get-Content -LiteralPath (Join-Path $violiltStage 'inventory.json') -Raw | ConvertFrom-Json
$violiltInventory | Add-Member -NotePropertyName package_sha256 -NotePropertyValue (Get-FileHash -LiteralPath $violiltPackagePath -Algorithm SHA256).Hash.ToLowerInvariant()
$violiltInventory | Add-Member -NotePropertyName package_bytes -NotePropertyValue (Get-Item -LiteralPath $violiltPackagePath).Length
$violiltInventory | Add-Member -NotePropertyName signing -NotePropertyValue 'unsigned; installation and certification not yet tested'
$violiltInventory | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $violiltOutput ('inventory-' + $Version + '.json')) -Encoding utf8
Write-Output ('Built unsigned local compatibility package: ' + $violiltPackagePath)
Write-Output 'Includes CPU + NVIDIA GPU. Uses a separate test identity/library. No certificates were created or trusted; nothing was installed or published.'
