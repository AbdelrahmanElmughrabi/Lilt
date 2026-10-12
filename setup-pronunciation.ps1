param([string]$BootstrapPython = '.\.venv\Scripts\python.exe')
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$liltCandidateTemp = Join-Path $PSScriptRoot '.tmp\pronunciation-pip-temp'
New-Item -ItemType Directory -Path $liltCandidateTemp -Force | Out-Null
$env:TEMP = $liltCandidateTemp
$env:TMP = $liltCandidateTemp
$liltCandidatePython = Join-Path $PSScriptRoot '.tmp\pronunciation-env\Scripts\python.exe'
if (!(Test-Path -LiteralPath $liltCandidatePython)) {
    & $BootstrapPython -m venv (Join-Path $PSScriptRoot '.tmp\pronunciation-env')
    if ($LASTEXITCODE -ne 0) { throw 'Candidate environment creation failed.' }
}
& $liltCandidatePython -m ensurepip --upgrade
if ($LASTEXITCODE -ne 0) { throw 'Candidate pip preparation failed.' }
$liltCandidateRequirements = if (Test-Path -LiteralPath 'requirements-pronunciation.lock.txt') { 'requirements-pronunciation.lock.txt' } else { 'requirements-pronunciation.txt' }
& $liltCandidatePython -m pip install --cache-dir (Join-Path $PSScriptRoot '.pip-cache') -r $liltCandidateRequirements
if ($LASTEXITCODE -ne 0) { throw 'Candidate dependency installation failed.' }
& $liltCandidatePython -m pip check
if ($LASTEXITCODE -ne 0) { throw 'Candidate dependency resolution is inconsistent.' }
& $liltCandidatePython tools\assemble_pronunciation_notices.py --download-sources
if ($LASTEXITCODE -ne 0) { throw 'Candidate notice/source preparation failed.' }
Write-Output 'Prepared .tmp\pronunciation-env. The baseline environment remains available.'
