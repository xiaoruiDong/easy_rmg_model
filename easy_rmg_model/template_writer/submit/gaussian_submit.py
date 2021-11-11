#!/usr/bin/env python3
# encoding: utf-8


from easy_rmg_model.template_writer import BaseTemplateWriter

class GaussianSubmit(BaseTemplateWriter):

    default_settings = {
        'package': 'g09',
        'modules': ['c3ddb/gaussian/09.d01',],
        'scratch_dir': '/scratch/users/xiaorui',
        'queue': 'slurm',
        'package_root': '/opt',
        'input': 'input.gjf',
        'output': 'input.log',
        'checkfile': 'check.chk',
        'fchk_file': 'check.fchk',
        'generate_fchk': True,
        'save_path': './gaussian_submit_script.sh',
        'template_file': None,
    }

    default_template = """{%- for module in modules %}
module load {{ module }}
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

{{ package }} < {{ input | safe }} > {{ output | safe }}
{%- if generate_fchk %}
formchk {{ checkfile | safe }} {{ fchk_file | safe }}
{%- endif %}
cp * "$SubmitDir/"

rm -rf $GAUSS_SCRDIR
rm -rf $WorkDir

"""

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

    def to_dict(self):
        return {'modules': self.modules,
                'work_dir': self.work_dir,
                'gauss_scrdir': self.gauss_scrdir,
                'package': self.package,
                'package_root': self.package_root,
                'input': self.input,
                'output': self.output,
                'checkfile': self.checkfile,
                'fchk_file': self.fchk_file,
                'generate_fchk': self.generate_fchk,
                }
