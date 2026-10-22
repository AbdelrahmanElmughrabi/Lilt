# Privacy release review

Traced 21 October 2026 against the hardened working tree and its separate CPU/GPU evaluation build. This is internal release evidence, **not a published privacy policy**. Publisher/contact details, public URLs, retention choices and installed-package verification remain open.

## Trace and proposed decisions

| Surface | Evidence / current behavior | Required result before release |
| --- | --- | --- |
| Text and audio | App-written processing uses the local library, speech worker and loopback media server. The source search found no app-written analytics, crash uploader or app-update client. | Retain local processing; verify external traffic on the final installed package before making network/privacy claims. |
| Model fallback | Runtime downloads now use fixed HTTPS GitHub release URLs and independently pinned file hashes. Local packaged models are available for offline inference. | Disclose the network contact when setup/download is used. GitHub and its asset delivery hosts receive normal connection/request information. Test offline first run and failures. |
| WebView2 | Existing integration does not override SmartScreen or custom crash-reporting settings. Microsoft's documentation describes required/optional diagnostic data, SmartScreen notices and crash minidumps. | Verify the actual runtime settings. Preserve security protections and provide the applicable Microsoft notices; decide whether to use custom crash reporting. Do not claim the app sends no diagnostics. |
| ONNX Runtime | CPU 1.30.0 and GPU 1.24.4 ship as official Windows builds. Both versions document platform ETW telemetry, enabled by default, with control APIs. No app call to disable non-essential events was found. | Deliberately select and test a diagnostic policy in both parent and worker processes. Document its limits, including initialization events; changing a current-main environment variable is not evidence for these shipped versions. |
| Local library | SQLite stores copied text, source paths, settings, job snapshots and playback state. WAVs, section cache, browser data and logs are separate files. | Verify per-user permissions on a clean standard-user install; document custom/shared data-folder behavior. Do not claim app-level encryption. |
| Backups and recovery | Schema upgrades now create verified SQLite backups. Malformed rows are retained in the original table and recovery records, and the app shows a recovery notice. | Specify recovery/export/support behavior and retention. A full deletion design must include backups and recovery records. |
| Deletion | Removing a document does not remove historical job snapshots. Removing a recording can retain audio unless the user selects audio deletion. Browser data/cache/backups are additional copies. | Make each deletion action accurate and understandable. Define a full-library removal procedure and test uninstall/reinstall retention. Do not promise secure erasure. |
| Support | No remote support channel or automatic log submission was added. Local errors/logs and crash data can contain paths or application state. | Supply publisher contact details and explain any optional user-supplied diagnostics. Review logs before sharing and minimize sensitive content. |

## Primary references checked for these versions

R-02 source probe update, 22 October: canceled native navigation retained the trusted document and blocked the controlled foreign page's script/native access, but preliminary GETs reached the controlled destination. No Referer/Cookie was observed in those requests. Cancellation does not establish zero external contact; Microsoft documents preliminary requests before cancellation takes effect in [NavigationStartingEventArgs](https://learn.microsoft.com/en-us/microsoft-edge/webview2/reference/win32/icorewebview2navigationstartingeventargs). Do not turn this limited source observation into an installed-package privacy claim. Raw local known-port/recording-UUID audio access also remains possible; browser fetch/media/frame isolation passed its synthetic probe. See [R-02 results](r02-results-2026-10-22.md). Runtime diagnostics, installed traffic/permissions and public disclosures are still open.

- [WebView2 data and privacy](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/data-privacy): required diagnostic collection, Windows optional diagnostics, SmartScreen notice, and default crash reporting. Exact application/runtime behavior still needs verification.
- [ONNX Runtime 1.30.0 privacy](https://github.com/microsoft/onnxruntime/blob/v1.30.0/docs/Privacy.md): Windows ETW behavior and non-essential-event controls; a minimal initialization event can precede the API call.
- [ONNX Runtime 1.24.4 privacy](https://github.com/microsoft/onnxruntime/blob/v1.24.4/docs/Privacy.md): official Windows builds use platform telemetry and provide control APIs.
- [Microsoft Store policies](https://learn.microsoft.com/en-us/windows/apps/publish/store-policies): the published 7.20 document becomes effective 22 October 2026. Recheck the applicable version when submitting.

## Plan

1. Verify shipped WebView2/runtime settings and observe the installed app's external connections with synthetic text; distinguish Windows/runtime traffic from app-authored requests.
2. Implement and verify the chosen diagnostic and retention controls, with CPU/GPU support preserved.
3. Draft the public policy and in-app notices around verified behavior, adding the actual publisher, support contact and hosting URLs.
4. Check deletion/export/recovery and uninstall behavior against those promises. Publisher reviews the completed disclosures before publication.

This trace does not establish a legal privacy determination or that diagnostic traffic contains no user content. Native crash dumps may contain application memory; vendor documentation must be reflected accurately.
