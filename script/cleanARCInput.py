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
from easy_rmg_model.rmg2arc.kinetics_db import (load_kinetics_database,
                                              load_kinetics_lib_by_path)
from rmgpy.molecule.molecule import Molecule

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
                        help='The dir path to save results.')

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
        thermo_db = load_thermo_database(libraries=libraries['built-in_thermo_libs'])
        for t_lib in libraries['external_thermo_libs']:
            load_thermo_lib_by_path(t_lib, thermo_db)
        kinetics_db = load_kinetics_database(libraries=libraries['built-in_kinetics_libs'])
        for k_lib in libraries['external_kinetics_libs']:
            load_kinetics_lib_by_path(k_lib, kinetics_db)
        # Clean work
        clean = []
        for label, spc in spc_info.items():
            if spc.get("is_ts",False):
                reactants = []
                products = []

                react,prod = spc["label"].split("<=>")
                for smiles in react.strip().split("+"):
                    reactants.append(Molecule().from_smiles(smiles.strip()))
                for smiles in prod.strip().split("+"):
                    products.append(Molecule().from_smiles(smiles.strip()))
                reactions = kinetics_db.generate_reactions_from_libraries(reactants=reactants,products=products) + kinetics_db.generate_reactions_from_libraries(reactants=products,products=reactants) 
                if reactions:
                    print(f'Warning: ts {label} is cleaned out due to existing '
                        f'in kinetics libraries')
                else:
                    clean.append(label)
            else:
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

    # Remove not desirable symbol from species label
    replace_list = [s for s in "()#"]
    for spc in cleaned_info.values():
        for symbol in replace_list:
            if not spc.get("is_ts",False):
                if symbol in spc['label']:
                    spc['label'] = spc['label'].replace(symbol, "_")

    # Convert species info to ARC input
    print(f'Eventually, {len(cleaned_info)} species are left...')

    arc_input1, arc_input2 = {'species': []}, {'species': []}
    for spc in cleaned_info.values():
        if ('multiplicity' in spc) and (spc['multiplicity'] < 3):
            # closed_shell species and multiplicity 1 species
            if spc.get("is_ts",False):
                if spc.get("adjlist",None):
                    spc.pop("adjlist")
                if spc.get("smiles",None):
                    spc.pop("smiles")
            
            arc_input1['species'].append(spc)
                
        else:
            # other species
            arc_input2['species'].append(spc)

    output = output or os.curdir
    output1 = os.path.join(output, 'input_cleaned_mul12.yml')
    output2 = os.path.join(output, 'input_cleaned_mul3p.yml')
    actual_output_path1 = save_yaml_file(output1, arc_input1, overwrite=False)
    actual_output_path2 = save_yaml_file(output2, arc_input2, overwrite=False)
    print(f'Species with mulitplicity < 3 are saved to {actual_output_path1}.\n'
          f'Species with mulitplicity >= 3 are saved to {actual_output_path2}.')

if __name__ == '__main__':
    main()
