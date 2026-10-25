"""Canonical isolated English pronunciation build for this branch."""
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, copy_metadata

root = Path(SPECPATH).parent
datas = [(str(root / 'frontend' / 'dist'), 'frontend/dist'),
         (str(root / 'examples'), 'examples'),
         (str(root / 'assets' / 'violilt.ico'), 'assets'),
         (str(root / 'assets' / 'desktop-api.js'), 'assets'),
         (str(root / 'backend' / '_vendor' / 'kokoro' / 'config.json'), 'backend/_vendor/kokoro')]
binaries = []
hiddenimports = ['backend.speech', 'backend.documents', 'backend.server',
                 'misaki.en', 'misaki.token', 'misaki.data', 'en_core_web_sm']
datas += collect_data_files('misaki', includes=['data/us_gold.json', 'data/us_silver.json',
                                             'data/gb_gold.json', 'data/gb_silver.json'])
datas += collect_data_files('en_core_web_sm')
datas += collect_data_files('pythonnet', includes=['runtime/*'])
datas += collect_data_files('clr_loader', includes=['ffi/dlls/**/*.dll'])
binaries += collect_dynamic_libs('pythonnet')
binaries += collect_dynamic_libs('clr_loader')
for package in ('misaki', 'spacy', 'thinc', 'regex', 'addict', 'numpy', 'en-core-web-sm', 'num2words', 'pypdf'):
    datas += copy_metadata(package)

excludes = ['soundfile', '_soundfile', '_soundfile_data', 'tools', 'tests', 'kokoro_onnx', 'phonemizer', 'phonemizer_fork', 'espeakng_loader',
            'misaki.espeak', 'misaki.cutlet', 'misaki.he', 'misaki.ja', 'misaki.ko',
            'misaki.vi', 'misaki.zh', 'misaki.zh_frontend', 'misaki.g2pkc',
            'misaki.vi_cleaner', 'misaki.zh_normalization',
            'torch', 'transformers', 'spacy_curated_transformers', 'curated_transformers',
            'cupy', 'tensorflow', 'jax', 'PyQt5', 'PyQt6', 'PySide6', 'tkinter',
            'matplotlib', 'IPython', 'pythonnet._pyinstaller', 'webview.__pyinstaller',
            'PyInstaller.utils', 'setuptools._vendor.autocommand',
            'spacy.tests', 'thinc.tests', 'numpy.tests']
a = Analysis([str(root / 'main.py')], pathex=[str(root)], binaries=binaries, datas=datas,
             hiddenimports=hiddenimports, hookspath=[], hooksconfig={}, runtime_hooks=[],
             excludes=excludes, noarchive=False,
             module_collection_mode={'num2words': 'py', 'certifi': 'py', 'tqdm': 'py'})
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='Violilt', debug=False,
          bootloader_ignore_signals=False, strip=False, upx=False, console=False,
          icon=str(root / 'assets' / 'violilt.ico'))
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='Violilt')
