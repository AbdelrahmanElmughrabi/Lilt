[CmdletBinding(SupportsShouldProcess)]
param([Parameter(Mandatory=$true)][string]$PackagePath)
$ErrorActionPreference = 'Stop'
$violiltWorkspace = Split-Path -Parent $PSScriptRoot
$violiltPackage = (Get-Item -LiteralPath $PackagePath).FullName
$violiltAllowed = [IO.Path]::GetFullPath((Join-Path $violiltWorkspace 'dist')) + [IO.Path]::DirectorySeparatorChar
if (!$violiltPackage.StartsWith($violiltAllowed, [StringComparison]::OrdinalIgnoreCase)) { throw 'Select the local compatibility package inside this workspace dist folder.' }
$violiltConfig = Get-Content -LiteralPath (Join-Path $violiltWorkspace 'packaging\msix\compatibility.json') -Raw | ConvertFrom-Json
Add-Type -AssemblyName System.IO.Compression.FileSystem
$violiltArchive = [IO.Compression.ZipFile]::OpenRead($violiltPackage)
try {
    $violiltManifestEntry = $violiltArchive.GetEntry('AppxManifest.xml')
    if (!$violiltManifestEntry) { throw 'Package manifest not found.' }
    $violiltReader = New-Object IO.StreamReader($violiltManifestEntry.Open())
    try { [xml]$violiltManifest = $violiltReader.ReadToEnd() } finally { $violiltReader.Dispose() }
} finally { $violiltArchive.Dispose() }
$violiltIdentity = $violiltManifest.Package.Identity
if ($violiltIdentity.Name -ne $violiltConfig.identity_name -or $violiltIdentity.Publisher -ne $violiltConfig.publisher) {
    throw 'This installer accepts only the explicit unsigned local compatibility identity. Store/other packages are refused.'
}
$violiltInventoryPath = Join-Path (Split-Path -Parent $violiltPackage) ('inventory-' + $violiltIdentity.Version + '.json')
$violiltInventory = Get-Content -LiteralPath $violiltInventoryPath -Raw | ConvertFrom-Json
if ($violiltInventory.compatibility_only -ne $true -or $violiltInventory.store_ready -ne $false -or
    (Get-FileHash -LiteralPath $violiltPackage -Algorithm SHA256).Hash -ne $violiltInventory.package_sha256) {
    throw 'The compatibility inventory/package hash check failed.'
}
Write-Output ('Verified local CPU/GPU test package ' + $violiltIdentity.Version + ', SHA256 ' + $violiltInventory.package_sha256)
if (!$PSCmdlet.ShouldProcess($violiltPackage, 'Install the local unsigned Violilt MSIX compatibility test package')) { return }
$violiltPrincipal = [Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent())
if (!$violiltPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Windows requires Administrator PowerShell for unsigned packages containing executable code. Re-run this helper in an Administrator PowerShell. No security setting or certificate trust was changed.'
}
Add-AppxPackage -Path $violiltPackage -AllowUnsigned
Get-AppxPackage -Name $violiltConfig.identity_name | Select-Object Name,Version,PackageFamilyName,InstallLocation
Write-Output 'Launch Violilt MSIX Compatibility from Start as your normal user. This installation does not prove CPU/GPU runtime or update compatibility; run the documented checks next.'
