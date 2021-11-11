#!/usr/bin/env python3
# encoding: utf-8


import os
try:
    # openbabel 3
    from openbabel import pybel
except ImportError:
    # openbabel 2
    import pybel

from rmgpy.molecule.molecule import Molecule
from rmgpy.molecule.converter import from_ob_mol

from arc.species.conformers import find_internal_rotors
from arc.species.converter import xyz_to_xyz_file_format
from arc.parser import parse_xyz_from_file

from rdmc.external.rmg import from_rdkit_mol

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
    # Does not work for generate resonance structure
    # Atom index will change
    try:
        mol = xyz_to_mol(xyz)
    except ValueError:
        return
    # spc.molecule = [mol]
    # spc.generate_resonance_structures()
    # for mol in spc.molecule:
    #     new_rotors_dict = find_internal_rotors(mol)
    #     try:
    #         old_rotors_dict = [rotor for rotor in new_rotors_dict
    #                            if rotor in old_rotors_dict]
    #     except NameError:
    #         old_rotors_dict = new_rotors_dict
    old_rotors_dict = find_internal_rotors(mol)
    return {ind: rotor for ind, rotor in enumerate(old_rotors_dict)}


def rdmol_to_rotors_dict(rdmol):

    mol = from_rdkit_mol(rdmol)
    old_rotors_dict = find_internal_rotors(mol)
    return {ind: rotor for ind, rotor in enumerate(old_rotors_dict)}


def xyz_to_xyz_file(spc, filename='xyz.txt'):
    xyz = spc['geom']
    with open(os.path.join(spc['directory'], filename), 'w') as f:
        f.write(xyz_to_xyz_file_format(xyz))
