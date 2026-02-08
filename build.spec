# -*- mode: python ; coding: utf-8 -*-

import os
import customtkinter

block_cipher = None

customtkinter_path = os.path.dirname(customtkinter.__file__)

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[
        ('external/whisper.exe', 'external'),
        ('external/*.dll', 'external'),
    ],
    datas=[
        ('assets/*.ico', 'assets'),
        ('config.json', '.'),
        (customtkinter_path, 'customtkinter'),
    ],
    hiddenimports=[
        'pynput.keyboard._win32',
        'pynput.mouse._win32',
        'pystray._win32',
        'plyer.platforms.win.notification',
        'model_manager',
        'config',
        'utils',
        'overlay',
        'settings_window',
        'hotkey_manager',
        'audio_recorder',
        'transcriber',
        'transcriber_api',
        'keyboard_injector',
        'main_logic',
        'updater',
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
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='VoiceTyper',
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
    icon='assets/icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VoiceTyper',
)
