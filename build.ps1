param([switch]$IncludeGpu)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
Push-Location -LiteralPath (Join-Path $PSScriptRoot 'frontend')
try {
    npm.cmd run check
    if ($LASTEXITCODE -ne 0) { throw 'Interface type check failed.' }
    npm.cmd run build
    if ($LASTEXITCODE -ne 0) { throw 'Interface build failed.' }
} finally { Pop-Location }
& '.\.venv\Scripts\python.exe' -m PyInstaller --noconfirm packaging\Lilt.spec
if ($LASTEXITCODE -ne 0) { throw 'Executable packaging failed.' }
$liltPackagedModels = Join-Path $PSScriptRoot 'dist\Lilt\models'
New-Item -ItemType Directory -Path $liltPackagedModels -Force | Out-Null
foreach ($liltModelName in @('kokoro-v1.0.int8.onnx', 'voices-v1.0.bin')) {
    $liltModelSource = Join-Path $PSScriptRoot ('.app-data\models\' + $liltModelName)
    if (Test-Path -LiteralPath $liltModelSource) {
        Copy-Item -LiteralPath $liltModelSource -Destination (Join-Path $liltPackagedModels $liltModelName) -Force
    }
}
$liltShortcutShell = New-Object -ComObject WScript.Shell
$liltShortcut = $liltShortcutShell.CreateShortcut((Join-Path $PSScriptRoot 'Lilt.lnk'))
$liltShortcut.TargetPath = Join-Path $PSScriptRoot 'dist\Lilt\Lilt.exe'
$liltShortcut.WorkingDirectory = Join-Path $PSScriptRoot 'dist\Lilt'
$liltShortcut.IconLocation = $liltShortcut.TargetPath + ',0'
$liltShortcut.Description = 'Lilt — local Markdown narration'
$liltShortcut.Save()
Write-Output 'Built dist\Lilt\Lilt.exe. Keep the complete Lilt folder together.'
if ($IncludeGpu) {
    $liltGpuSource = Join-Path $PSScriptRoot '.cuda-probe'
    if (!(Test-Path -LiteralPath (Join-Path $liltGpuSource 'lilt-runtime.json'))) { throw 'Run the real CUDA probe before including the GPU runtime.' }
    $liltGpuDestination = Join-Path $PSScriptRoot 'dist\Lilt\gpu-runtime'
    New-Item -ItemType Directory -Path $liltGpuDestination -Force | Out-Null
    foreach ($liltGpuPart in @('onnxruntime','nvidia','lilt-runtime.json')) {
        Copy-Item -LiteralPath (Join-Path $liltGpuSource $liltGpuPart) -Destination $liltGpuDestination -Recurse -Force
    }
    Get-ChildItem -LiteralPath $liltGpuSource -Directory | Where-Object { $_.Name -like 'nvidia*.dist-info' -or $_.Name -like 'onnxruntime_gpu*.dist-info' } | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $liltGpuDestination -Recurse -Force
    }
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot '.app-data\models\kokoro-v1.0.fp16-gpu.onnx') -Destination $liltPackagedModels -Force
    Write-Output 'Included optional NVIDIA runtime. CPU operation also remains available.'
}
