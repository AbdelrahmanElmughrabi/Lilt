param([string]$DataDirectory = '.tmp\pronunciation-eval\data')
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$violiltEvaluationPython = Join-Path $PSScriptRoot '.tmp\pronunciation-env\Scripts\python.exe'
if (!(Test-Path -LiteralPath $violiltEvaluationPython)) { throw 'Run setup-pronunciation.ps1 first.' }
$violiltEvaluationData = if ([IO.Path]::IsPathRooted($DataDirectory)) { [IO.Path]::GetFullPath($DataDirectory) } else { [IO.Path]::GetFullPath((Join-Path $PSScriptRoot $DataDirectory)) }
$violiltEvaluationModels = Join-Path $violiltEvaluationData 'models'
New-Item -ItemType Directory -Path $violiltEvaluationModels -Force | Out-Null
foreach ($violiltEvaluationName in @('kokoro-v1.0.int8.onnx', 'voices-v1.0.bin', 'kokoro-v1.0.fp16-gpu.onnx')) {
    $violiltEvaluationTarget = Join-Path $violiltEvaluationModels $violiltEvaluationName
    $violiltEvaluationSource = Join-Path $PSScriptRoot ('.app-data\models\' + $violiltEvaluationName)
    if (!(Test-Path -LiteralPath $violiltEvaluationTarget) -and (Test-Path -LiteralPath $violiltEvaluationSource)) {
        Copy-Item -LiteralPath $violiltEvaluationSource -Destination $violiltEvaluationTarget
    }
}
& $violiltEvaluationPython -B -X utf8 main.py --data-dir $violiltEvaluationData
exit $LASTEXITCODE
