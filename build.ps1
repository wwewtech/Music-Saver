$ErrorActionPreference = "Stop"

$venvPyInstaller = ".\.venv\Scripts\pyinstaller.exe"
if (-not (Test-Path $venvPyInstaller)) {
    throw "PyInstaller не найден в .venv. Выполните: .\.venv\Scripts\python.exe -m pip install -r requirements.txt"
}

if (Test-Path ".\build") {
    Remove-Item ".\build" -Recurse -Force
}

if (Test-Path ".\dist") {
    Remove-Item ".\dist" -Recurse -Force
}

& $venvPyInstaller --clean --noconfirm .\vk_music_saver.spec
Write-Host "Сборка завершена. Результат: .\dist\VKMusicSaver" -ForegroundColor Green
