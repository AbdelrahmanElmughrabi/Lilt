# R-01 — normal-close save reliability — 22 October 2026

**Later R-02 update:** the publisher authorized R-02 after this original R-01 report. Its canceled-navigation adapter changes `backend/desktop.py`, the only changed input in R-01's preserved eleven-file hash manifest. All six native close cases and 15 browser cases passed again; the final combined backend suite passed 281 tests. Review the [R-02 results and combined snapshot](r02-results-2026-10-22.md) for the current boundary. Original R-01 counts/authorization below remain historical, not a claim that R-02 was never performed. Independent acceptance remains pending.

Status: **source implementation complete and locally validated; independent verification pending**. The publisher authorized trace → plan → implementation for R-01 only. No R-02 implementation, dependency installation, commit, EXE/MSIX rebuild/installation, personal-library access or publication was performed. The existing backup waiver remains in effect.

## Trace and plan

The existing frontend orders document writes through `saveChain` and drains them before navigation/generation. However, normal native closing had no save handshake: `main.py` subscribed only startup behavior, and component teardown canceled autosave timers. Closing before the one-second idle save or while a write was pending could lose the latest edit.

The installed pywebview 6.2.1 WinForms backend runs its cancellable closing handlers synchronously on the UI thread. Waiting for JavaScript/native API results there would risk deadlock. The selected plan cancels the initial close synchronously, queues a frontend request without waiting, drains writes asynchronously, then permits one native close after a matching success response. A failure/slow save keeps the window open with retry/keep-editing controls.

## Implementation

- `backend/window_close.py`: one per-window guard, armed only after frontend initialization; fresh request IDs; one active request; Boolean/matching-ID response checks; UI-thread queued script/close completion; current-page checks before dispatch/completion; cancellation/stale-response protection. A cancel can revoke an already queued approval. The uninitialized window remains closable before editable UI is enabled.
- `main.py`: installs that guard on the application window before the native event loop starts.
- `backend/desktop.py`: routes only `violilt:close-ready` and `violilt:close-response` through the existing trusted-origin/size-checked native transport. Responses require bounded request IDs and the guard validates the Boolean value. The public Bridge method/arity allowlist is unchanged.
- `frontend/src/App.svelte`: handles the native request, reuses `flushSave(false)` to drain ordered writes without waiting for Spoken preparation, and shows a modal with **Keep editing** and **Retry save and close** on failure. Ten seconds without completion shows a recoverable timeout; this does not cancel a database write. Attempt IDs suppress late success after cancel/retry. The modal prevents normal editor interaction, document-drop imports and save/import shortcuts while close is pending. Existing save/navigation/generation paths still request Spoken preparation by default.
- `tests/test_window_close.py`: nine native-guard/transport unit methods covering initialization, synchronous cancellation, deduplication, matching Boolean replies, stale responses, revocable queued completion, origin rechecks and native dispatch/destroy failures.
- `tests/test_editor_save.cjs`: six close regressions added to the existing nine browser cases.
- `tools/native-close-check.py`: repeatable debug-off current-source integration probe using a new synthetic library per case, real native transport/Bridge/SQLite and explicit injected save gates/errors. Outputs must be new folders under this workspace `.tmp`; no model downloads/generation or user libraries are used.

## Validation actually performed

| Check | Result | Scope / limits |
| --- | --- | --- |
| Before production edits | New immediate-close browser regression failed against the old built frontend: no close completion before its paused autosave timer | App regression reproduced in the outside-sandbox run. The initial sandbox attempt failed during Edge startup and is not app-defect evidence. |
| Focused backend | **16/16**, 0.099 seconds | Nine new guard methods plus seven existing desktop transport/security methods. Native objects are fakes in this suite. |
| Full backend | **264/264**, 35.044 seconds, exit 0 | Existing suite plus the nine new methods. Synthetic/disposable data and existing project Python with `-B`. |
| Built-frontend browser suite | **15/15**, 19.542 seconds, exit 0 | Existing nine behaviors plus immediate close, in-flight/latest snapshot, failed-save retry, keep-editing/late completion, timeout/Escape and duplicate-close/shortcut guards. Synthetic API; no unexpected page errors. |
| Svelte checker | **0 errors, 0 warnings**, exit 0 | Existing installed checker, final production frontend source. |
| Frontend build | **Passed** with existing Vite | A sandbox attempt hit a `realpath` EPERM; the authorized outside-sandbox build passed. This rebuilt frontend assets, not the EXE/MSIX. |
| Native source integration | **6/6 cases**, debug off, separate fresh synthetic libraries | Immediate close; in-flight older/newer snapshots; injected save failure then retry; keep editing then late completion/new edit; real ten-second timeout then cancel; clean close with no save. All report success and expected text from a fresh SQLite connection after shutdown. |
| Whitespace review | `git diff --check` passed | Only line-ending normalization warnings were emitted. |

The native probe invokes WinForms `Close()` through `window.destroy()`, traversing the same cancellable `FormClosing` event as the title-bar X/Alt+F4. It did not physically click the title bar. The retry case intentionally logs an `OSError` from its injected failed save; that is expected test input, followed by a passing retry. Native database checks reopen SQLite, not a second full application UI.

## Evidence and reproduction

Evidence directory: `.tmp/r01-close-20261022/` (ignored, preserve for review).

- `browser-before.log`, `browser-after.log`, `backend-focused.log`, `backend-full.log`, `svelte-check.log`.
- `native-immediate.log`, `native-inflight.log`, `native-retry.log`, `native-cancel.log`, `native-timeout.log`, `native-clean.log`.
- Each `native-<case>/result.json`, its isolated SQLite library and WebView test profile.
- `source-hashes.json`: production/test files and built frontend asset hashes for this tested snapshot.

Use existing tools; do not install dependencies. From the repository root:

```powershell
& .\.tmp\pronunciation-env\Scripts\python.exe -B -m unittest tests.test_window_close tests.test_desktop -v
& .\.tmp\pronunciation-env\Scripts\python.exe -B -m unittest discover -s tests -v
$env:PLAYWRIGHT_MODULE = 'C:\Users\fireball\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules\playwright'
node --test tests/test_editor_save.cjs
& .\.tmp\pronunciation-env\Scripts\python.exe -B tools/native-close-check.py --case immediate --output .tmp/r01-independent-immediate
```

Build the current frontend before browser/native reproduction using the existing `frontend/node_modules` Vite; run Svelte check from `frontend`. Repeat the native command with cases `inflight`, `retry`, `cancel`, `timeout`, `clean`, each with a new output folder. Use disposable TEMP/TMP and existing tools. Sandbox restrictions on browser/native launch, loopback or Vite path access must be distinguished from application failures.

## Independent review and remaining boundaries

The next step is to return this batch to the verification chat. This implementation chat does not provide independent clearance. Review the native/UI race boundaries, failures/cancellation, unchanged public dispatch restrictions, the existing nine editor regressions and recorded outputs before accepting R-01. Include the new untracked guard/test/native-helper/report files when transferring work; ordinary tracked-file diffs alone omit them. No automatic message was sent to another chat.

This batch does not establish behavior for forced process termination, power loss, physical disk-full, Windows shutdown/restart, an unresponsive/crashed renderer, a physical title-bar click or independently observed GPU/CPU speech generation. A missing renderer response never grants close approval after arming. Playback-position/settings-close guarantees are not expanded by this document-save fix.

Existing EXE/MSIX artifacts still predate these refinements. Final-package, installed-MSIX, mandatory other-machine, low-end/no-GPU, licensing/privacy and Store-certification gates remain open and separate. After independent source verification, re-exercise normal-close behavior in the final package.
