# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['heic_to_jpg_converter.py'],
    pathex=[],
    binaries=[],
    datas=[('Converters.ico', '.')],
    hiddenimports=['opencv-python', 'numpy', 'pillow_heif', 'PyQt6', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt6.QtSql', 'PyQt6.QtNetwork', 'PyQt6.QtDBus'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='heic_to_jpg_converter',
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
    icon=['Converters.ico'],
)
