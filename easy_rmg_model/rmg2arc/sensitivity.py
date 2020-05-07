#!/usr/bin/env python3
# encoding: utf-8
"""
The toolbox for sensitivity analysis related tasks
"""


import os
from typing import Union

import pandas as pd

from easy_rmg_model.common import get_files_by_regex


def find_sensitivity_results(path: str) -> list:
    """
    Find all of the flux diagrams in the given directory. Flux diagrams under 
    the same folder have the same species if generated from RMG or RMS.

    Args:
        path (str): The path from where to find flux diagrams based on '.dot file
        avoid_repeats (bool): Whether to avoid the repeats. 

    Returns:
        list: A list of paths to flux diagram dot files.
    """
    if not os.path.isdir(path):
        raise ValueError(
            f'Not a invalid path ({path}), need to be a dir path.')

    sensitivities = get_files_by_regex(path, r"^sensitivity.+\.csv$")
    return sensitivities


def get_spc_label_from_sensitivity(file: str, N: int = 50) -> list:
    """
    Get the list of species contained in multiple sensitivity analysis

    Args:
        file (str): a sensitivity analysis csv file
        N (int): the upperbound number of species to be extracted

    Returns:
        list: a list contains species labels
    """
    # Open the sensitivity result in DataFrame
    df = pd.read_csv(file)

    # Find the most sensitve species
    max_sensitivity = []
    for header in df.columns:
        if 'dG' in header:
            label = header.split('dG')[1][1:-1]
            max_sensitivity.append((label, abs(df[header]).max()))
    sorted_labels = sorted(max_sensitivity, key=lambda tup: tup[1])

    label_list = [tup[0] for tup in sorted_labels[:min(len(sorted_labels), N)]]
    return label_list


def get_spc_info_from_sensitivities(files: Union[str, list],
                                    N: int = 50) -> dict:
    """
    Get the list of species contained in multiple sensitivity analysis

    Args:
        files (Union[str, list]): a list contains the paths of sensitivity
                                  analysis csv files
        N (int): the upperbound number of species to be extracted in each SA

    Returns:
        dict: a dictionary contains species information (labels)
    """
    if isinstance(files, str):
        files = [files]

    label_list = []
    for sa_file in files:
        label_list += get_spc_label_from_sensitivity(sa_file, N)

    # remove duplicates
    label_list = list(set(label_list))
    return {label: {'label': label} for label in label_list}
