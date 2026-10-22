# Violilt Microsoft Store release — handoff

## R-03 paused; new-chat checkpoint recorded — 22 October 2026

The publisher paused implementation and requested a complete record for another chat. **Start with [the paused R-03 handoff](r03-paused-handoff-2026-10-22.md) and [copyable new-chat prompt](r03-new-chat-prompt.md).** It records changes, runtime paths, passing/failing checks, unresolved causes, Expat dispositions, harness mistakes, existing work and release boundaries. This turn performed documentation/snapshot bookkeeping only; no fixes, tests, installs or package operations resumed.

OneDrive functionality is disabled per the publisher; exclude it as the proposed cause and do not resume OneDrive troubleshooting. Current blockers remain Expat security acceptance and mixed cleanup/GPU-deadline test results. Earlier update manifest coverage omitted canonical `build.ps1`; that gap is recorded. The new [pause-checkpoint manifest](../.tmp/r03-updates-20261022/handoff-checkpoint/source-hashes.json) includes it; older evidence is retained and not retroactively promoted to complete verification. R-03 remains open. Read-only review/report is the next-chat starting point; implementation stays paused until directed.

## R-03 isolated runtime/sanitizer updates implemented — 22 October 2026

The publisher explicitly approved isolated runtime/dependency installation. [New results and limits](r03-runtime-sanitizer-results-2026-10-22.md), [trace/plan](r03-updates-trace-plan-2026-10-22.md), [combined audio/runtime/sanitizer review prompt](r03-updates-independent-verification-prompt.md). The [reusable review hub](release-review-handoff.md) now targets the combined current revision; the audio fix has not yet received independent acceptance.

Selected isolated Windows x64 runtime is Python **3.12.15**, OpenSSL **3.5.9**, **Expat 2.8.5** (not the generic metadata's 2.9.0), with the same 70 Python distributions as before. DOMPurify is now pinned/built at **3.4.17**. Old `.tmp/pronunciation-env`, shared base runtime and `frontend/node_modules` remain unchanged; the latter intentionally stays 3.4.16. Setup/build now select the isolated inputs, reject old/native-drifted runtimes and build current frontend source with the new isolated dependencies. Nine selected native bytes are pinned; this is not a complete native SBOM. Fresh notices match the new sanitizer.

Actual CPU/CUDA, 15 browser tests, six native debug-off close cases, media protections and TLS/XML checks passed. Both runtimes passed a corrected 305-method diagnostic suite (304 passed/one skipped). Earlier plain runs hit temporary-directory WinError 145 teardown errors in different folders, including outside OneDrive. The final ordinary run had 303 passes/one GPU-counter deadline failure/one skip; the GPU module then passed three times per runtime. Causes remain unresolved; retain all failures. An initial separate diagnostic lacked a multiprocessing guard and was invalid; it was corrected and only its owned processes were stopped. Read the result's validation addendum before quoting counts or accepting the runtime.

The proposed Expat dispositions (32-bit-only overflow versus x64; invalid native buffer lengths versus bounded CPython callers) require independent review; no 2.9.0 patch/backport or blanket native clearance is claimed. All 450 prior audio-revision input contents were archived before updates. Original evidence is retained; current hashes belong to `.tmp/r03-updates-20261022/source-hashes.json`. No EXE/MSIX build/install, commit, personal-data access, publication or cross-chat messages. Backup waiver unchanged. R-02 findings and final-package/installed/mandatory other-machine/licensing/privacy/certification gates remain open. Earlier sections below are historical checkpoints.

## R-03 audio source remediation ready for independent review — 22 October 2026

Publisher authorized R-03 implementation. The stored-audio boundary is now implemented and locally validated: bounded pure-Python PCM handling replaces native autodetection, cache/export use staged canonical copies, browser media uses the same validated handle, and assembly reads raw PCM. Unsupported existing sections/recordings are retained before regeneration. [Results and limits](r03-audio-remediation-results-2026-10-22.md), [trace/plan](r03-audio-remediation-plan-2026-10-22.md), [review prompt](r03-audio-independent-verification-prompt.md). The [reusable review hub](release-review-handoff.md) targets this new revision; independent acceptance is pending.

Validation: 301 backend methods run (300 passed, one Windows handle-replacement skip), 15 browser tests, six native close cases, actual browser media playback/HTTP protections, and real CPU/CUDA generation. Precise snapshots and harness corrections are in the result document. All 386 original R-03 repository input contents were preserved before product edits under `.tmp/r03-remediation-20261022/input-snapshot/`; old reports/manifests/evidence remain unchanged. The current modified source needs its new manifest, not the old R-02/R-03 hashes.

R-03 remains open: runtime/OpenSSL/Expat updates, DOMPurify update and exact native/final-package coverage are separate. [Concrete isolated update plan](r03-runtime-sanitizer-update-plan-2026-10-22.md): Astral 20261021 CPython 3.12.15, upstream metadata selects OpenSSL 3.5.9 and Expat 2.9.0; DOMPurify 3.4.17. Actual binary versions/compatibility are unverified. Specific installation approval was requested under the publisher's earlier restriction; no dependencies, shared runtime, pins or frontend assets were changed. No EXE/MSIX build/install, commit, personal-library access, publication or cross-chat messages.

The separately reviewed R-02 parent-cache, removal/retry and navigation-helper findings remain unresolved. Six existing native close cases do not cover that parent-cache failure. Final-package/installed/mandatory other-machine/low-end/no-GPU, licensing/privacy and certification gates remain open; old artifacts predate these changes. Backup waiver unchanged. Earlier sections below are historical checkpoints.

## R-03 independent investigation accepted; fix plan recorded — 22 October 2026

The publisher returned the [R-03 independent review](../.tmp/r03-independent-20261022-b019f803/review.md): **passes the scoped investigation**, with runtime/audio/native coverage still required and sanitizer update recommended. [Reconciliation and next batch plans](r03-review-reconciliation-2026-10-22.md). This is not release approval or source remediation acceptance. The original reviewed R-03 report/prompt/manifest remain unchanged.

The additional Expat 2.9.0 note is incorporated: assess XML_ParseBuffer length validation (CVE-2026-77214) and the 32-bit overflow case (CVE-2026-102633) against actual wrappers/architecture/patches before accepting a replacement runtime. A literal version label is not enough; verified equivalent fixes/dispositions can qualify.

The supplied review links an [R-02 review with needs-fixes verdict](../.tmp/r02-independent-20261022-3d986790/review.md): parent optional-cache failures can block startup/close; pending retry can recreate a removed recording; CDP errors can still produce a false pass. These are now separately tracked. Recommended order: R-02 review fixes, R-03 stored-audio boundary, authorized isolated runtime evaluation, coordinated sanitizer update/final native coverage. R-04 and Argon's R-11 read-only trial can continue independently.

This reconciliation applied no code/dependency/asset fixes and ran no new application tests. Existing review inputs/evidence are preserved; installs, commits, package operations, personal-data access, publication and cross-chat messages remain unauthorized. Backup waiver unchanged.

## R-03 advisory investigation ready; remediation/coverage open — 22 October 2026

Publisher authorized R-03 and then requested continuation. [Results and prioritized follow-up](r03-results-2026-10-22.md), [independent-review prompt](r03-independent-verification-prompt.md). The [reusable handoff](release-review-handoff.md) now targets this investigation; pending R-01/R-02 reviews remain recorded separately. R-03 is not checked off as a release gate.

- Inventoried 70 current CPU/build distributions, eight prepared GPU distributions and 98 npm lock pairs. All 70 CPU/build pins match; installed npm metadata has no version drift. OSV returned **178 ordered current-version results (80 PyPI + 98 npm), zero matches/errors/pagination**; npm bulk also returned empty. A separate known-vulnerable pypdf control returned advisories. These feed results are not a native/security clearance.
- Maintainer/native review found follow-up: OpenSSL 3.5.8 versus 3.5.9 client certificate memory-pressure fix, later Python/Expat security releases, unresolved stored/imported audio parser exposure and native provenance. DOMPurify 3.4.16 matches three Low maintainer advisories fixed in 3.4.17; current narrow configuration lacks affected modes and passed four targeted synthetic inputs. A coordinated update is recommended, not a demonstrated active-config bypass.
- Inventoried/hash-checked **199 old-payload native files** (all match saved old audit) and 25 prepared GPU DLLs. Older `bbe961f` artifacts still predate refinements/R-01/R-02. Five current runtime files have different hashes despite matching old displayed versions. Tagged ONNX C++ inputs, codec markers and metadata are not a complete measured wheel SBOM.
- Benign surface checks: one PDF text extraction avoided XMP parsing, with an active positive-control hook; `audio_info()` accepted AIFF named `.wav`, confirming native autodetection precedes its PCM checks. No hostile native PoC, app exploit/crash or full runtime suites were run. Exact scope/harness corrections are documented in the report.
- No product source/shared tests/assets/pins/dependencies were changed. All 69 preserved R-02 inputs remain matching. New evidence: `.tmp/r03-20261022/`, with its own manifest. No installations, commits, package builds/installs, personal-data access, publication or cross-chat messages; backup waiver unchanged.

Recommended next work: independent audit review; trace/plan native-audio validation and a trusted isolated interpreter/OpenSSL/Expat refresh, preserving GPU/cp312 compatibility. Dependency/runtime installations still need authorization under the publisher's standing constraint. R-04 rights/provenance work can proceed independently. Final-package/installed/MSIX-on-another-machine/privacy/performance/certification gates remain open.

## Standing independent-review workflow — 22 October 2026

The publisher requested a review handoff/prompt after **every completed R item**, so the review chat can verify that batch while this chat continues independent next-item work. Reusable entry point and copyable prompt: [release review handoff](release-review-handoff.md). Latest ready target is **R-02 with the R-01 navigation/close overlap**; both remain pending independent acceptance.

Each completion must provide its own report/prompt, exact input manifest, scoped evidence/limits and updated status. Preserve old snapshots; call out shared-input/dependency changes and isolate or coordinate affected checks so simultaneous work cannot silently invalidate review. The publisher brings the review report back here; this chat reconciles findings, fixes and reissues affected batches within authorization. No automatic cross-chat messaging or blanket release approval. Final-MSIX testing on another machine remains mandatory.

This workflow update changes documentation only. No new application tests or R-03 investigation, dependency installations, commits, package operations, personal-data access or publication. The backup waiver remains in effect.

## R-02 implemented and locally validated; combined review pending — 22 October 2026

The publisher authorized proceeding with R-02 after the trace/plan. [R-02 results](r02-results-2026-10-22.md) records reproductions, scoped fixes, exact evidence and remaining gates. [Combined independent-review prompt](r02-independent-verification-prompt.md). This is implementation-chat evidence, not independent acceptance or release approval.

- Confirmed/fixed background persistence failures, cleanup after failed shutdown writes, partial export replacement, unavailable recovery bookkeeping and optional-cache/output worker failures. Pending metadata is coalesced and retried with a visible warning; it remains in memory until a successful write. Existing durable data/audio is retained. Whole-file damaged SQLite already fails without rewriting original bytes; no destructive repair added.
- A native canceled-navigation probe exposed a save/close callback problem: pinned pywebview reinjected the bridge after canceled navigation. A process-local `backend/desktop.py` adapter preserves callback tables when the original trusted page remains. Successful loads/other failures retain initialization. Current probes pass navigation/UI/API/save-on-close; the historical body-locator timeout is not conclusively explained.
- Final evidence: **281 backend tests**, **15 browser cases**, **six native close reruns**, passing native navigation/media checks and actual **CPU/CUDA** generation. CPU recovered from an injected progress-write error; CUDA completed with optional cache unavailable. Model fixture hashes unchanged. Source/synthetic/same-machine checks; no human listening or performance clearance.
- Canceled navigation can still send preliminary GETs; none carried Referer/Cookie in this controlled probe. Browser audio fetch/embedding/framing isolation passed, while raw local known-ID access remains possible. Session binding stays optional on this evidence; installed ACL/privacy review remains open.
- R-02 changes `backend/desktop.py`, the **only changed input among the eleven in R-01's old manifest**; ten other inputs including frontend/assets match. Preserve `.tmp/r01-close-20261022/`. New combined hashes/evidence: `.tmp/r02-20261022/`. Review the combined boundary before accepting R-01/R-02; do not silently apply an old hash verdict to current source.
- No dependencies, commits, EXE/MSIX build/install, personal-data access, publication or cross-chat message. Existing work preserved; backup waiver unchanged. Older packages remain stale. Final-package/installed-MSIX, mandatory other-machine installer testing, low-end/no-GPU, licensing/privacy and certification gates are still open.

Next: independent combined source verification, then R-03 advisory/payload inventory. Rights/privacy and publisher identity preparation may proceed alongside it. Older sections below describe their then-current state; this section supersedes the planning-only R-02 status.

## R-01 review prompt and R-02 trace/plan — 22 October 2026

The publisher requested an independent R-01 review prompt while this chat traces/plans R-02. Copyable prompt: [R-01 verification](r01-independent-verification-prompt.md). It includes untracked files, current input-hash checks, existing tools/disposable outputs and a strict verification-only scope; it does not send a message or authorize the other chat to apply fixes.

[R-02 trace/plan](r02-trace-plan-2026-10-22.md) records read-only findings and proposed acceptance checks. Source inspection found candidates around uncaught job-state persistence errors/cleanup, direct export replacement and combined recovery/cache failures. These need fault reproduction before claiming demonstrated bugs. The historical JS navigation/body timeout remains unclassified; its returned assignment string is not proof that a foreign page loaded. Local known-ID audio access remains a threat-model/hardening decision, and implemented GPU runtime trust is not reopened.

Recommended R-02 first batch: disposable listener/shutdown and export fault reproductions, then separately scope fixes for confirmed results. Navigation classification and local-resource checks follow; installed ACL/DLL/update/other-machine evidence stays with the package gates. No R-02 tests/probes or product/test/asset edits were performed in this planning turn. Keep shared R-01 source/assets stable while independent review runs. No installation, commit, personal-data access, publication or cross-chat message; backup waiver unchanged.

## R-01 normal-close save reliability — 22 October 2026

The publisher authorized tracing, planning and implementing R-01. Source implementation is complete and locally validated; **independent verification is the next step**, not implied by these results. Full trace, paths, commands, evidence and limits: [R-01 report](r01-save-on-close-2026-10-22.md).

- Normal native close now waits for the ordered document-save queue. Save failure or a ten-second wait keeps the window open with retry/keep-editing controls. Cancellation revokes stale/queued approval. Closing does not await Spoken preparation. Existing public native dispatch restrictions remain in place.
- Validation: **264 backend tests**, **15 browser tests**, Svelte **zero errors/warnings**, frontend build passed; **six debug-off native source cases** passed with synthetic libraries and real Bridge/SQLite. A fresh SQLite connection after shutdown retained expected text. The new immediate-close regression failed against the old frontend before production edits.
- Native cases exercise WinForms `Close()` programmatically, not a physical title-bar click. Save delays/failures are injected; no power-loss/OS-shutdown/frozen/installed-MSIX or new speech-generation claim is made. The retry case's injected `OSError` is expected test input.
- Source files: `backend/window_close.py`, `backend/desktop.py`, `main.py`, `frontend/src/App.svelte`; tests/helper: `tests/test_window_close.py`, `tests/test_editor_save.cjs`, `tools/native-close-check.py`. New files remain untracked; include them in review. Evidence is in `.tmp/r01-close-20261022/`.
- Existing work was preserved. No dependency installation, commit, EXE/MSIX build/install, personal-data access or publication occurred; the backup requirement remains waived. Frontend assets were rebuilt for testing. Existing packages remain older and all final-package/installed/other-machine/licensing/privacy/certification gates remain open.

The older checkpoint's save-on-close limitation describes the pre-R-01 source. Use this section for the new implementation claim, and retain the earlier checkpoint for its independent refinement/generation evidence. No further R-02 implementation or cross-chat messaging was performed.

## Release sequencing agreement — 22 October 2026

The publisher asked to record the agreed required/preferred/post-release priorities before supplying another pre-release guide. The current plan is in [release readiness](release-readiness.md#release-priorities-agreed-22-october-2026); its priority classification supersedes older open-item lists while preserving their historical evidence.

- **Required:** normal-close save reliability; outstanding security/essential storage-failure triage; exact redistribution/privacy evidence; a fresh reviewed-source EXE/MSIX; installed production-identity/update/data-lifecycle checks; final-package CPU/CUDA validation; baseline accessibility/malware/applicable certification checks and publisher/listing readiness.
- **Testing the actual final MSIX on another machine is mandatory before release.** Portable/extracted payload checks are insufficient. Prefer a clean physical CPU-only PC near the proposed minimum, without development dependencies; exercise installation, imports, saving/closing/reopening, generation/playback, offline use, updates and uninstall/reinstall. Record package identity/version/hash, hardware and performance. Obtain separate low-end/no-GPU evidence if the second machine does not cover it; validate CUDA on supported NVIDIA hardware too.
- **Preferred:** second-tester usability and listening review, wider hardware/driver coverage, acceptable-baseline performance improvements, fuller recovery/export UX and optional code protection. Serious findings become blockers. No local packaging can promise uninspectable code.
- **Can follow later:** OCR/multilingual/custom-model features, old-title repair, separately reviewed diagnostics/sharing, further polish/optimization and monetization changes. Free without ads is the launch recommendation, not a final decision. Ongoing patching follows release, but the update/support route must be established beforehand.
- **Next step:** R-01 is implemented and locally validated as recorded above; return it to the verification chat for independent review before accepting the source fix or progressing to fresh-package validation. Licensing/privacy and publisher setup can progress alongside it. Keep source, final-package, installed-MSIX, low-end/no-GPU, licensing/privacy and Store-certification evidence separate.
- **Guide reviewed; remaining-work checklist consolidated:** the publisher's 21 October release guide largely overlaps existing work and has an outdated fix/commit/test snapshot. Current [release readiness](release-readiness.md) now tracks required R-01–R-12, preferred P-01–P-05 and post-release A-01–A-05 checkboxes. Added explicit final-build hygiene, unavailable WebView2/driver/low-GPU-memory/download-failure cases, defined update/recovery procedures and per-package/machine evidence fields. Original S-01–S-06 source fixes stay completed within their recorded scope. Additional review models and public VirusTotal uploads are not mandatory; guide prompts do not authorize execution. No report grants blanket release approval or permission to expand scope.

This update is documentation only. No application edits, tests, package builds/installs, dependency installations, commits, personal-data access or publication were authorized/performed by this planning update. Preserve existing work; the backup requirement remains waived.

## Current source verification and Store-chat checkpoint — 22 October 2026

The user authorized this chat to add GPU-counter recovery, verify the completed
TXT/PDF work from the other chat, then consolidate the handoff for the main
Microsoft Store chat. This batch was completed without an agent commit; the
refinements are now committed in the release-planning checkout as noted below.
The earlier backup requirement was explicitly waived. During that verification
batch, no dependency was added or installed,
no personal library/document was used, and no commit, state-changing Git command,
package rebuild/installation, shortcut change or publication occurred.

Use this checkpoint and the immediately following implementation sections for
the current refinement state. Older open-item lists and older successful
package checks describe their recorded snapshots; they do not establish that
these source refinements have shipped. Verification originally recorded HEAD
`bbe961f4af81046f8ea76ad5fc04124e1a62068a`; the release-planning review now finds
the refinements committed at `bdf58f1b4c89a269d0647050fe26f524e73b4c12`.
This bookkeeping correction implies no test rerun or package rebuild. Older
implementation sections retain their at-the-time uncommitted descriptions.

| Item | Current result | Evidence / remaining limits |
| --- | --- | --- |
| TXT import | Verified for the exercised source/native paths | Eight TXT regression methods, title coverage, real native UTF-16 drop with Turkish characters/emoji, invalid-encoding rejection, unchanged original fixtures, actual English CPU generation. UTF-8/BOM UTF-16 scope and 2-MiB source/converted-copy limits remain. Unicode import does not promise multilingual speech. |
| Selectable-text PDF import | Verified for the exercised source/native paths | Eleven PDF regression methods, title coverage, real parser/native import and rejection paths, actual uncached CUDA generation. Existing 20-MiB source, 200-page, 2-MiB extracted/converted-text, 20-second extraction and monitored 512-MiB RSS limits remain. No OCR/password entry/layout reconstruction. |
| R-01: imported title loss | Fixed and independently verified | Current `backend/bridge.py` retains the stored title as `prepare` fallback in save/generate; explicit edited Markdown headings still override it. Seven title methods pass; removing only these fallbacks in memory produces 25 assertion failures across five methods, with the two explicit-heading guards still passing. Real completed native PDF and TXT jobs and read-only SQLite inspection retain filename titles. Already overwritten titles are not automatically repaired. |
| GPU utilization and recovery | Verified for the exercised source/native paths | 23 GPU test methods, including six new recovery/stop methods. Real CUDA worker counter was deliberately failed once, its value became unavailable, the same PID reopened a real PDH query after 5.032 seconds, real readings/UI resumed and audio generation completed. CPU generation returned null GPU values. Physical driver resets and other hardware were not tested. |

### GPU change made in this batch

Only `backend/gpu_usage.py`, `tests/test_gpu_usage.py` and this handoff changed.
The TXT/PDF/title implementation and all other earlier edits were preserved.

- Replace permanent sampler shutdown after an `OSError`/`ValueError` with
  delayed query reopening on the existing background thread. Wait 5 seconds
  after the first failure, then 10, 20 and at most 30 seconds between repeated
  failures; continue at the capped interval only while sampling is requested.
  A successful counter read resets that delay to 5 seconds.
- Close failed queries and immediately clear their published value. Unavailable
  remains null/hidden; a measured zero remains zero. A reopened rate query takes
  a new baseline before publishing a later reading. The bridge does not wait
  for query access or retry delays.
- Retain one-second sampling, three-second freshness, idle cleanup after more
  than five seconds without requests, event-driven cancellation on worker/CPU
  changes, and protection against old workers replacing current readings.
  Cancellation remains responsive during the longer backoff. Unsupported
  counters remain optional and retry at the capped interval, without affecting
  speech generation. This is a robustness improvement, not evidence that the
  original review had found a broken GPU reading on the tested machine.

### Validation actually run for this checkpoint

- Before the GPU production edit, the sampler suite ran **11 methods**:
  **five failed assertions, six passed, zero errors**. Five new methods
  demonstrate missing recovery/backoff/reset/idle behavior. The sixth new
  cancellation-during-backoff method also passed the old implementation and is
  a guard, not proof of a new fix. Tests use virtual monotonic time and fake
  counter results to verify the full 30-second cap without slow wall-clock waits.
- Current full backend suite: **255/255 in 35.588 seconds**, exit 0.
  Focused TXT/PDF/title/GPU/performance/model-memory/native-bridge suite:
  **78/78 in 12.108 seconds**, exit 0. Both use disposable TEMP/TMP and the
  existing project Python with `-B`. An initial focused sandbox run passed
  44/45 but hit WinError 10013 on an existing loopback-server test; the complete
  outside-sandbox runs above passed. This was not an app-error assertion.
- Current built-frontend editor/save/autosave browser suite: **9/9 in 13.850
  seconds**, exit 0, using the existing Playwright/Edge and a synthetic API.
  Installed Svelte checker: **zero errors/warnings**, exit 0. `pip check`:
  **No broken requirements found**. `git diff --check` passed. Ruff/pyright
  were not found in PATH, the project Python Scripts directory or frontend
  tool bins; nothing was installed. No frontend production source changed in
  this batch and its existing built assets retained their hashes.
- Independent title counterfactual: change only the two fallbacks in the
  imported Bridge module in memory; leave project source intact. **Seven
  methods, 25 assertion failures, zero errors in 7.154 seconds**. The initial
  helper lacked the Windows multiprocessing main guard and is invalid PDF
  counterfactual evidence; it was corrected and the valid run above retained.
- Native current-source pywebview/WebView2 app: **six checks passed, zero page
  errors**, using a fresh disposable library and copies of previously verified
  public model fixtures. Actual Bridge/SQLite/parser children, disk-backed
  native File objects, PDH and speech workers ran. Only picker selection was
  stubbed and one PDH read raised a deliberately injected OSError. Successful
  PDF/TXT import, Unicode preservation, scanned/encrypted/malformed PDF and
  invalid TXT rejection, overlay recovery, retained document/job titles,
  uninterrupted uncached CUDA generation, counter recovery, CPU generation
  without GPU values and media delivery/muted playback were observed.
- Native results include **142 polled non-null GPU values** (polls can repeat a
  one-second sample), maximum **58.6%**. Reopen retained the same worker PID.
  Both completed WAVs are mono PCM16 at 24 kHz with nonzero samples: GPU
  **12,156,704 frames / 506.529 seconds**, CPU **626,848 frames / 26.119
  seconds**. These are audio durations, not inference timings. No human audio
  quality listening or independent GPU-profiler comparison is claimed.
- All **seven successful-run original fixtures** remained byte-identical.
  Of **165 recorded pre-batch files/assets**, **163 retained their hashes**
  through validation; only the intended GPU module/tests differed. This
  handoff was edited afterward. The other chat's title code/tests, PDF parser,
  requirements/spec, UI and model/runtime trust files were unchanged.
  Two initial native harness failures (a locator matching five paragraphs and
  an incorrectly escaped emoji fixture) were corrected; neither is counted as
  an app failure or a passing native run. Their logs remain available.

Reproduce with the existing project Python: `-B -m unittest discover -s tests
-v` for the full suite; focused `-B -m unittest tests.test_import_titles
tests.test_text_import tests.test_pdf_import tests.test_gpu_usage
tests.test_performance tests.test_model_memory tests.test_desktop -v`.
Browser command remains `node --test tests/test_editor_save.cjs`, with
`PLAYWRIGHT_MODULE` pointing to the already available module. Svelte check is
`node ./node_modules/svelte-check/bin/svelte-check --tsconfig ./tsconfig.json`
from `frontend`. No installation is required.

Evidence (external to the project):
`C:\Users\fireball\.codex\visualizations\2026\10\21\01a15fcf-c186-7223-9ac8-b727e17c3402\gpu-recovery-final-review-20261022`
contains `gpu-before-fix.log`, `gpu-recovery.diff`, `full-suite.log`,
`all-three-focused.log`, `browser-tests.log`, `svelte-check.log`,
`title-counterfactual.py`, `title-counterfactual.log`, `native-results.json`,
`counter-events.jsonl`, `native-validation.log`, `final-evidence.json`,
before/stability manifests and disposable fixture/library/helper files.
The earlier independent review remains in neighboring
`import-gpu-independent-review-20261022/review.md`; its R-01 is now closed for
current source by the checks above. Its other test/hardware/package limitations
are not erased by this targeted follow-up.

### Remaining work to reconcile with the main Store chat

1. **Build and validate the final source revision.** The existing checkpoint
   portable EXE/MSIX and shortcuts predate generation-status, GPU, TXT/PDF,
   autosave and title refinements. Rebuild into a new output, keep source/hash
   evidence, audit the actual frozen payload/model/runtime pins and eSpeak
   exclusion, and verify included pypdf metadata/notices, frozen PDF spawning,
   TXT/PDF flows, CPU/GPU generation and playback. The earlier small frozen-PDF
   probe and older full-package successes do not replace this check.
2. **Validate the installed production package and supported hardware.** Still
   open: real Store identity/profile/configuration; install, standard-user
   permissions, worker spawning/WebView2/dialogs, offline first run, updates,
   interruption/recovery and uninstall/data-retention behavior. Run actual
   low-end/physical no-GPU and supported NVIDIA hardware checks, including
   startup/first-audio time and memory use. This source run used one NVIDIA
   RTX 3060 Laptop/WDDM system, not an installed MSIX or no-GPU machine.
3. **Finish release evidence and publisher decisions.** Reconcile authoritative
   redistribution/license evidence for the exact models, voice/dictionary and
   native runtime payloads; same-upstream SHA-256 pins establish bytes, not
   independent provenance. Complete the actual shipped WebView2/ONNX runtime
   traffic/diagnostic and privacy/retention review, publisher/support/privacy
   information, production configuration/identity and any chosen code-protection
   work. Recheck current Store requirements and run the appropriate package,
   malware/accessibility/certification checks before submission. This batch
   does not grant blanket licensing/privacy/security or Store clearance.
4. **Keep unresolved behavior explicit.** Closing before autosave finishes can
   lose pending edits; no native close/save handshake exists. The prior
   JavaScript foreign-navigation cancellation/body timeout was also observed
   on the older checkpoint; its visible impact versus harness state remains
   unresolved. Broader restore/disk-full/resource-failure coverage still needs
   assessment. Do not re-list completed S-05/GPU-runtime-trust hardening as
   unfixed merely because older historical paragraphs still mention it.
5. **Choose or defer optional product work separately.** Diagnostics/consent
   and sharing, arbitrary custom-model support/policy, OCR/multilingual speech,
   public/developer visibility restrictions, and repair of previously lost
   titles remain decisions, not implemented features. No telemetry collection
   or new network export was added here. The currently supported model import
   still requires the approved pinned model/voice bytes.

No further implementation is authorized by this checkpoint. Stop after this
batch; subsequent Store-chat changes can be brought back for independent
verification. The main Store chat should use this file as the shared handoff;
this session did not send a message to another chat.

## TXT/PDF title preservation — 22 October 2026

The user requested a narrowly scoped fix for the independently verified loss of
imported titles on save/generation. This batch is complete and uncommitted.
Preserve all earlier TXT/PDF, save/Spoken, generation-status, GPU, native-drop
and documentation edits. No other TXT/PDF defect was confirmed or addressed.
Stop here for the user's go-ahead.

Trace verified against current code:

- Import already calls `prepare` with the filename stem as `fallback_title`.
  Literal TXT/PDF conversion does not supply an explicit Markdown heading, so
  the imported document initially receives that filename title.
- `backend/documents.py::prepare` already prefers the first nonempty parsed
  heading over its fallback. Its default fallback is Untitled reading.
  `Bridge.save_document` and `Bridge.generate` omitted the stored title when
  calling it, then persisted that default into the working copy. `Jobs.start`
  takes its title from that document, propagating the loss into the job.

Implementation:

- Only `backend/bridge.py` production code changed in this batch. Under the
  existing bridge lock, save and generation read the current stored title and
  pass it as `fallback_title` to `prepare`. No heading means preserve that title;
  an explicit working-copy Markdown heading still supplies the new title.
- `backend/documents.py`, import/conversion, storage, Jobs, frontend and schemas
  are unchanged. Existing titles are used directly, including titles differing
  from the filename; the source path is not re-read to invent a replacement.
  Removing a heading preserves the most recently stored title. Empty text can
  still be saved with its existing title; existing no-readable-text generation
  rejection remains unchanged.
- No migration or old-record repair: a title already overwritten before this
  fix is not recovered automatically. No personal libraries or source files
  were accessed or modified.

Regression coverage and validation actually run:

- Added `tests/test_import_titles.py`, using disposable TXT, generated PDF and
  Markdown fixtures, real Bridge/prepare/SQLite storage and real `Jobs.start`.
  The speech worker, runtime identity and model availability are doubles; no
  actual model is loaded or inference performed. The existing PDF fixture
  builder is reused; no dependency installation was needed.
- Seven new methods cover unchanged/edited/empty saves; direct generation
  without a prior save; save/reopen/generate; existing titles differing from
  filenames; explicit edited headings on save/generation; ATX and Setext heading
  behavior; and preserving the latest Markdown title after removing its heading.
  Both TXT and PDF are checked for returned job titles, queued worker-command
  titles, persisted job titles and reopened working-copy titles. Working-copy
  text/source metadata and byte-identical original files are also asserted.
- Before implementation: **7 methods run in 5.815 seconds; 25 assertion
  failures across five methods, two explicit-heading methods passing, zero
  errors**. This reproduced Untitled reading in saved/reopened documents and
  returned/queued/persisted jobs. No app source was swapped for this red run.
- After implementation: relevant import-title/TXT/PDF/document/bridge/symbol-job
  suites passed **56/56 in 17.262 seconds**. Full backend discovery passed
  **249/249 in 31.605 seconds**, exit code 0. Commands used the existing project
  Python with `-B` and a disposable TEMP/TMP. Full discovery ran outside the
  restricted sandbox for the existing loopback/junction tests. No automatic
  approval rejection occurred.
- Of **160 recorded pre-batch files**, **159 retained their hashes** through
  validation; only `backend/bridge.py` changed. The only new repository file was
  the title regression test. This handoff was updated afterward.
  `git diff --check` passed.

Limits: job-creation/queue/persistence coverage does not establish completed
audio or native UI behavior. No frontend build/check, native-app run, actual
speech inference, old-record repair, OCR, multilingual speech, GPU change,
packaging/rebuild, shortcut change or commit occurred. Existing executable
artifacts remain unchanged. Those items are outside this batch.

Reproduce with the existing `.tmp/pronunciation-env/Scripts/python.exe -B`:
focused `-m unittest tests.test_import_titles tests.test_text_import
tests.test_pdf_import tests.test_documents tests.test_bridge
tests.test_symbol_jobs -v`; full `-m unittest discover -s tests -v`.

Evidence:
`C:\Users\fireball\.codex\visualizations\2026\10\22\01a161f1-34e5-70e3-a0f8-919b05427c01\import-titles-20261022`
(`before-fix.log`, `focused.log`, `full-suite.log`, `source-before.json`,
`source-stability.json`, and disposable `temp/`). Stop after this batch.

## Save/Spoken synchronization and autosave — 22 October 2026

The user approved fixing save/Spoken synchronization and the discussed autosave
timing before considering developer/public visibility restrictions. Their word
"autocorrect" was explicitly interpreted as autosave in the chat; **no automatic
spelling correction or document rewriting was added**. This batch is complete
and uncommitted. Preserve all prior generation-status, GPU, TXT/PDF, native-drop
and documentation changes. Stop here for the user's go-ahead.

Trace: `editChanged` previously scheduled save plus review after 600 ms of idle
time; Ctrl+S called only `flushSave`, cancelling that timer without review. The
dirty flag was also cleared when a write was queued, so Saved could appear
before persistence. Continuous typing could postpone saving indefinitely.
Generate already re-prepared its input in the backend; the stale Spoken preview
was not evidence that generation reused that displayed preview.

Changes are confined to `frontend/src/App.svelte`, new regression coverage in
`tests/test_editor_save.cjs`, the built frontend output, and this handoff:

- Autosave after **one second of idle typing**, with an additional **five-second
  deadline during continuous typing**. These schedule save attempts; slow bridge
  responses or a blocked UI can delay persistence. Manual save and existing
  document-navigation/Generate flushes cancel both timers and use the same
  save-and-review path. They also drain edits made during pending work before
  returning, so a late response does not silently discard the newer working copy.
- Keep writes ordered; do not let an older saved snapshot overwrite newer editor
  text. Preserve unsaved edits and allow Ctrl+S retry after a failed save. Track
  pending writes separately: show Unsaved changes while waiting, Saving changes
  during writes, and Saved to your shelf after successful persistence.
- Every flush refreshes prepared text, including Ctrl+S with a pending write or
  no new write. Keep preparation outside the persistence queue so a slow preview
  does not prevent a newer save. Invalidate pending preparation on edits/settings
  changes; apply responses only for the current document, matching text and
  latest request. No audio regeneration on edits, and no mutation of existing
  recordings/jobs was added. The backend generation/preparation code is unchanged.
- Clear both autosave timers when the component is destroyed. This batch does
  not add a native close/save handshake; edits can still be lost if the app is
  closed or terminated before autosave or an explicit save completes.

Validation actually run:

- New built-frontend regressions use Node's test runner and existing bundled
  Playwright/Edge, a loopback static server, an in-memory disposable desktop API
  and virtual browser time. Against the unchanged pre-fix built frontend,
  **7/9 tests failed and 2 passed in 18.753 seconds**. Failures demonstrated the
  stale manual/retry/overlap preview, early Saved status, idle-timing mismatch,
  missing five-second continuous-typing save and stale preparation response.
  Navigation and Generate baseline checks passed. No app source was swapped.
- After implementation, **9/9 browser tests passed in 16.083 seconds**, with
  zero unexpected page errors. Coverage includes Ctrl+S cancelling both timers,
  the one-second idle boundary, continuous-typing deadline, pending-write status,
  ordered overlapping edits, late preview results, failed-save retry, navigation
  persistence, and Generate waiting for saves/receiving the current text. The
  Generate fixture captures the request and intentionally returns a fixture
  error; this is not speech-model inference or an audio comparison.
- Relevant backend document/speech-text/symbol-job/TXT/PDF suites:
  **58/58 in 14.959 seconds**. No full backend-suite rerun in this frontend-only
  batch; the earlier 242-test result belongs to the PDF batch below.
- Frontend production build passed in **18.64 seconds**; current asset is
  `index-Ccu07Co7.js`. Svelte check reported **zero errors and warnings**. Its
  initial npm wrapper/tool session lingered after output; a direct run of the
  installed checker, `node ./node_modules/svelte-check/bin/svelte-check
  --tsconfig ./tsconfig.json` from `frontend`, completed with **exit code 0** and
  the same zero-error/warning result. No dependencies were added or installed.
- Three real current-source pywebview/WebView2 checks passed, **zero page
  errors**, in a hidden app with a new disposable library: immediate Ctrl+S
  persists exact Unicode/emoji edits and displays real backend-prepared Spoken
  text; idle autosave persists and refreshes the real prepared text; navigation
  flushes pending edits and reopening reads the saved copy. The imported fixture
  file remained byte-identical. Expected speech text came from the actual
  backend `prepare` function. The fixture picker modal was stubbed, while real
  native keyboard/API callbacks, SQLite persistence and preparation ran.
  A hidden-window screenshot timed out; it is not counted as a visual pass.
- All **158 other pre-batch files** retained their hashes through validation
  (159 recorded files, only App.svelte changed). The new browser regression file
  was the only new repository file. This handoff was updated afterward.
  `git diff --check` passed.

No real user data/library was accessed, no actual speech-model inference,
model download, dependency change, EXE/MSIX rebuild, shortcut change or commit
occurred. Existing packaged copies still lack these refinements. Public vs
developer build separation, hiding Spoken, restricting `--debug`/preview entry
points, diagnostics sharing and custom-model policy remain separate work.

Reproduce browser regressions after a frontend build with
`node --test tests/test_editor_save.cjs`. Set `PLAYWRIGHT_MODULE` to an existing
Playwright module directory (this session used the Codex bundled runtime at
`C:\Users\fireball\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules\playwright`);
`BROWSER_EXECUTABLE` optionally overrides the existing installed Edge executable.
This is validation tooling, not a new application dependency.

Evidence:
`C:\Users\fireball\.codex\visualizations\2026\10\22\01a161f1-34e5-70e3-a0f8-919b05427c01\editor-save-20261022`
(`before-fix.log`, `after-fix.log`, `backend-focused.log`, `frontend-check.log`,
`frontend-build.log`, `implementation.diff`, `source-before.json`,
`source-after-validation.json`, `source-stability.json`, `expected.json`,
`launch-source.py`, `validate-native.cjs`, `native-validation.log`, `results.json`
and disposable fixture/library folders). Browser/native loopback checks and
Vite's previously sandbox-blocked realpath ran outside the restricted sandbox.
No automatic-approval rejection occurred. The Ctrl+S limitation documented in
the historical PDF section below is resolved in current source by this batch.

## Selectable-text PDF import — 22 October 2026

The user approved adding/installing pinned **pypdf 6.21.2**, without optional
extras, after discussion of its BSD-3-Clause license and alternative parsers.
This PDF implementation batch is complete and uncommitted. Preserve the prior
generation-status, TXT, GPU-usage, native-drop and documentation changes. Stop
here for the user's go-ahead. Older sections below describe earlier states;
their statements that PDF import was unimplemented are historical.

Trace and implementation:

- `backend/bridge.py`: add `.pdf` to the picker, native dropped batches and
  original-file reveal. Read a bounded source snapshot and convert extracted
  text through the existing literal-text Markdown working-copy path. Preserve
  source files, duplicate suppression, individual errors and the 32-file batch
  limit. Failed PDF imports do not create library documents; successful files
  in mixed batches remain imported. Markdown/TXT behavior remains covered.
- `backend/pdf_import.py`: use pypdf in a fresh spawned process, with strict
  parsing, no password entry or OCR. Reject encrypted PDFs even if an empty
  password could open them. Reject malformed/unsupported and entirely textless
  PDFs. Extract available text from mixed text/image PDFs in page order, join
  nonempty pages, and keep PDF punctuation/code/HTML literal in the editor.
  Images, scans and graphical content are omitted. Columns, tables, headers,
  font encodings and reading order still require review; there is no layout
  reconstruction or dehyphenation heuristic.
- Limits: **20 MiB source, 200 pages, 2 MiB extracted UTF-8 text and 2 MiB
  escaped editable Markdown**, with one extraction worker at a time. Each
  worker has a **20-second extraction deadline** and a monitored **512 MiB RSS
  threshold**. Terminate/join workers after completion, failure, timeout or
  excess memory. Return bounded JSON bytes through a pipe, without unpickling
  parser results or exposing raw parser exceptions to the UI. The memory
  threshold can be exceeded between samples; process separation is not an OS
  security sandbox. No source path is passed to the parser. Code inspection
  shows no PDF-action execution, external fetching, analytics or upload path
  added by this batch.
- `backend/documents.py`: parameterize only the literal converter's format
  label so PDF conversion overflow has accurate wording; TXT remains the
  default. No database schema, speech engine, model trust or runtime changes.
- `frontend/src/App.svelte`, `Home.svelte`, `FileDrop.svelte`: advertise
  Markdown/TXT/PDF. Imported PDFs carry a visible selectable-text/omitted-image
  and reading-order notice in Read, Edit and Spoken views, derived from their
  persisted source extension. The native File-object transport and its prior
  UI-thread response fix remain unchanged.
- `requirements.txt` and `requirements.lock.txt`: pin the exact pure-Python
  pypdf wheel by URL and SHA-256
  `1d44d1a3a200f25062adff0085b02040e4646431ac2ccac22e42679e91466084`.
  Only pypdf 6.21.2 was added to the existing project environment; all other
  distribution versions stayed unchanged. No extras/global installs.
  `packaging/Violilt.spec` now collects pypdf metadata. Retain its complete
  upstream license in `thirdparty/licenses/pypdf-6.21.2-LICENSE.txt`, provenance
  in that directory's README, and policy/limits in `thirdparty/PDF-IMPORT.md`.
  The existing notice assembler collects the installed license unchanged.

Validation actually run:

- Six initial `tests/test_pdf_import.py` regression methods failed before
  implementation: **8 assertion failures, zero errors**, demonstrating absent
  picker/drop/reveal support and absent PDF-specific rejection behavior.
  The final file contains **11 methods**, also covering extraction/conversion
  bounds, exact page/text boundaries, source admission independent of the
  smaller text limit, stalled/memory-limited/crashed workers, invalid responses,
  cleanup and successful retry. Resource tests use shortened deadlines/lower
  thresholds and a disposable stalled child; they do not allocate 512 MiB.
  Source-boundary admission isolates extraction with a double; it does not
  claim to parse a real 20-MiB PDF. Real generated PDFs cover extraction and
  the exact 200/201-page boundary. Tests use no personal library/document.
- Final focused PDF/TXT/native-bridge suite: **26/26 in 8.658 seconds**.
  Full backend suite: **242/242 in 32.900 seconds**, including the preserved
  generation-status and GPU tests. `npm --prefix frontend run check`: **zero
  errors/warnings**. Frontend production build passed in **6.19 seconds**;
  current asset is `index-AQPVyTU3.js`. Existing dependencies were used.
- Real current-source pywebview/WebView2 app, with a fresh disposable library,
  passed **six native checks**, **zero page errors**: picker advertises PDF/TXT
  and imports a two-page Unicode/literal PDF; edit/autosave/spoken preparation
  and the notice in all views; disk-backed native PDF drop clears the overlay;
  scanned/encrypted/malformed drops show errors without shelf mutation; UTF-16
  TXT still works without a PDF notice; mixed Markdown/PDF drops retain both
  successes and report the failed PDF while clearing the overlay. Native
  `CoreWebView2File` objects and callback IPC were real. The OS picker modal was
  replaced with a fixture selection, and drop events used CDP-selected disk
  files. Actual Explorer mouse gestures and the real modal were not exercised.
- Disposable PDF fixtures were generated with existing bundled ReportLab;
  both selectable PDF pages were rendered with Poppler and visually inspected.
  A native PDF reading screenshot was also inspected. Captures on subsequent
  hidden-window runs timed out; these are retained as evidence limitations,
  not counted as successful screenshots. DOM/IPC assertions still passed.
- The notice assembler ran into disposable output: **69 package records,
  177 notice files, no missing notice evidence**. Its pypdf license hash matches
  both the approved wheel and the checked-in complete license. This is a
  collection check, not a new blanket release-clearance claim.
- Of 155 recorded pre-batch repository files, **146 retained their hashes
  through validation**; the nine changes were the intended shared import/UI,
  requirements/spec and license-provenance files. Existing generation-status,
  GPU, native-drop and package-validation files retained their hashes. This
  handoff was updated afterward. `git diff --check` passed.

Observed limitation outside this PDF change: invoking **Ctrl+S before the
600-ms autosave review** saved the edit but left the Spoken preview stale in
the native check. The unchanged shared handler invokes `flushSave`, which
cancels the pending review timer without calling `review`; that code trace
indicates a pre-existing editing issue. Its presence on an older executable
was not tested. Reopening the reading runs review. Normal autosave passed the
native PDF check. This limitation was reported to the user and left for a
separate approved batch. Earlier fixture runs also had a wrong button locator
and an expectation that ignored existing speech-symbol spacing/Markdown
escaping; those were test-harness corrections, not additional app fixes.

No speech-model inference, model download, frozen-worker test, portable/MSIX
rebuild, installed-package validation, shortcut change or commit occurred.
**All existing EXEs/MSIX artifacts still predate these source refinements.**
For manual source testing, build the frontend and launch the project Python
with an explicitly disposable `--data-dir`; do not infer current behavior from
the old shortcuts. Diagnostics sharing, custom-model policy/support and OCR
remain separate unresolved/planned work.

Evidence and reproducible helpers:
`C:\Users\fireball\.codex\visualizations\2026\10\22\01a161f1-34e5-70e3-a0f8-919b05427c01\pdf-import-20261022`
(`before-fix.log`, `focused-final.log`, `full-suite.log`, `frontend-check.log`,
`frontend-build.log`, `make-fixtures.py`, `launch-source.py`,
`validate-native.cjs`, `native-validation.log`, `results.json`,
`results-ctrl-s-preview.json`, `native-file-objects.jsonl`,
`native-pdf-reading.png`, `fixture-page-1.png`, `fixture-page-2.png`,
`pypdf-release.json`, `stability-and-notices.json`, `source-before.json`,
`packages-before.json`, disposable `notices/` and per-run fixture libraries).
Initial harness/screenshot failures are retained separately. Tests requiring
loopback/junction access, Vite's prior sandbox-blocked realpath, and the native
hidden app ran outside the restricted sandbox; no automatic-approval rejection
occurred. Stop after this batch for the user's go-ahead.

## Native drop recovery and old shortcut diagnosis — 22 October 2026

The user reported a drop overlay that never settled and an import picker that
still listed only Markdown, and asked whether an old shortcut was involved.
Both causes were traced: the shortcuts target an old build, and the current
source also contained a native drop-response threading bug. This small fix is
complete and uncommitted. Preserve all prior TXT, generation-status, GPU-usage
and documentation edits. Stop after this batch for the user's go-ahead.

Shortcut evidence (read only): both
`C:\Users\fireball\OneDrive\Desktop\Violilt.lnk` and
`C:\Users\fireball\OneDrive\Desktop\LiltTTS\Violilt.lnk` target
`dist\pronunciation\Violilt\Violilt.exe`, without arguments. That executable
is dated **21 October 2026, 22:04:40 Istanbul time**; its bundled frontend is
`index-BEvnxnXg.js` and still contains Import Markdown. The current source and
`frontend/dist` use Import document and the Markdown/TXT filter. Neither
shortcut nor executable was changed. The next artifact batch should build a
fresh output and validate it before repointing shortcuts; no rebuild/install
was done here. PDF import remains unimplemented, so PDF should be rejected
clearly rather than appear in the picker or leave an active import overlay.

Reproduction and fix:

- A hidden current-source app with a new disposable library reproduced the
  stuck drop using real disk-backed WebView2 `CoreWebView2File` objects. The
  import worker completed its library work, then read
  `control.CoreWebView2.Source` from the background thread. WebView2 threw
  `InvalidOperationException: CoreWebView2 can only be accessed from the UI
  thread`, preventing the JavaScript callback and leaving importing active.
- `backend/desktop.py`: keep file import on the worker, but post response
  delivery through the WinForms control's `BeginInvoke` using the existing
  .NET `Action` delegate. Read/recheck the page origin and call
  `CoreWebView2.ExecuteScriptAsync` on the UI thread. Do not call pywebview's
  synchronous `run_js` there: its result wait would block that same thread.
  Existing request IDs, native File-only transport, explicit method contract,
  origin/navigation restrictions and CSP remain enforced.
- `tests/test_desktop.py`: three new regressions cover successful and rejected
  response delivery without worker access to UI properties, nonblocking script
  dispatch and a fresh origin check after dispatch is queued. Update the
  existing native-transport double for asynchronous UI delivery. All three
  new methods failed on assertions before the code fix (seven total tests,
  three failures, zero errors), then the focused suite passed **7/7 in 0.095
  seconds**. Final full backend suite: **231/231 in 26.065 seconds**.
- The real source app/native bridge passed four checks after the fix: the
  picker bridge passes the TXT filter and imports its fixture selection;
  BOM-marked UTF-16 TXT crosses the native File-object drop transport and
  clears the overlay; unsupported PDF shows a format error and clears the
  overlay; a mixed Markdown/PDF drop keeps the Markdown success and reports
  PDF rejection. **Zero page errors**. The final screenshot was inspected.

Native verification used existing pywebview/WebView2 and Playwright/CDP, with
debug instrumentation and a fresh disposable profile on every run. The OS
picker modal was replaced by a fixture selection, while the real Bridge and
native IPC ran. Drop events were injected using CDP-selected disk files; an
actual Explorer mouse-drag gesture was not performed. The first remote
Playwright upload created memory-backed Files, which WebView2 rejected with
an error while correctly clearing the overlay; switching the fixture to
`DOM.setFileInputFiles` reached the native transport and exposed the real
threading bug. Initial unsuccessful evidence is retained.

No personal libraries/documents/audio were read or changed, no model download
or inference occurred, and no dependency, frontend source, runtime/model pins,
commit or package/shortcut change was made. Frontend check/build were not
repeated for this Python-only fix; the previously built current frontend ran
in the native check. `git diff --check` passed. Packaged copies still lack
the new source refinements and this fix. Actual OS picker/drag gestures and
the rebuilt executable remain validation work for the next artifact batch.

Evidence and reproducible helpers:
`C:\Users\fireball\.codex\visualizations\2026\10\22\01a161f1-34e5-70e3-a0f8-919b05427c01\native-import-20261022`
(`launch-source.py`, `validate-native.cjs`, `before-fix-desktop.log`,
`after-fix-desktop.log`, `full-suite.log`, `results-native-before-fix.json`,
`validation-after-fix.log`, `results.json`, `native-file-objects.jsonl`,
`native-mixed-drop.png`, and per-run `app-*.log`). Only disposable libraries
and fixture files are under this evidence directory.

## TXT document import — 22 October 2026

The user approved TXT import as the first planned-additions batch, with UTF-8
(optional BOM) and BOM-marked UTF-16 in either byte order. This batch is complete
and uncommitted. PDF/OCR, diagnostics and custom models remain separate work.
The existing generation-status changes, package-validation documentation and
the separately completed CPU/GPU usage work below were preserved.

Trace and implementation:

- `backend/bridge.py`: accept `.txt` alongside `.md`/`.markdown` in the picker,
  dropped batches and original-file reveal. Decode TXT strictly as UTF-8 or
  BOM-marked UTF-16; reject malformed encoding, UTF-32 and NUL-containing input
  with encoding guidance. No legacy-codepage guessing. Existing Markdown
  decoding remains UTF-8 with optional BOM. Keep duplicate suppression,
  per-file errors, the 32-file batch limit and untouched source files.
- `backend/documents.py`: convert TXT once into the existing editable Markdown
  working-copy format. Escape punctuation and protect leading indentation so
  headings, frontmatter, code fences, HTML/script/style text, links, entities
  and tables stay literal rather than being interpreted or omitted. Normalize
  CRLF/CR to LF and retain paragraph breaks. The original file is unchanged;
  later working-copy edits use the existing Markdown editor and save flow.
  Existing speech symbol/pronunciation policies still apply.
- Both the source file and converted UTF-8 working copy must fit within the
  existing **2 MiB** limit. Escaping or UTF-16-to-UTF-8 expansion can therefore
  require splitting a TXT file whose original bytes fit the source limit.
  Reject oversize conversions before parsing or library mutation. No database
  schema, model/runtime trust, dependency or speech-worker changes were needed.
- `frontend/src/App.svelte`, `frontend/src/Home.svelte` and
  `frontend/src/FileDrop.svelte`: use Import document and generic reading labels,
  advertise Markdown/TXT and include `.txt` in the drop overlay. Preserve the
  generation-status and CPU/GPU Performance details implementations.
- `tests/test_text_import.py`: eight disposable-fixture regressions cover the
  picker and Unicode encodings, literal spoken/chunk content, save/reload,
  original-file reveal after edit/restart, mixed drops and source preservation,
  malformed/unmarked encodings, empty text, paragraph normalization, source and
  conversion limits, and exact 2-MiB/32-file boundaries. Native dialogs and
  Explorer are test doubles; no personal library or real user document is used.

Validation actually run for this batch:

- Before implementation, all seven initial regression methods failed on the
  unchanged code (20 assertion failures across subtests, zero errors). After
  adding the exact-boundary method, all eight failed against the original
  `backend/bridge.py` and `backend/documents.py` loaded into memory using
  read-only `git show` (21 assertion failures, zero errors). Their original
  hashes matched the pre-batch files; no workspace source was restored/swapped.
- The focused eight-test suite passed in **1.641 seconds**. After coordination
  with the other chat, the final full backend suite passed **228/228 in 27.448
  seconds**, including the completed GPU-usage and generation-status tests.
  Final `npm run check`: **zero errors/warnings**. Final `npm run build`: passed
  in **6.17 seconds** using existing dependencies.
- Existing headless Edge/Playwright checked the actual built frontend with a
  synthetic in-memory bridge and output from real backend imports in a
  disposable library. Five checks passed: import labels; literal TXT rendering
  (including HTML/code/links/entities/tables/Unicode); saved-copy editor and
  spoken preview; TXT drop overlay/mixed-error handling; normal Markdown
  headings/emphasis. Zero page errors. Reading/drop screenshots were visually
  inspected. The first harness lacked the `generate` bridge stub required for
  frontend initialization; correcting that fixture resolved its timeout.
- All **155 recorded repository files** retained their pre-validation
  hashes through the final checks. The original `backend/speech.py`,
  `tests/test_generation_status.py` and package-validation report also retained
  their pre-TXT hashes. Only this handoff was updated after validation.
  `git diff --check` passed.

Earlier attempts remain recorded, not passing final results: the restricted
backend run hit five loopback/junction errors and one junction skip; Vite hit
the previously recorded `EPERM` resolving `frontend/index.html`. The same
checks ran outside that sandbox with disposable fixtures. A subsequent run
overlapped the other chat's then-incomplete GPU work and reported nine assertion
failures in its five new GPU tests. TXT work paused, the user confirmed the
other work was paused, and final validation was rerun on the stable completed
tree. No automatic-approval rejection occurred.

Limits: this batch did not run the native file picker/drag transport, actual
speech-model inference, a portable/MSIX rebuild or installed-package tests.
The browser bridge is a fixture, and speech preparation checks do not establish
native end-to-end TXT generation. Existing executable/MSIX artifacts still
predate these refinements. No dependency installation, commit, backup,
analytics/upload feature or personal-data access was performed.

Evidence and reproducible browser/counterfactual harnesses:
`C:\Users\fireball\.codex\visualizations\2026\10\22\01a161f1-34e5-70e3-a0f8-919b05427c01\txt-import-20261022`
(`before-fix.log`, `run-pre-fix.py`, `before-fix-all-eight.log`, `after-fix.log`,
`full-suite-final.log`, `frontend-check-resumed.log`,
`frontend-build-resumed.log`, `validate-ui.cjs`, `ui-fixture.json`,
`ui-validation-final.log`, `ui-results.json`, `txt-reading.png`, `txt-drop.png`,
`source-before.json`, `source-before-final-validation.json`,
`source-stability.json`). Stop after this batch for the user's go-ahead.

## CPU/GPU usage display — 22 October 2026

The user explicitly asked this chat to trace, plan, then implement GPU usage
alongside CPU usage. This approved batch is complete and uncommitted. The tree
already contained generation-status changes and separate TXT-import edits in
`backend/bridge.py`, `backend/documents.py`, `frontend/src/App.svelte`,
`frontend/src/FileDrop.svelte`, `frontend/src/Home.svelte` and
`tests/test_text_import.py`; those edits were preserved.

Trace: existing CPU usage measures the speech worker and normalizes across all
logical CPU processors. There was no GPU utilization reader. The selected
configuration can describe the next reading, so it cannot identify the provider
actually running the current job. The implementation uses the active job's
engine and live worker PID instead.

Changes:

- `backend/gpu_usage.py`: optional Windows PDH GPU Engine counters via stdlib
  ctypes, loading `pdh.dll` from System32 only. Query instances are scoped to
  the worker PID. Report the busiest valid GPU engine, excluding other PIDs,
  invalid/nonfinite/out-of-range samples and unavailable data. This is worker
  utilization, not total device utilization or an estimate of CUDA core load.
- Sample in a daemon thread about once per second; bridge reads do not wait for
  native sampling. Hide samples older than three seconds, discard results from
  a replaced worker/query, close counters on target changes and after five
  seconds without UI polling. Missing counters/unsupported platforms remain
  optional and return null, distinct from a measured 0%. Windows' no-instance
  and invalid-first-rate-sample statuses wait for subsequent samples instead of
  permanently stopping sampling as a new GPU context is created.
- `backend/performance.py` and `backend/jobs.py`: expose nullable `gpu_percent`
  for the active GPU job's worker. CPU jobs, idle/dead workers and legacy jobs
  without engine metadata stop GPU sampling. Pending settings for the next job
  do not change the current reading's measurement.
- `frontend/src/api.ts`, `frontend/src/App.svelte`, `frontend/src/styles.css`:
  retain generation speed, first-audio time and ready audio in the main status;
  move CPU usage and add GPU usage under expandable Performance details. GPU
  values appear only for an active CUDA/DirectML job with a real measurement.
  Hide unavailable values and the details entirely when neither reading exists.
  Tooltips explain the worker scope. Measured 0% remains visible.
- `tests/test_gpu_usage.py`: integration, native-array parsing/status handling,
  bounded buffers, PID filtering, sample freshness, asynchronous publication and
  cleanup coverage. `tests/test_model_memory.py` updates its status test double
  to accept the active-engine keyword. This handoff records the batch.

Validation:

- The first five integration tests failed against the pre-batch code (nine
  assertion failures across subtests), then passed. The focused suite now has
  **17 passing tests**. Live testing exposed the invalid-initial-rate edge case;
  its additional regression failed on all six stage/status cases before the
  correction, then passed. The final full backend suite passed **228 tests in
  34.040 seconds**, including the existing TXT-import tests.
- `npm run check` reported **zero errors/warnings**, and the production frontend
  build passed in **9.40 seconds**. The check's tool-shell session lingered after
  displaying the successful diagnostics and was interrupted afterward. An
  initial Svelte const placement error was corrected before the successful
  check/build.
- Existing headless Edge/Playwright tested the built UI with a synthetic bridge:
  **11 checks passed**, zero page errors, including collapsed/expanded details,
  both readings, null versus measured 0%, current-job versus next-device
  selection, and the earlier generation-status/error-recovery behavior. CPU/GPU
  screenshots were visually inspected; these UI readings were fixtures.
- Separately, the real sampler observed a disposable CUDA speech process using
  existing verified model/runtime fixtures: **49 readings, 39 nonzero, highest
  30.1%**, with no counter errors in the final run. All four actual generated
  WAVs passed mono/24-kHz/finite/nonzero sample checks. No human listening test
  or controlled performance benchmark was performed. The first harness watched
  the venv launcher instead of the actual Python PID; that fixture was corrected.
  Subsequent live diagnosis identified and fixed the initial-rate-status bug.
  Windows counter access was unavailable in the tool sandbox but worked outside
  that sandbox; no administrator configuration or counter repair was needed.
- `git diff --check` passed. No dependencies were added/installed, no model/runtime
  pins changed, no analytics/upload feature added, no personal libraries or real
  user data accessed, and no commit or portable/MSIX rebuild performed. Existing
  packaged executables still predate these refinements. Other GPU/driver/OS
  combinations and installed-MSIX behavior remain untested for this change.

Evidence, harnesses and disposable audio are outside the project at
`C:\Users\fireball\.codex\visualizations\2026\10\21\01a15fcf-c186-7223-9ac8-b727e17c3402\gpu-usage-20261022`:
`before-fix.log`, `before-context-fix.log`, `after-fix.log`,
`full-suite-final.log`, `validate-ui.cjs`, `ui-results.json`,
`gpu-details.png`, `cpu-details.png`, `validate-native.py`,
`native-results-context-fix.json`, `native-gpu-audio-context-fix/`.
Earlier unsuccessful live-run evidence is retained alongside the final run.

Implementation references:
[PDH language-neutral counters](https://learn.microsoft.com/en-us/windows/win32/api/pdh/nf-pdh-pdhaddenglishcounterw),
[wildcard arrays](https://learn.microsoft.com/en-us/windows/win32/api/pdh/nf-pdh-pdhgetformattedcounterarrayw),
[rate sampling](https://learn.microsoft.com/en-us/windows/win32/perfctrs/collecting-performance-data),
[Microsoft's busiest-engine explanation](https://devblogs.microsoft.com/directx/gpus-in-the-task-manager/).
Stop after this batch for the user's next instruction; the planned additions
and release gates below remain separate work.

## Planned additions and next-chat scope — 22 October 2026

After completing the generation-status refinement below, the user discussed
three further additions and asked that all plans be recorded for the next
implementation chat. The user subsequently chose the TXT portion as the first
batch, completed above. The remaining implementation order and open design
choices below are not settled.

1. **Performance diagnostics to improve later releases.** Useful proposed
   fields are broad CPU/GPU/RAM specifications, app/runtime/provider versions,
   model-loading and first-audio timings, generation speed, memory usage and
   structured failure codes. Exclude reading text, audio, file paths and
   persistent device IDs. The recommendation is to ask once with Enable / Not
   now, keep sharing off until the user explicitly agrees, and provide a
   Settings toggle and report preview. Start with local reports/exports;
   automatic sending needs a chosen endpoint, retention policy and disclosure.
   These are recommendations, not finalized user decisions. Existing hardware
   detection, saved benchmark results and per-job generation timings are local;
   no app-written analytics uploader was found. ONNX Runtime/WebView2 vendor
   diagnostics are separate and remain part of the privacy-release review.
2. **Additional/custom model support.** The user wants to explore importing
   models for testing and speech generation. Current Use existing files only
   accepts the exact approved Kokoro model/voice bytes, with an optional approved
   GPU model, through `backend/models.py` and `backend/model_trust.py`. It does
   not support arbitrary models. Define supported model families/formats,
   voices/tokenization, CPU/GPU compatibility and the custom-model trust policy
   before implementation. Do not silently bypass existing approved-model pins.
3. **TXT and PDF document import.** TXT alongside Markdown is now implemented
   as recorded above, with approved Unicode encodings and existing limits.
   PDF remains unimplemented. Selectable-text PDFs first, with scanned PDFs/OCR
   considered separately, was the assistant's recommendation; the user has not
   decided OCR scope. Confirm extraction/reading order, PDF import limits and
   any required dependency before implementation. Reuse disposable fixtures
   and protect existing Markdown/TXT behavior.

Suggested workflow: a new implementation chat in this project, with this chat
reserved for independent verification after each finished batch. Do not run
overlapping implementation/testing work on the shared checkout. The user has
not asked the agent to create a new chat. Preserve current uncommitted changes,
work one item per batch, add a regression test that fails without the change,
run relevant checks, update this handoff, then stop for the user's go-ahead.
No commits or new dependencies without explicit authorization; no personal
libraries or real user data. The earlier backup requirement was explicitly
waived by the user. Existing release gates below remain open.

## Generation status refinement — 22 October 2026

The user requested visible model-loading and actual-generation status as the
first feature refinement. This batch changes `backend/speech.py`,
`frontend/src/App.svelte`, adds `tests/test_generation_status.py`, and updates
this handoff. It remains uncommitted. The earlier package-validation report
and handoff edits were already present and were preserved.

Generate now immediately shows a disabled "Preparing your reading…" button
while its request is pending. The worker reports "Loading model…" immediately
before actual engine construction; "Model loaded" and "Generating audio…"
appear only after loading succeeds, just before inference. A warm engine avoids
a false loading message. Saved-audio reuse stays in preparation and names the
reuse; assembly shows "Saving recording…". Stopping during model loading now
checks cancellation before beginning inference. No state/schema/dependency
changes or telemetry collection/upload were added.

All five new worker tests failed against the original implementation, then
passed after the change. They cover cold-load/inference ordering, warm reuse,
load failure, saved-section reuse, and cancellation while loading, using only
disposable files and synthetic audio with a stubbed engine. The full backend
suite passed **203 tests in 25.715 seconds**. `npm run check` reported **zero
errors/warnings**; `npm run build` passed in **6.61 seconds**. Vite initially
hit a sandbox `EPERM` reading `frontend/index.html`; the unchanged command
passed outside that restricted sandbox using existing dependencies.

An existing headless Edge/Playwright installation checked the actual built
frontend against a synthetic in-memory bridge: pending button, loading,
generation/model-ready label, assembly, saved-audio display and rejected-request
recovery all passed, with zero page errors. Loading/generating screenshots were
visually inspected. An initial harness selector matched two Reading room
buttons; scoping it to Main navigation resolved that harness-only failure.
These are source-worker and browser-fixture tests; native model inference and
the portable/MSIX build were not rerun for this refinement. Evidence and the
reproducible UI harness are outside the project at
`C:\Users\fireball\.codex\visualizations\2026\10\21\01a15fcf-c186-7223-9ac8-b727e17c3402\generation-status-20261022`
(`before-fix.log`, `after-fix.log`, `full-suite.log`, `validate-ui.cjs`,
`ui-results.json`, `loading.png`, `generating.png`). `git diff --check` passed.

The user also asked about improvement diagnostics. Suggested direction only:
opt-in local reports with broad hardware specs, app/runtime/provider versions,
model-load/first-audio timing, generation speed, memory and structured failure
codes, excluding reading text, audio, file paths and persistent device IDs.
Collection fields, consent/preview/export, retention and any upload destination
remain undecided; no collection feature is implemented. Stop after this batch
for the user's next instruction. The previously validated executable/MSIX below
remain artifacts of `bbe961f` and **do not contain this refinement**. Earlier
release gates remain open.

## Current package validation — 22 October 2026

The user committed the four follow-up batches as
`bbe961f4af81046f8ea76ad5fc04124e1a62068a` (`Harden recovery, packaging, and GPU
runtime loading`), then approved rebuilding and validating the CPU/GPU package.
The checkout was clean when validation began. All 150 tracked files retained
their exact pre-build hashes through build and runtime execution; only this
handoff and the validation report were updated afterward. No application-code
fix, dependency installation, commit/push or personal-library access was needed.

**Rebuild and functional validation passed.** The backend suite passed 198 tests
in 26.056 seconds; Svelte/TypeScript reported zero errors/warnings, and the
production frontend build passed. The canonical CPU/GPU build, model/runtime
pin checks and actual executable audit passed (2,335 frozen modules, 1,146
files, zero violations). The new unsigned x64 compatibility MSIX is version
**1.0.3.0**, with 1,151 mapped files plus two standard package metadata entries.
Every mapped file's size/hash, all three model pins, all 371 runtime pins and
the isolated MSIX profile were verified inside the archive.

Actual speech generation passed in the new portable executable and in the
verified MSIX's extracted App payload on both CPU and CUDA, with caching off.
A separate disposable copy with no GPU add-on also generated CPU speech.
GPU workers loaded the bundled CUDA provider and appeared in NVIDIA's compute
process list. All five WAVs passed PCM16/24-kHz/mono/nonzero/finite validation;
muted playback advanced, and documents/settings/jobs/listening position survived
full app restarts. All portable and extracted MSIX files remained unchanged.

Current artifacts:

- [Executable](C:/Users/fireball/OneDrive/Desktop/LiltTTS/dist/validation-bbe961f-20261022/Violilt/Violilt.exe)
- [Unsigned MSIX 1.0.3.0](C:/Users/fireball/OneDrive/Desktop/LiltTTS/dist/validation-msix-bbe961f-20261022/Violilt-MsixCompatibility-1.0.3.0-x64.msix)
- [MSIX inventory](C:/Users/fireball/OneDrive/Desktop/LiltTTS/dist/validation-msix-bbe961f-20261022/inventory-1.0.3.0.json)
- [Detailed validation, hashes, timings and limitations](C:/Users/fireball/OneDrive/Desktop/LiltTTS/docs/package-validation-2026-10-22.md)

The executable SHA-256 is
`38640646e3f302981e0a749639d29e2ab605984dcc189e297e7eaec99adab63a`.
The MSIX is 2,253,573,807 bytes, SHA-256
`beaab443310cd2f1dc11afa817f14b1839e85647bc8435d30374a87269b88e92`.
Evidence, synthetic libraries and helpers are outside the project at
`C:\Users\fireball\.codex\visualizations\2026\10\21\01a15fcf-c186-7223-9ac8-b727e17c3402\package-validation-20261022-bbe961f`.

**Still open:** installation under real MSIX identity, installed permissions/
ACLs, worker/media/file access under that identity, update/uninstall testing,
low-end/physical no-GPU testing and controlled startup/first-audio profiling.
The current session is not Administrator; the unsigned installer was checked
only with `-WhatIf`, which passed. No package/certificate was installed. Tests
used `--debug` with local-only CDP instrumentation; debug-off execution and human
audio-quality review were not rerun. Observed startup was 18.9–28.6 seconds and
first audio 12.8–21.6 seconds in these instrumented, partly concurrent runs;
these timings need profiling, not a blanket performance pass. Existing license,
privacy, Store identity and certification gates remain. Feature refinements
require their own requested batch; this validation batch is complete.

## Earlier follow-up — all four approved implementation batches completed

Updated 21 October 2026 after the independent verification review. Baseline is
`2b0f4d1c9efeca71eb31f5d9c5c6e48265296aef` (`Changed icon`), following the committed
security work in `72974c8`. The tree was clean before batch 1. The agent left
these changes uncommitted at each batch boundary; the user subsequently
committed all four batches as `bbe961f`. No agent commit or push was performed.

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

These implementation batches were completed before the current package
validation, with the changes committed afterward by the user. Full restore UX,
broader schema/recovery review and installed update/recovery testing
are still open; batch 1 addresses the reproduced S-05 failures and related field
validation, not universal corruption recovery. Batch 2 validates the bytes during
mapping preparation; it does not make the source directory immutable during a
subsequent MakeAppx run. Runtime byte verification does not establish immutable
directory permissions or eliminate concurrent file-replacement races. The fresh
build and extracted-package CPU/GPU inference checks have now passed as recorded
at the top. Installed ACL/DLL-search and inference verification under actual
MSIX identity remain open. Artifact paths and runtime results in the earlier
release section below are historical; use the current artifact paths above.

## Earlier release implementation and evidence

Prepared 21 October 2026. **The first security implementation pass is complete and tested; public-release gates remain open.** Resume from the combined checklist rather than restarting the original investigation.

## Workspace and working rules

- Workspace: `C:\Users\fireball\OneDrive\Desktop\LiltTTS`; PowerShell on Windows.
- Branch: `pronunciation-replacement`; validated HEAD: `bbe961f4af81046f8ea76ad5fc04124e1a62068a`. The original investigation compared against `c8acbab63643871c59c372b43ae1c6697f8e2904`.
- Rebranding, prior release tooling and the first security pass were committed in `72974c8`; icon/favicon changes followed in `2b0f4d1`, then the four follow-up batches in `bbe961f`. The latest validation changed documentation only; no new commit was made. Preserve local changes; do not reset/revert the tree.
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

The [original security investigation](C:/Users/fireball/OneDrive/Desktop/LiltTTS/docs/security-investigation-2026-10-21.md) is a **pre-fix historical baseline**. Its statement that application code was unchanged describes that investigation, not this implementation pass. The initial Store plan/findings also contain dated assumptions and older package evidence. The earlier release artifact below was **1.0.2.0**; the current tested archive is **1.0.3.0**, linked at the top.

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
