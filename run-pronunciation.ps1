param([string]$DataDirectory = '.tmp\pronunciation-eval\data')
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$liltEvaluationPython = Join-Path $PSScriptRoot '.tmp\pronunciation-env\Scripts\python.exe'
if (!(Test-Path -LiteralPath $liltEvaluationPython)) { throw 'Run setup-pronunciation.ps1 first.' }
$liltEvaluationData = if ([IO.Path]::IsPathRooted($DataDirectory)) { [IO.Path]::GetFullPath($DataDirectory) } else { [IO.Path]::GetFullPath((Join-Path $PSScriptRoot $DataDirectory)) }
$liltEvaluationModels = Join-Path $liltEvaluationData 'models'
New-Item -ItemType Directory -Path $liltEvaluationModels -Force | Out-Null
foreach ($liltEvaluationName in @('kokoro-v1.0.int8.onnx', 'voices-v1.0.bin', 'kokoro-v1.0.fp16-gpu.onnx')) {
    $liltEvaluationTarget = Join-Path $liltEvaluationModels $liltEvaluationName
    $liltEvaluationSource = Join-Path $PSScriptRoot ('.app-data\models\' + $liltEvaluationName)
    if (!(Test-Path -LiteralPath $liltEvaluationTarget) -and (Test-Path -LiteralPath $liltEvaluationSource)) {
        Copy-Item -LiteralPath $liltEvaluationSource -Destination $liltEvaluationTarget
    }
}
& $liltEvaluationPython -B -X utf8 main.py --data-dir $liltEvaluationData
exit $LASTEXITCODE
