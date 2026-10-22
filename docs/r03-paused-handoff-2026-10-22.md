# R-03 paused handoff — 22 October 2026

**Current state: paused at the publisher's request. R-03 is unfinished and has no independent remediation/release approval.** This document records the work and open questions for a new chat. Writing this handoff did not resume implementation, dependency installation, application tests or packaging.

Workspace: `C:\Users\fireball\OneDrive\Desktop\LiltTTS`. App: Violilt, formerly Lilt. Base commit: `bdf58f1b4c89a269d0647050fe26f524e73b4c12`; extensive uncommitted/untracked work belongs to this and earlier batches. Preserve it. CPU and NVIDIA support remain in scope.

**Publisher clarification:** OneDrive synchronization/application functionality is disabled. The folder name does not establish active syncing. Exclude OneDrive as the proposed explanation; no more OneDrive troubleshooting is requested. Cleanup also failed in a separate local folder. Tool-sandbox permission restrictions and the automatic approval rejection described in the reports are separate from the unresolved application/test questions.

## What R-03 was addressing

The dependency/native investigation was independently accepted **as an investigation**. It identified runtime/OpenSSL/Expat updates, generic native decoding of stored audio, a recommended DOMPurify update and incomplete exact native/final-package coverage. Empty advisory feeds did not clear those issues.

References:

- [Original R-03 investigation](r03-results-2026-10-22.md) and [returned-review reconciliation](r03-review-reconciliation-2026-10-22.md).
- [Audio remediation report](r03-audio-remediation-results-2026-10-22.md) and [audio plan](r03-audio-remediation-plan-2026-10-22.md).
- [Runtime/sanitizer report](r03-runtime-sanitizer-results-2026-10-22.md), [update plan](r03-updates-trace-plan-2026-10-22.md) and [combined independent-review prompt](r03-updates-independent-verification-prompt.md).

Read those as dated evidence with limits. None constitutes blanket security approval.

## Changes already applied

### Stored-audio boundary

`backend/pcm_audio.py` implements bounded Python RIFF/PCM inspection and coherent reads. Stored input must be supported mono 24-kHz 16-bit PCM WAV, with structural/chunk/size bounds. Renamed AIFF and unsupported/malformed containers are rejected before generic native inspection/decoding.

`backend/cache.py`, `backend/speech.py`, `backend/server.py` and `backend/bridge.py` use it for cache, section reuse/assembly, playback and export. Playback/export provide a canonical WAV header and original sample bytes from the validated handle. Staged writes preserve existing destinations on failure. Unsupported existing sections/recordings are retained under unique `.unreadable-<id>` names before replacement during regeneration. Native writing of freshly generated numeric samples remains; native-library provenance/licensing is still required.

New parser/worker/export tests and valid PCM transport fixtures were added. The earlier audio source run completed 301 methods: 300 passed, one Windows handle-replacement skip. Before/after benign AIFF evidence confirms changed admission behavior and retained original bytes. Independent acceptance of this implementation is still pending.

### Isolated runtime and sanitizer

The publisher explicitly approved isolated runtime/dependency installation after the audio batch. The old environment and shared runtime were preserved.

| Input | Current selected state |
| --- | --- |
| Python | Windows x64 CPython **3.12.15**, Astral python-build-standalone release **20261021**, ABI retained |
| OpenSSL | Actual runtime **3.5.9**, 29 September 2026 |
| Expat | Actual runtime **2.8.5**, **not 2.9.0** |
| SQLite / zlib | Actual 3.53.1 / 1.3.2 |
| Python distributions | Same 70 names/versions as the preserved baseline; dependency consistency passed |
| DOMPurify | Exact **3.4.17** in the canonical package/lock, selected isolated dependencies and rebuilt assets |
| Old frontend dependencies | `frontend/node_modules` deliberately remains at **3.4.16**, preserved for comparison |

The official runtime archive is 46,388,793 bytes, SHA-256 `be7f14464d1d66f84429ad27e01f6d1482963afff64a2fb5256b2a51c7b5d398`; it matched the earlier GitHub asset record and was extracted with path/type/size bounds. This identifies a third-party Windows artifact, not an independently reproduced or python.org Windows installer build.

`packaging/release-runtime.json` records selected paths, versions, nine native hashes and **proposed** Expat dispositions. `tools/verify_release_runtime.py` rejects the old interpreter and changed selected native inputs. Passing it proves the selected checks, not acceptance of the security dispositions or a complete native SBOM. `tools/prepare_release_runtime.py` provides pinned preparation/reuse.

`setup-pronunciation.ps1` and canonical `build.ps1` now select the new isolated inputs. `build-pronunciation.ps1` forwards to `build.ps1`. `tools/build_frontend.py` builds current canonical source in fresh staging with the selected isolated dependencies, checks the installed DOMPurify version and retains previous assets. Direct npm builds using preserved old `frontend/node_modules` are not this release route.

Notice assembly accepts the selected frontend dependency folder and rejects installed-version/lock mismatches. Fresh collection produced 69 Python package records, 177 collected files plus the manifest (178 files on disk), six source archives and no missing entries in that collector. This does not settle redistribution rights. The full setup/build scripts were syntax checked, not executed end-to-end. No EXE/MSIX was produced from these changes.

## Current blockers and unknown causes

| Item | Confirmed observation | Still unresolved / acceptance needed |
| --- | --- | --- |
| Expat security coverage | The generic upstream dependency table listed 2.9.0, but the executed Windows binary and CPython bundled header identify **2.8.5**. No 2.9.0 backport is claimed. | Independently accept adequately supported non-applicability dispositions, or select a compatible verified patched runtime/backport. Do not declare this solved from a version label or pin check. |
| Temporary-folder cleanup | Three ordinary 305-method runs each hit **WinError 145: directory is not empty** in teardown, in different test fixtures. One occurred outside the directory named OneDrive. | Underlying cause not established. Do not blame disabled OneDrive, assume file locks/antivirus or attribute it to the runtime without evidence. No cleanup errors were suppressed and no retry fix was applied. |
| GPU counter deadline | Final ordinary run failed `test_sampler_releases_counter_when_ui_stops_polling` at `tests/test_gpu_usage.py:379`, `closed.wait(1)`. | Determine whether this reflects test scheduling/isolation, resource cleanup or product/runtime behavior. It is a one-second counter-release assertion, not a failed TTS generation. No deadline was extended and no GPU code was changed. |
| Independent acceptance / native scope | Investigation accepted; new audio/runtime/sanitizer implementation and Expat dispositions not independently accepted. | Review current source and evidence; complete relevant exact final native/package coverage later. |

Expat proposals, **not accepted conclusions**:

- CVE-2026-102633 is described upstream as a 32-bit allocation overflow; selected runtime is x64.
- CVE-2026-77214 concerns invalid caller lengths to `XML_ParseBuffer`. Reviewed CPython Parse/ParseFile/readinst and ElementTree paths bound actual lengths; probes reject oversized bytes/bytearray readers. This supports a proposed consumer-specific disposition, not proof that the native library contains the patch. Reassess all relevant consumers and the upstream unfixed-issues warning. The app's earlier PDF text probe did not request XMP; that single case does not clear every XML path.

These questions prevent confidently signing off R-03 and approving this runtime as final release input. Other independent release work can proceed when authorized. They do not make exploratory EXE testing technically impossible. Recommended order is to clarify the source/runtime findings before treating a newly built EXE/MSIX as the final candidate. Any exploratory package operation needs its own authorization, fresh output and clearly limited purpose.

## What passed, and what did not

| Run/check | Recorded outcome |
| --- | --- |
| Audio batch backend, earlier baseline runtime | 301 methods: **300 passed, one skipped** |
| Initial isolated updated-runtime backend (`backend.log`) | 301 methods: **300 passed, one skipped** |
| New runtime verifier unit tests | Four passed; old/version/architecture, altered/missing-byte and escaping-pin rejection covered |
| `backend-final.log` | 305 methods: **303 passed, one teardown error, one skip**; continuation cache test |
| `backend-serial.log` | 305 methods: **303 passed, one teardown error, one skip**; branding migration test |
| `backend-local-temp.log` | 305 methods: **303 passed, one teardown error, one skip**; model download/pins test |
| Corrected diagnostic comparison: `backend-baseline-guarded.log` and `backend-updated-guarded.log` | Each **305 methods: 304 passed, one skipped**; no failures, cleanup errors or recorded cleanup observations. Wrapper records/re-raises errors; it does not suppress or retry. |
| Latest ordinary run: `backend-final-plain.log` | **305 methods: 303 passed, one GPU deadline failure, one skipped**; no cleanup error in this run |
| Focused repetitions | Continuation module passed three times per runtime; GPU module passed three times per runtime. This does not identify the mixed full-run results' cause. |
| UI | 15 browser tests passed against staged assets; four promoted asset hashes matched exactly. Frontend check: zero errors/warnings. |
| Native UI | Six source WinForms/WebView2/Bridge/SQLite close cases passed, debug off: immediate/inflight/retry/cancel/timeout/clean |
| Actual speech generation | CPUExecutionProvider **168,448 frames**; CUDAExecutionProvider **171,008 frames**. Injected persistence/optional worker-cache faults recovered; existing approved model fixtures unchanged. |
| Other bounded checks | Media HEAD/Range/playback and foreign-origin protections passed; four app sanitizer inputs passed, XHTML advisory control lost its unsafe target attribute; normal XML/oversized-reader/malformed UTF-16 and certificate-verified public HEAD checks passed. Actual fixed model URL redirected successfully without downloading a body. |

The one backend skip is the OS refusing replacement of a tested open file. Do not call 305 methods run “305 passed,” substitute guarded comparisons for the final ordinary result, or rerun broadly until green as the acceptance rule.

## Harness mistakes and limits to retain

- The first separate baseline diagnostic runner lacked a multiprocessing main guard. That attempt is invalid comparison evidence; its failures are not app regression findings. Only its two identified owned processes were stopped. The corrected runner includes the main guard/freeze support and its comparison runs passed. Keep `backend-baseline-diagnostic.log` separate from `backend-baseline-guarded.log`.
- The first runtime verifier incorrectly interpreted the first three elements of OpenSSL's `(3, 5, 0, 9, 0)` tuple as its version. It was corrected to check the full version string plus native hashes. No arbitrary DLL was substituted.
- Vite initially needed tool-sandbox escalation for file-realpath access. One sanitizer command was rejected because automatic review interpreted it as editing older evidence; it did not execute. A newly authored isolated runner was approved and passed. No action remains blocked by that review. These tool restrictions are not evidence of OneDrive interference.
- Cleanup `os.py`, `shutil.py` and `tempfile.py` were byte-identical between old and new runtimes. This does not prove all native behavior or external conditions equal. Root causes remain unknown.

## Locations, snapshots and bookkeeping correction

All paths below are relative to the workspace unless absolute:

- New Python: `.tmp/r03-updates-20261022/env/Scripts/python.exe`; base `.tmp/r03-updates-20261022/runtime/python/`.
- Old Python: `.tmp/pronunciation-env/Scripts/python.exe`; shared base runtime unchanged.
- Selected frontend dependencies: `.tmp/r03-updates-20261022/frontend/node_modules/`.
- Main update evidence: `.tmp/r03-updates-20261022/`; audio evidence: `.tmp/r03-remediation-20261022/`; investigation: `.tmp/r03-20261022/`.
- Actual public model fixtures: `dist/validation-bbe961f-20261022/Violilt/models`; approved GPU source fixture: `.tmp/pronunciation-gpu-runtime`.
- Before the audio edits, 386 investigation input contents were archived. Before runtime/sanitizer edits, 450 audio-revision input contents were archived in `.tmp/r03-updates-20261022/input-snapshot/`. These are content archives, not complete checkouts/environments.
- The update manifest `.tmp/r03-updates-20261022/source-hashes.json` recorded **751 inputs, 55 new-base native files, 85 evidence entries and 178 notice files**. Its recorded inputs matched when this documentation task started. **Coverage gap:** it omitted root `build.ps1`, which was changed. Do not regard it as complete build-input coverage.
- New pause checkpoint: `.tmp/r03-updates-20261022/handoff-checkpoint/source-hashes.json`. It includes current canonical `build.ps1`, root build/setup/configuration inputs and this handoff. The earlier manifest is preserved unchanged. The checkpoint also retains earlier index documents, the current build diff and a Git HEAD build reference. The HEAD reference is not claimed to be exact archived pre-edit working-file bytes.

New checkpoint hashes describe files at documentation time. They do **not** mean application tests or the build pipeline were rerun against a new verified package. Ignored evidence/environments are not committed or guaranteed to transfer with Git; preserve them for later review. The backup requirement remains waived.

## Separate release work still open

R-02's independently reported parent-cache/startup/close failure, pending retry resurrecting a deleted recording and CDP helper false-success path remain unresolved. The current six close cases do not reproduce the parent-cache trigger. R-04 exact redistribution/licensing and privacy remain separate; Argon's R-11 trial was trace/plan-only pending review.

Existing EXE/MSIX artifacts predate refinements and these R-03 changes. Source evidence does not validate final frozen payloads, installed-MSIX behavior, update/uninstall retention or certification. Testing the actual final MSIX on another machine before release remains **mandatory**, with separate low-end/no-GPU and supported NVIDIA evidence as needed.

No commits, destructive Git, personal-library access, EXE/MSIX build/install, publication or automatic cross-chat messages occurred in these batches. The installation approval covered the scoped isolated updates. The publisher then paused implementation. The latest request authorized documenting this handoff and snapshot bookkeeping only.

## How the next chat should begin

Use [the new-chat prompt](r03-new-chat-prompt.md). First review this checkpoint and the underlying logs/source read-only. Report which observations are established, what remains unknown and a minimal diagnostic plan. Trace the specific failures and relevant lifetimes/scheduling first; compare matched old/new environments only when justified. Avoid another broad installation/update/test loop, changing test deadlines, ignoring cleanup errors or treating inferred CVE non-applicability as accepted.

Keep Expat/security acceptance separate from intermittent test diagnosis. Propose the smallest next batch and its closure evidence before applying changes. Resume implementation or package operations only when the publisher directs it. Use the independent-review prompt when the publisher wants verification rather than implementation.
