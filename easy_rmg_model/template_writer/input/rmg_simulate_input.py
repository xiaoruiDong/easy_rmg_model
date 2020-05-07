#!/usr/bin/env python3
# encoding: utf-8

import os

from rmgpy.chemkin import load_species_dictionary
from rmgpy.molecule.molecule import Molecule

from easy_rmg_model.template_writer import BaseTemplateWriter

class RMGSimulateInput(BaseTemplateWriter):

    default_settings = {
        "species_dictionary": "./species_dictionary.txt",
        "fuel": '',
        "sens_spc": [],
        "temp": 1000,
        "pressure": 10,
        "phi": 1.0,
        "tf": 10.0,
        'template_file': None,
        'save_path': './input.py',
    }

    default_template = """database(
    thermoLibraries=['primaryThermoLibrary'],
    kineticsDepositories=['training'],
    reactionLibraries=['BurkeH2O2inN2'],
    seedMechanisms=['Klippenstein_Glarborg2016'],
    kineticsEstimator='rate rules',
)

species(
    label='{{ fuel['label'] }}',
    reactive=True,
    structure=SMILES("{{ fuel['smiles'] }}"),
)

species(
    label='N2',
    reactive=False,
    structure=SMILES("N#N"),
)

species(
    label='O2',
    reactive=True,
    structure=SMILES("[O][O]"),
)

{%- for spc in sens_spc %}
species(
    label="{{ spc['label'] }}",
    reactive=True,
    structure=SMILES("{{ spc['smiles'] }}"),
)
{%- endfor %}

simpleReactor(
    temperature=({{ temp }}, 'K'),
    pressure=({{ pressure }}, 'atm'),
    initialMoleFractions={
        "{{ fuel['label'] }}": {{ 1 * phi }},
        "O2": {{ oxygen_to_fuel }},
        "N2": {{ oxygen_to_fuel }} * 3.76,
    },
    terminationTime=({{ tf }}, 's'),
    {%- if sens_spc %}
    sensitivity = {{ sensitivity | safe }},
    sensitivityThreshold=0.01,
    {%- endif %}
)

simulator(
    atol=1e-16,
    rtol=1e-8,
    sens_atol=1e-6,
    sens_rtol=1e-4,
)
"""

    def __init__(self, spec):
        if 'species_dictionary' in spec:
            self.spc_dict = spec['species_dictionary']
        else:
            self.spc_dict = self.default_settings['species_dictionary']
        for key, value in spec.items():
            setattr(self, key, value)
        for key, value in self.default_settings.items():
            if not hasattr(self, key):
                setattr(self, key, value)

    @property
    def spc_dict(self):
        return self._spc_dict

    @spc_dict.setter
    def spc_dict(self, value):
        if not os.path.isfile(value):
            raise ValueError(f'Species dictionary ({value}) is invalid')
        else:
            self._spc_dict = load_species_dictionary(value)

    @property
    def fuel(self):
        return self._fuel

    @fuel.setter
    def fuel(self, value):
        self._fuel = self.update_spc_info(value)

    @property
    def sens_spc(self):
        return self._sens_spc

    @sens_spc.setter
    def sens_spc(self, value):
        self._sens_spc = []
        for spc_info in value:
            self._sens_spc.append(self.update_spc_info(spc_info))

    @property
    def oxygen_to_fuel(self):
        mol = Molecule().from_smiles(self.fuel['smiles'])
        atom_dict = mol.get_element_count()
        oxygen_to_fuel = 0
        for element, counts in atom_dict.items():
            if element == 'C':
                oxygen_to_fuel += counts
            elif element == 'H':
                oxygen_to_fuel += counts / 4
            elif element == 'O':
                oxygen_to_fuel -= counts / 2
        return oxygen_to_fuel

    @property
    def sensitivity(self):
        return [spc['label'] for spc in self.sens_spc]

    def update_spc_info(self, value):
        if 'smiles' in value and 'label' not in value:
            mol = Molecule().from_smiles(value['smiles'])
            for label, spc in self.spc_dict.items():
                if spc.is_isomorphic(mol):
                    value['label'] = label
                    break
            else:
                raise ValueError(f'Given SMILES ({value["smi"]}) invalid.')
        elif 'smiles' not in value and 'label' in value:
            for label, spc in self.spc_dict.items():
                if label == value['label']:
                    value['smiles'] = spc.molecules[0].to_smiles()
                    break
            else:
                raise ValueError(f'Given label ({value["label"]}) invalid.')
        elif 'smiles' in value and 'label' in value:
            mol = Molecule().from_smiles(value['smiles'])
            for label, spc in self.spc_dict.items():
                if label == value['label'] and spc.is_isomorphic(mol):
                    break
            else:
                raise ValueError(
                    f'Given label ({value["label"]}) and SMILES ({value["smi"]}) are invalid.')
        return value

    def to_dict(self):
        return {'fuel': self.fuel,
                'sens_spc': self.sens_spc,
                'oxygen_to_fuel': self.oxygen_to_fuel,
                'temp': self.temp,
                'phi': self.phi,
                'pressure': self.pressure,
                'sensitivity': self.sensitivity,
                'tf': self.tf,
                }
