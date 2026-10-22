# Violilt Microsoft Store release — handoff

## Current follow-up — all four approved batches completed

Updated 21 October 2026 after the independent verification review. Baseline is
`2b0f4d1c9efeca71eb31f5d9c5c6e48265296aef` (`Changed icon`), following the committed
security work in `72974c8`. The tree was clean before batch 1. The changes
below are **uncommitted**; no commit or push was performed.

The user initially approved these follow-up items, in order: **(1) S-05 saved-data
validation/recovery, (2) packaging verification against actual payload content,
(3) continuation compatibility across branding changes**. After those batches,
the user explicitly approved **(4) GPU runtime loading trust** on 21 October.
The user explicitly waived the separate
working-tree backup requirement. No backup was created, dependencies added or
installed, or personal libraries/real user data opened or modified. Continue one
item per batch and **stop after each batch for the user's go-ahead**.

Batch 1 changes:

- `backend/settings.py`: finite-number checks reject overflowing integers as
  ordinary validation errors. Saved benchmark validation now checks the provider,
  device, descriptions, timings and results consumed by the resolver/UI. Older
  CPU thread-only recommendations remain supported; valid GPU measurements and
  failed benchmark candidates remain usable.
- `backend/storage.py`: validate saved document metadata and supplied job text,
  timing, counts, warnings, options, chunks and audio sections before returning
  records. Invalid records/settings use the existing recovery path: keep raw rows
  and audio, omit damaged records from the normal listing, retain healthy records,
  and expose a recovery notice. Optional metadata missing from older records is
  not filled in or rewritten. Overflow errors are handled by recovery as well.
- `tests/test_recovery.py`: six added regression tests reproduce the review's
  document/job state failures, huge-number settings failures, and malformed
  benchmark acceptance. They check public library state, atomic rejection,
  default/CPU fallback, raw-row/audio preservation, deduplicated recovery notices,
  and valid CPU/GPU benchmark compatibility using disposable fixtures.

Validation used the existing `.tmp/pronunciation-env/Scripts/python.exe`, with
`-B`, `PYTHONDONTWRITEBYTECODE=1` and external `TEMP`/`TMP` paths. No new test
dependency was required. Before changing implementation, all six new tests
collected and failed on the old code; the seven existing recovery tests passed
(13 tests, 32 assertion failures / 9 errors across the failing cases/subtests).
After implementation, the focused recovery suite passed **13/13**, then the full
suite passed **176/176 in 21.477 seconds**. The full run used execution outside
the restricted sandbox so the existing loopback/junction fixtures could run.
`git diff --check` passed. No native app, model inference, build or installed
package was run for this batch; these are source/test results.

Commands: `python -B -m unittest discover -s tests -p test_recovery.py -v` before
and after the fix, followed by `python -B -m unittest discover -s tests -v`.
Logs are outside the project at
`C:\Users\fireball\.codex\visualizations\2026\10\21\01a15fcf-c186-7223-9ac8-b727e17c3402\s05-batch-20261021`
(`before-fix-recovery.log`, `after-fix-recovery.log`, `after-fix-full-suite.log`).

Batch 2 changes (packaging verification):

- `tools/msix_package.py`: verify all three CPU/GPU/voice files against the
  existing size/SHA-256 pins and run the actual executable/package audit before
  publishing a mapping. A previous passing JSON report alone is insufficient.
  Reparse/private-entry checks run before the new audit. Reject unreadable
  archives, forbidden runtime content, and disagreement between audited model
  hashes and verified pins. Compare the mapped file inventory against the audit
  before publishing the mapping/inventory to detect changes during preparation.
- `tools/package_pronunciation_audit.py`: allow callers to obtain a report
  without writing into the payload; existing standalone/default report output is
  preserved. Runtime eSpeak/phonemizer components are rejected in nested paths
  as well as at package roots. Legal source/notice archives remain permitted.
- The input payload is unchanged. A fresh audit is written into staging and
  mapped in place of the old report, with hashes for the actual mapped files,
  including the isolated MSIX marker. The inventory records verified model
  hashes. Production hash constants and the GPU runtime trust policy are
  unchanged; same-source model hashes still do not establish independent
  provenance.
- `tests/test_msix_package.py`: six new regression methods cover changed CPU,
  GPU and voice bytes with a stale passing audit; nested eSpeak/phonemizer files;
  actual PYZ forbidden modules and dormant imports; unreadable executable
  archives; changes after auditing; and fresh staged reporting with byte-for-byte
  preservation of the input. Fixtures use inert files and real disposable
  PyInstaller-format archives, without executing them. Model pins are patched
  only in test memory to match disposable fixture bytes. The already installed
  PyInstaller archive reader/writer is used; no dependency was added/installed.

Batch 2 validation used the same existing Python environment and external
`TEMP`/`TMP` isolation as batch 1. All six new regression methods failed on
assertions against the two original tool implementations loaded from HEAD into
memory using read-only `git show`: **14 tests, 13 assertion failures, zero
errors** across subtests; the eight original tests passed. No project source was
restored or swapped for that counterfactual run. After implementation, the MSIX
and package-audit suites passed **17/17 in 4.155 seconds**; the full suite passed
**182/182 in 25.622 seconds**. The full run used execution outside the restricted
sandbox for existing loopback/junction fixtures. Direct invocation of
`tools/msix_package.py --help` from outside the project passed. `git diff --check`
passed. No real model download, model inference, native DLL execution, portable
rebuild, MakeAppx run or installed-package test was performed for this batch.

Focused command: `python -B -m unittest discover -s tests -p test_msix_package.py
-v`, plus the existing `test_package_audit.py` suite; full command: `python -B -m
unittest discover -s tests -v`. Batch 2 evidence is outside the project at
`C:\Users\fireball\.codex\visualizations\2026\10\21\01a15fcf-c186-7223-9ac8-b727e17c3402\packaging-batch-20261021`
(`run_pre_fix.py`, `before-fix-msix-final.log`, `after-fix-packaging.log`,
`after-fix-full-suite.log`). Earlier intermediate red/green logs remain there.

Batch 3 changes (branding/continuation compatibility):

- `backend/pronunciation.py` and `backend/speech_text.py`: restore the original
  persisted pronunciation, adapter and symbol-policy revision labels. These are
  algorithm identities, independent of the displayed product name. The product
  remains Violilt. Recognize exactly the two historical label sets as equivalent
  only when all other pronunciation identity fields match. Verify the symbol
  digest with its historical policy label; do not discard the digest, accept
  arbitrary brand-prefix replacements, or extend this exception to future
  algorithm revisions.
- `backend/jobs.py`: use that compatibility check for the public continuation
  status and resume gate. Recalculate the model/voice/runtime identity using the
  validated saved pronunciation label, preserving saved snapshots and cache
  keys for both brand histories. Model files, voice data, runtime, original text,
  voice, speed and options still have to match. No saved identity is rewritten.
- `backend/speech.py`: apply the same brand compatibility check in the actual
  worker before extending audio. Runtime-directory loading policy is unchanged.
- `tests/test_continuation_branding.py`: four new tests cover both historical
  brands in interrupted/cancelled/failed states, immutable snapshots and saved
  section bytes, real worker publication/assembly using synthetic samples,
  pre-rebrand cache reuse by new readings, and rejection of changed revisions,
  adapters, fallback rules, asset hashes, symbol digests/revisions, dependency
  versions, mixed brand labels, model/voice inputs and runtime identity.
  Pronunciation distributions and all model/library/audio files are disposable
  fixtures. Engine creation is stubbed; no real TTS model is loaded. The worker
  runs in-process with fixture queues, so this does not verify native app/IPC or
  installed update behavior. `tests/test_pronunciation.py` now asserts the stable
  pre-rebrand algorithm revision in the existing cheap-import test.

Batch 3 validation: all four new methods collected and failed against the
unchanged implementation before fixing it (**4 tests, 8 assertion failures,
zero errors** across subtests). After the fix, the focused suite passed **4/4
in 2.826 seconds**, and the full suite passed **186/186 in 23.684 seconds**,
including the existing pronunciation, symbols, performance, branding and worker
lifecycle tests. Commands were `python -B -m unittest discover -s tests -p
test_continuation_branding.py -v` before/after, then `python -B -m unittest
discover -s tests -v`, with the same environment and external temporary paths as
the earlier batches. The full suite used execution outside the restricted
sandbox for existing loopback/junction fixtures. `git diff --check` passed.
Logs: `C:\Users\fireball\.codex\visualizations\2026\10\21\01a15fcf-c186-7223-9ac8-b727e17c3402\continuation-batch-20261021`
(`before-fix-continuation.log`, `after-fix-continuation.log`,
`after-fix-full-suite.log`).

Batch 4 changes (GPU runtime loading trust):

- `backend/gpu_trust.py` embeds 371 exact path/size/SHA-256 pins and eight wheel
  SHA-256 hashes in application code. All eight existing cached wheels matched
  release-specific PyPI metadata, and all selected existing runtime bytes matched
  those wheel contents. No runtime-supplied manifest can approve code. The source
  and limits are documented in `thirdparty/GPU-RUNTIME-INTEGRITY.md`; PyPI hashes
  from that same distribution source are not independent provenance/signatures.
- `backend/runtime.py`: frozen apps and workers accept only the bundled runtime;
  source runs use `.tmp/pronunciation-gpu-runtime` or a verified development
  override. Check the complete file/directory set, sizes and hashes, and reject
  bytecode and reparse/junction paths before exposing any runtime code. Invalid
  optional selections return no GPU runtime, retaining CPU availability. Every
  worker revalidates its actual argument. Disable bytecode output in activated
  workers. Restrict DLL searches in that process to registered directories and
  System32, retain registrations for deferred loads, and preload CUDA/cuDNN via
  explicit approved absolute paths. No OS-wide policy or PATH change is made.
- `backend/speech.py` activates the verified runtime before runtime imports;
  `backend/performance.py` uses the restricted loader instead of scanning
  arbitrary sys.path entries for NVIDIA folders or invoking fallback DLL search.
  Runtime activation hashes the full 2,911,428,414-byte payload once; a duplicate
  full hash at native preload was removed. Selection in the parent still checks
  content; startup I/O cost has not been comprehensively benchmarked.
- `tools/prepare_gpu_runtime.py` copies only pinned bytes from a source into a
  fresh separate folder, verifies the copied content, and preserves the source.
  Unrelated source packages/bytecode are not copied. Preparation does not assert
  a successful CUDA inference probe. `build.ps1` uses this tool, and the actual
  package audit (therefore existing-payload MSIX preparation) enforces the pins.
  `tools/probe_cuda.py` and `tools/pronunciation_samples.py` activate the verified
  runtime instead of bypassing these loading checks. No dependencies were added,
  installed or upgraded. Existing requirements lock files are unchanged.
- `tests/test_runtime.py` has 11 tests: eight runtime selection/worker regression
  methods, a native-loader regression and two preparation guards. The initial
  eight methods failed on real assertions before implementation (8 tests, 16
  assertion failures, zero errors), including execution of a harmless disposable
  shadow module before old worker validation. The native-loader test failed
  against HEAD's performance implementation loaded into memory with read-only
  git show (1 assertion failure, zero errors). The added MSIX runtime-code/DLL
  mutation test failed against the pre-batch audit (2 assertion failures across
  subtests, zero errors). The two new preparation guards verify new tool behavior;
  no pre-fix regression claim is made for those new interfaces. Runtime/model pins
  in tests are replaced only in memory with hashes for disposable fixtures.

Batch 4 validation used the same existing Python environment, `-B`, bytecode
suppression, and external TEMP/TMP isolation. Focused runtime tests passed 11/11
and MSIX tests passed 15/15. The final full suite passed **198/198 in 27.912
seconds**, using execution outside the restricted sandbox for loopback/junction
fixtures. `git diff --check` and new-file whitespace checks passed. `build.ps1`
passed PowerShell parser validation. Ruff and Pyright executables/modules were
not installed in the checked environment; nothing was installed to run them.
A fresh CPU
process rejected the unprepared override and loaded base ONNX Runtime 1.30.0
with CPU support. A separate, prepared copy of the real approved runtime was
used for Windows DLL loading and ONNX Runtime 1.24.4/CUDA-provider import, with
PATH unchanged. The final native smoke passed in **16.066 seconds**, including
**14.401 seconds** for full verification/activation and **0.161 seconds** for
explicit CUDA/cuDNN preloading. This is one run on this machine, not an app
startup benchmark; parent verification adds further I/O. The first smoke with
duplicate full hashing took about 45 seconds under different cache conditions.
This is real native loading, not a model inference test. No
personal library, real user document or recording was opened or changed.

Batch 4 evidence is outside the project at
`C:\Users\fireball\.codex\visualizations\2026\10\21\01a15fcf-c186-7223-9ac8-b727e17c3402\gpu-trust-batch-20261021`:
`verify_runtime_source.py`, `verified-runtime-source.json`,
`runtime-source-verification.log`, `before-fix-runtime.log`,
`before-fix-runtime-packaging.log`, `run_pre_fix_native.py`,
`before-fix-native-loading.log`, `after-fix-runtime.log`,
`after-fix-runtime-packaging.log`, `after-fix-full-suite.log`,
`prepare-real-runtime.log`, `native_runtime_smoke.py`,
`native-runtime-smoke.log` and `cpu-fallback-smoke.log`.
The 2.9 GB disposable prepared runtime used for native testing was removed after
the successful smoke. The source runtime and cached wheels were preserved; the
preparer and recorded source verification allow recreating the test copy.
For normal source runs, `.tmp/pronunciation-gpu-runtime` was then prepared and
verified from the existing public `.cuda-probe` files (371 pinned files plus the
marker). This ignored development runtime intentionally remains available; it
uses about 2.9 GB. `prepare-development-runtime.log` records the result. No model
or application library data was copied by this preparation.

All current follow-up changes remain **uncommitted**. Stop after batch 4;
every other review/release item remains outside this request. Full restore UX,
broader schema/recovery review and installed update/recovery testing
are still open; batch 1 addresses the reproduced S-05 failures and related field
validation, not universal corruption recovery. Batch 2 validates the bytes during
mapping preparation; it does not make the source directory immutable during a
subsequent MakeAppx run. Runtime byte verification does not establish immutable
directory permissions or eliminate concurrent file-replacement races. A fresh
real package build, installed ACL/DLL-search verification and CPU/GPU inference
in that rebuilt package remain open. Earlier artifact paths and runtime results
below are historical;
no current package containing these batches has been built or verified.

## Earlier release implementation and evidence

Prepared 21 October 2026. **The first security implementation pass is complete and tested; public-release gates remain open.** Resume from the combined checklist rather than restarting the original investigation.

## Workspace and working rules

- Workspace: `C:\Users\fireball\OneDrive\Desktop\LiltTTS`; PowerShell on Windows.
- Branch: `pronunciation-replacement`; current baseline HEAD: `2b0f4d1c9efeca71eb31f5d9c5c6e48265296aef`. The original investigation compared against `c8acbab63643871c59c372b43ae1c6697f8e2904`.
- Rebranding, prior release tooling and the first security pass were committed in `72974c8`; icon/favicon changes followed in `2b0f4d1`. Only the current follow-up changes listed above are uncommitted. Preserve them; do not reset/revert the tree.
- Product name is **Violilt**, although the workspace directory is still LiltTTS. Target: x64 Windows MSIX, local English TTS, CPU **and NVIDIA GPU support in version 1**, proprietary application code and Store-delivered updates.
- Pricing is undecided; the user was leaning toward a free first release. No ads, payments, account service or custom updater were added.
- The user explicitly requested **trace → plan → dive in before each step**. Inspect the current paths/evidence, state the intended change and checks, implement/investigate, validate, and record the result. Do not repeatedly ask for permission for already-authorized reversible work.
- No applicable repository/ancestor AGENTS.md was found during this pass; check for newly introduced instructions when resuming. No subagents were used.
- Personal libraries were not opened, migrated or modified. Runtime tests used disposable data; public local model assets were read. Continue that isolation. Inspect older helper scripts before executing: some default to existing `.app-data` or `artifacts` directories.

## Read first

1. [Combined release readiness and current statuses](C:/Users/fireball/OneDrive/Desktop/LiltTTS/docs/release-readiness.md).
2. [Implemented changes, validation and artifact evidence](C:/Users/fireball/OneDrive/Desktop/LiltTTS/docs/release-hardening-2026-10-21.md).
3. [Privacy trace and remaining decisions](C:/Users/fireball/OneDrive/Desktop/LiltTTS/docs/privacy-release-review.md).
4. [Third-party release review](C:/Users/fireball/OneDrive/Desktop/LiltTTS/thirdparty/PRONUNCIATION-CANDIDATE.md) and [model integrity provenance](C:/Users/fireball/OneDrive/Desktop/LiltTTS/thirdparty/MODEL-INTEGRITY.md).

The [original security investigation](C:/Users/fireball/OneDrive/Desktop/LiltTTS/docs/security-investigation-2026-10-21.md) is a **pre-fix historical baseline**. Its statement that application code was unchanged describes that investigation, not this implementation pass. The initial Store plan/findings also contain dated assumptions and older package evidence. Current compatibility artifact is **1.0.2.0**.

## What was implemented

| Area | Current implementation / files |
| --- | --- |
| S-01 dependencies | certifi **2026.10.19** in [requirements.lock.txt](C:/Users/fireball/OneDrive/Desktop/LiltTTS/requirements.lock.txt). pip **26.2.2** bootstrap is wheel-hash-pinned in [requirements-build.lock.txt](C:/Users/fireball/OneDrive/Desktop/LiltTTS/requirements-build.lock.txt) and installed before application dependencies by [setup-pronunciation.ps1](C:/Users/fireball/OneDrive/Desktop/LiltTTS/setup-pronunciation.ps1). Matching notices/source archives refreshed. |
| S-02 native boundary | [desktop.py](C:/Users/fireball/OneDrive/Desktop/LiltTTS/backend/desktop.py) enforces an exact public method/arity contract, bounded messages, ASCII callback IDs and registered async callbacks before pywebview generic dispatch. Private/dotted traversal and unused generic framework proxies are rejected. Browser-provided origin/navigation checks and native File-object drop transport remain. |
| S-03 model integrity | [model_trust.py](C:/Users/fireball/OneDrive/Desktop/LiltTTS/backend/model_trust.py) pins CPU/GPU/voice sizes and SHA-256 hashes from independently fetched upstream release assets. The upstream API has **no asset digests**. [models.py](C:/Users/fireball/OneDrive/Desktop/LiltTTS/backend/models.py), [performance.py](C:/Users/fireball/OneDrive/Desktop/LiltTTS/backend/performance.py), [verify_models.py](C:/Users/fireball/OneDrive/Desktop/LiltTTS/tools/verify_models.py), the GPU downloader and build script enforce the pins. Unverified bytes fail before inference; invalid optional GPU content leaves CPU usable. |
| S-04 model replacement | Stage/verify complete sets, preserve previous files in a durable journaled transaction, roll back failed replacement, recover pending transactions on restart. Bridge model changes coordinate with generation and worker release. |
| S-05 settings/database | [settings.py](C:/Users/fireball/OneDrive/Desktop/LiltTTS/backend/settings.py) centralizes validation. [storage.py](C:/Users/fireball/OneDrive/Desktop/LiltTTS/backend/storage.py) uses schema version **1**, makes verified pre-upgrade backups, rejects unsupported newer schemas, preserves malformed rows/recovery evidence and keeps healthy records available. Bridge/frontend expose a recovery notice. This is initial recovery support, not a complete restore product. |
| S-06 library copy | Source library lock, managed-entry allowlist, reparse/junction rejection, bounded copying, disk-space checks and before/after source snapshots. Original library data remains available. The source lock may create its housekeeping lock file. |
| Resource limits | Markdown **2 MiB**, file batches **32**, native messages **8 MiB**; library import **100 GiB**, **100,000 entries**, maximum nesting **64**. Limits span [limits.py](C:/Users/fireball/OneDrive/Desktop/LiltTTS/backend/limits.py), bridge, parser, desktop transport and storage. |

New focused tests are in `tests/test_models.py`, `tests/test_recovery.py` and `tests/test_library_import.py`, with desktop/performance/branding regression updates. Earlier per-library process locking and compatibility-profile isolation remain in place.

## Validation already completed

- **170 backend tests passed** in 22.696 seconds; Svelte/TypeScript check and production frontend build passed.
- `pip check` passed. OSV queried **79 distinct CPU/GPU package/version pairs**, with **zero known findings** after updates. This does not clear native DLLs, drivers, CPython or WebView2 against all advisories.
- Real native startup/playback passed with **debugging disabled**: bridge, Home, saved WAV, listening-position recovery and replay.
- The **fresh frozen executable** passed a separate disposable-library check: valid private Store write blocked, malformed callback ID blocked, `voice: null` rejected, real CPU and CUDA recordings completed, settings/documents retained after reload, zero page errors. That check used a temporary debugging connection for instrumentation; it is distinct from the debug-off check.
- Payload audit: **2,334 frozen modules / 1,467 inventoried files**, no forbidden-content findings, no active eSpeak/phonemizer path. All packaged model pins matched independently downloaded upstream bytes. This is not blanket licensing clearance.
- All **80 recorded application/build source files** were unchanged across the build and runtime validation. Payload audit hashes matched after execution; no extra/missing/changed payload files were found.
- Targeted secret scan: all **17 local Git revisions / 297 unique blobs**, no selected private-key/AWS/GitHub pattern hits. It is not a comprehensive credential audit.
- MSIX creation/MakeAppx validation passed. Archive executable hash and installer `-WhatIf` identity/inventory/full-package hash verification passed.

## Exact artifacts and evidence

| Artifact | Location |
| --- | --- |
| CPU/GPU evaluation executable | [Violilt.exe](C:/Users/fireball/OneDrive/Desktop/LiltTTS/dist/security-hardening-20261021/Violilt/Violilt.exe) |
| Frozen payload inventory/audit | [package-audit.json](C:/Users/fireball/OneDrive/Desktop/LiltTTS/dist/security-hardening-20261021/Violilt/package-audit.json) |
| Unsigned local compatibility MSIX | [Violilt-MsixCompatibility-1.0.2.0-x64.msix](C:/Users/fireball/OneDrive/Desktop/LiltTTS/dist/security-msix-20261021/Violilt-MsixCompatibility-1.0.2.0-x64.msix) |
| MSIX inventory | [inventory-1.0.2.0.json](C:/Users/fireball/OneDrive/Desktop/LiltTTS/dist/security-msix-20261021/inventory-1.0.2.0.json) |

MSIX size: **2,253,679,469 bytes**; **1,168 mapped files** plus two standard MSIX metadata entries.

- MSIX SHA-256: `9f72a0da48107be007a86ad649191d1341750557ed86319cb44f2894a33b1221`.
- Executable SHA-256: `303d31664524d4e35e58f2ece248ccfeb477ff38c56c6984a8fab8edfb2a8b75`.

These artifacts use evaluation/compatibility profiles, **not a production Store identity**. [main.py](C:/Users/fireball/OneDrive/Desktop/LiltTTS/main.py) still requires the frozen candidate marker and chooses an allowlisted isolated profile. The compatibility MSIX uses `Violilt.MsixCompatibilityProbe` / `Violilt-MSIX-Compatibility`. Do not submit it to the Store or repoint its tests at personal libraries.

Ignored evidence: [.tmp/release-hardening-20261021](C:/Users/fireball/OneDrive/Desktop/LiltTTS/.tmp/release-hardening-20261021). Important files: `unittest.log`, `python-advisories.json`, `verified-upstream-models.json`, `native-startup.log`, `packaged-results.json`, `payload-verification.json`, `msix-verification.json`, `build-source-hashes.json`, `history-secret-scan.json`, and `final-verification.json`. Reproduction helpers and synthetic libraries are there too. Initial investigation evidence is separately retained under `.tmp/security-20261021`.

**Evidence and built artifacts are ignored/uncommitted. Preserve needed files before cleanup or transferring to another checkout.** The Markdown results and inventory hashes retain the key conclusions.

## Where to resume

1. **Trace the current tree and artifact inventory.** Check for changes since the 80-file build snapshot. Read the combined readiness document; retain completed checks rather than rerunning everything without a relevant change.
2. **Finish exact redistribution/native evidence.** Map actual model conversion, full voice artifact, dictionaries, libsndfile/codecs, Microsoft runtime DLLs and NVIDIA DLL versions to authoritative grants/notices/source arrangements. Existing notices and eSpeak exclusion are partial evidence. Current components include Kokoro v1.0 INT8/FP16, Misaki 0.9.4 without English extras/eSpeak, spaCy model 3.8.0, CPU ORT 1.30.0 and GPU ORT 1.24.4.
3. **Complete privacy/runtime decisions.** Verify actual WebView2 settings and external connections with synthetic data; choose/test diagnostic controls for the shipped parent/worker runtimes. Preserve SmartScreen protections and disclose behavior accurately. Define retention, full-library deletion/export and recovery behavior, including backups/cache/browser data/job text snapshots. The privacy review is not a public policy. Publisher/contact/hosting details are still needed.
4. **Finish security/data scope still open.** Broader persisted-record schema validation, restore UX/rehearsal, native advisory inventory, runtime/install ACLs and GPU override trust, disk-full/cancellation cases, and session-bound audio access need assessment. The confirmed reproductions were addressed; do not label the entire application fully audited.
5. **Prepare production configuration and code protection.** Obtain the real Partner Center identity and finalize production data/profile behavior. Prove the proposed proprietary-module compilation and inspect its output. Current PyInstaller packaging remains inspectable; retain third-party LGPL/MPL source and replacement rights. Do not remove GPU support to bypass work.
6. **Run installed-package and clean-machine gates.** Administrator-capable test environment, CPU/NVIDIA under MSIX identity, worker spawning, dialogs/loopback/WebView2, offline first run, supported Windows/driver/hardware combinations, standard-user permissions, Unicode/space paths, DPI/accessibility, older-to-newer update/recovery and uninstall retention. Then malware/WACK checks and final Store submission preparation.

No verified Partner Center identity/name reservation was supplied. Account/name/MFA/recovery, publisher/support details, pricing/markets and final publication require publisher involvement. Recheck Store policies against the date of submission; the privacy review records the version checked on 21 October.

## Environment limits and useful commands

This session was **not a Windows administrator**. Unsigned executable-MSIX installation requires Administrator PowerShell according to the existing installer helper. WACK was not found in the checked standard location. Installation was not attempted; no certificates were created/trusted and nothing was published. A tool sandbox escalation does not make Windows PowerShell an administrator. No automatic-approval rejection caused these limits.

Run commands from this workspace. The following verification commands use existing artifacts and disposable data:

```powershell
Set-Location -LiteralPath 'C:\Users\fireball\OneDrive\Desktop\LiltTTS'
$handoffTemp = Join-Path (Get-Location) '.tmp\handoff-verification'
New-Item -ItemType Directory -Path $handoffTemp -Force | Out-Null
$env:TEMP = $handoffTemp
$env:TMP = $handoffTemp
& '.tmp\pronunciation-env\Scripts\python.exe' -m unittest discover -s tests -v
& '.tmp\pronunciation-env\Scripts\python.exe' tools\verify_models.py --directory '.app-data\models' --include-gpu
& '.tmp\pronunciation-env\Scripts\python.exe' tools\native-startup-check.py
& '.\tools\install_msix_test.ps1' -PackagePath 'dist\security-msix-20261021\Violilt-MsixCompatibility-1.0.2.0-x64.msix' -WhatIf
```

Backend/native tests may need execution outside the restricted tool sandbox for loopback, IPC or GUI startup. Read/install commands only after tracing their behavior. Choose unused output paths and a new version when rebuilding; retain the exact tested package/inventory together. Any application/dependency change requires relevant tests and a fresh artifact before carrying forward package claims.

The earlier handoff-only turn did not change application behavior. The current
S-05, packaging, continuation and GPU runtime follow-up changes and validation are recorded
at the top of this document.
