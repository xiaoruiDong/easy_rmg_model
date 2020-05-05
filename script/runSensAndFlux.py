#!/usr/bin/env python3
# encoding: utf-8

import argparse
import datetime
import itertools
import os
import subprocess
import time

import pandas as pd
from rmgpy.molecule.molecule import Molecule
from rmgpy.chemkin import load_species_dictionary

from easy_rmg_model.template_writer.input import RMGSimulateInput
from easy_rmg_model.template_writer.submit import SLURMSubmitScript
from easy_rmg_model.settings import RMG_PATH


DEFAULT_TS = [700, 800, 900, 1000, 1200, 1400, 1600, 2000]  # in Kelvin
DEFAULT_PS = [10, 30, 50]  # in atm
DEFAULT_PHIS = [0.5, 1.0, 1.5]
DEFAULT_TF = 10.0  # in seconds
DEFAULT_JOB_TIME_OUT =  5 * 60 * 60  # 5 hours
CHECK_POOLING_JOB = 2 * 60  # 2 min

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('model_path', metavar='MODELPATH', type=str, nargs=1,
                        help='The folder path to RMG model')
    parser.add_argument('fuel', metavar='FUEL', nargs=1,
                        help='The label or the smiles of the fuel')
    parser.add_argument('-T', '--temperature', nargs='+', help='Temperatures')
    parser.add_argument('-P', '--pressure', nargs='+', help='Pressures')
    parser.add_argument('-p', '--phi', nargs='+', help='Fue-to-air equivalence ratio')
    parser.add_argument('-f', '--final_time', nargs=1, help='The t_final of the simulation')
    parser.add_argument('-s', '--simulate_path', nargs=1, help='Path to save simulation results')
    parser.add_argument('-S', '--sensitivity_path', nargs=1, help='Path to save sensitivity results')
    parser.add_argument('-F', '--flux_diagram_path', nargs=1, help='Path to save flux diagram results')

    args = parser.parse_args()

    model_path = os.path.abspath(args.model_path[0])
    fuel = args.fuel[0]
    Ts = [float(T) for T in args.temperature] if args.temperature else DEFAULT_TS
    Ps = [float(P) for P in args.pressure] if args.pressure else DEFAULT_PS
    phis = [float(phi) for phi in args.phis] if args.phis else DEFAULT_PHIS
    tf = float(args.final_time[0]) if args.final_time else DEFAULT_TF
    outputs = {}
    for job_type in ['simulate', 'sensitivity', 'flux_diagram']:
        job_path = getattr(args, f'{job_type}_path')
        outputs[job_type] = job_path[0] if job_path else os.path.join(os.path.dirname(model_path), job_type)

    return model_path, fuel, Ts, Ps, phis, tf, outputs

def find_molecule(molecule, spc_dict):
    # Find the molecule according to the smiles or the label information
    if molecule in spc_dict:
        return {'label': molecule, 'smi': spc_dict[molecule].molecules[0].to_smiles()}
    try:
        mol = Molecule().from_smiles(molecule)
    except:
        raise ValueError(f'Invalid molecule input {molecule} should be a SMILES string or the species label')
    for label, spc in spc_dict.items():
        if spc.is_isomorphic(mol):
            return {'label': 'label', 'smi': spc.molecules[0].to_smiles()}


def run_simulation(input_path, chemkin_path, spc_dict_path, work_dir='.'):
    py_file = f"{RMG_PATH}/scripts/simulate.py"
    cmd = f'python "{py_file}" ' \
          f'"{input_path}" "{chemkin_path}" "{spc_dict_path}";'
    try:
        output = subprocess.check_output(cmd,
                                         stderr=subprocess.STDOUT,
                                         cwd=work_dir,
                                         shell=True,
                                         timeout=DEFAULT_JOB_TIME_OUT)
        return True
    except subprocess.CalledProcessError as e:
        print(f'Simulation failed. Got (e.output)')
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
                                         timeout=DEFAULT_JOB_TIME_OUT)
        return True
    except subprocess.CalledProcessError as e:
        print(f'Flux diagram failed. Got (e.output)')
        return


def generate_rmg_input_file(spec):
    rmg_sim_input = RMGSimulateInput(spec)
    rmg_sim_input.save()


def pooling_jobs(pool):

    org_len = len(pool)
    while org_len == len(pool):
        print(f'{datetime.datetime.now()}: Running: {pool}')
        for job_id in pool:
            cmd = f'squeue --job {job_id}'
            try:
                output = subprocess.check_output(cmd, shell=True)
            except:
                pool.remove(job_id)
                print(f'Job {job_id} is finished.')
                return
            else:
                if len(output.splitlines()) == 1:
                    pool.remove(job_id)
                    print(f'Job {job_id} is finished.')
                    return
        time.sleep(120)


def main():

    model_path, fuel, Ts, Ps, phis, tf, outputs = parse_arguments()

    chemkin_path = os.path.join(model_path, 'chem_annotated.inp')
    spc_dict_path = os.path.join(model_path, 'species_dictionary.txt')

    spc_dict = load_species_dictionary(spc_dict_path)
    spc_num = len(spc_dict)

    fuel = find_molecule(fuel, spc_dict)

    for T, P, phi in itertools.product(Ts, Ps, phis):

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
        spec.update({'save_path': input_path})
        generate_rmg_input_file(spec)
            
        done = run_simulation(input_path, chemkin_path, spc_dict, work_dir)
        
        # Get ignition delay
        if done:
            try:
                df = pd.read_csv(os.path.join(work_dir, 'solver',
                                              f'simulation_1_{spc_num}.csv'))
                df = df.set_index('Time (s)')
                idt = df['OH(6)'].idxmax()
            except:
                print('Cannot get ignition delay time. Use default time {tf}')
                idt = tf
        
        # Generate flux diagram
        work_dir = os.path.join(outputs['flux_diagram'], folder_name,)
        os.makedirs(work_dir, exist_ok=True)
        input_path = os.path.join(work_dir, 'input.py')
        spec.update({'save_path': input_path,
                     'tf': idt * 10})
        generate_rmg_input_file(spec)

        generate_flux_diagram(input_path, chemkin_path, spc_dict, work_dir)

        # Create sens input
        work_dir = os.path.join(outputs['simulate'], folder_name,)
        os.makedirs(work_dir, exist_ok=True)
        input_path = os.path.join(work_dir, 'input.py')
        sens_spc = [{'smiles': '[OH]', },
                    {'smiles': '[H]', },
                    {'smiles': 'O[O]',},]
        spec.update({'save_path': input_path,
                     'sens_spc': sens_spc,
                     'tf': idt})
        generate_rmg_input_file(spec)

    # Sensitivity usually takes longer, use queue software
    job_pool = []
    for T, P, phi in itertools.product(Ts, Ps, phis):
        print(f'Running sensitivity T: {T}, P: {P}, phi:{phi}')

        folder_name = f'{T}_{P}_{phi}'
        work_dir = os.path.join(outputs['simulate'], folder_name,)
        os.makedirs(work_dir, exist_ok=True)

        input_path = os.path.join(work_dir, 'input.py')
        submit_script_path = os.path.join(work_dir, 'submit_script.sh')
        content = f"""conda activate rmg_env
python "{RMG_PATH}/scripts/simulate.py" "{input_path}" "{chemkin_path}" "{spc_dict_path}"    
conda deactivate
        """
        spec = {
            'partition': 'long',
            'job_name': f'S{T}_{P}_{phi}',
            'n_processor': 1,
            'mem_per_cpu': 8000,  # MB,
            'job_time': '10-00',
            'content': content,
            'save_path': submit_script_path,
        }
        submit_script = SLURMSubmitScript(spec)
        submit_script.save()

        cmd = 'sbatch submit_script.sh'
        try:
            output = subprocess.check_output(cmd, cwd=work_dir, shell=True)
        except subprocess.CalledProcessError:
            continue
        else:
            job_id = int(output.strip().split()[3])
            job_pool.append(job_id)
            time.sleep(2)

        if len(job_pool) >= 3:
            pooling_jobs(job_pool)


if __name__ == '__main__':
    main()
