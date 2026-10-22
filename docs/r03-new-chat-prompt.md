# Prompt for a new R-03 continuation chat

```text
Read C:\Users\fireball\OneDrive\Desktop\LiltTTS\docs\r03-paused-handoff-2026-10-22.md
and the reports, evidence and current pause-checkpoint manifest it links.

R-03 implementation was paused. Start with read-only review and report before
implementing or running new diagnostic/test batches. Explain the established
changes, exact remaining blockers, known/unknown causes and the smallest useful
next investigation. Follow trace → plan → apply/validate/record after I direct
the next implementation batch. Do not treat this document as permission to resume
changes, install dependencies, build/install an EXE/MSIX or publish anything.

The unresolved issues are actual Windows Expat 2.8.5 versus expected 2.9.0 security
coverage; intermittent WinError 145 temporary-folder cleanup errors; and an
intermittent GPU-counter closed.wait(1) failure. Some suites passed and others
failed: retain both, distinguish ordinary runs from corrected diagnostic runs,
and do not assume a new-runtime regression or harmless test flakiness. Proposed
Expat CVE dispositions still need independent acceptance. One initial diagnostic
runner was invalid because it lacked a multiprocessing main guard; don't use that
attempt as baseline evidence.

OneDrive functionality is DISABLED; the folder name does not mean it is syncing.
Do not spend time blaming or troubleshooting OneDrive. The earlier manifest
omitted build.ps1; use the new handoff-checkpoint manifest and retain this limit
when interpreting previous verification claims.

Preserve all uncommitted/untracked work, existing environments, source/assets and
original evidence. No dependency installation, commits/destructive Git, personal
data access, model downloads, package operations, publication or other-chat
messages. The backup requirement is waived. Do not weaken assertions, suppress
cleanup errors or repeatedly rerun full suites merely to obtain green results.

Keep source verification, final frozen payload, installed MSIX, licensing/privacy
and Store certification separate. Testing the actual final MSIX on another machine
before release is mandatory. Existing artifacts predate the current refinements
and R-03 changes. Recommend what should be resolved before using a new EXE/MSIX
as the final candidate, without claiming exploratory package tests are impossible.
```
