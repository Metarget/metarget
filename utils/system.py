"""
System Functions
"""

import subprocess

import utils.color_print as color_print
import utils.verbose as verbose_func


def reboot_system(verbose=False):
    stdout, stderr = verbose_func.verbose_output(verbose)
    cmd_reboot = 'init 6'.split()
    try:
        subprocess.run(cmd_reboot, stdout=stdout, stderr=stderr, check=True)
    except subprocess.CalledProcessError:
        color_print.error('failed to reboot system')
        return False
