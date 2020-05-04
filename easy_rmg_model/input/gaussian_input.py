#!/usr/bin/env python3
# encoding: utf-8

import os.path

from jinja2 import Environment, FileSystemLoader, Template

from arc.species.converter import  (xyz_file_format_to_xyz,
                                    xyz_to_str)


class GaussianInput(object):
    """
    A Input class used to create input file for quantum calculation using Gaussian.

    Args:
        spec (dict): 
    """

    default_settings = {
        'fine': True,
        'ts': False,
        'job_type': 'scan',
        'level_of_theory': 'b3lyp/cbsb7',
        'trsh': {},
        'checkfile': '',
        'geom': '',
        'scan': [],
        'freeze': [],
        'scan_res': 8,
        'multiplicity': 1,
        'charge': 0,
        'memory': 14000,  # mb
        'n_processor': 8,
        'template_file': None,
        'save_path': './input.gjf'
    }

    default_template = """{{ checkfile_args }}
{{ memory_args }}
{{ processor_args }}

{{ calculation_args }}

name

{{ charge }} {{ multiplicity }}
{{ geometry_args }}

{{redundant_ic_args}}


"""

    def __init__(self, spec={}):
        for key, value in spec.items():
            setattr(self, key, value)
        for key, value in self.default_settings.items():
            if not hasattr(self, key):
                setattr(self, key, value)

    @property
    def opt_args(self):
        options = ['calcfc', 'noeigentest']
        if self.ts:
            options += ['ts', 'maxcycles=100']
        if self.fine and self.job_type != 'scan':
            options += ['tight', 'maxstep=5']
        if self.job_type == 'scan':
            options += ['modredundant', 'maxstep=5']
        options = list(set(options))
        if not options:
            return 'opt'
        else:
            return f'opt=({", ".join(options)})'

    @property
    def scf_args(self):
        options = []
        if self.fine:
            options += ['tight', 'direct']
        if 'ro' not in self.level_of_theory_args.lower():
            options.append('xqc')
        if 'scf' in self.trsh:
            for item in self.trsh['scf']:
                if item in ['nosymm', 'NDump=30', 'NoDIIS']:
                    # Current only support 3 types of trsh
                    options.append(item)
        options = list(set(options))
        if not options:
            return ''
        else:
            return f'scf=({", ".join(options)})'

    @property
    def integral_args(self):
        options = []
        if self.fine:
            options += ['grid=ultrafine', 'Acc2E=12']
        if 'integral' in self.trsh:
            for item in self.trsh['scf']:
                if 'Acc2E' in item:
                    for option in options:
                        option = option if 'Acc2E' not in option else item
                elif 'grid' in item:
                    for option in options:
                        option = option if 'grid' not in option else item

        options = list(set(options))
        if not options:
            return ''
        else:
            return f'integral=({", ".join(options)})'

    @property
    def guess_args(self):
        if self.checkfile:
            return 'guess=read'
        else:
            return 'guess=mix'

    @property
    def freq_args(self):
        return 'freq iop(7/33=1)'

    @property
    def level_of_theory_args(self):
        if isinstance(self.level_of_theory, str):
            return self.level_of_theory
        elif isinstance(self.level_of_theory, dict) \
                and 'method' in self.level_of_theory \
                and 'basis' in self.level_of_theory:
                return f'{self.level_of_theory["method"]}/' \
                       f'{self.level_of_theory["basis"]}'
        elif isinstance(self.level_of_theory, dict) \
                and 'method' in self.level_of_theory \
                and 'composite' in self.job_type:
                return f'{self.level_of_theory["method"]}'

    @property
    def other_args(self):
        return 'iop(2/9=2000)'

    @property
    def calculation_args(self):
        arg_list = ['opt', 'scf', 'integral', 'guess', 'freq', 'level_of_theory',
                    'other']
        if 'freq' not in self.job_type:
            arg_list.remove('freq')
        if 'sp' in self.job_type:
            arg_list.remove('opt')
        final_args = '#P'
        for arg_type in arg_list:
            args = getattr(self, arg_type + '_args')
            if args:
                final_args += ' ' + args
        return final_args

    @property
    def geometry_args(self):
        if isinstance(self.geom, str):
            # TODO: check the xyz is valid
            return self.geom
        elif isinstance(self.geom, dict):
            # Assume it is a ARC xyz
            return xyz_to_str(self.geom)
        elif os.path.isfile(self.geom):
            xyz = xyz_file_format_to_xyz(self.geom)
            return xyz_to_str(xyz)

    @property
    def redundant_ic_args(self):

        if self.job_type != 'scan':
            return ''
        if not hasattr(self, 'scan'):
            raise Exceptions('Invalid scan jobs as specification "scan" not provided')
        scan_args = ''
        default_res = 8
        scan = self.scan
        scan_res = self.scan_res or default_res
        if len(scan) == 4:
            scan_args += 'D ' + ' '.join([f'{num}' for num in scan]) + ' S '
            scan_args += f'{int(360 / scan_res)} {scan_res}'

        constraint_args = ''
        if hasattr(self, 'freeze') and self.freeze:
            for ic in self.freeze:
                if len(ic) == 2:
                    constraint_args += '\nB '
                elif len(ic) == 3:
                    constraint_args += '\nA '
                elif len(ic) == 4:
                    constraint_args += '\nD '
                constraint_args += ' '.join([f'{num}' for num in ic]) + ' F'

        return scan_args + constraint_args

    @property
    def memory_args(self):

        allowed_units = ['kb', 'mb', 'gb', 'tb',
                         'kw', 'mw', 'gw', 'tw']
        if isinstance(self.memory, (int, float)):
            return f'%mem={self.memory}mb'  # Assume the default unit is mb
        elif isinstance(self.memory, tuple) and len(self.memory) == 2:
            value, unit = self.memory
            if ((isinstance(value, str) and value.isdigit())
                    or (isinstance(value, (int, float)))) \
                    and (isinstance(unit, str) and unit.lower() in allowed_units):
                return f'%mem={value}{unit}'
        elif isinstance(self.memory, str):
            for index, char in enumerate(self.memory):
                if not char.isdigit():
                    break
            value, unit = self.memory[:index], self.memory[index:]
            if value and unit.lower() in allowed_units:
                return f'%mem={value}{unit}'
        return ''  # result in using default memory

    @property
    def processor_args(self):
        return f'%NProcShared={self.n_processor}'

    @property
    def checkfile_args(self):
        # if self.checkfile:
        #     return f'%chk={self.checkfile}'
        # else:
        return '%chk=check.chk'

    @property
    def jinja2_template(self):
        if self.template_file:
            template_dir, template_file = os.path.split(self.template_path)
            env = Environment(loader=FileSystemLoader(template_dir),
                              autoescape=True)
            template = env.get_template(template_file)
        else:
            template = Template(self.default_template, autoescape=True)
        return template

    @property
    def rendered_template(self):
        if not hasattr(self, '_rendered'):
            if self.jinja2_template:
                self._rendered = self.jinja2_template.render(self.to_dict())
        return self._rendered

    def save(self):
        with open(self.save_path, 'w') as f:
            f.write(self.rendered_template)
        return True

    def to_dict(self):
        return {'checkfile_args': self.checkfile_args,
                'memory_args': self.memory_args,
                'processor_args': self.processor_args,
                'calculation_args': self.calculation_args,
                'charge': self.charge,
                'multiplicity': self.multiplicity,
                'geometry_args': self.geometry_args,
                'redundant_ic_args': self.redundant_ic_args, }

    @classmethod
    def from_dict(cls, spec_dict):
        return cls(spec_dict)
