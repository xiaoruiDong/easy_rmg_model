#!/usr/bin/env python3
# encoding: utf-8
"""
The toolbox for works related to ARC input files
"""

from typing import Optional, Union

from easy_rmg_model.rmg2arc.species_dict import (expand_spc_info_by_spc_dict,
                                                 find_species_from_spc_dict,
                                                 spc_dict_from_spc_info)


def combine_spc_infos(*spc_infos: Union[list, tuple],
                      resonance: bool = True
                      ) -> list:
    """
    Combine species lists used in ARC input files

    Args:
        spc_infos (list): Many pieces of species info.
        resonance (bool): Generate resonance structures when checking isomorphism.

    Returns:
        dict: A species info combined from each pieces
    """
    base_spc_info = spc_infos[0]
    if len(spc_infos) == 1:
        raise ValueError('Only one species info is provided.')
    spc_dict = spc_dict_from_spc_info(base_spc_info, resonance=resonance)
    base_spc_info = expand_spc_info_by_spc_dict(base_spc_info, spc_dict)

    # Compare each spc_list to base list
    for spc_info in spc_infos[1:]:
        base_spc_info = combine_spc_info(base_spc_info,
                                         spc_info,
                                         spc_dict)
    return base_spc_info


def combine_spc_info(spc_info1: dict,
                     spc_info2: dict,
                     spc_dict: Optional[dict] = None,
                     resonance: bool = True,
                    ) -> dict:
    """
    Combine two spc_infos. The major challenges are smiles and adjacency list are not unique, though
    comparing them are relatively cheap, while isomorphism comparison is unique but expensive. This module
    first, tries to compare smiles and adjacency list, if not match, will compare structure. It can take
    the benefit of a species dictionary, if that is provided, to avoid generating species repeatedly.

    Args:
        spc_info1 (dict): The first piece of species info.
        spc_info2 (dict): The second piece of species info.
        spc_dict (Optional[dict]): You can provide a species dictionary to avoid repeated generating
                                   Species instance.
        resonance (bool): Generate resonance structures when checking isomorphism.

    Returns:
        dict: The combined species info
    """

    if not spc_dict:
        spc_dict = spc_dict_from_spc_info(spc_info1)
    else:
        # spc_info1 should be consistent with spc_dict
        bad_items = {}
        for label, spc1 in spc_info1.items():
            if label not in spc_dict:
                # For now, only check the ones that have different labels
                try:
                    # See if it can be found in the dictionary
                    dict_label, species = find_species_from_spc_dict(spc1, spc_dict)
                except:
                    # if we cannot generate geom info, it is a bad item
                    bad_items[label] = None
                    continue
                else:
                    if dict_label:
                        # spc_info1 used a different label, replace it
                        bad_items[label] = dict_label
                    else:
                        # if spc_info1 contains new species, append it
                        spc_dict.update(spc_dict_from_spc_info({label: spc1},
                                                               resonance=resonance))
        # remove bad_items
        for label_in_info1, label_in_dict in bad_items.items():
            if label_in_dict:
                spc_info1[label_in_dict] = spc_info1[label_in_info1]
            del spc_info1[label_in_info1]

    spc_info1 = expand_spc_info_by_spc_dict(spc_info1, spc_dict)

    combined_spc_info = spc_info1.copy()

    for label, spc2 in spc_info2.items():
        if label in spc_info1:
            if 'smiles' in spc2 \
                    and spc2['smiles'] == spc_info1[label]['smiles']:
                # label and smiles are identical, skip
                continue
            if 'adjlist' in spc2 \
                    and spc2['adjlist'] == spc_info1[label]['adjlist']:
                # label and adjacency list are identical, skip
                continue
            try:
                # Compare if spc2 is the same thing as spc_info1[label]
                dict_label, species = find_species_from_spc_dict(spc2, {label: spc_dict[label]})
            except:
                # if we cannot generate geom info, it is a bad item
                continue
            if dict_label:
                # Means we find it in spc_info1, skip
                continue
        try:
            # Compare if spc2 is the same thing as spc_info1[label]
            dict_label, species = find_species_from_spc_dict(spc2, {label: spc_dict[label]})
        except:
            # If we cannot generate geom info, it is a bad item
            continue
        if not dict_label:
            # This is a new species
            combined_spc_info[label] = spc2
            spc_dict.update(spc_dict_from_spc_info({label: spc2}, resonance=resonance))

    return combined_spc_info
