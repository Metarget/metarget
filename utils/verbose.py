"""
deal with verbose information
"""

import sys
import subprocess


def verbose_output(verbose=False):
    if verbose:
        return sys.stdout, sys.stderr
    else:
        return subprocess.DEVNULL, subprocess.DEVNULL
