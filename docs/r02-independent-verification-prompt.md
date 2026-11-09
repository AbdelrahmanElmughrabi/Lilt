# Prompt: independently verify R-02 and its R-01 overlap

Copy this into the verification chat:

```text
Independently verify current R-02 source fixes and their R-01 navigation/close overlap in:
C:\Users\fireball\OneDrive\Desktop\LiltTTS

Read docs/r02-results-2026-10-22.md, docs/r02-trace-plan-2026-10-22.md,
docs/r01-save-on-close-2026-10-22.md, docs/HANDOFF.md and docs/release-readiness.md.
Inspect .tmp/r02-20261022/source-hashes.json and saved logs/results. Claims are
recorded evidence with limits, not independent approval. R-02 reports 281 backend
tests, 15 browser cases, six native close reruns, native navigation/media probes
and real CPU/CUDA generation with injected storage/cache faults.

Verification only: preserve all existing uncommitted/untracked work and evidence.
Do not edit application/tests/shared assets or apply fixes. No dependency installs,
Git mutations, model downloads, EXE/MSIX builds/installs, personal-data access,
publication or messages to other chats. Backup was waived. You may create a new
uniquely named .tmp/r02-independent-* folder for synthetic probes/logs/report.
Use existing dependencies and -B with the project Python. Check input hashes
before and after; qualify/repeat affected checks if source drifts.

Inspect the five changed backend files: jobs.py, bridge.py, storage.py, speech.py,
desktop.py. Include the new tests/test_io_failures.py, test_worker_io.py,
test_navigation_completion.py and tools/r02-* helpers; tracked diff alone misses
new files. Include existing R-01 guard/frontend/tests/helper where boundaries overlap.
HEAD baseline is bdf58f1b4c89a269d0647050fe26f524e73b4c12.

Verify bounded/coalesced retries and real listener survival, latest terminal/position
retention, truthful unsaved state and blocked new work, cleanup despite write failure,
and actual recovery after storage becomes usable. Look for races or hidden loss.
Do not demand that unavailable storage successfully save data; assess the stated
in-memory/forced-exit limit and preservation of earlier durable data.

Verify failed copy/replace preserves source and previous export, required output
failure reports a failed job without killing later commands, optional cache failure
permits generation, malformed-row/recovery-write failure preserves healthy rows,
and whole-file damaged SQLite fails non-destructively without automatic reset.

Review the pywebview NavigationCompleted adapter: skip only canceled navigation
while the original trusted page remains; preserve successful/other-error loads.
Reproduce foreign navigation/frame, old/new API references, actual UI action,
in-flight save and latest edit on close; inspect foreign-page execution markers.
Keep the known preliminary GET limitation: cancellation is not zero network.
Historical body-locator timeout root cause is not conclusively established.

Recheck app-origin playback/Range and foreign fetch/media/frame isolation. Distinguish
raw local known-port/UUID access (still possible) from browser-readable disclosure.
Do not claim session authentication or installed cross-user isolation. Assess whether
evidence supports keeping session binding optional; do not implement it automatically.

Use the reproduction commands in the R-02/R-01 reports and new output folders.
Do not overwrite frontend/dist; verify its unchanged hashes first. Run meaningful
focused/full backend, 15 browser and native checks with existing tools where available.
The runtime helper uses only existing pinned public model fixtures and synthetic text;
inspect before running. Separate sandbox/tool failures from app failures. Review failed
baseline/diagnostic runs too: corrected IO baseline supersedes its initial bad fixture;
zero-GET was an invalid harness expectation; guard tests need not fail before a fix.

The preserved original R-01 eleven-file manifest differs only in backend/desktop.py.
Use the new combined R-02 snapshot for current checks, retain the old evidence, and
report any impact on an earlier R-01 verdict. No final-package, installed-MSIX,
other-machine, low-end/no-GPU, licensing/privacy or certification clearance is implied.

Return verdict (passes / needs fixes / insufficient evidence), actionable findings
with absolute file/line, trigger and reproduction, exact checks actually rerun versus
saved evidence/source inference/not checked, input hashes and remaining limits.
Recommend source acceptance separately from release approval. Stop after the report.
```
