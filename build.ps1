$ErrorActionPreference = "Stop"

$venvPyInstaller = ".\.venv\Scripts\pyinstaller.exe"
$pyInstallerCmd = $null

if (Test-Path $venvPyInstaller) {
    $pyInstallerCmd = $venvPyInstaller
} else {
    # CI runs without a project-local .venv, so use the active Python environment.
    try {
        python -m PyInstaller --version | Out-Null
        $pyInstallerCmd = "python -m PyInstaller"
    } catch {
        throw "PyInstaller не найден ни в .venv, ни в текущем Python. Установите зависимости: python -m pip install -r requirements.txt"
    }
}

if (Test-Path ".\build") {
    Remove-Item ".\build" -Recurse -Force
}

if (Test-Path ".\dist") {
    Remove-Item ".\dist" -Recurse -Force
}

if ($pyInstallerCmd -is [string] -and $pyInstallerCmd -like "python -m PyInstaller") {
    python -m PyInstaller --clean --noconfirm .\vk_music_saver.spec
} else {
    & $pyInstallerCmd --clean --noconfirm .\vk_music_saver.spec
}
Write-Host "Сборка завершена. Результат: .\dist\MusicSaver" -ForegroundColor Green
