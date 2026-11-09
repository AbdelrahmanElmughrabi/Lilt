# Violilt: Microsoft Store release plan

Current combined checklist and implementation status: [release readiness](release-readiness.md).
The initial assumptions and dated evidence below are retained for context.

Prepared 18 October 2026. Status: implementation started with the local CPU/GPU MSIX compatibility build; release gates below remain open until supported by evidence. Track observations in [the findings register](ms-store-findings.md).

The target is a Microsoft Store MSIX release of Violilt with local English narration, both CPU and NVIDIA GPU processing, proprietary Violilt application code, and Store-delivered updates. GPU remains part of version 1. This plan preserves the existing reading, recording, resume, playback, export, and appearance features.

**Release sequence:** establish product identity and resolve distribution rights; prove MSIX compatibility early; harden security and data handling; finalize the production build; test installation and real updates; finish the listing; certify and publish.

## Starting point and decisions

The current branch is `pronunciation-replacement`. It produces a portable pronunciation evaluation build through `build.ps1` and `packaging/Violilt.spec`, not a production Store package. `main.py` currently requires the candidate marker and selects the evaluation data profile. There is no Store manifest or app updater in the reviewed release setup.

The preliminary review found useful protections: sanitized Markdown, strict script policy, a loopback-only server, Host/path checks, parameterized SQL, and non-pickle voice loading. Seven storage/server tests passed. The frontend production dependency audit reported no known vulnerabilities at the time checked. Three local databases passed SQLite quick checks and contained valid JSON. These results do not constitute a complete security audit, a native dependency audit, or installed-MSIX validation.

| Decision | Plan / remaining choice |
| --- | --- |
| Distribution | Microsoft Store MSIX; preserve package identity across updates. |
| Processing | Ship CPU and NVIDIA GPU support. Machines without compatible NVIDIA hardware retain CPU support. |
| GPU failure behavior | Auto mode may choose CPU and explain why; an explicit GPU request must report failure rather than silently switch devices. |
| Architecture | x64 first. ARM64/x86 support requires separate dependency and hardware validation before being advertised. |
| Windows versions | Set minimum build from actual Python/native/WebView2 support and clean-machine testing. Validate every advertised Windows 10/11 target; do not infer support from the development PC. |
| Models | Bundle the approved CPU model, GPU model, and voices for offline generation after installation and prerequisite setup. |
| GPU delivery | First prove one MSIX containing the CPU app and the required GPU runtime/model. Optimize size without removing GPU. A separate Store-managed optional package is a contingency requiring its own deployment/update proof. |
| Code ownership | Keep Violilt-owned source private; retain third-party notices/source and applicable replacement rights. |
| Code protection | Prove compilation of selected proprietary modules with Cython, retaining PyInstaller as the initial bundler. No promise of unextractable local software. |
| Pricing | Undecided; publisher is considering a free first release. No ads are being added during release preparation. Choose pricing, markets, and any trial before completing the submission. No custom subscription/account service is assumed. |
| Telemetry | Keep the current absence of app analytics unless a separate product decision changes it. Store diagnostics and WebView2 behavior must be described accurately. |

## 1. Establish ownership, identity, and release scope

**Owner:** publisher for account/business choices; engineering for the release specification.

- [ ] Confirm the publisher's legal identity and the appropriate Individual/Company developer account type. Secure the account with MFA and recovery access; use only the roles needed for releases.
- [ ] Create or verify Partner Center access, complete verification, and reserve the desired app name. Name availability is unverified.
- [ ] Record the exact Package Identity Name, Publisher value, publisher display name, and product identifiers from Partner Center. Do not invent manifest identity values.
- [ ] Confirm CPU + NVIDIA GPU scope, supported architecture/Windows targets, interface language, narration language, price/trial, launch markets, and support contact.
- [ ] If paid, complete the required tax/payout setup and verify the chosen purchase/trial experience. Add in-app licensing only if the selected business model needs it; keep offline behavior explicit.
- [ ] Keep production, developer, and pronunciation evaluation identities/data profiles distinct. Retain the preserved baseline and existing libraries while implementation proceeds.

**Deliverable:** release specification, publisher/identity record, and a decision log with owners for unresolved items. Identity documents and payout details stay in Microsoft's account flow, outside the repository.

**Done when:** the product identity is available and immutable identity fields can be used in a real package; commercial choices are assigned and resolved before submission. Follow Microsoft's current [account onboarding instructions](https://learn.microsoft.com/en-us/windows/apps/publish/partner-center/open-a-developer-account?tabs=individual).

## 2. Resolve distribution rights and privacy requirements

**Owner:** engineering gathers evidence; publisher obtains qualified licensing/privacy review where an unresolved question requires it.

- [ ] Close each open gate in [the candidate distribution review](../thirdparty/PRONUNCIATION-CANDIDATE.md): exact Kokoro ONNX conversion, the complete voice artifact, dictionaries and modification notices, libsndfile build/codecs and corresponding source, native/vendored contents, VC/UCRT/API-set redistribution, NVIDIA components, and app/icon rights.
- [ ] Inventory the exact CPU and GPU files that will ship. Record version, upstream origin, SHA-256, license, redistribution basis, required notices/source, and any restrictions for each relevant component. A runtime probe marker is not redistribution evidence.
- [ ] Match each bundled NVIDIA DLL to the grant for its actual version. Review both ONNX Runtime variants and model assets. Verify that no driver installer is bundled; identify the compatible user-installed NVIDIA driver requirements.
- [ ] Complete the third-party notice/source collection for the actual release payload. Verify source links/archives and license text, rather than relying only on package metadata or the existing isolation audit.
- [ ] Ensure MSIX and code protection preserve applicable LGPL/MPL rights, including required replacement/relinking or debugging arrangements. Test the selected arrangement on the installed package. Do not encrypt or compile third-party components in a way that defeats those rights.
- [ ] Prepare the proprietary application license/EULA with the necessary third-party exceptions. Confirm rights to branding, example documents, screenshots, and sample audio.
- [ ] Publish a privacy policy for this Win32 app. Cover imported documents, original file paths, database/settings, audio, caches, logs, backups, model downloads, WebView2 diagnostics, deletion, support submissions, and uninstall behavior. Local processing is not an exemption from the Store's privacy-policy requirement.
- [ ] Resolve storage protection against the actual information processed and Store policy 10.5. Document and test protection of the database, audio, caches, and backups together. If encryption is needed, use maintained cryptography and Windows-backed key protection; define recovery/backup portability before selecting the implementation. Do not claim encryption or secure erasure without evidence.

**Deliverable:** closed distribution checklist with evidence, final notices/covered source, privacy policy, and app license. Unknown redistribution rights are release blockers.

**Done when:** every shipped artifact has an established distribution basis, user rights remain exercisable in the selected package, and data-handling claims match behavior. Microsoft requires privacy policies for Win32/Desktop Bridge products and sets personal-information security requirements in [Store policy 10.5](https://learn.microsoft.com/en-us/windows/apps/publish/store-policies#105-personal-information).

## 3. Prove the MSIX deployment approach before major release changes

**Owner:** engineering. Use disposable libraries and clearly identified test packages.

- [ ] Add a minimal x64 package manifest and command-line packaging script using Windows SDK tools. Populate identity from Partner Center and use a desktop/full-trust configuration appropriate to the existing application.
- [ ] Install the existing app payload as a test MSIX and verify pywebview/WebView2 startup, the native bridge and file drop transport, worker spawning/freeze support, local HTTP/audio playback, native dialogs, and GPU DLL loading.
- [ ] Confirm the packaged process's actual networking behavior. Do not require customers to enable developer mode, change firewall settings, or run a loopback-exemption command as the normal installation flow.
- [ ] Prove CPU and NVIDIA ONNX Runtime separation inside MSIX, including no-NVIDIA machines. Ensure CPU startup does not require CUDA DLLs and GPU loading cannot select the wrong runtime.
- [ ] Identify all installation-directory writes. Keep installed application/model/runtime files read-only; place mutable databases, caches, downloads, WebView data, and generated audio in deliberate per-user locations.
- [ ] Test MSIX AppData virtualization and legacy-library discovery on each Windows target. Choose and document the production data location and uninstall behavior from measured behavior, not a guessed path.
- [ ] Prove the WebView2 prerequisite strategy for the Store route. Prefer the serviced Evergreen runtime; test a machine where it is missing. App Installer dependency features must not be assumed to behave identically for Store deployment.
- [ ] Verify native prerequisites such as VC runtimes and the .NET components used by pythonnet on clean systems. Choose a supported, licensed deployment path for every prerequisite.
- [ ] Measure the real package/install footprint with GPU included. Remove unneeded development artifacts and redundant files only after dependency analysis. Do not assume the older baseline size is the current candidate's size.

**Deliverable:** installable test MSIX and a compatibility report naming any architecture changes needed.

**Done when:** the complete CPU/GPU app works under package identity without privilege workarounds and its writable data/prerequisites are understood. Use Microsoft's [manual MSIX packaging guide](https://learn.microsoft.com/en-us/windows/msix/desktop/desktop-to-uwp-manual-conversion), [WebView2 distribution guidance](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution), and [AppData virtualization documentation](https://learn.microsoft.com/en-us/windows/msix/desktop/flexible-virtualization).

## 4. Harden the application boundaries

**Owner:** engineering. Changes belong primarily in `main.py`, `backend/desktop.py`, `backend/server.py`, `backend/bridge.py`, and `backend/models.py`.

- [ ] Write a short threat model covering malicious imported Markdown, hostile browser content contacting loopback, unexpected WebView navigation/messages, malformed models, and package tampering. Treat hostile software already running as the same Windows user as a limit of local protection, not something source obfuscation solves.
- [ ] Restrict top-level/frame navigation to the intended application content. Validate message source/origin before native dispatch, including the custom file-drop handler; apply checks before the original pywebview handler receives ordinary API messages as well.
- [ ] Introduce per-launch access protection for local UI/media where appropriate, preserve strict Host validation, reject unintended cross-site browser access, and prevent external framing. Keep application commands off HTTP; the current HTTP server serves files/audio, not a REST command API.
- [ ] Preserve strict script restrictions, sanitizer allowlists, disabled remote Markdown images, and safe JSON serialization. Add framing policy through HTTP headers where required; a meta CSP cannot implement every directive.
- [ ] Validate native bridge input types, identifiers, settings, numeric finiteness/ranges, and path containment. Verify media/export/delete handling cannot escape managed paths, including relevant Windows reparse-point cases.
- [ ] Define practical document/file-count/model size limits and disk-space checks. Reject oversized inputs with usable messages; keep cancellation and the UI responsive.
- [ ] Verify trusted model hashes for bundled/downloaded assets. Downloads must not skip verification when upstream metadata omits a digest. Define a deliberate validation/trust policy for user-imported models; publish asset changes through a reviewed release process.
- [ ] Make multi-file model updates recoverable and avoid exposing mixed/incomplete model sets. Preserve a working set if a download/import fails.
- [ ] Audit Python, frontend, native, and GPU dependencies against current advisories. Record actual packaged versions, triage findings for reachability, and resolve release-blocking findings. Include WebView2/pywebview bridge compatibility in dependency updates.
- [ ] Remove release-only exposure to preview/debug tools and remote debugging. Review environment/runtime overrides for production use; never load executable plugins from an untrusted download or the current working directory.
- [ ] Review logs, exception messages, support exports, and package contents for document text, full sensitive paths, secrets, or developer-machine details.

**Deliverable:** security changes, meaningful regression tests, dependency inventory/SBOM, and a findings register with severity, evidence, and resolution.

**Done when:** no unresolved release-blocking security findings remain and targeted tests cover the newly enforced boundaries. Microsoft's [WebView2 security guidance](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/security) specifically addresses origin/message validation and navigation restrictions.

## 5. Make databases and recordings safe across crashes and upgrades

**Owner:** engineering. Retain SQLite; a hosted database is not needed for this product.

- [ ] Add an explicit data/schema version, ordered transactional migrations, and compatibility checks. Refuse an unknown newer format without overwriting it; do not try to downgrade it automatically.
- [ ] Create a consistent database backup before migration using SQLite's backup mechanism. Keep required recordings/manifests coherent with library backups; a database-only backup is not a complete recording-library backup.
- [ ] Provide a documented restore path and integrity checks. Handle malformed records/corruption with recovery choices and useful errors rather than silently replacing the library with an empty one.
- [ ] Add a per-production-library single-instance guard before startup job recovery. Today startup marks nonterminal jobs interrupted; another instance must not disturb an active reading. Focus the existing instance or exit with a clear message.
- [ ] Audit concurrency and crash consistency for job state, section WAVs, manifests, final WAV assembly, cache entries, and database commits. Test forced termination and insufficient disk space.
- [ ] Design a deliberate import/migration path from existing libraries. Keep the pronunciation evaluation library separate unless the user explicitly chooses to import it; never overwrite a populated production library.
- [ ] Validate JSON record shape as well as JSON syntax. Define reasonable library-size behavior so loading every saved job/document does not make startup unusable.
- [ ] Document deletion semantics across database entries, saved audio, reusable speech cache, backups, logs, and original files. Keep the user's original Markdown and exported audio outside destructive library cleanup.
- [ ] Implement the storage-protection decision from stage 2, including key loss, restore on another machine, encrypted backups if applicable, and user-facing recovery instructions.

**Deliverable:** migration/backup/restore implementation, compatibility policy, data-location decision, and lifecycle tests.

**Done when:** upgrade and recovery tests preserve documents, recordings, settings, positions, and recoverable work; opening a second app instance cannot mutate the first instance's jobs. Uninstall/reinstall behavior is verified for the final package.

## 6. Produce the proprietary production build

**Owner:** engineering; publisher reviews the realistic protection level.

- [ ] Replace evaluation-only startup behavior with explicit production/development profiles, a production title/AppUserModelID, and stable data selection. Preserve the isolated evaluation launcher/build while needed.
- [ ] Centralize the release version and expose it with support/privacy/third-party information in an About area. Keep executable metadata, frontend identification, manifest, notices, and release notes aligned.
- [ ] Prototype Cython compilation of selected Violilt-owned modules. Validate multiprocessing, native bridge discovery, packaging, error reporting, CPU/GPU inference, and performance before adopting it broadly.
- [ ] Audit the actual payload to ensure protected modules are not also shipped as readable `.py` or recoverable `.pyc` copies. Keep private symbols/build sources outside the customer package, without removing required third-party materials.
- [ ] Minify the production frontend and omit source maps from the public payload. Accept that client-side UI code, assets, public models, and native machine code can still be inspected or reverse engineered.
- [ ] Keep repositories/build credentials private and scan the release payload for accidental secrets, local databases, personal recordings, test tools, caches, and unrelated artifacts.
- [ ] Lock dependencies and build inputs; verify downloaded inputs and record hashes for models, native binaries, and source materials. Build from a clean checkout/environment, not the accumulated development folders.
- [ ] Extend the existing executable/package audit for the chosen compiler and production profile. Preserve license auditing as a separate check: isolation success alone does not grant distribution rights.

**Deliverable:** reproducible documented build procedure, protected production payload, versioned notices, and payload audit evidence. Reproducibility here means reconstructable inputs/process; byte-identical output is a separate claim requiring proof.

**Done when:** the publisher accepts the practical protection level, release functionality passes, and the production payload contains only intended artifacts. PyInstaller documents the [bytecode exposure and Cython option](https://pyinstaller.org/en/stable/operating-mode.html#hiding-the-source-code); neither packaging nor compilation guarantees secrecy on a customer's machine.

## 7. Finalize MSIX packaging and update delivery

**Owner:** engineering.

- [ ] Finalize `packaging/msix/` assets/manifest and a versioned `tools/build_msix.ps1` (proposed paths), separate from the existing evaluation output. Include the approved CPU/GPU payload, models, notices, and covered source.
- [ ] Use the exact Store identity, x64 architecture, validated minimum Windows build, correct executable/visual assets, and only necessary capabilities. Explain the desktop/full-trust capability in certification notes. Do not add administrator elevation or broad capabilities without a real need.
- [ ] Produce correctly sized/scaled Start/Store assets and verify light/dark/contrast appearance. Add file associations only if they are deliberately supported and tested.
- [ ] Finalize the tested WebView2 and native-prerequisite handling. Provide actionable missing-runtime/unsupported-driver errors, with CPU available when GPU hardware/driver requirements are unmet.
- [ ] Validate the package manifest and payload using Windows SDK tooling. Use an appropriate test signature for sideload testing; keep signing material outside the repository. Microsoft signs accepted Store MSIX packages, so a purchased public certificate is not required solely for Store submission.
- [ ] Establish monotonically increasing Store package versions, for example `1.0.0.0` then `1.0.1.0`, with the fourth component reserved as required by current Store rules. Keep identity stable.
- [ ] Use Store update delivery rather than a custom self-updater that rewrites installed files. Document that update timing depends on Store/device conditions and app use.
- [ ] Test a real older-to-newer package upgrade, including a database migration and a changed model/pronunciation identity. Saved WAVs must remain playable; incompatible unfinished generation must explain what can be resumed or regenerated.
- [ ] Prepare a forward-fix/hotfix procedure with a higher version number. Stopping a rollout does not itself restore older binaries or reverse a data migration.

**Deliverable:** upload-ready MSIX plus version/hash manifest, dependency/SBOM records, license materials, test signature instructions, and upgrade evidence.

**Done when:** installation and upgrade work as a standard user with both processing paths intact. Microsoft documents [signing, identity, and version rules](https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msix/app-package-requirements) and [Store update behavior by packaging route](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/publish-first-app#step-5-set-up-auto-update).

## 8. Validate the installed release candidate

**Owner:** engineering plus independent testers/listening review. Test the installed MSIX, not only a source or portable build.

| Area | Required coverage / pass condition |
| --- | --- |
| Clean installation | Each advertised Windows target; standard user; no Python/Node/CUDA toolkit; missing/present WebView2; no unexplained prerequisite failure. |
| Hardware | CPU-only system; a supported NVIDIA system; incompatible/missing driver; low memory; explicit GPU error and Auto device behavior. Record actual hardware/driver versions. |
| Core workflows | Import/paste/edit, drop multiple Markdown files, voice preview, generation, early playback, seeking, cancel/resume, WAV export, restart/position recovery, Explorer actions, and deletions. |
| Offline use | With prerequisites and bundled assets installed, narration/playback/export work without network access. Missing assets/download failure produce honest guidance. |
| Pronunciation/audio | Listening review of representative English, numbers/currency, punctuation/code, symbols, unfamiliar words, and all advertised voice choices. Exported audio matches the streamed result and pause settings. |
| Lifecycle/data | Forced termination, active generation during shutdown/update, disk full, migration failure/restore, old/new database compatibility, second launch, uninstall/reinstall, and legacy-library import. |
| Untrusted input | Malicious HTML/Markdown, remote resources, oversized files, malformed bridge messages/settings/models, cross-origin/framing attempts, and relevant path/reparse-point cases are rejected or safely handled. |
| UI/accessibility | Keyboard-only operation, screen-reader labels, visible focus, high contrast, scaling/DPI, reduced motion, smallest supported window, long filenames, and non-ASCII Windows usernames/paths. |
| Update rehearsal | Install version A, create a representative library, update to B through the real Store test route when available, and verify records/audio/settings/positions. Local sideload upgrades are an earlier check, not the only evidence. |
| Certification/performance | Current Windows App Certification Kit, package validation, reasonable startup/idle behavior, responsive UI, bounded caching, no leftover workers after exit, and measured CPU/GPU disk/memory requirements. |

Reuse existing checks where they cover real behavior: the unittest suite, `tools/smoke_test.py`, `tools/native-startup-check.py`, pronunciation/symbol/punctuation integration tools, model-memory checks, Home/desktop/drop/context-menu flows, and package audits. Update their setup for the final build. Keep intentionally enabled debugging confined to test builds/runs.

**Deliverable:** release-candidate report with package hash, test machine/OS/runtime/driver versions, results, defects, listening approval, and certification-kit output. [Windows App Certification Kit guidance](https://learn.microsoft.com/en-us/windows/uwp/debug-test-perf/windows-app-certification-kit).

**Done when:** no blocker/high-severity defects remain, all advertised platforms/features have evidence, and both CPU and NVIDIA paths pass. A certification-kit pass is preparation, not Microsoft's certification decision.

## 9. Complete the listing and certification submission

**Owner:** engineering prepares assets/text/evidence; publisher supplies business details and reviews the final submission.

- [ ] Prepare an accurate description and feature list: local English Markdown narration, bundled voices, CPU/NVIDIA requirements, WAV export, offline prerequisites, known pronunciation limitations, and measured storage requirements. Distinguish interface language from supported narration language.
- [ ] Capture at least four useful screenshots from the final release with synthetic documents: Home/library, reading/editing, generation/playback, and settings including acceleration. Prepare required logos and any optional promotional art at current Partner Center specifications.
- [ ] Make privacy/support links publicly accessible without login; include them in the app where appropriate. Provide support email/contact, copyright/branding details, and final license terms.
- [ ] Complete pricing, availability/markets, age-rating questionnaire, category, system requirements, product declarations, and any applicable AI/audio disclosures based on the actual features and current form/policy. Do not guess ratings or claim voice cloning.
- [ ] Write reviewer instructions covering launch, importing the bundled sample, generating/exporting audio, offline behavior, model/prerequisite setup, local loopback use, full-trust need, and optional GPU requirements. Make the CPU flow fully testable on reviewer hardware.
- [ ] Upload the approved package, resolve Partner Center validation findings, and verify that the identity/version match the tested artifact.
- [ ] Use a Store flight/private audience where available to rehearse acquisition and updates before general availability. Hold automatic public publishing until the final listing/package/business review is complete.
- [ ] Submit for certification and address actual feedback against the same release evidence. Record what changed and repeat affected checks if the package changes.

**Deliverable:** complete reviewed submission and certification result. Microsoft's [submission checklist](https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msix/create-app-submission) defines the current fields; verify them again at submission time.

**Done when:** certification is accepted and the exact product/package intended for launch is ready to publish. A failed or pending submission is not a completed release.

## 10. Publish and maintain the release

**Owner:** publisher controls public launch; engineering owns technical verification and fixes.

- [ ] Publish the approved release and verify the public listing, price/markets, install button, support/privacy links, launch, and both processing paths through a customer-style acquisition.
- [ ] Archive the release tag/commit, build inputs, package hashes, dependency/license inventory, notices/source, test reports, listing assets/text, and reviewer notes in controlled storage. Keep code and credentials private.
- [ ] Review Partner Center crash/certification signals, support reports, reviews, and dependency advisories. Establish a routine maintenance cadence and an urgent path for security/data-loss issues; no additional app telemetry is assumed.
- [ ] For every update: bump the version, review dependencies/licenses, back up/migrate data safely, run affected regression and upgrade tests, validate the installed package, update release/privacy notes when behavior changes, submit, and verify delivery.
- [ ] Define incident handling: triage, reproduce on the affected release, stop an available rollout/acquisition when appropriate, protect existing libraries, and publish a tested higher-version repair. Communicate material issues through the chosen support channels.

**Deliverable:** live Store listing, verified acquisition, and a repeatable release/maintenance runbook.

**Done when:** a customer can acquire and use the app and a subsequent certified version can reach an existing installation without losing the library.

## Dependencies, milestones, and release gates

| Milestone | Work that can proceed together | Required result |
| --- | --- | --- |
| A: identity and feasibility | Account/name setup, distribution evidence, MSIX CPU/GPU spike | Real identity; package feasibility; no unknown architecture blocker. |
| B: production readiness | Security, data lifecycle, code compilation, production profile; rights/privacy review continues | Hardened production build; safe libraries; protected proprietary modules; closed distribution/privacy gates. |
| C: release candidate | Final packaging, installed-system tests, real update rehearsal, screenshots/listing | Tested artifact with CPU/GPU, certification-kit evidence, complete business/listing fields. |
| D: launch and servicing | Certification responses, held launch review, public acquisition, first update verification | Published product and demonstrated servicing path. |

Engineering preparation can proceed while the publisher completes account/business work. External release must wait for distribution clearance, privacy/data requirements, and the installed-package/update gates. Dates should be estimated after the MSIX spike and licensing inventory: account verification, third-party evidence, hardware availability, and certification are external timing dependencies.

**Final launch checklist**

- [ ] Publisher/account verified; exact identity and app name established; price/markets decided.
- [ ] Every CPU/GPU/model/native artifact cleared for distribution, with required notices/source and license rights preserved.
- [ ] No unresolved release-blocking security findings; model verification and native/WebView boundaries tested.
- [ ] Production/evaluation separation correct; single-instance handling, migrations, backup/restore, and storage protection complete.
- [ ] Proprietary-code protection accepted with realistic limits; no private data, secrets, or unintended source in the payload.
- [ ] Installed MSIX works on all advertised Windows/hardware targets, including CPU-only and NVIDIA machines.
- [ ] Missing prerequisites/driver errors and offline behavior are usable and accurately documented.
- [ ] Older-to-newer Store update tested; audio, documents, settings, positions, and migration recovery verified.
- [ ] Privacy policy, support, app terms, screenshots, age ratings, descriptions, and reviewer instructions complete.
- [ ] Package/certification checks pass; exact package hash approved for launch; hotfix procedure and support ownership ready.

**First implementation batch:** record the product decisions and artifact inventory, add the disposable MSIX CPU/GPU compatibility spike, and create the security/data findings register. Use the spike results to finalize data locations, GPU deployment, and prerequisites before making broad production changes.
