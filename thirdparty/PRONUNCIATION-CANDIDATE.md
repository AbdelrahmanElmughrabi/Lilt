# English pronunciation candidate: third-party terms and release review

This development build evaluates Misaki 0.9.4 English without its `en` extras or
eSpeak fallback. Violilt-owned application code may remain proprietary. Third-party
code and data retain their own terms; this document is not blanket release clearance.

`third-party/` beside the candidate executable contains versioned package notices,
the Python runtime license, frontend notices, source archives and a manifest.
The manifest distinguishes the installed build environment from actual packaged
modules. A post-build audit examines the executable's archive and package files.

Misaki is Apache-2.0; the spaCy engine and small English model are MIT; Kokoro's
upstream model is Apache-2.0. The trimmed ONNX adapter derives from the MIT
kokoro-onnx wrapper. Their applicable license texts and notices must remain with
distributed copies. Only English Misaki dictionaries are collected.

num2words 0.5.14 is LGPL. Its unchanged source is collected as external `.py`
files in `_internal/num2words`, outside the executable archive. A usable section-6(b)
arrangement with interface-compatible modified libraries still requires final
validation; external placement alone is insufficient for a protected MSIX. A matching upstream source archive
and its license are supplied under `third-party/sources`. certifi and tqdm contain
MPL-covered code; their covered source and license texts are supplied there too,
and external Python source is retained when collected. These component licenses
do not turn independent Violilt files into open-source files.

Generated sections use NumPy and the standard-library PCM16 WAV writer.
The actual candidate must exclude SoundFile/libsndfile runtime modules and native
binaries even when optional developer tools still have SoundFile installed.
Historical notices/source materials are preserved; they do not authorize an old
payload containing the DLL. Any reintroduction requires exact native source,
rights and practical replacement review. Existing num2words LGPL and certifi/tqdm
MPL obligations and eventual application exceptions remain separate.

Review gates before any external release:

- Reconcile the exact final Kokoro model/whole-voice and selected dictionary
  bytes with the accompanying MODEL-ATTRIBUTIONS.md, complete license texts and
  applicable modification/attribution notices. Retain the recorded supplier chain
  without asserting an independently reproduced conversion recipe.
- Verify actual absence of removed SoundFile/libsndfile runtime modules and
  binaries, and preserve applicable historical notice/source evidence.
- Review actual package native/vendored contents and complete applicable notices;
  a permissive top-level package label does not cover every artifact automatically.
- Establish redistribution authority for Microsoft VC/UCRT/API-set runtime DLLs.
- For optional GPU packages, match each NVIDIA DLL/version with its authoritative
  redistribution grant and notices. Runtime-only collection reduces scope but does
  not settle mismatches in wheel versus current online terms.
- Review app/icon rights and eventual app EULA, installer and Store requirements.

No Store publication, commercial release or blanket legal approval is authorized
by this development build. Baseline recordings and libraries remain separate.

Primary references: [Misaki](https://github.com/hexgrad/misaki),
[spaCy model](https://github.com/explosion/spacy-models/releases/tag/en_core_web_sm-3.8.0),
[Kokoro model](https://huggingface.co/hexgrad/Kokoro-82M),
[kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx),
[libsndfile licensing](https://libsndfile.github.io/libsndfile/#licensing),
[MPL source obligations](https://www.mozilla.org/en-US/MPL/2.0/FAQ/).

Accompanying-source paths and license rights are detailed in `SOURCE-RIGHTS.md`;
model/voice/data identities and acknowledgements are in `MODEL-ATTRIBUTIONS.md`.
These documents remain development-candidate records, not final release clearance.
