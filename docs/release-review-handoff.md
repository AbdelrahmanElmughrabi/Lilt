# Release review handoff

> **Current checkpoint — 24 October 2026:** Consult [source/release status](release-source-status.md)
> before selecting any review target. The R-05 retention, logging/export, cleanup
> and final startup-seam source passes are returned; old "running/pending" rows
> below are dated records. R-03 dispositions and the recorded R-01/R-02 combined
> acceptance remain separate. Reuse unchanged verdicts and review only a concrete
> changed or uncovered boundary. No new review, execution or publication is
> authorized merely by this index update.

**Current continuation context — 23 October:** Latest ready target is the combined correction of all three returned R-02 findings, including affected R-01 save/close behavior. All are locally corrected, pending independent acceptance. The latest tooling batch leaves product/frontend/assets unchanged. Prior cache/removal/R-05 snapshots and their limits remain preserved. R-03 engineering remains paused; all release gates remain open. Argon is off the project; R-11 correction/review/assignment remain open. The previous validation chat remains independent and is not automatically retargeted. Publisher carries prompts/results; no automatic messages. HEAD remains `eda83ed`; implementation is uncommitted.

Agreed with the publisher on 22 October 2026. This file is the reusable entry point for the independent review chat. After each R item is ready, the implementation chat adds a batch entry and supplies its review link. The publisher sends the prompt below to the review chat and brings its report back here. No automatic cross-chat messages are authorized.

## Prompt to send each time

```text
Read C:\Users\fireball\OneDrive\Desktop\LiltTTS\docs\release-review-handoff.md.
Review the latest ready batch listed there, following its batch-specific prompt
and the standing review rules. Independently verify the recorded claims and return
a report with findings, evidence, scope and limitations. This is verification only;
do not apply fixes. The implementation chat may continue other release work, so
check input hashes before and after and do not combine different snapshots silently.
```

Use this same prompt for each newly completed R item. The latest entry below identifies what is ready; planned/in-progress items are not automatically part of the review.

## Latest ready batch

**Combined R-02 V-02-01/02/03 corrections and affected R-01 boundary — locally
validated; independent acceptance pending.**
[Latest navigation-helper results](r02-navigation-helper-results-2026-10-23.md),
[cache results](r02-cache-fix-results-2026-10-23.md),
[removal/retry results](r02-removal-retry-results-2026-10-23.md),
[combined batch-specific prompt](r02-corrections-independent-verification-prompt.md).

Latest exact inputs/evidence: `.tmp/r02-cdp-fix-20261023-2f7d8c51/`, with 230
starting copies, final manifest/integrity/validation, before/after VM logs and
actual debug-off native navigation results. The unchanged helper failed 19 of
21 checks; the corrected helper passed all 21. Real native checks passed URL/
marker preservation, API/UI after canceled navigation/CDP, and durable close.
No product/frontend/dependency/asset change or build in the latest tooling batch.
Prior 66 backend/18 editor-browser/native results retain their separate recorded
scopes; do not add them into a new combined-suite count. Check exact snapshot
changes and the cache report's earlier harness-provenance limitation.

Review all three corrections and relevant R-01 overlap; no known returned finding
remains unimplemented, but independent review may identify more. Deferred P3
native-error wording, R-03 engineering pause/unaccepted dispositions/unknown tests,
R-04/R-05 and all final package/installed/update/performance/accessibility/
certification gates remain. Actual final MSIX on another machine is mandatory.

## Previous ready batch — V-02-02 removal snapshot retained

**R-02 V-02-02 removal/retry correction — implemented and locally validated;
independent acceptance pending.**
[Reasoning/results](r02-removal-retry-results-2026-10-23.md),
[batch-specific review prompt](r02-removal-retry-independent-verification-prompt.md).

Evidence: `.tmp/r02-removal-fix-20261023-849e3c2a/`; read `PLAN.md`, `before.json`,
all 227 copied starting inputs, final hashes/integrity/validation, test logs and
before/after real-listener results. Two backend files/two tests and coordinator
indexes changed; frontend source/assets and all prior evidence are preserved.
66 focused tests passed; four real-listener terminal/audio combinations stay
removed after natural retry/shutdown while an unrelated benchmark still saves.
Earlier assertion failures and four reproduced resurrection cases remain recorded.
The completed sandbox baseline wrapper lingered and was interrupted; no shell
zero-exit pass is claimed for it. Post-correction acceptance completed normally.

Review the removal boundary and relevant shared cache behavior; prior native
results are for their recorded source bytes. Both V-02-01/02 require independent
acceptance. V-02-03 remains next; R-03 engineering remains paused. All other release
gates, including actual final MSIX on another machine, remain open.

## Previous ready batch — V-02-01 cache snapshot retained

**R-02 V-02-01 cache/save-close correction — implemented and locally validated;
independent acceptance pending.**
[Results](r02-cache-fix-results-2026-10-23.md),
[problem/plan](r02-cache-failure-plan-2026-10-22.md),
[before-fix baseline](r02-cache-baseline-2026-10-22.md),
[batch-specific review prompt](r02-cache-fix-independent-verification-prompt.md).

Evidence: `.tmp/r02-cache-fix-20261023-6c9a2b71/`; inspect `source-hashes.json`,
`before.json`, `after-integrity.json`, `validation.json`, build provenance,
scoped logs and native results. Four product source files/two tests and built
assets changed; old assets/evidence remain preserved. 56 focused backend tests,
18 browser checks, clean Svelte check/build and five actual debug-off native
scenarios passed (six runs including a capture repeat). This is local source
validation, not independent, installed or release acceptance. V-02-02/03 and
R-01/R-02 closure remain pending. R-03 engineering stays paused. All separate
rights/privacy/package/installed/update/performance/accessibility/certification
and mandatory final-MSIX-on-another-machine gates remain open.

## Previous ready batch — R-05 snapshot retained

**R-05 privacy investigation and disclosure preparation — locally complete;
independent review pending; R-05 release gate open.**
[Results/data map](r05-results-2026-10-22.md),
[trace/plan](r05-trace-plan-2026-10-22.md),
[internal draft](r05-privacy-policy-draft-2026-10-22.md),
[future runtime plan](r05-runtime-validation-plan-2026-10-22.md),
[batch-specific review prompt](r05-independent-verification-prompt.md).

| Field | R-05 review target |
| --- | --- |
| Exact evidence | `.tmp/r05-20261022-privacy-a73f9b24/`, final `source-hashes.json`, before/supplemental manifests, preserved prior indexes, probes/results/logs, primary-reference records and validation/integrity records |
| Base | `eda83ed1c4742b8585d68a1ce267225ca28d6bdd`; earlier modified/untracked documents preserved |
| Executed | Eight asserted synthetic data-lifecycle groups; real export-error/pywebview dispatcher with five outcome checks plus fixture guard; source/vendor inspection and documentation/hash checks |
| Changes | New R-05 documents/evidence and additive coordinator/privacy index updates only; no application/shared test/dependency/asset edits, native app/traffic capture or package operations |
| Scope left open | Runtime/native-setting and CPU/GPU diagnostic effects, installed ACL/privacy/update/uninstall behavior, chosen controls/retention, publisher/contact/public URL and final disclosures |
| Other work | Previous chat retains R-11 validation; R-02 unresolved; R-03 engineering paused; every final-package/other-machine/rights/certification gate remains |

## Earlier ready batch — paused R-03 remediation

**Current publisher instruction: R-03 implementation is paused.** The publisher requested documentation for a new chat. Read [the paused handoff](r03-paused-handoff-2026-10-22.md) and [new-chat prompt](r03-new-chat-prompt.md) first. Do not automatically launch more tests/fixes from this index. OneDrive is disabled per the publisher. The historical update manifest omitted `build.ps1`; the [pause-checkpoint manifest](../.tmp/r03-updates-20261022/handoff-checkpoint/source-hashes.json) includes current root build inputs. Prior manifests/evidence remain unchanged. This is documentation-time bookkeeping, not new test or package approval.

**Combined R-03 audio/runtime/sanitizer remediation — implemented; independent acceptance pending.** [Latest update results](r03-runtime-sanitizer-results-2026-10-22.md), [combined review prompt](r03-updates-independent-verification-prompt.md), [earlier audio report](r03-audio-remediation-results-2026-10-22.md). Include the unaccepted audio fix, Expat dispositions and cleanup observations. The earlier investigation's scoped pass is not remediation acceptance. R-02 findings and final native coverage remain open.

| Field | Recorded batch |
| --- | --- |
| Review instructions | [Combined current R-03 review prompt](r03-updates-independent-verification-prompt.md) |
| Result and limitations | [Runtime/sanitizer results](r03-runtime-sanitizer-results-2026-10-22.md), [update plan](r03-updates-trace-plan-2026-10-22.md), [audio results](r03-audio-remediation-results-2026-10-22.md) |
| Earlier findings | [Reconciliation](r03-review-reconciliation-2026-10-22.md); R-02 needs fixes, R-03 investigation accepted within scope |
| Base commit | `bdf58f1b4c89a269d0647050fe26f524e73b4c12`; uncommitted/untracked work is part of the batch |
| Current input manifest | [Pause-checkpoint manifest](../.tmp/r03-updates-20261022/handoff-checkpoint/source-hashes.json); current inputs including canonical `build.ps1`. Earlier 751-input update manifest is retained with its coverage gap documented. |
| Evidence directory | `.tmp/r03-updates-20261022/`; installation/provenance, checks, notices and 450 preserved previous audio-revision contents. Prior audio evidence remains separately preserved. |
| Validation | Initial 301-method source pass; added four guard tests; both corrected comparisons passed 305 methods (304 passes/one skip). Ordinary runs show teardown errors or a GPU-counter deadline failure; focused GPU module passed three times per runtime. 15 browser/six native/media/CPU/CUDA/TLS/XML checks passed. |
| Shared-input change | Runtime/build tooling, DOMPurify lock/isolated install and built assets changed. Audio application code unchanged in this update. Original source contents, base runtime and environments retained; old manifest hashes cannot describe new assets/tooling. |
| Review status | Combined audio/runtime/sanitizer review pending. Actual Windows Expat 2.8.5 requires proposed scoped dispositions or another compatible patched build. Cleanup/GPU timing findings and exact final native coverage open. R-02 findings remain unresolved. |
| Next implementation work | R-02 corrections remain next engineering batch; R-04 and Argon's R-11 trace/plan remain separate. No package/publication authorization follows from isolated installation approval. |

Check that working files match the current manifest before testing. The updates folder preserves 450 preceding audio-revision input contents; the audio folder separately preserves 386 investigation inputs. Neither is a complete environment or Git checkout. Use the explicitly selected new interpreter/dependencies for this batch; the old environments remain available for labeled comparisons. Source hashes alone do not prove runtime identity. This handoff is a changing index; original batch manifests/reports/logs are retained.

## Standing review rules

1. Read the batch report, its trace/plan and batch-specific prompt, then inspect the actual changes and evidence. Include relevant untracked files. Treat saved results as claims to verify, not automatic acceptance. Distinguish new changes from previously reviewed work; revisit prior checks when an overlap or finding justifies it.
2. Verification only: preserve application source, tests, shared built assets, existing evidence and all unrelated work. No dependency installations, Git mutations, model downloads, EXE/MSIX builds/installations, personal-data access or publication. No messages to other chats. The backup requirement was waived. A later explicit publisher instruction can authorize a separately scoped action.
3. Use existing tools and new uniquely named `.tmp/rNN-independent-*` folders for synthetic probes, logs and the review report. Do not overwrite implementation evidence or shared `frontend/dist`. Use `-B` with the existing project Python. Only use existing public model fixtures when the batch prompt permits them; do not inspect personal libraries.
4. Hash relevant source/test/assets before and after checks and compare with the batch manifest. Record relevant runtime/dependency versions. If inputs or dependencies differ, identify exactly what changed. Use a suitable isolated copy with existing tools where practical, or qualify/defer only affected checks. Do not overwrite shared files, switch the shared checkout or claim that a current-source pass validates an older snapshot.
5. Run checks appropriate to the batch and its claims. Include meaningful failure/race/recovery boundaries, and inspect the harness for false positives. Do not require every guard test to fail on the old baseline. Separate actual application failures from invalid harness assumptions, missing tools and sandbox restrictions. An advisory or documentation batch may need inventory/source verification rather than another full runtime suite; explain coverage.
6. Keep source, frozen payload, installed production MSIX, another-machine/low-end/no-GPU, licensing/privacy and Store-certification evidence separate. The actual final MSIX must still be tested on another machine before release. Avoid upgrading a scoped pass into blanket security/release approval.
7. Return a verdict of **passes**, **needs fixes** or **insufficient evidence**, scoped to the exact checked inputs. Findings need severity, absolute file/line or evidence reference, trigger, expected/actual behavior and reproduction where possible. Separate checks actually rerun, saved evidence inspected, source inference and not checked. Report exact counts, hashes/versions, evidence/report location, unresolved assumptions and impact on previously reviewed batches. Stop after the report; do not apply fixes.

## Implementation chat's completion and continuation rule

For every R item, follow **trace → plan → implement/investigate → validate → record → independent review**. Before handing it off:

- Write a batch-specific result/handoff and copyable review prompt. Include the problem/scope, confirmed findings, changed/new files, validation actually performed, reproduction commands, evidence paths and practical limits. For inventory/advisory work, record exact versions, query date, sources and shipped-versus-environment coverage. Do not invent test requirements/results for work that does not need them.
- Record the exact inputs in a new batch manifest and preserve prior manifests/evidence. Include relevant dependency/configuration identities as well as source/assets; identify uncommitted/untracked inputs. If an existing snapshot needs revision, create a new revision/evidence directory rather than overwriting its proof.
- Add the new latest-ready entry here, link it from `HANDOFF.md` and `release-readiness.md`, and provide its review link in the completion response. Mark implementation/local validation and independent acceptance separately. Do not check off a release gate merely because a handoff exists.
- Continue independent next-item tracing/planning and already authorized work while review runs. A pending review does not by itself block unrelated work. It also does not authorize a new dependency installation, package operation or publication. Before changing inputs relevant to a pending review, record the overlap and preserve the reviewed content in an isolated copy where needed; otherwise coordinate that boundary through the publisher. Keep unaffected work moving.
- When the publisher returns a review report or path, read and reconcile it. Trace actionable findings, plan/fix within authorization, validate the affected boundary, and issue a new review revision. Record what was accepted, what remains open and which earlier evidence was affected. Serious unresolved findings remain blockers; do not repeatedly rerun unrelated suites without reason.

## Batch history

| Batch | Implementation/evidence | Independent review |
| --- | --- | --- |
| R-05 investigation/documentation | [Results](r05-results-2026-10-22.md), [review prompt](r05-independent-verification-prompt.md), new manifests/evidence and provisional disclosure/runtime plans; no product controls | Pending scoped investigation review. R-05 runtime/installed/disclosure and release closure remain open. |
| R-01 | [Normal-close report](r01-save-on-close-2026-10-22.md); original eleven-file manifest retained under `.tmp/r01-close-20261022/` | Pending; use the combined R-02 target for the changed native boundary. No prior verdict is assumed. |
| R-02 + R-01 overlap | [R-02 report](r02-results-2026-10-22.md), [review prompt](r02-independent-verification-prompt.md), combined 69-file manifest | [Needs fixes](../.tmp/r02-independent-20261022-3d986790/review.md): parent cache, deletion/retry and helper acceptance; source remediation pending. |
| R-03 investigation | [R-03 report](r03-results-2026-10-22.md), [review prompt](r03-independent-verification-prompt.md), new input/evidence manifest | [Scoped investigation pass](../.tmp/r03-independent-20261022-b019f803/review.md); runtime/audio/native coverage unresolved, sanitizer recommended, Expat 2.9.0 note recorded. |
| R-03 audio remediation | [Audio report](r03-audio-remediation-results-2026-10-22.md), [review prompt](r03-audio-independent-verification-prompt.md), new manifest and prior-input content archive | Pending independent review; source/local checks passed within stated limits. Runtime/sanitizer/native coverage and R-02 findings remain open. |
| R-03 authorized runtime/sanitizer updates | [Update report](r03-runtime-sanitizer-results-2026-10-22.md), [combined current review prompt](r03-updates-independent-verification-prompt.md), new input/evidence manifest | Pending combined review, including audio, actual Expat dispositions and intermittent cleanup observations; final native/package gates open. |

The original R-03 investigation ran inventory/query consistency and two targeted benign surface helpers; it did not rerun the earlier 281/15/six suites. The new audio revision adds the separately recorded 301/15/six/media/CPU/CUDA checks. Counts remain evidence for their own snapshots and scopes.
