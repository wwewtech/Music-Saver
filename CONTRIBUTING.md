# Contributing to Music Saver

Спасибо, что хотите участвовать в проекте. Ниже — базовые правила для работы с репозиторием.

## Как сообщить об ошибке

Используйте [шаблон Bug report](.github/ISSUE_TEMPLATE/bug_report.yml) в разделе Issues. Постарайтесь указать шаги для воспроизведения, версию ОС и Chrome, и прикрепить лог из приложения если есть.

## Как предложить функцию

Откройте Issue с шаблоном [Feature request](.github/ISSUE_TEMPLATE/feature_request.yml). Опишите задачу, которую должна решить функция, а не только конкретную реализацию.

## Как сделать Pull Request

1. Форкните репозиторий и создайте ветку от `main`:
   ```bash
   git checkout -b fix/my-fix
   ```

2. Установите зависимости:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Внесите изменения. Следуйте структуре проекта:
   - `src/ui/` — компоненты интерфейса
   - `src/services/` — бизнес-логика
   - `src/domain/` — модели
   - `src/database/` — работа с SQLite

4. Проверьте, что импорты и синтаксис не сломаны:
   ```bash
   python -c "import src.app_config"
   python -m py_compile main.py
   ```

5. Запустите приложение локально и убедитесь, что изменение работает:
   ```bash
   python main.py
   ```

6. Создайте Pull Request с понятным описанием — что изменено и зачем.

## Стиль кода

- Python 3.10+, форматирование через `ruff` (конфиг в `pyproject.toml`).
- Длина строки — 100 символов.
- Типы аннотировать там, где это улучшает читаемость.

## Сборка standalone-версии

```bash
.\build.ps1
```

Использует `vk_music_saver.spec` и PyInstaller.
