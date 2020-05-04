#!/usr/bin/env python3
"""
The toolbox for flux diagram related tasks
"""

import os

import pydot


def get_spc_label_from_fluxdiagrams(result_folder):
    """
    Get the list of species contained in multiple flux diagrams

    Args:
        result_folder (str): The path to a folder which contains the flux diagram result

    Return:
        spc_list (list): A list of species
    """
    # Find the dot file
    flux_diagrams = []
    for root, _, files in os.walk(result_folder):
        for file in files:
            if file.endswith('.dot'):
                # Flux diagrams under the same folder have the same species
                flux_diagrams.append(os.path.join(root, file))
                break

    # Get non duplicate labels from flux diagrams
    label_list = list()
    for fd in flux_diagrams:
        label_list += get_spc_label_from_fluxdiagram(fd)
    return list(set(label_list))


def get_spc_label_from_fluxdiagram(file_path):
    """
    Given the flux diagram in dot file, the species labels
    on the flux diagram will be extracted and output as a list

    Args:
        path (str): The file path to the flux diagram dot file

    Returns:
        label_list (list): A list which contains species labels
    """
    # Read the .dot file to graph
    graph = pydot.graph_from_dot_file(file_path)
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
