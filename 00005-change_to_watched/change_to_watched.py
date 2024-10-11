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
    Change first unWatched file to Watched.
    """
    to_be_removed_chars = 0 if status['is_unwatched'] else status['to_be_removed_chars']
    repeat_number = int(status['repeat_number'])
    repeat_number = repeat_number + \
        1 if not status['is_unwatched'] else repeat_number
    next_prefix = '[Watched{}]'.format(repeat_number)

    for f in get_video_files(path):
        if not f.startswith(next_prefix):
            os.rename(os.path.join(path, f),
                      os.path.join(path, next_prefix + f[to_be_removed_chars:]))
            if os.path.isfile(os.path.join(path, f[:-4] + '.srt')):
                os.rename(os.path.join(
                    path, f[:-4] + '.srt'), os.path.join(path, next_prefix + f[to_be_removed_chars:-4] + '.srt'))
            break


def check_is_any_unwatched(path):
    """
    Checks if there is any unwatched files or not.
    """
    repeat_number = 0

    for f in get_video_files(path):
        tmp_repeat_number = find_repeat_number(f)

        if (tmp_repeat_number != repeat_number) or ((tmp_repeat_number > repeat_number if type(tmp_repeat_number) == 'int' else False)):
            repeat_number = tmp_repeat_number

    repeat_number = repeat_number if repeat_number != '' else 0
    previous_prefix = '[Watched{}]'.format(
        repeat_number) if repeat_number else ''
    to_be_removed_chars = re.search(r"^(\[Watched\d*\])", previous_prefix)

    if (to_be_removed_chars):
        to_be_removed_chars = len(to_be_removed_chars.group(1))
    else:
        to_be_removed_chars = 0

    for f in get_video_files(path):
        if not f.startswith(previous_prefix):
            return {
                'is_unwatched': True,
                'repeat_number': repeat_number,
                'to_be_removed_chars': to_be_removed_chars,
            }

    return {
        'is_unwatched': False,
        'repeat_number': repeat_number,
        'to_be_removed_chars': to_be_removed_chars,
    }


def find_repeat_number(txt):
    """
    Checks the prefix to find the repeatation number.
    """
    repeat_number = re.search(r"^\[Watched(\d*)\]", txt)

    if (repeat_number):
        return repeat_number.group(1)
    else:
        return ''


# Global Variables
PATH = os.path.dirname(__file__)
STATUS = check_is_any_unwatched(PATH)

# Run the Application
change_to_watched(PATH, STATUS)
