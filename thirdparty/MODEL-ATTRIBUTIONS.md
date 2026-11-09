# Model and pronunciation data notices

## Kokoro model and distributed voice container

Kokoro-82M is provided by hexgrad under Apache License 2.0. Retain the complete
license at `native/Apache-2.0.txt`. Upstream source/model information:
https://huggingface.co/hexgrad/Kokoro-82M . The upstream model card identifies
source weights with SHA-256
`496dba118d1a58f5f3db2efc88dbdc216e0483fc89fe6e47ee1f2c53f18ad1e4`.

The distributed ONNX/voice assets are supplied by the official kokoro-onnx
`model-files-v1.0` release:
https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0 .
The selected local identities are:

| Payload path relative to the app folder | Bytes | SHA-256 |
| --- | ---: | --- |
| `models/kokoro-v1.0.int8.onnx` | 92361271 | `6e742170d309016e5891a994e1ce1559c702a2ccd0075e67ef7157974f6406cb` |
| `models/kokoro-v1.0.fp16-gpu.onnx` | 177464787 | `c1610a859f3bdea01107e73e50100685af38fff88f5cd8e5c56df109ec880204` |
| `models/voices-v1.0.bin` | 28214398 | `bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d` |

**Conversion/modification notice:** the ONNX assets are converted/optimized
representations of upstream Kokoro weights. The release describes optimized
int8/f16 assets and references taylorchu/kokoro-onnx v0.2.0:
https://github.com/taylorchu/kokoro-onnx/tree/v0.2.0 . The selected fp16 GPU
variation is distributed under its own release filename above. The release's
conversion description is not a claim that Violilt independently reproduced
every transformation. No further weight/vector editing by Violilt is performed
in the reviewed distribution path. The conversion project's MIT grant does not
replace the underlying model's Apache terms.

The complete `voices-v1.0.bin` has 54 named vector members. This notice covers
the whole container, including voices not enabled by the English UI:

`af_alloy`, `af_aoede`, `af_bella`, `af_heart`, `af_jessica`, `af_kore`, `af_nicole`, `af_nova`, `af_river`, `af_sarah`, `af_sky`, `am_adam`, `am_echo`, `am_eric`, `am_fenrir`, `am_liam`, `am_michael`, `am_onyx`, `am_puck`, `am_santa`, `bf_alice`, `bf_emma`, `bf_isabella`, `bf_lily`, `bm_daniel`, `bm_fable`, `bm_george`, `bm_lewis`, `ef_dora`, `em_alex`, `em_santa`, `ff_siwis`, `hf_alpha`, `hf_beta`, `hm_omega`, `hm_psi`, `if_sara`, `im_nicola`, `jf_alpha`, `jf_gongitsune`, `jf_nezumi`, `jf_tebukuro`, `jm_kumo`, `pf_dora`, `pm_alex`, `pm_santa`, `zf_xiaobei`, `zf_xiaoni`, `zf_xiaoxiao`, `zf_xiaoyi`, `zm_yunjian`, `zm_yunxi`, `zm_yunxia`, `zm_yunyang`.

Upstream training acknowledgements, retained as reported by the model author:

- Koniwa `tnc`, CC BY 3.0: https://github.com/koniwa/koniwa ;
  https://creativecommons.org/licenses/by/3.0/ .
- SIWIS, CC BY 4.0: https://datashare.ed.ac.uk/handle/10283/2353 ;
  https://datashare.ed.ac.uk/bitstream/handle/10283/2353/license_text .
- StyleTTS 2 architecture: Li et al / yl4579,
  https://github.com/yl4579/StyleTTS2 ; upstream model training credit: `rzvzn`.
- Upstream acknowledges Pendrokar, synthetic-data contributors and compute sponsors.

These report upstream acknowledgements; they do not assert that a training-data
license automatically determines the license of model weights or generated audio,
or certify creator consent, exclusivity or rights in a user's input/output.

## English pronunciation dictionaries

Misaki 0.9.4 and the four selected English dictionaries are supplied under the
Apache-2.0 repository/package grant. The selected file blobs match this immutable
source tree:
https://github.com/hexgrad/misaki/tree/fba1236595f2d2bf21d414ba6e57d25256afada3/misaki/data .
Retain `native/Apache-2.0.txt` and the complete package notices under `python/`.

| Selected dictionary | SHA-256 | Git blob identity |
| --- | --- | --- |
| `gb_gold.json` | `29e62f4b60261c88f7f3c2c7811ca3825978948090b72d2b27d565b729282f71` | `8c7de92c8bf311dcd145fdde163a9d43ffa7d08a` |
| `gb_silver.json` | `48131e2d92ccc41655f4543e87e0f938e71463eb5a54be7f0693bb712ebb6bce` | `9c9d24390be5cda8a6c102d845ab012fe3d2ae4b` |
| `us_gold.json` | `dc414872a49a28ae6c141463d502fd945f3b2fde040484fdc47d00cc4612686f` | `8ef4bdc43cf8e29a8d259e674f3c3d60e1b0376b` |
| `us_silver.json` | `de8f67be911bb6c659187b4a65fd966b6a30e56350e0f790d763210b053ac475` | `121ba0c4a4ed40d284a58f9fd1fcaa2003613df0` |

The separately hosted current HF dataset has different blobs; it is not used as
the exact-byte source reference for these four distributed files. The reviewed
distribution path does not alter these dictionary files.

## spaCy English pipeline and retained source notices

`en_core_web_sm` 3.8.0 is supplied under its MIT model license:
https://github.com/explosion/spacy-models/releases/tag/en_core_web_sm-3.8.0 .
Preserve its complete LICENSE and LICENSES_SOURCES, including WordNet 3.0's
copyright, permission and disclaimer. OntoNotes is identified there as upstream
training data licensed by Explosion; no raw OntoNotes training corpus is selected.
Accompanying files:

- `python/en_core_web_sm-3.8.0/en_core_web_sm/en_core_web_sm-3.8.0/LICENSE`
- `python/en_core_web_sm-3.8.0/en_core_web_sm/en_core_web_sm-3.8.0/LICENSES_SOURCES`
- `python/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0.dist-info/LICENSE`
- `python/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0.dist-info/LICENSES_SOURCES`

## Adapted inference code

Violilt's inference adapter and retained helpers derive from Kokoro-ONNX 0.6.1,
copyright 2025 github.com/thewh1teagle, under MIT. Configuration/inference are
modified for Violilt's English pronunciation path. Retain the complete license
at `native/kokoro-onnx-MIT-LICENSE.txt`, plus the separate permission/copyright
notice at `native/librosa-trim-NOTICE.txt` and the notices retained in source.

Final candidate checks must confirm these exact artifacts and all accompanying
notices. Hashes identify selected bytes; no upstream asset digest or independent
conversion reproduction is implied by this notice.
