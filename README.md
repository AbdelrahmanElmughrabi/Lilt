# Lilt

A Windows desktop reading room for turning English Markdown into local narration. Built with **pywebview + Svelte + Python + Kokoro-ONNX**. Lilt uses warm ivory, deep ink, muted lilac, and soft sage. Settings offers Lilt (default) and Classic palettes, each with light, dark, or Windows appearance.

## Pronunciation evaluation branch

This branch uses offline Misaki 0.9.4 English, without its `en` extra or eSpeak fallback, through an attributed Kokoro inference adapter. Launch `dist\pronunciation\Lilt\Lilt.exe` to try the candidate. Keep its entire folder together. Its default library is `%LOCALAPPDATA%\Lilt-Pronunciation-Evaluation`; it does not migrate the existing library. `LILT_EVALUATION_DATA_DIR` or an explicit `--data-dir` selects another evaluation folder. General `LILT_DATA_DIR` / `FOLIO_DATA_DIR` overrides do not select this candidate's default library.

Unfamiliar English words may be spelled aloud. Accented Latin text may use its English spelling; both produce visible notices. Pronunciation fallback handles punctuation inside unfamiliar tokens, including compact number lists, as well as grouping, thousands separators, decimal digits and currency amounts. Numeric en-dash ranges use “to,” negative values use “minus,” and approximate amounts such as `~10` use “about.” Sentence punctuation retains its pause marks. Common graphic symbols are read by their listed names, such as `➔` becoming “right arrow.” Unlisted symbols are omitted individually from the speech copy while surrounding words remain; Read/Edit keep the original Markdown and Spoken shows the prepared wording. The omitted-symbol count is shown in the preview/player, and `jobs/<recording-id>/unread.txt` inside the local data folder lists each omitted symbol and its Unicode code points. The report describes the prepared text, including later passages that may not have been generated if a reading was stopped. Actual non-English words and model/integrity failures can still stop generation. Saved WAV playback remains independent of pronunciation. A partial reading from another pronunciation identity can still be played, but must be generated as a new reading. Cache entries and performance recommendations also include pronunciation identity.

The speech copy adds spaces around selected code operators/grouping marks so expressions such as `generate(seed, version)` and `body=3` can use ordinary word pronunciation. Brackets and commas retain their punctuation role, while operator pronunciation retains its meaning. Word spelling/case and original Markdown stay unchanged; Spoken shows the added spacing. Straight/curly apostrophes retain contractions and possessives and are never renamed as the word “apostrophe.” Numeric commas, decimal/currency formats and common URLs/email addresses are protected from the spacing edits.

The candidate is a development evaluation pending listening and distribution review. Lilt-owned source can remain proprietary subject to compatible third-party terms. Required texts, covered component source and remaining release gates are described in [thirdparty/PRONUNCIATION-CANDIDATE.md](thirdparty/PRONUNCIATION-CANDIDATE.md) and collected beside the executable in `third-party/`. Changing external pronunciation libraries requires restarting Lilt; changed source/assets invalidate compatible continuation and caches.

## Open the preserved baseline

Double-click **`dist\Lilt\Lilt.exe`**. Keep the entire `Lilt` folder together: the executable needs `_internal` and `models` next to it. Python, Node, a terminal, and a browser tab are not needed to run this build.

The project folder also retains the **Lilt shortcut** from the preserved `main` baseline. Current-branch builds use the separate candidate output and do not replace this shortcut. The CPU app is approximately 243 MB including its model/runtime. This build also includes an optional `gpu-runtime` folder (~2.9 GB) and GPU model (~177 MB), making the full folder about 3.35 GB. Keep `gpu-runtime` to use NVIDIA acceleration; the CPU app works without it.

The build includes the local model and voice assets, so speech is ready immediately. Windows needs the Microsoft **WebView2 Evergreen Runtime**, normally already available on Windows 10/11. If it is missing, install it from [Microsoft](https://developer.microsoft.com/en-us/microsoft-edge/webview2/).

Lilt opens on **Home**, with recent readings, saved recordings, and **Continue listening** from your saved position. Completed audio is saved automatically as WAV; reopening or playing it does not generate it again. Use the recording's download button to export a copy for listening elsewhere.

1. Import a UTF-8 `.md` / `.markdown` file, or add a reading and paste text in **Edit**.
2. Use **Read** for formatted Markdown or **Spoken** to check the wording sent to the voice.
3. Choose an English voice, try its sample, and adjust narration speed and paragraph pauses.
4. Select **Create your audio**. Stop after the current section if needed; **Your recordings → Continue** resumes saved sections.
5. Listen in the bottom player as sections arrive. Seek within available audio; Export becomes available when the complete WAV is ready.
6. Open **Settings → Less waiting. More listening.** to run a speed test, choose processing resources, or adjust buffering.

Documents are working copies: editing or removing one does not change its original file. Removing a recording keeps its audio on disk unless you explicitly select deletion. Normal app data lives in `%LOCALAPPDATA%\Lilt`: SQLite library/settings, model downloads, section audio, completed WAVs, and WebView cache. `LILT_DATA_DIR` overrides that location for development.

Existing users are migrated on first launch: Lilt copies the previous `%LOCALAPPDATA%\Folio` library, model downloads, section cache and saved audio into its new folder, leaving the old folder as a backup. Appearance and performance preferences are retained; Lilt becomes the default palette. Existing Lilt libraries are never replaced. Old `FOLIO_DATA_DIR` / `FOLIO_GPU_RUNTIME` overrides and GPU validation markers remain accepted for compatibility.

## Included

- Local English narration with 28 bundled American and British voices.
- Home with recent-open times, saved WAV playback/export, listening-position recovery, and unfinished recordings.
- Markdown editing and automatic working-copy saves; formatted and spoken previews.
- Headings, paragraphs, lists, quotes, link labels, image alt text, and tables.
- Code blocks omitted by default, with a toggle to include them; document front matter omitted.
- Background speech process, early listening, section progress, cancellation, and checkpoint-based continuation.
- Quiet/Balanced/Fast/Custom processing, real CPU thread controls, worker CPU usage, and generation-rate feedback.
- Local speed test with cancellation and hardware/model-specific Auto recommendations.
- Optional NVIDIA CUDA acceleration, startup voice preparation, and bounded reusable-passage cache.
- Immutable text/settings snapshots, disk-based WAV assembly, persistent library and listening position.
- Playback, seeking, skip controls, volume, playback speed, and native WAV export dialogs.
- Lilt and Classic palettes, each with Daylight, After hours, and system appearance; keyboard shortcuts and visible focus.
- Visible model setup/download/import when assets are missing.

There are no paid TTS APIs or app analytics. Model setup fetches assets from the Kokoro-ONNX project's GitHub release; generation uses local files. Imported Markdown cannot load remote images or execute scripts in the preview. The embedded Microsoft WebView2 runtime has its own [diagnostic behavior](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/data-privacy).

## Develop

Use Python 3.12 and Node 20.19+ / 22.12+. On this evaluation branch, install its separate environment and run with separate data:

```powershell
& .\setup-pronunciation.ps1
Push-Location frontend
npm.cmd ci
npm.cmd run build
Pop-Location
& .\run-pronunciation.ps1
```

The source launcher uses `.tmp\pronunciation-eval\data` and copies any existing model files there without changing the originals. If assets are missing, use the candidate app's Settings to download/import them, or download into this same isolated library:

```powershell
& .\.tmp\pronunciation-env\Scripts\python.exe tools\setup_models.py --data-dir .tmp\pronunciation-eval\data
```

The frontend development preview is available through `npm run dev`; native file dialogs and real speech are available in the desktop app. Production uses the compiled local frontend, with no development server dependency. A read-only server on a random loopback port supplies UI files and audio seeking; application commands go through the pywebview bridge.

`main.py --serve-preview` prints an explicit `?preview=1` URL for interface checks. A failed desktop connection shows a retry screen; the normal application never substitutes preview/sample data for your library. The pinned pywebview version uses an application-owned CSP adapter to build API methods and deliver native callbacks without `eval` or `new Function` execution. The strict script policy stays enabled.

## Build and checks

```powershell
& .\build.ps1
# Add -IncludeGpu to include the previously validated optional runtime.
& .\.tmp\pronunciation-env\Scripts\python.exe -m unittest discover -s tests -v
& .\.tmp\pronunciation-env\Scripts\python.exe tools\smoke_test.py
& .\.tmp\pronunciation-env\Scripts\python.exe tools\native-startup-check.py
```

`build.ps1` is the canonical build on this branch. It uses `requirements.lock.txt`, `packaging/Lilt.spec`, `build\pronunciation`, and `dist\pronunciation`. `build-pronunciation.ps1` forwards to it for existing candidate commands. Both paths use the current pronunciation environment, collect notices/covered source, and audit the actual executable/archive. The retained baseline executable, environment and shortcut stay separate.

Only runtime application code is frozen. Integration checks and sample generation are source-only developer tools. Run `tools/pronunciation_integration.py --output <new-directory> --device cpu` (or `gpu`) for early media, exact streamed/exported samples, cache reuse, cancellation/restart and benchmarks. Run `tools/pronunciation_samples.py --output <new-directory> --device cpu` for current-engine listening samples. Previously generated baseline/candidate A/B clips remain in the Obsidian evaluation evidence; baseline reproduction uses the preserved `main` revision. The executable does not contain baseline comparison code or the development evaluation CLI.

Build reads available assets from `.app-data\models` and a validated GPU runtime from `.cuda-probe` by default, without altering either. Use `-ModelDirectory` and `-GpuRuntimeDirectory` for separate candidate assets. The old baseline dependency declarations/build recipe remain available through `main` history.

Developer-only desktop checks in `tools/ui-check.cjs`, `tools/desktop-flow.cjs`, and `tools/long-reading.cjs` attach Playwright to the app's embedded WebView2 when explicitly launched with `WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS=--remote-debugging-port=9223`. Normal launches do not enable that debugging port. Set `LILT_PLAYWRIGHT` to a Playwright module location if it is not installed in the local Node environment.

`tools/native-startup-check.py` checks normal WebView2 startup with debugging off, isolated data, Home, native commands, WAV playback, and position recovery. `node tools/home-flow.cjs` checks the production CSP, late/missing bridge connections, stalled startup and retry, empty libraries, Home navigation, and light/dark/small-window layouts using fixture data. It requires Microsoft Edge and Playwright, plus the local Python environment's pywebview JS assets.

## Performance and local GPU setup

Processing performance, narration speed, and playback speed are independent. Quiet uses one CPU thread, lower process priority, and slight pacing. Balanced limits CPU work; Fast uses an efficient measured configuration. Custom exposes 1–16 threads on this PC. Auto stays on CPU until a matching speed test recommends the available GPU. The GPU build uses the same local narration workflow, with a GPU-friendly FP16 model; small numerical differences from the CPU INT8 model are expected.

The speed test compares warmed inference, excludes model loading and cached passages, and prefers fewer CPU threads when results are within 5%. Results are tied to model/runtime/hardware identities. More threads do not guarantee faster speech. CPU utilization is measured for the speech process, normalized to the machine's logical processors.

Baseline measurements on this i7-11800H / RTX 3060 Laptop GPU (not candidate performance guarantees): representative CPU passages produced approximately 1.0–1.1 audio seconds per processing second; NVIDIA produced approximately 10–12.5. A real 89-second recording generated in 8.1 seconds, with its first section available after 2.4 seconds. A warmed packaged run produced 68 seconds in 8 seconds; all 12 sections were reused on a repeat in 0.31 seconds. Cold GPU DLL/model loading took about 22 seconds on the first packaged run and can vary; optional startup preparation reduces the wait for a later request. These measurements are examples from this PC.

Automatic playback follows Start sooner (~1 second), Balanced (adaptive ~4–10 seconds), or Fewer interruptions (~24 seconds) of decoded audio. Manual Play starts any available audio. If generation is slower than playback, the player freezes at the last available sample and continues once its buffer is ready. Decoding/prefetch is bounded; the final exported WAV matches the raw section audio and intended pauses. Partial recordings retain listening position and can be played/continued after restart.

Reusable speech is keyed by text, voice, narration speed, model/voice content, and runtime identity. The 128/256/512 MB limit evicts least-recently-used passages. Clearing it leaves saved recordings untouched. Continuation keeps the original snapshot and section layout; it refuses changed model files and, on this branch, changed pronunciation identity.

The bundled NVIDIA add-on is optional and requires a compatible NVIDIA driver. DirectML was evaluated but failed Kokoro synthesis on both adapters here. For source development, install GPU dependencies separately and validate them before packaging:

```powershell
& .\.tmp\pronunciation-env\Scripts\python.exe -m pip install --target .tmp\pronunciation-gpu-runtime -r requirements-gpu.lock.txt
& .\.tmp\pronunciation-env\Scripts\python.exe tools\download_gpu_model.py --models .tmp\pronunciation-eval\data\models
& .\.tmp\pronunciation-env\Scripts\python.exe tools\probe_cuda.py --runtime .tmp\pronunciation-gpu-runtime --models .tmp\pronunciation-eval\data\models
$env:LILT_GPU_RUNTIME = Join-Path (Get-Location) '.tmp\pronunciation-gpu-runtime'
& .\build.ps1 -IncludeGpu -GpuRuntimeDirectory .tmp\pronunciation-gpu-runtime -ModelDirectory .tmp\pronunciation-eval\data\models
```

The probe verifies finite audible output and actual CUDA nodes before writing its validation marker. Generation refuses an unavailable requested GPU instead of silently running a different backend. `LILT_GPU_RUNTIME` can point to a validated runtime folder. Keep base CPU dependencies separate from the optional GPU installation.

## Current boundaries

This first build exports WAV. MP3, queues, pronunciation overrides, bookmarks, and read-along highlighting are later work. Processing speed depends on the selected CPU/GPU backend and hardware; cancellation takes effect after the current section. Long readings use section files and incremental assembly, with disk space and the WAV size limit as practical constraints.

The executable is a portable development build, not a signed installer. It has been verified on this Windows PC; clean-machine installation and release signing remain distribution work.

## Source map

`main.py` owns the desktop lifecycle. `backend/documents.py` prepares narration, `jobs.py` owns job state, `speech.py` runs inference, `server.py` serves local audio, `storage.py` persists the library, `models.py` handles assets, and `bridge.py` exposes desktop commands. `performance.py`, `cache.py`, and `sections.py` own tuning, reuse, and the published timeline. `pronunciation.py` owns offline English coverage/identity, and `kokoro_engine.py` adapts the licensed inference helpers in `backend/_vendor/kokoro`. `backend/desktop.py` adapts the native bridge for strict CSP. `frontend/src/App.svelte` contains the UI shell, `Home.svelte` the landing page, `PerformanceSettings.svelte` the tuning panel, and `stream-player.ts` the bounded live player; `tokens.css` and `styles.css` define its theme.
