#!/usr/bin/env python3
# encoding: utf-8

import argparse
import datetime
import itertools
import os
import shutil
import sqlite3
import subprocess
import time

import pandas as pd
from rmgpy.molecule.molecule import Molecule
from rmgpy.chemkin import load_species_dictionary

from easy_rmg_model.common import regularize_path
from easy_rmg_model.settings import RMG_PATH
from easy_rmg_model.template_writer.input import RMGSimulateInput
from easy_rmg_model.template_writer.submit import SLURMSubmitScript



DEFAULT_TS = [700, 800, 900, 1000, 1200, 1400, 1600, 2000]  # in Kelvin
DEFAULT_PS = [10, 30, 50]  # in atm
DEFAULT_PHIS = [0.5, 1.0, 1.5]
DEFAULT_TF = 10.0  # in seconds
DEFAULT_JOB_TIME_OUT =  5 * 60 * 60  # 5 hours
CHECK_POOLING_JOB = 2 * 60  # 2 min

def parse_arguments():

    parser = argparse.ArgumentParser()
    parser.add_argument('sensitivity_path', nargs=1, help='Path to save sensitivity results')

    args = parser.parse_args()

    model_path = regularize_path(args.model_path[0])
    sens_path = regularize_path(args.sensitivity_path[0])

    return sens_path

    
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

    model_path, sens_path = parse_arguments()

    chemkin_path = os.path.join(model_path, 'chem_annotated.inp')
    spc_dict_path = os.path.join(model_path, 'species_dictionary.txt')
    
    # File structure in sens_path
    # /condition/[input, submit_script.sh]
    jobs = os.listdir(sens_path)
    
    job_pool = []
    for job in jobs:
        if os.path.isdir(job):
            # job is formatted as 'T_P_phi'
            T, P, phi = job.split('_')
            # Sensitivity usually takes longer, use queue software
            print(f'Running sensitivity T: {T}, P: {P}, phi: {phi}')
            work_dir = os.path.join(sens_path, job,)
            os.makedirs(work_dir, exist_ok=True)

            input_path = os.path.join(work_dir, 'input.py')
            submit_script_path = os.path.join(work_dir, 'submit_script.sh')
            if not os.path.isfile(submit_script_path):
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
