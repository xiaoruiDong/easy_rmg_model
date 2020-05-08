#!/usr/bin/env python3
# encoding: utf-8

"Clean ARC input species section"

import argparse
import os

from easy_rmg_model.common import (read_yaml_file,
                                   regularize_path,
                                   save_yaml_file)
from easy_rmg_model.rmg2arc.arc_input import (combine_arc_species_inputs,
                                              combine_spc_info,
                                              find_species_from_spc_dict,)
from easy_rmg_model.rmg2arc.species_dict import (load_spc_dict,
                                                 species_from_spc_info)
from easy_rmg_model.rmg2arc.thermo_db import (load_thermo_database,
                                              load_thermo_lib_by_path)

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=str,
                        help='The ARC input file to be cleaned.')
    parser.add_argument('-l', '--libraries', type=str, nargs='?',
                        help='A yaml file contains the thermo library list to be '
                             'checked. If any entry is included in the library, it '
                             'will be removed from the input file.')
    # TODO: In the future can filter by its substructure
    parser.add_argument('-f', '--filter_species', type=str, nargs='?',
                        help='A file contains the species to be filtered.')
    parser.add_argument('-o', '--output', type=str, nargs='?',
                        help='The path to save results.')

    args = parser.parse_args()

    input_file = regularize_path(args.input)
    libraries = regularize_path(args.libraries) \
                        if args.libraries else ''
    filter_spc_dict = regularize_path(args.filter_species) \
                      if args.filter_species else ''
    output = regularize_path(args.output) if args.output else ''

    return input_file, libraries, filter_spc_dict, output


def main():

    input_file, libraries_path, filter_spc_dict, output = parse_arguments()

    # Get species info in the input file
    arc_input_species = read_yaml_file(input_file)['species']
    spc_info = {spc['label']: spc for spc in arc_input_species}
    print(f'Starting with {len(spc_info)} species...')

    if filter_spc_dict:
        # Load filtered species dictionary
        filter_spc_dict = load_spc_dict(filter_spc_dict)
        # Clean work
        clean = []
        for label, spc in spc_info.items():
            dict_label, _ = find_species_from_spc_dict(spc, filter_spc_dict)
            if not dict_label:  # cannot find species
                clean.append(label)
            else:
                print(f'Warning: species {label} is cleaned out due to belonging '
                      f'to filtered species dictionary')
        spc_info = {label: spc for label, spc in spc_info.items()
                    if label in clean}

    if libraries_path:
        # Load thermo libraries
        libraries = read_yaml_file(libraries_path)
        thermo_db = load_thermo_database(libraries=libraries['built-in_libs'])
        for t_lib in libraries['external_libs']:
            load_thermo_lib_by_path(t_lib, thermo_db)
        # Clean work
        clean = []
        for label, spc in spc_info.items():
            try:
                thermo_data = thermo_db.get_all_thermo_data(
                    species_from_spc_info(spc))
            except:
                print(f'Warning: Cannot generate thermo for {label}.')
                continue
            if len(thermo_data) <= 1:  # Only GAV availabel
                clean.append(label)
            else:
                print(f'Warning: species {label} is cleaned out due to existing '
                      f'in thermo libraries')
        spc_info = {label: spc for label, spc in spc_info.items()
                    if label in clean}

    # Make sure there is no duplicates in the spc_info
    # Iteratively using combine function can help filter out duplicates
    cleaned_info = {}
    cleaned_spc_dict = {}
    for label, spc in spc_info.items():
        cleaned_info = combine_spc_info(spc_info1=cleaned_info,
                                        spc_info2={label: spc},
                                        spc_dict=cleaned_spc_dict)

    # Convert species info to ARC input
    print(f'Eventually, {len(cleaned_info)} species are left...')
    arc_input = {'species': [spc for spc in cleaned_info.values()]}

    if not output:
        output = os.path.join('.', 'input_cleaned.yml')
    actual_output_path = save_yaml_file(output, arc_input, overwrite=False)
    print(f'Saved to {actual_output_path}.')

if __name__ == '__main__':
    main()
