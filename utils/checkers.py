"""
Checkers
"""

import subprocess
import re

import utils.color_print as color_print
import utils.verbose as verbose_func


def docker_kubernetes_installed(verbose=False):
    if not docker_installed(verbose=verbose):
        color_print.error(
            'error: it seems docker is not installed or correctly configured')
        color_print.error(
            'you can run `metarget gadget install docker --version 18.03.1` to install one')
        return False
    if not kubernetes_installed(verbose=verbose):
        color_print.error(
            'error: it seems kubernetes is not installed or correctly configured')
        color_print.error(
            'you can run `metarget gadget install k8s --version 1.16.5` to install one')
        return False
    return True


def kubernetes_installed(verbose=False):
    _, stderr = verbose_func.verbose_output(verbose)
    try:
        temp_cmd = 'kubectl version'.split()
        subprocess.run(temp_cmd, stdout=subprocess.PIPE, stderr=stderr, check=True)
        color_print.debug('kubernetes already installed')
        return True
    except (FileNotFoundError, AttributeError, IndexError, subprocess.CalledProcessError):
        return False


def docker_installed(verbose=False):
    _, stderr = verbose_func.verbose_output(verbose)
    try:
        temp_cmd = 'docker version'.split()
        subprocess.run(temp_cmd, stdout=subprocess.PIPE, stderr=stderr, check=True)
        color_print.debug('docker already installed')
        return True
    except (FileNotFoundError, AttributeError, IndexError, subprocess.CalledProcessError):
        return False


def kubernetes_specified_installed(temp_gadget, verbose=False):
    _, stderr = verbose_func.verbose_output(verbose)
    try:
        temp_cmd = 'kubectl version'.split()
        res = subprocess.run(temp_cmd, stdout=subprocess.PIPE, stderr=stderr, check=True)
        server_string = res.stdout.decode('utf-8').split('\n')[1]
        server_version = re.search(r'GitVersion:".?([\d]+\.[\d]+\.[\d]+)"', server_string).group(1)
        if server_version == temp_gadget[0]['version']:
            return True
        return False
    except (FileNotFoundError, AttributeError, IndexError, subprocess.CalledProcessError):
        return False


def docker_specified_installed(temp_gadget, verbose=False):
    _, stderr = verbose_func.verbose_output(verbose)
    try:
        temp_cmd = 'docker version'.split()
        res = subprocess.run(temp_cmd, stdout=subprocess.PIPE, stderr=stderr, check=True)
        server_string = res.stdout.decode('utf-8').split('Server')[1]
        server_version = re.search(r'Version: *([\d]+\.[\d]+\.[\d]+)', server_string).group(1)
        if server_version == temp_gadget[0]['version']:
            return True
        return False
    except (FileNotFoundError, AttributeError, IndexError, subprocess.CalledProcessError):
        return False


def kernel_specified_installed(temp_gadget, verbose=False):
    try:
        _, stderr = verbose_func.verbose_output(verbose)
        temp_cmd = 'uname -r'.split()
        res = subprocess.run(temp_cmd, stdout=subprocess.PIPE, stderr=stderr, check=True)
        version_string = res.stdout.decode('utf-8')
        if version_string.startswith(temp_gadget[0]['version']):
            return True
        return False
    except (FileNotFoundError, AttributeError, IndexError, subprocess.CalledProcessError):
        return False
