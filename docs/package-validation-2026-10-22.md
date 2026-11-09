# Current CPU/GPU package validation — 22 October 2026

The current executable and unsigned local compatibility MSIX were rebuilt from
clean commit `bbe961f4af81046f8ea76ad5fc04124e1a62068a` (`Harden recovery,
packaging, and GPU runtime loading`). Functional validation passed on this
Windows PC. This includes actual speech inference from the new executable and
from the verified MSIX's extracted payload. It does not include installation
under MSIX identity or Store release certification.

No application code, requirements or dependencies changed during validation.
All 150 tracked files matched their pre-build hashes after build and execution;
only this report and HANDOFF.md were updated afterward. No commits/pushes,
package installation, certificate trust changes or personal-library access were
performed. Libraries/documents/audio for tests were disposable synthetic data.
Model inputs came from the earlier public `.verified` release evidence, were
staged separately, and passed the existing approved pins. Those fetches used the
same upstream source as the pins and do not establish independent provenance.

## Artifacts

- [Current executable](C:/Users/fireball/OneDrive/Desktop/LiltTTS/dist/validation-bbe961f-20261022/Violilt/Violilt.exe)
- [Unsigned compatibility MSIX 1.0.3.0](C:/Users/fireball/OneDrive/Desktop/LiltTTS/dist/validation-msix-bbe961f-20261022/Violilt-MsixCompatibility-1.0.3.0-x64.msix)
- [MSIX inventory](C:/Users/fireball/OneDrive/Desktop/LiltTTS/dist/validation-msix-bbe961f-20261022/inventory-1.0.3.0.json)

MSIX size: **2,253,573,807 bytes**. Identity: `Violilt.MsixCompatibilityProbe`, x64.

- Executable SHA-256: `38640646e3f302981e0a749639d29e2ab605984dcc189e297e7eaec99adab63a`
- MSIX SHA-256: `beaab443310cd2f1dc11afa817f14b1839e85647bc8435d30374a87269b88e92`

The MSIX uses the deliberately isolated `Violilt-MSIX-Compatibility` data
profile and a local test publisher. It is unsigned and is not a production Store
package. Existing dist artifacts were preserved; select these explicit paths.

## Checks performed

- Full backend suite: **198 tests passed in 26.056 seconds**.
- Existing Svelte/TypeScript check: **0 errors, 0 warnings**; production frontend
  build passed (6.54 seconds). Existing Python, Node/npm, PyInstaller, Playwright
  and Microsoft-signed SDK tools were used. Nothing was installed.
- `pip check` passed: no broken Python requirements were found.
- Canonical `build.ps1 -IncludeGpu`: passed. CPU INT8, GPU FP16 and voice pins
  passed before/after packaging. GPU preparation copied/verified 371 pinned files.
- Actual executable/package audit: **2,335 frozen modules, 1,146 files, zero
  violations**. The frozen runtime trust module is present. No active forbidden
  eSpeak/phonemizer runtime component or dormant removed-pronunciation import was
  found. Legal notices/source archives can mention inactive optional packages;
  this audit does not establish blanket licensing clearance.
- Native API tests rejected a private/dotted call and an invalid voice setting;
  supported API calls returned successfully through the real native bridge.
- Each run used fresh synthetic reading text with caching disabled. Both CPU
  INT8 and CUDA FP16 generation completed with generated sections and zero cache
  hits. The GPU workers loaded the bundled CUDA provider DLL and appeared in
  `nvidia-smi`'s compute-process list. WDDM reported GPU memory as N/A; no numeric
  GPU-memory claim or per-node ONNX profile is made.
- All five generated WAVs passed direct inspection: mono PCM16, 24 kHz, finite
  nonzero samples and durations matching the jobs. Browser playback decoded and
  advanced, with audio muted. Documents, settings, completed jobs and a saved
  listening position survived closing/restarting each app instance.

| Executable tested | CPU audio | CUDA audio | Playback and restart | GPU add-on behavior |
| --- | --- | --- | --- | --- |
| Fresh portable payload | 8.835 s | 8.963 s | Passed | Unapproved environment override ignored |
| Disposable copy without GPU add-on | 8.856 s | Unavailable as expected | Passed | CPU remained usable with GPU runtime absent |
| Extracted, verified MSIX App payload | 8.835 s | 8.963 s | Passed | Unapproved environment override ignored |

Every native run used `--debug` and a local-only WebView2 CDP connection for test
instrumentation. These are actual frozen-app executions, not source-only or
mock inference tests. Debug-off startup was not separately rerun for this build.
No speaker listening/naturalness assessment was performed.

## MSIX archive validation

MakeAppx creation/manifest validation passed. Every one of the **1,151 mapped files**
matched the inventory's exact size and SHA-256; the ZIP contains **1,153 entries**,
including the two standard package metadata parts. OPC percent-encoded ZIP names
were decoded before comparison with filesystem names. The executable matched the
audited portable executable. All three model pins and all 371 GPU runtime pins
were confirmed inside the MSIX, and its staged marker selected the compatibility
profile. No files were missing or unexpected.

After native tests, all 1,146 original payload files and all 1,151 extracted MSIX
files still matched their inventories, with no added/missing/changed files.
The installer helper's identity/inventory/whole-package SHA-256 check passed with
`-WhatIf`; it did not install anything.

## Findings and limits

1. **Installed-MSIX gate remains open.** This session is not a Windows
   administrator, and the existing unsigned executable-MSIX installer requires
   Administrator PowerShell. Installation was not attempted. Installed CPU/GPU
   behavior, identity-specific worker spawning/WebView/media/file access,
   permissions/ACLs, update/rollback and uninstall retention remain unverified.
2. **Startup/first-audio latency needs controlled profiling.** These instrumented
   runs used fresh WebView profiles, cold loads and some concurrent build work;
   they are functional checks, not a controlled performance benchmark or an
   accepted startup SLA. Worker RSS below is one post-generation sample, not peak
   RAM or total app/browser memory. Harness elapsed times also include post-run
   process inspection and are not pure generation times.

| Run | App startup | First CPU audio | First CUDA audio | Worker RSS after CPU / CUDA |
| --- | --- | --- | --- | --- |
| Portable | 21.25 s | 19.03 s | 21.64 s | 500.6 MiB / 1348.4 MiB |
| GPU add-on omitted | 28.56 s | 12.79 s | — | 501.7 MiB / — |
| Extracted MSIX | 18.90 s | 18.33 s | 17.77 s | 501.3 MiB / 1342.8 MiB |

3. **Low-end/physical no-GPU testing remains open.** Removing the runtime proved
   the CPU fallback path on this NVIDIA-equipped PC. No 2-core/4-GB VM, actual
   low-end PC, physically GPU-less/integrated-only system or clean-machine driver
   environment was tested. GPU capability/driver/hardware compatibility is not
   cleared universally by this one machine.
4. **Build warnings retained.** PyInstaller emitted 413 warnings for deliberately
   excluded upstream spaCy/thinc tests and three other missing hidden imports:
   `pycparser.lextab`, `pycparser.yacctab`, `tzdata`. No failure was observed in the
   exercised startup/speech paths. No dependencies were added to silence them;
   unexercised paths are not thereby verified.
5. **Other release gates remain open.** Store identity/signing/certification,
   licensing/provenance clearance, privacy/traffic review, native advisories,
   actual native file-drop coverage, recovery/update rehearsals and installed
   immutable-directory protection were not broadened or completed in this batch.

No product-code fix was needed for this rebuild. Feature changes should start
as a separate requested batch, preserving this tested source checkpoint.

## Reproduction and evidence

Build commands, with existing dependencies and new output paths:

```powershell
& .tmp/pronunciation-env/Scripts/python.exe -B -m unittest discover -s tests -v
& ./build.ps1 -IncludeGpu -ModelDirectory '<evidence>/models' -GpuRuntimeDirectory '.tmp/pronunciation-gpu-runtime' -OutputDirectory 'dist/validation-bbe961f-20261022'
& ./tools/build_msix.ps1 -CompatibilityTest -PayloadDirectory 'dist/validation-bbe961f-20261022/Violilt' -OutputDirectory 'dist/validation-msix-bbe961f-20261022' -Version '1.0.3.0'
& ./tools/install_msix_test.ps1 -PackagePath 'dist/validation-msix-bbe961f-20261022/Violilt-MsixCompatibility-1.0.3.0-x64.msix' -WhatIf
```

The build's PyInstaller cache was isolated under the evidence directory. Model
staging used only the public `.verified` release assets, not personal library
files. The existing build work directory was checked for reparse points before
allowing normal build cleanup. All test libraries were explicitly separate.

Evidence directory: `C:\Users\fireball\.codex\visualizations\2026\10\21\01a15fcf-c186-7223-9ac8-b727e17c3402\package-validation-20261022-bbe961f`.

Key files: `source-before-build.json`, `source-after-build.json`,
`source-after-execution.json`, `unittest.log`, `build.log`, `build-warnings.json`,
`validate_packaged.cjs`, `observe_worker.py`, `portable/results.json`,
`cpu-only/results.json`, `msix-payload/results.json`, `audio-validation.json`,
`payload-after-execution.json`, `msix-payload-after-execution.json`,
`msix-build.log`, `verify_msix.py`, `msix-verification.json`,
`inspect_audio_and_payload.py`, and `installer-whatif.log`.
Build/fixture artifacts are ignored/outside Git; preserve the exact tested
MSIX/inventory together. Do not repoint helpers at personal libraries.
