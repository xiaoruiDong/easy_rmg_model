#!/usr/bin/env python3
# encoding: utf-8

import argparse
import datetime
import itertools
import os
import shutil
import subprocess
import time
from multiprocessing import Pool

import pandas as pd
from rmgpy.molecule.molecule import Molecule
from rmgpy.chemkin import load_species_dictionary

from easy_rmg_model.common import regularize_path
from easy_rmg_model.settings import (IDT_SPECIES,
                                     PHIS_POST_PROCESS,
                                     POOL_SIZE_POST_PROCESS,
                                     PS_POST_PROCESS,
                                     RMG_PATH,
                                     SENS_SPECIES,
                                     SIM_TIME_FINAL_POST_PROCESS,
                                     SIM_TIME_OUT_POST_PROCESS,
                                     TS_POST_PROCESS)
from easy_rmg_model.template_writer.input import RMGSimulateInput
from easy_rmg_model.template_writer.submit import SLURMSubmitScript


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('model_path', type=str, nargs=1,
                        help='The folder path to RMG model')
    parser.add_argument('fuel', metavar='FUEL', nargs=1,
                        help='The label or the smiles of the fuel')
    parser.add_argument('-T', '--temperature', nargs='+',
                        help='Temperatures [K]')
    parser.add_argument('-P', '--pressure', nargs='+', help='Pressures [atm]')
    parser.add_argument('-p', '--phi', nargs='+',
                        help='Fue-to-air equivalence ratio')
    parser.add_argument('-f', '--final_time', nargs=1,
                        help='The t_final of the simulation')
    parser.add_argument('-s', '--simulate_path', nargs=1,
                        help='Path to save simulation results')
    parser.add_argument('-S', '--sensitivity_path', nargs=1,
                        help='Path to save sensitivity results')
    parser.add_argument('-F', '--flux_diagram_path', nargs=1,
                        help='Path to save flux diagram results')
    parser.add_argument('--pool_size', nargs='?', type=int,
                        help='The size of the job pool')

    args = parser.parse_args()

    model_path = regularize_path(args.model_path[0])
    fuel = args.fuel[0]
    Ts = [float(T) for T in args.temperature] if args.temperature else TS_POST_PROCESS
    Ps = [float(P) for P in args.pressure] if args.pressure else PS_POST_PROCESS
    phis = [float(phi) for phi in args.phi] if args.phi else PHIS_POST_PROCESS
    tf = float(args.final_time[0]) if args.final_time else SIM_TIME_FINAL_POST_PROCESS
    outputs = {}
    for job_type in ['simulate', 'sensitivity', 'flux_diagram']:
        job_path = getattr(args, f'{job_type}_path')
        outputs[job_type] = regularize_path(job_path[0]) if job_path else \
            os.path.join(os.path.dirname(model_path), job_type)
    pool_size = POOL_SIZE_POST_PROCESS if not args.pool_size else args.pool_size

    return model_path, fuel, Ts, Ps, phis, tf, outputs, pool_size


def find_molecule(molecule, spc_dict):
    # Find the molecule according to the smiles or the label information
    if molecule in spc_dict:
        return {'label': molecule, 'smiles': spc_dict[molecule].molecule[0].to_smiles()}
    try:
        mol = Molecule().from_smiles(molecule)
    except:
        raise ValueError(
            f'Invalid molecule input {molecule} should be a SMILES string or the species label')
    for label, spc in spc_dict.items():
        if spc.is_isomorphic(mol):
            return {'label': label, 'smiles': spc.molecule[0].to_smiles()}


def run_simulation(input_path, chemkin_path, spc_dict_path, work_dir='.'):
    py_file = f"{RMG_PATH}/scripts/simulate.py"
    cmd = f'python "{py_file}" ' \
          f'"{input_path}" "{chemkin_path}" "{spc_dict_path}";'
    try:
        output = subprocess.check_output(cmd,
                                         stderr=subprocess.STDOUT,
                                         cwd=work_dir,
                                         shell=True,
                                         timeout=SIM_TIME_OUT_POST_PROCESS)
        return True
    except subprocess.CalledProcessError as e:
        print(f'Simulation failed. Got ({e.output})')
        return


def generate_flux_diagram(input_path, chemkin_path, spc_dict_path, work_dir='.'):
    py_file = f"{RMG_PATH}/scripts/generateFluxDiagram.py"
    # generate flux diagram
    cmd = f'python "{py_file}" ' \
          f'"{input_path}" "{chemkin_path}" "{spc_dict_path}";'
    try:
        output = subprocess.check_output(cmd,
                                         stderr=subprocess.STDOUT,
                                         cwd=work_dir,
                                         shell=True,
                                         timeout=SIM_TIME_OUT_POST_PROCESS)
    except subprocess.CalledProcessError as e:
        print(f'Flux diagram failed. Got ({e.output})')
        return
    else:
        # remove the species folder
        shutil.rmtree(os.path.join(work_dir, 'species'))
        return True


def run_sensitivity(model_path, sens_path, Ts, Ps, phis, pool_size):
    cmd = ['python', os.path.join(os.path.dirname(__file__), 'runSens.py')]
    cmd += [model_path, sens_path, ]
    cmd += ['-T'] + [str(T) for T in Ts]
    cmd += ['-P'] + [str(P) for P in Ps]
    cmd += ['-p'] + [str(phi) for phi in phis]
    cmd += ['--pool_size', str(pool_size)]
    try:
        output = subprocess.check_output(cmd,
                                         stderr=subprocess.STDOUT,
                                         cwd=model_path)
    except subprocess.CalledProcessError as e:
        print(f'Sensitivity job terminated. Got ({e.output})')
        return
    else:
        print('Finished Sensitivity.')


def generate_rmg_input_file(spec: dict, save_path: str):
    """
    A helper function to save rmg input file.

    Args:
        spec (dict): The specifications used to generate the rmg input file.
        save_path (str): The path to save the input file.
    """
    spec.update({'save_path': save_path})
    rmg_sim_input = RMGSimulateInput(spec)
    rmg_sim_input.save()


def main():

    global model_path, fuel, Ts, Ps, phis, tf, outputs, pool_size
    model_path, fuel, Ts, Ps, phis, tf, outputs, pool_size = parse_arguments()

    global chemkin_path, spc_dict_path
    chemkin_path = os.path.join(model_path, 'chem_annotated.inp')
    spc_dict_path = os.path.join(model_path, 'species_dictionary.txt')

    global spc_dict, spc_num
    spc_dict = load_species_dictionary(spc_dict_path)
    spc_num = len(spc_dict)

    global  idt_species
    fuel = find_molecule(fuel, spc_dict)
    idt_species = find_molecule(IDT_SPECIES["smiles"], spc_dict)
    #trying to run parallel
    #for T, P, phi in itertools.product(Ts, Ps, phis):
    print('Running in parallel with {pool} processors'.format(pool=pool_size))
    with Pool(pool_size) as p:
            p.map(running_similation, itertools.product(Ts, Ps, phis))
    p.close()
    p.join()
    # Sensitivity usually takes longer, use queue software
    run_sensitivity(
        model_path, outputs['sensitivity'], Ts, Ps, phis, pool_size)

def running_similation(TPPhi):
    T, P, phi = TPPhi
    print(f'Running simulation T: {T}, P: {P}, phi:{phi}')

    folder_name = f'{T}_{P}_{phi}'
    spec = {
        'species_dictionary': spc_dict_path,
        'fuel': fuel,
        'temp': T,
        'pressure': P,
        'phi': phi,
        'tf': tf,
    }

    # Create folder and input file
    work_dir = os.path.join(outputs['simulate'], folder_name,)
    os.makedirs(work_dir, exist_ok=True)
    input_path = os.path.join(work_dir, 'input.py')
    generate_rmg_input_file(spec, save_path=input_path)

    done = run_simulation(input_path, chemkin_path,
                          spc_dict_path, work_dir)

    # Get ignition delay
    if done:
        try:
            df = pd.read_csv(os.path.join(work_dir, 'solver',
                                          f'simulation_1_{spc_num}.csv'))
            df = df.set_index('Time (s)')
            idt = df[idt_species["label"]].idxmax()
        except:
            print(f'Cannot get ignition delay time. Use default time ({tf} seconds).')
            idt = tf
    else:
        idt = tf

    # Generate flux diagram
    print(f'Generating flux diagram T: {T}, P: {P}, phi: {phi}')
    work_dir = os.path.join(outputs['flux_diagram'], folder_name,)
    os.makedirs(work_dir, exist_ok=True)
    input_path = os.path.join(work_dir, 'input.py')
    spec.update({'tf': min(idt * 10, tf)})
    generate_rmg_input_file(spec, save_path=input_path)

    generate_flux_diagram(input_path, chemkin_path,
                          spc_dict_path, work_dir)

    # Create sens input
    work_dir = os.path.join(outputs['sensitivity'], folder_name,)
    os.makedirs(work_dir, exist_ok=True)
    input_path = os.path.join(work_dir, 'input.py')
    spec.update({'sens_spc': SENS_SPECIES,
                 'tf': idt})
    generate_rmg_input_file(spec, save_path=input_path)


if __name__ == '__main__':
    main()
