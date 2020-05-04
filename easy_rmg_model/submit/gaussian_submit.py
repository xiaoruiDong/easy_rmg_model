#!/usr/bin/env python3
# encoding: utf-8

import os.path

from jinja2 import Environment, FileSystemLoader, Template


class GaussianSubmit(object):

    default_settings = {
        'package': 'g09',
        'modules': ['c3ddb/gaussian/09.d01', ],
        'scratch_dir': '/scratch/users/xiaorui',
        'queue': 'slurm',
        'package_root': '/opt',
        'input': 'input.gjf',
        'output': 'input.log',
        'checkfile': 'check.chk',
        'save_path': './gaussian_submit_script.sh',
        'template_file': None,
    }

    default_template = """{%- for module in modules %}
module add {{ module }}
{% endfor %}

WorkDir={{ work_dir }}
SubmitDir=`pwd`

GAUSS_SCRDIR={{ gauss_scrdir }}
export GAUSS_SCRDIR

mkdir -p $GAUSS_SCRDIR
mkdir -p $WorkDir

if [ -z ${ {{ package }}root+x } ]
then
  export {{ package }}root={{ package_root }}
fi

cd $WorkDir
. ${{ package }}root/{{ package }}/bsd/{{ package }}.profile

cp "$SubmitDir/input.gjf" .
cp "$SubmitDir/check.chk" .

{{ package }} < {{ input }} > {{ output }}
formchk {{ checkfile }} check.fchk
cp * "$SubmitDir/"

rm -rf $GAUSS_SCRDIR
rm -rf $WorkDir

"""

    def __init__(self, spec={}):
        for key, value in spec.items():
            setattr(self, key, value)
        for key, value in self.default_settings.items():
            if not hasattr(self, key):
                setattr(self, key, value)

    @property
    def package(self):
        return self._package

    @package.setter
    def package(self, value):
        if value not in ['g03', 'g09', 'g16']:
            raise ValueError(f'Invalid package, got {value}')
        else:
            self._package = value

    @property
    def work_dir(self):
        work_dir = f'{self.scratch_dir}/'
        if self.queue.lower() == 'slurm':
            return work_dir + '$SLURM_JOB_NAME-$SLURM_JOB_ID'
        elif self.queue.lower() in ['sge', 'oge', 'pbs']:
            return work_dir + '$JOB_NAME -$JOB_ID'

    @property
    def gauss_scrdir(self):
        gauss_scrdir = f'{self.scratch_dir}/{self.package}/'
        if self.queue.lower() == 'slurm':
            return gauss_scrdir + '$SLURM_JOB_NAME-$SLURM_JOB_ID'
        elif self.queue.lower() in ['sge', 'oge', 'pbs']:
            return gauss_scrdir + '$JOB_NAME -$JOB_ID'

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
        return {'modules': self.modules,
                'work_dir': self.work_dir,
                'gauss_scrdir': self.gauss_scrdir,
                'package': self.package,
                'package_root': self.package_root,
                'input': self.input,
                'output': self.output,
                'checkfile': self.checkfile, }

    @classmethod
    def from_dict(cls, spec_dict):
        return cls(spec_dict)
