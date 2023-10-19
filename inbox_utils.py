import os
import shutil

def process_subdirectories(root_dir='Inbox'):
    # Получаем список всех подпапок в указанной папке
    subdirs = [d for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d))]

    # Фильтруем подпапки, исключая 'blogs' и оставляя только те, что названы числами
    subdirs = [d for d in subdirs if d.isdigit() and d != 'blogs']

    # Сортируем подпапки по номерам (от меньшего к большему)
    subdirs.sort(key=int)

    # Инициализируем список папок для удаления
    dirs_to_remove = []

    # Перебираем все подпапки и проверяем количество файлов в каждой из них
    for subdir in subdirs:
        subdir_path = os.path.join(root_dir, subdir)
        files = [f for f in os.listdir(subdir_path) if os.path.isfile(os.path.join(subdir_path, f))]
        if len(files) < 2:
            print(f"Directory with less than two files found: {subdir_path}")
            dirs_to_remove.append(subdir_path)

    # Удаляем папки с меньше чем два файла
    for dir_path in dirs_to_remove:
        shutil.rmtree(dir_path)
        print(f"Removed directory: {dir_path}")

    # Получаем обновленный список подпапок после удаления
    subdirs = [d for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d)) and d.isdigit()]

    # Сортируем подпапки по номерам (от меньшего к большему)
    subdirs.sort(key=int)

    # Переименовываем подпапки, чтобы исключить пробелы в нумерации
    for idx, subdir in enumerate(subdirs, start=1):
        if int(subdir) != idx:
            print(f"Gap detected: Expected {idx} but got {subdir}")
        old_path = os.path.join(root_dir, subdir)
        new_path = os.path.join(root_dir, str(idx))
        os.rename(old_path, new_path)
        print(f"Renamed directory: {old_path} -> {new_path}")

    print(f"Total directories removed: {len(dirs_to_remove)}")
    print(f"Total directories renamed: {len(subdirs)}")
    
process_subdirectories()
