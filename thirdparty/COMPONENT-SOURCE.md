# Accompanying component source and license rights

This development candidate accompanies its third-party components with source
archives and notices in the `third-party` folder beside the executable. No hosted
service, email-only source offer or three-year written offer is used here.

## Obtain the accompanying source

Open `third-party/sources/` and use a tar-compatible archive reader to extract
the component archive you need. `sources/source-manifest.json` records origin,
version and SHA-256. Keep original license/copyright files with extracted source.

| Component | Path relative to this folder | SHA-256 |
| --- | --- | --- |
| num2words 0.5.14 | `sources/num2words-0.5.14.tar.gz` | `b066ec18e56b6616a3b38086b5747daafbaa8868b226a36127e0451c0cf379c6` |
| certifi 2026.10.19 | `sources/certifi-2026.10.19.tar.gz` | `035c1e85572b141bf1c3a3eff0e33a8eb74917522f2559075ff8d2fea780a1ae` |
| tqdm 4.70.1 | `sources/tqdm-4.70.1.tar.gz` | `cefd0eca11b2a37a3aee776544d4f4ae913f02688135b5556b8788dfa474afc4` |
| soundfile 0.13.1 | `sources/soundfile-0.13.1.tar.gz` | `b2c68dab1e30297317080a5b43df57e302584c49e2942defdde0acccc53f0e5b` |
| proxy_tools 0.1.0 | `sources/proxy_tools-0.1.0.tar.gz` | `ccb3751f529c047e2d8a58440d86b205303cf0fe8146f784d1cbcd94f0a28010` |

The num2words, certifi, tqdm, SoundFile-wrapper and proxy_tools source matches
the reviewed unmodified selected files. These archives are not asserted to
provide source for unrelated native libraries or other components.

## LGPL num2words

num2words 0.5.14 remains LGPL-2.1-or-later. The contemplated compliance route
uses LGPL 2.1: accompanying library source and notices, with section 6(b)'s
suitable shared-library mechanism for the applicable combined work. The frozen
layout selects `_internal/num2words` as external Python source, not frozen PYZ
code. The current classic-EXE replacement procedure is in
`LIBRARY-REPLACEMENT.md`; the protected Store/MSIX arrangement remains separate.
Compatible library modifications must be usable under the actual provided
arrangement. The full text is at `native/LGPL-2.1.txt`; retain library-specific
copyrights and COPYING under `python/` and in the source archive.

The section 6 permission concerns modification of the work for the recipient's
own use and reverse engineering to debug those modifications. It cannot be
narrowed to library-file edits by an application prohibition. Final application
terms must preserve that permission and the applicable component rights.

## MPL certifi and tqdm

certifi 2026.10.19 and MPL-covered tqdm 4.70.1 files remain MPL-2.0. Their covered
source, including certifi CA data, is in the accompanying archives above and
external source directories when collected. The full text is at `native/MPL-2.0.txt`.
Retain tqdm's MIT contribution notices as well as MPL notices. Covered source
may be inspected, modified and redistributed under its license; application
terms must not limit those source rights. This accompanying-media method provides
the source directly, without a source-access charge. MPL alone does not impose
LGPL section 6 executable replacement/relink requirements.

## Eigen source for ONNX Runtime

CPU ONNX Runtime 1.30.0 and GPU ONNX Runtime 1.24.4 declare the same Eigen
revision 1d8b82b0740839c0de7f1242a3585e3390ff5f33 and ordered patch set.
The complete source arrangement is at `sources/onnxruntime-eigen/`: pinned source
ZIP, both original patches, original eigen.cmake, full source-access README and
source-manifest.json. The archive retains all upstream licenses, including MPL2.

Archive SHA-1 declared by upstream: 05b19b49e6fbb91246be711d801160528c135e34.
Locally recorded archive SHA-256:
6a60d76351f97132669daeeb721d6bf14b008101883ad2d687a3201c5c461eb0.
The latter is a local identity pin, not an upstream-published SHA-256.

Follow that README to unpack full source and apply s390x-build.patch, then
s390x-build-werror.patch, preserving the original source/notices and both patches.
The filenames do not justify omitting patches on Windows. Covered source remains
under its applicable licenses, and application terms do not restrict those rights.
No MPL executable replacement/relink requirement or independent app-source
disclosure is inferred. This is the ordinary official-release source/patch
association, not a measured attestation of every Windows-wheel compilation input.
Final source inclusion/access and R-03 N2 protobuf remain separate.

## Native audio runtime retirement

Generated sections use NumPy and the standard-library PCM16 WAV writer. The new
candidate must exclude SoundFile/libsndfile runtime modules and native binaries,
including when optional developer tools still have SoundFile installed. Its
package audit must prove actual absence and presence of the generated PCM writer.

Existing SoundFile-wrapper and bare libsndfile source archives/notices remain
review material. Their retention is not runtime inclusion, and does not clear
older payloads that distribute the static-codec DLL combination. Reintroducing
that combination requires complete matching source/build/patch materials and an
actual compatible-library arrangement before distribution. No such source or
replacement claim is made for an older payload by this retirement proposal.

The num2words LGPL section 6(b) arrangement, applicable application-term exception
and future protected-package delivery remain separate; removal of native audio
does not settle those requirements. See `LIBRARY-REPLACEMENT.md` for the writable
classic-EXE procedure.

Third-party source rights do not automatically require disclosure of independent
Violilt files. Model/GPU integrity and package-signature controls remain separate
and must not be weakened to manufacture a replacement test pass.
