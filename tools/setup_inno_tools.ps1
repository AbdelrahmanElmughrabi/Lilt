param()
$ErrorActionPreference = 'Stop'
$violiltWorkspace = Split-Path -Parent $PSScriptRoot
$violiltPin = Get-Content -LiteralPath (Join-Path $violiltWorkspace 'packaging/test-installer/toolchain.json') -Raw | ConvertFrom-Json
$violiltToolRoot = Join-Path $violiltWorkspace ('.tmp/inno-toolchain/' + $violiltPin.version)
New-Item -ItemType Directory -Path $violiltToolRoot -Force | Out-Null
$violiltDownload = Join-Path $violiltToolRoot 'innosetup-x64.exe'
if (!(Test-Path -LiteralPath $violiltDownload)) {
    Invoke-WebRequest -Uri $violiltPin.url -OutFile $violiltDownload
}
if ((Get-FileHash -LiteralPath $violiltDownload -Algorithm SHA256).Hash -ne $violiltPin.sha256) {
    throw 'Inno Setup download does not match the pinned official release. Preserved for inspection.'
}
$violiltSignature = Get-AuthenticodeSignature -LiteralPath $violiltDownload
if ($violiltSignature.Status -ne 'Valid' -or $violiltSignature.SignerCertificate.Subject -notmatch 'O="?Pyrsys B\.V\."?(?:,|$)') {
    throw ('Official Inno Setup signature validation failed: ' + $violiltSignature.Status)
}
$violiltCompilerRoot = Join-Path $violiltToolRoot 'portable'
$violiltCompiler = Join-Path $violiltCompilerRoot 'ISCC.exe'
if (!(Test-Path -LiteralPath $violiltCompiler)) {
    # Official /PORTABLE=1 disables uninstaller/associations/shortcuts. No OS trust changes.
    $violiltArguments = @('/PORTABLE=1', '/CURRENTUSER', '/VERYSILENT', '/SUPPRESSMSGBOXES', '/SP-', '/NORESTART', '/NOICONS', '/TASKS=""', ('/DIR="' + $violiltCompilerRoot + '"'), ('/LOG="' + (Join-Path $violiltToolRoot 'portable-extraction.log') + '"'))
    $violiltProcess = Start-Process -FilePath $violiltDownload -ArgumentList $violiltArguments -WindowStyle Hidden -Wait -PassThru
    if ($violiltProcess.ExitCode -ne 0) { throw ('Portable compiler extraction failed: ' + $violiltProcess.ExitCode) }
}
$violiltCompilerSignature = Get-AuthenticodeSignature -LiteralPath $violiltCompiler
if ($violiltCompilerSignature.Status -ne 'Valid' -or $violiltCompilerSignature.SignerCertificate.Subject -notmatch 'O="?Pyrsys B\.V\."?(?:,|$)') {
    throw 'Extracted compiler signature validation failed.'
}
Write-Output $violiltCompiler
