#!/usr/bin/env python3
# encoding: utf-8

import datetime
import json
import logging
import os
import shutil
import yaml

import numpy as np
import matplotlib.pyplot as plt

from arc.common import (determine_symmetry,
                        is_same_pivot)

from arc.job.trsh import (scan_quality_check,
                          trsh_scan_job)
from easy_rmg_model.job.trsh import determine_convergence

from arc.parser import (parse_1d_scan_energies,
                        parse_scan_args,
                        parse_trajectory,
                        parse_xyz_from_file)
from easy_rmg_model.parser import (parse_charge_and_mult,
                                   parse_species_in_arc_input,
                                   parse_termination_time)

from arc.plotter import plot_1d_rotor_scan

from arc.species.converter import (compare_confs,
                                   molecules_from_xyz,
                                   xyz_to_xyz_file_format)
from easy_rmg_model.species.converter import (xyz_to_mol,
                                              xyz_to_rotors_dict,
                                              xyz_to_xyz_file)

from arc.species.species import ARCSpecies, determine_rotor_symmetry, enumerate_bonds

from easy_rmg_model.template_writer.input import ArkaneSpecies, GaussianInput

from arkane.statmech import is_linear

from rdmc.mol import RDKitMol
try:
    # openbabel 3
    from openbabel import pybel
except:
    # openbabel 2
    import pybel


def find_all_species_from_calcs_path(calc_path):
    """
    A function used to find all species in the calcs folder.
    """
    spc_info = {}
    species_path = os.path.join(calc_path, 'Species')
    for spc_label in os.listdir(species_path):
        path = os.path.join(species_path, spc_label)
        if os.path.isdir(path):
            spc_info.update(
                {spc_label: {'label': spc_label, 'directory': path, 'ts': False}})
    return spc_info


def find_all_species_from_database(db_path):
    """
    A function used to find all species in the calcs folder.
    """
    spc_info = {}
    for root, _, files in os.walk(db_path):
        if 'info.txt' in files:
            label = root.replace(db_path, '')
            spc_info[label] = {'label': label, 'directory': root, 'ts': False}
    return spc_info


def find_all_species_in_arc_project(project_path):
    """
    A function used to find all species in the project.
    """
    calc_path = os.path.join(project_path, 'calcs')
    input_path = os.path.join(project_path, 'input.yml')

    spc_info = dict()
    spc_info.update(parse_species_in_arc_input(input_path))
    calc_spc_info = find_all_species_from_calcs_path(calc_path)

    for spc, info in spc_info.items():
        info.update(calc_spc_info[spc])
    return spc_info


def classify_jobs(spc,
                  job_types=['composite', 'scan', 'freq', 'irc', 'opt'],
                  output_file_name='output.out'):
    """
    A function used to classify all of the jobs under the species calculation
    directory by the output files defined by ``output_file_name``. The classification
    is naively done by assuming we use job type name in the path, e.g., 'scan_a1'.
    """

    if 'directory' not in spc:
        raise RuntimeError('Encounter a species without any file location information.')

    new_info = {job_type: [] for job_type in job_types}

    for root, _, files in os.walk(spc['directory']):
        if not output_file_name in files:
            continue
        for job_type in job_types:
            if job_type in root:
                new_info[job_type].append(os.path.join(root, output_file_name))
                break

    spc.update(new_info)
    return spc


def find_latest_terminated_job(spc, job_types=['composite', 'freq']):
    """
    A function used to find the latest jobs of given types
    """
    for job_type in job_types:
        path, t_time = '', datetime.datetime(1970, 1, 1)
        for file in spc[job_type]:
            try:
                file_ttime = parse_termination_time(file)
            except Exception as e:
                print('problem', e)
                continue
            if file_ttime > t_time:
                path, t_time = file, file_ttime
        spc[job_type] = path
    return spc


def check_converge_and_geom_consist(spc,
                                    job_types=['composite', 'freq'],
                                    basis_job='composite'):

    basis_xyz = None
    done = determine_convergence(spc[basis_job], basis_job, spc['ts'])
    if done:
        try:
            basis_xyz = parse_xyz_from_file(spc[basis_job])
        except:
            pass
        else:
            if 'species' in spc \
                    and not spc['species'].check_xyz_isomorphism(xyz=basis_xyz):
                basis_xyz = None

    if not basis_xyz:
        return

    spc['geom'] = basis_xyz
    spc['final_xyz'] = basis_xyz
    spc['checkfile'] = ''
    spc['charge'], spc['multiplicity'] = parse_charge_and_mult(spc[basis_job])
    try:
        spc['smiles'] = xyz_to_mol(spc['geom']).to_smiles()
    except:
        try:
            spc['smiles'] = molecules_from_xyz(spc['geom'],
                                            spc['multiplicity'],
                                            spc['charge'])[0].to_smiles()
        except:
            spc['smiles'] = ''
            logging.warning(f"Cannot generate SMILES for {spc['label']}")

    # Assume checkfile is located under the same dir and named check.chk
    check_path = os.path.join(os.path.dirname(spc[basis_job]), 'check.chk')
    if os.path.isfile(check_path):
        spc['checkfile'] = check_path

    for job_type in job_types:

        if job_type == basis_job:
            continue

        xyz_to_compare = None
        done = determine_convergence(spc[job_type], job_type, spc['ts'])
        if done:
            try:
                xyz_to_compare = parse_xyz_from_file(spc[job_type])
            except:
                pass

        if not xyz_to_compare or not compare_confs(basis_xyz, xyz_to_compare):
            # It seems like only basis job is well done
            spc[job_type] = ''
            continue

    return spc


def find_rotors_from_xyz(spc):
    """
    A function used to generate rotors dict from xyz.
    """
    rotors_dict = xyz_to_rotors_dict(spc['geom'])
    if rotors_dict is None:
        return
    spc['rotors_dict'] = {ind: rotors_dict for ind,
                          rotors_dict in enumerate(rotors_dict)}
    spc['number_of_rotors'] = len(rotors_dict)
    return spc


def filter_scans(spc, scan_filter='latest'):
    """
    A function used to filter and keep 'non_frozen' or 'latest' scans.
    """
    good_scans = []

    for rotor_dict in spc['rotors_dict'].values():
        rotor_dict['archived'] = []

    for scan_path in spc['scan']:

        done = determine_convergence(scan_path, 'scan')

        # Check if the scan is finished and its initial geom is consistent
        # with the basis xyz
        if done:
            try:
                init_xyz = parse_trajectory(scan_path)[0]
            except:
                continue
            else:
                if not compare_confs(init_xyz, spc['geom']):
                    continue

        # Parse the scan arguments
        try:
            scan_args = parse_scan_args(scan_path)
        except:
            continue

        for rotor in spc['rotors_dict'].values():
            # Find the rotor shares same pivots
            if is_same_pivot(scan_args['scan'], rotor['scan']):

                if scan_filter == 'non-frozen' and scan_args['freeze']:
                    # filter out constraint scans
                    rotor['archived'].append(scan_path)

                elif scan_filter == 'latest' and rotor['scan_path']:
                    # filter out non latest scans
                    time_1 = parse_termination_time(scan_path)
                    time_2 = parse_termination_time(rotor['scan_path'])
                    if time_1 <= time_2:
                        rotor['archived'].append(scan_path)
                        break
                rotor['scan_path'] = scan_path
                good_scans.append(scan_path)
                break
    # Only keeps good scans
    spc['scan'] = good_scans
    return spc


def check_scan_quality(spc):
    """
    A helper function used to get the status of rotor scans
    """

    for rotor in spc['rotors_dict'].values():

        path = rotor['scan_path']
        if path:
            scan_args = parse_scan_args(path)
            energies, _ = parse_1d_scan_energies(path)
            invalid, reason, _, actions = scan_quality_check(spc['label'], pivots=rotor['scan'][1:-1],
                                                             energies=energies, scan_res=scan_args['step_size'],
                                                             log_file=path)
        else:
            rotor['success'] = False
            rotor['invalidation_reason'] = 'Unknown'
            continue

        if not invalid:
            rotor['success'] = True
            rotor['symmetry'] = determine_rotor_symmetry(label=spc['label'],
                                                         pivots=rotor['scan'][1:3],
                                                         energies=energies)[0]
            continue

        if 'change conformer' in actions:
            print(
                spc['label'] + ': has a bad conformer orientation according to ' + str(rotor['scan']))
            xyz = xyz_to_xyz_file_format(actions['change conformer'])
            return {'label': spc['label'], 'change conformer': xyz}

        if 'barrier' in reason:
            rotor['success'] = False
            rotor['invalidation_reason'] = reason
            continue

        # Otherwise need to come up with troubleshooting methods
        species_scan_lists = [rotor['scan']]
        scan_trsh, scan_res = trsh_scan_job(spc['label'],
                                            scan_args['step_size'],
                                            rotor['scan'],
                                            species_scan_lists,
                                            actions,
                                            path)
        rotor['trsh_methods'] = [
            {'scan_trsh': scan_trsh, 'scan_res': scan_res}]
        rotor['archived'].append(rotor['scan_path'])
        spc['scan'].remove(rotor['scan_path'])

    return spc


def generate_summary(spc):
    """
    Generate summary report of the species jobs.
    """
    summary = ''
    for job_type in ['composite', 'sp', 'opt', 'freq']:
        if job_type in spc:
            summary += f'{job_type}: '
            summary += 'succeeded\n' if spc[job_type] else 'failed\n'

    for rotor in spc['rotors_dict'].values():
        summary += f'scan_{str(rotor["scan"])}: '
        if rotor['success'] or \
            (not rotor['success'] and 'barrier' in rotor['invalidation_reason']):
            summary += 'succeeded\n'
        else:
            summary += 'failed\n'
    spc['summary'] = summary
    spc['success'] = False if 'failed' in summary else True
    return summary


def generate_geom_info(spc, xyz_file=None):
    if not 'geom' in spc:
        xyz_file = xyz_file or os.path.join(spc['directory'], 'xyz.txt')
        try:
            spc['geom'] = parse_xyz_from_file(xyz_file)
        except:
            return
    try:
        mol = xyz_to_mol(spc['geom'])
    except:
        return

    spc['smiles'] = mol.to_smiles()
    spc['mol'] = mol.to_adjacency_list()
    spc['bond_dict'] = enumerate_bonds(mol)
    spc['atom_dict'] = mol.get_element_count()
    spc['linear'] = is_linear(coordinates=np.array(spc['geom']['coords']))
    spc['external_symmetry'], spc['optical_isomers'] = determine_symmetry(
        spc['geom'])
    return spc


def generate_arkane_input(spc,
                          arkane_spec,
                          save_dir=None,
                          template_file=None):

    save_dir = save_dir or spc['directory']

    if template_file:
        arkane_spec['template_file'] = template_file

    bac = [(True, 'species_with_bac.py'),
           (False, 'species_no_bac.py')]
    for use_bac, file_name in bac:
        extra_dict = {'use_bond_corrections': use_bac,
                      'save_path': os.path.join(save_dir, file_name)}
        arkane = ArkaneSpecies({**spc, **arkane_spec, **extra_dict})
        arkane.save()


def generate_gaussian_input(spc, gaussian_spec, scan_spec=None):
    if not ('save_path' in gaussian_spec and gaussian_spec['save_path']):
        save_dir, file_name = '', 'input.gjf'

    if gaussian_spec['job_type'] != 'scan':
        if not save_dir:
            gaussian_spec['save_path'] = os.path.join(spc['directory'],
                                                    gaussian_spec['job_type'],
                                                    file_name)
        gaussian = GaussianInput({**spc, **gaussian_spec})

    elif not scan_spec or 'scan' not in scan_spec:
        raise Exception('Need to assign scan_spec when dealing with scan jobs.')

    else:
        if not save_dir:
            gaussian_spec['save_path'] = os.path.join(spc['directory'],
                                                      f'scan_{"_".join([str(i) for i in scan_spec["scan"]])}',
                                                      file_name)
        gaussian = GaussianInput({**spc, **gaussian_spec, **scan_spec})

    gaussian.save()


def transfer_species_jobs(spc, new_dir, output_file_name='output.out'):
    for job_type in ['composite', 'sp', 'opt', 'freq']:
        if job_type in spc:
            os.makedirs(os.path.join(new_dir, job_type), exist_ok=True)
            if spc[job_type]:
                shutil.copy(spc[job_type], os.path.join(
                    new_dir, job_type, output_file_name))
                spc[job_type] = os.path.join(
                    new_dir, job_type, output_file_name)

    for rotor in spc['rotors_dict'].values():
        new_rotor_dir = os.path.join(new_dir, f'scan_{str(rotor["scan"])}')
        os.makedirs(new_rotor_dir, exist_ok=True)
        if rotor['success'] or \
            (not rotor['success'] and 'barrier' in rotor['invalidation_reason']):
            new_rotor_path = os.path.join(new_rotor_dir, output_file_name)
            shutil.copy(rotor['scan_path'], new_rotor_path,)
            spc['scan'].remove(rotor['scan_path'])
            spc['scan'].append(new_rotor_path)
            rotor['scan_path'] = new_rotor_path
        else:
            with open(os.path.join(new_rotor_dir, 'trsh.txt'), 'w') as trsh_f:
                trsh_f.write(json.dumps(rotor['trsh_methods']))
        for file_index, archived in enumerate(rotor['archived']):
            shutil.copy(archived, os.path.join(
                new_rotor_dir, str(file_index), output_file_name))


def transfer_to_database(spc, database_path, output_file_name='output.out'):

    # Create a new folder to store
    if 'smiles' not in spc:
        spc['smiles'] = xyz_to_mol(spc['geom']).to_smiles()

    for i in range(100):
        new_dir = os.path.join(database_path, spc['smiles'], str(i))
        try:
            os.makedirs(new_dir, exist_ok=False)
        except:
            continue
        else:
            break

    # make sure it is the updated summary
    generate_summary(spc)
    with open(os.path.join(new_dir, 'info.txt'), 'w') as info:
        info.write(spc['summary'])

    transfer_species_jobs(spc, new_dir, output_file_name)

    spc['directory'] = new_dir
    xyz_to_xyz_file(spc)
    for rotor in spc['rotors_dict'].values():
        try:
            energies, angles = parse_1d_scan_energies(rotor['scan_path'])
            plot_1d_rotor_scan(angles=angles,
                               energies=energies,
                               path=os.path.dirname(rotor['scan_path']),
                               scan=rotor['scan'])
        except:
            pass

    return spc
