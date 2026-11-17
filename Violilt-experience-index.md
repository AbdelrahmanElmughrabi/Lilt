# Experience extract: Violilt / LiltTTS

**Violilt is an AI-assisted Windows desktop text-to-speech project that progressed from a local reading prototype to a privately tested installer and Store-release preparation.** Its strongest documented themes are local ML inference integration, desktop product engineering, failure and recovery testing, performance investigation, and coordinating AI-assisted implementation and review.

The record supports saying that you directed and evaluated substantial work on the project. It does **not** establish which individual lines you wrote yourself or that every investigation was performed personally. The wording below therefore distinguishes your direct statements from what the code and saved reports show.

## Scope and evidence

This extract covers **one project and its related branches**:

- **LiltTTS** is the repository and project name. The product was called **Lilt** and was later rebranded **Violilt**. Older records also use **Folio** for an earlier identity.
- `main`, `pronunciation-replacement`, `pronunciation-fallback`, and `reading-diagnostics` are development histories or candidates within that project. They should not be counted as separate products.
- The repository references an earlier `TTS` path. That directory was not accessible during this inspection, so its relationship and contents were not independently established. It is not treated as a second project here.
- A publisher website is referenced in release notes, but its source and deployment were not examined and are not included as a separate project.

Sources inspected read-only:

| Source type | What it can establish |
|---|---|
| [Current repository README](C:/Users/fireball/OneDrive/Desktop/LiltTTS/README.md), selected [backend source](C:/Users/fireball/OneDrive/Desktop/LiltTTS/backend/speech.py), frontend configuration, tests and tools | Current checked-out implementation and documented workflows. Source presence alone does not establish who wrote each part or that a test was run. |
| Git branches, commit subjects, dates and remote | Visible development sequence from 8–25 October 2026. Commits carry your name, but that does not by itself distinguish manual authorship from AI-assisted work. The repository remote is [github.com/AbdelrahmanElmughrabi/Lilt](https://github.com/AbdelrahmanElmughrabi/Lilt); its public availability was not checked. |
| [Release source status](C:/Users/fireball/OneDrive/Desktop/LiltTTS/docs/release-source-status.md), [redistribution status](C:/Users/fireball/OneDrive/Desktop/LiltTTS/docs/release-redistribution-status.md), [28 October MSIX campaign](C:/Users/fireball/OneDrive/Desktop/LiltTTS/docs/msix-production-campaign.md), and selected ignored `.tmp` records | Saved, largely assistant-produced results, reviews, plans and handoffs. These report test scope and outcomes; they are not all independent primary observations. |
| [Original performance JSON](C:/Users/fireball/OneDrive/Desktop/LiltTTS/artifacts/performance-integration.json) and [CPU-only result](C:/Users/fireball/OneDrive/Desktop/LiltTTS/artifacts/cpu-only.json) | Recorded measurements and configurations for particular runs. |
| Selected [Obsidian project notes](<C:/Users/fireball/OneDrive/Desktop/Obsidian Vaults/LiltTTS/LiltTTS/00 Start Here.md>), including pronunciation diagnoses and candidate results | Historical decisions, experiments, reported outcomes and planned work. Several notes explicitly supersede earlier statements. |
| The recent **“Continue Violilt release coordination,” “Continue Violilt Store launch readiness,”** and **“Close Violilt R04 redistribution requirements”** chats | Your direct reports, requests and approvals, plus assistant responses. These are accessible through Codex chat history; I inspected selected turns, not every earlier conversation. |

Ignored artifacts and the Obsidian archive were accessible, and I inspected selected records rather than exhaustively reviewing every log, audio sample, historical build or conversation. I did not rerun experiments, listen to samples, inspect personal libraries, change files, or independently verify the current Store or website state.

## Identity, purpose and contribution

The documented goal was a **local English reading application**: import or paste text, convert it into spoken audio without a paid TTS API, and begin listening during longer generation. The original notes clarify that this was intended to read supplied text, not generate podcast scripts or summaries. The later application also supports TXT and PDF import. [Product decisions](<C:/Users/fireball/OneDrive/Desktop/Obsidian Vaults/LiltTTS/LiltTTS/01 Product and Decisions.md>); [release source status](C:/Users/fireball/OneDrive/Desktop/LiltTTS/docs/release-source-status.md).

**Context:** the records describe you as the publisher and show a desired option for commercial, closed-source distribution. They do not establish an employment, academic, internship or formal research context. Treat it as a **personal product project**, subject to your confirmation if a different context matters.

**Dates:** the available Git history begins on **8 October 2026**, and the latest examined release planning is dated **28 October 2026**. That is a documented activity window, not proof of the project’s start date or a basis for calculating years of experience.

### Your role and working method

Your direct chat statements and the saved records support the following:

- You set the product direction: local narration, desktop usability, support for long readings, and a possible future commercial release.
- You reported concrete reading-quality and application issues, approved specific investigation and implementation work, requested plans and verification, and made decisions about scope and continuation.
- You coordinated work through multiple Codex chats, including focused implementation and separate reviews. You explicitly discussed **checking AI-generated code**, and asked how to describe the testing process.
- You reported that the classic EXE worked well and marked other-PC testing complete. The records call this **publisher-reported acceptance**, not an independent hardware certification.
- You explored Microsoft Store submission, update behavior, identity, licensing and release readiness; those were still being worked through in the latest inspected checkpoint.

The project code, tests, commits and assistant-generated reports show substantial implementation and validation activity under your direction. They do **not** reliably identify which changes you personally coded, which you reviewed line by line, or which tests you personally executed. A credible application description can say **“built with AI assistance”** or **“directed development and validation”**; stronger individual authorship verbs should be matched to what you personally did.

## System flow and engineering work

The current checked-out `pronunciation-replacement` branch contains a Windows desktop app built with **Python, pywebview/WebView2, Svelte, TypeScript and Vite**. Its documented flow is:

1. A reader imports Markdown, TXT or PDF, or pastes text into an editable working copy.
2. Python extracts and prepares speech text, preserving the original document and showing a separate spoken preview. Rules handle Markdown structure, pauses, selected symbols, punctuation and numeric formats.
3. A background process uses **Misaki** for English pronunciation and **Kokoro-ONNX / ONNX Runtime** for local speech synthesis. The current branch spells some unfamiliar words and surfaces warnings; it is not the separate neural-fallback experiment described below.
4. The worker publishes audio in sections, permitting playback while later sections generate. Completed sections can be reused through a bounded cache, and a final WAV is assembled incrementally.
5. **SQLite and local files** retain library entries, settings, job snapshots, recordings and listening positions. A partially generated recording can continue when its saved identity and inputs remain compatible.

The design handles state beyond the visible playback interface: a persistent worker owns inference; commands and events coordinate work; cancellation takes effect after the current section; section files are published atomically; cache keys and continuation checks include model and pronunciation identity. These choices reduce the chance of combining incompatible audio after an engine or asset change. [Architecture notes](<C:/Users/fireball/OneDrive/Desktop/Obsidian Vaults/LiltTTS/LiltTTS/03 Architecture and Data Flow.md>); [speech worker](C:/Users/fireball/OneDrive/Desktop/LiltTTS/backend/speech.py); [pronunciation identity](C:/Users/fireball/OneDrive/Desktop/LiltTTS/backend/pronunciation.py).

Other documented work includes:

- **CPU and optional NVIDIA acceleration:** ONNX Runtime configurations, an isolated GPU runtime, real synthesis checks, hardware-specific speed recommendations and controls for worker resources. Requested unavailable GPU execution is intended to fail visibly rather than silently change backend.
- **Desktop security and privacy:** a restricted local server and pywebview bridge, a strict content security policy, sanitized Markdown preview, model/runtime integrity checks, and bounded, content-minimized local diagnostics. The app has no publisher analytics according to the current README; WebView2 has its own diagnostic behavior.
- **Reliability:** ordered saves, recovery and continuation, explicit handling of optional cache failures, and protection against stale pending updates recreating removed recordings.
- **Product and accessibility:** onboarding, voice setup, themes, keyboard focus, accessible controls, generation states, playback and small-window UI checks. The records keep screen-reader, scaling and final installed-package validation separate from browser fixtures.
- **Packaging:** PyInstaller builds, a private per-user Inno Setup installer, package inventories and hashes, third-party notices and source-delivery work, and a separate compatibility MSIX path.

The available evidence shows **integration and use of pretrained models**, plus an experiment exporting existing pronunciation models to ONNX. It does not establish training or fine-tuning a TTS model, building a training dataset, or operating a hosted ML service.

## Experiments, findings and validation

### Pronunciation: successful generation did not prove good speech

A 12 October replacement candidate used Misaki without the prior eSpeak route to explore a distribution-compatible offline pronunciation path. Its report records **16 finite 24 kHz baseline/candidate samples** across CPU/GPU and content categories, alongside automated and packaged checks. The report explicitly says valid audio and coverage did not establish naturalness; listening and distribution review remained pending. [Candidate results](<C:/Users/fireball/OneDrive/Desktop/Obsidian Vaults/LiltTTS/LiltTTS/21 Pronunciation Replacement Candidate Results.md>).

A later user-reported problem exposed why that distinction mattered. The words **“nondeterministic”** and **“subtrees”** were being spelled out. A 15 October trace across **14 isolated US/UK cases** located the behavior before synthesis: missing dictionary entries reached a conservative letter-spelling fallback. The trace did not run ONNX inference or prove anything about all possible acoustic-model errors. [Diagnosis](<C:/Users/fireball/OneDrive/Desktop/Obsidian Vaults/LiltTTS/LiltTTS/32 Unknown Word Pronunciation Diagnosis.md>).

A **separate `pronunciation-fallback` branch** then evaluated constrained word composition and small US/UK BART grapheme-to-phoneme models exported to ONNX. Its saved report states:

- **30/30 reference token sequences** matched between exported and original local models; this is export parity, not pronunciation accuracy.
- On one **165-section document**, sections needing a spelling warning fell from **30 to 8 for US** and **31 to 8 for UK**. This measures fallback usage on that document, not correctness or generalization.
- **143 Python tests** passed in that candidate’s recorded run. Listening review and wider model/data provenance and distribution review remained open.

The inspected current release branch does **not** contain that fallback commit, and its pronunciation source still identifies the v4 spelling policy. The fallback is meaningful experimental work, but it should not be described as a feature of the current release candidate without further integration evidence. [Fallback results](<C:/Users/fireball/OneDrive/Desktop/Obsidian Vaults/LiltTTS/LiltTTS/34 Unknown Word Fallback Implementation Results.md>).

### Performance: measured under specific conditions

An 8 October integration record on the documented **i7-11800H / RTX 3060 Laptop GPU** reports an approximately **89.33-second** recording generated in **8.09 seconds**, with first audio at **2.41 seconds**, using CUDA and no cache hits. A separate repeat reused **10/10 sections**; after a small edit, **9/10** were reused. These are local baseline observations, not promises for the later pronunciation candidate or other hardware. [Recorded JSON](C:/Users/fireball/OneDrive/Desktop/LiltTTS/artifacts/performance-integration.json).

The same speed-test record compared warmed configurations: approximately **1.13 audio seconds per processing second** for four-thread CPU and **12.47** for the tested CUDA configuration, on short samples with slightly different resulting audio durations. Model loading and cached passages were excluded from the warm inference comparison. DirectML synthesis also failed in the recorded investigation, so the application used the separately validated NVIDIA route; the inspected raw probe shows a failure on the RTX adapter. [Performance probe](C:/Users/fireball/OneDrive/Desktop/LiltTTS/artifacts/performance-probe.json); [README conditions](C:/Users/fireball/OneDrive/Desktop/LiltTTS/README.md).

### Failure handling and test quality

Two examples show work that would be invisible in a feature list:

- **Cache failure and saving:** an injected unavailable cache could make a healthy library or an already durable save appear to fail, blocking close. The correction separated optional cache availability from required writes. The 23 October report records **56 focused backend tests**, **18 browser tests**, and **five debug-off native scenarios** using synthetic libraries; it also preserves old-source failures and states the limits of those checks. [Cache correction results](C:/Users/fireball/OneDrive/Desktop/LiltTTS/docs/r02-cache-fix-results-2026-10-23.md).
- **Recording resurrection:** after an injected metadata-write failure, a successful removal left a pending retry that could recreate the deleted row. The report reproduced this in **four failed/cancelled × keep/delete-audio combinations**, with the row returning after about **2.03 seconds**. The correction coordinates deletion and the pending snapshot under the existing lock. It does not make file deletion and SQLite one transaction. [Removal/retry results](C:/Users/fireball/OneDrive/Desktop/LiltTTS/docs/r02-removal-retry-results-2026-10-23.md).

The team also corrected a **test-helper false pass**: a navigation check could report success after observation errors. The revised helper required specific URL, body, marker and runtime observations. That was a defect in validation tooling, not evidence that malicious navigation had occurred. [Navigation-helper results](C:/Users/fireball/OneDrive/Desktop/LiltTTS/docs/r02-navigation-helper-results-2026-10-23.md).

### Packaging and actual user feedback

The 25 October private classic installer wrapped an existing payload. The saved report says **1,175 installed payload files** matched their source size and SHA-256, and local silent install/uninstall checks passed while preserving external library metadata. That local installer check did not itself launch the application or exercise the wizard. On **26 October**, you reported the other-PC test step complete; the later handoff records Windows 11 CPU/NVIDIA device-flow acceptance, with hardware details incomplete. [Release status](C:/Users/fireball/OneDrive/Desktop/LiltTTS/docs/release-source-status.md); [test installer instructions](C:/Users/fireball/OneDrive/Desktop/LiltTTS/packaging/test-installer/README.md).

An earlier unsigned **MSIX 1.0.4.0** failed to install with `0x80073D2B`; an administrator `-AllowUnsigned` attempt also failed. The classic installer was the replacement **private test route**, not evidence of a working Store installation or update. The latest inspected plan says the production identity, package, install/update campaign, final licensing decisions and public support/privacy verification were still open. [Production MSIX plan](C:/Users/fireball/OneDrive/Desktop/LiltTTS/docs/msix-production-campaign.md).

## Capability map

“Specific thing I did” below describes work you **directed or participated in**, unless direct personal execution is explicitly established. The final column is an interpretation for future applications.

| Capability or work pattern | Specific thing I did | Project/version | Evidence or source | Scope and limitations | Possible relevance to future roles |
|---|---|---|---|---|---|
| Product definition | Defined a local reading workflow with early listening and no paid TTS service; clarified that the app reads supplied text. | Lilt → Violilt | [Product decisions](<C:/Users/fireball/OneDrive/Desktop/Obsidian Vaults/LiltTTS/LiltTTS/01 Product and Decisions.md>) | Saved notes summarize user direction; not evidence of market research or adoption. | Product-minded software engineering; requirements definition. |
| AI-assisted development and coordination | Directed focused implementation, independent review and release-readiness work across chats; asked how to communicate AI-code checks. | Violilt release work | Recent coordination and Store-readiness chats; [source status](C:/Users/fireball/OneDrive/Desktop/LiltTTS/docs/release-source-status.md) | Exact manual coding and line-by-line review responsibility is unclear. “Independent” reviews may also be AI-assisted. | AI-assisted engineering workflows; review and task coordination. |
| Local ML integration | Worked on a flow from prepared text and pronunciation to Kokoro ONNX synthesis, CPU/NVIDIA execution and audio output. | Current replacement branch | [Speech worker](C:/Users/fireball/OneDrive/Desktop/LiltTTS/backend/speech.py), [README](C:/Users/fireball/OneDrive/Desktop/LiltTTS/README.md) | Integration of existing models; no demonstrated model training. | Applied ML engineering; inference integration. |
| Error analysis | Reported unnatural readings and traced dictionary misses through phonemes before synthesis. | 15 October pronunciation investigation | [Unknown-word diagnosis](<C:/Users/fireball/OneDrive/Desktop/Obsidian Vaults/LiltTTS/LiltTTS/32 Unknown Word Pronunciation Diagnosis.md>) | Specific words and traced cases; not a comprehensive pronunciation benchmark. | ML product debugging; qualitative evaluation. |
| Model experimentation | Evaluated an isolated ONNX grapheme-to-phoneme candidate and checked export parity and fallback counts. | `pronunciation-fallback` | [Fallback results](<C:/Users/fireball/OneDrive/Desktop/Obsidian Vaults/LiltTTS/LiltTTS/34 Unknown Word Fallback Implementation Results.md>) | Separate branch; no general accuracy or current-release claim. | Model deployment experimentation; reproducible evaluation. |
| Asynchronous state and recovery | Developed a section-based worker flow with cancellation, continuation, cache identity and saved playback positions. | Violilt desktop | [Architecture notes](<C:/Users/fireball/OneDrive/Desktop/Obsidian Vaults/LiltTTS/LiltTTS/03 Architecture and Data Flow.md>), [speech source](C:/Users/fireball/OneDrive/Desktop/LiltTTS/backend/speech.py) | Code demonstrates design; individual authorship is unresolved. | Backend and desktop reliability engineering. |
| Fault injection and regression testing | Investigated cache outages and stale retry/removal interactions, preserving before/after evidence. | R-02 corrections | [Cache](C:/Users/fireball/OneDrive/Desktop/LiltTTS/docs/r02-cache-fix-results-2026-10-23.md), [retry](C:/Users/fireball/OneDrive/Desktop/LiltTTS/docs/r02-removal-retry-results-2026-10-23.md) | Triggered failure scenarios on scoped environments, not evidence of widespread incidents. | Reliability, data integrity and test engineering. |
| Performance analysis | Compared warmed CPU/CUDA inference, first-audio latency, caching and device behavior. | 8 October baseline | [Performance JSON](C:/Users/fireball/OneDrive/Desktop/LiltTTS/artifacts/performance-integration.json) | One machine and specific runs; timing is not product-wide impact. | Profiling and resource-aware inference. |
| UI and accessibility | Directed or participated in keyboard, focus, status, onboarding and layout improvements, with focused browser checks. | 24–25 October source | [Release source status](C:/Users/fireball/OneDrive/Desktop/LiltTTS/docs/release-source-status.md) | Fixture passes do not establish full assistive-technology or installed-package accessibility. | Frontend and inclusive product engineering. |
| Packaging and delivery | Prepared and checked a per-user installer, tracked package hashes and handled the failed MSIX test. | Private 1.0.4.0 | [Installer README](C:/Users/fireball/OneDrive/Desktop/LiltTTS/packaging/test-installer/README.md), release status | Private-device test; no verified Store release. | Windows delivery, build validation and release engineering. |
| Security, privacy and dependency work | Reviewed local boundaries, diagnostic behavior, model integrity and third-party distribution materials. | Release preparation | [Security investigation](C:/Users/fireball/OneDrive/Desktop/LiltTTS/docs/security-investigation-2026-10-21.md), [redistribution status](C:/Users/fireball/OneDrive/Desktop/LiltTTS/docs/release-redistribution-status.md) | Investigation and preparation; remaining package and supplier decisions are not a blanket clearance. | Secure development and software supply-chain awareness. |

## Application-ready material

### Concise factual description

**Violilt** is a Windows desktop reading application developed with AI assistance. It converts imported or pasted English text into locally generated speech using Kokoro-ONNX, supports playback during section-by-section generation, and saves recordings and reading state for later use. A private installer was prepared and tested; Microsoft Store release work remained open at the latest inspected checkpoint.

### Strongest supported capabilities

1. Directing an AI-assisted desktop product from requirements through implementation, review and private-device testing.
2. Integrating pretrained local speech models with CPU and optional NVIDIA inference.
3. Diagnosing output-quality problems at the boundary between text preparation, pronunciation and synthesis.
4. Designing and testing stateful generation, caching, continuation and failure recovery.
5. Evaluating changes with scoped automated, native, packaging and manual checks.
6. Preparing Windows distribution while tracking dependencies, licensing, privacy and unresolved release gates.

### Candidate CV bullets

Choose only the wording that matches your personal contribution; these are alternatives, not cumulative claims:

- **Product / general engineering:** Directed AI-assisted development of Violilt, a Windows reading app that converts Markdown, text and PDFs into locally generated speech and supports playback during generation.
- **Applied ML:** Integrated and evaluated local Kokoro-ONNX speech inference and an offline pronunciation pipeline, investigating differences between successful audio generation and natural pronunciation.
- **Reliability / backend:** Developed and validated a section-based narration workflow with cached audio, cancellation, saved positions and compatibility checks for resuming partial recordings.
- **Evaluation / debugging:** Investigated reported pronunciation errors by tracing dictionary lookup and emitted phonemes, then evaluated a separate ONNX grapheme-to-phoneme fallback against a preserved baseline.
- **Testing / release:** Coordinated focused regression, native-app and package checks for an AI-assisted desktop application, including injected storage failures and private Windows installer validation.

If you did not personally implement a particular component, replace “developed,” “integrated,” or “investigated” with **“directed development of,” “coordinated,”** or another verb that reflects your actual role.

### Interview stories

**1. Pronunciation quality despite passing technical checks**

- **Context:** The app generated valid audio, but you reported that ordinary technical words were being read letter by letter.
- **Work:** You requested investigation; the documented trace followed the words through speech preparation, dictionary lookup and fallback to the model’s phoneme input. A separate candidate explored constrained composition and ONNX pronunciation prediction.
- **Result:** The cause for the reproduced cases was identified, and the separate candidate reduced spelling warnings on one 165-section document.
- **Limit:** Warning counts and export parity do not establish natural pronunciation accuracy. Listening review remained necessary, and the candidate was not shown to be merged into the current release branch.

**2. A deletion that reappeared after recovery**

- **Context:** A failed recording metadata write was retained for retry, but a subsequent deletion could be undone when that retry succeeded.
- **Work:** The project reproduced the issue using a deliberately failed write, real listener and SQLite; the correction coordinated the successful delete with removal of that recording’s pending update.
- **Result:** The saved reports describe focused regression and lifecycle checks around the correction.
- **Limit:** The trigger was injected; the records do not establish that users experienced it in ordinary use. Filesystem deletion and database deletion still were not a single transaction.

### Claim boundaries

Do not claim a public launch, Store certification, production MSIX update success, broad hardware support, a user base, revenue, or business impact from the evidence above. Do not present the fallback-warning reduction as a pronunciation-accuracy improvement, or the single-PC benchmark as a general speed guarantee. The records establish pretrained-model integration and an export experiment, not training or fine-tuning.

## Compact project card

| Field | Record |
|---|---|
| **Name** | Violilt; repository/project **LiltTTS**; previously Lilt and earlier Folio |
| **Purpose** | Windows desktop reading room for local English narration of imported or pasted text |
| **Context** | Personal/publisher-directed product; exact formal context and individual authorship split unknown |
| **Technologies used** | Python, Svelte, TypeScript, Vite, pywebview/WebView2, SQLite, Kokoro-ONNX, Misaki, ONNX Runtime, optional CUDA, PyInstaller, Inno Setup; separate BART-to-ONNX pronunciation experiment |
| **Key work** | Product direction; local inference and audio workflow; pronunciation diagnosis; recovery and fault testing; UI/accessibility work; private installer and Store-readiness preparation |
| **Last known state** | Implemented and privately tested; other-PC experience accepted by you. Production Store package and final release checks remained open in the latest inspected records. |
| **Documented dates** | Git activity 8–25 October 2026; later release planning through 28 October 2026 |
| **Links** | [Repository](https://github.com/AbdelrahmanElmughrabi/Lilt); [local README](C:/Users/fireball/OneDrive/Desktop/LiltTTS/README.md); [release status](C:/Users/fireball/OneDrive/Desktop/LiltTTS/docs/release-source-status.md) |
| **Evidence limits** | Selected code, history, notes, artifacts and chats inspected; no fresh tests, listening review or independent Store-state verification |

### Important corrections and conflicts

- Older notes describe **drag-and-drop, TXT/PDF import and installation** as future work; later source and release records show those features or test routes were subsequently added.
- The 15 October note calls the neural pronunciation fallback a current candidate **for its separate branch**. The inspected current release branch does not contain that commit and retains the v4 spelling fallback.
- An older README says the portable executable had only been verified on one PC. The later release record and your chat report add **other-PC private-test acceptance**. They still do not establish a final Store-package test.
- A successful package build or audit did not mean the unsigned MSIX installed; the recorded device attempt failed. The classic installer addressed private testing, while production MSIX work remained separate.
- Earlier release reviews and test counts apply to their dated source and environments. Later corrections and independent reviews changed some statuses; historical counts should not be combined into a single current acceptance result.

### Missing or incompletely inspected sources

- The earlier `C:\Users\fireball\OneDrive\Desktop\TTS` directory was unavailable.
- Many older chats, the full Obsidian archive, raw `.tmp` evidence, listening samples, and every branch diff were not exhaustively reviewed.
- The current public status of the repository, publisher website and Store submission was not independently checked.
- Personal authorship of specific code, direct test execution, broader user feedback and any later release activity are not established by the inspected evidence.

### Targeted questions

1. For applications, which parts did you personally code or review in detail, and which did you mainly specify, direct and validate through Codex?
2. Was Violilt entirely a personal project, or was it undertaken for an organization, course or other formal context?
3. Did you complete a listening comparison of the separate pronunciation fallback, and was that candidate ever adopted later?
4. Has the app been publicly released or used by anyone beyond the private device tests since the 28 October checkpoint?
