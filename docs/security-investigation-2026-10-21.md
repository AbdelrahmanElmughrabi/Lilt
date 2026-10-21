# Violilt security investigation — 21 October 2026

**Historical baseline:** fixes applied after this investigation are tracked in
[release hardening results](release-hardening-2026-10-21.md) and the combined
[release readiness checklist](release-readiness.md). The findings below describe
the pre-fix working tree and retain the original reproduction evidence.

**Result: address the findings below before public release, then audit the installed release package.** The checks found specific hardening and data-recovery gaps. They did not demonstrate a remote takeover through imported Markdown or a foreign website. No application code, dependency versions, or personal libraries were changed during this investigation.

## Scope and baseline

This review covers the current working tree, including the Violilt rebrand and existing uncommitted work, based on commit `c8acbab63643871c59c372b43ae1c6697f8e2904`. It combines source inspection, dependency advisory queries, disposable database/model fixtures, an isolated production frontend build, browser probes, and native WebView2 checks. It is not certification of every possible attack path.

The environment used Python 3.12.14 on Windows 11 build 26200, pywebview 6.2.1, CPU ONNX Runtime 1.30.0, and GPU ONNX Runtime 1.24.4. The browser probe used Edge 155.0.4283.62; that version should not be assumed to identify the separately hosted WebView2 runtime.

SHA-256 values for 75 source/build/configuration files were recorded and rechecked unchanged. All writes from the runtime probes went to disposable audit fixtures. The advisory services received package names and versions, not document contents. Evidence is retained in the ignored [.tmp/security-20261021 directory](C:/Users/fireball/OneDrive/Desktop/LiltTTS/.tmp/security-20261021); copy it deliberately if evidence needs to survive workspace cleanup. See the [baseline](C:/Users/fireball/OneDrive/Desktop/LiltTTS/.tmp/security-20261021/baseline.json).

## Checks that passed

| Check | Result and limit |
| --- | --- |
| Existing backend tests | **150 passed** in 20.486 seconds. This includes the existing storage, server, desktop, and instance-lock coverage. |
| Frontend checks | Svelte/TypeScript check passed with zero errors/warnings; isolated production build succeeded. |
| Frontend dependency advisory check | `npm audit --json --package-lock-only`, including development dependencies, reported zero known findings. This is a dated registry result, not proof of absence. |
| Markdown rendering | The compiled frontend stripped tested scripts, event attributes, dangerous links, frames, SVG, form, and mutation-style payloads; no injected marker executed. |
| Content Security Policy | An ordinary same-origin script was prevented from using dynamic evaluation. The result was checked outside DevTools' evaluation bypass. |
| Browser isolation | A separate origin could not read the synthetic audio response through `fetch`. Host and encoded traversal checks returned 403; unknown audio identifiers returned 404; POST returned 501. Framing/resource headers were present. |
| Native startup/playback | Debug off, native bridge, Home, saved WAV, playback-position recovery, and replay checks passed. A separate native probe confirmed foreign navigation was blocked. |

Evidence: [unit tests](C:/Users/fireball/OneDrive/Desktop/LiltTTS/.tmp/security-20261021/unittest.log), [npm audit](C:/Users/fireball/OneDrive/Desktop/LiltTTS/.tmp/security-20261021/npm-audit.json), [browser results](C:/Users/fireball/OneDrive/Desktop/LiltTTS/.tmp/security-20261021/browser-results.json), [native startup](C:/Users/fireball/OneDrive/Desktop/LiltTTS/.tmp/security-20261021/native-startup.log), and [controlled probe results](C:/Users/fireball/OneDrive/Desktop/LiltTTS/.tmp/security-20261021/probes.json).

## Findings and proposed fixes

Priority describes the proposed release order. Severity describes the demonstrated application exposure; upstream advisory severity is stated separately.

### S-01 — Affected certificate bundle and outdated build tooling

**Priority: first fix batch. Exposure: conditional runtime trust risk and build supply-chain risk.**

[requirements.lock.txt:9](C:/Users/fireball/OneDrive/Desktop/LiltTTS/requirements.lock.txt:9) pins certifi 2026.7.22. The installed bundle contains emSign roots affected by the maintainer's newly published, upstream **Critical** advisory concerning compromised intermediate keys. Use the verified available release **2026.10.19** as the update target. The advisory names 2026.10.18 as patched, while the current published release is 2026.10.19. Sources: [maintainer advisory](https://github.com/certifi/python-certifi/security/advisories/GHSA-6q48-6c7w-9gw2), [published release](https://pypi.org/project/certifi/2026.10.19/).

This does **not** establish a working man-in-the-middle attack against Violilt: the model downloader uses urllib's default SSL context, does not explicitly select certifi, and the default context inspected here did not contain emSign. The package specification nevertheless collects certifi, so remove the affected dependency from the release payload. See [TLS evidence](C:/Users/fireball/OneDrive/Desktop/LiltTTS/.tmp/security-20261021/tls-check.json).

The CPU environment also has pip 25.0.1. OSV returned six distinct pip advisories after deduplicating GHSA/PYSEC aliases: `GHSA-4xh5-x5gv-qwph`, `GHSA-58qw-9mgm-455v`, `GHSA-6vgw-5pg2-w6jp`, `GHSA-jp4c-xjxw-mgf9`, `GHSA-qwm4-qh6w-59xr`, and `GHSA-wf93-45jw-7689`. These concern installation/input handling. pip is build tooling; the inspected package audit did not list it as a frozen runtime module. These are not six demonstrated customer-facing exploits.

**Fix and acceptance:** explicitly bootstrap a patched, pinned pip in [setup-pronunciation.ps1:13](C:/Users/fireball/OneDrive/Desktop/LiltTTS/setup-pronunciation.ps1:13), update certifi and required hashes, recreate environments, and rebuild. pip **26.2.2** is the verified current target and includes the updated vendored certifi. Repeat advisory checks and inspect the resulting payload. The [pip changelog](https://pip.pypa.io/en/stable/news/) documents that release. The [saved Python advisory evidence](C:/Users/fireball/OneDrive/Desktop/LiltTTS/.tmp/security-20261021/python-advisories.json) covers 79 distinct installed package/version pairs across CPU and GPU environments; it is not a complete native-DLL advisory audit.

### S-02 — Native messages can dispatch private Python methods

**Priority: first fix batch. Severity: Medium, conditional on app-origin script execution.**

[desktop.py:44](C:/Users/fireball/OneDrive/Desktop/LiltTTS/backend/desktop.py:44) correctly checks the browser-provided message source, then forwards ordinary messages to pywebview's generic handler. In the pinned dependency, that handler resolves dotted attributes on the Python API object. The advertised public JavaScript API is therefore not an enforced native dispatch allowlist.

**Reproduction:** in a minimal real WebView using the app's server, bridge, and adapter, an app-origin native message naming `_store.save_settings` persisted an invalid theme directly through the private Store object. It bypassed the public Bridge method's theme validation. The probe changed only its disposable database and executed no shell command. See [native-boundary results](C:/Users/fireball/OneDrive/Desktop/LiltTTS/.tmp/security-20261021/native-boundary-results.json) and [probe source](C:/Users/fireball/OneDrive/Desktop/LiltTTS/.tmp/security-20261021/native_boundary_probe.py).

An attacker would first need script execution in the allowed app page, such as a separate injection or compromised frontend asset. The tested Markdown payloads did not provide that prerequisite. The issue increases the consequences of a future injection.

**Fix and acceptance:** enforce an exact list of intended public methods and necessary framework control messages before generic dispatch; reject private/dotted traversal and malformed or oversized arguments/callback identifiers. Confirm private calls fail while supported calls, return delivery, native file drops, navigation blocking, and playback still work. This follows Microsoft's guidance to validate messages and avoid generic host proxies: [WebView2 security](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/security).

### S-03 — Model integrity checks can accept unverified content

**Priority: first fix batch. Severity: Medium, model supply-chain boundary.**

[models.py:73](C:/Users/fireball/OneDrive/Desktop/LiltTTS/backend/models.py:73) checks a hash only when upstream metadata supplies `digest`. [models.py:24](C:/Users/fireball/OneDrive/Desktop/LiltTTS/backend/models.py:24) checks voice-file readability and model size, rather than an approved model hash or model validity.

**Reproduction:** mocked download responses omitted the digest, supplied a valid synthetic NumPy voice archive and 1,000,001 bytes of known non-model data. The files were promoted and reported **ready**. No synthetic ONNX content was passed to the inference engine. This proves acceptance of unverified bytes, not exploitation of a native parser.

**Fix and acceptance:** define an approved versioned model/voice manifest with mandatory known hashes, reject missing/mismatched integrity information, and apply a deliberate trust policy to bundled, imported, and GPU models. A hash supplied by the same replaceable download channel alone does not provide independent provenance. Missing, changed, truncated, and wrong-version fixtures must fail before activation; approved CPU/GPU sets must still work.

### S-04 — Failed model import overwrites the previous files

**Priority: second fix batch. Severity: Medium, availability/recovery.**

[models.py:84](C:/Users/fireball/OneDrive/Desktop/LiltTTS/backend/models.py:84) replaces each model destination before validating the complete imported set. The disposable reproduction started with identifiable old fixture bytes, imported invalid files, and confirmed the old bytes were gone when the state became `error`. It establishes the destructive replacement order; it did not use a genuine working model set.

**Fix and acceptance:** stage and validate the complete set before activation, then use a recoverable switch or rollback. Coordinate import/download with generation. A failed validation, interrupted copy, or failed activation must retain the previous usable set. See the `invalid_import` result in the controlled probe evidence.

### S-05 — Settings validation and database recovery are incomplete

**Priority: second fix batch. Severity: Medium, primarily reliability.**

[bridge.py:166](C:/Users/fireball/OneDrive/Desktop/LiltTTS/backend/bridge.py:166) validates only part of the settings schema. Public calls accepted and persisted `voice: null`, `heading_pause: "not-a-number"`, and `include_code: "false"`. Separately, one malformed JSON settings row in a disposable SQLite database caused an unhandled `JSONDecodeError` when [storage.py:137](C:/Users/fireball/OneDrive/Desktop/LiltTTS/backend/storage.py:137) read settings.

The current schema is created with `IF NOT EXISTS`; a general versioned migration/backup/recovery mechanism was not found. Invalid settings can break later computations, and malformed saved JSON definitely breaks the tested settings read. Ordinary UI controls were not shown to generate these malformed inputs.

**Fix and acceptance:** centralize types, allowed values, finite numeric ranges, and voice validation; validate persisted data when loading. Add schema versions, consistent backups, transactional migrations, unknown-newer-version protection, and a recoverable path for malformed rows. Corruption tests must preserve unaffected documents/settings and present a usable recovery result. Include document/job JSON as well as settings.

### S-06 — Library import follows directory junctions outside the selected source

**Priority: second fix batch. Severity: Low, conditional import/privacy risk.**

[storage.py:60](C:/Users/fireball/OneDrive/Desktop/LiltTTS/backend/storage.py:60) copies arbitrary source subdirectories using `shutil.copytree`. A synthetic imported library contained a directory junction to a sibling fixture folder. The marker outside the selected source was copied into the destination. Both folders were inside the audit directory; no personal files were accessed.

This requires an explicitly selected, untrusted library folder with a reparse point. It is not a Markdown import attack or demonstrated remote file disclosure.

**Fix and acceptance:** allowlist managed library entries, reject unexpected reparse points, and enforce source containment plus copy-size limits. Test file and directory links/junctions. Also verify source-library quiescence: SQLite backup is consistent, but separately copied job/audio files need a coherent snapshot. The possible concurrent-copy inconsistency was identified by inspection, not dynamically reproduced.

## Additional hardening and privacy work

- **Import limits:** [bridge.py:154](C:/Users/fireball/OneDrive/Desktop/LiltTTS/backend/bridge.py:154) reads the entire Markdown file; no practical file/batch cap was found. Add useful size limits, disk-space handling, and cancellation. Resource exhaustion was not attempted.
- **Local audio access:** a raw client knowing a completed job's random identifier can fetch its audio without a session credential. The actual browser cross-origin read failed, and CORS/CORP/framing defenses were present. Consider session-bound resource access as additional protection; the evidence does not show cross-site audio theft or guessable identifiers.
- **Data protection:** SQLite, audio, cache, logs, and backups need an explicit permissions, retention, export/deletion, and privacy-policy design. Plaintext storage alone does not establish a vulnerability. Cross-user Windows ACL behavior and all encryption threat models were not audited.
- **GPU code-loading trust:** the `VIOLILT_GPU_RUNTIME` override can select an import path. This is a local environment/install-directory trust boundary, not a demonstrated remote exploit. Verify installed package permissions, approved runtime provenance, and CPU/GPU DLL loading in the final build.
- **Secrets:** the targeted source scan found no tested private-key/AWS/GitHub credential patterns. Full Git history and every possible credential format were outside scope.

## Release gates and recommended sequence

1. Fix S-01 through S-03; rerun focused boundary, integrity, and advisory checks.
2. Fix model rollback, settings/database recovery, and library-copy boundaries; add practical import limits and resolve the data-protection policy.
3. Build a fresh production package and test installed MSIX behavior with CPU **and NVIDIA GPU support retained**. Audit native dependencies and actual payloads, signing, permissions, worker/runtime loading, and WebView2 behavior.
4. Rehearse an older-to-newer installed update and rollback/recovery while preserving documents, audio, settings, and positions; repeat security regression checks on that exact package.

The existing compatibility MSIX was inspected for manifest metadata only during this investigation; it was not installed or treated as evidence for the current source. No release clearance is claimed for installed updates, GPU execution under package identity, or the complete native dependency inventory. Closed-source packaging and redistribution/license decisions remain separate release work.

**Changes made by this investigation:** this report, its release-register link, and ignored disposable audit evidence only. Application fixes are proposed above and have not been applied.
