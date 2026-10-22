# R-03 stored-audio remediation — 22 October 2026

Status: **source implementation and local validation complete; independent acceptance pending**. This addresses **R03-F02** from the accepted investigation, not all of R-03. [Trace/plan](r03-audio-remediation-plan-2026-10-22.md), [independent-review prompt](r03-audio-independent-verification-prompt.md). R03-F01 runtime/OpenSSL/Expat, F03 sanitizer update and F04 exact native/final-package coverage remain open. [Concrete runtime/sanitizer candidate plan](r03-runtime-sanitizer-update-plan-2026-10-22.md). Installation approval was requested separately; no dependencies were installed or locks/assets changed in this audio batch.

## Reproduction and resulting behavior

Before editing, a disposable real AIFF file named `.wav` reproduced admission by `audio_info`, cache fetch and published sections. The copied bytes matched the unsupported original. After editing, the **same file** is rejected in all three places with native `soundfile.info` and `SoundFile` patched to fail if called. Its original bytes remain unchanged. Evidence: `.tmp/r03-remediation-20261022/before-results.json`, `after-results.json` and `after-audio-check.py`. These are benign reachability checks, not hostile native exploits.

Stored audio now uses bounded Python RIFF/PCM handling, with no generic native codec autodetection. Accepted audio is little-endian RIFF/WAVE, mono 24-kHz 16-bit integer PCM, including explicitly validated PCM extensible headers. Exact file/chunk extents, format alignment, nonempty/even sample bytes and a single ordered format/data pair are checked. Chunk count and metadata work are bounded; audio is sought over and copied in bounded blocks rather than allocated wholesale. Unsupported containers, compressed WAV and malformed structures are unavailable for section reuse, playback or export.

Playback and export expose a canonical 44-byte WAV header plus raw samples **from the same validated open handle**. HEAD/Range operate on that view. Incidental source metadata is omitted from delivery/export; stored originals are unchanged. Changed/truncated files abort reads, and export/cache staging preserves existing destinations on failure. Unsupported saved sections and existing complete recordings are retained under a unique `.unreadable-<id>` name before replacement during regeneration; failed retention stops generation instead of destroying the original. No automatic repair/import feature was added.

Final assembly reads stored sections through the same Python reader and writes PCM with the standard-library WAV writer. Section frame counts, pauses, cancellation and the final timeline remain checked. Native SoundFile output writing for freshly generated numeric samples remains; this is not removal of libsndfile or its redistribution obligations.

## Changed source and tests

- New `backend/pcm_audio.py`; consumers `backend/cache.py`, `backend/speech.py`, `backend/server.py` and `backend/bridge.py`.
- New `tests/test_pcm_audio.py` (17 methods); two worker regressions and one export regression. Tests include forbidden native calls, container/format/chunk bounds, coherent handles and file changes, original/destination preservation, metadata-free HTTP HEAD/Range, sample-exact resumed assembly and invalid-section retention.
- Existing `test_bridge.py`, `test_io_failures.py`, `test_storage_server.py` and `test_performance.py` transport/export fixtures now contain actual PCM WAVs instead of arbitrary bytes. Their range/atomic-write assertions remain meaningful. `test_worker_io.py` injects final-write failure at the new standard WAV writer.
- Existing R-01/R-02 changes remain. No parent-cache, pending-deletion/retry or CDP helper remediation is claimed; those separate independent findings remain open.

## Validation actually run

Existing `.tmp/pronunciation-env/Scripts/python.exe`, installed Node/Edge/Playwright, and approved public model/GPU fixtures were reused. No personal library was accessed and no model downloaded.

| Check | Result / evidence under `.tmp/r03-remediation-20261022/` |
| --- | --- |
| Focused backend before the last three added methods | 47 methods run: 46 passed, one skipped; `focused-second.log` |
| Full final backend suite | **301 methods run: 300 passed, one skipped**; `backend-final.log`. Earlier full pass retained in `backend-full.log`; final repeat includes preservation of unsupported complete recordings. |
| Built UI regressions | **15 passed** against unchanged existing `frontend/dist`; `browser.log` |
| Native WinForms/WebView2 close | **Six passed**: immediate, inflight, retry, cancel, timeout, clean; `close-*/` and matching logs |
| Source browser media/security boundary | Passed raw GET/HEAD/Range, published section, local playback advancement, rejected invalid routes/Host/method, blocked controlled foreign fetch/embed/frame; `media-validated/`, `media-validated.log` |
| Real source CPU worker | CPUExecutionProvider, **168,448 frames**, 7.0186667 seconds, injected one-time progress persistence failure recovered; final `real-runtime-final/`, `real-runtime-final.log` (earlier successful run retained in `real-runtime/`) |
| Real source CUDA worker | CUDAExecutionProvider, **171,008 frames**, 7.1253333 seconds, injected optional worker-cache initialization failure recovered; same evidence |
| Model fixture stability | Runtime helper's before/after hashes unchanged; no new inference benchmark or human listening |
| Before/after AIFF reproduction | Acceptance changed to rejection, original retained, no native inspection/decode invoked; `before-results.json`, `after-results.json` |
| Whitespace check | `git diff --check` passed, with existing LF/CRLF normalization notices |

One backend test is skipped on Windows because the OS refuses replacement of the tested open file. It does not establish successful concurrent path replacement on Windows. Other coherent-read/change checks and native-call exclusions ran. Full-suite counts mean 300 passing methods plus this skip, not 301 passes.

Harness corrections are retained: the first focused attempt used the sandbox's inaccessible default temporary directory; the corrected run set workspace TEMP/TMP. Two initial later commands resolved the Windows Store `python` alias; subsequent commands used the explicit project interpreter. An initial media run omitted the existing Playwright module path, so no browser result was generated; the corrected run used a fresh folder and passed. These are failed harness attempts, not successful validation or application regressions. Native/loopback checks required execution outside the restricted tool sandbox. No automatic-approval rejection occurred.

## Snapshot and scope limits

Before product edits, **all 386 prior R-03 repository input files** were hash-checked and copied to `input-snapshot/`; the original manifest was copied as `prior-input-manifest.json`. The original R-02/R-03 reports/manifests/evidence remain unchanged. Their old hashes naturally no longer describe the modified current source/tests. Current inputs and evidence are recorded separately in `source-hashes.json`. A preserved content snapshot is not a new Git checkout or complete frozen environment; shared runtime identities remain separate records.

This batch changes R-02 audio/export/server/worker inputs, so its old normal-path counts cannot be substituted for this revision. R-02's independent parent-cache/startup/close, removed-recording resurrection and false-success navigation-helper findings remain unresolved. The native close rerun covers its six existing cases, not the reviewer's optional-cache failure trigger.

No dependency/runtime installation, frontend source/build/asset change, commit, destructive Git action, EXE/MSIX build/install, publication or cross-chat message occurred. Backup waiver unchanged. Current EXE/MSIX artifacts predate these fixes and the refinements. Final frozen/installed-MSIX, mandatory other-machine/low-end/no-GPU, licensing/privacy and Store certification gates remain separate. Independent review must assess this parser design and consumers before source acceptance; no blanket security or release approval is claimed.
