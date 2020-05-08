#!/usr/bin/env python3
# encoding: utf-8
"""
The toolbox for works related to RMG thermo database
"""

import os

from rmgpy import settings as rmg_settings
from rmgpy.data.thermo import ThermoDatabase, ThermoLibrary


def load_thermo_lib_by_path(path: str,
                            thermo_db: ThermoDatabase):
    """
    Load thermo library given its path. This is really helpful when the
    library is not located in the RMG-database.

    Args:
        path (str): Path to thermo library file
        thermo_database (ThermoDatabase): RMG thermo database object
    """
    if not os.path.exists(path):
       raise ValueError(f'The library file {path} does not exist.')

    if path not in thermo_db.library_order:
        lib = ThermoLibrary()
        try:
            lib.load(path,
                     ThermoDatabase().local_context,
                     ThermoDatabase().global_context)
        except:
            raise ValueError(f'The library file {path} is not vaild.')
            return
        else:
            lib.label = path
            thermo_db.libraries[lib.label] = lib
            thermo_db.library_order.append(lib.label)
            print(f'Loading thermo library {os.path.split(path)[1]} '
                  f'from {os.path.split(path)[0]} ...')
    else:
        print(f'The library {path} has already been loaded')


def load_thermo_database(libraries: Optional[list] = None):
    """
    A helper function to load thermo database given libraries used

    Args:
        libraries (Optional[list]): A list of libraries to be imported. All
                                    libraies will be imported if not assigned.
    """
    thermo_db_path = os.path.join(rmg_settings['database.directory'],
                                  'input', 'thermo')
    thermo_db = ThermoDatabase()
    thermo_db.load(thermo_db_path, libraries=libraries)
    return thermo_db
