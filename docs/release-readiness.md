# Violilt release readiness

Continuation notes: [handoff](C:/Users/fireball/OneDrive/Desktop/LiltTTS/docs/HANDOFF.md).

Updated 21 October 2026. This combines the [release plan](ms-store-release.md), [security investigation](security-investigation-2026-10-21.md), and subsequent release review. The investigation remains historical evidence; this checklist tracks the work that follows it. Release scope: x64 Windows desktop MSIX, proprietary Violilt code, local English TTS, CPU and optional NVIDIA GPU support, Store-delivered updates. Pricing remains undecided; no ads or payments are being added.

## Working method

For every item: **trace → plan → implement/investigate → validate → record**. Trace the current code, dependency versions, artifact and existing evidence first. State the intended change and acceptance checks before editing. Retest the changed boundary and relevant real workflow. Record the result, remaining limits and exact build where applicable. A passing source test is not installed-package evidence. Preserve personal libraries and existing unrelated changes.

Status: **passed** means evidence exists for the stated scope; **confirmed issue** means reproduced or established by inspection; **open** means not yet verified; **publisher action** means an external account/product action is required. No public submission or publication is authorized by this checklist.

## Gate 1 — Distribution, ownership and privacy

| Item | Trace / plan / acceptance | Status |
| --- | --- | --- |
| Account and identity | No verified Partner Center account/name was supplied. Publisher creates/verifies the account, reserves Violilt, enables MFA/recovery and supplies exact package identity. | Publisher action |
| Dependency/code/data rights | Fresh package audit found no forbidden eSpeak/phonemizer modules/files. Matching notices/source archives were refreshed. Close exact model/voice/dictionary, LGPL/MPL replacement, libsndfile/codecs, Microsoft runtime and NVIDIA DLL grants. See `thirdparty/PRONUNCIATION-CANDIDATE.md`. | Partial evidence passed; redistribution clearance open |
| Proprietary packaging | App code is intended to remain private. Verify selected module compilation, inspect output for unintended source, and preserve third-party source/replacement rights. Local software cannot be made uninspectable. | Open |
| Privacy and telemetry | Source and version-specific runtime documentation traced in [privacy review](privacy-release-review.md). Next verify runtime settings/traffic and retention, preserve security protections, and prepare public/in-app disclosures and delete/export behavior. | Trace/plan recorded; implementation and disclosure open |
| Product/listing choices | x64 and CPU/NVIDIA scope are recorded. Confirm supported Windows/hardware from tests, price, markets, support contact, age rating, artwork/name rights and terms/notices. | Part publisher action |

Gate 1's unresolved distribution rights prohibit public release; reversible engineering and isolated test builds can proceed alongside the evidence review.

## Gate 2 — Application security and data recovery

| Item | Trace / plan / acceptance | Status |
| --- | --- | --- |
| S-01 dependencies | certifi is now 2026.10.19; pip bootstrap is hash-pinned to 26.2.2. Environment consistency, refreshed notices, 79 package/version advisory queries (zero findings) and patched certifi in the fresh payload verified. | Passed for updated environment/evaluation payload; native advisory audit open |
| S-02 native dispatch | Exact public method/arity contract, message-size/callback-ID bounds and registered-callback checks now precede generic dispatch. Native file objects retain their dedicated transport. Unit, native debug-off playback, and frozen valid-private-call rejection tests passed. | Implemented and passed for tested source/frozen build; installed test open |
| S-03 model trust | Independently fetched CPU/GPU/voice bytes are pinned in code. Downloads/imports, readiness, build payload and inference verify hashes. Invalid optional GPU content leaves CPU usable. | Implemented; focused and real CPU/CUDA generation checks passed |
| S-04 model replacement | Complete sets are staged and verified, previous files are journaled/backed up, interrupted transactions recover, and imports coordinate with worker release/generation. | Validation/replacement-failure/restart tests passed; installed update/power-loss rehearsal open |
| S-05 settings/data | Shared settings validation; schema v1 with pre-upgrade backup; newer schemas rejected; malformed preferences/JSON records retained for recovery with a UI notice. | Confirmed reproductions addressed and tests passed; full record-schema/restore UX and installed recovery rehearsal open |
| S-06 library import | Managed-entry allowlist, reparse rejection, source lock, bounded copy, free-space checks and before/after source snapshots. | Junction/concurrency/change/low-space regressions passed; older non-cooperating apps/installed scenarios still need validation |
| Resource limits | 2 MB Markdown, 32-file batches, 8 MB native messages; library import bounded at 100 GB / 100,000 entries with disk-space checks. | Bounds implemented/tested; broader disk-full/cancellation and performance checks open |
| Local access/runtime trust | Cross-origin browser reads failed. Targeted secret scan covered all 17 local Git revisions / 297 unique blobs with zero pattern findings. Session-bound audio access, GPU runtime/install ACLs and logs/privacy permissions need further review. | Partial checks passed; remaining scope open |

## Gate 3 — Exact release package

| Item | Trace / plan / acceptance | Status |
| --- | --- | --- |
| Production profile/build | Fresh CPU/GPU evaluation executable and unsigned compatibility MSIX 1.0.2.0 built with inventories/hashes; source unchanged across build/runtime checks. Production identity/data profile and proprietary compilation remain separate work. | Evaluation/compatibility build passed; production build open |
| Native payload | Inventory actual DLLs, versions, origins, hashes, advisories and redistribution grants; separate shipped artifacts from unused environment dependencies. | Open |
| Installed behavior | Frozen executable passed native boundary, settings, CPU/CUDA generation and reload tests. New MSIX passed MakeAppx validation, executable hash and installer `-WhatIf` checks. Installation requires Administrator PowerShell, unavailable in this session. | Portable checks passed; installed package identity remains untested |
| Clean machines | Standard user, CPU-only PC, compatible/incompatible NVIDIA drivers, supported Windows builds, offline first run, limited RAM/disk, non-English/space paths and high DPI. | Open |
| Accessibility | Verify keyboard/focus, screen-reader names/state, contrast and text scaling in core workflows before launch. | Open |
| Updates/recovery | Older-to-newer installed update, interrupted operation/recovery, documents/audio/settings/positions retained, reinstall/uninstall behavior understood. | Open |
| Certification/security scans | Run applicable WACK tests and malware checks on exact submission payload; investigate failures. WACK was not found in the checked standard installation location. | Open; WACK/install environment needed |

## Gate 4 — Submission and maintenance

Verify the Store policies effective at submission, manifest identity/capabilities and full-trust explanation, optional NVIDIA dependency notes, privacy/support URLs, screenshots/icons, accurate requirements and age rating. Reserve and retain the exact source revision, dependency inventory, package hashes and test evidence. Establish a support/security reporting route, account recovery, dependency-advisory review and a rehearsed patch process. Use a small initial audience/flight where available. Publisher reviews the concrete submission before publication.

## Work log

- **Trace completed:** current working tree, existing report, build/setup scripts, model paths, native dispatch and licensing notes inspected. No applicable repository/ancestor AGENTS.md was found. Existing unrelated changes are retained.
- **Plan:** first implement S-01/S-02 and model trust/rollback together, because validating after destructive replacement would retain the availability defect. Keep final-package/rights checks open until the rebuilt artifact exists.
- **Baseline evidence:** 150 backend tests and browser/native protection probes passed on the investigation baseline. Those results remain scoped to that baseline; affected checks will be repeated after changes.
- **Security implementation completed:** dependency/tooling pins, exact native dispatch, approved model hashes and transactional activation, preference/JSON recovery, library-copy boundaries and input limits. Each change followed a code trace and stated acceptance checks. Current tests: **170 passed**; frontend check/build passed.
- **Runtime validation completed:** normal native debug-off startup/playback passed. A separate frozen executable check rejected private dispatch, invalid callback identifiers and invalid settings; generated real CPU and CUDA audio; retained settings/documents after reload; and reported no page errors.
- **Package evidence completed:** 1,467 audited payload files / 2,334 frozen modules; zero forbidden-content findings; all model pins verified. Compatibility MSIX 1.0.2.0 contains 1,168 mapped files plus two standard MSIX metadata entries, with CPU/NVIDIA assets retained. Installer dry run verified the complete package hash; nothing was installed or published.
- **Privacy trace completed:** source network/log surfaces and version-specific ONNX/WebView2 documentation recorded; diagnostic controls, final policy and retention/deletion decisions remain open.
- **Next gates:** finish exact redistribution/runtime/privacy evidence and production configuration; use an administrator-capable test environment for installed CPU/GPU, update/recovery, clean-machine and certification checks. Account/name/MFA, publisher/support details and product choices require the publisher. These pending gates are not waived by passing unit tests.

Detailed evidence and artifact links: [implementation results](release-hardening-2026-10-21.md).
