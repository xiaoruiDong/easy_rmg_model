#!/usr/bin/env python3
# encoding: utf-8

"Get species info from flux diagram"

import argparse
import os
from typing import Union

from rmgpy.molecule.molecule import Molecule

from easy_rmg_model.common import regularize_path, save_yaml_file
from easy_rmg_model.rmg2arc.chemkin import get_species_aliases
from easy_rmg_model.rmg2arc.sensitivity import (find_sensitivity_results,
                                                get_spc_info_from_sensitivities)
from easy_rmg_model.rmg2arc.species_dict import (expand_spc_info_by_spc_dict,
                                                 load_spc_dict)


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('model_path', metavar='MODELPATH', type=str, nargs=1,
                        help='The folder path to RMG model')
    parser.add_argument('sensitivity_path', metavar='SENSITIVITY', type=str, nargs=1,
                        help='The folder path to sensitivity results')
    parser.add_argument('-s', '--software', nargs='?', const='rmg', default='rmg',
                        type=str, help='The software used to generate the flux diagram')
    parser.add_argument('-o', '--output', nargs=1, help='The dir path to save results')

    args = parser.parse_args()

    model_path = regularize_path(args.model_path[0])
    if args.software.lower() not in ['rmg', 'cantera', 'rms']:
        raise ValueError('Not an invalid software arguments. Currently support "RMG", "RMS" and "Cantera"')
    else:
        software = args.software.lower()
    sens_path = regularize_path(args.sensitivity_path[0])
    output = regularize_path(args.output[0]) if args.output else None
    if output and os.path.isfile(output):
        raise ValueError('The path to the output exists.')

    return model_path, sens_path, software, output


def main():

    model_path, sens_path, software, output = parse_arguments()

    chemkin_path = os.path.join(model_path, 'chem_annotated.inp')
    spc_dict_path = os.path.join(model_path, 'species_dictionary.txt')

    spc_dict = load_spc_dict(spc_dict_path)

    # Get species info from flux diagrams
    sensitivities = find_sensitivity_results(sens_path)
    print('Find sensitivities:\n' + '\n'.join(sensitivities))
    spc_info = get_spc_info_from_sensitivities(sensitivities)

    # The results usually contains a lot of S(XX), better to convert them using aliases
    spc_aliases = get_species_aliases(chemkin_path, key='chemkin')

    # Get smiles, adjacency list and other information from speceis dictionary
    spc_info = expand_spc_info_by_spc_dict(spc_info, spc_dict)

    # Generate ARC input
    arc_input = {'species': []}
    for label, spc in spc_info.items():
        spc.update({'label': spc_aliases[label]})
        arc_input['species'].append(spc)

    output = output or os.curdir
    output = os.path.join(output, 'input_sens.yml')
    actual_output_path = save_yaml_file(output, arc_input, overwrite=False)
    print(f'Saved to {actual_output_path}.')

if __name__ == '__main__':
    main()
