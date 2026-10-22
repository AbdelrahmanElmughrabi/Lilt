# R-03 stored-audio remediation — independent review prompt

Send this to the review chat:

```text
Review R03-F02's stored-audio remediation in:
C:\Users\fireball\OneDrive\Desktop\LiltTTS

Read docs/r03-audio-remediation-results-2026-10-22.md,
docs/r03-audio-remediation-plan-2026-10-22.md and the standing rules in
docs/release-review-handoff.md. Read the original R-03 investigation and returned
independent report only as earlier evidence, not acceptance of this new code.

Verification only. Preserve source/tests, shared assets/dependencies and all prior
evidence. No installations, Git mutations, model downloads, builds of EXE/MSIX,
installed-package operations, personal-data access, publication or other-chat
messages. Use existing tools, -B and a new unique workspace .tmp review folder.
Backup requirement is waived. Hash inputs before and after; include untracked work.

The audio implementation snapshot is:
.tmp/r03-remediation-20261022/source-hashes.json
All 386 prior R-03 repository input contents were preserved before editing in:
.tmp/r03-remediation-20261022/input-snapshot/
with prior-input-manifest.json. Original R-02/R-03 evidence is unchanged; its old
hashes do not describe current modified files. Do not overwrite evidence.

Inspect backend/pcm_audio.py and its cache, speech, server and bridge consumers.
Assess bounded structural parsing, accepted PCM/extensible compatibility, exact
chunk/data/file extents, metadata/chunk/allocation limits, same-handle reads,
mid-read changes/truncation and native parser exclusion on stored input. Check
cache/export atomicity and cleanup; invalid saved-section retention/regeneration;
resume/cancellation; raw assembly samples/pauses/timeline; canonical media
HEAD/Range/playback; unsupported-file behavior and original-data preservation.
Consider any other stored-audio consumers and security/regression gaps.

Independently reproduce the original benign AIFF case and appropriate malformed
variants. Prove native info/read/autodetection isn't called, including assembly,
not merely that a final return value is rejected. Realistic adversarial test
generation must stay disposable and resource-bounded; no hostile native exploit
is needed. Review harnesses for false-positive acceptance and test fixture changes.

Claimed validation: 301 backend methods run (300 passed, one Windows open-handle
replacement skip), 15 browser tests, six source native close cases, browser media
boundary and actual CPU/CUDA generation. Inspect saved evidence and rerun checks
appropriate to your findings. Do not count inspected logs as freshly rerun tests.
Only existing public model fixtures may be used for real generation:
dist/validation-bbe961f-20261022/Violilt/models
and the existing approved .tmp/pronunciation-gpu-runtime. No personal library.

Example commands from the repository root (use fresh evidence output paths):
$env:TEMP = '<new workspace .tmp review folder>'
$env:TMP = $env:TEMP
& .tmp/pronunciation-env/Scripts/python.exe -B -m unittest discover -s tests -v
$env:PLAYWRIGHT_MODULE = 'C:\Users\fireball\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules\playwright'
& 'C:\Program Files\nodejs\node.exe' --test tests/test_editor_save.cjs
& .tmp/pronunciation-env/Scripts/python.exe -B tools/r02-boundary-check.py --mode media --output '<new workspace .tmp media folder>'
Native checks may need tool-sandbox escalation; this is not Windows administrator
elevation. Read helpers before running and use each helper's supported arguments.

Runtime/OpenSSL/Expat, DOMPurify and exact native/final payload coverage remain
open; no dependency installation or new frontend build occurred in this batch.
The R-02 independent findings (parent-cache availability, deletion/pending retry,
navigation-helper false success) are recorded and NOT claimed fixed. Source
close checks do not cover that parent's optional-cache failure trigger. Separate
preexisting findings from regressions introduced by this revision.

Return passes/needs fixes/insufficient evidence for the scoped audio source
remediation, with severity, absolute file/line, trigger, expected/actual behavior,
reproduction/evidence and input hashes. Distinguish rerun, inspected, inferred and
unverified claims. Record full counts/versions and practical limits. Keep final
package, installed MSIX, mandatory other-machine, low-end/no-GPU, licensing/privacy
and certification gates open. Stop after writing/reporting; do not apply fixes.
```
