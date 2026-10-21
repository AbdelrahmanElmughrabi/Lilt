param()
$ErrorActionPreference = 'Stop'
$violiltWorkspace = Split-Path -Parent $PSScriptRoot
$violiltToolchain = Get-Content -LiteralPath (Join-Path $violiltWorkspace 'packaging\msix\toolchain.json') -Raw | ConvertFrom-Json
$violiltToolRoot = Join-Path $violiltWorkspace '.tmp\msix-toolchain'
$violiltExtracted = Join-Path $violiltToolRoot $violiltToolchain.version
$violiltBin = Join-Path $violiltExtracted $violiltToolchain.bin_directory
if (!(Test-Path -LiteralPath $violiltExtracted)) {
    New-Item -ItemType Directory -Path $violiltToolRoot -Force | Out-Null
    $violiltArchive = Join-Path $violiltToolRoot ($violiltToolchain.version + '.nupkg')
    if (!(Test-Path -LiteralPath $violiltArchive)) {
        Invoke-WebRequest -Uri $violiltToolchain.url -OutFile $violiltArchive
    }
    if ((Get-FileHash -LiteralPath $violiltArchive -Algorithm SHA256).Hash -ne $violiltToolchain.sha256) {
        throw 'Windows SDK package hash does not match the pinned toolchain. Leaving the download untouched for inspection.'
    }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [IO.Compression.ZipFile]::ExtractToDirectory($violiltArchive, $violiltExtracted)
}
foreach ($violiltToolName in @('makeappx.exe', 'signtool.exe')) {
    $violiltToolPath = Join-Path $violiltBin $violiltToolName
    $violiltSignature = Get-AuthenticodeSignature -LiteralPath $violiltToolPath
    if ($violiltSignature.Status -ne 'Valid' -or $violiltSignature.SignerCertificate.Subject -notmatch 'O=Microsoft Corporation(?:,|$)') {
        throw ('Microsoft signature verification failed for ' + $violiltToolName)
    }
}
Write-Output $violiltBin
