#!/usr/bin/env python3
# encoding: utf-8
"""
The toolbox for species dictionary involved operations
"""

import os
from typing import Optional, Union

from rmgpy.chemkin import load_species_dictionary
from rmgpy.molecule.molecule import Molecule
from rmgpy.species import Species

from easy_rmg_model.species.converter import xyz_to_mol


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
        return load_species_dictionary(spc_dict)
    else:
        raise ValueError(f'Invalid species dictionary {spc_dict}')


def expand_spc_info_by_spc_dict(spc_info: dict,
                                spc_dict: Union[str, dict],
                                spc_aliases: Optional[dict] = None,
                                ) -> dict:
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
            molecule = spc_dict[label].molecule[0]
        except KeyError:
            print(f'Warning: Cannot find the species {spc["label"]} in species dictionary.')
        else:
            for attribute in ['smiles', 'charge', 'multiplicity', 'adjlist']:
                if attribute in spc:
                    continue
                try:
                    if attribute == 'smiles':
                        geom_info[attribute] = molecule.to_smiles()
                    elif attribute == 'charge':
                        geom_info[attribute] = molecule.get_net_charge()
                    elif attribute == 'multiplicity':
                        geom_info[attribute] = molecule.get_net_charge()
                    else:
                        geom_info[attribute] = molecule.to_adjacency_list()
                except:
                    print(f'Warning: Cannot generate {attribute} for the species {label}.')
    return spc_info


def find_species_from_spc_dict(spc: Union[dict, Species, Molecule],
                               spc_dict: Union[str, dict],
                               ) -> Optional[Species]:
    """
    Find a species from a species dictionary. It will firstly check if any label match, then
    compare the string geometric representation, then the graphical geometric representation.

    Args:
        spc (Union[dict, Species, Molecule]): A data structure which stores molecule info.
        spc_dict (Union[str, dict]): The path or the actual dict of species dictionary.

    Returns:
        Optional[Species]: the species stored in the dictionary if match, ``None`` otherwise.
    """
    spc_dict = load_spc_dict(spc_dict)

    if isinstance(spc, dict):
        if not 'label' in spc:
            raise ValueError('Invalid species info which should at least label info.')
        label = spc['label']
        if label in spc_dict:
            # Species dictionary has a same-label entry
            # Try cheap method before comparing isomorphism
            if 'smiles' in spc \
                    and spc['smiles'] == spc_dict[label].molecule[0].to_smiles():
                # label and smiles are identical
                return label, spc_dict[label]
            if 'adjlist' in spc \
                    and spc['adjlist'] == spc_dict[label].molecule[0].to_smiles():
                # label and adjacency list are identical
                return label, spc_dict[label]
            if 'smiles' in spc:
                # smiles are different (may be using non-canonical smiles)
                species = Species().from_smiles(spc['smiles'])
            elif 'adjlist' in spc:
                # smiles are different (may be different atom order)
                species = Species().from_adjacency_list(spc['adjlist'])
            elif 'xyz' in spc:
                # Generate the species from xyz
                species = Species(label=label)
                species.set_structure(xyz_to_mol(spc['xyz']).to_smiles())
            else:
                raise ValueError('Invalid species info which has no geom info.')
            if spc_dict[label].is_isomorphic(species):
                return label, spc_dict[label]

    elif isinstance(spc, (Molecule, Species)):
        if hasattr(spc, 'label') and spc.label in spc_dict:
            if spc.to_smiles() == spc_dict[spc.label].molecule[0].to_smiles():
                return label, spc_dict[spc.label]
            if spc_dict[spc.label].is_isomorphic(spc):
                return label, spc_dict[spc.label]
        species = spc

    for species_in_dict in spc_dict.values():
            if species_in_dict.is_isomorphic(species):
                return label, species_in_dict
    return None, None


def species_from_spc_info(spc: dict,
                          resonance: bool = True,
                          ) -> Optional[Species]:
    """
    Generate a RMG Species from species info.

    Args:
        spc (dict): A single species info contains the species geom info.
        resonance (bool): Whether generate resonance geom in the species dictionary.

    Returns:
        Species: The Species instance from spc.
    """
    label = spc['label']
    if 'adjlist' in spc:
        return Species(label=label).from_adjacency_list(spc['adjlist'])
    elif 'smiles' in spc:
        return Species(label=label).from_smiles(spc['smiles'])
    elif 'xyz' in spc:
        species = Species(label=label)
        species.set_structure(xyz_to_mol(spc['xyz']).to_smiles())
        return species
    # else: return None
    # TODO: Add warning


def spc_dict_from_spc_info(spc_info: dict, resonance: bool = True) -> dict:
    """
    Generate a species dictionary from species info.

    Args:
        spc_info (dict): Species info contains the label and species geom info.
        resonance (bool): Whether generate resonance geom in the species dictionary.

    Returns:
        dict: The species dictionary generated from the spc_info.
    """
    spc_dict = {}
    for label, spc in spc_info.items():
        species = species_from_spc_info(spc)
        if not species:
            continue
        if resonance:
            species.generate_resonance_structures()
        spc_dict[label] = species
    return spc_dict
