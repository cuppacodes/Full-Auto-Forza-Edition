# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('C:\\Users\\The white wolf\\Downloads\\New APP\\app_lang.py', '.'), ('C:\\Users\\The white wolf\\Downloads\\New APP\\config.py', '.'), ('C:\\Users\\The white wolf\\Downloads\\New APP\\capture.py', '.'), ('C:\\Users\\The white wolf\\Downloads\\New APP\\race.py', '.'), ('C:\\Users\\The white wolf\\Downloads\\New APP\\mastery.py', '.'), ('C:\\Users\\The white wolf\\Downloads\\New APP\\main_window.py', '.'), ('C:\\Users\\The white wolf\\Downloads\\New APP\\setup_panel.py', '.'), ('C:\\Users\\The white wolf\\Downloads\\New APP\\log_widget.py', '.')]
binaries = []
hiddenimports = ['customtkinter', 'PIL', 'PIL.Image', 'asyncio', 'asyncio.base_events', 'asyncio.events', 'asyncio.futures', 'asyncio.tasks']
tmp_ret = collect_all('customtkinter')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['forza_app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='FAFE',
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
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='FAFE',
)
