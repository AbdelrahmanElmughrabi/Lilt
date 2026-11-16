# Validation status

Violilt is in beta. These results describe local checks on Windows; they are not a guarantee for every device or input.

## Verified locally

- On 17 November 2026, the Python suite ran 396 tests with one skipped using Python 3.12.15. It includes checks for document preparation, all 39 listed symbol aliases in US and GB English, caching, persistence, and recovery. See the [symbol tests](../tests/test_pronunciation.py) and [recovery tests](../tests/test_recording_removal_retry.py).
- On 17 November 2026, all 18 cases in the [editor browser suite](../tests/test_editor_save.cjs) passed against a built frontend and a simulated desktop API. These are browser-fixture checks, not native application or speech tests.
- A source launch opened the desktop window. The launch check did not assess playback.
- The [performance integration tool](../tools/performance_integration.py) generated audio on an NVIDIA GeForce RTX 3060 Laptop GPU and checked streamed sections against the exported recording. Its timing and cache observations apply to the recorded runs, not every machine or document.
- Independent reviews found that a retry could recreate a deleted recording and that stored audio could be accepted without the expected WAV-format checks. Reproduction and source fixes followed; the deletion check used a real listener and SQLite across four failed/cancelled and keep/delete-audio combinations. See the [retry tests](../tests/test_recording_removal_retry.py) and [audio tests](../tests/test_pcm_audio.py).

### Four-thread comparison

On 17 November 2026, an isolated copy of the integration tool was set to use four supporting CPU threads and extended to run the same reading again in the same worker. Both generated 86.92 seconds of audio, with streamed samples matching the exported recording. The warm run regenerated all 10 sections with cache reuse disabled.

| Reading | Worker processing | First audio after request |
| --- | ---: | ---: |
| First, new worker | 10.94 s | 12.92 s |
| Warm, same worker | 7.71 s | 0.31 s |

In separate cache checks in that integration run, an unchanged repeat reused 10/10 sections and a small edit reused 9/10.

### Earlier performance records

- An earlier RTX 3060 Laptop GPU integration run generated 89.33 seconds of audio in 8.09 seconds of worker processing, with first audio at 2.41 seconds. Its saved result does not establish whether the worker was warm.
- For a separate 1,012-word reading, an earlier note reported about 26 seconds; a retained UI rerun recorded 43.85 seconds for 350.25 seconds of audio. The records do not resolve the discrepancy.
- A packaged CUDA load was measured at about 22 seconds in a separate cold-start test.

The detailed historical performance reports are not tracked in this repository.

## Not established

- Automated tests do not establish listening quality or correct pronunciation of every word and voice. Reports do not automatically retrain the model.
- Final packaged-app installation, updates, and Store behavior have not been established.
- Behavior and performance across other hardware and operating systems have not been established by these checks.
- Setup can download voice assets, and WebView2 has its own network behavior; a fully offline or zero-traffic claim is not established.
