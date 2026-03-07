# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files

project_root = Path(SPECPATH)

customtkinter_datas = collect_data_files("customtkinter")

bin_datas = []
for binary_name in ("chromedriver.exe", "ffmpeg.exe"):
    binary_path = project_root / "bin" / binary_name
    if binary_path.exists():
        bin_datas.append((str(binary_path), "bin"))

datas = customtkinter_datas + bin_datas


a = Analysis(
    ["main.py"],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=["telebot", "telebot.apihelper"],
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
    name="VKMusicSaver",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="VKMusicSaver",
)
