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
without NVIDIA and machines with NVIDIA, including unspecified MX models. Plan
one compatibility test payload containing CPU plus the optional NVIDIA runtime.
CPU operation is the baseline on each device; acceleration is checked against
the actual GPU model/driver rather than promised for every MX-branded device.
The existing unsigned Windows 11 test-MSIX route requires Administrator
PowerShell to install executable content. A portable folder build remains an
option when installation access is unavailable; it does not replace final MSIX
installation/update testing. No concrete package has been created for this batch.

No package, installation, website publication or account operation is authorized
or performed solely by recording these addresses. Existing release requirements
remain as recorded in `release-source-status.md`.
