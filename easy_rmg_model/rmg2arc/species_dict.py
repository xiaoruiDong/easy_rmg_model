#!/usr/bin/env python3
# encoding: utf-8
"""
The toolbox for species dictionary involved operations
"""

import os
from typing import Optional, Union

from rmgpy.chemkin import load_species_dictionary

def load_spc_dict(spc_dict: Union[dict, str]) -> dict:
    """
    A helper function to consistent the species dictionary dict instance

    Args:
        spc_dict (Union[dict, str]): The path to species dictionary or the
                                     actual species dictionary

    Returns:
        dict: The species dictionary ``dict`` instance
    """
    if isinstance(spc_dict, dict):
        return spc_dict
    elif isinstance(spc_dict, str) and os.path.isfile(spc_dict):
        spc_dict = load_species_dictionary(spc_dict)
    else:
        raise ValueError(f'Invalid species dictionary {spc_dict}')


def expand_spc_info_by_spc_dict(spc_info: dict,
                                spc_dict: Union[str, dict],
                                spc_aliases: Optional[dict]):
    """
    Expand the given spc_info ``dict`` by using species dictionary. The updates are
    based on the label information.

    Args:
        spc_info: The species info, which should at least contains label information
        spc_dict (Union[dict, str]): The path to species dictionary or the
                                     actual species dictionary
        spc_dict (Optional[dict]): In case label systems are different, you can provide
                                   aliases to help convert the names

    Returns:
        dict: The updated species information
    """

    spc_dict = load_spc_dict(spc_dict)

    for label, spc in spc_info.items():
        if spc_aliases:
            label = spc_aliases[label]
        try:
            rmg_spc = spc_dict[label]
        except KeyError:
            print(f'Warning: Cannot find the species {spc["label"]} in species dictionary.')
        else:
            try:
                smiles = rmg_spc.molecule[0].to_smiles()
                charge = rmg_spc.molecule[0].get_net_charge()
                adjlist = rmg_spc.to_adjacency_list()
            except:
                print(f'Warning: Cannot generate geom info for the species {label}.')
            else:
                spc.update({'smiles': smiles,
                            'adjlist': adjlist, 'multiplicity': spc.multiplicity,
                            'charge': charge, })
    return spc_dict
