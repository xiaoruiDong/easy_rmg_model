#!/usr/bin/env python3
# encoding: utf-8

"Generate species images for a model"

import argparse
import os

from easy_rmg_model.common import regularize_path
from rmgpy.tools.loader import load_rmg_job

def parse_arguments():

    parser = argparse.ArgumentParser()
    parser.add_argument('model_path', type=str, nargs=1,
                        help='The folder path to RMG model')
    args = parser.parse_args()
    model_path = regularize_path(args.model_path[0])
    return model_path


def main():

    model_path  = parse_arguments()

    print(f'Using RMG model from {model_path}...')
    input_file = os.path.join(model_path, 'input.py')
    chemkin_file = os.path.join(model_path, 'chem_annotated.inp')
    species_dict = os.path.join(model_path, 'species_dictionary.txt')
    load_rmg_job(input_file, chemkin_file, species_dict,
                        generate_images=True)


if __name__ == '__main__':
    main()