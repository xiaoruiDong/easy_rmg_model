#!/usr/bin/env python3
# encoding: utf-8
"""
The toolbox for flux diagram related tasks
"""

import os

import pydot


def find_flux_diagrams(path, avoid_repeats=True):
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
        raise ValueError(f'Not a invalid path ({path}), need to be a dir path.')

    flux_diagrams=[]
    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith('.dot'):
                if avoid_repeats:
                    # Flux diagrams under the same folder have the same species
                    flux_diagrams.append(os.path.join(root, file))
                    break
                else:
                    flux_diagrams.append(os.path.join(root, file))
    return flux_diagrams


def get_spc_info_from_flux_diagrams(files):
    """
    Get the list of species contained in multiple flux diagrams

    Args:
        files (list): A list of files from which read species info

    Return:
        spc_info (list): A list of species info contains species label
    """
    # Get all species label
    label_list = list()
    for fd in files:
        label_list += get_spc_label_from_fluxdiagram(fd)
    # Get non duplicate labels from flux diagrams
    label_list = list(set(label_list))
    # Return the format of species info
    return {label: {'label': label} for label in label_list}


def get_spc_label_from_fluxdiagram(path):
    """
    Given the flux diagram in dot file, the species labels
    on the flux diagram will be extracted and output as a list

    Args:
        path (str): The file path to the flux diagram dot file

    Returns:
        label_list (list): A list which contains species labels
    """
    # Read the .dot file to graph
    graph = pydot.graph_from_dot_file(path)
    # Extract the node list
    node_list = graph[0].get_node_list()
    # Read the name of each node which is the species label
    label_list = [node.get_name() for node in node_list
                  if not node.get_name() in ["node", "graph"]]
    # Solve inconsistency in quotation marks
    # Cases that somes nodes may have extra quotation marks
    for index, label in enumerate(label_list):
        label_with_quote = label.split("\"")
        if len(label_with_quote) > 1:
            label_list[index] = label_with_quote[1]
    return label_list
