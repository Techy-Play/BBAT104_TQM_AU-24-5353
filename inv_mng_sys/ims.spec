# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all
from pathlib import Path

block_cipher = None

# Collect all customtkinter assets, themes, and hidden imports
ctk_datas, ctk_binaries, ctk_hiddenimports = collect_all('customtkinter')

datas = [
    ('app_icon.ico', '.'),
    ('app_icon.png', '.'),
] + ctk_datas

hiddenimports = [
    'sqlite3',
    'darkdetect',
    'PIL',
    'PIL._tkinter_finder',
] + ctk_hiddenimports

a = Analysis(
    ['run.py'],
    pathex=['.'],
    binaries=ctk_binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pytest', 'unittest'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='InventoryManagementSystem',
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
    icon='app_icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='InventoryManagementSystem',
)
