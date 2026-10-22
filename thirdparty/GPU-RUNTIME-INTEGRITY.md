# GPU runtime integrity

Recorded 21 October 2026. The approved Windows x64 runtime is ONNX Runtime GPU
1.24.4 with the seven NVIDIA packages already listed in requirements-gpu.lock.txt.
No package was installed or upgraded for this change.

`backend/gpu_trust.py` contains 371 exact path/size/SHA-256 pins (2,911,428,414
bytes) and eight wheel SHA-256 hashes. This module is application code and is
collected into the frozen executable. No manifest supplied by a selectable
runtime folder can add approved files or change these pins.

The existing cached wheel archives were hashed in full and compared with the
release-specific PyPI JSON metadata below. Selected files were streamed from
those verified archives, hashed, and compared with the existing `.cuda-probe`
files. All selected bytes matched. Pins cover the ONNX Python/native payload,
NVIDIA runtime DLLs and legal notices, and selected original wheel metadata.
Installed RECORD/INSTALLER/REQUESTED files, bytecode, unrelated packages, headers
and development libraries are excluded. License texts retained here do not
settle all redistribution obligations.

| Wheel | PyPI SHA-256 |
| --- | --- |
| [nvidia_cublas_cu12-12.9.2.10-py3-none-win_amd64.whl](https://pypi.org/pypi/nvidia-cublas-cu12/12.9.2.10/json) | `623f43027d40d44ceadf0043f002bd25cf353e8f13ce90b9a87057019f560661` |
| [nvidia_cuda_nvrtc_cu12-12.9.86-py3-none-win_amd64.whl](https://pypi.org/pypi/nvidia-cuda-nvrtc-cu12/12.9.86/json) | `72972ebdcf504d69462d3bcd67e7b81edd25d0fb85a2c46d3ea3517666636349` |
| [nvidia_cuda_runtime_cu12-12.9.79-py3-none-win_amd64.whl](https://pypi.org/pypi/nvidia-cuda-runtime-cu12/12.9.79/json) | `8e018af8fa02363876860388bd10ccb89eb9ab8fb0aa749aaf58430a9f7c4891` |
| [nvidia_cudnn_cu12-9.27.0.42-py3-none-win_amd64.whl](https://pypi.org/pypi/nvidia-cudnn-cu12/9.27.0.42/json) | `06e9b0026f3bad97d2b58666330fabec04fe1672f776661ecb0ce0029c27f142` |
| [nvidia_cufft_cu12-11.4.1.4-py3-none-win_amd64.whl](https://pypi.org/pypi/nvidia-cufft-cu12/11.4.1.4/json) | `8e5bfaac795e93f80611f807d42844e8e27e340e0cde270dcb6c65386d795b80` |
| [nvidia_curand_cu12-10.3.10.19-py3-none-win_amd64.whl](https://pypi.org/pypi/nvidia-curand-cu12/10.3.10.19/json) | `e8129e6ac40dc123bd948e33d3e11b4aa617d87a583fa2f21b3210e90c743cde` |
| [nvidia_nvjitlink_cu12-12.9.86-py3-none-win_amd64.whl](https://pypi.org/pypi/nvidia-nvjitlink-cu12/12.9.86/json) | `cc6fcec260ca843c10e34c936921a1c426b351753587fdd638e8cff7b16bb9db` |
| [onnxruntime_gpu-1.24.4-cp312-cp312-win_amd64.whl](https://pypi.org/pypi/onnxruntime-gpu/1.24.4/json) | `da5c1e327d8e119a831be2790e69f93cf6daab9145ed0aca7577f412a620f709` |

These hashes come from the same PyPI distribution source as the wheel bytes.
They establish pinned integrity against that source, not independent provenance.
No separately signed Microsoft/NVIDIA attestation was verified. Vendor signatures
or independently published checksums/attestations for these exact wheels or
binaries could provide additional corroboration; matching filenames cannot.

## Loading and preparation

The packaged app ignores VIOLILT_GPU_RUNTIME and selects only its sibling
`gpu-runtime` folder. Source runs default to `.tmp/pronunciation-gpu-runtime`;
a development override must pass exactly the same content verification. Invalid
optional runtimes leave CPU mode available. Each worker rechecks its actual
argument before adding a search path or importing runtime code. Unexpected
files/directories, bytecode, links/junctions and any missing/changed pin are
rejected. Bytecode writing is disabled for the activated worker.

DLL directories are registered only from the verified runtime. The voice/helper
process's default DLL search is restricted to registered directories and System32.
CUDA/cuDNN
preloading uses pinned absolute paths with Windows DLL-load-directory,
registered-directory and System32 search flags, without PATH/current-directory
fallback. Runtime metadata is descriptive, not authority to approve code.
Preparing files does not claim a successful GPU inference probe.

Use the existing Python environment to prepare a *new* folder without installing
anything or changing the source:

```powershell
& '.tmp/pronunciation-env/Scripts/python.exe' -B tools/prepare_gpu_runtime.py --source '.cuda-probe' --output '.tmp/pronunciation-gpu-runtime'
& '.tmp/pronunciation-env/Scripts/python.exe' -B tools/prepare_gpu_runtime.py --verify '.tmp/pronunciation-gpu-runtime'
```

`build.ps1 -IncludeGpu` uses this preparer. It copies only approved bytes,
retains the pinned notices, rejects an existing output runtime, and fails if any
source file differs. The executable/package audit and existing-payload MSIX
preparation also enforce these pins. Updated probe/sample helpers activate the
verified runtime before using CUDA. Unrelated developer experiments that load
other runtimes explicitly are not part of the shipped loading boundary.

## Limits

A current portable/MSIX rebuild, installed permissions/ACL inspection and actual
CPU/GPU inference in that rebuilt package remain required release checks.
Verification is of bytes at check time. It does not establish immutable directory
permissions or prevent an attacker with concurrent write access from racing a
later read/load; installed package protection and final DLL search behavior must
be checked under the real MSIX identity. It cannot protect an application whose
own executable/trust code can be replaced. No native advisory or broad license
clearance is implied by accepting these exact versions.
