#!/usr/bin/env python3
# encoding: utf-8

import os
import re
import yaml
from typing import Union


def regularize_path(path: str) -> str:
    """
    Regularize the path.
    If the path has a initial component of ~ or ~user, it will be replaced by home directory
    If the path is not the absolutized path, absolute path will be returned.

    Args:
        path (str): Path to be regularized
    """
    if path.startswith('~'):
        return os.path.expandvars(os.path.expanduser(path))
    else:
        return os.path.abspath(os.path.expandvars(path))


def get_files_by_regex(path: str, regex: str) -> list:
    """
    Get all the file paths corresponding the regex given

    Args:
        path (str): The directory which contains files to be found
        regex (regex): The regular expression of the search

    Return:
        file_list (list): A list of file paths
    """
    file_list = list()
    for root, _, files in os.walk(path):
        for file_name in files:
            if re.search(regex, file_name):
                file_list.append(os.path.join(root, file_name))
    return file_list


def save_yaml_file(path: str,
                   content: Union[str, dict], overwrite: bool = True):
    """
    Save yaml files with options for overwriting.

    Args:
        path (str): The directory which contains files to be found
        regex (regex): The regular expression of the search

    Return:
        file_list (list): A list of file paths
    """
    if not isinstance(path, str):
        raise ValueError(f'Invalid path ({path}) due to wrong type ({type(path)})')

    yaml.add_representer(str, string_representer)
    content = yaml.dump(data=content)

    dirname = os.path.dirname(path)
    filename = os.path.basename(path)

    # Make sure the dir is exists
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname)

    # Make sure the suffix is correct
    if filename.endswith('.yml') or filename.endswith('.yaml'):
        suffix = '.' + filename.split('.')[-1]
        filename = filename.replace(suffix, '')
    else:
        suffix = '.yml'

    # Overwrite handling
    if not overwrite:
        i = 0
        while i < 100000:
            index = '' if not i else f' ({i})'
            new_path = os.path.join(dirname, f'{filename}{index}{suffix}')
            if not os.path.isfile(new_path):
                break
            i += 1
    else:
        new_path = os.path.join(dirname, f'{filename}{suffix}')

    with open(new_path, 'w') as f:
        f.write(content)

    return True


def string_representer(dumper, data):
    """
    Add a custom string representer to use block literals for multiline strings.
    """
    if len(data.splitlines()) > 1:
        return dumper.represent_scalar(tag='tag:yaml.org,2002:str', value=data, style='|')
    return dumper.represent_scalar(tag='tag:yaml.org,2002:str', value=data)


def read_yaml_file(path: str) -> dict or list:
    """
    Read a YAML file and return the parameters as python variables.

    Args:
        path (str): The YAML file path to read.

    Returns:
        dict or list: The content read from the file.
    """
    if not isinstance(path, str):
        raise ValueError(
            f'Invalid path ({path}).')
    if not os.path.isfile(path):
        raise ValueError(f'Given path ({path}) does not exist.')
    with open(path) as f:
        content = yaml.load(stream=f, Loader=yaml.FullLoader)
    return content
