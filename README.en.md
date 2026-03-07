# VK Music Saver

<div align="center">

### 🎵 Desktop app for downloading music from VK

A local Python tool with a CustomTkinter UI, automated tagging, and download history storage.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![CustomTkinter](https://img.shields.io/badge/UI-CustomTkinter-1F6FEB?style=for-the-badge)
![Selenium](https://img.shields.io/badge/Automation-Selenium-43B02A?style=for-the-badge&logo=selenium&logoColor=white)
![SQLite](https://img.shields.io/badge/Storage-SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Mutagen](https://img.shields.io/badge/Tags-Mutagen-7B68EE?style=for-the-badge)
![Requests](https://img.shields.io/badge/HTTP-Requests-222222?style=for-the-badge)
![Telegram Bot API](https://img.shields.io/badge/Integration-Telegram%20Bot%20API-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)
![Yandex Music](https://img.shields.io/badge/Integration-Yandex%20Music-FFCC00?style=for-the-badge&logo=yandex&logoColor=black)
![PyInstaller](https://img.shields.io/badge/Build-PyInstaller-FF6B35?style=for-the-badge)
![Desktop](https://img.shields.io/badge/App-Desktop-3B82F6?style=for-the-badge)
![Windows](https://img.shields.io/badge/OS-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)
![Local First](https://img.shields.io/badge/Mode-Local%20First-16A34A?style=for-the-badge)
![Tagging](https://img.shields.io/badge/ID3-Tagging-9333EA?style=for-the-badge)
![Music Library](https://img.shields.io/badge/Use%20Case-Music%20Library-EC4899?style=for-the-badge)
![VK](https://img.shields.io/badge/Source-VK-2787F5?style=for-the-badge&logo=vk&logoColor=white)
![Yandex](https://img.shields.io/badge/Source-Yandex-FF0000?style=for-the-badge&logo=yandex&logoColor=white)

</div>

<p align="center">
	<a href="./README.ru.md">Русская версия</a>
</p>

---

## What this project does

`VK Music Saver` downloads tracks from VK in a desktop workflow with metadata, cover art, and local history.

The project is built for a practical “launch and use” flow: graphical UI, modular architecture, and built-in service configuration.

## Key features

- Music downloading from VK via Selenium automation.
- ID3 tagging support (artist, title, album, cover art).
- Local SQLite database for tracking downloaded tracks.
- Layered architecture: UI, domain logic, services, and database.
- Additional services for Telegram and Yandex scenarios in the project.

## Requirements

- Python `3.10+`
- Google Chrome (latest version recommended)
- Dependencies listed in `requirements.txt`

## Quick start

```bash
python -m venv .venv
# Windows
.\.venv\Scripts\activate

pip install -r requirements.txt
python main.py
```

## Project structure

```text
src/
├─ app_controller.py        # application orchestration
├─ ui/                      # windows, views, and UI components
├─ services/                # business services (VK, Telegram, Yandex, download)
├─ domain/                  # models and tagger
├─ database/                # SQLite manager and repositories
└─ utils/                   # logging and helper utilities
```

## Build

The standalone build uses a `PyInstaller` spec:

- `vk_music_saver.spec`
- `build.ps1`
