# Folio — product plan and implementation status

Status: the portable Windows build and the earlier-listening/performance milestone are implemented. The agreed stack is pywebview, Svelte, Python, and Kokoro-ONNX. Reading/editing, local voices, background generation, cancellation/resume, the library, player, WAV export, model setup, and themes are connected to real application data. Source, dependencies, and a Windows executable are present in this workspace. The performance controls, section cache, adaptive player, speed test, and optional NVIDIA runtime are connected to real inference.

Validation: Svelte type checks and the production build pass. Twenty-nine focused Python tests pass. The packaged executable generated a 196-word, 12-section recording, played and sought it, and restored its listening position after reload. A separate 673-word, 31-section packaged-worker run passed cancellation and continuation, preserving the first saved section; its final recording is approximately 138 seconds at 1.8× narration. A 4,000-word extraction test checks complete, ordered section coverage.

Distribution still needs a signed installer and clean-machine verification. The current deliverable is `dist/Folio/Folio.exe` with its adjacent `_internal` and `models` folders. MP3 and the follow-ups below remain later work. See `README.md` for running, building, storage, and current boundaries.

## Agreed direction

- A Windows desktop application with its own window, icon, and executable.
- English narration of short or long Markdown documents and pasted text.
- Read the supplied wording; do not summarize or rewrite it into a podcast script.
- Speech runs locally after the required model assets and runtime dependencies are available.
- A polished interface intended for regular personal use: warm paper, charcoal, copper, sage, serif headlines, and light/dark/system themes.
- Stack: pywebview, Svelte, Python, and Kokoro-ONNX.

## Implemented first build

| Area | Features | Expected behavior |
|---|---|---|
| Input | Open `.md` / `.markdown` files; paste or edit Markdown | Keep a local working copy. Editing in the app does not overwrite the imported file. |
| Reading preview | Rendered document and a preview of the text that will be spoken | Make skipped content visible in the spoken-text preview. Show word count and an approximate reading duration. |
| Markdown options | Code-block toggle; heading and paragraph pauses | Read heading/list text without syntax markers and link labels without their URLs. Code blocks are skipped by default, with an explicit setting to include them. |
| Voices | 28 available English voices, a short voice preview, narration speed | Preview uses a short original sample. Changing settings creates a new generation rather than modifying an existing recording. |
| Generation | Generate, completed-section progress, cancel, retry/resume | One active speech job at a time. Report sections completed rather than claiming an exact time remaining. Preserve completed sections for recovery. |
| Playback | Play/pause, seek, volume, playback speed, resume listening | Playback speed changes listening only; narration speed changes the generated recording. Remember the last position for each recording. |
| Library | Recent documents and saved recordings | Reopen a document or play an earlier recording with its saved voice/settings. Allow removal of an app record; deleting audio is an explicit separate action. |
| Export | Save/copy the finished recording as WAV | Produce one combined audio file. Do not overwrite an existing export without the user's explicit choice in the save dialog. |
| Appearance | Consistent layout, light/dark/system modes, responsive sizing | Use reusable colors, typography, spacing, and controls so the eventual theme is easy to change. |
| Settings/setup | Model readiness, model asset setup/import, storage location, remembered defaults | Model setup is a visible one-time step. Normal generation uses local files and does not silently download missing assets. |

Earlier listening and generation performance are implemented, as described below. MP3 export is the next optional milestone. Other later additions: multiple-file queues, read-along highlighting, bookmarks, pronunciation overrides, drag-and-drop import, voice presets, and optional tray behavior.

## Implemented: earlier listening and performance settings

Status: implemented and verified with real CPU/CUDA inference and native desktop playback. See `PERFORMANCE_PLAN.md` for the implementation sequence and evidence. NVIDIA acceleration is available through the optional local runtime; DirectML failed synthesis on this PC and is not the shipped accelerator.

| Priority | Addition | Behavior and tradeoff |
|---|---|---|
| 1 | Listen while generating | Make completed sections playable before the document finishes. Continue inference in the background, preserve paragraph/heading pauses, and retain one final WAV for export. Show available audio separately from generation progress. If playback reaches unfinished audio, buffer and continue automatically when more is ready. |
| 1 | Listening-start preference | Offer Start sooner, Balanced, and Fewer interruptions. These choose an initial audio buffer, not a promise of immediate or uninterrupted playback. An adaptive default accounts for observed generation speed and the chosen playback rate. |
| 1 | Performance presets | Offer Quiet, Balanced, Fast, and Custom. Presets control speech-worker CPU threads and optional pacing/normal or below-normal process priority. Quiet leaves more resources for other apps; Fast uses a measured efficient configuration. |
| 1 | Advanced CPU control | Expose Auto or an explicit thread count within the available processors. Show measured speech-worker utilization. A thread budget or approximate CPU target is not an exact system-wide CPU percentage; OS scheduling and model operations determine actual load. Thread changes that require a new inference session should apply at a clearly stated boundary. |
| 1 | Speed test and useful feedback | A user-triggered local benchmark compares a small set of thread counts using representative speech after warm-up. Report time to first audio, generated audio seconds per processing second, and playable audio ahead. Separate initial model loading from steady-state inference; retain the result for this hardware/model configuration. |
| 2 | Adaptive section sizes | Use a short, meaningful first passage to reduce the initial wait, then benchmark larger later passages to reduce overhead. Preserve sentence boundaries, wording, order, pauses, cancellation checkpoints, and model input limits. Avoid exposing engine chunk sizes in the everyday flow. |
| 2 | Optional GPU acceleration | Offer Auto, CPU, or an actually available and tested GPU backend. Validate provider/model compatibility and measure whether it improves this machine's speed. Keep CPU available and show the backend actually used. The current folder includes a validated NVIDIA CUDA runtime and FP16 GPU model. CPU remains available; Auto uses a matching speed-test result. |
| 2 | Optional startup warm-up | Load the voice engine while the user reads or edits, with an explicit preference because it uses RAM earlier. The existing app already keeps its engine loaded after the first job; this extends that behavior to a new app session. |
| 3 | Cache unchanged passages across jobs | Reuse section audio when prepared text, voice, narration speed, and engine/model identity match, including after small document edits. Keep pause assembly separate, bound disk usage, and offer cache clearing. Checkpoints also preserve the original section layout within the same immutable job. |

Keep **performance** separate from **narration speed** and **playback speed**. More compute changes processing time; it should preserve the selected voice and spoken pace. The app already uses an INT8 model and reuses its loaded inference session, so those are existing foundations rather than new promised optimizations.

Implement settings under a Performance area in Settings, with a compact preset selector and live generation/buffer status in the reading room. Use measured values rather than a cosmetic percentage slider. [ONNX Runtime threading controls](https://onnxruntime.ai/docs/performance/tune-performance/threading.html) provide thread-count and spinning settings; more threads or more power do not inherently yield better throughput. [Kokoro's streaming example](https://github.com/thewh1teagle/kokoro-onnx/blob/main/examples/with_stream.py) demonstrates incremental synthesis/playback.

Completion checks: first audio becomes usable while a sufficiently long job is still generating; playback consumes each section once in order with intended pauses; pause/resume, seeking within available audio, cancellation, and app restart preserve a coherent position; the assembled final export matches the streamed sections. Resource settings retain their values, report the active configuration, keep the UI responsive, and are benchmarked before claiming improvements. No new APIs or subscriptions are introduced.

The first release is complete when a user can install the app, open a Markdown document, preview the spoken wording and voice, generate a full recording, export it, and return later to resume playback. A short demo alone does not satisfy the long-document requirement.

## Screen layout

- Left: recent documents and recording library.
- Center: the Markdown document, with a switch to its spoken-text preview.
- Right: voice, narration speed, Markdown reading options, and generation controls.
- Bottom: a persistent audio player.

At smaller window sizes, collapse the library and move voice/settings controls into a panel. Keep the player and primary action accessible. Include keyboard navigation, visible focus, readable contrast, and useful empty/loading/error states from the first UI implementation.

The first theme is implemented using reusable design variables. Typography, accent colors, surfaces, and corner styles can change without redesigning the workflow.

## Application logic

1. **Import:** read the chosen file or pasted text into a document snapshot. Prefer UTF-8; show a useful error or encoding choice rather than silently replacing unreadable characters. Preserve the original source reference and keep edits in the app's working copy.
2. **Prepare Markdown:** parse Markdown structure with [markdown-it-py](https://markdown-it-py.readthedocs.io/en/latest/using.html). Extract readable text from headings, paragraphs, lists, quotes, and link labels. Preserve wording and order. Skip fenced/indented code according to the setting, remove metadata/front matter from speech, and use image alt text when present. Read table cells in row order with clear separators. Treat embedded HTML as content to extract or omit, never as executable app UI.
3. **Review:** display the exact normalized text that will be sent to speech generation. Record which kinds of content were omitted. Require some readable text before enabling generation.
4. **Split:** divide the prepared text into sections at paragraphs and sentence boundaries. Keep sections within tested engine limits; split unusually long sentences again rather than truncating them. Plain text must also work without punctuation. Every part of the prepared text must be covered once, in order.
5. **Snapshot a job:** capture document contents, reading options, voice, narration speed, and model/engine identity. A running job uses this snapshot even if the editor changes afterward.
6. **Generate:** send the job to a dedicated background speech process. Load the model lazily on the first preview/job and reuse it while the app is open. Write each completed section to a temporary local WAV and checkpoint progress. Keep the UI responsive and allow only one active inference operation.
7. **Recover:** reuse completed sections only when the snapshot, settings, and model identity match. After cancellation, an error, or an app restart, offer continuation from the first unfinished section. Cancellation stops after the current inference section completes; the UI must explain that boundary rather than promising an immediate stop.
8. **Assemble:** append completed sections and the planned pauses to a combined WAV incrementally. Check format consistency, verify the result, then publish it with an atomic move into the library. Never label a partial recording as complete.
9. **Play/export:** expose the finished recording through a controlled local media route for the player. Store playback position and recording metadata. Export by copying to the path chosen in the save dialog.

Job states: `preparing → generating → assembling → completed`, with explicit `cancelling`, `cancelled`, `failed`, and `interrupted` states. Model readiness and playback state are separate from generation state. Errors should identify the failed step and offer a relevant next action.

Long recordings are written and assembled on disk rather than held as one giant audio array. Length remains subject to available storage and processing time; there is no subscription or character quota.

## Implementation structure

| Layer | Responsibilities |
|---|---|
| Svelte + TypeScript + Vite | Screens, reusable components, theme variables, editor/preview, playback controls, and displaying job state |
| pywebview shell | Window lifecycle, native file/save dialogs, and a small explicit Python bridge |
| Python document service | Markdown extraction, reading options, coverage-preserving section splitting, and document snapshots |
| Python job controller | A synchronized job state machine, worker lifecycle, checkpoints, retries, and progress events |
| Speech worker | Kokoro-ONNX inference using local model/voice assets; section audio output |
| Audio service | Incremental WAV assembly, validated media access, and export |
| Storage | SQLite from Python's standard library for documents, jobs, recordings, and settings; audio and model assets stored separately |

The [pywebview bridge](https://pywebview.flowrl.com/guide/interdomain.html) supports direct JavaScript/Python calls. Exposed calls may execute concurrently, so the Python controller must own and synchronize job state. Use structured payloads and identifiers rather than embedding document text into JavaScript strings.

Bundle the frontend's production assets locally. Use the bridge for app commands and a narrowly scoped loopback media service for audio playback; the user does not start a separate server or browser. [pywebview architecture](https://pywebview.flowrl.com/guide/architecture)

Implemented folder responsibilities:

```text
frontend/                 Svelte interface and design variables
main.py                   Desktop entry point
backend/bridge.py         UI-facing commands
backend/documents.py      Markdown and spoken-text preparation
backend/jobs.py           Job control and recovery
backend/speech.py         Local engine adapter and worker
backend/server.py         Local assets and media; assembly is in speech.py and export in bridge.py
backend/storage.py        Settings and library persistence
tests/                    Focused behavior and recovery checks
packaging/                Portable executable configuration
```

App-managed data belongs in a per-user application data directory, separate from the installation folder. Store an immutable snapshot for each generation, not only a path to a source file that might later change.

The app will use bundled UI assets and local speech processing without app analytics, remote fonts, or fetching resources embedded in Markdown. Configure document preview and navigation so imported content cannot invoke privileged bridge commands or load remote pages. Microsoft's WebView2 diagnostic behavior remains a separate runtime consideration. [Microsoft privacy documentation](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/data-privacy)

## Build sequence and completion checks

1. **Verify the desktop and speech foundations.** Create a minimal packaged window and generate a short WAV with local Kokoro model assets. Confirm the Windows phonemizer/runtime dependencies, output quality, and CPU speed on this PC. Verify a background worker starts correctly in the packaged executable. Completion: real speech and a real desktop window work with networking unavailable after setup.
2. **Define the UI structure and build the desktop shell.** Implement the main layout, reusable design variables, and useful states with sample document/library data. Then connect native import/save dialogs and persistent settings. Completion: the app looks coherent at normal and smaller sizes and opens without a terminal or browser tab.
3. **Implement Markdown reading.** Add the working-copy editor, Markdown view, spoken-text view, reading options, and sentence/section splitting. Completion: representative headings, lists, links, code blocks, tables, HTML, and very long paragraphs preserve the expected readable wording and order.
4. **Connect generation.** Implement the engine adapter, worker, progress, cancellation, checkpointing, and disk-based audio assembly. Completion: a long document generates fully while the interface responds, and a cancelled/interrupted job resumes without duplicating or skipping completed sections.
5. **Complete the everyday workflow.** Connect the player, playback position, recording library, document reopening, and WAV export. Completion: the generated recording remains usable after an app restart, seeks correctly, and exports to a user-chosen location.
6. **Package and verify the full application.** Build the frontend, freeze the Python app with PyInstaller, bundle the required resources, and create a Windows installer/shortcut. Keep large model assets separate from a single self-extracting executable to reduce repeated startup work. [pywebview packaging guidance](https://pywebview.flowrl.com/guide/freezing)
7. **Add MP3 export and selected refinements.** Choose an encoder, measure the packaged size and startup/idle memory, and refine the chosen theme. Completion: export plays in common players and the final app has no development-server dependency.

Pin dependency versions after the foundation check. The exact engine model, voice assets, and packaging configuration should be based on that working result rather than an untested version combination. Kokoro's [local WAV example](https://github.com/thewh1teagle/kokoro-onnx/blob/main/examples/save.py) provides the starting integration shape.

## Validation priorities

- Markdown extraction and section coverage: expected words appear once, in order; selected omissions are accurately shown.
- Real synthesis: short samples, ordinary prose, numbers/acronyms, unpunctuated text, and a document long enough to exercise many sections.
- Job recovery: cancellation at a section boundary, failure during assembly, and restart with a partially completed job.
- Persistence: original imported files stay untouched; library/settings/player position survive a restart; changed voice/settings cannot reuse incompatible audio sections.
- Privacy behavior: document previews do not fetch external resources; model inference works without network access after setup; app commands accept only appropriate document/job/media identifiers.
- Windows packaging: launch on a machine without separately installed Python or Node; verify required WebView2/phonemizer assets, worker startup, native dialogs, playback, paths with spaces/non-ASCII characters, and read-only installation directories.

## Decisions still open

- Whether to keep the working name, Folio, and refine its current theme.
- Favorite/default English voice, based on listening to samples.
- Any refinements to the current natural/short/unhurried paragraph pauses.
- Whether MP3 export should ship with the first installer or immediately afterward.

These can be decided during the relevant milestone; they do not require changing the agreed stack.
