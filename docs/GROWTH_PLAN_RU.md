# Growth Plan (RU)

## Цель

Поднять видимость репозитория за счет дистрибуции (релиз), визуальной упаковки (README) и внешнего трафика (посты/статьи).

## Weekend checklist

1. Выпустить релиз `v1.0.0`
- Обновить версию в `resources/app.default.toml` и при необходимости в `pyproject.toml`.
- Создать git tag `v1.0.0` и отправить его в origin.
- Проверить, что GitHub Action `release.yml` прикрепил `MusicSaver-windows.zip` к релизу.

2. Упаковать README
- Добавить `docs/media/demo.gif`.
- Добавить 3 скриншота: `dashboard.png`, `downloader.png`, `settings.png`.
- Проверить, что ссылка `../../releases/latest` открывает релиз в GitHub UI.

3. Получить первый внешний трафик
- Публикация на Пикабу с упором на боль пользователя и готовый `.exe`.
- Техническая статья на Хабре с архитектурой и ограничениями.
- Пост в DTF/VC.ru про бэкап личной медиатеки.

4. Расширить discoverability на GitHub
- Добавить topics: `yandex-music-downloader`, `vk-music-downloader`, `mp3-downloader`, `gui`, `telegram-bot`, `id3-tag-editor`.
- Добавить 2 issue с лейблами `good first issue` и `help wanted`.

## Templates

### Release notes short template

```
## Music Saver v1.0.0

### Added
- Windows build in release assets.
- Improved README with demo and screenshots.

### Notes
- If VK/Yandex integration breaks after platform updates, open an issue with steps to reproduce.
```

### Pikabu/Habr angle

- Проблема: каталоги и доступность контента меняются.
- Решение: локальная библиотека с тегами и обложками.
- Доказательство: GIF + скриншоты + короткий roadmap.
