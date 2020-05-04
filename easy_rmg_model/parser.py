#!/usr/bin/env python3
# encoding: utf-8

import datetime
import os
import re

from arkane.ess import ess_factory, GaussianLog

from arc.common import read_yaml_file
from arc.species.species import ARCSpecies
from easy_rmg_model.species.converter import xyz_to_mol


def _get_lines_from_file(path) -> list:
    """
    A helper function for getting a list of lines from a file.

    Args:
        path (str): The file path.

    Returns:
        list: Entries are lines from the file.

    Raises:
        InputError: If the file could not be read.
    """
    if os.path.isfile(path):
        with open(path, 'r') as f:
            lines = f.readlines()
    else:
        raise ValueError(f'Could not find file {path}')
    return lines


def parse_termination_time(path):
    """
    Parse the termination time from the output log file.
    """
    log = ess_factory(fullpath=path)

    if isinstance(log, GaussianLog):
        regex = r'[a-zA-Z]+\s+\d+\s+\d{2}\:\d{2}\:\d{2}\s+\d{4}'
        lines = _get_lines_from_file(path)
        for line in lines[::-1]:
            if 'termination' in line:
                time_str = re.search(regex, line).group()
                return datetime.datetime.strptime(time_str, '%b %d %H:%M:%S %Y')
        return None
    else:
        raise NotImplementedError


def parse_species_in_arc_input(input_path: str) -> dict:
    """
    A function used to get species scope from the ARC input file.
    """
    spc_info = {}
    try:
        input_file = read_yaml_file(input_path)
    except:
        # Bad input path
        return spc_info

    if not 'species' in input_file:
        # An input file without species information, weird!
        return spc_info

    for spc in input_file['species']:
        label = spc['label']
        if 'smiles' in spc:
            try:
                spc_info[label] = {'label': label,
                                   'species': ARCSpecies(label=label,
                                                         smiles=spc['smiles']),
                                   'smi': spc['smiles'],
                                   'ts': False}
            except:
                pass
        elif 'xyz' in spc:
            try:
                mol = xyz_to_mol(spc['xyz'])
            except:
                pass
            else:
                smiles = mol.to_smiles()
                spc_info[label] = {'label': label,
                                   'species': ARCSpecies(label=label,
                                                         smiles=smiles),
                                   'smi': smiles,
                                   'ts': False}
        if label not in spc_info:
            # Cannot get smiles or xyz
            spc_info[label] = {'label': label, 'ts': False}
    return spc_info


def parse_charge_and_mult(path):
    """
    Parse the termination time from the output log file.
    """
    log = ess_factory(fullpath=path)

    if isinstance(log, GaussianLog):
        lines = _get_lines_from_file(path)
        for line in lines[::]:
            if 'charge' in line.lower() and 'multiplicity' in line.lower():
                items = line.strip().split()
                charge, mult = items[2], items[5]
                return charge, mult
        return
    else:
        raise NotImplementedError


def parse_constrained_internal_coords(coords_str):
    freeze = []
    if isinstance(coords_str, str):
        coords_str = coords_str.splitlines()
    frz_pat = r'[DBA]?(\s+\d+){2,4}\s+F'
    value_pat = r'[\d.]+'
    for line in coords_str:
        if re.search(frz_pat, line.strip()):
            values = re.findall(value_pat, line)
            freeze.append([int(values[i])
                          for i in range(len(values))])
    return freeze
