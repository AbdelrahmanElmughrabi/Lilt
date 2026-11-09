# R-03 independent review reconciliation and next fix batches

22 October 2026. The publisher supplied the [independent R-03 report](../.tmp/r03-independent-20261022-b019f803/review.md). It **passes the scoped investigation**, while leaving remediation, exact native coverage and release approval open. This accepts the investigation's evidence/limits, not the application for release. The original R-03 result/prompt/manifest remain unchanged as reviewed inputs.

This turn read/reconciled the review, traced relevant current consumers and checked the additional primary Expat reference. It did not apply product fixes, install dependencies, execute new app probes or repeat application suites. Existing counts are reviewer/implementation evidence for their recorded snapshots. Backup waiver remains unchanged.

## R-03 disposition

| Item | Recorded independent outcome | Next action |
| --- | --- | --- |
| R03-F01 runtime/OpenSSL/Expat | Must resolve before release; current version/reachability claims supported. A component-specific supported patch/non-applicability disposition can resolve a finding; blindly upgrading every library is not required. | Prepare a trusted isolated Windows runtime evaluation with explicit interpreter, OpenSSL, Expat and ABI acceptance. Installation remains outside current authorization. |
| R03-F02 stored/imported native audio parsing | Must resolve before release; independent probes additionally confirmed that published_sections and cache.fetch accept/copy renamed AIFF. Exact Windows x64 exploitation was not demonstrated. | Narrow all stored-audio reads before native autodetection, preserve valid audio/data and test recovery/resume/cache/assembly/delivery. See source plan below. |
| R03-F04 native/final payload | Must complete relevant coverage before release; component tags and package metadata are not a measured final binary SBOM. | Continue exact provenance with R-04; repeat applicable inventory/advisory checks against final submission bytes in R-06/R-07/R-08. |
| R03-F03 DOMPurify | Should fix before release; current affected configurations absent, no current-config bypass demonstrated. | Plan a coordinated dependency/lock/build update to at least the reviewed patched release, with existing restrictions retained. No install/update performed. Deferral requires an explicit evidence-based rationale. |
| V03-01 Expat 2.9.0 completeness | Should resolve before accepting a replacement runtime. | Explicitly assess both additional CVEs, actual architecture and wrapper/call paths; do not stop at the older 2.8.4/2.8.5 examples. |

The [Expat maintainer announcement, 5 October 2026](https://blog.hartwork.org/posts/expat-2-9-0-released/) identifies **CVE-2026-77214** (XML_ParseBuffer length validation/potential out-of-bounds read) and **CVE-2026-102633** (integer overflow affecting 32-bit platforms). The latter must not automatically be assigned to the x64 interpreter. For the former, trace actual wrapper use and compiled patches. The acceptance requirement is adequate supported fixes or justified dispositions, not a literal 2.9.0 version label without provenance. A Python version upgrade alone does not prove which Expat/OpenSSL patches its Windows build contains.

## Related R-02 review discovered through the supplied report

The R-03 review explicitly links [R-02 independent findings](../.tmp/r02-independent-20261022-3d986790/review.md). Those are read and recorded separately; R-03's pass does not accept R-02. Its overall verdict is **needs fixes**:

- **V-02-01, P2, must fix:** parent cache initialization/status failure can prevent opening a healthy library or completing normal close even after the text is durable. Worker-only cache handling is insufficient. Current `Jobs.__init__` constructs the cache unconditionally; `cache_state()` directly scans it; Bridge state refresh depends on that result.
- **V-02-02, P2, should fix:** R-02's retained job snapshot can recreate a successfully removed failed recording on retry. This is introduced by this implementation's persistence queue. Removal and pending-write cancellation must be coordinated under the existing job lock, preserving the pending state when deletion itself fails.
- **V-02-03, P3 tooling, should fix before final validation:** the CDP helper records observation errors but unconditionally sets success. Current saved/independent observations were inspected and did pass, so this finding does not erase them or prove a navigation bypass. Future automated acceptance must require valid observations.
- The prior R-01 native-destroy failure modal polish is listed as P3/can follow after release; keep it separate from the essential parent-cache/save-completion boundary.

These findings were read and traced here, not independently reproduced again. The reviewer records real-listener deletion/retry and native cache/close evidence; inspect those saved proofs before implementation. Do not silently count its 281/15/six reruns as new runs by this chat.

## Recommended sequence and acceptance

### Batch 1 — R-02 review fixes, without dependency changes

Address the existing parent-cache, removal/retry and helper-acceptance gaps first, in a new reviewed revision:

1. Make optional parent cache initialization/status/clear failure degrade independently of healthy library/edit/save operations. A cache-disabled/unavailable library must open; state remains useful; errors are reported truthfully. A transient optional refresh failure must not declare a durable document save failed or block normal close.
2. Coordinate pending-job persistence and removal. A successful deletion cannot be upserted later, including natural listener retry. A failed deletion must not silently drop unsaved metadata. Retain existing audio-delete choice and unrelated active jobs.
3. Require the navigation helper's necessary observations, URL/document marker and runtime values; report errors and exit nonzero when acceptance cannot be established. Preserve harmless cancellation behavior and never close the owned native app from CDP cleanup.

Reproduce each review trigger with disposable fixtures before edits. Cover startup/cache disabled, status scan/close recovery, terminal pending state/removal ordering with real listener, deletion failures/audio choices and deliberately failed CDP observations. Rerun affected R-01 close/browser/native boundaries and appropriate backend checks. No dependency install is needed; source/shared-input changes still require a new preserved review snapshot and implementation authorization.

### Batch 2 — R-03 native stored-audio boundary

Current trace:

- `backend/cache.py:audio_info` invokes native `sf.info` before its PCM checks; cache fetch copies accepted input to a section.
- `backend/sections.py:published_sections` uses it for stored sections; `backend/jobs.py` uses that path for resume/streaming.
- `backend/speech.py` inspects existing/cache audio, then opens stored sections with native `sf.SoundFile` during final assembly. Validating only the first helper leaves that read path and reopen/change boundaries to assess.
- `backend/server.py` delivers stored recording/section bytes to the browser, and Bridge exports stored recordings. Include these consumers in boundary tracing; changing metadata inspection alone must not leave unsupported imported containers advertised as WAV.
- `backend/storage.py` library copy checks containment/reparse/size/stability; it does not establish each audio file is strict supported PCM. Preserve that import protection and retained originals.

Preferred implementation direction to evaluate: bounded pure-Python/standard-library handling for stored PCM WAV metadata and reads, with mono/24-kHz/16-bit requirements checked before native autodetection. Native generation/output writing can remain where necessary; this is not automatic permission to remove SoundFile or licensing materials. Avoid check-then-reopen as the only protection; read/validate coherent handles or staged copies and define file-change failure behavior. Establish the exact compatible RIFF/PCM variants from existing generated/legacy fixtures first.

Acceptance must include:

- Renamed AIFF/MAT4, compressed WAV, invalid format/bit depth/channels/rate, truncated or out-of-bounds chunk/data sizes, invalid padding and inconsistent frame lengths fail before generic native parsing. Bound chunk work and allocations; do not load multi-gigabyte audio into memory merely to inspect it.
- Valid existing/generated PCM samples, section durations, pause counts and final timeline stay sample-correct; partial/cancel/resume/cache/recovery behavior remains usable. Do not destroy or silently rewrite originals to hide invalid data.
- Tests prove the stored-input paths do not call native autodetection, rather than only asserting a rejected final return value. Check cache copy/staging and assembly consumers as well as metadata.
- Relevant server HEAD/Range/playback/export behavior remains correct for accepted audio. Define how unsupported/corrupt items are surfaced without broadening this into a new import/repair feature.
- Reproduce review examples, exercise targeted/full relevant backend checks and actual CPU/CUDA generation using existing approved public model fixtures in a fresh evidence folder. Independent review precedes accepting the new source boundary. Package/installed/hardware checks remain separate.

This is a plan, not a verified parser design or applied fix. Exact native codec/build provenance remains open even if an app-level read boundary reduces exposure.

### Batch 3 — trusted isolated runtime evaluation

Inventory candidate provenance/signatures or hashes, interpreter build, OpenSSL/Expat/SQLite/zlib versions and actual patch dispositions. Explicitly include V03-01's two CVEs and all applicable reviewed deltas. Preserve or revalidate `cp312-cp312-win_amd64` GPU compatibility and pythonnet/pywebview/PyInstaller support. Do not replace the shared Codex runtime or copy arbitrary DLLs into it.

Use a separate authorized environment; no install has been authorized/performed here. Runtime selection must supply concrete trusted artifacts and a validation plan before installation. Acceptance includes backend/browser/native startup/close, PDF worker spawning, actual CPU/CUDA, model setup/offline/errors, current advisories and coordinated notice/provenance refresh. Final-package validation repeats after the final build.

### Batch 4 — coordinated sanitizer update and final native coverage

Recommend an authorized isolated DOMPurify lock/install/asset update while retaining current narrow options. Revalidate actual built UI/native/editor behavior. Feed-only empty results are insufficient. Exact final native inventory/rights/advisory dispositions stay with the final-package gates; they cannot be completed against today's stale artifacts.

R-04 may continue independent rights/provenance work; Argon's R-11 trial remains trace/plan-only until reviewed. Neither needs the remediation batches to be falsely declared complete. Each applied batch must get its own new evidence, hash manifest and review prompt. Original R-02/R-03 evidence is retained.
