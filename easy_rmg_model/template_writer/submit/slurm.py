#!/usr/bin/env python3
# encoding: utf-8

import os

from easy_rmg_model.template_writer import BaseTemplateWriter


class SLURMSubmitScript(BaseTemplateWriter):

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

    def to_dict(self):
        return {'partition': self.partition,
                'job_name': self.job_name,
                'n_processor': self.n_processor,
                'mem_per_cpu': self.mem_per_cpu,
                'job_time': self.job_time,
                'content': self.content}
