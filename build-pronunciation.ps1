# Compatibility entry point; canonical build uses only this branch's dependencies.
param([switch]$IncludeGpu, [string]$ModelDirectory = '.app-data\models', [string]$GpuRuntimeDirectory = '.cuda-probe', [string]$OutputDirectory = 'dist\pronunciation')
& (Join-Path $PSScriptRoot 'build.ps1') -IncludeGpu:$IncludeGpu -ModelDirectory $ModelDirectory -GpuRuntimeDirectory $GpuRuntimeDirectory -OutputDirectory $OutputDirectory
