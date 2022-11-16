import os
import time


def remove_duplicates(messy_list):
    return list(dict.fromkeys(messy_list))


def to_list(possible_list):
    if type(possible_list) is list:
        return possible_list
    else:
        return [possible_list]


def file_age(filepath):
    return time.time() - os.path.getmtime(filepath)
