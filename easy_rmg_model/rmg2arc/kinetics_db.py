#!/usr/bin/env python3
# encoding: utf-8

"""
The toolbox for works related to RMG kinetics database
"""

import glob
import os
from copy import deepcopy
from typing import Optional

from rmgpy import settings as rmg_settings
from rmgpy.data.kinetics.database import KineticsDatabase
from rmgpy.data.kinetics.library import KineticsLibrary


def load_kinetics_lib_by_path(path: str,
                              kinetics_db: KineticsDatabase,
                              reload: bool = False):
    """
    Load kinetics library given its library path and store it into
    the given RMG KineticsDatabase instance

    Args:
        path (str): Path to kinetics library file
        kinetics_database (KineticsDatabase): RMG kinetics database object
        reload (bool): Whether to reload the library if this library is in the KineticsDatabase
    """
    lib = KineticsLibrary()
    try:
        lib.load(path,
                 KineticsDatabase().local_context,
                 KineticsDatabase().global_context)
    except FileNotFoundError:
        print(f'The library file {path} does not exist.')
    except (SyntaxError, ImportError):
        print(f'The library file {path} is not valid.')
    else:
        if path in kinetics_db.library_order and not reload:
            print(f'The library {path} has already been loaded.')
            return
        elif path not in kinetics_db.library_order:
            kinetics_db.library_order.append(path)
        lib.label = path
        lib.name = path
        kinetics_db.libraries[lib.label] = lib
        print(f'The kinetics library {path} is loaded.')


def load_kinetics_database(families: str = 'defaults',
                           libraries: Optional[list] = None):
    """
    A helper function to load kinetics database given libraries used

    Args:
        libraries (Optional[list]): A list of libraries to be imported. All
                                    libraies will be imported if not assigned.
    """
    kinetics_db_path = os.path.join(rmg_settings['database.directory'], 'kinetics')
    kinetics_db = KineticsDatabase()
    kinetics_db.load(kinetics_db_path, families=families, libraries=libraries)
    return kinetics_db


def find_kinetics_libs(path: str):
    """
    This function search for the kinetics library
    based on ``RMG libraries/kinetics/*.py``

    Args:
        path (str): The path to project directories

    Returns:
        kinetics_lib_list (list): Entries of the path to kinetics libraries
    """
    # Initiate the kinetics lib list
    kinetics_lib_list = list()
    # Try to find all kinetics library according to the species dictionary
    spc_dict_list = glob.glob(os.path.join(path, '**', 'dictionary.txt'), recursive=True)

    for spc_dict in spc_dict_list:
        folder_path = os.path.dirname(spc_dict)
        kinetics_lib_path = os.path.join(folder_path, 'reactions.py')

        if os.path.isfile(kinetics_lib_path):
            kinetics_lib_list.append(kinetics_lib_path)
            print(f'Find kinetics library at {kinetics_lib_path}')
    return kinetics_lib_list


def merge_kinetics_lib(base_lib: KineticsLibrary,
                       lib_to_add: KineticsLibrary,
                       tbd_lib: KineticsLibrary):
    """
    Merge one library (lib_to_add) into the base library.

    Args:
        base_lib (RMG KineticsLibrary): The library used as the base
        lib_to_add (RMG KineticsLibrary): The library to be added to the base library
    """
    for rxn_to_add in lib_to_add.entries.values():
        formula = rxn_to_add.item.__str__()
        for base_rxn in base_lib.entries.values():
            formula_base = base_rxn.item.__str__()
            if formula != formula_base:
                continue
            if rxn_to_add.item.is_isomorphic(base_rxn.item):
                in_base = True
                break
        else:
            in_base = False

        if in_base:
            # Temporary solution
            continue
        else:
            rxn_to_add.index = len(base_lib.entries)
            base_lib.entries.update({rxn_to_add.index: deepcopy(rxn_to_add)})
            rxn_to_add.short_desc += f"\nMerged into the base library {base_lib.label}"
            print(f'The kinetics of {rxn_to_add.label} from {lib_to_add.label} is merged.')
