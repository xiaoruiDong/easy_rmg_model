#!/usr/bin/env python3
# encoding: utf-8

import os

from jinja2 import Environment, FileSystemLoader, Template
import pandas as pd


class SLURMSubmitScript(object):

    default_settings = {
        'partition': '',
        'job_name': 'test_job',
        'n_processor': 1,
        'mem_per_cpu': 1000,  # MB,
        'job_time': '5-00',
        'content': 'echo "Hello world!"',
        'save_path': './submit_script.sh',
        'template_file': None,
    }

    default_template = """#!/bin/bash -l
{%- if partition %}
#SBATCH -p {{ partition | safe }}
{%- endif %}
#SBATCH -J {{ job_name | safe}}
#SBATCH -N 1
#SBATCH -n {{ n_processor }}
#SBATCH --time={{ job_time }}
#SBATCH --mem-per-cpu={{ mem_per_cpu }}

echo "============================================================"
echo "Job ID : $SLURM_JOB_ID"
echo "Job Name : $SLURM_JOB_NAME"
echo "Starting on : $(date)"
echo "Running on node : $SLURMD_NODENAME"
echo "Current directory : $(pwd)"
echo "============================================================"

{{ content | safe }}
"""

    def __init__(self, spec={}):
        for key, value in spec.items():
            setattr(self, key, value)
        for key, value in self.default_settings.items():
            if not hasattr(self, key):
                setattr(self, key, value)

    @property
    def content(self):
        if not self._content:
            return None
        else:
            return self._content

    @content.setter
    def content(self, value):
        if not isinstance(value, str):
            raise ValueError(f'Invalid content ({value})')
        self._content = value

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
        return {'partition': self.partition,
                'job_name': self.job_name,
                'n_processor': self.n_processor,
                'mem_per_cpu': self.mem_per_cpu,
                'job_time': self.job_time,
                'content': self.content}

    @classmethod
    def from_dict(cls, spec_dict):
        return cls(spec_dict)
