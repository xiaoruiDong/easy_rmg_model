#!/usr/bin/env python3
# encoding: utf-8


from arkane.ess import ess_factory, GaussianLog, MolproLog, OrcaLog, QChemLog, TeraChemLog

from arc.job.trsh import determine_ess_status

from arc.parser import parse_frequencies


def determine_convergence(path, job_type, ts=False):
    try:
        log = ess_factory(path)
    except:
        return False
    else:
        for log_type in [GaussianLog, MolproLog, OrcaLog, QChemLog, TeraChemLog]:
            if isinstance(log, log_type):
                software = log_type.__name__.replace('Log', '').lower()
                break
    try:
        done = determine_ess_status(path,
                                    species_label='',
                                    job_type=job_type,
                                    software=software,
                                    )[0] == 'done'
    except:
        return False

    if done and job_type in ['optfreq', 'freq', 'composite']:
        freqs = parse_frequencies(path=path, software=software)
        if not len(freqs):
            # Single atom without freq
            return done
        neg_freqs = [freq for freq in freqs if freq < 0]
        if not ts:
            return done and not len(neg_freqs)
        return done and len(neg_freqs) == 1
