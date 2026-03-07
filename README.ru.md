# VK Music Saver

<div align="center">

### 🎵 Desktop-приложение для загрузки музыки из VK

Локальный инструмент на Python с интерфейсом на CustomTkinter, автоматическим теггингом и хранением истории загрузок.

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
	<a href="./README.en.md">English version</a>
</p>

---

## Что делает проект

`VK Music Saver` помогает скачивать треки из VK в удобном desktop-формате: с сохранением метаданных, обложек и локальной историей.

Проект ориентирован на сценарий «запустил и работаешь»: графический интерфейс, модульная архитектура и настройка через встроенные сервисы.

## Ключевые возможности

- Загрузка музыки из VK через Selenium-автоматизацию.
- Обработка ID3-тегов (исполнитель, название, альбом, обложка).
- Локальная база SQLite для учёта загруженных треков.
- Разделённая архитектура: UI, доменная логика, сервисы, база данных.
- Дополнительные сервисы для Telegram и Яндекс-сценариев в составе проекта.

## Требования

- Python `3.10+`
- Google Chrome (актуальная версия)
- Зависимости из `requirements.txt`

## Быстрый старт

```bash
python -m venv .venv
# Windows
.\.venv\Scripts\activate

pip install -r requirements.txt
python main.py
```

## Структура проекта

```text
src/
├─ app_controller.py        # оркестрация приложения
├─ ui/                      # окна, представления и компоненты интерфейса
├─ services/                # бизнес-сервисы (VK, Telegram, Yandex, загрузка)
├─ domain/                  # модели и теггер
├─ database/                # SQLite-менеджер и репозитории
└─ utils/                   # логирование и вспомогательные утилиты
```

## Сборка

Для сборки standalone-версии используется `PyInstaller`-спека:

- `vk_music_saver.spec`
- `build.ps1`
