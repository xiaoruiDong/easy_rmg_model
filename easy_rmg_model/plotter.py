#!/usr/bin/env python3
# encoding: utf-8

import os

import matplotlib.pyplot as plt
import numpy as np
from typing import Optional, Union

from rmgpy.data.base import Entry
from rmgpy.thermo.model import HeatCapacityModel


def compare_thermo(entry_list: Union[list, tuple],
                   thermo_property: str = 'free_energy',
                   reference_entry: Union[int, Entry, HeatCapacityModel] = 0,
                   fig_title: str = '',
                   T_min: Union[int, float] = 300,
                   T_max: Union[int, float] = 2000,
                   legends: Optional[list] = None,
                   size: Union[int, float] = 4.):
    """
    Plot the Gibbs free energy of a common species from two different library entries

    Args:
        entry_list (list): A list of RMG Thermo Entry or Entry.data.t
        thermo_property (str): A string indicating the thermo properties to be plotted.
        ref_index (int): The reference entry to generate the comparison.
        fig_title (str): The species label used for the figure title.
        T_min (num): The lower bound of temperature range being plotted.
        T_max (num): The upper bound of temperature range being plotted.
        legends (list): A list of legends used in the graph.
        size (num): The size of the graph being plotted.
    """
    if T_min >= T_max:
        raise ValueError(f'Invalid T_min({T_min}) and T_max({T_max}) arguments')
    T_list = np.arange(T_min, T_max + 1, min((T_max - T_min) / 100, 10.0))
    num_T = T_list.shape[0]

    thermo_property = thermo_property.lower()
    if thermo_property in ['free_energy', 'gibbs_free_energy', 'free energy',
                           'gibbs free energy', 'dg']:
        fun_name = 'get_free_energy'
    elif thermo_property in ['enthalpy', 'dh', 'h']:
        fun_name = 'get_enthalpy'
    elif thermo_property in ['entropy', 'ds', 's']:
        fun_name = 'get_entropy'
    elif thermo_property in ['heat capacity', 'heat_capacity', 'cp']:
        fun_name = 'get_heat_capacity'
    else:
        raise ValueError(f'Invalid thermo property ({thermo_property}).')

    if isinstance(reference_entry, (Entry, HeatCapacityModel)):
        entry_list = [reference_entry] + entry_list
    elif not isinstance(reference_entry, int):
        raise ValueError(
            f'The reference entry {reference_entry} is invalid. Neglecting the entry in plotting')

    value = []
    for entry in entry_list:
        value.append([])
        if isinstance(entry, Entry):
            try:
                fun = getattr(entry.data, fun_name)
            except AttributeError:
                raise ValueError(f'The entry {entry} is invalid. Neglecting the entry in plotting')
        elif isinstance(entry, HeatCapacityModel):
            try:
                fun = getattr(entry, fun_name)
            except AttributeError:
                raise ValueError(f'The entry {entry} is invalid. Neglecting the entry in plotting')
        else:
            raise ValueError(f'The entry {entry} is invalid. Neglecting the entry in plotting')

        for i in range(num_T):
            try:
                value[-1].append(fun(T_list[i]))
            except (ValueError, AttributeError):
                value[-1].append(np.nan)

    value = np.array(value) / 4.184
    if fun_name in ['get_free_energy', 'get_enthalpy']:
        value /= 1000
        unit = 'kcal/mol'
    else:
        unit = 'cal/mol/K'

    rel_err = np.zeros_like(value)
    err = np.zeros_like(value)
    reference_index = reference_entry if isinstance(reference_entry, int) else 0
    for i in range(value.shape[0]):
        err[i, :] = value[i, :] - value[reference_index, :]
        rel_err[i, :] = err[i, :] * 2 / abs(value[i, :] + value[reference_index, :]) * 100

    fig, axes = plt.subplots(1, 3, figsize=(3 * size + 1, size))
    fig.suptitle(fig_title)
    for i in range(value.shape[0]):
        axes[0].plot(T_list, value[i, :])
        axes[1].plot(T_list, err[i, :])
        axes[2].plot(T_list, rel_err[i, :])

    for ax in axes:
        ax.set_xlabel('Temperature [K]')
        ax.set_xlim(T_min, T_max)

    axes[0].set_ylabel(' '.join(fun_name[4:].split('_')) + f' [{unit}]')
    axes[1].set_ylabel(f'Error [{unit}]')
    axes[2].set_ylabel(f'Relative error [%]')

    if not legends:
        legends = [str(i) for i in range(value.shape[0])]
    legends[reference_entry] += ' (ref)'
    axes[0].legend(legends)
    plt.tight_layout()
    plt.show()
