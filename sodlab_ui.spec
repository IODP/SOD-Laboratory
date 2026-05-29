# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['workflows\\sodlab_ui.py'],
    pathex=[],
    binaries=[],
    datas=[('workflows/settings.json', '.'), ('C:\\Users\\vpercuoco\\Anaconda3\\envs\\sod\\Lib\\site-packages\\gradio_client', 'gradio_client'), ('C:\\Users\\vpercuoco\\Anaconda3\\envs\\sod\\Lib\\site-packages\\gradio', 'gradio'), ('C:\\Users\\vpercuoco\\Anaconda3\\envs\\sod\\Lib\\site-packages\\safehttpx', 'safehttpx')],
    hiddenimports=[],
    hookspath=['hooks'],
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
    name='sodlab_ui',
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
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='sodlab_ui',
)
