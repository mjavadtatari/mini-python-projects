# Import libraries
import os
import re


def get_files_name_sorted(path):
    """
    Get all files in the directory, and sort them by name.
    """
    return sorted([f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))])


def get_video_files(path):
    """
    Get all mp4 OR mkv files in the directory.
    """
    temp_out = [f for f in get_files_name_sorted(path) if f.endswith('.mp4')]
    if len(temp_out) == 0:
        return [f for f in get_files_name_sorted(path) if f.endswith('.mkv')]
    return temp_out


def change_to_watched(path, status):
    """
    Change first unWatched mp4 file to Watched.
    """
    result = status['result']
    repeat_number = status['repeat_number']
    next_prefix = '[Watched{}]'.format(
        2 if repeat_number == '' else int(repeat_number) + 1)

    for f in get_video_files(path):
        if not f.startswith(next_prefix):
            os.rename(os.path.join(path, f),
                      os.path.join(path, next_prefix + f[result:]))
            if os.path.isfile(os.path.join(path, f[:-4] + '.srt')):
                os.rename(os.path.join(
                    path, f[:-4] + '.srt'), os.path.join(path, next_prefix + f[result:-4] + '.srt'))
            break


def check_is_any_unwatched(path):
    """
    Checks if there is any unwatched files or not.
    """
    repeat_number = ''

    for f in get_video_files(path):
        tmp_repeat_number = find_repeat_number(f)

        if (tmp_repeat_number != repeat_number) or ((tmp_repeat_number > repeat_number if type(tmp_repeat_number) == 'int' else False)):
            repeat_number = tmp_repeat_number

    previous_prefix = '[Watched{}]'.format(repeat_number)
    result = re.search(r"^(\[Watched\d*\])", previous_prefix)

    if (result):
        result = len(result.group(1))
    else:
        result = 0

    for f in get_video_files(path):
        if not f.startswith(previous_prefix):
            return {
                'is_unwatched': True,
                'repeat_number': repeat_number,
                'result': result,
            }

    return {
        'is_unwatched': False,
        'repeat_number': repeat_number,
        'result': result,
    }


def find_repeat_number(txt):
    """
    Checks the prefix to find the repeatation number.
    """
    result = re.search(r"^\[Watched(\d*)\]", txt)

    if (result):
        return result.group(1)
    else:
        return ''


# Global Variables
PATH = os.path.dirname(__file__)
STATUS = check_is_any_unwatched(PATH)

# Run the Application
change_to_watched(PATH, STATUS)
