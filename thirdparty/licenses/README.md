# Supplemental notice provenance

These verbatim upstream notices cover artifacts whose wheel or baseline package
does not reliably collect their complete texts. Other versioned notices are
collected from the installed candidate distributions by the notice assembler.

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
