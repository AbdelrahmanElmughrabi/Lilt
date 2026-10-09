"""Publish the authorized branding handoff into the user's existing Obsidian vault."""
from pathlib import Path
import re
import shutil

root = Path(__file__).resolve().parents[1]
vault = Path(r'C:\Users\fireball\OneDrive\Desktop\Obsidian Vaults\LiltTTS\LiltTTS')
if not (vault / '00 Start Here.md').is_file():
    raise RuntimeError('Expected existing project vault was not found.')
evidence = vault / 'Evidence/2026-10-08/Lilt'
reference = vault / 'Reference/2026-10-08/Lilt'
evidence.mkdir(parents=True, exist_ok=True)
reference.mkdir(parents=True, exist_ok=True)
for name in ['lilt-light.png', 'lilt-dark.png', 'classic-light.png', 'classic-dark.png', 'settings.png', 'minimum-window.png', 'about.png', 'playback.png', 'native-check.json', 'migration-check.json', 'windows-check.json']:
    shutil.copy2(root / 'artifacts/lilt-branding' / name, evidence / name)
for name in ['LILT_BRANDING.md', 'README.md', 'APP_PLAN.md']:
    shutil.copy2(root / name, reference / name)
body = (root / 'LILT_BRANDING.md').read_text(encoding='utf-8')
note = '''---
created: 2026-10-08
updated: 2026-10-08
tags: [lilt-tts, branding, project-handoff]
---

'''+body+r'''

## Current paths

```text
Project: C:\Users\fireball\OneDrive\Desktop\LiltTTS
App:     C:\Users\fireball\OneDrive\Desktop\LiltTTS\dist\Lilt\Lilt.exe
Link:    C:\Users\fireball\OneDrive\Desktop\LiltTTS\Lilt.lnk
Data:    %LOCALAPPDATA%\Lilt
```

## Screenshots

Lilt light:
![[Evidence/2026-10-08/Lilt/lilt-light.png]]

Lilt dark:
![[Evidence/2026-10-08/Lilt/lilt-dark.png]]

Palette and appearance settings:
![[Evidence/2026-10-08/Lilt/settings.png]]

Classic light / dark:
![[Evidence/2026-10-08/Lilt/classic-light.png]]
![[Evidence/2026-10-08/Lilt/classic-dark.png]]

## Continue from here

The rename/theme work is complete. Streaming, caching, performance tuning, local CPU/CUDA generation, and the faithful Markdown-reading workflow are retained. The next milestone remains a separate choice: see [[07 Roadmap and Next Session]]. Product decisions and architecture are in [[01 Product and Decisions]] and [[03 Architecture and Data Flow]]; earlier performance measurements remain in [[04 Performance and Benchmarks]].

Earlier vault notes and their original Reference snapshots preserve the pre-branding history. Use this note and the current README for current file paths, naming and appearance. Build command: `.\build.ps1 -IncludeGpu`; tests: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`.
'''
(vault / '09 Lilt Branding and Themes.md').write_text(note, encoding='utf-8')

index_path = vault / '00 Start Here.md'
index = index_path.read_text(encoding='utf-8')
index = index.replace('Snapshot of the work completed on **8 October 2026**. This vault is named **LiltTTS**; the implemented application still uses the working name **Folio**. Renaming the product has not been implemented or decided by this note.', 'Current handoff for **8 October 2026**. The product is now **Lilt**; the project and vault are **LiltTTS**. The branding/theme milestone is complete: start with [[09 Lilt Branding and Themes]] for the latest build, appearance, migration and checks.')
index = index.replace('**29 passing Python tests**', '**35 passing Python tests**')
index = index.replace(r'C:\Users\fireball\OneDrive\Desktop\TTS', str(root)).replace(r'dist\Folio\Folio.exe', r'dist\Lilt\Lilt.exe')
if '| [[09 Lilt Branding and Themes]]' not in index:
    index = index.replace('| [[08 Work Log 2026-10-08]] | Milestone history and the final handoff state |', '| [[08 Work Log 2026-10-08]] | Milestone history and the initial handoff state |\n| [[09 Lilt Branding and Themes]] | Latest rename, icon, palettes, migration, build and validation |')
index = index.replace('- Notes describe the final implementation; source snapshots also retain some historical planning language.', '- Note 09 describes the current branding implementation. Earlier notes and source snapshots retain pre-branding history; current README/branding copies are in `Reference/2026-10-08/Lilt/`.')
index_path.write_text(index, encoding='utf-8')

for name in ['01 Product and Decisions.md', '02 Features and UI.md', '03 Architecture and Data Flow.md', '06 Development and Packaging.md']:
    path = vault / name
    text = path.read_text(encoding='utf-8')
    marker = '> [!info] Branding update\n> Product name, paths, icon and themes were updated after this initial handoff. See [[09 Lilt Branding and Themes]] for the current Lilt build; the material below preserves the earlier snapshot.\n\n'
    if marker not in text:
        front_end = text.find('---', 3) + 3
        text = text[:front_end] + '\n\n' + marker + text[front_end:].lstrip('\n')
        path.write_text(text, encoding='utf-8')
roadmap = vault / '07 Roadmap and Next Session.md'
text = roadmap.read_text(encoding='utf-8')
text = text.replace('- [ ] Decide whether Folio remains the product name or becomes LiltTTS, with deliberate data migration if needed.', '- [x] Adopt **Lilt** as the product name, with supplied icon, new default palette, Classic alternative, and verified data migration; see [[09 Lilt Branding and Themes]].')
text = text.replace('- Keep Folio or adopt LiltTTS as the app name?', '- Naming is decided: **Lilt** is the app, **LiltTTS** is the project/vault.')
text = re.sub(r'> Continue the local Windows Markdown-to-speech project[^\n]+', '> Continue the local Windows Markdown-to-speech project in `'+str(root).replace('\\', r'\\')+'`. The product is Lilt. Read [[09 Lilt Branding and Themes]] and [[00 Start Here]] for the current state, then architecture/performance notes. The branding milestone is complete and has 35 passing Python tests plus native appearance, icon, migration, and GPU speech/playback checks. Preserve the existing library, CPU/CUDA behavior, section streaming/cache, and recovery. Choose the next milestone before changing scope.', text)
roadmap.write_text(text, encoding='utf-8')
log_path = vault / '08 Work Log 2026-10-08.md'
log = log_path.read_text(encoding='utf-8')
if '## Lilt branding milestone' not in log:
    log += '\n\n## Lilt branding milestone\n\nAfter the initial handoff, the user chose **Lilt** as the product name and renamed the workspace to **LiltTTS**. Implemented the supplied icon, default ivory/lilac/sage palette, optional Classic palette, independent light/dark/system appearance, portable executable/shortcut/window title, and first-launch migration with the original library retained as a backup. 35 Python checks and native appearance, persistence, contrast, minimum-window, icon-resource, real CUDA speech/playback and byte-for-byte migration checks passed. See [[09 Lilt Branding and Themes]] for current paths and evidence.\n'
    log_path.write_text(log, encoding='utf-8')
for note in vault.glob('[0-9][0-9] *.md'):
    for link in re.findall(r'\[\[([^\]]+)\]\]', note.read_text(encoding='utf-8')):
        target = link.split('|')[0].split('#')[0]
        if target and not any(p.exists() for p in [vault / target, vault / (target + '.md')]):
            raise RuntimeError(f'Broken vault link: {note.name}: {target}')
print('Updated linked branding note, project index, roadmap and work log; copied screenshots and verification evidence.')
