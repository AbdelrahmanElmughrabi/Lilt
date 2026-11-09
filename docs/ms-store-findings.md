# Microsoft Store release findings

**Current security investigation (21 October 2026):** see the
[Violilt investigation report](C:/Users/fireball/OneDrive/Desktop/LiltTTS/docs/security-investigation-2026-10-21.md)
for fresh tests, confirmed findings, evidence, and the proposed fix order.
The register and package evidence below retain their historical dates; they do
not establish that a package contains the current working tree.

Updated 18 October 2026. This register distinguishes confirmed observations from
work that still needs investigation. The current build is not cleared for public
distribution. GPU remains included in the launch scope.

| ID | Priority / type | Observation and required result | Status |
| --- | --- | --- | --- |
| REL-01 | Blocker: publisher | No developer account/name reservation yet. Publisher completes verification and supplies exact MSIX identity from Partner Center. | Waiting on publisher; local test identity used meanwhile. |
| REL-02 | Blocker: redistribution | Candidate review still lists model/voice/dictionary provenance, libsndfile/codecs, Microsoft runtime DLLs, NVIDIA grants, and artwork rights. Close with evidence for the actual payload. | Open; see `thirdparty/PRONUNCIATION-CANDIDATE.md`. |
| REL-03 | Blocker: deployment | Portable app behavior does not prove installed MSIX behavior. Verify worker spawning, loopback, native bridge, dialogs, data virtualization, WebView2 and CPU/CUDA DLL loading under package identity. | Compatibility packaging implemented; installed testing pending. |
| REL-04 | Blocker: updates | No older-to-newer Store installation/update rehearsal. Preserve documents, WAVs, settings, positions, and migration recovery. | Open. |
| SEC-01 | High: native boundary | The original WebView integration lacked an origin/navigation allowlist. Both custom drop messages and ordinary pywebview dispatch now check the browser-provided message source; navigation is pinned to app pages and frames are blocked. | Implemented; regression and native startup/playback checks pass. Installed-MSIX verification remains. |
| SEC-02 | Medium: local resources | Host/UUID/path checks now have DENY framing, CSP frame-ancestors and same-origin resource headers. Session access protection and a complete cross-origin review remain. | Partially addressed; session-access work open. |
| SEC-03 | Medium: model trust | Download digest verification is conditional on upstream metadata; imported/bundled files need an explicit integrity/trust policy. Multi-file replacement should be recoverable. | Open. |
| SEC-04 | Medium: resource limits | File import reads the entire Markdown file and batch/settings inputs need a complete type/size/finiteness review. Add practical limits and usable errors. | Open. |
| SEC-05 | Required investigation | Python/native/GPU advisory review is incomplete. The prior frontend production audit found no known advisories; that is not clearance for the rest of the payload. | Open. |
| DATA-01 | High: concurrent launch | A per-library OS file lock now precedes Store/Jobs startup. Another process cannot enter job recovery for an active library; process exit releases the lock without deleting the library. | Implemented; competing-process/crash-exit tests and real startup rejection check pass. Second-launch window-focus UX remains a later refinement. |
| DATA-02 | High: upgrades/recovery | Databases use unversioned JSON rows (`user_version=0` in the inspected libraries). Add versioned migrations, consistent backups, validation, restore, and unknown-newer-format protection. | Open. |
| DATA-03 | Required investigation | Database, audio, caches, logs, and backups are unencrypted app-managed files. Resolve protection/retention against actual data and Store privacy requirements; do not claim encryption/secure deletion prematurely. | Open. |
| DATA-04 | Implemented boundary | The local MSIX probe must not select or migrate existing production/evaluation libraries. A separate allowlisted profile and independent override now provide this boundary. | Focused isolation tests pass; installed path verification pending. |
| PROD-01 | Release requirement | Production startup still needs its final title/identity/data-profile design. Current evaluation and compatibility modes remain explicitly labeled. | Open; no production switch made. |
| PROD-02 | Publisher requirement | PyInstaller bytecode and frontend assets remain inspectable. Prove selected proprietary-module compilation, audit duplicate sources/bytecode, and preserve third-party rights. | Open. |
| PROD-03 | Blocker: user information | Public privacy policy/support links, final app terms, system requirements, screenshots, ratings, and reviewer notes are not ready. | Open. |
| PROD-04 | Product decision | Pricing is undecided; publisher is considering a free first release. No ad SDK or payment/activation system is being introduced by the compatibility work. | Decision can follow technical feasibility. |

**Evidence from the preliminary review:** seven storage/server tests passed, three
local SQLite libraries passed quick checks with valid JSON, and the frontend
production advisory check reported zero known findings at that time. Existing
personal libraries were inspected read-only. These checks are limited in scope.

**Compatibility package 1.0.1.0:** `dist/msix-compatibility/Violilt-MsixCompatibility-1.0.1.0-x64.msix`.
MakeAppx 10.0.28000.2705 reported package creation success, with validation enabled.
The package contains CPU and NVIDIA assets and the isolated compatibility marker.
Archive inspection confirmed all 1,168 mapped payload entries and matched the
frozen executable's hash. Only the expected MSIX block map/content-type metadata
were added by MakeAppx. The version 1.0.0.0 experiment predates these security
changes and is superseded.

- Package size: 2,253,663,107 bytes (about 2.25 GB); uncompressed mapped payload:
  3,478,591,578 bytes.
- Package SHA-256: `580a81f5bc53c25a13298e4b6dca70ec5380099cb5c2a5a8b8ad32a36b703b8e`.
- Per-file inventory: `dist/msix-compatibility/inventory-1.0.1.0.json`.
- `tools/install_msix_test.ps1 -WhatIf` verified identity and the complete package
  hash successfully; installation was not attempted by that dry run.
- Installed MSIX startup/CPU/CUDA/data-path/update checks remain **not run**.
  The execution host does not have a Windows administrator token. The explicit
  unsigned-test workflow requires Administrator PowerShell for executable content;
  instructions are in [the packaging README](../packaging/msix/README.md).

Packaging validation must not be recorded as a passed installation, GPU runtime,
or update test. No certificates were trusted, security settings changed, or app
published by this work.

**Implementation checks, 18 October 2026:** the final full suite passed 148 tests.
Frontend type checking reported zero errors/warnings and the production frontend
build passed. The native startup probe passed with debugging disabled, exercising
the guarded bridge, Home, saved WAV playback, position recovery and replay. A real
`main()` preview launch also served the new security headers and rejected a second
process using its disposable library. The rebuilt executable audit passed with
2,331 frozen modules and no listed isolation violations. This still does not grant
redistribution clearance or prove installed CUDA inference.
