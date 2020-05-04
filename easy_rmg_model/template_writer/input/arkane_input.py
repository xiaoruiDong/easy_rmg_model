#!/usr/bin/env python3
# encoding: utf-8

import json

from arkane.encorr.corr import assign_frequency_scale_factor

from easy_rmg_model.template_writer import BaseTemplateWriter


class ArkaneInput(BaseTemplateWriter):

    default_settings = {
        'model_chemistry': 'cbs-qb3',
        'freq_scale_factor': None,
        'use_bond_corrections': True,
        'atom_dict': {},
        'bond_dict': {},
        'rotors_dict': {},
        'multiplicity': 1,
        'charge': 0,
        'linear': False,
        'external_symmetry': 1,
        'optical_isomers': 1,
        'freq': './freq/output.out',
        'composite': './composite/output.out',
        'sp': None,
        'template_file': None,
        'save_path': './input.py'
    }

    default_template = """#!/usr/bin/env python3
# encoding: utf-8

modelChemistry = "{{ model_chemistry }}"
frequencyScaleFactor = {{ freq_scale_factor }}
useHinderedRotors = {{ rotors_dict | length > 0 }}
useBondCorrections = {{ use_bond_corrections }}

atoms = {{ atom_dict | safe }}

bonds = {{ bond_dict | safe }}

spinMultiplicity = {{ multiplicity }}

linear = {{ linear }}

externalSymmetry = {{ external_symmetry }}

opticalIsomers = {{ optical_isomers }}

energy = {
    '{{ model_chemistry }}': Log('{{ energy }}'),
}

geometry = Log('{{ freq }}')

frequencies = Log('{{ freq }}')

{% if rotors_dict | length > 0 -%}
rotors = [
{%- for rotor in rotors_dict.values() %}
{%- if rotor['success'] %}
    HinderedRotor(scanLog=Log('{{ rotor['scan_path'] }}'),
                  pivots={{ rotor['pivots'] }},
                  top={{ rotor['top'] }},
                  symmetry={{ rotor['symmetry'] }},
                  fit='fourier'),
{%- endif %}
{%- endfor %}
]
{%- endif %}
"""

    @property
    def freq_scale_factor(self):
        if not self._freq_scale_factor:
            self._freq_scale_factor = assign_frequency_scale_factor(
                self.model_chemistry)
        return self._freq_scale_factor

    @freq_scale_factor.setter
    def freq_scale_factor(self, value):
        if value == None or \
           (isinstance(value, (int, float)) and
                value > 0 and value < 5):
            self._freq_scale_factor = value
        else:
            raise ValueError(f'Not valid frequency scale factor, got: {value}')

    @property
    def use_bond_corrections(self):
        if self.bond_dict == '{}':
            # Add a warning / or automatically generate one
            # False, otherwise will fail the job
            return False
        else:
            return self._use_bond_corrections

    @use_bond_corrections.setter
    def use_bond_corrections(self, value):
        if isinstance(value, bool):
            self._use_bond_corrections = value

    @property
    def atom_dict(self):
        return json.dumps(self._atom_dict, sort_keys=True,
                          indent=4, separators=(',', ': '))

    @atom_dict.setter
    def atom_dict(self, value):
        if isinstance(value, dict):
            self._atom_dict = value
        elif value == None:
            self._atom_dict = {}
        else:
            raise ValueError(f'Invalid atom dictionary, got {value}')

    @property
    def bond_dict(self):
        return json.dumps(self._bond_dict, sort_keys=True,
                          indent=4, separators=(',', ': '))

    @bond_dict.setter
    def bond_dict(self, value):
        if isinstance(value, dict):
            self._bond_dict = value
        elif value == None:
            self._bond_dict = {}
        else:
            raise ValueError(f'Invalid bond dictionary, got {value}')

    @property
    def energy(self):
        # TODO: a method check, check if model chemistry is the
        # same as indicated
        if hasattr(self, '_energy') and self._energy:
            return self._energy
        if hasattr(self, 'composite')\
           and self.composite:
            return self.composite
        elif hasattr(self, 'sp')\
                and self.sp:
            return self.sp
        elif hasattr(self, 'opt')\
                and self.opt:
            return self.opt
        elif hasattr(self, 'freq')\
                and self.freq:
            return self.freq

    @energy.setter
    def energy(self, value):
        if isinstance(value, str) or value == None:
            self._energy = value

    @property
    def freq(self):
        if self._freq:
            return self._freq
        elif hasattr(self, 'composite') and self.composite:
            return self.composite

    @freq.setter
    def freq(self, value):
        if isinstance(value, str) or value == None:
            self._freq = value
        else:
            raise ValueError(f'Not valid frequency, got {value}')

    def to_dict(self):
        return {'model_chemistry': self. model_chemistry,
                'freq_scale_factor': self.freq_scale_factor,
                'use_bond_corrections': self.use_bond_corrections,
                'atom_dict': self.atom_dict,
                'bond_dict': self.bond_dict,
                'rotors_dict': self.rotors_dict,
                'multiplicity': self.multiplicity,
                'charge': self.charge,
                'linear': self.linear,
                'external_symmetry': self.external_symmetry,
                'optical_isomers': self.optical_isomers,
                'energy': self.energy,
                'freq': self.freq,
                'save_path': self.save_path,
                }
