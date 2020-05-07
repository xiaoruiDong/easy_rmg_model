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
