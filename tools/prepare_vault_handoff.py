"""Prepare the dated Obsidian handoff in workspace staging; publication is separate."""
from pathlib import Path
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / 'artifacts' / 'vault-handoff-2026-10-08'
STAGE.mkdir(parents=True, exist_ok=True)
DATE = '2026-10-08'

def note(name, body):
    header = f'---\ncreated: {DATE}\nupdated: {DATE}\ntags: [lilt-tts, project-handoff]\n---\n\n'
    (STAGE / (name + '.md')).write_text(header + body.strip() + '\n', encoding='utf-8')

note('00 Start Here', r'''
# LiltTTS — project handoff

Snapshot of the work completed on **8 October 2026**. This vault is named **LiltTTS**; the implemented application still uses the working name **Folio**. Renaming the product has not been implemented or decided by this note.

## Current position

We have a working portable Windows desktop application for reading English Markdown aloud locally. The first application milestone and the streaming/performance milestone are implemented. Real CPU and NVIDIA speech, native playback, caching, cancellation, and process-restart recovery have been exercised. The final suite has **29 passing Python tests**, passing Svelte checks/build, and separate desktop/scheduler checks.

The source and executable live at:

```text
C:\Users\fireball\OneDrive\Desktop\TTS
C:\Users\fireball\OneDrive\Desktop\TTS\dist\Folio\Folio.exe
```

Keep the portable folder together. It is a development build, with release signing, an installer, and clean-machine validation still pending.

## Read the handoff

| Note | Purpose |
|---|---|
| [[01 Product and Decisions]] | Intent, constraints, stack, naming, and boundaries |
| [[02 Features and UI]] | Implemented everyday workflow and visual design |
| [[03 Architecture and Data Flow]] | Modules, generation/player logic, persistence, and recovery |
| [[04 Performance and Benchmarks]] | Every optimization, defaults, measurements, and GPU tradeoffs |
| [[05 Testing and Fixes]] | Verification evidence, bugs corrected, and regression checks |
| [[06 Development and Packaging]] | How to run, build, test, and reproduce the GPU setup |
| [[07 Roadmap and Next Session]] | Unfinished work, proposed priorities, and restart context |
| [[08 Work Log 2026-10-08]] | Milestone history and the final handoff state |

## Evidence and source snapshots

- `Evidence/2026-10-08/` contains the retained benchmark/recovery JSON reports and selected UI screenshots.
- `Reference/2026-10-08/` contains copies of the source README, product plan, performance plan, and dependency locks at this handoff.
- Notes describe the final implementation; source snapshots also retain some historical planning language.
- Measurements are from this PC, rather than performance guarantees for other systems. Loading, warmed inference, cache hits, and whole-job time are different measurements.
- This is a documentation handoff, not a backup of the application source, model weights, user library, or audio. The project directory remains necessary for continued development.

## Quick orientation

The stack is **pywebview + Svelte + Python + Kokoro-ONNX**, packaged with PyInstaller. It opens its own Windows window; it uses embedded WebView2 for the interface without requiring a browser tab or a frontend development server. Text is read faithfully rather than rewritten into a podcast script.

The RTX 3060 Laptop GPU measured roughly **10–12.5 audio seconds per processing second** on representative warmed passages. A cold packaged CUDA load measured about **22 seconds**. The optional GPU runtime adds roughly **2.9 GB**, plus a **177 MB** GPU model. The base CPU app is roughly **243 MB** and was verified with the GPU directory disabled.

Start with [[07 Roadmap and Next Session]] before making the next implementation decision.
''')

note('01 Product and Decisions', r'''
# Product and decisions

Related: [[00 Start Here]] · [[02 Features and UI]] · [[07 Roadmap and Next Session]]

## What the user wanted

- Give the app short or long text and listen to it.
- Start with English Markdown (`.md` / `.markdown`) and pasted text. Other file formats are outside the current scope.
- Run speech locally without paid TTS APIs or subscriptions.
- Use a normal desktop application instead of opening a browser tab.
- Have a polished, customizable interface suitable for everyday personal use.
- For long readings, begin listening before the whole recording finishes.
- Offer useful controls over generation resources and speed, without misleading utilization promises.

The initial podcast wording was clarified to **reading the provided text**. Summaries, rewritten scripts, conversational hosts, and generative podcast transformation are not part of the implemented app.

## Settled stack

| Layer | Choice | Role |
|---|---|---|
| Desktop host | pywebview | Native window and Python bridge; WebView2 on Windows |
| Interface | Svelte + TypeScript | Custom visual design and interactive controls |
| Frontend tooling | Vite | Compile local production assets |
| Application logic | Python | Markdown preparation, jobs, settings, files, and inference integration |
| Local voice engine | Kokoro-ONNX + ONNX Runtime | English speech with local model/voice files |
| Persistence | SQLite and local files | Working copies, job snapshots, settings, positions, and WAVs |
| Packaging | PyInstaller portable folder | Executable without a separate Python/Node installation |

PySide/Qt and Tauri were discussed during stack exploration. The implemented choice is pywebview with Svelte; no framework migration is required for the next milestone. Classic Windows app stacks were also discussed as context, not selected for this build.

## Identity and design

The executable, window title, data folder, and UI currently say **Folio**. The vault's **LiltTTS** name is documentation context, not an automatic code rename. A future rename needs coordinated UI, executable, shortcut, packaging, and data-migration decisions.

The theme uses warm paper, charcoal, copper, and sage; serif headlines and clear everyday controls. It supports light, dark, and system appearance. Theme variables make later changes possible without rewriting generation logic.

## Operating boundaries

- Generation is local after assets/runtime setup. Model setup uses the Kokoro-ONNX GitHub release.
- No app analytics or paid speech service was added.
- Imported Markdown is sanitized, cannot execute scripts in the preview, and does not load its remote images.
- The embedded Microsoft WebView2 runtime has its own diagnostic behavior. Local speech does not imply that the host runtime has no independent network behavior.
- Working copies protect the original imported files.
- Deleting a library entry and deleting its audio are separate choices.
- Resource settings, narration speed, and playback speed remain separate concepts.
- GPU compatibility and speed are checked with real inference, not merely the presence of an adapter.

## Explicitly unfinished

WAV is the current export format. MP3, batch queues, highlighting, bookmarks, pronunciation overrides, drag-and-drop, tray behavior, a signed installer, and clean-machine distribution validation remain future work. No deadline or next feature was committed after the performance milestone.
''')

note('02 Features and UI', r'''
# Implemented features and UI

Related: [[01 Product and Decisions]] · [[03 Architecture and Data Flow]] · [[04 Performance and Benchmarks]]

## Reading workflow

1. Import a UTF-8 Markdown file, or create a reading and paste/edit its text.
2. Use **Read** for rendered Markdown, **Edit** for the working copy, and **Spoken** to inspect what the engine receives.
3. Select an English narrator, listen to a voice sample, and choose narration speed and pauses.
4. Create audio. Completed sections become available while the worker continues generating.
5. Listen, pause, seek within available audio, change playback speed or volume, and skip by ten seconds.
6. Stop generation at a section boundary when necessary. Available audio remains listenable; Continue preserves existing sections.
7. Export the combined WAV after the job completes, or reopen it from the recording library later.

## What is implemented

| Area | Behavior |
|---|---|
| Input | `.md` / `.markdown`, UTF-8 BOM handling, new readings, pasted text |
| Editing | Automatically saved local working copy; original file is not overwritten |
| Markdown | Headings, prose, lists, quotes, table text, link labels, and image alt text |
| Omissions | Front matter omitted; code blocks skipped by default with an explicit include-code toggle; script/style content omitted |
| Review | Formatted and spoken-text previews, word count, rough listening-duration estimate |
| Narrators | 28 American/British English voices, sample playback, 0.5–2× narration speed |
| Generation | Persistent worker, section progress, stop/continue, immutable snapshots, visible failures |
| Live listening | Automatic listening preference, adaptive buffer choices, seek within ready audio, underrun recovery |
| Playback | Play/pause, ten-second skips, volume, independent playback rate, saved positions |
| Library | Finished and partial readings; listen to partial audio and continue generation |
| Removal | Working-copy removal leaves original files/recordings; recording removal retains audio unless deletion is selected |
| Export | Native WAV save dialog, filename cleanup, overwrite confirmation |
| Settings | Local model readiness/setup/import, themes, storage path, performance presets, device/thread settings, speed test, warm-up, cache |
| Feedback | Active backend and threads, measured worker CPU usage, generation rate, first-audio time, ready duration, buffer ahead, reuse count |
| Shortcuts | Ctrl+O import, Ctrl+S save working copy, Space play/pause outside editing controls |

## Layout

- Left: identity, document shelf, recording library, and Settings.
- Center: document reading/editing/spoken preview.
- Right: narrator, voice art, narration pace, reading details, compact processing presets, generation action/progress.
- Bottom: persistent player across pages.

The voice controls scroll while the main generation action remains accessible. Normal and minimum-window layouts were checked, including a 1,024-pixel-wide viewport. The initial native window is 1,440 × 960 with a 1,024 × 720 minimum including window framing.

## Screenshots retained in this vault

These are real desktop verification screenshots using test-library content; they are not screenshots of the user's current library. Some historical images predate the final small fixes.

### Reading room

![[Evidence/2026-10-08/ui-studio.png]]

### Performance controls and measured results

![[Evidence/2026-10-08/ui-performance-final.png]]

### Listening during generation

![[Evidence/2026-10-08/ui-streaming-packaged.png]]

### Dark appearance

![[Evidence/2026-10-08/ui-performance-dark.png]]

### Smaller window

![[Evidence/2026-10-08/ui-small-window.png]]
''')

note('03 Architecture and Data Flow', r'''
# Architecture and data flow

Related: [[02 Features and UI]] · [[04 Performance and Benchmarks]] · [[05 Testing and Fixes]] · [[06 Development and Packaging]]

## End-to-end flow

```mermaid
flowchart LR
    A[Markdown working copy] --> B[Prepare spoken text]
    B --> C[Immutable job and sections]
    C --> D[Python speech worker]
    E[Reusable passage cache] <--> D
    D --> F[Published section WAVs]
    F --> G[Web Audio live player]
    F --> H[Incremental WAV assembly]
    H --> I[Completed recording and export]
    J[SQLite settings and library] <--> C
    J <--> G
```

The compiled frontend is served over a random loopback port inside the desktop window. That server supplies assets and audio; app operations use pywebview's Python bridge. The production app does not need Vite running.

## Source map

All paths below are relative to `C:\Users\fireball\OneDrive\Desktop\TTS`.

| File | Responsibility |
|---|---|
| `main.py` | Desktop lifecycle, assets, per-user WebView cache, startup preparation, shutdown, frozen-worker support |
| `backend/bridge.py` | UI commands, file dialogs, document/settings operations, library removal, final export |
| `backend/documents.py` | Markdown-to-spoken extraction, omissions, pauses, section preparation |
| `backend/models.py` | CPU/GPU asset names, readiness, English voice inventory, download/import |
| `backend/storage.py` | SQLite records/settings, working copies, per-user data location |
| `backend/jobs.py` | Job snapshots, worker ownership, event handling, cancellation/recovery, manifests, saved positions, benchmark coordination |
| `backend/speech.py` | Persistent inference session, generation, priority, cache/checkpoint reuse, atomic publication, incremental assembly |
| `backend/performance.py` | Settings validation, ONNX session configuration, hardware identity, recommendations, CPU usage |
| `backend/devices.py` | Windows DXGI adapter enumeration |
| `backend/runtime.py` | Locate optional validated NVIDIA runtime |
| `backend/cache.py` | Speech-section keys, audio validation, bounded LRU storage |
| `backend/sections.py` | Opening layout and sample-accurate published timeline |
| `backend/server.py` | Local static/media routes, range requests, host/path checks |
| `frontend/src/App.svelte` | Main pages, bridge state, document workflow, player integration |
| `frontend/src/PerformanceSettings.svelte` | Full performance/settings controls |
| `frontend/src/stream-player.ts` | Evolving Web Audio schedule and bounded prefetch |
| `frontend/src/api.ts` | Bridge contracts and types; frontend development preview |
| `frontend/src/tokens.css`, `styles.css` | Theme variables and layouts |
| `packaging/Folio.spec`, `build.ps1` | Frozen executable, resources, models, GPU add-on, shortcut |

## Job and worker logic

A job retains the Markdown, narration options, voice, speed, and original section layout. Editing a working copy does not mutate an existing recording. One speech job or benchmark owns inference at a time; generation may queue behind an in-progress warm-up.

The persistent spawned process owns Kokoro/ONNX inference. Queues carry commands/events; an event controls cancellation. Model loading is lazy for normal generation and the engine is reused until its configuration/files change. Only a cache miss needs inference.

Each completed raw section is **24 kHz, mono, PCM16 WAV**. It is written to a temporary file and atomically renamed before publication. Metadata contains index, cumulative start, duration, and pause. The final section has no trailing pause. Pause durations are quantized to sample boundaries.

Final assembly reads section files in blocks and writes their pauses to one WAV, rather than holding an entire long recording in a giant array. Export is restricted to completed jobs. The current size guard rejects output approaching the WAV capacity limit (approximately 4 GB), so exceptionally long work needs splitting.

## Player logic

Partial/live readings use Web Audio. A freshly selected completed reading uses its final WAV through HTML audio. When a live job finishes, its player continues on the same timeline rather than replacing the source and resetting playback.

Prefetch is bounded by a roughly 60-second horizon, with at most three loads in flight. Old decoded audio is evicted, ended source nodes are released, and disposed players abort pending fetches. Source scheduling uses the audio clock with pause/rate alignment. If the buffer runs out, the position freezes at the available boundary until enough new audio is decoded.

Pause, seek, or rate changes stop/rebuild scheduled sources from the preserved position. Manual play bypasses the larger automatic buffer target. A failed audio fetch stops repeated retries until the user requests another play.

## Persistence and recovery

Normal user data is `%LOCALAPPDATA%\Folio`, containing SQLite settings/library, job folders, reusable speech cache, models when not bundled, logs, and WebView cache. The project/portable directory is separate. `FOLIO_DATA_DIR` overrides data storage for development and tests.

Typical job files:

```text
jobs/<job-id>/section-000000.wav
jobs/<job-id>/section-000001.wav
jobs/<job-id>/recording.wav
section-cache/<speech-key>.wav
library.sqlite3
```

Positions for active/partial jobs are saved under the controller lock so they cannot overwrite generation progress. Resume scans contiguous valid checkpoints, keeps the original layout, and refuses incompatible model/text/voice settings. Already published duration/section counts never decrease while checkpoints are scanned.

Shutdown records an interrupted state before stopping the child. Listener guards prevent a late worker exit/event from replacing it with a failure. Older first-release jobs are checked with their original fingerprint, then adapted so they can continue more than once.

## Media routes and preview boundaries

- `/media/<32-hex-job-id>.wav`: completed recording only.
- `/media/<32-hex-job-id>/section-000000.wav`: published sections of known jobs only.
- Range and HEAD support allow seeking.
- Host validation and path confinement protect the local file-serving boundary.
- DOMPurify strips script-capable content/attributes from Markdown preview; arbitrary remote document resources are not loaded.
''')

packaged = json.loads((ROOT/'artifacts/packaged-performance.json').read_text(encoding='utf-8'))
integration = json.loads((ROOT/'artifacts/performance-integration.json').read_text(encoding='utf-8'))
streaming = json.loads((ROOT/'artifacts/streaming-ui.json').read_text(encoding='utf-8'))
rows = []
for result in packaged['benchmark']['results']:
    label = f"CPU ({result['threads']} threads)" if result['provider']=='CPUExecutionProvider' else 'NVIDIA CUDA (2 CPU threads)'
    rows.append(f"| {label} | {result.get('load_seconds',0):.2f} | {result.get('processing_seconds',0):.3f} | {result.get('audio_seconds',0):.3f} | {result.get('throughput',0):.2f}x |")
table = '\n'.join(rows)
note('04 Performance and Benchmarks', r'''
# Performance optimizations and benchmarks

Related: [[03 Architecture and Data Flow]] · [[05 Testing and Fixes]] · [[07 Roadmap and Next Session]]

## The problem and approach

The user wanted to listen to long text promptly rather than wait for the whole recording. We addressed both **time before listening** and **total generation throughput**. Streaming can improve the first experience even on a slower CPU; acceleration improves the amount generated while listening.

Processing performance is separate from narration pace and playback pace. A measured 10x throughput means ten seconds of audio produced per processing second, not a narrator speaking ten times faster.

## Implemented optimizations

| Optimization | What changed | Tradeoff |
|---|---|---|
| Early publication | Every completed section can be listened to before final assembly | Playback can catch up and need buffering |
| Short opening | First substantial passage split around 180 characters; later sections retain the roughly 420-character preparation limit | More opening boundaries, with preserved wording/order and intended pauses |
| Persistent engine | Reuse loaded inference session across requests | Model/session memory remains allocated |
| CPU presets | Quiet, Balanced, Fast, Custom affect real threads/priority/pacing | Higher thread counts are not necessarily faster |
| No busy spinning | ONNX thread spinning disabled; sequential execution | Selected for measured/controlled behavior rather than maximum idle CPU use |
| Real local speed test | Compare warmed CPU 1/2/4/8-thread candidates bounded by physical cores and available GPU | One-off compute/load cost; can cancel at a sample boundary |
| Validated NVIDIA backend | CUDA runtime and GPU-friendly FP16 model | Large optional runtime, compatible NVIDIA driver, cold loading cost |
| Optional startup preparation | Load voice session as Folio opens | Uses model RAM/GPU memory earlier; off by default |
| Cross-job cache | Reuse unchanged raw speech after repeats or small edits | Bounded extra local disk usage |
| Sample-accurate timeline | Share section/pause offsets between player and final WAV | Requires careful scheduling and publication state |
| Bounded audio memory | Prefetch/decode only a time window; release old buffers and ended nodes | Seeking back may decode a section again |
| Incremental final assembly | Read/write blocks from section files | Disk space and WAV size remain practical limits |

## Controls and defaults

| Setting | Code default / behavior |
|---|---|
| Processing preset | Balanced |
| Device | Auto; conservative CPU without a matching recommendation |
| CPU threads | 0 means Auto; explicit values within logical processors in Custom |
| GPU adapter | -1 means Auto |
| Quiet | One CPU thread, below-normal process priority, slight pacing on newly generated sections |
| Balanced CPU | Up to the measured efficient CPU count, bounded by approximately half physical cores |
| Fast CPU | Measured efficient count; defaults conservatively before a speed test |
| Balanced/Fast GPU | Matching measured GPU thread setting; otherwise up to two supporting CPU threads |
| Startup preparation | Off initially |
| Automatic listening | On |
| Listening buffer | Balanced |
| Reusable passage cache | On, 256 MB; choices 128/256/512 MB |

Settings apply to the next generation/continuation when they require a new session. The UI shows the active configuration separately from pending settings. CPU usage is worker feedback normalized to the machine's logical processors, not a guaranteed exact system-wide utilization target. No GPU-percentage cap was implemented.

Buffer choices use decoded audio ahead: Start sooner roughly 1 second; Balanced roughly 4 seconds when observed production comfortably beats playback, otherwise roughly 10; Fewer interruptions roughly 24. Manual play can start the available portion. Terminal short readings can play without waiting for an impossible buffer target.

The speed test separates loading from warmed inference and excludes passage-cache shortcuts. CPU results within 5% of the maximum prefer fewer threads. Recommendations include hardware/runtime/model identity; stale results do not steer Auto. A matching packaged recommendation was saved for this PC, so its normal Auto setting can select NVIDIA.

## Cache details

The speech key includes prepared section text, voice, narration speed, model and voice-file content hashes, Kokoro version, and runtime version. Theme and CPU-thread settings do not alter the spoken snapshot. Pauses are assembled separately from cached raw speech.

Job checkpoints are separate from the shared cache. They preserve an immutable reading across stop/restart; the cache accelerates different compatible jobs. LRU eviction bounds the shared cache, while clearing it leaves documents and recordings intact.

## Hardware and engine assets

- Intel i7-11800H: 8 physical cores / 16 logical processors.
- NVIDIA GeForce RTX 3060 Laptop GPU: approximately 6 GB VRAM (DXGI reported 5,994 MB).
- Intel UHD graphics also present; adapter enumeration order differs from some Windows hardware listings.
- CPU: `kokoro-v1.0.int8.onnx` (~92.4 MB).
- English voices: `voices-v1.0.bin` (~28.2 MB).
- GPU: `kokoro-v1.0.fp16-gpu.onnx` (~177.5 MB).
- Base ONNX Runtime 1.30.0; isolated optional GPU runtime 1.24.4 with CUDA 12 / cuDNN 9 dependencies.

The CPU INT8 and GPU FP16 models can produce small numerical differences; they retain the same faithful-reading workflow. Cache identities distinguish their assets.

## Retained packaged speed-test results

The following table is generated from the retained packaged benchmark report. Loading is separate from warmed speech time.

| Backend | Load seconds | Speech processing seconds | Audio seconds | Warm throughput |
|---|---:|---:|---:|---:|
''' + table + r'''

Source: [[Evidence/2026-10-08/packaged-performance.json]]. The two-thread CPU result was within the 5% efficiency tolerance in this particular run. Another CPU run chose four threads; Auto follows the retained matching measurement instead of assuming that the largest thread count is best.

## Real generation and cache evidence

- GPU integration: **89.33 seconds of audio in 8.09 seconds**, with the first section available at **2.41 seconds**. That earlier integration configuration used four supporting CPU threads; the final Balanced GPU policy uses two/matching measured threads.
- Independent CUDA probe: about **11.35x and 12.24x** on two passages; **6,840 actual profiled CUDA nodes** verified accelerator execution.
- Warm packaged reading: **68.31 seconds of audio in 8.03 seconds**, first section approximately **0.47 seconds** after request (engine already loaded).
- Packaged repeat: **12/12 cache hits**, final recording ready in approximately **0.31 seconds**.
- Integration repeat: **10/10 hits**, approximately **0.035 seconds** for that smaller test; editing one passage reused **9/10**, generating one new section.
- A 1,012-word desktop reading produced **350.25 seconds** of audio. An earlier observed run took roughly **26 seconds**; the retained UI rerun took **''' + f"{streaming['gpu']['processing_seconds']:.2f}" + r''' seconds**. Source-plan snapshots still cite the earlier result. Use the retained JSON when reproducing/comparing a specific run, and do not treat either timing as a fixed promise.

Evidence: [[Evidence/2026-10-08/performance-integration.json]], [[Evidence/2026-10-08/cuda-probe.json]], [[Evidence/2026-10-08/streaming-ui.json]]. Cache-hit throughput is reuse speed and must not be advertised as inference speed.

## GPU investigation and lessons

DirectML was tested in an isolated runtime on the NVIDIA and Intel adapters. Kokoro failed at `/encoder/F0.1/pool/ConvTranspose` with error `0x80070057`; the tested full-precision variant did not solve it. DirectML is not the shipped accelerator.

CUDA initially could not locate `cudnn_engines_tensor_ir64_9.dll` even though the file existed. Adding the NVIDIA package `bin` directories to the worker's PATH, then preloading DLLs, resolved the load chain. ONNX fallback is disabled for the selected session so a requested accelerator does not silently turn into CPU inference.

The optional runtime must have a validation marker and its ONNX package. The probe writes that marker only after valid audible output and actual CUDA-node verification. The spawned worker prepends the runtime directory as a **string** before inference imports; a Path object in `sys.path` was corrected during integration.

## Size and startup tradeoffs

Base CPU app: approximately **243 MB**. Optional GPU runtime: approximately **2.9 GB**, plus the **177 MB** model. Full portable folder: approximately **3.35 GB**. These are approximate decimal sizes for this build.

First packaged CUDA DLL/model loading measured **about 22 seconds**. Warmed first audio can be much faster, but streaming does not remove cold model/runtime initialization. Optional startup preparation moves loading earlier. CPU-only narration was explicitly tested with the GPU folder temporarily disabled, then the folder was restored.

Other-hardware throughput, driver compatibility, cold-start causes, and distribution size are still areas for further investigation.
''')

note('05 Testing and Fixes', r'''
# Testing, evidence, and fixes

Related: [[03 Architecture and Data Flow]] · [[04 Performance and Benchmarks]] · [[06 Development and Packaging]]

## What passed

The final Python suite contains **29 passing tests**. Svelte checks reported **0 errors and 0 warnings**; production frontend and PyInstaller builds succeeded. Separate real-inference, native-desktop, and controlled-clock scheduler checks supplement the unit suite.

| Area | Verification |
|---|---|
| Extraction | Ordered complete wording, long unpunctuated text, 4,000-word coverage, heading pauses, Markdown tables/alt text, code options, HTML/script/style handling |
| Original files | UTF-8 BOM import, working-copy persistence/removal, original preserved |
| Export/library | Complete WAV copy and extension, declined overwrite respected, optional audio deletion |
| Media boundary | Range seeking, unknown recording, host/path checks, only published sections exposed, incomplete final export unavailable |
| Tuning | Typed/bounded settings, performance preferences excluded from spoken snapshot |
| Cache | Speech-key invalidation, oldest-entry eviction, clearing does not delete recordings |
| Timeline | Exact samples, pause alignment, contiguous publication stops at missing sections |
| Recovery | Saved positions retain active progress; publication cannot decrease on resume; legacy jobs can continue repeatedly; shutdown cannot overwrite interrupted state |
| Real inference | CPU/CUDA synthesis, valid finite audible output, actual CUDA execution, cancellation/continue, cache hits and small-edit reuse |
| Live UI | Play during active generation, pause, seek, playback rate, buffering freeze/recovery, no reset at completion |
| Actual restart | Partial position restored, optional startup preparation, checkpoint files unchanged on continuation |
| Packaging | Real frozen worker on CPU and GPU; CPU succeeds with accelerator folder disabled |
| Visuals | Light/dark, document views, recording library, no horizontal overflow, minimum-window action remains accessible |
| Scheduler | Longer buffer works with many short sections; correct pause ordering, rate/seek offsets, ended audio sources released |

An initial packaged long-reading check used 673 words / 31 sections, producing roughly 138 seconds at 1.8x narration while checking cancel/continue. The performance milestone then exercised the larger live reading and actual process-restart cases.

## Corrected bugs worth remembering

| Problem | Correction / regression concern |
|---|---|
| Old completed jobs repeatedly hijacked selection during refresh | Track newly completed jobs rather than repeatedly selecting completed entries |
| Position updates changed library order | Sort recordings by creation time, rather than SQLite update time |
| Partial player briefly had zero available duration on reopen | Initialize its duration from saved available audio; wait for a real manifest before emitting player state |
| Saving active position risked stale progress overwrite | Save under the job-controller lock and update the active object |
| Resume briefly reduced section count/available audio while scanning old checkpoints | Preserve monotonic publication; reused checkpoints avoid Quiet pacing delays |
| Legacy first-release job only resumed once after migration | Validate original fingerprint, then normalize saved narration options |
| App shutdown could become failed instead of interrupted | Closing guards on listener/event handling and clear active state before child termination |
| Completed Web Audio nodes retained decoded buffers | Remove/disconnect ended source nodes and prune old decoded audio |
| Fixed small section-count prefetch prevented a longer buffer filling | Bound prefetch by time instead of 16 section objects |
| Missing audio could trigger endless fetch retries | Hold playback and suppress retry until a new play request |
| Selected GPU could silently fall back | Check initialized provider and disable ONNX session fallback |
| GPU worker initially used base runtime | Insert runtime path as string before worker inference imports |
| cuDNN delayed sublibrary load failed | Include NVIDIA package bin paths for inference-time loads |

Native test harness startup also needed to wait for the WebView/debug endpoint. Reloading while the Python bridge was being injected could leave that test page waiting; a stable reloaded session then passed. This was observed during automation, not established as a normal user-startup failure.

## Evidence files retained

| File | Meaning |
|---|---|
| [[Evidence/2026-10-08/cuda-probe.json]] | Actual CUDA profile and two passage measurements |
| [[Evidence/2026-10-08/performance-integration.json]] | Generation, exact PCM assembly, cache/edit reuse, Quiet CPU, speed test |
| [[Evidence/2026-10-08/streaming-ui.json]] | Native early listening, control behavior, buffering, partial positions |
| [[Evidence/2026-10-08/packaged-performance.json]] | Frozen CPU/GPU, speed test, warm-up, cache reuse, saved position |
| [[Evidence/2026-10-08/restart-flow.json]] | Actual process restart and unchanged checkpoint continuation |
| [[Evidence/2026-10-08/cpu-only.json]] | Base portable app without GPU runtime |

Reports were produced at different points in the milestone; not every earlier report was regenerated after each final small patch. The final shutdown regression passed in the 29-test suite and the subsequently repeated packaged restart flow. The benchmark note distinguishes historical and retained rerun timings.

## Practical limits of this evidence

Validation is on this Windows PC. A signed installer, clean-machine setup, a broader hardware/driver matrix, and other-platform packaging have not been verified. Avoid claiming identical startup, uninterrupted listening, or fixed generation speed from these local results.
''')

note('06 Development and Packaging', r'''
# Development and packaging

Related: [[03 Architecture and Data Flow]] · [[04 Performance and Benchmarks]] · [[05 Testing and Fixes]]

## Paths and running the portable application

```text
Source: C:\Users\fireball\OneDrive\Desktop\TTS
App:    C:\Users\fireball\OneDrive\Desktop\TTS\dist\Folio\Folio.exe
Link:   C:\Users\fireball\OneDrive\Desktop\TTS\Folio.lnk
Data:   %LOCALAPPDATA%\Folio
```

The portable folder needs `_internal` and `models` beside the executable. NVIDIA acceleration additionally uses `gpu-runtime`. A separate Python installation, Node installation, terminal, or browser tab is not required to use it. WebView2 is required on Windows.

The shortcut and final app were rebuilt. After verification the optional GPU folder was restored, the app reopened without developer debugging, and its existing three library recordings remained present. A matching benchmark recommendation from this PC was saved for Auto selection.

## Dependency versions at the handoff

Python 3.12.14; pywebview 6.2.1; Kokoro-ONNX 0.6.1; base ONNX Runtime 1.30.0; NumPy 2.5.3; SoundFile 0.13.1; markdown-it-py 4.2.0; phonemizer 3.4.0; espeakng-loader 0.2.4; psutil 7.2.2; PyInstaller 6.22.3.

Frontend lock: Svelte 5.57.2; Vite 7.3.7; TypeScript 5.9.3; DOMPurify 3.4.16; marked 15.0.12. `frontend/package.json` still has package version 0.1.0; the performance milestone did not constitute a formal numbered release.

Optional runtime: ONNX Runtime GPU 1.24.4, CUDA 12 wheels, cuDNN 9.27.0.42. Exact versions/dependency lists are in the copied locks, not a requirement to upgrade during the next session.

## Source setup

From the source directory in PowerShell, use Python 3.12 and a Vite-compatible Node version:

```powershell
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
Push-Location frontend
npm.cmd ci
npm.cmd run build
Pop-Location
$env:FOLIO_DATA_DIR = Join-Path (Get-Location) '.app-data'
& .\.venv\Scripts\python.exe main.py
```

Model setup is visible in Settings, or use `tools/setup_models.py`. The current workspace already has models in `.app-data/models`. Imported originals and normal user data should not be repurposed as disposable test fixtures.

## Base build and checks

Close the running portable app before replacing its output folder.

```powershell
& .\build.ps1
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v
& .\.venv\Scripts\python.exe tools\smoke_test.py
node tools\stream-player-check.cjs
```

The build checks and compiles Svelte, freezes Python using `packaging/Folio.spec`, copies available CPU/voice model files, and creates the shortcut. A GPU build needs `-IncludeGpu`.

The development sandbox needed TEMP/TMP pointing to a workspace `.tmp` folder for Python temporary test data, and explicit permission for loopback/GUI/process operations. These were execution-environment constraints, not product runtime requirements.

## Reproduce the isolated GPU add-on

```powershell
& .\.venv\Scripts\python.exe -m pip install --target .cuda-probe -r requirements-gpu.lock.txt
& .\.venv\Scripts\python.exe tools\download_gpu_model.py
& .\.venv\Scripts\python.exe tools\probe_cuda.py
& .\build.ps1 -IncludeGpu
```

Keep base CPU dependencies separate from the GPU target. The probe must succeed before it writes `.cuda-probe/folio-runtime.json`; packaging requires that marker. The build copies ONNX, NVIDIA runtime components/metadata, and the GPU model into the portable folder.

GPU runtime lookup: `FOLIO_GPU_RUNTIME` if supplied; otherwise `gpu-runtime` beside a frozen executable, or `.cuda-probe` in source development. A marker and ONNX package must exist. Do not infer successful acceleration merely from installed files; rerun actual synthesis/benchmark when changing hardware, model, or runtime.

The DirectML experiment lives in `.gpu-probe`; it is not the validated shipping path. `tools/probe_performance.py` and `tools/probe_cuda.py` preserve the investigation tools.

## Verification tools

| Tool | Scope |
|---|---|
| `tools/smoke_test.py` | Actual synthesis, stop, resume, preserved first section |
| `tools/performance_integration.py` | CUDA/CPU, timeline equality, cache/edit reuse, benchmark |
| `tools/ui-check.cjs` | Actual desktop bridge, reading views, themes, visuals |
| `tools/desktop-flow.cjs` | Completed playback, seeking, position |
| `tools/long-reading.cjs` | Longer packaged reading and recovery |
| `tools/library-flow.cjs` | Working copies, removal, previews, library controls |
| `tools/window-check.cjs` | Minimum-window layout |
| `tools/streaming-ui.cjs` | Live player, controls, buffering, partial continuation |
| `tools/packaged-performance.cjs` | Frozen speed test, devices/threads, warm-up, reuse |
| `tools/restart-flow.cjs` | Prepare then verify across real process restart |
| `tools/cpu-only.cjs` | Actual base-app synthesis with GPU add-on disabled |
| `tools/stream-player-check.cjs` | Controlled audio-clock scheduler/memory cases |

Native checks attach Playwright to the app's own WebView2 when explicitly launched with debugging:

```powershell
$env:FOLIO_DATA_DIR = Join-Path (Get-Location) 'artifacts\some-test-data'
$env:WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS = '--remote-debugging-port=9223'
& .\dist\Folio\Folio.exe
```

Set `FOLIO_PLAYWRIGHT` to a usable Playwright module location. These are developer checks; normal launches do not need or enable the debugging port. Helpers use specific test folders/content and may need adaptation before repeating them in a different environment.

## Documentation snapshots

[[Reference/2026-10-08/README]] · [[Reference/2026-10-08/APP_PLAN]] · [[Reference/2026-10-08/PERFORMANCE_PLAN]]

Exact dependency files are copied under `Reference/2026-10-08/`: `requirements.txt`, `requirements.lock.txt`, `requirements-gpu.lock.txt`, `frontend-package.json`, and `frontend-package-lock.json`.
''')

note('07 Roadmap and Next Session', r'''
# Roadmap and next session

Related: [[00 Start Here]] · [[01 Product and Decisions]] · [[04 Performance and Benchmarks]] · [[05 Testing and Fixes]]

## Completed baseline to build on

Local English Markdown narration, polished desktop UI, real voices, background jobs, a library, WAV export, live listening, device/thread controls, local benchmarks, optional NVIDIA acceleration, bounded passage reuse, and restart recovery are implemented.

The next level does not require rebuilding this baseline. Choose a focused milestone and retain its existing verification/recovery guarantees.

## Remaining work already identified

- [ ] MP3 export and packaged encoder choice.
- [ ] Windows installer, release signing, and clean-machine installation checks.
- [ ] Broader CPU/GPU/driver compatibility and resource/startup measurements.
- [ ] Multiple-file queue.
- [ ] Read-along highlighting.
- [ ] Bookmarks and richer listening navigation.
- [ ] Pronunciation overrides.
- [ ] Drag-and-drop import.
- [ ] Saved narrator/reading presets.
- [ ] Optional tray/background behavior.
- [ ] Decide whether Folio remains the product name or becomes LiltTTS, with deliberate data migration if needed.
- [ ] Refine theme and default narrator based on actual everyday use.

These are pending possibilities, not approved implementation tasks or promised release dates.

## Suggested milestone choices

| Direction | Why it matters | Useful completion criteria |
|---|---|---|
| Daily-use listening | Improve navigation and export before expanding engines | Chapters/bookmarks, useful keyboard controls, MP3 plays elsewhere, persistence remains correct |
| Easier distribution | Make the application practical to move/install | CPU-first installer, separate optional GPU component, first-run readiness, test without developer Python/Node |
| Faster cold start / smaller GPU install | Address the largest current performance/size tradeoff | Measure DLL/session/phonemizer loading separately, evaluate changes with cold and warm tests, compare size and speech quality |
| Batch reading | Turn a collection of Markdown into an orderly listening queue | Clear queue state, per-document progress, stop/resume/restart behavior, bounded resources |
| Product identity and polish | Consolidate the name and everyday feel | Consistent branding/shortcut/title, existing library migrates safely, light/dark/minimum-window behavior preserved |

Future engine/model evaluation is an option if startup, size, or voice quality warrants it. Compare time to first audio, warmed throughput, quality, memory, disk size, and packaging before committing to a change. Hardware recommendations should come from measured inference on the relevant machine.

## Open questions for a future discussion

- Is the next priority listening features, lighter distribution, or startup performance?
- Keep Folio or adopt LiltTTS as the app name?
- Which voices and narration defaults feel best during long real readings?
- How much GPU-install size is acceptable for the speed improvement?
- Should CPU and GPU packages be separately downloadable?
- Is MP3 export the first convenience feature, or are chapter/bookmark controls more valuable?

## Guardrails to carry forward

- Keep faithful wording, selected voice, and narration pace intact.
- Keep performance settings separate from narration/playback speed.
- Preserve original files, immutable job snapshots, and existing recordings.
- Maintain partial playback and checkpoint recovery after cancellation or restart.
- Keep published audio monotonic; do not reset playback at generation completion.
- Bound audio memory and shared cache; clearing cache must not delete recordings.
- Distinguish cold loading, warmed inference, cached repeats, and whole-job time in performance claims.
- Keep CPU operation independent of the optional GPU component.
- Preserve the polished light/dark UI and accessible primary action at small window sizes.

## Pasteable restart context

> Continue the local Windows Markdown-to-speech project in `C:\Users\fireball\OneDrive\Desktop\TTS`. The implemented app is still named Folio; this Obsidian vault is LiltTTS. Read `00 Start Here`, architecture, performance, and testing notes first. The stack is pywebview/Svelte/Python/Kokoro-ONNX. The portable build includes a separately located validated NVIDIA runtime and GPU model, while CPU-only operation passes. Streaming, presets/threads, benchmark-driven Auto, warm-up, cache, and restart continuation are implemented. There are 29 Python tests plus native and scheduler checks. Do not reimplement completed work. Review the proposed next milestone with the user before changing scope. Benchmark claims must distinguish cold loading, warmed inference, and cache reuse; preserve original files, saved audio, and partial recovery.
''')

note('08 Work Log 2026-10-08', r'''
# Work log — 8 October 2026

Related: [[00 Start Here]] · [[05 Testing and Fixes]] · [[07 Roadmap and Next Session]]

## 1. Scope and stack planning

The user wanted a local app for reading long or short text, without paid APIs, with a proper desktop window and an attractive customizable UI. Input was narrowed to English Markdown and pasted text, and behavior to faithful reading. Desktop options were discussed; pywebview, Svelte, Python, and Kokoro-ONNX became the settled stack.

## 2. First usable application

Implemented the Folio reading room, working-copy editor, formatted/spoken views, local English narrators, speed/pauses, background generation, section checkpoints, cancellation/continuation, recording shelf, completed-audio player, WAV export, model setup, and themes. Packaged a Windows executable and shortcut. Initial Python suite had 18 tests; real packaged reading/playback and longer cancellation/continuation checks passed.

## 3. Performance milestone accepted

The user wanted to listen promptly without waiting for an entire long document, endorsed early listening, and asked about resource controls and further speed improvements. We recorded the milestone, created `PERFORMANCE_PLAN.md`, then implemented it rather than stopping at a proposal.

## 4. Foundations and hardware investigation

Added real thread/session settings, presets, hardware/device discovery, process usage feedback, benchmark commands, optional startup preparation, short opening passages, timeline metadata, and bounded raw-speech reuse. CPU measurements showed that increasing threads indefinitely did not improve throughput.

DirectML was evaluated and failed Kokoro convolution-transpose inference. Isolated CUDA dependencies and the FP16 GPU model were tested next. Resolving inference-time cuDNN DLL lookup enabled successful synthesis, and actual CUDA-node profiling confirmed execution. The validated optional runtime was integrated into spawned/frozen workers.

## 5. Live playback and recovery

Added section media routes and the Web Audio streaming player with pause/seek/rate/volume, adaptive buffers, underrun recovery, and bounded audio memory. Kept its timeline when generation completes; retained final-WAV playback for fresh completed selections. Made partial recordings listenable after reopening.

Desktop and process-restart checks exposed ordering, initial-duration, publication, and shutdown races. Corrected them and added regression checks. Fixed repeated legacy continuation, ended-source memory retention, too-small fixed-section prefetch, and uncontrolled failed-media retries.

## 6. Final delivery verification

The final suite reached 29 Python tests. Frontend checks/build, real CPU/CUDA synthesis, exact streamed/exported PCM alignment, cache/edit reuse, native controls, themes, minimum window, and full process-restart recovery passed. GPU-disabled CPU synthesis also passed. Rebuilt the executable/shortcut, restored the GPU add-on, saved this PC's matching recommendation, and reopened the normal app with its existing library and debugging disabled.

## 7. Vault handoff

At the user's request, documented product decisions, features, architecture, performance, testing, build/reproduction steps, pending ideas, and this work log in the LiltTTS vault. Retained selected screenshots, raw evidence reports, and source-document/dependency snapshots. Existing vault welcome/settings are preserved. No further application implementation was undertaken for this documentation request.

## Handoff state

The application/performance milestone is implemented. The next milestone is undecided. This vault provides the starting context for discussing and implementing the next level later; it does not rename the application or commit to new features.
''')

evidence = STAGE / 'Evidence' / DATE
reference = STAGE / 'Reference' / DATE
evidence.mkdir(parents=True, exist_ok=True)
reference.mkdir(parents=True, exist_ok=True)
for name in ['cuda-probe.json','performance-integration.json','streaming-ui.json','packaged-performance.json','restart-flow.json','cpu-only.json',
             'ui-studio.png','ui-performance-final.png','ui-streaming-packaged.png','ui-performance-dark.png','ui-small-window.png','ui-library.png']:
    shutil.copy2(ROOT/'artifacts'/name, evidence/name)
for name in ['README.md','APP_PLAN.md','PERFORMANCE_PLAN.md','requirements.txt','requirements.lock.txt','requirements-gpu.lock.txt']:
    shutil.copy2(ROOT/name, reference/name)
for source, target in [('package.json','frontend-package.json'),('package-lock.json','frontend-package-lock.json')]:
    shutil.copy2(ROOT/'frontend'/source, reference/target)
print(json.dumps({'staging':str(STAGE),'notes':len(list(STAGE.glob('*.md'))),'evidence':len(list(evidence.iterdir())),'reference':len(list(reference.iterdir()))}))
