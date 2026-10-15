param([switch]$IncludeGpu, [string]$ModelDirectory = '.app-data\models', [string]$GpuRuntimeDirectory = '.cuda-probe', [string]$OutputDirectory = 'dist\pronunciation')
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$liltCandidateDistRoot = if ([IO.Path]::IsPathRooted($OutputDirectory)) { [IO.Path]::GetFullPath($OutputDirectory) } else { [IO.Path]::GetFullPath((Join-Path $PSScriptRoot $OutputDirectory)) }
$liltAllowedDistRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'dist')) + [IO.Path]::DirectorySeparatorChar
if (!$liltCandidateDistRoot.StartsWith($liltAllowedDistRoot, [StringComparison]::OrdinalIgnoreCase)) { throw 'Build output must be a subdirectory of this workspace dist folder.' }
$liltOutputExecutable = Join-Path $liltCandidateDistRoot 'Lilt\Lilt.exe'
if (Get-Process -Name Lilt -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $liltOutputExecutable }) { throw 'This output is running. Close that Lilt copy or choose another -OutputDirectory before building.' }
$liltCandidatePython = Join-Path $PSScriptRoot '.tmp\pronunciation-env\Scripts\python.exe'
if (!(Test-Path -LiteralPath $liltCandidatePython)) { throw 'Run setup-pronunciation.ps1 first.' }
$liltCandidateTemp = Join-Path $PSScriptRoot '.tmp\pronunciation-pip-temp'
New-Item -ItemType Directory -Path $liltCandidateTemp -Force | Out-Null
$env:TEMP = $liltCandidateTemp
$env:TMP = $liltCandidateTemp
Push-Location -LiteralPath (Join-Path $PSScriptRoot 'frontend')
try {
    npm.cmd run check
    if ($LASTEXITCODE -ne 0) { throw 'Interface type check failed.' }
    npm.cmd run build
    if ($LASTEXITCODE -ne 0) { throw 'Interface build failed.' }
} finally { Pop-Location }
& $liltCandidatePython -m PyInstaller --noconfirm --clean --distpath $liltCandidateDistRoot --workpath build\pronunciation packaging\Lilt.spec
if ($LASTEXITCODE -ne 0) { throw 'Candidate executable packaging failed.' }
$liltCandidateFolder = Join-Path $liltCandidateDistRoot 'Lilt'
$liltCandidateModelSource = if ([IO.Path]::IsPathRooted($ModelDirectory)) { [IO.Path]::GetFullPath($ModelDirectory) } else { [IO.Path]::GetFullPath((Join-Path $PSScriptRoot $ModelDirectory)) }
$liltCandidateMarker = @{ data_profile = 'Lilt-Pronunciation-Evaluation'; development = $true } | ConvertTo-Json
[IO.File]::WriteAllText((Join-Path $liltCandidateFolder 'lilt-candidate.json'), $liltCandidateMarker, (New-Object Text.UTF8Encoding($false)))
$liltCandidateModels = Join-Path $liltCandidateFolder 'models'
New-Item -ItemType Directory -Path $liltCandidateModels -Force | Out-Null
foreach ($liltModelName in @('kokoro-v1.0.int8.onnx', 'voices-v1.0.bin')) {
    $liltModelSource = Join-Path $liltCandidateModelSource $liltModelName
    if (!(Test-Path -LiteralPath $liltModelSource)) { throw ('Missing local model: ' + $liltModelName) }
    Copy-Item -LiteralPath $liltModelSource -Destination (Join-Path $liltCandidateModels $liltModelName) -Force
}
if ($IncludeGpu) {
    $liltGpuSource = if ([IO.Path]::IsPathRooted($GpuRuntimeDirectory)) { [IO.Path]::GetFullPath($GpuRuntimeDirectory) } else { [IO.Path]::GetFullPath((Join-Path $PSScriptRoot $GpuRuntimeDirectory)) }
    if (!(Test-Path -LiteralPath (Join-Path $liltGpuSource 'lilt-runtime.json'))) { throw 'Run the real CUDA probe before including the GPU runtime.' }
    $liltGpuDestination = Join-Path $liltCandidateFolder 'gpu-runtime'
    New-Item -ItemType Directory -Path $liltGpuDestination -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $liltGpuSource 'onnxruntime') -Destination $liltGpuDestination -Recurse -Force
    # The optional Nvidia portion contains only runtime DLLs and license texts;
    # headers and import/development libraries are deliberately omitted.
    foreach ($liltGpuFile in Get-ChildItem -LiteralPath (Join-Path $liltGpuSource 'nvidia') -Recurse -File) {
        if ($liltGpuFile.Extension -ne '.dll' -and $liltGpuFile.Name -notmatch '(?i)license|copying|notice|eula') { continue }
        $liltGpuRelative = $liltGpuFile.FullName.Substring($liltGpuSource.Length + 1)
        $liltGpuTarget = Join-Path $liltGpuDestination $liltGpuRelative
        New-Item -ItemType Directory -Path (Split-Path -Parent $liltGpuTarget) -Force | Out-Null
        Copy-Item -LiteralPath $liltGpuFile.FullName -Destination $liltGpuTarget -Force
    }
    Copy-Item -LiteralPath (Join-Path $liltGpuSource 'lilt-runtime.json') -Destination $liltGpuDestination -Force
    Get-ChildItem -LiteralPath $liltGpuSource -Directory | Where-Object { $_.Name -like 'nvidia*.dist-info' -or $_.Name -like 'onnxruntime_gpu*.dist-info' } | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $liltGpuDestination -Recurse -Force
    }
    Copy-Item -LiteralPath (Join-Path $liltCandidateModelSource 'kokoro-v1.0.fp16-gpu.onnx') -Destination $liltCandidateModels -Force
}
& $liltCandidatePython tools\assemble_pronunciation_notices.py --output (Join-Path $liltCandidateFolder 'third-party')
if ($LASTEXITCODE -ne 0) { throw 'Candidate notice assembly failed.' }
& $liltCandidatePython tools\package_pronunciation_audit.py --package $liltCandidateFolder
if ($LASTEXITCODE -ne 0) { throw 'Candidate package isolation audit failed.' }
Write-Output ('Built ' + (Join-Path $liltCandidateFolder 'Lilt.exe') + '. This is a development evaluation build pending distribution review.')
