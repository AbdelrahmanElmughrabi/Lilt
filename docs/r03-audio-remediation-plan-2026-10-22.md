# R-03 stored-audio remediation plan

22 October 2026. The publisher authorized proceeding with R-03 fixes after investigation/review. Preserve prior evidence and unrelated work; no commits, personal libraries, destructive operations or package/publication actions. Reviewed input content is now separately preserved under `.tmp/r03-remediation-20261022/input-snapshot/` (386 inputs), with the old manifest copied alongside. Old hash manifests are unchanged and cease to describe current modified inputs once fixes begin.

## Current trace and selected boundary

`cache.audio_info`, published sections/resume and cache fetch currently invoke native libsndfile autodetection on stored files. Final assembly reopens those files natively. The media server and export copy stored bytes without validating their actual container. Existing tests use both genuine WAVs and artificial byte strings; transport fixtures will become genuine PCM WAVs while preserving their original HTTP/atomic-copy assertions.

Implement a small bounded Python PCM reader shared by those consumers. Accept explicit little-endian RIFF/WAVE, mono 24-kHz 16-bit integer PCM (including well-formed PCM extensible headers where compatible). Validate all chunk extents/padding, format consistency, a single nonempty data chunk and exact declared/file lengths. Bound metadata size/chunk count; seek over audio rather than allocate it. Reject renamed AIFF/MAT4, compression, truncated or inconsistent structures before native decoding. Check actual generated/legacy fixtures.

Expose a canonical 44-byte PCM WAV view plus raw sample bytes from the same validated open handle. Browser delivery/export therefore receive no untrusted metadata/codec container. Preserve original files; canonicalization removes incidental metadata from delivery/export, not from stored originals. Serve Range/HEAD against this view's size, with bounded reads. Do not rely on validate-then-reopen of the source path. Truncation/change during copying must fail without replacing an existing destination.

`audio_info` becomes pure Python. Cache copy stages accepted PCM through the coherent reader and validates before publishing, with cleanup limited to owned temporary files. Final recording assembly reads raw PCM blocks using the Python reader/standard WAV writer; no stored section goes through native autodetection. Retain unsupported existing sections and complete recordings under unique names before replacing them during regeneration. Existing engine-to-PCM output writing can remain; native-library rights/patch coverage still require completion. Timeline/pauses must remain sample-exact and memory use bounded.

## Acceptance and execution

1. Save a disposable pre-fix reproduction of renamed AIFF admission/cache reuse before production edits.
2. Add focused parsing, native-call exclusion, preserved-output, coherent-handle, changed/truncated-file, metadata/chunk bounds, HTTP canonical Range/HEAD and export regressions. Guard tests need not fail pre-fix; baseline reproductions must be distinguished from new-module tests.
3. Update consumers and real-audio test fixtures. Retain existing generation/cancellation/cache/resume/error behavior; unsupported files are unavailable for reuse/delivery, with originals retained. Reject unsupported export with a useful error.
4. Run focused/full appropriate backend tests, existing browser cases, relevant source-native/media and actual CPU/CUDA generation with existing public fixtures. Preserve outputs in new folders. No final/installed package or other-machine clearance.
5. Record a new results/hash snapshot and independent-review prompt, including R-01/R-02 source overlaps. The independent review's parent-cache/deletion/CDP findings remain separate unless explicitly addressed by another revision.

Runtime and sanitizer fixes require isolated evaluation and coordinated input changes; this audio plan does not pretend they are already resolved. Select runtime patches with provenance, cp312/GPU compatibility and explicit Expat 2.9.0 CVE dispositions. Final native coverage remains a final-package gate.
