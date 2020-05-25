#!/usr/bin/env python3
# encoding: utf-8

"""
The toolbox for works related to ARC project management
"""

import logging
import os

from arc.exceptions import ServerError
from arc.job.ssh import SSHClient

from easy_rmg_model.common import read_yaml_file


def remove_remote_calc_files(server_name: str,
                             local_project_path: str,
                             only_converged: bool = True):
    """
    Remove calculations from the remote server.

    Args:
        server_name (str): The server host the calculations
        local_project_path (str): The path to the local project
        only_converged (bool): Remove all calculation files or only converged
                               calculation files. ``True`` for only converged ones.
    """
    restart_file_path = os.path.join(local_project_path, 'restart.yml')
    restart_dict = read_yaml_file(restart_file_path)
    project_name = restart_dict['project']

    species_to_delete = []
    for label, output_info in restart_dict['output'].items():
        if not only_converged or output_info['convergence']:
            species_to_delete.append(label)

    with SSHClient(server_name) as ssh:
        for label in species_to_delete:
            remote_label = label.replace('(', '_').replace(')', '_')
            remote_path = os.path.join(
                'runs', 'ARC_Projects', project_name, remote_label)
            try:
                ssh.remove_dir(remote_path)
            except ServerError as e:
                if 'No such file or directory' in e.args[0]:
                    pass
            except Exception as e:
                logging.warning(
                    f"Cannot remove {label} dir ({remote_path}). Got: {e}. Skip.")
            else:
                logging.warning(
                    f"{label} dir ({remote_path}) is removed.")
