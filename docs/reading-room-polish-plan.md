# Reading-room polish proposal

25 October 2026. Implemented and accepted by the publisher: reading-room
checkpoint `a79eaee9b62c`, with the later approved thin waveform amendment
`47fb00ae110e`. Settings preceded it and the player followed. The original plan
below retains its intended boundaries; no additional implementation is pending.
The coordinator reconciled the final combined source/build/assets and ran 24
focused UI cases, all passing without failures/skips. See
`.tmp/ui-polish-commits-20261025-f83a6d2b/REPORT.md` and the original
`.tmp/reading-room-polish-20261025-b7a31e92/REPORT.md` for exact evidence scopes.

## Original starting point and order

The committed checkpoint is `74ebde196d432780941c037475a92a30dd56c89a`.
The Settings chat has returned an uncommitted candidate, recorded in
`.tmp/settings-polish-20261025-80d5f6c0/REPORT.md`. Preserve it and review it before
the next source batch. This plan follows Settings; the
[audio-player plan](audio-player-polish-plan.md) follows this one. All three touch
App/styles, so avoid simultaneous edits to those files. Each accepted batch gets
its own checkpoint; capture the actual current inputs before implementation.

## Outcome

Make voice selection, narration options and generation easy to scan, with a
clear primary action and readable feedback. Keep the current reading-room
identity, document presentation, and existing behavior.

## Proposed changes

1. **Simpler voice panel.** Use a direct heading such as “Voice & narration.”
   Reduce the competing eyebrow, two-line introduction and decorative voice-art
   block. Keep the artwork as a smaller accent where space permits, with less
   decoration on short windows so the controls remain reachable.
2. **Readable controls.** Aim for 13–14px labels and 12px supporting text, clear
   spacing, aligned values and visible keyboard focus. Existing narrator labels
   reach 7px, supporting metadata 9px and generation footnotes 8px. Preserve voice
   names, accents and the existing voice list; make the chosen voice obvious.
   Keep the sample action secondary and separate from full narration.
3. **Clear grouping.** Group Voice/sample, Narration speed, Reading options and
   Processing. Retain Read code blocks, paragraph pause, all processing presets
   and the Settings shortcut. Remove decorative/repeated helper lines; retain
   explanations of actual consequences. Keep “Narration speed” distinct from the
   player's “Playback speed.”
4. **Primary action and progress.** Keep “Create your audio” as the primary idle
   action, with readable estimated duration. Retain the missing-model setup path.
   While active, clearly distinguish preparing, generating, saving and stopping;
   show existing section progress and ready-audio information. Keep Stop generation
   easy to find and preserve its after-current-section behavior. Make secondary
   performance metrics quieter while keeping the existing native Performance
   details disclosure and all pronunciation/error warnings accessible.
5. **Reading workspace.** Improve Read/Edit/Spoken button readability and selected
   state, toolbar spacing, metadata and the existing save-status presentation.
   Preserve the current prose width, content hierarchy, editor behavior and Find
   functionality. Do not report a save as complete before the existing save state
   acknowledges it.
6. **Restrained feedback.** Use brief approximately 120–180ms color/opacity or
   small control transitions, matching Settings. Preserve reduced motion and
   avoid reflow, decorative loops, fabricated progress or animation of the reading
   text. Loading/disabled/error states must remain understandable without motion.

## Boundaries

Expected edits are the reading-room markup in `frontend/src/App.svelte` and scoped
rules in `frontend/src/styles.css`, plus affected UI fixtures if warranted. Keep
Settings and the player candidate intact; scope selectors to the studio/voice
panel rather than changing shared toggle, hint or button rules globally.

Preserve script handlers, settings values/bindings, voice-popup keyboard/focus
restoration, selected/pressed semantics, editor autosave/normal close, document
sanitization, original Markdown, narration generation, model/download trust,
CPU/NVIDIA behavior and storage. No dependency/backend changes, new product
features, real inference or packaging are part of this visual pass. A functional
defect is described and scoped separately. The unresolved first-close VRAM
observation remains outside this work.

## Verification and handback

- Capture before/after screenshots with identical fixture content. Check both
  palettes in light/dark, 1440×960 and the supported minimum 1024×720, plus a
  narrower fixture for wrapping and shelf/voice-panel reachability. Check enlarged
  text and reduced motion; record actual Windows scaling separately if available.
- Run frontend Svelte/type checks and the production build on the final candidate.
  Reuse affected Read/Edit/Spoken and preset state cases from
  `tests/test_state_context_accessibility.cjs`, voice-popup/focus cases from
  `tests/test_modal_popup_keyboard.cjs`, and relevant Space/native-details cases
  from `tests/test_keyboard_accessibility.cjs`. Include editor/save cases from
  `tests/test_editor_save.cjs` only where changed markup or a finding affects them.
- Exercise synthetic missing/ready model, empty reading, starting, preparing,
  generating, assembling, cancelling and error/warning states. Verify one action
  per activation, retained disabled conditions, preset synchronization and no
  unintended speech while merely choosing controls. Add only meaningful missing
  state/interaction coverage; retain behavioral assertions when changing copy.
- Confirm the accepted Settings layout and existing player remain usable after
  the build. Do not repeat unaffected audio/runtime campaigns just for styling.
  A native smoke check may use disposable data with startup preparation disabled;
  real narration and installed-package tests retain their later release scopes.

Return changed paths/identities, before/after previews, actual commands/results
and remaining limitations in one ignored report. Leave the candidate uncommitted
for review; checkpoint an accepted result before beginning player edits.

Acceptance: controls fit and remain reachable, primary/secondary actions are
clear, tiny helper-text clutter is reduced, genuine progress/errors remain
visible, keyboard/focus behavior is preserved, and affected checks pass.
