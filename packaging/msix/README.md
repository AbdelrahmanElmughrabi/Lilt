# Local MSIX compatibility build

This is the first deployment experiment for the Microsoft Store release. It keeps
both CPU and NVIDIA GPU support and uses **Violilt MSIX Compatibility**, a local test
identity. It is not a production identity and must not be submitted to Partner Center.

The app uses the separate `Violilt-MSIX-Compatibility` library profile. It ignores
production and pronunciation-evaluation data overrides. An explicit
`VIOLILT_MSIX_TEST_DATA_DIR` or `--data-dir` may select disposable test data. Existing
production/evaluation libraries are not migrated by this profile.

From the repository root:

```powershell
& .\tools\build_msix.ps1 -CompatibilityTest -BuildPayload -Version 1.0.1.0
```

This rebuilds the current source with `build.ps1 -IncludeGpu` into
`dist\msix-payload\Violilt`, then creates an **unsigned** package in
`dist\msix-compatibility`. It leaves the normal `dist\pronunciation` build and
preserved baseline output alone. Close the MSIX payload executable before rebuilding
that folder.

To package an already built CPU/GPU payload:

```powershell
& .\tools\build_msix.ps1 -CompatibilityTest -PayloadDirectory dist\msix-payload\Violilt -Version 1.0.2.0
```

The tools do not overwrite an existing package with the same version/output path.
MakeAppx validates the manifest during packing. A mapping file references the existing
payload, avoiding a second full copy of the GPU DLLs. The mapping is not shipped;
the external inventory records each shipped file's size/hash and the completed
package's hash. Personal databases/audio, unexpected top-level files, and reparse
points are rejected. A missing GPU model/runtime or failing existing payload audit
stops the build; there is no CPU-only fallback in this packaging pipeline.

`tools/setup_msix_tools.ps1` downloads the pinned official Microsoft Windows SDK
BuildTools NuGet package into `.tmp\msix-toolchain` when needed. The archive hash
is pinned in `toolchain.json`; Microsoft Authenticode signatures on MakeAppx and
SignTool are checked before use. No system-wide SDK installation is needed.

Package assets are resized from the existing Violilt artwork using Windows
System.Drawing. The Windows minimum build in `compatibility.json` is provisional
for this experiment, not a declaration of the production app's tested OS support.

The compatibility identity uses Microsoft's explicit unsigned-test publisher OID.
This keeps it separate from signed/Store identities. On Windows 11 the concrete
package can be tested without trusting a development certificate. Windows requires
Administrator PowerShell to install an unsigned package containing executable code;
this is a local testing requirement, not a customer installation requirement.
See [Microsoft's unsigned-package guidance](https://learn.microsoft.com/en-us/windows/msix/package/unsigned-package).

After a successful build, inspect installation without changing the machine:

```powershell
& .\tools\install_msix_test.ps1 -PackagePath .\dist\msix-compatibility\Violilt-MsixCompatibility-1.0.1.0-x64.msix -WhatIf
```

To install, run the same command without `-WhatIf` from an Administrator PowerShell.
The helper checks the identity, inventory and package hash before installation. It
does not change certificate trust, developer mode, firewall policy or loopback
exemptions. The build itself never installs the package or publishes anything.
Launch the test app from Start as a standard user after installation.

An unsigned MSIX is a build artifact, not proof of installation or runtime
compatibility. The remaining deployment checks are:

- Install the concrete test artifact through the explicit local unsigned-test workflow.
- Launch it as a standard user and verify the actual virtualized data location.
- Exercise WebView2/native bridge/file drop, CPU and CUDA inference, streaming and
  export, worker cleanup, and missing-runtime/driver behavior.
- Rehearse an older-to-newer package update with a disposable library.
- Test every advertised OS/hardware target, including a machine without NVIDIA.

Store identity, redistribution clearance, security/data hardening, and certification
remain separate release gates. See [the release plan](../../docs/ms-store-release.md)
and [findings register](../../docs/ms-store-findings.md).
