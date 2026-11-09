# R-03 runtime and sanitizer update candidate

22 October 2026. This records a concrete next batch, not an installed runtime or verified dependency update. The stored-audio source fix is separate. A specific installation question is pending under the publisher's earlier no-installation-without-authorization rule. No binaries or packages have been downloaded/installed for this plan.

## Trace and candidates

The current build uses `.tmp/pronunciation-env/Scripts/python.exe`, based on the shared Codex Python 3.12.14 runtime. `setup-pronunciation.ps1` accepts a bootstrap interpreter but reuses the existing environment when present; `build.ps1` selects that existing environment. Merely evaluating a new interpreter would not change the production build input. Preserve both the shared runtime and existing environment.

Candidate: Astral python-build-standalone release **20261021**, CPython **3.12.15**, Windows x64 MSVC, `install_only` archive. [Official release](https://github.com/astral-sh/python-build-standalone/releases/tag/20261021), [tagged dependency metadata](https://raw.githubusercontent.com/astral-sh/python-build-standalone/20261021/pythonbuild/downloads.json). These are upstream publisher records, not proof of the downloaded/executed bytes. Saved metadata: `.tmp/r03-remediation-20261022/runtime-releases.json` and `runtime-build-downloads.json`.

- Artifact: `cpython-3.12.15+20261021-x86_64-pc-windows-msvc-install_only.tar.gz` (46,388,793 bytes).
- Official GitHub asset digest: `be7f14464d1d66f84429ad27e01f6d1482963afff64a2fb5256b2a51c7b5d398` (SHA-256).
- The tagged dependency table selects OpenSSL **3.5.9**, Expat **2.9.0**, SQLite **3.53.1**, zlib **1.3.2** and libffi **3.8.0**. Verify actual Windows build configuration and runtime identities; metadata alone cannot close R03-F01.
- Retains `cp312`/Windows x64 rather than introducing a new ABI. Existing CPU, pythonnet/WebView2, PyInstaller and approved cp312 GPU wheels still require actual compatibility testing.

Expat acceptance explicitly includes both [2.9.0 maintainer fixes](https://blog.hartwork.org/posts/expat-2-9-0-released/): CVE-2026-77214's XML_ParseBuffer length validation, and CVE-2026-102633's 32-bit overflow. A demonstrated x64 build limits the second's applicability; it does not settle the first. Require patched compiled component provenance and targeted XML/PDF checks. OpenSSL acceptance includes the reviewed 29 September issues and actual TLS/model-fetch behavior, not just a Python version string.

DOMPurify: upgrade the direct dependency from the installed/locked **3.4.16** to exact **3.4.17**, keeping the current narrow HTML/string allowlist and no attributes. [Maintainer release](https://github.com/cure53/DOMPurify/releases/tag/3.4.17). Its fixes cover the three previously reviewed configurations. No current-config bypass was demonstrated; this is the recommended preventive update.

## Authorized execution sequence when installation approval is given

1. Download only from the identified official release/registry endpoints into a new workspace folder; verify size/SHA-256 or npm integrity before use. Record provenance and license inputs. No arbitrary DLL replacement or change to shared Codex tools.
2. Safely extract the complete runtime, rejecting traversal, links and unexpected entry types. Probe interpreter/build/native component identities, architecture and TLS/XML behavior before bringing in application dependencies.
3. Create a separately named project environment with the existing application/build pins. Retain approved GPU bytes and model fixtures. Check dependency consistency and actual CPU/CUDA, PDF worker spawning, model download/offline/error paths, frontend and native startup/close. Do not fetch fresh model weights.
4. Stage the frontend lock/install in isolation; allow only the intended DOMPurify change, disable lifecycle scripts for dependency installation, retain existing dependency inputs, and build/check/test the staged UI. Refresh built assets and matching notices only as a coordinated reviewed revision.
5. Make the selected build interpreter explicit and enforce the accepted runtime versions/provenance so a default build cannot silently retain the old interpreter. Do not build an EXE/MSIX in this batch. Record a fresh manifest/review prompt and the effect on old inputs.
6. Feed exact native provenance/rights to R-04. Final frozen/installed/another-machine/advisory/certification gates still repeat against the eventual submission bytes. The current artifacts remain stale.

This plan does not install dependencies, mutate locks/assets, switch the build runtime or close R03-F01/F03/F04. R-02's separate parent-cache, deletion/retry and navigation-helper findings remain open.
