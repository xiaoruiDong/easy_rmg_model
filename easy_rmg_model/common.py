#!/usr/bin/env python3
# encoding: utf-8

import os


def regularize_path(path: str):
    """
    Regularize the path.
    If the path has a initial component of ~ or ~user, it will be replaced by home directory
    If the path is not the absolutized path, absolute path will be returned.

    Args:
        path (str): Path to be regularized
    """
    if path.startswith('~'):
        return os.path.expandvars(os.path.expanduser(path))
    else:
        return os.path.abspath(os.path.expandvars(path))
