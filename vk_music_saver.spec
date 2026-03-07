# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files

project_root = Path(SPECPATH)

customtkinter_datas = collect_data_files("customtkinter")

# ffmpeg is auto-downloaded at runtime by BinaryManager.
# If you want to bundle it anyway (for offline installs),
# place ffmpeg.exe into bin/ before building.
bin_datas = []
ffmpeg_path = project_root / "bin" / "ffmpeg.exe"
if ffmpeg_path.exists():
    bin_datas.append((str(ffmpeg_path), "bin"))

datas = customtkinter_datas + bin_datas

icon_path = project_root / "resources" / "VKMusicSaver.ico"

# Добавляем папку resources, чтобы иконка была доступна и внутри запущенного приложения
if (project_root / "resources").exists():
    datas.append((str(project_root / "resources"), "resources"))

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

exe_kwargs = {
    "exclude_binaries": True,
    "name": "VKMusicSaver",
    "debug": False,
    "bootloader_ignore_signals": False,
    "strip": False,
    "upx": True,
    "console": False,
    "disable_windowed_traceback": False,
}

if icon_path.exists():
    exe_kwargs["icon"] = str(icon_path)

exe = EXE(
    pyz,
    a.scripts,
    [],
    **exe_kwargs,
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
