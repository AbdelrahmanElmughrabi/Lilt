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
& '.\.venv\Scripts\python.exe' -m PyInstaller --noconfirm packaging\Folio.spec
if ($LASTEXITCODE -ne 0) { throw 'Executable packaging failed.' }
$folioPackagedModels = Join-Path $PSScriptRoot 'dist\Folio\models'
New-Item -ItemType Directory -Path $folioPackagedModels -Force | Out-Null
foreach ($folioModelName in @('kokoro-v1.0.int8.onnx', 'voices-v1.0.bin')) {
    $folioModelSource = Join-Path $PSScriptRoot ('.app-data\models\' + $folioModelName)
    if (Test-Path -LiteralPath $folioModelSource) {
        Copy-Item -LiteralPath $folioModelSource -Destination (Join-Path $folioPackagedModels $folioModelName) -Force
    }
}
$folioShortcutShell = New-Object -ComObject WScript.Shell
$folioShortcut = $folioShortcutShell.CreateShortcut((Join-Path $PSScriptRoot 'Folio.lnk'))
$folioShortcut.TargetPath = Join-Path $PSScriptRoot 'dist\Folio\Folio.exe'
$folioShortcut.WorkingDirectory = Join-Path $PSScriptRoot 'dist\Folio'
$folioShortcut.IconLocation = $folioShortcut.TargetPath + ',0'
$folioShortcut.Description = 'Folio — local Markdown narration'
$folioShortcut.Save()
Write-Output 'Built dist\Folio\Folio.exe. Keep the complete Folio folder together.'
if ($IncludeGpu) {
    $folioGpuSource = Join-Path $PSScriptRoot '.cuda-probe'
    if (!(Test-Path -LiteralPath (Join-Path $folioGpuSource 'folio-runtime.json'))) { throw 'Run the real CUDA probe before including the GPU runtime.' }
    $folioGpuDestination = Join-Path $PSScriptRoot 'dist\Folio\gpu-runtime'
    New-Item -ItemType Directory -Path $folioGpuDestination -Force | Out-Null
    foreach ($folioGpuPart in @('onnxruntime','nvidia','folio-runtime.json')) {
        Copy-Item -LiteralPath (Join-Path $folioGpuSource $folioGpuPart) -Destination $folioGpuDestination -Recurse -Force
    }
    Get-ChildItem -LiteralPath $folioGpuSource -Directory | Where-Object { $_.Name -like 'nvidia*.dist-info' -or $_.Name -like 'onnxruntime_gpu*.dist-info' } | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $folioGpuDestination -Recurse -Force
    }
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot '.app-data\models\kokoro-v1.0.fp16-gpu.onnx') -Destination $folioPackagedModels -Force
    Write-Output 'Included optional NVIDIA runtime. CPU operation also remains available.'
}
