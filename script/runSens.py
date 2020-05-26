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
from easy_rmg_model.settings import (CONDA_ENV,
                                     PHIS_POST_PROCESS,
                                     POOL_SIZE_POST_PROCESS,
                                     POOL_CHECK_FREQ_POST_PROCESS,
                                     PS_POST_PROCESS,
                                     QUEUE_SPEC_POST_PROCESS,
                                     RMG_PATH,
                                     TS_POST_PROCESS)
from easy_rmg_model.template_writer.input import RMGSimulateInput
from easy_rmg_model.template_writer.submit import SLURMSubmitScript


def parse_arguments():

    parser = argparse.ArgumentParser()
    parser.add_argument('model_path', type=str, nargs=1,
                        help='The folder path to RMG model')
    parser.add_argument('sensitivity_path', type=str, nargs=1,
                        help='Path to save sensitivity results')
    parser.add_argument('-T', '--temperature', nargs='+',
                        help='Temperatures [K]')
    parser.add_argument('-P', '--pressure', nargs='+', help='Pressures [atm]')
    parser.add_argument('-p', '--phi', nargs='+',
                        help='Fue-to-air equivalence ratio')
    parser.add_argument('--pool_size', nargs='?', type=int,
                        help='The size of the job pool')

    args = parser.parse_args()

    model_path = regularize_path(args.model_path[0])
    sens_path = regularize_path(args.sensitivity_path[0])
    Ts = [float(T) for T in args.temperature] if args.temperature else TS_POST_PROCESS
    Ps = [float(P) for P in args.pressure] if args.pressure else PS_POST_PROCESS
    phis = [float(phi) for phi in args.phi] if args.phi else PHIS_POST_PROCESS
    pool_size = POOL_SIZE_POST_PROCESS if not args.pool_size else args.pool_size

    return model_path, sens_path, Ts, Ps, phis, pool_size


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

    model_path, sens_path, Ts, Ps, phis, pool_size = parse_arguments()

    print(f'Using RMG model from {model_path}...')
    chemkin_path = os.path.join(model_path, 'chem_annotated.inp')
    spc_dict_path = os.path.join(model_path, 'species_dictionary.txt')

    # File structure in sens_path
    # /condition/[input, submit_script.sh]
    jobs = os.listdir(sens_path)

    job_pool = []
    for job in jobs:
        work_dir = os.path.join(sens_path, job,)
        if os.path.isdir(work_dir):

            # job is formatted as 'T_P_phi'
            try:
                T, P, phi = [float(item) for item in job.split('_')]
            except ValueError:
                continue
            if not (T in Ts and P in Ps and phi in phis):
                continue

            print(f'Running sensitivity T: {T}, P: {P}, phi: {phi}')

            # Sensitivity usually takes longer, use queue software
            input_path = os.path.join(work_dir, 'input.py')
            submit_script_path = os.path.join(work_dir, 'submit_script.sh')

            content = f"conda activate {CONDA_ENV}\n" if CONDA_ENV else ""
            content += f'python "{RMG_PATH}/scripts/simulate.py" "{input_path}" "{chemkin_path}" "{spc_dict_path}"'
            content += "conda deactivate" if CONDA_ENV else ""

            spec = {**QUEUE_SPEC_POST_PROCESS,
                    **{'job_name': f'S{T}_{P}_{phi}',
                       'content': content,
                       'save_path': submit_script_path, }
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

        if len(job_pool) >= pool_size:
            pooling_jobs(job_pool)


if __name__ == '__main__':
    main()
