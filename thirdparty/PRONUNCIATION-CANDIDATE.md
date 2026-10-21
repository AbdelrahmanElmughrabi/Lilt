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
files in `_internal/num2words`, outside the executable archive, so recipients can
replace it with a compatible modified version. A matching upstream source archive
and its license are supplied under `third-party/sources`. certifi and tqdm contain
MPL-covered code; their covered source and license texts are supplied there too,
and external Python source is retained when collected. These component licenses
do not turn independent Violilt files into open-source files.

SoundFile's bundled libsndfile DLL is an external dynamic library at
`_internal/_soundfile_data/libsndfile_x64.dll`; it can be replaced by a compatible
DLL. Its LGPL terms permit modification and debugging of those modifications.
Any eventual Violilt EULA must preserve the recipient's corresponding LGPL/MPL
rights. Upstream libsndfile source is supplied for review, but exact DLL build and
embedded codec source/provenance arrangements still require completion before
distribution. Replacing source or DLLs must be tested with the candidate app.

Review gates before any external release:

- Complete exact Kokoro ONNX conversion, voice-vector and dictionary provenance,
  including the entire distributed voice artifact and applicable modification notices.
- Verify the exact libsndfile DLL build, included codecs, matching corresponding
  source/build materials and replacement behavior.
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
