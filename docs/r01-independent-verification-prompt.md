# Prompt: independently verify R-01 normal-close saving

Copy the following prompt into the verification chat:

```text
Independently verify the R-01 normal-close save changes in:
C:\Users\fireball\OneDrive\Desktop\LiltTTS

This is verification only. The publisher subsequently authorized R-02, which is
now implemented and locally checked in the same workspace. Do not implement fixes.
Read docs/r02-results-2026-10-22.md and its current combined source-hashes.json.
Only backend/desktop.py differs from the original R-01 eleven-file manifest;
R-02 also changes Jobs/Bridge/Store/speech outside that manifest. Review the native
navigation/close overlap using the new snapshot. The original evidence is retained.
For full combined R-02 verification use docs/r02-independent-verification-prompt.md.

Read first:
- docs/r01-save-on-close-2026-10-22.md
- docs/HANDOFF.md, beginning with the current R-02 and R-01 sections
- docs/release-readiness.md, especially R-01 and the evidence boundaries
- .tmp/r01-close-20261022/source-hashes.json and saved logs/native result.json files

Treat the handoff as recorded claims with evidence to inspect, not automatic
approval. The implementation chat records 264 backend tests, 15 browser tests,
six debug-off native cases, a clean Svelte check and a frontend build for its
original snapshot. R-02 records 281 backend / 15 browser and six close reruns on
the combined snapshot. Verify scope and independently reproduce relevant checks.

Rules:
1. Do not edit/delete/move application source, tests, shared built assets or
   existing evidence. Preserve all uncommitted and untracked work. No add,
   commit, reset, checkout, stash, clean, dependency installation, personal-data
   access, model downloads, EXE/MSIX builds/installations or publication.
2. You may create disposable synthetic fixtures, logs and a review report in a
   new, uniquely named .tmp/r01-independent-* folder. Use existing tools only
   and -B with the project Python. The backup requirement was waived.
3. Record hashes of the implementation/test/built-asset inputs before and after
   verification. Distinguish documentation updates from source drift. If relevant
   source/assets change, qualify or repeat affected
   checks rather than silently combining different revisions.
4. Use existing built assets only after checking the saved manifest. Do not
   overwrite shared frontend/dist. If rebuilding/counterfactual testing is
   needed, use an isolated copy that includes the current untracked files and
   existing dependencies; do not alter the shared working tree or install tools.
5. Distinguish sandbox/tool failures from application assertion failures. Report
   missing tools or blocked checks rather than inventing passing results.

Inspect the tracked diff against HEAD plus these new/untracked files explicitly:
- backend/window_close.py
- tests/test_window_close.py
- tools/native-close-check.py
- docs/r01-save-on-close-2026-10-22.md

The base commit recorded for R-01 is
bdf58f1b4c89a269d0647050fe26f524e73b4c12. It already contains earlier refinements.
Older S-01–S-06 implementations and TXT/PDF/title/GPU fixes are not new R-01 work.

Review these boundaries:
- main.py installs the guard on the real application window.
- WinForms closing is canceled synchronously without waiting for JS/native API
  work on the UI thread; queued completion permits only the intended close.
- Initialization arms protection before editable UI can be used; startup failure
  and a clean close remain usable.
- Immediate close, continuous typing and an in-flight save followed by a newer
  edit preserve the latest text in SQLite, in order.
- Failed/slow saves keep the window open, preserve the edit, and permit retry or
  Keep editing/Escape. A timeout does not abort a database write.
- Cancel/retry, duplicate close events, and late/stale replies cannot later close
  the window unexpectedly, including cancellation after completion was queued.
- Closing does not need Spoken preparation; Ctrl+S/autosave/navigation/generation
  still refresh Spoken and preserve existing title/import behavior.
- The modal prevents normal editing/import/save shortcuts while closing and
  returns control after cancellation. Check failure paths as well as success.
- Close messages retain trusted-origin/size/request-ID/type checks; foreign
  origins and malformed/unsolicited/stale approval cannot close the app. The
  public method/arity allowlist must remain unchanged.
- Native dispatch/destroy failure and missing renderer responses do not silently
  grant close approval. Assess usability limits without claiming forced-kill,
  power-loss or OS-shutdown guarantees.

Use the commands/tool paths in the R-01 report. Run the focused backend suite,
the full backend suite, all 15 browser cases and the installed Svelte checker
where available. Reproduce the six native cases with fresh output folders:
immediate, inflight, retry, cancel, timeout, clean. The native helper uses real
Bridge/SQLite/WebView2 with injected save delays/errors, and programmatic WinForms
Close(); inspect it for false positives and add independent probes in your new
scratch folder where useful. Do not modify its shared copy.

Assess the saved pre-fix browser failure and, where useful, demonstrate a targeted
regression against the correct pre-R-01 baseline in isolation. Guard tests may
legitimately pass both versions; not every new test must fail without the fix.

Return:
- A concise verdict: passes, needs fixes, or insufficient evidence.
- Actionable findings ordered by severity, with absolute file/line references,
  trigger, expected/actual behavior and reproduction/evidence.
- A table separating actually rerun, saved evidence inspected, source inference
  and not checked, including exact counts and input hashes.
- Remaining limits and any documentation/test-harness claims that overstate proof.
- A recommendation on accepting R-01 source behavior, separately from release
  approval. No frozen/installed-MSIX, other-machine, licensing/privacy, GPU speech
  or Store-certification clearance follows from this review.

Stop after the verification report; do not apply fixes or message another chat.
```
