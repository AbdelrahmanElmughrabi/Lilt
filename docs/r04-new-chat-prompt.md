# New-chat prompt — R-04 redistribution rights and provenance

Copy the prompt below into a new chat with this project available. This prompt prepares the investigation; it does not record that R-04 has started or passed. The current latest completed investigation remains R-03.

```text
Proceed with R-04: complete the redistribution/licensing/provenance investigation
for Violilt's intended Microsoft Store release.

Workspace: C:\Users\fireball\OneDrive\Desktop\LiltTTS
Use the actual current date for online terms/advisory checks. Prior reports are
dated 22 October 2026. Follow trace → plan → investigate/prepare → validate → record.
Start with read-only inspection, give a concise trace/plan update, then carry out
the authorized evidence review. Do not stop at a generic licensing checklist.

PRODUCT AND CURRENT STATE
- Violilt is a proprietary Windows x64 desktop TTS app, intended for MSIX/Microsoft
  Store distribution. Local English speech with CPU AND optional NVIDIA GPU stays
  in version 1. Do not remove GPU, voices or dependencies to simplify licensing.
- Pricing remains undecided; free without ads is only the recommendation. Do not
  add ads/payments or assume that a free release removes redistribution duties.
- The publisher wants Violilt-owned code closed source. Respect each third-party
  component's actual terms without assuming that all app code must be open source,
  or that proprietary packaging cancels component source/replacement rights.
- Existing EXE/MSIX artifacts are older. Compatibility MSIX 1.0.3.0 and the
  bbe961f portable payload predate later refinements and R-01/R-02. They are useful
  historical inventory, not proof of the future final package or release approval.
- R-01 normal-close and R-02 storage/navigation fixes are locally validated, with
  independent acceptance still pending. R-03's advisory investigation is complete,
  but runtime/audio remediation and native coverage are open. No independent
  verdict has been supplied here. Do not silently treat any report as approval.
- R-03 found Python/OpenSSL/Expat refresh needs, unresolved native audio parsing/
  provenance, and a recommended DOMPurify update. None was installed/applied.
  Rights evidence must be tied to exact reviewed versions and refreshed if later
  security remediation changes them. Stable components can be reviewed now.

READ FIRST (paths below are relative to the workspace)
1. docs/HANDOFF.md, newest R-03/R-02/source-checkpoint sections.
2. docs/release-readiness.md, especially R-04 and evidence boundaries.
3. docs/release-review-handoff.md, for per-R handoff and independent review rules.
4. docs/r03-results-2026-10-22.md and .tmp/r03-20261022/:
   inventory.json, python-inclusion.json, current-native-runtime.json,
   current-runtime-correspondence.json, numpy-build-config.json, tagged ONNX
   deps files, primary records and source-hashes.json.
5. thirdparty/PRONUNCIATION-CANDIDATE.md, GPU-RUNTIME-INTEGRITY.md, PDF-IMPORT.md,
   licenses/README.md and relevant versioned license files.
6. tools/assemble_pronunciation_notices.py, package_pronunciation_audit.py,
   msix_package.py, packaging/Violilt.spec, build.ps1, setup-pronunciation.ps1;
   requirements.txt, requirements.lock.txt, requirements-gpu.lock.txt and
   requirements-build.lock.txt; frontend/package.json and package-lock.json.
7. backend/model_trust.py, gpu_trust.py, runtime.py, kokoro_engine.py and
   backend/_vendor/kokoro/ including trim.py; repository artwork/fonts/examples
   and provenance records where relevant.
8. dist/validation-bbe961f-20261022/Violilt/package-audit.json and third-party/:
   manifest.json, MODEL-ATTRIBUTIONS.md, SOURCE-RIGHTS.md, README.md,
   sources/source-manifest.json, python/, frontend/, native/ and existing archives.
   Use existing .tmp/pronunciation-notices, .tmp/pronunciation-sources and prepared
   public GPU runtime metadata where useful. Never substitute a personal library.

WORK RULES / AUTHORIZATION
- Preserve all existing uncommitted/untracked work, original evidence, packaged
  artifacts and shared dependencies/assets. The HEAD baseline previously recorded
  is bdf58f1b4c89a269d0647050fe26f524e73b4c12; verify current state rather than assume.
- R-02's .tmp/r02-20261022/source-hashes.json covers 69 inputs. R-03's manifest
  covers additional configuration, dependency/runtime identities and evidence.
  Check relevant hashes before/after and report drift. Do not overwrite manifests.
  These are hash records, not archived source checkouts.
- No dependency installations/upgrades, commits or other Git mutations, destructive
  operations, EXE/MSIX builds/installations, model downloads, personal-data access,
  publication, vendor/contact messages, account actions, payments or source uploads.
  Do not run setup/build scripts or auto-fix dependencies. Backup requirement waived.
- Documentation, new evidence and clearly labeled staged notice/EULA drafts are
  allowed. Write into a fresh .tmp/r04-<date>-<unique>/ and new R-04 documents.
  Do not regenerate/overwrite historical notices or change application/build code.
  Report any needed implementation change with a concrete plan before applying it.
- Use existing tools. Read public existing wheel/source archives without executing
  their contents. Browse official upstream/vendor/license sources for current,
  version-specific primary evidence; save needed public terms/notices/build metadata
  in the new evidence folder. Avoid re-downloading large weights/runtime binaries.
  A dependency's README/SPDX label, a PyPI wheel, a matching hash or a prior agent's
  assertion alone does not establish every distributed artifact's rights.
- Other chats may review earlier batches. Continue independent investigation,
  record overlaps, and leave their source/assets/dependencies untouched. Do not
  create or send messages to other chats; I will carry the review prompt/report.

INVESTIGATE THESE BOUNDARIES
A. Exact distribution inventory and scope.
   Map current proposed components against actual older packaged files, frozen
   modules, external code, GPU files, models/data, frontend assets and notices.
   Distinguish shipped code/data from build-only/environment/unused extras and
   separately serviced machine prerequisites. PyInstaller's bootloader/hooks can
   ship even when its build package does not. certifi/num2words/tqdm can ship as
   external source. Current pypdf is required although absent from the old payload.
   Include embedded/vendored native subcomponents, not just top-level wheel labels.

B. Models, voices, conversion and dictionaries.
   Use the exact approved artifacts/hashes in backend/model_trust.py:
   kokoro-v1.0.int8.onnx, kokoro-v1.0.fp16-gpu.onnx and voices-v1.0.bin.
   Trace the upstream weight → conversion/quantization → release artifact chain,
   applicable license/NOTICE/modification attribution and redistribution evidence.
   Review the WHOLE distributed voice artifact, not only voices enabled in the UI.
   Review Misaki 0.9.4 English dictionary files and their data provenance separately
   from its package code, plus spaCy en_core_web_sm 3.8.0 and relevant data terms.
   Mark uncertain authority/data lineage honestly; do not infer all rights from a
   model-card headline, and do not invent consent/ownership evidence.

C. Proprietary code and third-party source/replacement obligations.
   Verify actual license versions and required arrangements for num2words 0.5.14,
   certifi, tqdm and libsndfile/SoundFile. Check matching source/build materials,
   notices, source-availability mechanism and practical replacement/debugging rights
   for the planned frozen/MSIX route. An upstream tarball with a similar version
   is not automatically corresponding source for a bundled patched DLL.
   Identify concrete EULA/reverse-engineering clauses that would conflict with
   component rights. Draft limited component exceptions/notice text where supported;
   keep publisher details/terms placeholders explicit and do not claim final legal
   approval. Do not apply a blanket source-disclosure requirement to independent
   Violilt code or promise that installed MSIX replacement has been tested.

D. Native audio and compiled dependencies.
   Establish exact libsndfile DLL build/patch origin, linked codecs and matching
   source/build/licensing evidence. R-03 observed libsndfile 1.2.2, FLAC 1.4.3 and
   Opus 1.5.2 markers, not a complete codec SBOM. Include other actual codec inputs.
   Review NumPy/OpenBLAS, libffi, CPython/stdlib/OpenSSL/SQLite and ONNX Runtime's
   compiled dependencies/notices where present. Tag-declared ONNX C++ protobuf/
   FlatBuffers versions are distinct from installed Python packages and do not
   prove exact wheel composition. Coordinate provenance gaps with R-03 rather
   than rerunning its advisory investigation or clearing its security findings.

E. NVIDIA/Microsoft redistribution.
   Match all actual pinned GPU DLLs to exact package/version-specific authoritative
   redistribution grants and required notices. Keep NVIDIA support. Reconcile wheel
   terms versus current online CUDA/cuDNN terms; do not assume all toolkit content
   is redistributable or that a toolkit EULA covers every wheel artifact.
   Review VC/UCRT/API-set files (including renamed NumPy copies), WebView2 SDK/
   wrappers/loader and Python/.NET bridge pieces. Distinguish SDK redistribution
   from the separately serviced Evergreen/Windows/.NET prerequisites. Signatures
   establish some provenance, not by themselves a redistribution license.

F. Remaining notices and product assets.
   Verify pypdf 6.21.2, frontend direct/transitive bundled code, Kokoro adapter/
   librosa-derived trim code, required license/NOTICE/modification texts, logos,
   icons, fonts and distributed example documents. Do not assume unknown artwork
   belongs to the publisher merely because it is in the repository.
   Check notice assembler completeness and whether its environment-wide manifest
   overstates/understates actual inclusion. Keep legally required source/notices
   compatible with the intended proprietary distribution and Store route. Account,
   pricing, general privacy and final Store-certification work remain separate.

REQUIRED DELIVERABLES
1. A concise trace/plan followed by a substantive R-04 results document.
2. A component/rights matrix, ideally CSV plus readable Markdown, with:
   artifact path/hash/version; shipped/proposed/build-only/prerequisite scope;
   provenance and primary version-specific license URLs/retrieval date; license/
   grant; notice/source/replacement/modification conditions; evidence actually
   inspected; remaining gap; concrete action/owner; release-blocker status.
   Separate verified evidence, inference, unverified assumptions and publisher input.
3. An actionable gap list: what is already supported, what needs materials or a
   packaging/notice/EULA change, what needs publisher ownership/contract details,
   and what must be rechecked after R-03 updates/final build. Do not make every
   ambiguity a generic lawyer blocker; identify the exact unresolved clause/fact.
4. Staged notice/source-offer/component-exception drafts where evidence supports
   them; label incomplete identity/hosting facts. Do not publish, accept terms for
   me, fabricate legal authority or silently replace missing license texts.
5. Appropriate checks: hashes, archive contents, license/NOTICE coverage and
   consistency between artifacts and rights records. No need to rerun unrelated
   application suites for a documentation-only audit. Existing runtime test counts
   must remain historical; installed replacement rights/behavior are not tested here.
6. Record exact inputs/evidence in a NEW manifest. Keep source/frozen-package,
   installed-MSIX, another-machine/low-end/no-GPU, rights/privacy and certification
   evidence separate. Testing the actual final MSIX on another machine before
   release remains mandatory. Do not clear a gate solely because a report exists.
7. Finish with docs/r04-independent-verification-prompt.md (or a clearly dated
   equivalent) for a different review chat: scope, files, evidence, claims to
   challenge, relevant checks, constraints and expected verdict. Update HANDOFF.md,
   release-readiness.md and release-review-handoff.md to record the R-04 batch
   and independent-review status, preserving pending earlier reviews/history.

FINAL RESPONSE
Briefly state completed investigation work, verified conclusions, unresolved release
blockers, decisions/materials I must supply and the recommended next batch. Link
the report, matrix and copyable independent-review prompt. Keep any legal conclusion
within the evidence; missing rights/provenance must remain explicit. Do not claim
blanket commercial/Store/legal approval or begin R-05 without a further instruction.
```
