# Folio performance upgrade — implementation plan

Implement the approved performance milestone without changing the local, faithful-reading workflow.

## Outcome

Users can listen to completed passages while the rest of a document generates, choose how much CPU work the speech process performs, compare real speed on their PC, and reuse audio after small edits. Voice/narration speed, playback speed, and processing performance remain independent.

This PC has an Intel i7-11800H (8 physical / 16 logical processors), Intel UHD graphics, and an NVIDIA RTX 3060 Laptop GPU. The current build runs CPU inference with four threads. GPU availability will be determined with an actual runtime/model inference check, not merely the presence of a GPU.

## Build sequence

1. **Performance foundation.** Add persisted Quiet, Balanced, Fast, and Custom presets; an advanced CPU thread count; startup warm-up; cache preferences; and Auto/CPU/validated-GPU device selection. Apply inference settings at the next generation or continuation. Add a dedicated local benchmark command with progress/cancellation and recommendations. Report worker CPU usage, active backend/threads, time to first audio, and generated audio seconds per processing second. Normal or below-normal priority keeps controls responsive; no exact CPU-percentage promise.
2. **Section metadata and cache.** Publish each atomically completed section with duration, pause, and cumulative timeline offsets. Keep checkpoint reuse within a job, then add a bounded cache keyed by section text, voice, narration speed, and engine/model identity. Reuse raw audio across jobs and assemble pauses separately. Preserve old job snapshots on continuation. A short opening section reduces the initial wait; later sections retain tested model limits.
3. **Local streaming routes.** Serve only published section WAVs from known jobs. Keep final WAV export restricted to complete jobs. Provide a manifest through the existing bridge and retain range support on section/final audio. Save listening position for partial jobs under the controller lock so playback updates cannot overwrite generation progress.
4. **Streaming player.** Use a Web Audio player for an evolving section timeline, prefetch/decode a bounded amount of audio, and schedule sections with their intended pauses. Support play/pause, seeking within available audio, volume, playback speed, buffering, cancellation, and continuation. Keep streaming at completion so there is no playback reset or duplicate passage; use the final WAV on a fresh selection/restart. Persist positions and make partial recordings listenable after restart.
5. **Everyday UI.** Add a Performance card in Settings, a compact preset selector during generation, Start sooner/Balanced/Fewer interruptions buffering preferences, and optional automatic listening. Show measured generation rate, CPU utilization, and audio ahead. Display the actual backend and state when a setting waits for the next job. Match Folio's existing light/dark styling and minimum window size.
6. **Hardware tuning.** Compare representative warm CPU inference at several thread counts. Evaluate DirectML and GPU-friendly Kokoro assets on the actual adapters in an isolated dependency probe. Enable acceleration only if synthesis succeeds and timings are useful; retain CPU fallback. Include optional GPU assets in the packaged folder if validated. Store model/runtime/hardware identities with benchmark results so stale results do not drive Auto mode.
7. **Validation and delivery.** Test coverage, exact streamed/final sample timeline agreement, early playback while generation is active, buffering/recovery, seek/pause/rate changes, partial-job position across restart, cached audio reuse/invalidation/eviction, settings validation, resource reporting, benchmark cancellation, and legacy recordings. Run real CPU/GPU synthesis, Svelte checks, desktop visual checks, and packaged worker tests. Rebuild the executable/shortcut and update the README with measured results and limitations.

## Defaults and tradeoffs

- Balanced is the default resource preset. Auto uses a matching speed-test recommendation when available, with conservative CPU settings otherwise.
- Quiet uses fewer threads and below-normal process priority. Fast uses a measured efficient configuration; Custom exposes a thread count. Thread count is a real control, while utilization is measured feedback.
- Streaming and automatic listening are enabled by default. Start sooner uses a small initial buffer; Balanced adapts to observed throughput; Fewer interruptions waits for more audio. Manual play can start any available portion. Generation slower than consumption can still require buffering.
- Startup warm-up is optional and off initially because it allocates model RAM before the first request. Once loaded, reuse the inference session.
- Cross-job section caching is on with a bounded 256 MB cache. Clearing it does not remove saved recordings or working copies.
- Never silently select a backend that cannot run the chosen model. Display fallback/error details and retain CPU generation.
- Existing completed recordings remain playable/exportable. Legacy interrupted jobs retain their original section layout and are checked against the original snapshot before continuation.

## Completion evidence

Record measured first-audio latency, generation throughput, actual thread/backend settings, cache hits, and streamed/final duration agreement in local verification artifacts. Document what was tested on this PC and what still needs other-hardware validation. GPU acceleration is conditional on the probe; all CPU streaming and resource-control functionality must work independently.

Implemented on 2026-10-08. Twenty-nine focused Python tests and Svelte checks pass. Evidence:

- `artifacts/cuda-probe.json`: actual CUDA execution (6,840 profiled CUDA nodes), finite audible output, two representative passages at 11.4–12.2× real time.
- `artifacts/performance-integration.json`: 89.3 seconds generated in 8.1 seconds; first audio at 2.4 seconds; exact streamed/exported PCM samples and pause alignment; repeat cache hits 10/10; a one-passage edit reuses 9/10 sections; Quiet uses one CPU thread and below-normal priority; benchmark cancellation and Auto selection pass.
- `artifacts/streaming-ui.json`: native early playback during generation, pause/seek/rate, no reset at completion, buffering freeze/recovery, partial listening position after reload, and checkpoint continuation pass. A real 1,012-word reading produces 350 seconds of audio in about 26 seconds.
- `artifacts/packaged-performance.json`: the portable executable runs actual CUDA at ~10.1× in its speed test, CPU at an explicit two threads, engine warm-up, early playback, position recovery, and full passage reuse. Cold first CUDA loading measured ~22 seconds; warmed first section ~0.5 seconds.
- `artifacts/restart-flow.json`: an actual packaged process restart restores partial position, runs optional startup preparation, resumes without reducing available audio, and leaves checkpoint files unchanged.
- `artifacts/cpu-only.json`: actual CPU synthesis succeeds with the GPU folder disabled.
- `tools/stream-player-check.cjs`: many short sections can satisfy the longer buffer preference; source nodes release completed audio; scheduled pauses and seek/playback-rate offsets remain aligned.
- Native light/dark and 1,024-pixel window checks pass. The primary action stays visible above the player.

DirectML failed Kokoro inference on the NVIDIA and Intel adapters. The shipped accelerator is the validated optional NVIDIA CUDA add-on. Its runtime adds ~2.9 GB plus a ~177 MB GPU model; the CPU app remains ~243 MB and works independently. Timing and compatibility on other hardware, a signed installer, and clean-machine release validation remain distribution work.
