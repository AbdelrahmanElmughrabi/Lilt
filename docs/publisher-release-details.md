# Provisional publisher links

25 October 2026. The publisher supplied `velourvolute.com` and the expected
`/violilt` app page. These are intended addresses, not verified deployed pages.

| Purpose | Address |
| --- | --- |
| Publisher website | https://velourvolute.com |
| Violilt website | https://velourvolute.com/violilt |
| Privacy policy | https://velourvolute.com/violilt/privacypolicy |
| Support | https://velourvolute.com/violilt/support |

The policy path reads the publisher's appended “policy” as `/privacypolicy`.
The support route remains the inferred app-specific route. Both can be changed
before deployment. The canonical application mapping is `PUBLISHER_LINKS` in
`backend/bridge.py`; About and Settings receive their addresses from it. The
native opener accepts fixed reference IDs, never caller-supplied addresses.
Microsoft's existing privacy references remain separate and unchanged.

The publisher display/legal name, exact Partner Center package identity and
support contact were not supplied by the domain alone. Do not derive a manifest
Publisher value from the domain or turn the compatibility identity into a
production identity. Public policies must describe the actual application and
the hosted links must work before the final submission.

A separately identified test build can be prepared for the publisher's controlled
device testing while the website is unfinished. Existing compatibility packaging
is not the final Store identity. Changes embedded in a build require a fresh
build and affected checks; hosted content at the same address can change without
an application rebuild. Stable redirects can preserve older embedded links.
Final production package/identity installation and update checks remain separate.

The publisher's intended test devices run Windows 11, with a mix of machines
without NVIDIA and machines with NVIDIA, including unspecified MX models. The
prepared compatibility payload contains CPU plus the optional NVIDIA runtime.
CPU operation is the baseline on each device; acceleration is checked against
the actual GPU model/driver rather than promised for every MX-branded device.
The unsigned Windows 11 test-MSIX route failed on the publisher's other device:
`0x80073D2B`, because an unsigned package cannot include executable activations.
Administrator PowerShell with `-AllowUnsigned` did not make it installable.
The earlier static archive checks passed but did not establish installation.
That MSIX handoff is superseded by the publisher-authorized classic unsigned
EXE installer route. No certificate or trust-store change is required by that
route. Actual CPU/NVIDIA device tests and final Store installation/update checks
remain separate.

Current handoff: [Violilt Test 1.0.4.0 Setup.exe](../dist/test-installer-20261025-1.0.4.0/Violilt-Test-1.0.4.0-x64-Setup.exe),
1,692,601,318 bytes (1.69 GB). Copy only that EXE to the test device and run its
normal setup wizard; then open **Violilt Test** from Start. CPU/NVIDIA runtimes,
models and notices are included. No certificate import or app rebuild was used.
The installer is unsigned, so Windows protection or managed policy can warn or
block it. Microsoft Edge WebView2 must be available on the target.

Local silent install and uninstall both returned 0. Every one of the 1,175
installed payload files matched its recorded size/SHA-256; Start-menu targets,
HKCU uninstall registration, unchecked desktop shortcut and removal passed.
Uninstall preserved a user-added file and external app-library file metadata.
The normal wizard was not driven interactively; no app launch, inference or
other-device acceptance is claimed. This wrapper retains the existing
`Violilt-Pronunciation-Evaluation` profile, shared with prior evaluation builds
and separate from the production library. Uninstall keeps that external library.
See [transfer/test instructions](../dist/test-installer-20261025-1.0.4.0/README-TEST.md)
and the [local install/uninstall record](../.tmp/test-installer-20261025-3f43ae90/install-test.json).
Installer SHA-256: `d394631df671490881186abaceaee362f5a0606a2eaab226e70f7ef315f6d14b`.

Historical failed-install test package: [dist/device-test-20261025-1.0.4.0/Violilt-MsixCompatibility-1.0.4.0-x64.msix](../dist/device-test-20261025-1.0.4.0/Violilt-MsixCompatibility-1.0.4.0-x64.msix).
Instructions/checksum/inventory are beside it in `dist/device-test-20261025-1.0.4.0`. Source commit:
`7ce6a21afd7a5f7d8dfe46b3081a11ec3947d764`. SHA-256:
`8a27da0cf563143eedf93df2ee520ebbcee9e6e76ff56035df5a4e56c9cd3ea7`.

The previous batch performed no installation; the subsequent publisher device
attempt failed as recorded above. No website publication or account operation
was performed. Existing release requirements remain as recorded in
`release-source-status.md`.

On 26 October 2026, the publisher marked the other-PC testing step complete and
reported that the application works perfectly. This is publisher-reported
acceptance of the classic test build. Final Store-identity MSIX installation,
update and certification retain their separate scope.

The fresh 26 October R04 closure authorization is recorded in the
[finite closure ledger](release-redistribution-status.md). The publisher confirmed that no
third-party pictures, logos or copied text were imported into the artwork or
first-reading sample. Actual Microsoft license acceptance and NVIDIA agreement
adoption remain unconfirmed; the [publisher action guide](publisher-licensing-actions.md)
explains the personal steps. Current accompanying-source delivery is verified;
additional notice/instruction files and a recipient-terms draft are prepared for
the next adopted distribution. The existing test installer and its hashes are
unchanged. Website/production identity and final Store certification remain
separate from this licensing/source closure batch.
