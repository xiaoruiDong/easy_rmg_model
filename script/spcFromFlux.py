#!/usr/bin/env python3
# encoding: utf-8

"Get species info from flux diagram"

import argparse
import os
from typing import Union

from arc.common import save_yaml_file
from rmgpy.chemkin import load_species_dictionary, read_species_block
from rmgpy.molecule.molecule import Molecule

from easy_rmg_model.common import regularize_path
from easy_rmg_model.rmg2arc.fluxdiagram import (find_flux_diagrams,
                                                get_spc_info_from_flux_diagrams)


def find_molecule(molecule: str, spc_dict: dict):
    # Find the molecule according to the smiles or the label information
    if molecule in spc_dict:
        return {'label': molecule, 'smi': spc_dict[molecule].molecule[0].to_smiles()}
    try:
        mol = Molecule().from_smiles(molecule)
    except:
        raise ValueError(
            f'Invalid molecule input {molecule} should be a SMILES string or the species label')
    for label, spc in spc_dict.items():
        if spc.is_isomorphic(mol):
            return {'label': 'label', 'smi': spc.molecule[0].to_smiles()}


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('model_path', metavar='MODELPATH', type=str, nargs=1,
                        help='The folder path to RMG model')
    parser.add_argument('flux_path', metavar='FLUXPATH', type=str, nargs=1,
                        help='The folder path to flux diagrams')
    parser.add_argument('-s', '--software', nargs='?', const='rmg', default='rmg',
                        type=str, help='The software used to generate the flux diagram')
    parser.add_argument('-o', '--output', nargs=1, help='The path to save results')

    args = parser.parse_args()

    model_path = regularize_path(args.model_path[0])
    if args.software.lower() not in ['rmg', 'cantera', 'rms']:
        raise ValueError('Not an invalid software arguments. Currently support "RMG", "RMS" and "Cantera"')
    else:
        software = args.software.lower()
    flux_path = regularize_path(args.flux_path[0])
    output = regularize_path(args.output[0]) if args.output else None
    if output and os.path.isfile(output):
        raise ValueError('The path to the output exists.')

    return model_path, flux_path, software, output


def get_species_aliases(chemkin_path: str):
    """
    Get the species aliases from RMG generated chemkin file.

    Args:
        chemkin_path (str): The path to Chemkin file.
    
    Returns:
        dict: A dictinary of {Chemkin_name: RMG_name}.
    """
    spc_aliases = {}
    read_mode = False
    with open(chemkin_path, 'r') as f:
        line = f.readline()
        while line != '':
            line = line.strip()
            if 'SPECIES' in line.upper() and not read_mode:
                read_mode = True
            elif 'END' == line.upper() and read_mode:
                read_mode = False
                break
            elif read_mode and '!' in line and line.split('!'):
                chemkin_name, rmg_name = [name.strip()
                                          for name in line.split('!')]
                if len(chemkin_name.split()) == 1 and len(rmg_name.split()) == 1:
                    spc_aliases[rmg_name] = chemkin_name
            line = f.readline()
    return spc_aliases


def main():

    model_path, flux_path, software, output = parse_arguments()

    chemkin_path = os.path.join(model_path, 'chem_annotated.inp')
    spc_dict_path = os.path.join(model_path, 'species_dictionary.txt')

    spc_dict = load_species_dictionary(spc_dict_path)

    # Get species info from flux diagrams
    flux_diagrams = find_flux_diagrams(flux_path)
    print('Find fluxdiagrams:\n' + '\n'.join(flux_diagrams))
    spc_info = get_spc_info_from_flux_diagrams(flux_diagrams)

    # These packages use rmg label instead of Chemkin label
    if software in ['rmg']:
        spc_aliases = get_species_aliases(chemkin_path)
    else:
        spc_aliases = {'label': label for label in spc_info.keys()}

    # Generate ARC input
    arc_input = {'species': []}
    for label, spc in spc_info.items():
        try:
            rmg_spc = spc_dict[spc_aliases[label]]
        except KeyError:
            print(
                f'Warning: Cannot find the species {spc["label"]} in species dictionary.')
        else:
            try:
                smiles = rmg_spc.molecule[0].to_smiles()
                charge = rmg_spc.molecule[0].get_net_charge()
                adjlist = rmg_spc.molecule[0].to_adjacency_list()
            except:
                print(
                    f'Warning: Cannot generate SMILES for the species {label}.')
            else:
                arc_input['species'].append({'label': label, 'smiles': smiles, 'adjlist': adjlist,
                                             'multiplicity': rmg_spc.multiplicity, 'charge': charge})

    # Save the ARC input file
    if not output:
        cur_dir = regularize_path('.')
        for index in [''] + [f' ({i})' for i in range(10000)]:
            output = os.path.join(cur_dir, f'input{index}.yaml')
            if not os.path.isfile(output):
                break

    save_yaml_file(output, arc_input)


if __name__ == '__main__':
    main()
