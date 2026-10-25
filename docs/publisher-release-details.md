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
The existing unsigned Windows 11 test-MSIX route requires Administrator
PowerShell to install executable content. A portable folder build remains an
option when installation access is unavailable; it does not replace final MSIX
installation/update testing. The subsequently authorized test-build batch
created Windows 11 x64 MSIX 1.0.4.0, with every mapped archive entry verified.
Installation and actual CPU/NVIDIA device tests remain pending.

Test package: [dist/device-test-20261025-1.0.4.0/Violilt-MsixCompatibility-1.0.4.0-x64.msix](../dist/device-test-20261025-1.0.4.0/Violilt-MsixCompatibility-1.0.4.0-x64.msix).
Instructions/checksum/inventory are beside it in `dist/device-test-20261025-1.0.4.0`. Source commit:
`7ce6a21afd7a5f7d8dfe46b3081a11ec3947d764`. SHA-256:
`8a27da0cf563143eedf93df2ee520ebbcee9e6e76ff56035df5a4e56c9cd3ea7`.

No installation, website publication or account operation was performed. The
link-recording phase and later package-building phase remain separate in the
local evidence. Existing release requirements remain as recorded in
`release-source-status.md`.
