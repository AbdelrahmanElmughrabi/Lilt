# UI polish proposal and checkpoint commits

25 October 2026. The initial four local checkpoint commits below preceded the
subsequently authorized and publisher-accepted UI polish. Settings is recorded in
`d10396ba4944`, reading room in `a79eaee9b62c`, player in `03d50acdab1c`, and
the later waveform amendment in `47fb00ae110e`. The original proposal below
retains its design/verification scope; implementation is complete. Final combined
verification passed 24 UI cases with no failures/skips. The matching zero-error/
warning Svelte check and production build were reused. See
`.tmp/ui-polish-commits-20261025-f83a6d2b/REPORT.md` for reconciliation and limits.
Existing release requirements remain separate.

## Checkpoint commit record

Entry capture preserved HEAD, the index, 247 file identities and recovery copies
of all 49 changed/untracked paths before staging. Entry HEAD was
`cb58e7d37a7d80480e1d9e867443c3af36763831`;
the index had no staged changes and was SHA-256
`79a321242a1e5184fec98f16f03e8e4330633ad904f70187fc0659b750b7af4b`.
The existing untracked model-attribution document matches its frozen R04 identity.
Local commits, in order:

| Commit | Contents | Existing evidence |
| --- | --- | --- |
| `9ba38f082e5c` — `fix(ui): expose current selections and recording context` | Accepted R11 state/context metadata in App, Home and PerformanceSettings, plus its focused test. Reviewed snapshots were staged without replacing the later live welcome work. | `.tmp/r11-state-independent-20261024-58e6b1a9/REVIEW.md`: eight focused cases. |
| `abc9474c5d4a` — `refactor(audio): retire native WAV writing and deliver Eigen sources` | The 27 accepted R04 paths plus the frozen model-attribution document: PCM writer, speech publication ordering, production dependency/packaging exclusions, source collector/audit, Eigen recipe/patches and affected tests. | `.tmp/r04-live-integration-20261025-693e0ac4/REPORT.md`: exact application and eleven focused checks; consolidated independent verdict remains applicable to its frozen bytes. |
| `dc2d0ae71022` — `feat(onboarding): welcome readers and clarify voice setup` | Welcome, VoiceSetup and shared MicrosoftPrivacy components; Settings/About access; Home setup; backend welcome persistence/model download-size metadata; approved compact privacy copy and affected fixtures/tests, including the later welcome adjustment to the R11 test. | `.tmp/welcome-setup-20261024-8d3f5a21/REPORT.md` and `.tmp/welcome-privacy-copy-20261024-1f594db2/RESULT.json`. |
| This documentation checkpoint — `docs: record source checkpoint and UI polish proposal` | Current release-source-status and this plan, preserving outstanding licensing, publisher, package and installed-testing boundaries. | Existing dated reports stay unchanged. |

Staging used explicit paths, exact snapshot identities and staged diffs. Python
AST, JavaScript and JSON syntax and intended paths were checked. R11 and welcome
staged whitespace checks passed. R04 retains whitespace findings only in the two
accepted upstream Eigen patches; those bytes were preserved. Source comparisons
allow only established Git line-ending normalization. `docs/.flowstate.toml`,
personal data, models, runtimes, generated assets and ignored evidence remain
outside the commits. No push or publication is included. Existing functional
campaigns were reused within their dated scopes, without rerunning them or
claiming new combined-application acceptance solely for these commits.

The final committed/live comparison and per-commit staged trees are recorded in
`.tmp/release-checkpoint-commits-20261025-ae84d620/state.json`.

## Separate observation: VRAM after the first close

Current disposition: the publisher cancelled further work on the technical/
licensing-check item in this batch. This observation remains unresolved; the
procedure below is retained as a possible later check, not current authorization
to run it. The publisher is building the website and will provide public details
later. No site, policy, runtime or licensing operation is included here.

The publisher reports approximately 1 GB of VRAM remaining after the first app
close, although the app appears to exit normally; the first-close distinction is
not yet reproduced or explained. A later read-only snapshot found no
Violilt/Python worker and no process reported by the NVIDIA compute-app query;
total GPU usage was 1,988 MiB. There was no matching before/during baseline, so
that snapshot neither attributes the remaining usage to Violilt nor disproves
the reported behavior.

Source already has manual memory release and worker termination during normal
close. Normal close waits up to three seconds without an explicit final
worker-exit check. This is a validation gap, not proof of the reported cause.
Do not label the issue fixed, introduce a required manual eject step, or change
shutdown code as part of the visual polish.

When undertaking the focused runtime check, record the same GPU/process counters
before launch, during GPU narration, after the first close, and after a second
launch/close. Track the app's worker PID and nearby readings after exit, and keep
other GPU workloads comparable. If attribution shows a surviving worker or a
repeatable app-related allocation, scope a functional fix and its shutdown tests
separately. This unresolved observation remains visible in the checkpoint; it
does not expand the current planning task into an automatic app/inference run.

## What the screenshots show

Settings has inconsistent text sizes and spacing, several explanations beneath
each control, overly long control rows, and duplicate memory-related status text.
The source confirms 10px shared toggle labels, 8px helper text, 9px Settings hints,
and no dedicated gap between the help-card heading and its action row. The first
polish should focus on this screen; a whole-app restyle would broaden its impact.

## Proposed Settings polish

1. **Clear groups.** Keep existing functionality, with visible sections for voice
   setup, processing/speed test, listening, voice memory, reusable audio,
   appearance, storage, and help/privacy. Put help/privacy toward the end of
   Settings; first-use access remains in the existing welcome. Avoid introducing
   nested tabs or hiding everyday controls behind advanced modes.
2. **Readable rows.** Aim for 13–14px control labels and 12px explanatory text,
   with comfortable line height and adequate contrast in both palettes. Use a
   consistent spacing scale: roughly 8px within related content, 16–20px between
   rows, and 24px between groups. Preserve the current brand colors and serif
   headings. Constrain Settings CSS so shared Reading-room controls are not
   unintentionally resized.
3. **Less repeated copy.** Use direct section names such as “Processing,”
   “Listening,” and “Voice memory.” Remove decorative subtitles such as “A little
   guidance, whenever you need it.” Keep a short helper only when it explains a
   consequence or tradeoff. Combine the preparation/release explanations into
   one concise memory note; show one current memory-status line. Keep important
   failure, safety, data-retention and model-download information available.
4. **Aligned controls.** On wider windows, align labels and related controls in
   consistent rows with sensible select widths. Stack them on narrow windows.
   Keep cache usage beside its limit/action and maintain distinct destructive
   actions. Add a clear gap between card headings and buttons, including the
   help/privacy card shown in the screenshot.
5. **Calm feedback.** Refine existing hover, keyboard-focus, pressed, loading,
   disabled, completion and error states. Add brief opacity/color/transform
   transitions, approximately 120–180ms, where they help explain an action.
   Reuse real preparation, release, benchmark and cache outcomes. Show success
   only after the existing operation acknowledges it; preserve visible errors.
   Avoid extra toasts for every toggle, artificial progress, layout jumps,
   repeated decorative motion or changes to action timing.
6. **Motion preferences.** Preserve `prefers-reduced-motion`; state changes must
   remain clear with animation disabled. Feedback must not steal focus or move
   controls while someone is using them.

This batch changes presentation and concise nonlegal helper copy. Preserve the
approved privacy disclosures/links, control values, handlers, settings persistence,
API contracts, native dialogs, model trust/downloads, audio generation, GPU runtime
and storage semantics. A discovered functional defect is a separately described
fix with the corresponding tests, rather than an implicit expansion of polish.

## Implementation sequence if approved

1. Use the completed checkpoint above and capture before screenshots.
2. Implement the Settings layout/copy/spacing as one coherent candidate. Review
   screenshots before adding subtle feedback transitions to that same candidate.
3. Verify the finished candidate once with the focused checks below. Correct only
   concrete findings, then repeat checks affected by those corrections.
4. Present before/after screenshots and the validation result for publisher review.
   Record the accepted polish separately in Git. The final normal app-flow pass
   follows the finished UI; packaging remains later in the release sequence.

## Proportionate verification

- Run the frontend type/Svelte check and production build on the final candidate.
- Reuse affected existing Settings/preset/theme/state, welcome/reopen and privacy
  access checks. Run keyboard/focus cases touched by changed markup. Preserve
  behavioral assertions when updating intentional copy or layout selectors.
- Check both palettes in light and dark appearance at normal desktop and
  narrow/short sizes, including scroll reachability, wrapped text, focus outlines,
  control clipping and the player/footer. Check text scaling and reduced motion.
- Exercise real UI fixture states: idle, busy, preparing, releasing, benchmark
  progress/failure, cache unavailable, and successful/failed actions. Add only
  missing behavioral coverage warranted by new feedback; avoid tests that merely
  mirror CSS values or animation durations.
- Because shared App markup and Settings actions are involved, include a short
  source-app smoke pass for opening Settings, saving/reopening preferences,
  CPU/NVIDIA selection and returning to a reading. Existing audio correctness
  suites need rerunning only if their code/inputs change or a relevant failure
  appears. Real CPU/NVIDIA flow and final installed-package/other-machine testing
  remain necessary in their planned release scopes.

Acceptance: Settings is easier to scan, the tiny helper-text pattern is removed,
actions and statuses stay truthful, controls remain keyboard accessible, and the
focused checks pass with no unintended product behavior change. No full-suite
rerun is proposed solely for these visual edits.
