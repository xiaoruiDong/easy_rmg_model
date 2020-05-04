#!/usr/bin/env python3
# encoding: utf-8


import os

import pybel

from rmgpy.molecule.molecule import Molecule
from rmgpy.molecule.converter import from_ob_mol

from arc.species.conformers import find_internal_rotors
from arc.species.converter import xyz_to_xyz_file_format
from arc.parser import parse_xyz_from_file


def xyz_to_mol(xyz):
    if isinstance(xyz, dict):
        string = xyz_to_xyz_file_format(xyz)
    elif isinstance(xyz, str):
        if not xyz[0].isdigit():
            atom_num = len(xyz.splitlines())
            string = f'{atom_num}\n\n' + xyz
        else:
            string = xyz
    elif os.path.isfile(xyz):
        string = xyz_to_xyz_file_format(parse_xyz_from_file(xyz))
    else:
        raise ValueError(f'Invalid xyz input, got: {xyz}')
    molecule = pybel.readstring('xyz', string)
    mol = Molecule()
    from_ob_mol(mol, molecule.OBMol)
    return mol


def xyz_to_rotors_dict(xyz):
    try:
        mol = xyz_to_mol(xyz)
        return find_internal_rotors(mol)
    except:
        return

