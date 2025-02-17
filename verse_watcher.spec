# -*- mode: python ; coding: utf-8 -*-

import sys
from os import path

block_cipher = None

# Add any additional data files here
added_files = [
    ('vw.ico', '.'),
    ('vw-logo.png', '.'),
    ('README.md', '.'),
    ('requirements.txt', '.')
]

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'win32gui',
        'win32con',
        'win32api',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.sip',
        'watchdog.observers',
        'watchdog.events'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Keep necessary Qt plugins and translations
a.datas = [d for d in a.datas if not (
    d[0].startswith('PyQt5/Qt/translations/qtbase_') or
    '.qm' in d[0]
) or d[0].startswith('PyQt5/Qt/translations/qtbase_en')]

# Keep only necessary Qt plugins
a.binaries = [b for b in a.binaries if not (
    b[0].startswith('Qt5WebEngine') or
    b[0].startswith('Qt5Quick') or
    b[0].startswith('Qt5Qml') or
    b[0].startswith('Qt5Network')
)]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='VerseWatcher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='vw.ico',
    version='file_version_info.txt'
) 