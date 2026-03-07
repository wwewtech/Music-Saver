import os
from pathlib import Path

start_dir = Path.cwd()
output_file = "output.txt"

# Расширения, которые нужно пропустить
SKIP_EXTENSIONS = {
    # Изображения
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg', '.ico', '.psd',
    # Видео
    '.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm', '.m4v', '.mpg', '.mpeg',
    # Аудио
    '.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a', '.wma',
    # Архивы
    '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.iso',
    # Исполняемые файлы
    '.exe', '.dll', '.so', '.dylib', '.bin', '.msi',
    # Документы (бинарные)
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    # Базы данных
    '.db', '.sqlite', '.mdb', '.sqlite3',
    # Прочее
    '.pyc', '.pyo', '.pyd', '.class', '.jar', '.war', '.ear'
}

# Кодировки для попытки чтения
ENCODINGS = ['utf-8', 'utf-8-sig', 'cp1251', 'cp866', 'iso-8859-1', 'latin-1']

def should_skip_file(file_path):
    """Проверяет, нужно ли пропускать файл"""
    # Проверка по расширению
    if file_path.suffix.lower() in SKIP_EXTENSIONS:
        return True
    
    # Проверка размера файла (больше 5MB - пропускаем)
    try:
        if file_path.stat().st_size > 5 * 1024 * 1024:  # 5 MB
            return True
    except (OSError, IOError):
        pass
    
    return False

def read_file_with_encodings(file_path):
    """Пытается прочитать файл с различными кодировками"""
    for encoding in ENCODINGS:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            return content, None
        except (UnicodeDecodeError, IOError, OSError, PermissionError) as e:
            last_error = e
            continue
    
    return None, last_error

with open(output_file, "w", encoding="utf-8") as out_f:
    for root, dirs, files in os.walk(start_dir):
        # Пропускаем некоторые системные директории
        dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', '.idea', '.vscode', 'node_modules'}]
        
        for file_name in files:
            # Пропускаем файл output.txt
            if file_name == output_file:
                continue
                
            full_path = Path(root) / file_name
            
            # Пропускаем бинарные и большие файлы
            if should_skip_file(full_path):
                continue
            
            rel_path = full_path.relative_to(start_dir)
            out_f.write(f"полный путь от исходной папки: {rel_path}\n")
            
            content, error = read_file_with_encodings(full_path)
            
            if content is not None:
                out_f.write("```\n")
                out_f.write(content)
                if not content.endswith("\n"):
                    out_f.write("\n")
                out_f.write("```\n\n")
            else:
                folder = os.path.dirname(str(rel_path))
                folder = folder if folder else "исходная папка"
                out_f.write(
                    f"В папке {folder} лежит файл {file_name}, который не удалось прочитать.\n"
                )
                out_f.write(f"Ошибка: {error}\n\n")