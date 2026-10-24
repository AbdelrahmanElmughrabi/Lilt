# Violilt release readiness

Continuation notes: [handoff](HANDOFF.md).

> **Current checkpoint — 24 October 2026:** [Source and release status](release-source-status.md)
> controls the current source acceptance and commit map. Dated entries below retain
> their historical scope. R-03/R-05 current batches are finished; R-05 source fixes
> have scoped passes. Outstanding reviews/dispositions, R-04 rights, R-05 notices
> and final-package/installed gates remain. Do not repeat accepted unchanged work
> or interpret every missing build fact as an automatic product defect.

**Current coordination — 23 October:** All three returned R-02 findings now have locally validated corrections: [cache/save-close](r02-cache-fix-results-2026-10-23.md), [removal/retry](r02-removal-retry-results-2026-10-23.md), and [navigation-helper acceptance](r02-navigation-helper-results-2026-10-23.md). [Combined independent review](r02-corrections-independent-verification-prompt.md) is pending; R-01/R-02 are not accepted as complete. Product/frontend/assets were unchanged in the last tooling batch. Prior snapshots remain preserved with explicit drift. Argon is off the project; R-11 correction/review/future assignment remain open. This coordinator owns the checklist; the previous validation chat remains independent. [R-05 investigation/draft](r05-results-2026-10-22.md) remains available for its recorded snapshot, with final privacy checks/review and website preparation open/deferred. HEAD remains `eda83ed`. R-03 engineering stays paused; actual final-MSIX testing on another machine is mandatory.

**R-03 is paused at the publisher's request.** [Complete paused handoff](r03-paused-handoff-2026-10-22.md), [new-chat prompt](r03-new-chat-prompt.md). Documentation/snapshot bookkeeping only was authorized after the pause. Expat coverage, cleanup/GPU deadline findings and independent acceptance remain open. OneDrive functionality is disabled; do not use its folder name as a cause. The new pause checkpoint covers root build inputs omitted from the earlier update manifest. No final EXE/MSIX validation or publication approval follows from these records.

Updated 23 October 2026. This combines the [release plan](ms-store-release.md), [security investigation](security-investigation-2026-10-21.md), and subsequent release review. The investigation remains historical evidence; this checklist tracks the work that follows it. Release scope: x64 Windows desktop MSIX, proprietary Violilt code, local English TTS, CPU and optional NVIDIA GPU support, Store-delivered updates. Pricing remains undecided; free without ads is the recommendation, not a final publisher decision. No ads or payments are being added.

## Working method

For every item: **trace → plan → implement/investigate → validate → record**. Trace the current code, dependency versions, artifact and existing evidence first. State the intended change and acceptance checks before editing. Retest the changed boundary and relevant real workflow. Record the result, remaining limits and exact build where applicable. A passing source test is not installed-package evidence. Preserve personal libraries and existing unrelated changes.

After every completed R item, provide a batch report and copyable independent-review prompt, record exact inputs/evidence, and update the [reusable review handoff](release-review-handoff.md). The publisher sends it to the review chat and returns the report here. Continue independent next-item work while review is pending; preserve or coordinate overlapping source/dependency inputs and never silently mix snapshots. Keep implementation/local validation separate from independent acceptance and release approval. Reconcile returned findings, validate fixes and issue a new review revision where needed. No automatic cross-chat messages are authorized.

Status: **passed** means evidence exists for the stated scope; **confirmed issue** means reproduced or established by inspection; **open** means not yet verified; **publisher action** means an external account/product action is required. No public submission or publication is authorized by this checklist.

## Release priorities agreed 22 October 2026

This section controls the current sequencing and distinguishes release gates from improvements that can wait. Earlier test/build results remain evidence for their recorded revisions, not approval for the current package. These are project release gates; Microsoft certification is a separate decision.

### Execution order — finish the application before the final build

The publisher wants required application improvements finished and reviewed
before producing the release candidate. R numbers identify work groups; they
are not an instruction to build at R-06 before addressing R-11 application work.

| Priority | Work and completion boundary |
| --- | --- |
| 1. Fix known application blockers | All three returned R-02 findings are corrected and locally validated. Complete combined independent R-01/R-02 review and reconcile any findings before closing that gate. The separate P3 native destroy-error wording remains deferred. Argon is off the project; previous R-11 correction/review and future assignment remain open. |
| 2. Finish required version-1 source work | Complete reviewed R-11 keyboard/focus/usability corrections and any necessary performance work, then chosen R-05 diagnostic/log controls and notices. Resolve R-04 obligations that affect shipped inputs before freezing them. R-03 runtime/security and unexplained tests must also receive a supported disposition and independent acceptance before selecting final release inputs, but its engineering remains paused until the publisher resumes it. Unaffected source work can continue during that pause. |
| 3. Validate and freeze the release inputs | Complete appropriate source checks and independent reviews; reconcile returned findings. Confirm production identity/version and required package configuration. Record the exact reviewed source, dependencies, models, assets and build configuration. Source preparation may exercise R-07 feature cases, but cannot close its package gate. |
| 4. Build the candidate | R-06: produce fresh EXE/MSIX outputs from those fixed inputs, with inventories, hashes and payload audit. Aim for one planned candidate build after known changes; rebuild if actual package defects or required input changes demand it. No build is authorized by this ordering note. |
| 5. Validate those exact outputs | R-07 final-package features, R-08 installed behavior, R-09 updates/data lifecycle and mandatory R-10 actual final-MSIX testing on another machine. Include applicable final R-05 privacy/ACL, R-11 performance/accessibility and R-12 certification checks. Keep low-end/no-GPU and supported NVIDIA evidence as needed. |
| 6. Finish submission readiness | Finalize verified privacy/support pages, listing, price/markets and publisher requirements; reconcile every remaining gate and request publication authorization. Exact production identity is needed before the final MSIX; website publication can be prepared later, before submission. |

Parallel preparation: R-04 rights/provenance, R-05 investigation review, test-case
preparation, hardware arrangements and publisher/account/listing decisions can
advance without shared product edits. Website hosting does not block source
improvements. Optional feature expansion and nonessential polish can follow
release unless a finding establishes a blocker; the plan is not an open-ended
redesign. Preserve prior evidence and avoid changing inputs under review.

**Current next acceptance step: independent review of the completed R-02 corrections.**
All three returned findings are locally corrected; use the [combined review prompt](r02-corrections-independent-verification-prompt.md). Local checks do not close R-01/R-02 or any package/release gate.
R-05 remains available for its historical snapshot; its runtime/control batch
is a later action. Argon is off the project; previous R-11 work needs review and future assignment.
R-03 remains paused. This prioritization changes no authorization or gate status.

For the first R-02 correction, use the [cache failure problem and resolution plan](r02-cache-failure-plan-2026-10-22.md):
deliberate fault injection exposed an optional-dependency/error-boundary defect;
normal caching was not established to be broken. Engineering order is reproduce
and define responsibilities → correct cache isolation and save/refresh separation
→ complete truthful fallback/recovery → validate actual workflows and independently
review. Design regression checks before edits. Harden acceptance tooling before
relying on it; message polish follows behavioral correctness. The resolution
record now links the locally validated correction; independent acceptance remains pending.

Step 1 now has a [fresh current-code trace and visible baseline](r02-cache-baseline-2026-10-22.md):
six backend diagnostic cases and three completed native cases distinguish
healthy operation, the optional-cache/durable-save defect and correct blocking
on a required-write error. Actual screenshots and retained failed sandbox runs
are included. This is baseline evidence; no product correction is accepted.

### Evidence carried forward

- Source refinements are complete for the exercised paths: TXT/selectable-text PDF imports, title preservation, autosave/Spoken synchronization, generation-stage feedback, native-drop recovery and GPU utilization/counter recovery. The checkpoint records **255 backend tests, nine browser tests and six native checks**, including real CPU/CUDA generation. See the [current source checkpoint](HANDOFF.md#current-source-verification-and-store-chat-checkpoint--22-october-2026) for evidence and limits.
- The release-planning review found the refinements committed at `bdf58f1b4c89a269d0647050fe26f524e73b4c12`. This corrects the checkpoint's earlier uncommitted/HEAD bookkeeping; it does not claim another test run.
- Existing EXE/MSIX artifacts predate these refinements. The latest recorded compatibility MSIX is **1.0.3.0 from `bbe961f`**; its extracted-payload tests are not installed-MSIX evidence. See [package validation](package-validation-2026-10-22.md).
- Keep source, frozen-package, installed-MSIX, low-end/no-GPU, licensing/privacy and Store-certification evidence separate. Completed S-05/data-validation and GPU-runtime-trust hardening must not be reopened merely because an older status describes earlier work.
- The original S-01 through S-06 source fixes are implemented with evidence for their recorded scope. Remaining work below covers unresolved questions and release boundaries; it does not restart those implementations.
- R-01 normal-close saving is now implemented and locally validated: **264 backend / 15 browser tests, six debug-off native close cases**, clean Svelte check and rebuilt frontend. Independent verification is pending; earlier 255/9/six-native refinement evidence retains its original scope. See [R-01 report](r01-save-on-close-2026-10-22.md).
- R-02 subsequently passed **281 backend / 15 browser tests, six native close reruns**, native navigation/media checks and actual CPU/CUDA generation with injected storage/cache faults. It changes R-01's shared native completion boundary; use the [combined results/snapshot](r02-results-2026-10-22.md) for current review. No frontend changes/rebuild in R-02 and no package release clearance.
- R-03 refreshed **80 PyPI + 98 npm pairs** and old/native inventories without changing source/dependencies. The [independent review](../.tmp/r03-independent-20261022-b019f803/review.md) accepted this scoped investigation; runtime/audio/native coverage remain required and a DOMPurify update is recommended. [Review reconciliation/fix plans](r03-review-reconciliation-2026-10-22.md) include Expat 2.9.0's additional fixes. No release-gate closure.

### Required before public release

- [ ] **R-01 — Save safely on normal close. Source implemented/local checks passed; independent verification pending.** The normal-close guard drains pending writes, keeps failures/timeouts recoverable and rejects stale completion after keep-editing/cancel. Immediate/in-flight/retry/cancel/timeout/clean native cases pass and reopened synthetic SQLite retains expected text. Return to the verification chat before acceptance; final-package repetition belongs to R-07/R-08/R-10. No forced-kill/power-loss guarantee. See [R-01 report](r01-save-on-close-2026-10-22.md).
- [ ] **R-02 — Resolve remaining behavior/security questions. Independent review needs fixes.** Original [results](r02-results-2026-10-22.md) retain their scoped normal-path passes. [Independent findings](../.tmp/r02-independent-20261022-3d986790/review.md) require parent optional-cache/startup/save-close degradation, recommend removal/retry coordination and correction of the CDP helper's false-success path. R-01 overlaps the close/state-refresh boundary. [Fix plan](r03-review-reconciliation-2026-10-22.md) recorded; no remediation applied in reconciliation. Preliminary navigation GETs/raw known-ID access remain documented limits; installed checks remain separate.
- [ ] **R-03 — Refresh advisory coverage. Investigation accepted; combined remediation/dispositions awaiting independent review.** [Audio fix](r03-audio-remediation-results-2026-10-22.md), [authorized runtime/sanitizer update results](r03-runtime-sanitizer-results-2026-10-22.md), [combined review prompt](r03-updates-independent-verification-prompt.md). Selected Python 3.12.15/OpenSSL 3.5.9 and DOMPurify 3.4.17 are implemented in isolated build inputs; prior environments preserved. Windows Expat is actually 2.8.5: proposed architecture/bounded-caller dispositions for the two 2.9.0 CVEs need independent acceptance, with no backport claim. CPU/CUDA/browser/native/media checks passed. Both corrected comparisons passed 305 methods (304 passed/one skipped); ordinary runs show unresolved cleanup errors or a GPU-counter one-second deadline failure. Focused GPU suites pass on both runtimes; no assertions relaxed. Exact final native coverage remains open. Empty feeds/version labels are not blanket clearance.
- [ ] **R-04 — Complete exact redistribution evidence.** Resolve rights/notices for the shipped models, voices, dictionaries and native runtimes, including required source/replacement arrangements. File hashes alone do not establish distribution rights. Check required app/license terms against the exact components.
- [ ] **R-05 — Complete privacy and data-policy review. Scoped source/synthetic investigation complete; independent acceptance and release closure open.** [Results/data map](r05-results-2026-10-22.md), [internal disclosure draft](r05-privacy-policy-draft-2026-10-22.md), [next runtime/installed plan](r05-runtime-validation-plan-2026-10-22.md), [review prompt](r05-independent-verification-prompt.md). Eight data-lifecycle acceptance groups and a separate real-export-error/dispatcher probe passed. Retained snapshots/backups/recovery/cache and local path-bearing diagnostics are documented; no live app traffic/native-setting measurement or product control was performed. Choose diagnostic/log/retention behavior, verify parent/CPU/GPU worker and installed evidence, finalize policy/contact/hosting later, and preserve SmartScreen. No claim of zero traffic, app encryption or secure erasure.
- [ ] **R-06 — Finalize production identity/configuration and build.** Obtain the intended publisher identity, then build fresh EXE/MSIX outputs from the reviewed revision with pinned inputs, a clean build environment and recorded inventories/hashes. Audit actual frozen/external payloads, approved model/GPU bytes and eSpeak exclusion; exclude unintended development material, secrets, test fixtures and personal libraries. Environment recreation is a final-build check, not a requirement after every small change.
- [ ] **R-07 — Verify current features in the final package.** Exercise frozen PDF spawning, TXT/PDF errors and limits, title preservation, save/Spoken behavior and normal-close fix, native drop, generation feedback, CPU/CUDA generation and GPU-counter recovery, playback and restart. Include normal debug-off use; older/source-only passes do not clear this package.
- [ ] **R-08 — Verify installed production-MSIX behavior and failure cases.** Check standard-user app operation, installed identity/permissions, workers/DLL loading, WebView2, dialogs/drop and offline launch. Exercise unavailable WebView2, unsupported/missing GPU or drivers, low GPU memory and blocked/interrupted model fallback setup as relevant; establish clear recovery/errors. Do not change system security settings to manufacture a pass.
- [ ] **R-09 — Rehearse updates and the data lifecycle.** Update an older installed test version containing synthetic data; confirm documents/audio/settings/positions survive. Define and test interruption/recovery and any supported rollback procedure, separately from database recovery. Verify uninstall/reinstall retention against the stated policy; do not assume arbitrary package downgrades are supported.
- [ ] **R-10 — Test the actual final MSIX on another machine (mandatory).** Use a separate machine without development-tool/project dependencies, preferably a clean physical CPU-only Windows PC near the proposed minimum. Exercise installation, imports, saving/closing/reopening, CPU generation/playback, offline operation, update retention and uninstall/reinstall. Portable/extracted payload tests are insufficient. Obtain separate low-end/no-GPU evidence if this machine does not cover it, and verify final-package CUDA on supported NVIDIA hardware.
- [ ] **R-11 — Establish supported performance and accessibility. Accessibility investigation reviewed; corrections required, no implementation accepted.** Argon's source/synthetic-browser findings and plan contain material contradictions and acceptance-harness gaps; use the [review summary/work split](release-coordinator-continuation-2026-10-22.md) and [correction prompt](r11-argon-plan-correction-prompt.md). Measure startup, first-audio time and memory on the supported baseline; choose minimum Windows/RAM/hardware commitments from results. Check core keyboard/focus, actual screen-reader names/state, contrast and text scaling. The investigation does not close these gates.
- [ ] **R-12 — Finish final certification and publisher readiness.** Run applicable WACK and local malware checks on the exact submission package; investigate failures. Finalize account/name verification, MFA/recovery, price/markets, support/privacy pages, age rating, listing assets, accurate feature/dependency requirements and capability/certification notes. Review policies effective at submission. Establish support/security reporting and a rehearsed patch route before requesting publication authorization.

For each package/machine check record: **case, source revision, package identity/version/hash, OS/hardware, result, evidence location and limitations**. Package/source changes after validation require appropriate revalidation. Licensing/privacy and publisher setup can proceed alongside engineering; these numbered items are work groups, not a requirement to finish every investigation before beginning the next.

### Preferred before release, subject to findings

- [ ] **P-01 — Independent user experience/listening pass.** Have a second tester exercise usability, keyboard navigation, errors and representative document lengths/voices.
- [ ] **P-02 — Expand coverage and optimize.** Test more Windows/NVIDIA configurations beyond the supported minimum and improve startup, memory/package size where the measured baseline is already acceptable.
- [ ] **P-03 — Improve recovery/support convenience.** Polish restore/export and consider a privacy-reviewed local diagnostics-export button beyond essential recovery/support requirements.
- [ ] **P-04 — Consider additional code protection.** Optional proprietary module compilation can discourage inspection but cannot make local software uninspectable. Preserve third-party source/replacement rights. Excluding unintended private material/secrets remains required.
- [ ] **P-05 — Consider a limited initial audience/flight.** Use it where available after release gates are met; publication still requires authorization.

Serious failures discovered during these checks become release blockers. They are not deferred solely because the investigation started as an improvement.

### Can follow after release

- [ ] **A-01 — Optional feature expansion.** OCR, multilingual speech, extra voices and arbitrary custom models, each with its own scope/trust/licensing review.
- [ ] **A-02 — Historical-data repair.** Tools for titles already overwritten by earlier versions.
- [ ] **A-03 — Optional diagnostics/sharing.** Separate consent/privacy review before adding collection or export.
- [ ] **A-04 — Further polish and monetization.** Performance, cosmetics, convenience, broader hardware coverage, optional code protection and any separately chosen paid/advertising model. Free without ads remains the version-1 recommendation.
- [ ] **A-05 — Ongoing maintenance.** Monitor advisories, address support/security reports and deliver tested patches. This is recurring work, not a one-time item; update/support arrangements must already exist at launch.

### Publisher decisions and next batch

Still needed: account/name-reservation status and production identity, pricing/markets, support/privacy contacts/pages, measured minimum hardware commitments, retention/delete/restore behavior and the desired optional code-protection effort. NVIDIA support stays in scope; deferred features are not silently added to version 1.

**Next steps:** Independently review the [completed R-05 investigation](r05-independent-verification-prompt.md). The [R-02 correction plan](release-coordinator-continuation-2026-10-22.md) remains the next proposed engineering batch. Any R-05 runtime collection/control work needs the concrete [scope and acceptance plan](r05-runtime-validation-plan-2026-10-22.md), with overlapping UI/build ownership coordinated through the publisher. The previous chat retains Argon's R-11 validation; no corrected plan/implementation acceptance has been returned here. R-04 rights/provenance and publisher preparation can progress independently when directed. Keep R-03 engineering paused; its combined review, Expat dispositions and mixed tests remain open. All fresh-package/installed/mandatory other-machine/privacy/certification gates remain separate.

The publisher's [21 October release guide](</C:/Users/fireball/OneDrive/Desktop/testing notes/violilt-release-guide (1).md>) has now been reviewed. Its earlier fix/commit/test snapshot is superseded by current evidence. Useful details were merged into R-06/R-08/R-09 and the evidence-recording rule: final-build hygiene, missing-runtime/driver/low-memory/download-failure cases and explicit update/recovery procedures. Most other content overlaps existing gates. The guide's backup requirement remains waived; its prompts do not authorize execution. Guard tests need not fail on a pre-fix baseline, additional review models are optional, and review-round limits cannot clear unresolved blockers. Public sample-upload services such as VirusTotal are not part of the local scan baseline and require a separate sharing decision.

The original planning update authorized documentation only; the publisher subsequently authorized R-01, R-02 and R-03 implementation and the scoped isolated runtime/dependency updates. Preserve existing work and prior environments; no commits, destructive Git operations, personal-data access or publication. The backup requirement remains waived.

## Gate 1 — Distribution, ownership and privacy

| Item | Trace / plan / acceptance | Status |
| --- | --- | --- |
| Account and identity | No verified Partner Center account/name was supplied. Publisher creates/verifies the account, reserves Violilt, enables MFA/recovery and supplies exact package identity. | Publisher action |
| Dependency/code/data rights | Fresh package audit found no forbidden eSpeak/phonemizer modules/files. Matching notices/source archives were refreshed. Close exact model/voice/dictionary, LGPL/MPL replacement, libsndfile/codecs, Microsoft runtime and NVIDIA DLL grants. See `thirdparty/PRONUNCIATION-CANDIDATE.md`. | Partial evidence passed; redistribution clearance open |
| Proprietary packaging | App code is intended to remain private. Inspect output for unintended private material/secrets and preserve third-party source/replacement rights. Selected module compilation is an optional protection decision; local software cannot be made uninspectable. | Payload hygiene required; additional protection optional |
| Privacy and telemetry | Source and version-specific runtime documentation traced in [privacy review](privacy-release-review.md). Next verify runtime settings/traffic and retention, preserve security protections, and prepare public/in-app disclosures and delete/export behavior. | Trace/plan recorded; implementation and disclosure open |
| Product/listing choices | x64 and CPU/NVIDIA scope are recorded. Confirm supported Windows/hardware from tests, price, markets, support contact, age rating, artwork/name rights and terms/notices. | Part publisher action |

Gate 1's unresolved distribution rights prohibit public release; reversible engineering and isolated test builds can proceed alongside the evidence review.

## Gate 2 — Application security and data recovery

| Item | Trace / plan / acceptance | Status |
| --- | --- | --- |
| S-01 dependencies | Original certifi/pip fixes remain implemented. Investigation independently accepted; audio fix and isolated Python/OpenSSL/DOMPurify update implemented. Actual Windows Expat 2.8.5 dispositions, cleanup observations and combined remediation need review. Final native coverage remains open. | Investigation accepted; combined source/disposition review and final coverage open |
| S-02 native dispatch | Exact public method/arity contract, message-size/callback-ID bounds and registered-callback checks now precede generic dispatch. Native file objects retain their dedicated transport. Unit, native debug-off playback, and frozen valid-private-call rejection tests passed. | Implemented and passed for tested source/frozen build; installed test open |
| S-03 model trust | Independently fetched CPU/GPU/voice bytes are pinned in code. Downloads/imports, readiness, build payload and inference verify hashes. Invalid optional GPU content leaves CPU usable. | Implemented; focused and real CPU/CUDA generation checks passed |
| S-04 model replacement | Complete sets are staged and verified, previous files are journaled/backed up, interrupted transactions recover, and imports coordinate with worker release/generation. | Validation/replacement-failure/restart tests passed; installed update/power-loss rehearsal open |
| S-05 settings/data | Shared settings and persisted document/job/benchmark validation; schema v1 with pre-upgrade backup; newer schemas rejected; malformed records/audio quarantined for recovery while retaining healthy data. | Confirmed source reproductions addressed and tested; installed/broader failure rehearsal open; fuller restore UX preferred |
| S-06 library import | Managed-entry allowlist, reparse rejection, source lock, bounded copy, free-space checks and before/after source snapshots. | Junction/concurrency/change/low-space regressions passed; older non-cooperating apps/installed scenarios still need validation |
| Resource limits | Existing limits remain: 2 MB Markdown, 32-file batches, 8 MB native messages and library import bounded at 100 GB / 100,000 entries with disk-space checks. TXT has 2-MiB source/converted-copy limits; PDF has 20-MiB source, 200-page, 2-MiB extracted/converted-text, 20-second extraction and monitored 512-MiB RSS limits. Parser process isolation is not an OS security sandbox. | Exercised source limits passed; frozen/installed and broader disk-full/cancellation/performance checks open |
| Local access/runtime trust | R-02 source navigation/media checks passed with a canceled-navigation bridge fix. Preliminary navigation GETs and raw local known-ID media access remain possible; session binding remains optional on current evidence. GPU runtime byte pins, per-worker verification and trusted DLL loading are implemented. Installed ACLs/concurrent replacement, runtime/log permissions and final-package behavior remain open. | Source hardening/local boundary checks passed for exercised scope; independent and installed review open |

## Gate 3 — Exact release package

| Item | Trace / plan / acceptance | Status |
| --- | --- | --- |
| Production profile/build | Older CPU/GPU evaluation executable and unsigned compatibility MSIX 1.0.3.0 were built from `bbe961f` with inventories/hashes. They predate `bdf58f1` refinements. Production identity/data profile and a current-source build remain required; additional proprietary compilation is optional. | Historical compatibility build passed; current production build open |
| Native payload | R-03 inventoried 199 historical EXE/DLL/PYD files plus 25 prepared GPU DLLs, with version/hash/scope records. Exact native/vendored provenance and unresolved advisories remain open, and final-package bytes must be inventoried again. Redistribution grants remain R-04. | Historical/current-component evidence recorded; remediation and final-payload review open |
| Installed behavior | Older frozen/extracted-MSIX checks passed their recorded boundaries; see the 22 October package report. No installed production-MSIX pass is established. Earlier installation was blocked by the available non-administrator environment. | Historical portable/extracted checks passed; current installed package identity open |
| Clean machines | Final MSIX installation/use on another machine is mandatory. Prefer a clean physical CPU-only PC near the measured minimum; validate supported Windows/hardware, standard-user and offline use, paths/scaling and data lifecycle. Expand the driver/OS matrix as needed for advertised support. | Required before release; open |
| Accessibility | Verify keyboard/focus, screen-reader names/state, contrast and text scaling in core workflows before launch. | Open |
| Updates/recovery | Older-to-newer installed update, interrupted operation/recovery, documents/audio/settings/positions retained, reinstall/uninstall behavior understood. | Open |
| Certification/security scans | Run applicable WACK tests and malware checks on exact submission payload; investigate failures. WACK was not found in the checked standard installation location. | Open; WACK/install environment needed |

## Gate 4 — Submission and maintenance

Verify the Store policies effective at submission, manifest identity/capabilities and full-trust explanation, optional NVIDIA dependency notes, privacy/support URLs, screenshots/icons, accurate requirements and age rating. Reserve and retain the exact source revision, dependency inventory, package hashes and test evidence. Establish a support/security reporting route, account recovery, dependency-advisory review and a rehearsed patch process. Use a small initial audience/flight where available. Publisher reviews the concrete submission before publication.

## Work log

- **22 October independent-review reconciliation:** read the returned R-03 pass-for-investigation report and its linked R-02 needs-fixes report; verified the additional Expat maintainer reference; traced stored-audio/cache/state/helper consumers and recorded concrete next batches. Updated acceptance versus remediation status while retaining original report/manifests. Documentation/review only; no product fixes, installs or new application tests.

- **22 October R-03 investigation:** traced locks/current metadata and historical payload, recorded a plan, queried 80 PyPI + 98 npm pairs and checked vendor sources/native versions. Empty feed responses coexist with maintainer/native findings. Targeted sanitizer/PDF/audio boundary helpers passed their stated benign scope after documented fixture corrections. Runtime/audio follow-up and native coverage remain open; recommended DOMPurify update not applied. New review prompt/snapshot; all 69 R-02 inputs unchanged. No installs, commits, source/assets changes, package operations, personal libraries, publication or messages to another chat.

- **22 October standing review handoff:** recorded the publisher's requirement for a per-R completion report/prompt and reusable review entry point, with independent continuation, input-drift handling and returned-finding reconciliation. Latest target is R-02 plus R-01 overlap; acceptance remains pending. Documentation only; no new application tests or R-03 work.

- **22 October R-02 execution:** followed the trace/plan with disposable reproductions and scoped persistence/cleanup/export/quarantine/worker-cache/native-completion fixes. Final 281 backend / 15 browser tests, six native close reruns, native navigation/media probes and real CPU/CUDA generation passed. Original R-01 hashes retained; new combined snapshot records the shared desktop boundary. Independent acceptance and all separate release gates remain open. No installs, commits, EXE/MSIX builds/installations, personal-data access, publication or cross-chat messages.

- **22 October verification prompt and R-02 planning:** wrote a copyable verification-only R-01 prompt, then traced navigation/local media/storage/runtime boundaries and existing evidence without running new probes. Recorded fault-reproduction candidates and a bounded R-02 sequence; no product/test/asset edits, new test counts, fixes or installations in this planning turn.
- **22 October R-01 implementation:** traced the missing native close/save handshake and synchronous WinForms closing behavior, planned and implemented queued native/frontend approval, recoverable failure/timeout and cancellation guards. New baseline browser regression failed on old frontend; final checks passed 264 backend tests, 15 browser tests, six debug-off native close cases, Svelte check and frontend build. Independent review and package checks remain open. No dependencies, commits, EXE/MSIX builds/installs, personal libraries or publication.
- **22 October consolidated remaining-work checklist:** converted current priorities into R/P/A checkboxes and incorporated the reviewed guide's useful acceptance details without reopening completed source fixes. Preserved historical gates/evidence. Documentation only; no tests, implementation, installation, commit or publication.
- **22 October planning reconciliation:** carried forward the 255 backend / nine browser / six native source checks without rerunning them; distinguished older `bbe961f` package evidence from committed `bdf58f1` refinements. Recorded required/preferred/post-release work, mandatory final-MSIX testing on another machine, publisher decisions and the pending external guide comparison. Documentation only; no implementation, installation, commit or publication.

The entries below describe earlier work and its then-current counts/artifacts, not the latest source verification or a current-package pass.

- **Trace completed:** current working tree, existing report, build/setup scripts, model paths, native dispatch and licensing notes inspected. No applicable repository/ancestor AGENTS.md was found. Existing unrelated changes are retained.
- **Plan:** first implement S-01/S-02 and model trust/rollback together, because validating after destructive replacement would retain the availability defect. Keep final-package/rights checks open until the rebuilt artifact exists.
- **Baseline evidence:** 150 backend tests and browser/native protection probes passed on the investigation baseline. Those results remain scoped to that baseline; affected checks will be repeated after changes.
- **Security implementation completed:** dependency/tooling pins, exact native dispatch, approved model hashes and transactional activation, preference/JSON recovery, library-copy boundaries and input limits. Each change followed a code trace and stated acceptance checks. Current tests: **170 passed**; frontend check/build passed.
- **Runtime validation completed:** normal native debug-off startup/playback passed. A separate frozen executable check rejected private dispatch, invalid callback identifiers and invalid settings; generated real CPU and CUDA audio; retained settings/documents after reload; and reported no page errors.
- **Package evidence completed:** 1,467 audited payload files / 2,334 frozen modules; zero forbidden-content findings; all model pins verified. Compatibility MSIX 1.0.2.0 contains 1,168 mapped files plus two standard MSIX metadata entries, with CPU/NVIDIA assets retained. Installer dry run verified the complete package hash; nothing was installed or published.
- **Privacy trace completed:** source network/log surfaces and version-specific ONNX/WebView2 documentation recorded; diagnostic controls, final policy and retention/deletion decisions remain open.
- **Next gates:** finish exact redistribution/runtime/privacy evidence and production configuration; use an administrator-capable test environment for installed CPU/GPU, update/recovery, clean-machine and certification checks. Account/name/MFA, publisher/support details and product choices require the publisher. These pending gates are not waived by passing unit tests.

Detailed evidence and artifact links: [implementation results](release-hardening-2026-10-21.md).
