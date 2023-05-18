import os
import re


def create_folders(current_path, number_of_folders):
    """
    creates folder by the number
    """

    for i in range(1, number_of_folders+1):
        if i <= 9:
            dir_number = '0'+str(i)
        else:
            dir_number = str(i)

        if not os.path.exists(current_path+"\\Season "+dir_number):
            os.makedirs(current_path+"\\Season "+dir_number)

    return True


current_path = os.path.dirname(__file__)
file_name_regex = "([a-z_]*)([0-9]*)(\.py)"
number_of_folders = int(
    re.search(file_name_regex, os.path.basename(__file__)).group(2))


create_folders(current_path, number_of_folders)
