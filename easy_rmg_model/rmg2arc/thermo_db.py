#!/usr/bin/env python3
# encoding: utf-8
"""
The toolbox for works related to RMG thermo database
"""

import os
from typing import Optional

from rmgpy import settings as rmg_settings
from rmgpy.data.thermo import ThermoDatabase, ThermoLibrary



def load_thermo_lib_by_path(path: str,
                            thermo_db: ThermoDatabase,
                            reload: bool = False):
    """
    Load thermo library given its library path and store it into
    the given RMG ThermoDatabase instance

    Args:
        path (str): Path to thermo library file
        thermo_database (ThermoDatabase): RMG thermo database object
        reload (bool): Whether to reload the library if this library is in the ThermoDatabase
    """
    lib = ThermoLibrary()
    try:
        lib.load(path,
                 ThermoDatabase().local_context,
                 ThermoDatabase().global_context)
    except FileNotFoundError:
        print(f'The library file {path} does not exist.')
    except (SyntaxError, ImportError):
        print(f'The library file {path} is not valid.')
    else:
        if path in thermo_db.library_order and not reload:
            print(f'The library {path} has already been loaded.')
        elif path not in thermo_db.library_order:
            thermo_db.library_order.append(lib.label)
        lib.label = path
        thermo_db.libraries[lib.label] = lib
        print(f'The thermodynamics library {path} is loaded.')


def load_thermo_database(libraries: Optional[list] = None):
    """
    A helper function to load thermo database given libraries used

    Args:
        libraries (Optional[list]): A list of libraries to be imported. All
                                    libraies will be imported if not assigned.
    """
    thermo_db_path = os.path.join(rmg_settings['database.directory'], 'thermo')
    thermo_db = ThermoDatabase()
    thermo_db.load(thermo_db_path, libraries=libraries)
    return thermo_db


def find_thermo_libs(path: str):
    """
    This function search for the thermo library
    based on ``RMG libraries/thermo/*.py``

    Args:
        path (str): The path to project directories

    Returns:
        thermo_lib_list (list): Entries of the path to thermo libraries
    """
    # Initiate the thermo lib list
    thermo_lib_list = list()
    # Walk through the dirs under path
    for root_p, dirs, _ in os.walk(path):
        if not dirs:
            continue
        # Use ARC folder organization to check thermo library
        chk_path = os.path.join(root_p, 'RMG libraries', 'thermo')
        if os.path.isdir(chk_path):
            # Find the corresponding thermo lib file
            thermo_lib = glob.glob(os.path.join(chk_path, '*.py'))
            if thermo_lib:
                thermo_lib_list.append(thermo_lib[0])
                print(f'Find thermo library at {thermo_lib[0]}')
    return thermo_lib_list
