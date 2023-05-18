import os

def get_all_files(path):
    """
    Get all files from a directory and sort them by their name
    """
    all_files = []
    for root, dirs, files in os.walk(path):
        for file in files:
            all_files.append(file)
    return sorted(all_files)

def capital_first_letters_of_files(path):
    """
    Capitalize the first letter of each file name
    """
    files = get_all_files(path)
    for file in files:
        os.rename(os.path.join(path,file), os.path.join(path,file[:-4].title() + file[-4:]))


capital_first_letters_of_files(os.path.dirname(__file__))