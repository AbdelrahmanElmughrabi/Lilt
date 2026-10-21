# Approved model integrity

The application pins the byte lengths and SHA-256 values in
[model_trust.py](../backend/model_trust.py). On 21 October 2026 all three assets
were independently fetched over HTTPS from the upstream
[model-files-v1.0 release](https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0)
and hashed without loading them. The release API supplies no asset digest, so
runtime downloads cannot use that optional field as their trust anchor.

| Asset | Bytes | SHA-256 |
| --- | --- | --- |
| kokoro-v1.0.int8.onnx | 92361271 | 6e742170d309016e5891a994e1ce1559c702a2ccd0075e67ef7157974f6406cb |
| kokoro-v1.0.fp16-gpu.onnx | 177464787 | c1610a859f3bdea01107e73e50100685af38fff88f5cd8e5c56df109ec880204 |
| voices-v1.0.bin | 28214398 | bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d |

The audit download records are retained under
`.tmp/release-hardening-20261021/verified-upstream-models.json`. Reverify a new
release against authoritative upstream provenance before deliberately changing
these pins. If upstream replaces an asset, the current app fails closed.

These values establish expected bytes. They do not settle model/voice licensing
or prove that an inference implementation has no defects; redistribution review
remains open in `PRONUNCIATION-CANDIDATE.md`.
