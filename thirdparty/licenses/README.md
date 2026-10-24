# Supplemental notice provenance

These verbatim upstream notices cover artifacts whose wheel or baseline package
does not reliably collect their complete texts. Other versioned notices are
collected from the installed candidate distributions by the notice assembler.

- pypdf 6.21.2 BSD-3-Clause license: exact approved PyPI wheel, verified with
  SHA-256 `1d44d1a3a200f25062adff0085b02040e4646431ac2ccac22e42679e91466084`.
  The notice assembler also collects this wheel's installed license.
  [Versioned upstream license](https://github.com/py-pdf/pypdf/blob/6.21.2/LICENSE).

- WebView2 SDK 1.0.3856.49 LICENSE and NOTICE: inspected official NuGet SDK archive;
  the baseline pywebview Core/WinForms DLLs matched that archive. CPU bridge
  versions are held fixed in this candidate. [Official package](https://www.nuget.org/packages/Microsoft.Web.WebView2/1.0.3856.49).
- kokoro-onnx 0.6.1 MIT license: exact baseline installed distribution. The
  candidate's trimmed inference adapter derives from that version.
  [Upstream](https://github.com/thewh1teagle/kokoro-onnx).
- librosa trimming implementation permission notice: complete retained module docstring
  from `backend/_vendor/kokoro/trim.py`, as adapted by the Kokoro-ONNX wrapper.
  This is shipped as a separate readable notice as well as retained in code.
- FlatBuffers 25.12.19 license: exact upstream tag; its Python wheel does not
  include a license file. [Tag license](https://github.com/google/flatbuffers/blob/v25.12.19/LICENSE).
- proxy_tools 0.1.0 license: upstream LICENSE.txt retains both proxy_tools and
  Werkzeug attributions. The matching digest-verified PyPI source distribution
  is also available in candidate source materials.
  [Upstream license](https://github.com/jtushman/proxy_tools/blob/master/LICENSE.txt).

These notices do not cover the separate Microsoft VC/UCRT or NVIDIA runtime
redistribution questions. Exact native artifact/source and model provenance review
remain documented release gates.

## Selected-runtime and frontend supplements

The collector retains these additions alongside every existing package notice;
they do not replace NumPy's legal files, both ONNX Runtime notice sets, spaCy's
WordNet terms, Lucide/Feather, WebView2, or other existing notices.

- Expat 2.8.5: verbatim `R_2_8_5/COPYING`. The actual selected Windows runtime
  records Expat 2.8.5; the generic PBS table's 2.9.0 is a different declaration.
  https://github.com/libexpat/libexpat/blob/R_2_8_5/COPYING
- Base-runtime libffi: verbatim LICENSE at the Windows recipe's pinned CPython
  source-deps commit `16fad4855b3d8c03b5910e405ff3a04395b39a98` (copyright through
  2021). The recipe candidate declares 3.4.2; no measured compiled version/patch
  set is asserted for `libffi-8.dll`. This supersedes the older generic PBS
  1996-2019 candidate as the proposed source-pin notice, preserving prior evidence.
  https://github.com/python/cpython-source-deps/blob/16fad4855b3d8c03b5910e405ff3a04395b39a98/LICENSE
- CFFI 2.1.1 embedded libffi: distinct verbatim `src/c/libffi_x86_x64/LICENSE`,
  copyright 1996-2003 Red Hat. Tagged MSVC setup compiles that directory;
  CFFI's top-level MIT-0 label does not replace this attribution.
  https://github.com/python-cffi/cffi/blob/v2.1.1/src/c/libffi_x86_x64/LICENSE
- CPython 3.12.15 stdlib: complete versioned `Doc/license.rst`, retained
  conservatively alongside the actual runtime's LICENSE.txt. This upstream list
  calls itself incomplete; sections for optional/unshipped modules do not prove
  inclusion. Its older OpenSSL discussion is historical, not the governing license
  of selected OpenSSL 3.5.9. The selected Apache-2.0 text remains retained.
  https://github.com/python/cpython/blob/v3.12.15/Doc/license.rst
- libmpdec: PBS's tagged notice (copyright 2008-2020 Stefan Krah), whose complete
  permission/disclaimer also appears in the selected CPython document's libmpdec
  section. CPython 3.12's Windows recipe uses bundled libmpdec; final `_decimal`
  inclusion still requires final-payload reconciliation.
  https://github.com/astral-sh/python-build-standalone/blob/20261021/LICENSE.mpdecimal.txt
- Full LGPL-2.1 and MPL-2.0 texts supplement, never replace, component-specific
  notices and matched source archives. Source access and any LGPL section 6
  arrangement need their separate completed release materials.
  https://www.gnu.org/licenses/old-licenses/lgpl-2.1.txt
  https://www.mozilla.org/MPL/2.0/
- DOMPurify 3.4.17: `DOMPurify-3.4.17-license-choice.txt` documents the Apache
  alternative. Existing frontend notices and the generic Apache text remain.

These additions are scoped notice inputs. Binary/build correspondence, vendor
authority, matching covered source, practical replacement and actual final
payload inclusion remain separate reviews. Runtime/package changes require the
affected versioned texts and mappings to be reviewed again.
