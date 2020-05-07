#!/usr/bin/env python3
# encoding: utf-8

import os
import re



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
