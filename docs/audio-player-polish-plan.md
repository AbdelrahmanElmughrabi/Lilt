# Audio-player polish proposal

25 October 2026. Implemented after Settings and the
[reading-room pass](reading-room-polish-plan.md), and accepted by the publisher.
Player checkpoint: `03d50acdab1c`; later decorative header amendment:
`47fb00ae110e`. The original proposal below retains its intended boundaries;
no further player implementation is pending. The coordinator verified preserved
handlers/player core and final combined source/build/assets, with 24 focused UI
cases passing and no failures/skips. See
`.tmp/ui-polish-commits-20261025-f83a6d2b/REPORT.md` and the original
`.tmp/audio-player-polish-20261025-928f4b6c/REPORT.md` for scope and limitations.

## Outcome

Make playback controls and timing comfortable to read, communicate genuine
buffering clearly, and retain access to controls in compact windows. Preserve
the existing audio engine, timing, buffering and saved listening position.

## Proposed changes

1. **Clear control hierarchy.** Keep the central Play/Pause action prominent with
   balanced Back/Forward 10 seconds controls and larger usable hit areas. Improve
   the current 33px play button and unpadded secondary icon targets without making
   the footer dominate the reading. Retain familiar icons, native buttons, visible
   keyboard focus and disabled states.
2. **Readable timing and seeking.** Raise the existing 8px time labels toward
   12px, keep tabular numbers and reserve enough width for long recordings. Make
   the native seek control easier to target, with a visible thumb/focus state and
   useful accessible value text. Preserve the exact seek values, step, bounds
   and saved-position behavior; do not animate or interpolate the actual time or
   thumb value.
3. **Honest playback status.** Use concise existing states such as “Voice preview,”
   “Buffering…” and an accurate amount of audio available/decoded ahead. Keep
   the ability to pause requested playback while it is buffering. During streaming,
   `StreamPlayer` reports available audio as duration, not estimated full length;
   clarify that in presentation without changing the duration source or implying
   the recording is finished. Completed recordings retain their actual duration.
   Do not add percentage bars, fake wait estimates or a second loading model.
4. **Clear secondary controls.** Improve track-title/voice metadata, playback-rate
   readability, the volume slider and export state. Keep “Playback speed” visibly
   or accessibly identified so it cannot be confused with narration speed. Retain
   the existing speed-cycle values and completed-recording export restriction.
   Long titles should wrap or truncate gracefully while their full identity stays
   available; keep pronunciation warnings discoverable.
5. **Compact layout.** Use a balanced desktop layout and wrap the footer into a
   compact second row when necessary. At the supported 1024×720 minimum, keep
   seeking, speed, volume and export reachable. For narrower/scaled layouts,
   prefer wrapping over the current rule that hides the whole secondary-control
   region. Do not add a new overflow-menu interaction or cover the reading,
   primary generation action, dialogs or toast messages.
6. **Subtle feedback.** Match the other polish passes with brief color/opacity
   transitions for control states and genuine buffering indication. Preserve
   reduced motion and clear static labels. Keep status changes stable and avoid
   announcing the clock or continuously updating buffered seconds through a live
   region; any live announcement should describe an actual state transition.

## Boundaries

Expected edits are the footer markup in `frontend/src/App.svelte` and scoped
player rules in `frontend/src/styles.css`, plus meaningful presentation/interaction
fixtures. No queue, waveform, mute, repeat, new playback mode or other feature is
included. Preserve the Settings/reading-room candidates, themes and welcome/privacy
surfaces; account for the footer's presence on every app page.

Keep `frontend/src/stream-player.ts` unchanged, including scheduling, prefetch,
buffer thresholds, pause offsets, clock and disposal. Preserve App's existing
selection, Play/Pause, seek, volume, speed, audio event and position-persistence
handlers, user-activation/autoplay rules and global shortcut/modal protections.
Do not smooth over an engine fault in presentation. Unexpected audio behavior is
a separate functional issue with its own checks. No backend/runtime/model changes,
actual model download/inference, VRAM reproduction or package operation belongs
to this visual batch.

## Verification and handback

- Run frontend Svelte/type checks and a production build on the final candidate.
  Compare preserved player-engine/handler identities and review any necessarily
  changed accessible labels without weakening their behavioral assertions.
- Use built-UI fixtures with controlled media/clock state for empty player,
  voice preview, paused/playing saved audio, streaming audio, buffering, resumed
  availability, completion and playback failure. Check seeking/clamping, skip
  controls, speed/volume dispatch, export availability and saved-position calls.
  Verify each real activation invokes the intended action once.
- Reuse relevant playback Space and native-button cases from
  `tests/test_keyboard_accessibility.cjs` and modal/popup shortcut protections from
  `tests/test_modal_popup_keyboard.cjs`. Add only genuinely missing player UI
  coverage. `tools/stream-player-check.cjs` is an existing deterministic scheduler
  check if an engine-boundary concern appears; unchanged core code does not require
  its wholesale rerun solely for layout. `tools/streaming-ui.cjs` drives native
  GPU narration and is not a harmless visual-only fixture; do not run it as a
  substitute for focused checks in this batch.
- Inspect before/after screenshots on Home, reading room and Settings, both
  palettes/light/dark, normal and minimum desktop sizes, narrow/short fixtures,
  enlarged text and reduced motion. Check long titles and hour-scale timestamps,
  native range-key behavior, visible focus and secondary-control reachability.
  Distinguish browser text enlargement from actual Windows DPI/scaling coverage.
- Reuse unaffected audio correctness results. Real CPU/NVIDIA playback, device
  behavior and installed-package/other-machine tests remain later release gates.

Return one ignored report with exact changed paths/identities, before/after
previews, commands/results and precise limitations. Leave the finished candidate
uncommitted for review, then checkpoint the accepted player separately.

Acceptance: playback/time/control states are easier to understand and operate,
compact layouts retain the necessary controls, motion is optional, and focused
tests show unchanged playback command and persistence behavior.
