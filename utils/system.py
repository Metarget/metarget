"""
System Functions
"""

import subprocess
import os
from pathlib import Path

import utils.color_print as color_print
import utils.verbose as verbose_func


def reload_daemon_config(verbose=False):
    color_print.debug('reloading daemon configurations')
    stdout, stderr = verbose_func.verbose_output(verbose)
    try:
        subprocess.run(
            'systemctl daemon-reload'.split(),
            stdout=stdout,
            stderr=stderr,
            check=True)
        return True
    except subprocess.CalledProcessError:
        color_print.error('failed to reload daemon configurations')
        return False


def reboot_system(verbose=False):
    stdout, stderr = verbose_func.verbose_output(verbose)
    cmd_reboot = 'init 6'.split()
    try:
        subprocess.run(cmd_reboot, stdout=stdout, stderr=stderr, check=True)
    except subprocess.CalledProcessError:
        color_print.error('failed to reboot system')
        return False


def mkdir_if_not_exist(dir_path):
    try:
        p = Path(dir_path)
        p.mkdir(parents=True)
    except FileExistsError:
        pass


def create_file_if_not_exist(file_path):
    try:
        f = open(file_path, 'r')
        f.close()
    except FileNotFoundError:
        dir_path = Path(os.path.split(file_path)[0])
        if not dir_path.exists():
            dir_path.mkdir(parents=True)
        p = Path(file_path)
        p.touch()
