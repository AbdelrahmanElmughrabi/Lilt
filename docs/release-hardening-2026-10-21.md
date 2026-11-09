# Violilt release hardening — 21 October 2026

This records the implementation following the read-only security investigation. It is combined with the broader Store/privacy/licensing work in [release readiness](release-readiness.md). The earlier investigation remains a historical baseline.

## Changes and validation

| Step | Trace / implementation | Evidence |
| --- | --- | --- |
| Dependencies | Replaced affected certifi 2026.7.22 with 2026.10.19; hash-pinned pip bootstrap to 26.2.2 before dependency setup; refreshed matching notices/sources. | Environment `pip check` passed; 79 distinct CPU/GPU package/version OSV queries returned no findings; new certifi verified in the payload. |
| Native boundary | Replaced origin-only generic dispatch with an explicit public method/arity contract, bounded message/ID validation and registered async callback checks. File drops still use native File objects. | Unit transport tests reject private/dotted traversal; real frozen app rejects a valid private Store write and a malformed callback ID while public calls work. Normal debug-off native startup and playback passed. |
| Model trust | Independently fetched all three upstream release assets; hashes are reviewed code constants rather than optional remote digests. Readiness, import/download, packaging and inference verify approved bytes. | Existing local and freshly packaged CPU/GPU/voice files match the independent downloads. Tests reject modified model content before ONNX parser creation. |
| Model activation | Stage and verify complete sets; durable transaction journal/backups; rollback on replacement failure; restore interrupted pending changes; stop/coordinate workers for model changes. | Tests preserve an existing usable set after invalid import, roll back a failed second replacement, recover after restart, and retain invalid recovery-journal evidence. |
| Settings and database | Shared typed preferences, schema version 1, verified pre-upgrade SQLite backup, newer-version protection, retained malformed rows and visible recovery notice. | Invalid preferences reject the entire update. Corrupt preference/document fixtures preserve originals and healthy items. Migration/backup failure/newer-schema checks passed. Full record-schema/recovery UX and installed restore rehearsal remain open. |
| Import boundaries | Restrict library copy to managed entries, reject reparse points, lock the source, bound copied bytes/count/depth, check disk space and source snapshots. Bound Markdown and file batches before parsing/storage. | Junction, active-source, changing-source, low-space, copy-cap and legacy migration regressions passed. |

The complete backend suite passed **170 tests in 22.696 seconds**. Svelte/TypeScript check and production frontend build passed. No personal library was opened or migrated; runtime tests used disposable data. Public bundled model files were read for verification. Existing unrelated working-tree changes were retained.

## Fresh artifacts

- [CPU/GPU evaluation executable](C:/Users/fireball/OneDrive/Desktop/LiltTTS/dist/security-hardening-20261021/Violilt/Violilt.exe), with [payload audit](C:/Users/fireball/OneDrive/Desktop/LiltTTS/dist/security-hardening-20261021/Violilt/package-audit.json): 2,334 frozen modules, 1,467 inventoried files, no forbidden module/file findings. In particular, the audit found no active eSpeak/phonemizer path; this is not blanket redistribution clearance.
- [Unsigned MSIX compatibility package 1.0.2.0](C:/Users/fireball/OneDrive/Desktop/LiltTTS/dist/security-msix-20261021/Violilt-MsixCompatibility-1.0.2.0-x64.msix), with [inventory](C:/Users/fireball/OneDrive/Desktop/LiltTTS/dist/security-msix-20261021/inventory-1.0.2.0.json). **Local testing only, not a production Store identity.**

The MSIX is 2,253,679,469 bytes. MakeAppx validated package creation; archive inspection matched the frozen executable hash. Its 1,168 mapped files plus two standard MSIX metadata entries retain CPU and NVIDIA support.

Package SHA-256: `9f72a0da48107be007a86ad649191d1341750557ed86319cb44f2894a33b1221`.

Executable SHA-256: `303d31664524d4e35e58f2ece248ccfeb477ff38c56c6984a8fab8edfb2a8b75`.

Installer `-WhatIf` verified identity/inventory/full-package hash. Installation was not attempted: the unsigned executable package requires an Administrator PowerShell session, and this session is not an administrator. WACK was not found in its checked standard installation directory. No certificates were created/trusted and nothing was installed or published.

## Runtime evidence

The freshly built frozen executable used a disposable library and a temporary debugging connection for instrumentation. It blocked private native dispatch and invalid callback IDs, rejected `voice: null`, generated completed recordings through CPU and CUDA providers, and preserved settings/documents across reload with zero page errors. A separate native startup/playback probe ran with debugging disabled. This does not prove execution under installed MSIX identity or a clean target PC.

Evidence retained under the ignored [.tmp/release-hardening-20261021 directory](C:/Users/fireball/OneDrive/Desktop/LiltTTS/.tmp/release-hardening-20261021):

- [Unit tests](C:/Users/fireball/OneDrive/Desktop/LiltTTS/.tmp/release-hardening-20261021/unittest.log), [advisory query results](C:/Users/fireball/OneDrive/Desktop/LiltTTS/.tmp/release-hardening-20261021/python-advisories.json), [upstream asset hashes](C:/Users/fireball/OneDrive/Desktop/LiltTTS/.tmp/release-hardening-20261021/verified-upstream-models.json).
- [Frozen runtime results](C:/Users/fireball/OneDrive/Desktop/LiltTTS/.tmp/release-hardening-20261021/packaged-results.json), [debug-off native check](C:/Users/fireball/OneDrive/Desktop/LiltTTS/.tmp/release-hardening-20261021/native-startup.log), [payload/source verification](C:/Users/fireball/OneDrive/Desktop/LiltTTS/.tmp/release-hardening-20261021/payload-verification.json), [MSIX verification](C:/Users/fireball/OneDrive/Desktop/LiltTTS/.tmp/release-hardening-20261021/msix-verification.json).
- [Targeted Git-history secret scan](C:/Users/fireball/OneDrive/Desktop/LiltTTS/.tmp/release-hardening-20261021/history-secret-scan.json): all 17 local revisions / 297 unique blobs, zero matches for the selected private-key/AWS/GitHub patterns; not a comprehensive credential audit.

Copy ignored evidence deliberately before workspace cleanup. Package inventories and this document preserve the release-relevant conclusions and artifact hashes.

## Remaining release work

Exact model/voice/dictionary and native redistribution grants, LGPL/MPL replacement/source arrangements, NVIDIA/MS runtime rights, proprietary compilation, final privacy/diagnostic/retention choices and publisher identity are still open. See the [privacy trace](privacy-release-review.md).

Installed CPU/GPU, old-to-new update/recovery, broader malformed-record/restore handling, Windows ACLs, clean-machine compatibility, accessibility, native advisory inventory, malware/WACK checks and final Store submission remain separate gates. Passing the checks above does not clear them.
