# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

datas = []
datas += collect_data_files('bookocr')


block_cipher = None


a_c = Analysis(
    ['mainc.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz_c = PYZ(a_c.pure, a_c.zipped_data, cipher=block_cipher)
exe_c = EXE(
    pyz_c,
    a_c.scripts,
    [],
    exclude_binaries=True,
    name='mainc',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)


a_w = Analysis(
    ['mainw.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz_w = PYZ(a_w.pure, a_w.zipped_data, cipher=block_cipher)
exe_w = EXE(
    pyz_w,
    a_w.scripts,
    [],
    exclude_binaries=True,
    name='mainw',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)


coll = COLLECT(
    exe_c,
    a_c.binaries,
    a_c.zipfiles,
    a_c.datas,

    exe_w,
    a_w.binaries,
    a_w.zipfiles,
    a_w.datas,

    strip=False,
    upx=True,
    upx_exclude=[],
    name='bookocr-app',
)