# Production MSIX: remaining work and focused update campaign

28 October 2026. Planning and source inspection only; no production package,
installation, certification, supplier assent or release acceptance is claimed.
The private EXE and publisher-reported other-PC tests retain their existing scope.

## Inputs and package preparation

1. Copy the exact Identity Name, Publisher and PublisherDisplayName from Partner
   Center's app identity details. Preserve punctuation and case. Establish a
   production packaging path: `tools/build_msix.ps1` and `tools/msix_package.py`
   deliberately reject production identities and write an isolated compatibility
   marker. Do not submit their current output. Confirm the production marker and
   data profile from the resulting artifact, not just the source configuration.
2. Keep Name and Publisher stable between releases; use a higher version for the
   update. Store-targeted package versions end in `.0` at build time. Record both
   manifests, package family names, versions, architecture and artifact hashes.
   Store may change the fourth component when signing. Choose actual versions
   after checking the Partner Center submission history.
3. Resolve supported Microsoft C++ runtime deployment in the actual package.
   The present compatibility manifest declares only a target device family, not
   a VCLibs framework dependency. Microsoft's Desktop Bridge guidance specifies
   the matching framework package rather than merely bundling Visual C++ runtime
   libraries. Determine the appropriate version and reconcile the actual payload
   and dependencies; verify installation and loading on the target. Do not assume
   the existing bundled DLLs or a generic manifest edit prove this gate.
4. Include the new notice/source material and the adopted recipient terms, with
   a verified agreement mechanism. A protected MSIX needs a usable LGPL library
   replacement/source arrangement or another implemented section 6 route; the
   writable copied EXE demonstration does not prove the protected package route.
   The Store listing's additional license terms are a possible surface, but their
   presentation and sufficiency for this distribution remain to be established.
5. Choose a concrete install channel. A local signed test needs an appropriate
   certificate whose subject matches the manifest publisher and device trust;
   certificate creation/import and device policy changes require explicit review.
   Alternatively investigate a Store-delivered test/flight when the publisher is
   ready; it entails Partner Center submission and is not authorized here. A local
   test identity cannot establish update continuity from a Store identity. The
   Store signs the accepted distribution, so no purchased CA certificate is
   required for the Store MSIX. Do not repeat the failed unsigned executable test.

## One baseline-to-update campaign

Use an isolated Windows test account/device and synthetic data only; record the
actual channel and exact package hashes. Preserve existing personal libraries.
Build a representative baseline and higher-version candidate using the same
production package family and runtime/data layout. A local signing route is a
preflight; final Store-signed install and update evidence remains distinct.

1. Install baseline, launch as a standard user, identify the actual writable data
   and model locations, and create a disposable library with settings, a document,
   recording/export and model state. Record fingerprints and meaningful contents.
   `backend/storage.py` selects `%LOCALAPPDATA%/Violilt` for production absent an
   override; actual packaged path/virtualization and persistence remain unproved.
   Existing evaluation and compatibility profiles are separate; any migration is
   explicit and must be tested only on a disposable copy if offered.
2. Attempt the update with the app running; record the actual prompt, deferral or
   error and whether unsaved work is handled safely. Close normally if required,
   complete the update, relaunch and check identity/version and every seeded item.
   Verify that no unexpected fresh library, data loss, model re-download or broken
   paths occur. Record outcomes rather than assuming Windows terminates or preserves
   a running app in a particular way.
3. Exercise the affected normal launch/close, native bridge, CPU narration and
   export; observe the claimed NVIDIA path and deferred runtime load attempts on
   an appropriate supported GPU. If a selected alternate path fails for its absent
   companion, resolve that observed failure. Reuse accepted prior device results;
   do not promise support for every MX model.
4. Verify actual runtime dependencies, delivered notices and the practical LGPL
   replacement route on the protected final package. Run WACK and focused installed
   lifecycle, accessibility/scaling and privacy/support-link checks against the
   relevant final artifact; retain logs, versions, hashes and any exceptions.
   Record the R03 N2 supplier statement or explicit component-specific residual-risk
   disposition without asserting the unproved protobuf exclusions.

Windows/MSIX supplies the update mechanism; no bespoke updater is currently
needed. A later fix for users already on a bad version needs a higher applicable
package version. See Microsoft's [update constraints](https://learn.microsoft.com/en-us/windows/msix/app-package-updates),
[Store package requirements](https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msix/app-package-requirements),
[Store update process](https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msix/publish-update-to-your-app-on-store)
and [C++ framework guidance](https://learn.microsoft.com/en-us/troubleshoot/developer/visualstudio/cpp/libraries/c-runtime-packages-desktop-bridge).

Publisher actions and the complete draft are in [the licensing guide](publisher-licensing-actions.md)
and [recipient terms](../thirdparty/RECIPIENT-TERMS-DRAFT.md). The finite
[redistribution ledger](release-redistribution-status.md) controls their present
status. Public support/privacy links and publisher/contact facts remain to be
verified when finalized. Store certification and the publisher's release decision
remain final gates.
