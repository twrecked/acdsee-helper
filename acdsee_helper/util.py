import os
import time
from .color import vvprint


def remove_duplicates(messy_list):
    return list(dict.fromkeys(messy_list))


def to_list(possible_list):
    if possible_list is None:
        return []
    elif type(possible_list) is list:
        return possible_list
    else:
        return [possible_list]


def file_age(filepath):
    return time.time() - os.path.getmtime(filepath)


def walk(config, files_or_dirs, callback, **kwargs):
    for file_or_dir in files_or_dirs:
        if os.path.isdir(file_or_dir) and config.is_recursive:
            for root, dirs, files in os.walk(file_or_dir):
                for file in files:
                    file = f"{root}/{file}"
                    if config.is_excluded_file(file):
                        vvprint(f"ignoring excluded {file}")
                        continue
                    if config.is_data_file(file):
                        callback(cfg=config, file=file, **kwargs)
        elif config.is_data_file(file_or_dir):
            callback(cfg=config, file=file_or_dir, **kwargs)
        else:
            vvprint(f"ignoring {file_or_dir}")
