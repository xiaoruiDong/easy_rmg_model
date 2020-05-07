#!/usr/bin/env python3
# encoding: utf-8
"""
The toolbox for works related chemkin files
"""


def get_species_aliases(chemkin_path: str, key: str = 'rmg'):
    """
    Get the species aliases from RMG generated chemkin file.

    Args:
        chemkin_path (str): The path to Chemkin file.
        key (str): Whether the ``key`` is Chemkin labels or rmg labels`
    Returns:
        dict: A dictinary for converting labels.
    """
    spc_aliases = {}
    read_mode = False

    with open(chemkin_path, 'r') as f:
        line = f.readline()
        while line != '':
            line = line.strip()
            if 'SPECIES' in line.upper() and not read_mode:
                read_mode = True
            elif 'END' == line.upper() and read_mode:
                read_mode = False
                break
            elif read_mode and '!' in line and line.split('!'):
                chemkin_name, rmg_name = [name.strip()
                                          for name in line.split('!')]
                if len(chemkin_name.split()) == 1 and len(rmg_name.split()) == 1:
                    spc_aliases[rmg_name] = chemkin_name
            line = f.readline()

    if key.lower() == 'chemkin':
        spc_aliases = {chemkin_name: rmg_name for rmg_name,
                       chemkin_name in spc_aliases.items()}
    return spc_aliases
