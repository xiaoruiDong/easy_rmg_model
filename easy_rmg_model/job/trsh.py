#!/usr/bin/env python3
# encoding: utf-8


from arkane.ess import ess_factory, GaussianLog, MolproLog, OrcaLog, QChemLog, TeraChemLog
from rdmc.external.gaussian import GaussianLog

LOG_PARSER = {'GaussianLog': GaussianLog}

def determine_convergence(path, job_type, ts=False):
    try:
        log = ess_factory(path)
    except:
        return False
    else:
        try:
            log = LOG_PARSER[log.__class__.__name__](path)
        except KeyError:
            raise NotImplementedError

    if not log.success:
        return False

    if job_type in ['optfreq', 'freq', 'composite']:
        if not len(log.freqs): # Single atom without freq
            return True
        if not ts:
            return len(log.neg_freqs) == 0
        else:
            return len(log.neg_freqs) == 1
    else:
        return True
