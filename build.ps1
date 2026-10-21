param([switch]$IncludeGpu, [string]$ModelDirectory = '.app-data\models', [string]$GpuRuntimeDirectory = '.cuda-probe', [string]$OutputDirectory = 'dist\pronunciation')
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$violiltCandidateDistRoot = if ([IO.Path]::IsPathRooted($OutputDirectory)) { [IO.Path]::GetFullPath($OutputDirectory) } else { [IO.Path]::GetFullPath((Join-Path $PSScriptRoot $OutputDirectory)) }
$violiltAllowedDistRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'dist')) + [IO.Path]::DirectorySeparatorChar
if (!$violiltCandidateDistRoot.StartsWith($violiltAllowedDistRoot, [StringComparison]::OrdinalIgnoreCase)) { throw 'Build output must be a subdirectory of this workspace dist folder.' }
$violiltOutputExecutable = Join-Path $violiltCandidateDistRoot 'Violilt\Violilt.exe'
if (Get-Process -Name Violilt -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $violiltOutputExecutable }) { throw 'This output is running. Close that Violilt copy or choose another -OutputDirectory before building.' }
$violiltCandidatePython = Join-Path $PSScriptRoot '.tmp\pronunciation-env\Scripts\python.exe'
if (!(Test-Path -LiteralPath $violiltCandidatePython)) { throw 'Run setup-pronunciation.ps1 first.' }
$violiltCandidateTemp = Join-Path $PSScriptRoot '.tmp\pronunciation-pip-temp'
New-Item -ItemType Directory -Path $violiltCandidateTemp -Force | Out-Null
$env:TEMP = $violiltCandidateTemp
$env:TMP = $violiltCandidateTemp
$violiltCandidateModelSource = if ([IO.Path]::IsPathRooted($ModelDirectory)) { [IO.Path]::GetFullPath($ModelDirectory) } else { [IO.Path]::GetFullPath((Join-Path $PSScriptRoot $ModelDirectory)) }
$violiltModelCheckArguments = @('tools\verify_models.py', '--directory', $violiltCandidateModelSource)
if ($IncludeGpu) { $violiltModelCheckArguments += '--include-gpu' }
& $violiltCandidatePython @violiltModelCheckArguments
if ($LASTEXITCODE -ne 0) { throw 'Model verification failed before packaging.' }
Push-Location -LiteralPath (Join-Path $PSScriptRoot 'frontend')
try {
    npm.cmd run check
    if ($LASTEXITCODE -ne 0) { throw 'Interface type check failed.' }
    npm.cmd run build
    if ($LASTEXITCODE -ne 0) { throw 'Interface build failed.' }
} finally { Pop-Location }
& $violiltCandidatePython -m PyInstaller --noconfirm --clean --distpath $violiltCandidateDistRoot --workpath build\pronunciation packaging\Violilt.spec
if ($LASTEXITCODE -ne 0) { throw 'Candidate executable packaging failed.' }
$violiltCandidateFolder = Join-Path $violiltCandidateDistRoot 'Violilt'
$violiltCandidateModelSource = if ([IO.Path]::IsPathRooted($ModelDirectory)) { [IO.Path]::GetFullPath($ModelDirectory) } else { [IO.Path]::GetFullPath((Join-Path $PSScriptRoot $ModelDirectory)) }
$violiltCandidateMarker = @{ data_profile = 'Violilt-Pronunciation-Evaluation'; development = $true } | ConvertTo-Json
[IO.File]::WriteAllText((Join-Path $violiltCandidateFolder 'violilt-candidate.json'), $violiltCandidateMarker, (New-Object Text.UTF8Encoding($false)))
$violiltCandidateModels = Join-Path $violiltCandidateFolder 'models'
New-Item -ItemType Directory -Path $violiltCandidateModels -Force | Out-Null
foreach ($violiltModelName in @('kokoro-v1.0.int8.onnx', 'voices-v1.0.bin')) {
    $violiltModelSource = Join-Path $violiltCandidateModelSource $violiltModelName
    if (!(Test-Path -LiteralPath $violiltModelSource)) { throw ('Missing local model: ' + $violiltModelName) }
    Copy-Item -LiteralPath $violiltModelSource -Destination (Join-Path $violiltCandidateModels $violiltModelName) -Force
}
if ($IncludeGpu) {
    $violiltGpuSource = if ([IO.Path]::IsPathRooted($GpuRuntimeDirectory)) { [IO.Path]::GetFullPath($GpuRuntimeDirectory) } else { [IO.Path]::GetFullPath((Join-Path $PSScriptRoot $GpuRuntimeDirectory)) }
    if (!(Test-Path -LiteralPath (Join-Path $violiltGpuSource 'violilt-runtime.json'))) { throw 'Run the real CUDA probe before including the GPU runtime.' }
    $violiltGpuDestination = Join-Path $violiltCandidateFolder 'gpu-runtime'
    New-Item -ItemType Directory -Path $violiltGpuDestination -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $violiltGpuSource 'onnxruntime') -Destination $violiltGpuDestination -Recurse -Force
    # The optional Nvidia portion contains only runtime DLLs and license texts;
    # headers and import/development libraries are deliberately omitted.
    foreach ($violiltGpuFile in Get-ChildItem -LiteralPath (Join-Path $violiltGpuSource 'nvidia') -Recurse -File) {
        if ($violiltGpuFile.Extension -ne '.dll' -and $violiltGpuFile.Name -notmatch '(?i)license|copying|notice|eula') { continue }
        $violiltGpuRelative = $violiltGpuFile.FullName.Substring($violiltGpuSource.Length + 1)
        $violiltGpuTarget = Join-Path $violiltGpuDestination $violiltGpuRelative
        New-Item -ItemType Directory -Path (Split-Path -Parent $violiltGpuTarget) -Force | Out-Null
        Copy-Item -LiteralPath $violiltGpuFile.FullName -Destination $violiltGpuTarget -Force
    }
    Copy-Item -LiteralPath (Join-Path $violiltGpuSource 'violilt-runtime.json') -Destination $violiltGpuDestination -Force
    Get-ChildItem -LiteralPath $violiltGpuSource -Directory | Where-Object { $_.Name -like 'nvidia*.dist-info' -or $_.Name -like 'onnxruntime_gpu*.dist-info' } | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $violiltGpuDestination -Recurse -Force
    }
    Copy-Item -LiteralPath (Join-Path $violiltCandidateModelSource 'kokoro-v1.0.fp16-gpu.onnx') -Destination $violiltCandidateModels -Force
}
& $violiltCandidatePython tools\assemble_pronunciation_notices.py --output (Join-Path $violiltCandidateFolder 'third-party')
if ($LASTEXITCODE -ne 0) { throw 'Candidate notice assembly failed.' }
& $violiltCandidatePython tools\package_pronunciation_audit.py --package $violiltCandidateFolder
if ($LASTEXITCODE -ne 0) { throw 'Candidate package isolation audit failed.' }
$violiltModelCheckArguments = @('tools\verify_models.py', '--directory', $violiltCandidateModels)
if ($IncludeGpu) { $violiltModelCheckArguments += '--include-gpu' }
& $violiltCandidatePython @violiltModelCheckArguments
if ($LASTEXITCODE -ne 0) { throw 'Packaged model verification failed.' }
Write-Output ('Built ' + (Join-Path $violiltCandidateFolder 'Violilt.exe') + '. This is a development evaluation build pending distribution review.')
