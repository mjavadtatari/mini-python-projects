import os


def get_all_files(path, type_of_files=None):
    """
    Get all files from a directory and sort them by their name
    """
    all_files = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if type_of_files is None or file.endswith(type_of_files):
                all_files.append(file)
    return sorted(all_files)


def change_all_names_in_sequence(path, name_pattern, type_of_files=None):
    """
    Change all files in a directory by their name
    """
    all_files = get_all_files(path, type_of_files)
    for i, file in enumerate(all_files):
        os.rename(os.path.join(path, file), os.path.join(path, name_pattern.replace('$', f'{i+1:02}')+type_of_files))


change_all_names_in_sequence(os.path.dirname(
    __file__), 'DigitalDesign_E$_MaktabKhooneh', '.mp4')
