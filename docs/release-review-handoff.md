# Release review handoff

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
| R-01 | [Normal-close report](r01-save-on-close-2026-10-22.md); original eleven-file manifest retained under `.tmp/r01-close-20261022/` | Pending; use the combined R-02 target for the changed native boundary. No prior verdict is assumed. |
| R-02 + R-01 overlap | [R-02 report](r02-results-2026-10-22.md), [review prompt](r02-independent-verification-prompt.md), combined 69-file manifest | [Needs fixes](../.tmp/r02-independent-20261022-3d986790/review.md): parent cache, deletion/retry and helper acceptance; source remediation pending. |
| R-03 investigation | [R-03 report](r03-results-2026-10-22.md), [review prompt](r03-independent-verification-prompt.md), new input/evidence manifest | [Scoped investigation pass](../.tmp/r03-independent-20261022-b019f803/review.md); runtime/audio/native coverage unresolved, sanitizer recommended, Expat 2.9.0 note recorded. |
| R-03 audio remediation | [Audio report](r03-audio-remediation-results-2026-10-22.md), [review prompt](r03-audio-independent-verification-prompt.md), new manifest and prior-input content archive | Pending independent review; source/local checks passed within stated limits. Runtime/sanitizer/native coverage and R-02 findings remain open. |
| R-03 authorized runtime/sanitizer updates | [Update report](r03-runtime-sanitizer-results-2026-10-22.md), [combined current review prompt](r03-updates-independent-verification-prompt.md), new input/evidence manifest | Pending combined review, including audio, actual Expat dispositions and intermittent cleanup observations; final native/package gates open. |

The original R-03 investigation ran inventory/query consistency and two targeted benign surface helpers; it did not rerun the earlier 281/15/six suites. The new audio revision adds the separately recorded 301/15/six/media/CPU/CUDA checks. Counts remain evidence for their own snapshots and scopes.
