#!/usr/bin/env python3
# encoding: utf-8

"""
The toolbox for works related to RMG kinetics database
"""

import os
from rmgpy.data.kinetics import KineticsDatabase, KineticsLibrary
from typing import Optional
from rmgpy import settings as rmg_settings

def load_kinetics_database(libraries: Optional[list] = None):
    """
    A helper function to load thermo database given libraries used

    Args:
        libraries (Optional[list]): A list of libraries to be imported. All
                                    libraies will be imported if not assigned.
    """
    kinetics_db_path = os.path.join(rmg_settings['database.directory'], 'kinetics')
    kinetics_db = KineticsDatabase()
    kinetics_db.load(kinetics_db_path, libraries=libraries, families=[])
    kinetics_db.library_order = [(lib, 'Reaction Library') for lib in libraries]
    return kinetics_db

def load_kinetics_lib_by_path(path: str,
                            kinetics_db: KineticsDatabase,
                            reload: bool = True):
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
        print(f'The kineticsdynamics library {path} is loaded.')

