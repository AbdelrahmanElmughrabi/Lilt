# Private Windows device-test installer

This creates a classic unsigned EXE installer from an already audited CPU/NVIDIA
payload. It is separate from production MSIX packaging. No certificate, trust
import, system service, driver, security-setting change or app rebuild is involved.

The installer supports Windows 11 x64-compatible systems, installs for the current
user under `%LOCALAPPDATA%\Programs\VioliltTest`, creates Start-menu launch/uninstall
shortcuts, and offers an unchecked desktop-shortcut option. It never launches the
app automatically. Microsoft Edge WebView2 must already be available.

It preserves the payload's `Violilt-Pronunciation-Evaluation` data profile. That
profile is separate from the production `Violilt` library but shared with earlier
evaluation builds using the same profile. Uninstall removes installed files and
shortcuts; it does not delete the external app library or user-added files.

## Build

Use PowerShell 7. Obtain the official pinned Inno Setup compiler with:

```powershell
$compiler = ./tools/setup_inno_tools.ps1
```

The tool helper verifies the official release SHA-256 and Authenticode publisher,
then extracts the compiler in portable mode under `.tmp/inno-toolchain`. The
compiler's upstream license is included there. Inno Setup is used under its
[published license](https://jrsoftware.org/files/is/license.txt).

Pass the audit hash and original app source commit from the payload's saved build
record. Use a fresh output directory; existing outputs are never overwritten:

```powershell
python tools/build_test_installer.py `
  --compiler $compiler `
  --payload 'dist/device-test-payload-20261025-1.0.4.0/Violilt' `
  --audit-sha256 '5aa16925c6fbb422861c4e1e4bb689cc977baf642bdb827447f56391c8a5edd5' `
  --source-commit '7ce6a21afd7a5f7d8dfe46b3081a11ec3947d764' `
  --output 'dist/test-installer-new' `
  --version '1.0.4.0'
```

The builder verifies the complete payload file set and every size/hash, then
produces one `Setup.exe`, checksum, inventory and compiler log. Build completion
does not imply installation or app-flow acceptance. Verify the actual installer
on a disposable destination before handing it off. Hardware compatibility and
production redistribution/Store requirements retain their separate scope.

## Device testing

Copy the generated `Setup.exe` to a Windows 11 test PC, run it, finish the wizard,
then open **Violilt Test** from Start. No Python or Node installation is needed.
The bundled models are included. Start with CPU narration; NVIDIA acceleration
depends on the device's actual GPU and driver, including the specific MX model.
Windows may warn about the unsigned installer; managed security policies can
block it. Do not change certificate trust or disable protection to install it.

Uninstall **Violilt Test** from Windows Settings > Apps or its Start-menu shortcut.
This test route does not validate the eventual Store package's installation,
identity, update behavior or certification.
