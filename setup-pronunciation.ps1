param([string]$BootstrapPython = '', [string]$EnvironmentDirectory = '')
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$violiltReleasePolicy = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'packaging\release-runtime.json') | ConvertFrom-Json
if (!$BootstrapPython) { $BootstrapPython = Join-Path $PSScriptRoot ($violiltReleasePolicy.runtime_directory + '/python.exe') }
if (!$EnvironmentDirectory) { $EnvironmentDirectory = $violiltReleasePolicy.environment_directory }
$violiltEnvironmentRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot $EnvironmentDirectory))
$violiltIsolatedRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '.tmp')) + [IO.Path]::DirectorySeparatorChar
if (!$violiltEnvironmentRoot.StartsWith($violiltIsolatedRoot, [StringComparison]::OrdinalIgnoreCase)) { throw 'Use an isolated environment inside this workspace .tmp.' }
if (!(Test-Path -LiteralPath $BootstrapPython)) { throw 'Prepare the pinned runtime with tools/prepare_release_runtime.py first, or supply its exact interpreter using -BootstrapPython.' }
& $BootstrapPython -B tools\verify_release_runtime.py
if ($LASTEXITCODE -ne 0) { throw 'Bootstrap interpreter is not the selected release runtime. The old environment has not been modified.' }
$violiltCandidateTemp = Join-Path $PSScriptRoot '.tmp\release-pip-temp'
New-Item -ItemType Directory -Path $violiltCandidateTemp -Force | Out-Null
$env:TEMP = $violiltCandidateTemp
$env:TMP = $violiltCandidateTemp
$violiltCandidatePython = Join-Path $violiltEnvironmentRoot 'Scripts\python.exe'
if (!(Test-Path -LiteralPath $violiltCandidatePython)) {
    & $BootstrapPython -B -m venv $violiltEnvironmentRoot
    if ($LASTEXITCODE -ne 0) { throw 'Candidate environment creation failed.' }
}
& $violiltCandidatePython -B tools\verify_release_runtime.py
if ($LASTEXITCODE -ne 0) { throw 'Existing environment uses a different runtime; choose a new isolated -EnvironmentDirectory.' }
& $violiltCandidatePython -m ensurepip --upgrade
if ($LASTEXITCODE -ne 0) { throw 'Candidate pip preparation failed.' }
& $violiltCandidatePython -m pip install --require-hashes --only-binary=:all: --cache-dir (Join-Path $PSScriptRoot '.pip-cache') -r requirements-build.lock.txt
if ($LASTEXITCODE -ne 0) { throw 'Pinned build-tool preparation failed.' }
& $violiltCandidatePython -m pip install --cache-dir (Join-Path $PSScriptRoot '.pip-cache') -r requirements.lock.txt
if ($LASTEXITCODE -ne 0) { throw 'Candidate dependency installation failed.' }
& $violiltCandidatePython -m pip check
if ($LASTEXITCODE -ne 0) { throw 'Candidate dependency resolution is inconsistent.' }
$violiltFrontendDependencies = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot $violiltReleasePolicy.frontend_directory))
if (!$violiltFrontendDependencies.StartsWith($violiltIsolatedRoot, [StringComparison]::OrdinalIgnoreCase)) { throw 'Use isolated frontend dependencies inside this workspace .tmp.' }
New-Item -ItemType Directory -Path $violiltFrontendDependencies -Force | Out-Null
foreach ($violiltFrontendPin in @('package.json', 'package-lock.json')) {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot ('frontend/' + $violiltFrontendPin)) -Destination (Join-Path $violiltFrontendDependencies $violiltFrontendPin) -Force
}
& npm.cmd ci --prefix $violiltFrontendDependencies --ignore-scripts --no-audit --no-fund
if ($LASTEXITCODE -ne 0) { throw 'Isolated locked frontend installation failed.' }
& $violiltCandidatePython -B tools\assemble_pronunciation_notices.py --download-sources --frontend-directory $violiltFrontendDependencies --output (Join-Path $violiltEnvironmentRoot '..\notices')
if ($LASTEXITCODE -ne 0) { throw 'Candidate notice/source preparation failed.' }
Write-Output ('Prepared ' + $violiltEnvironmentRoot + '. The prior environment and frontend/node_modules remain available.')
