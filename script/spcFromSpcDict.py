#!/usr/bin/env python3
# encoding: utf-8

"Get species info from flux diagram"

import argparse
import os
from typing import Union

from easy_rmg_model.common import regularize_path, save_yaml_file
from easy_rmg_model.rmg2arc.chemkin import get_species_aliases
from easy_rmg_model.rmg2arc.species_dict import (expand_spc_info_by_spc_dict,
                                                 load_spc_dict)


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('model_path', metavar='MODELPATH', type=str, nargs=1,
                        help='The folder path to RMG model')
    parser.add_argument('-o', '--output', nargs=1, help='The path to save results')

    args = parser.parse_args()

    model_path = regularize_path(args.model_path[0])
    output = regularize_path(args.output[0]) if args.output else None

    return model_path, output


def main():

    model_path, output = parse_arguments()

    chemkin_path = os.path.join(model_path, 'chem_annotated.inp')
    spc_dict_path = os.path.join(model_path, 'species_dictionary.txt')

    spc_dict = load_spc_dict(spc_dict_path)
    spc_aliases = get_species_aliases(chemkin_path, key='rmg')

    spc_info = {label: {'label': label} for label in spc_dict.keys()}
    # Get smiles, adjacency list and other information from speceis dictionary
    spc_info = expand_spc_info_by_spc_dict(spc_info, spc_dict)

    # Generate ARC input
    arc_input = {'species': []}
    for label, spc in spc_info.items():
        spc.update({'label': spc_aliases[label]})
        arc_input['species'].append(spc)

    if not output:
        output = os.path.join(model_path, 'input_spc_dict.yml')
    save_yaml_file(output, arc_input, overwrite=False)


if __name__ == '__main__':
    main()
