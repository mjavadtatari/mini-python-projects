import os

def get_all_mkv_sorted(path):
    """
    Get all mkv files from a directory and sort them by their name
    """
    mkv_files = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith('.mkv'):
                mkv_files.append(file)
    return sorted(mkv_files)

def get_all_srt_sorted(path):
    """
    Get all srt files from a directory and sort them by their name
    """
    srt_files = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith('.srt'):
                srt_files.append(file)
    return sorted(srt_files)

def match_subs_to_mkvs(path, mkv_files, srt_files):
    """
    Match srt files to mkv files
    """
    for i in range(len(mkv_files)):
        if mkv_files[i][:-4] != srt_files[i][:-4]:
            os.rename(os.path.join(path, srt_files[i]), os.path.join(path, mkv_files[i][:-4] + '.srt'))


current_path = os.path.dirname(__file__)

match_subs_to_mkvs(current_path, get_all_mkv_sorted(current_path), get_all_srt_sorted(current_path))
