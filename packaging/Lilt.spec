from pathlib import Path
from PyInstaller.utils.hooks import collect_all, copy_metadata

root = Path(SPECPATH).parent
datas = [(str(root / 'frontend' / 'dist'), 'frontend/dist'),
         (str(root / 'examples'), 'examples'),
         (str(root / 'assets' / 'lilt.ico'), 'assets')]
binaries = []
hiddenimports = ['backend.speech', 'backend.documents', 'backend.server']
for package in ('kokoro_onnx', 'espeakng_loader', 'phonemizer', 'pythonnet', 'clr_loader'):
    package_data, package_binaries, package_imports = collect_all(package)
    datas += package_data
    binaries += package_binaries
    hiddenimports += package_imports
datas += copy_metadata('kokoro-onnx')

a = Analysis([str(root / 'main.py')], pathex=[str(root)], binaries=binaries, datas=datas,
             hiddenimports=hiddenimports, hookspath=[], hooksconfig={}, runtime_hooks=[],
             excludes=['PyQt5', 'PyQt6', 'PySide6', 'tkinter', 'matplotlib', 'IPython'], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='Lilt', debug=False,
          bootloader_ignore_signals=False, strip=False, upx=False, console=False,
          icon=str(root / 'assets' / 'lilt.ico'))
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='Lilt')
