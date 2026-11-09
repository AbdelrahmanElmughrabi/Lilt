# Combined R-03 remediation review prompt

Send this to the independent review chat:

```text
Review the current combined R-03 source remediation in:
C:\Users\fireball\OneDrive\Desktop\LiltTTS

Read docs/r03-runtime-sanitizer-results-2026-10-22.md and its trace/plan,
docs/r03-audio-remediation-results-2026-10-22.md and its plan, and the standing
review rules in docs/release-review-handoff.md. The earlier investigation passed
within its scope; the audio/runtime/sanitizer implementations are NOT independently
accepted yet. Review the combined current revision rather than repeating the old
unchanged 178-query investigation or silently testing mixed snapshots.

Verification only: preserve product source/tests, dependencies, shared assets and
all previous evidence. No installations, Git mutations, model downloads, EXE/MSIX
build/install, personal-data access, publication or messages to another chat.
Use existing tools and fresh uniquely named workspace evidence folders. Backup
requirement is waived. Check relevant hashes before and after; include untracked
inputs. Do not infer final/installed package approval from a source pass.

Current manifest: .tmp/r03-updates-20261022/source-hashes.json
Prior 450 audio-revision input contents: .tmp/r03-updates-20261022/input-snapshot/
Prior audio manifest/report/evidence remain unchanged. Earlier 386 investigation
contents are separately preserved under .tmp/r03-remediation-20261022/input-snapshot/.
These content snapshots are not complete Git checkouts or frozen environments.

Use the NEW interpreter for current-source/runtime checks:
.tmp/r03-updates-20261022/env/Scripts/python.exe
The preserved .tmp/pronunciation-env is the older 3.12.14 baseline. Its actual use
for comparison must be labeled explicitly. The preserved frontend/node_modules is
3.4.16; selected dependencies are .tmp/r03-updates-20261022/frontend/node_modules
at 3.4.17. The canonical frontend/dist matches the staged browser-tested new UI.
Do not rebuild shared assets; inspect input/provenance hashes and use an isolated
copy if a narrowly justified build is needed with existing dependencies.

Inspect the audio parser/consumers under the earlier audio review prompt, including
bounded chunks/formats/allocations, actual native-call exclusion, coherent reads,
changed files, cache/export atomicity, original retention, resume/cancellation,
sample/pause/timeline correctness and canonical HTTP HEAD/Range/playback. Actual
app audio source was unchanged in this runtime/sanitizer batch.

Inspect packaging/release-runtime.json, tools/verify_release_runtime.py,
tools/prepare_release_runtime.py, tools/build_frontend.py, setup-pronunciation.ps1,
build.ps1 and notice assembly. Check actual artifact size/SHA/provenance, nine
native pins, old-runtime rejection, safe extraction and build input selection.
Verify that a future build uses current canonical frontend source with matching
isolated dependencies, not stale staged source or the preserved old node_modules.
Assess failure paths/preserved assets and notice-lock/version correctness. The
full setup/build scripts were syntax checked, not end-to-end executed; no frozen
artifact was created. Runtime byte pins are a selected subset, not a final SBOM.

Important discrepancy: actual Windows runtime is CPython 3.12.15 / OpenSSL 3.5.9 /
Expat 2.8.5, NOT Expat 2.9.0. The generic upstream dependency table was misleading
for the Windows artifact. No 2.9.0 backport/patch is claimed. Independently assess:
- CVE-2026-102633: upstream describes a 32-bit-only overflow, selected runtime x64.
- CVE-2026-77214: invalid XML_ParseBuffer lengths. Review CPython 3.12.15 Parse,
  ParseFile/readinst bounds and ElementTree capsule use, actual benign wrapper
  results and all relevant application/native consumers. A proposed scoped
  non-applicability disposition is awaiting YOUR acceptance, not already settled.
Consider the upstream unfixed-issues warning and provenance limits. If evidence
is insufficient or the disposition fails, require a compatible verified patched
runtime/backport before release. Do not require merely a literal version label,
and do not turn source inference into demonstrated compiled patch coverage.

Verify the exact DOMPurify 3.4.17 lock/installed/built/notices integration. Only
root direct version and DOMPurify lock entry changed; other locked entries equal.
Current narrow string/HTML/no-attributes options remain. Four app-config probes
and the text-only XHTML advisory control passed; don't execute unsafe native
exploits or insert/click the nondefault control. The updated OSV query was empty,
which is dated supporting data, not evidence replacing maintainer advisories.

Review validation honestly. Initial updated runtime ran 301 methods with 300
passes/one Windows skip; four release-runtime tests were added. Several full
305-method runs hit a WinError 145 temporary-folder TEARDOWN error, including
outside OneDrive. No assertion failure in those runs. Failed logs and corrected
guarded comparison outcomes are retained; read the report's final addendum.
The first standalone diagnostic lacked a multiprocessing main guard and was
invalid; its two owned processes were stopped. Never use that attempt as baseline
evidence. The corrected runner has a proper main guard and suppresses/retries no
errors. Determine the cleanup issue's cause/scope rather than erasing it with
ignore_errors, retries or calling every run a pass. Old/new Python cleanup source
files are byte-identical. Relevant test-class repetitions passed on both runtimes.

Final ordinary run: 305 methods, 303 passed/one failure/one skip. The failure is
test_sampler_releases_counter_when_ui_stops_polling, closed.wait(1), at
tests/test_gpu_usage.py:379; no cleanup error in this run. The unchanged full GPU
module then passed three times on each runtime. Both corrected full comparisons
passed 304/one skip. These mixed results do not prove a new-runtime regression
or a clean ordinary-suite result; independently investigate the timing-sensitive
finding. Do not silently extend the deadline or rerun until green as acceptance.

Also inspect/rerun appropriately: 15 browser cases, six native debug-off close
cases, browser media boundary, actual CPU/CUDA with approved existing fixtures,
TLS/XML and notice collection. Label rerun versus saved evidence inspected.
Do not require broad reruns unless justified by changed inputs/findings.

Example current runtime command:
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:TEMP = '<new owned writable test-temp directory>'
$env:TMP = $env:TEMP
& .tmp/r03-updates-20261022/env/Scripts/python.exe -B -m unittest discover -s tests -v
& .tmp/r03-updates-20261022/env/Scripts/python.exe -B tools/verify_release_runtime.py
$env:PLAYWRIGHT_MODULE = 'C:\Users\fireball\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules\playwright'
& 'C:\Program Files\nodejs\node.exe' --test tests/test_editor_save.cjs

Only existing public model fixtures may be used for real generation:
dist/validation-bbe961f-20261022/Violilt/models and approved
.tmp/pronunciation-gpu-runtime. Read helpers first; write new output folders.
Native/loopback checks can require sandbox escalation, not Windows admin rights.

R-02 parent-cache/startup/close, deleted-recording retry and navigation-helper
findings remain separately unresolved. Do not credit them as fixed by these checks.
Keep final native/frozen package, installed MSIX, mandatory final-MSIX testing on
another machine, low-end/no-GPU, licensing/privacy and Store certification separate.

Return scoped passes/needs fixes/insufficient evidence, actionable findings with
severity, absolute file/line, trigger, expected/actual, reproduction, exact versions
and hashes. Distinguish new regressions, previous findings and harness problems.
Record checked/unverified claims, practical limits, report path and remaining gate
decisions. Stop after reporting; do not implement fixes or publish anything.
```
