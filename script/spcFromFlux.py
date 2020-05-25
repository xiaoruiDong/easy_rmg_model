#!/usr/bin/env python3
# encoding: utf-8

"Get species info from flux diagram"

import argparse
import os
from typing import Union

from easy_rmg_model.common import regularize_path, save_yaml_file
from easy_rmg_model.rmg2arc.chemkin import get_species_aliases
from easy_rmg_model.rmg2arc.fluxdiagram import (find_flux_diagrams,
                                                get_spc_info_from_flux_diagrams)
from easy_rmg_model.rmg2arc.species_dict import (expand_spc_info_by_spc_dict,
                                                 load_spc_dict)


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('model_path', metavar='MODELPATH', type=str, nargs=1,
                        help='The folder path to RMG model')
    parser.add_argument('flux_path', metavar='FLUXPATH', type=str, nargs=1,
                        help='The folder path to flux diagrams')
    parser.add_argument('-s', '--software', nargs='?', const='rmg', default='rmg',
                        type=str, help='The software used to generate the flux diagram')
    parser.add_argument('-o', '--output', nargs=1, help='The dir path to save results')

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


def main():

    model_path, flux_path, software, output = parse_arguments()

    chemkin_path = os.path.join(model_path, 'chem_annotated.inp')
    spc_dict_path = os.path.join(model_path, 'species_dictionary.txt')

    spc_dict = load_spc_dict(spc_dict_path)

    # Get species info from flux diagrams
    flux_diagrams = find_flux_diagrams(flux_path)
    print('Find fluxdiagrams:\n' + '\n'.join(flux_diagrams))
    spc_info = get_spc_info_from_flux_diagrams(flux_diagrams)

    # These packages use rmg label instead of Chemkin label
    if software in ['rmg']:
        spc_aliases = get_species_aliases(chemkin_path, key='rmg')
    else:
        spc_aliases = {'label': label for label in spc_info.keys()}

    # Get smiles, adjacency list and other information from speceis dictionary
    spc_info = expand_spc_info_by_spc_dict(spc_info, spc_dict, spc_aliases)

    # Generate ARC input
    arc_input = {'species': []}
    for label, spc in spc_info.items():
        spc.update({'label': spc_aliases[label]})
        arc_input['species'].append(spc)

    output = os.curdir or output
    output = os.path.join(output, 'input_flux.yml')
    actual_output_path = save_yaml_file(output, arc_input, overwrite=False)
    print(f'Saved to {actual_output_path}.')

if __name__ == '__main__':
    main()
