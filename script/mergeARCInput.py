#!/usr/bin/env python3
# encoding: utf-8

"Get species info from flux diagram"

import argparse
import os

from easy_rmg_model.common import regularize_path, save_yaml_file
from easy_rmg_model.rmg2arc.arc_input import combine_arc_species_inputs


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('input1', type=str,
                        help='The first input ARC input file')
    parser.add_argument('input2', type=str,
                        help='The second input ARC input file')
    parser.add_argument('--other_inputs', nargs='+',
                        help='Other inputs to be merged')
    parser.add_argument('-n', '--non_resonance', nargs='?', const=True, default=False,
                        help='Whether generating resonance structure to check duplicates')
    parser.add_argument('-o', '--output', help='The path to save results')

    args = parser.parse_args()

    input1 = regularize_path(args.input1)
    input2 = regularize_path(args.input2)
    if args.other_inputs:
        other_inputs = [regularize_path(input_file) for input_file in args.other_inputs]
    else:
        other_inputs = []
    resonance = True if not args.non_resonance else False
    output = regularize_path(args.output) if args.output else None

    inputs = [input1, input2] + other_inputs
    return inputs, output, resonance


def main():

    inputs, output, resonance = parse_arguments()

    arc_input = combine_arc_species_inputs(*inputs, resonance)

    if not output:
        output = os.path.join(os.curdir, 'input_merged.yml')
    actual_output_path = save_yaml_file(output, arc_input, overwrite=False)
    print(f'Saved to {actual_output_path}.')

if __name__ == '__main__':
    main()
