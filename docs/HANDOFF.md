# Violilt Microsoft Store release — handoff

Prepared 21 October 2026. **The first security implementation pass is complete and tested; public-release gates remain open.** Resume from the combined checklist rather than restarting the original investigation.

## Workspace and working rules

- Workspace: `C:\Users\fireball\OneDrive\Desktop\LiltTTS`; PowerShell on Windows.
- Branch: `pronunciation-replacement`; HEAD: `c8acbab63643871c59c372b43ae1c6697f8e2904`.
- The working tree contains substantial **uncommitted** rebranding, prior release tooling and security changes. No commit was created for this pass. Preserve existing changes; do not reset/revert the tree or infer that every diff belongs to this security work.
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

Only this handoff and its checklist link were added in the handoff turn; application behavior was not changed.
