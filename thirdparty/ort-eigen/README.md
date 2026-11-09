# Eigen source accompanying CPU ORT 1.30.0 and GPU ORT 1.24.4

This complete source archive and the two original release patches are associated
with both official ONNX Runtime release recipes. The recipes and patches are
byte-identical across those tags. This is a declared-release source arrangement,
not measured Windows-wheel compilation attestation. R-03 N2 protobuf remains
separate. Retain all upstream license/copyright files inside the archive.

Source revision: 1d8b82b0740839c0de7f1242a3585e3390ff5f33.
Archive: eigen-1d8b82b0740839c0de7f1242a3585e3390ff5f33.zip (4,075,744 bytes).
Upstream-declared SHA-1: 05b19b49e6fbb91246be711d801160528c135e34.
Locally recorded SHA-256: 6a60d76351f97132669daeeb721d6bf14b008101883ad2d687a3201c5c461eb0.
The SHA-256 is not represented as an upstream-published SHA-256.

To obtain the modified source form from these accompanying files:

1. Unpack the complete archive, preserving its source root and full notices.
2. From that source root apply s390x-build.patch first, then
   s390x-build-werror.patch. The original eigen.cmake records the command order
   and --binary --ignore-whitespace -p1 options. With a compatible patch utility:

   patch --binary --ignore-whitespace -p1 < ../s390x-build.patch
   patch --binary --ignore-whitespace -p1 < ../s390x-build-werror.patch

3. Keep both unmodified patch files and original source; these identify the
   published modifications. Their names do not justify dropping them for Windows.
   The set touches ZVector headers and RandomImpl.h.

The full source includes COPYING.MPL2 and other upstream license files. Covered
source remains under its applicable licenses; recipients may modify/redistribute
it accordingly. No independent application source or LGPL relink obligation is
inferred merely from Eigen MPL coverage. The four disposable headers used in a
preparation check are not this complete source and are not the delivered bundle.

source-manifest.json records original official URLs/hashes, both runtime tags and
the ordered patches. Source/patch identity alone does not demonstrate every final
wheel compiler input; final payload/source-notice inclusion remains separate.
