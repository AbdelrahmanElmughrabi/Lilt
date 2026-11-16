# Optional NVIDIA runtime: notices and governing-term references

This schedule identifies the retained runtime and the proposed governing basis.
It does not record the publisher's contract acceptance, grant new permissions or
supersede supplier wheel texts. Complete wheel licenses remain with the runtime.
Publisher adoption and actual recipient agreement remain separate release gates.

| Runtime | Version | Preserved supplied license relative to the application folder |
| --- | --- | --- |
| cuBLAS / cuBLASLt / nvBLAS | 12.9.2.10 | `gpu-runtime/nvidia_cublas_cu12-12.9.2.10.dist-info/licenses/License.txt` |
| CUDA runtime | 12.9.79 | `gpu-runtime/nvidia_cuda_runtime_cu12-12.9.79.dist-info/licenses/License.txt` |
| NVRTC / ordinary builtins | 12.9.86 | `gpu-runtime/nvidia_cuda_nvrtc_cu12-12.9.86.dist-info/licenses/License.txt` |
| cuFFT / cuFFTW | 11.4.1.4 | `gpu-runtime/nvidia_cufft_cu12-11.4.1.4.dist-info/licenses/License.txt` |
| cuRAND | 10.3.10.19 | `gpu-runtime/nvidia_curand_cu12-10.3.10.19.dist-info/License.txt` |
| cuDNN runtime DLLs | 9.27.0.42 | `gpu-runtime/nvidia_cudnn_cu12-9.27.0.42.dist-info/licenses/License.txt` |
| nvJitLink | 12.9.86 | `gpu-runtime/nvidia_nvjitlink_cu12-12.9.86.dist-info/licenses/License.txt` |

Versioned supplementary references accompany the notices in `native/`:

- `NVIDIA-CUDA-12.9.2-terms.txt`: complete readable capture of the official
  [CUDA 12.9.2 agreement](https://docs.nvidia.com/cuda/archive/12.9.2/eula/index.html).
  Sections 1.1.1–1.1.2 and CUDA Attachment A support conditional application
  redistribution; the supplement scopes SDK use to NVIDIA-GPU systems.
- `NVIDIA-cuDNN-9.27-terms.txt`: complete readable capture of the official
  [cuDNN 9.27 agreement and supplement](https://docs.nvidia.com/deeplearning/cudnn/backend/v9.27.0/reference/eula.html).
  Its Distribution provision lists runtime `.dll`/`.so` files. The wheel's older
  January 2020 supplement names cuDNN7; it remains preserved. The version-specific
  cuDNN9 route must be the publisher's actual applicable adopted basis.
- `NVIDIA-nvJitLink-LICENSE.txt`: complete direct NVIDIA
  [libnvjitlink redistribution license](https://developer.download.nvidia.com/compute/cuda/redist/libnvjitlink/LICENSE.txt).
  Together with CUDA 12.9.2 Attachment A, this supports the supplier-named
  `nvJitLink_120_0.dll` family; the older wheel attachment omission remains recorded.

Retaining the exact official-wheel `nvrtc64_120_0.alt.dll` (SHA-256
`ac56a4d3b5a99f294523abec28b8f648b96324a9277622a450ec20ddb9e2c47d`)
uses the independently accepted, bounded NVRTC-family inference. The agreement
does not expressly define the `.alt` suffix. This is not a blanket filename
waiver, an assertion that alternate builtins are supplied, or a promise that all
NVIDIA architectures or deferred engine paths work.

Recipient terms must preserve application-only access, supplier protections and
notices without restricting separately licensed LGPL/MPL rights. The publisher
must also fulfill its own supplier obligations. These references do not turn
the bundled runtime into a standalone SDK distribution or imply endorsement.
Review the applicable full terms, including restrictions, export rules, warranty/
liability limits, termination, enforcement and indemnity provisions. If actual
acquisition supplies materially different terms, reconcile that specific change.
