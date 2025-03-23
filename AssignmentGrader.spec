# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['grader_gui.py'],
    pathex=[],
    binaries=[('chromedriver.exe', '.')],
    datas=[('my_first_website_grader.py', '.'), ('utilities.py', '.'), ('auto_canvas.py', '.'), ('dungeon_grader.py', '.'), ('test_part_2_grader.py', '.'), ('my_first_webpage_grader.py', '.'), ('my_second_webpage_grader.py', '.')],
    hiddenimports=['bs4', 'selenium', 'pandas', 'pygetwindow'],
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
    a.binaries,
    a.datas,
    [],
    name='AssignmentGrader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
