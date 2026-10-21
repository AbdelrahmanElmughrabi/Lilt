param([string]$BootstrapPython = 'python')
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$violiltCandidateTemp = Join-Path $PSScriptRoot '.tmp\pronunciation-pip-temp'
New-Item -ItemType Directory -Path $violiltCandidateTemp -Force | Out-Null
$env:TEMP = $violiltCandidateTemp
$env:TMP = $violiltCandidateTemp
$violiltCandidatePython = Join-Path $PSScriptRoot '.tmp\pronunciation-env\Scripts\python.exe'
if (!(Test-Path -LiteralPath $violiltCandidatePython)) {
    & $BootstrapPython -m venv (Join-Path $PSScriptRoot '.tmp\pronunciation-env')
    if ($LASTEXITCODE -ne 0) { throw 'Candidate environment creation failed.' }
}
& $violiltCandidatePython -m ensurepip --upgrade
if ($LASTEXITCODE -ne 0) { throw 'Candidate pip preparation failed.' }
& $violiltCandidatePython -m pip install --require-hashes --only-binary=:all: --cache-dir (Join-Path $PSScriptRoot '.pip-cache') -r requirements-build.lock.txt
if ($LASTEXITCODE -ne 0) { throw 'Pinned build-tool preparation failed.' }
& $violiltCandidatePython -m pip install --cache-dir (Join-Path $PSScriptRoot '.pip-cache') -r requirements.lock.txt
if ($LASTEXITCODE -ne 0) { throw 'Candidate dependency installation failed.' }
& $violiltCandidatePython -m pip check
if ($LASTEXITCODE -ne 0) { throw 'Candidate dependency resolution is inconsistent.' }
& $violiltCandidatePython tools\assemble_pronunciation_notices.py --download-sources
if ($LASTEXITCODE -ne 0) { throw 'Candidate notice/source preparation failed.' }
Write-Output 'Prepared .tmp\pronunciation-env. The baseline environment remains available.'
