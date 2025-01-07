"""
Checkers
"""
import os
import subprocess
import re

import utils.color_print as color_print
import utils.verbose as verbose_func
import config
from packaging import version

def docker_kubernetes_installed(verbose=False):
    """Check whether Docker AND Kubernetes have been installed.

    Args:
        verbose: Verbose or not.

    Returns:
        If Docker and Kubernetes have been both installed, return True, else False.
    """
    if not docker_installed(verbose=verbose):
        color_print.error(
            'it seems docker is not installed or correctly configured')
        color_print.error(
            'you can run `metarget gadget install docker --version 18.03.1` to install one')
        return False
    if not kubernetes_installed(verbose=verbose):
        color_print.error(
            'it seems kubernetes is not installed or correctly configured')
        color_print.error(
            'you can run `metarget gadget install k8s --version 1.16.5` to install one')
        return False
    return True


def kubernetes_installed(verbose=False):
    """Check whether Kubernetes has been installed.

    Args:
        verbose: Verbose or not.

    Returns:
        If Kubernetes has been installed, return True, else False.
    """
    _, stderr = verbose_func.verbose_output(verbose)
    try:
        temp_cmd = 'kubectl version'.split()
        subprocess.run(
            temp_cmd,
            stdout=subprocess.PIPE,
            stderr=stderr,
            check=True)
        color_print.debug('kubernetes already installed')
        return True
    except (FileNotFoundError, AttributeError, IndexError, subprocess.CalledProcessError):
        return False


def docker_installed(verbose=False):
    """Check whether Docker has been installed.

    Args:
        verbose: Verbose or not.

    Returns:
        If Docker has been installed, return True, else False.
    """
    _, stderr = verbose_func.verbose_output(verbose)
    try:
        temp_cmd = 'docker version'.split()
        subprocess.run(
            temp_cmd,
            stdout=subprocess.PIPE,
            stderr=stderr,
            check=True)
        color_print.debug('docker already installed')
        return True
    except (FileNotFoundError, AttributeError, IndexError, subprocess.CalledProcessError):
        return False


def kubernetes_specified_installed(temp_gadget, verbose=False):
    """Check whether Kubernetes with specified version has been installed.

    Args:
        temp_gadget: Kubernetes gadgets (e.g. kubelet, kubeadm).
        verbose: Verbose or not.

    Returns:
        If Kubernetes with specified version has been installed, return True,
        else False.
    """
    _, stderr = verbose_func.verbose_output(verbose)
    try:
        temp_cmd = 'kubectl version'.split()
        res = subprocess.run(
            temp_cmd,
            stdout=subprocess.PIPE,
            stderr=stderr,
            check=True)
        server_string = res.stdout.decode('utf-8').split('\n')[1]
        server_version = re.search(
            r'GitVersion:".?([\d]+\.[\d]+\.[\d]+)"',
            server_string).group(1)
        if server_version == temp_gadget[0]['version']:
            return True
        return False
    except (FileNotFoundError, AttributeError, IndexError, subprocess.CalledProcessError):
        return False


def docker_specified_installed(temp_gadgets, verbose=False):
    """Check whether Docker with specified version has been installed.

    Args:
        temp_gadgets: Docker gadgets (e.g. docker-ce).
        verbose: Verbose or not.

    Returns:
        If Docker with specified version has been installed, return True,
        else False.
    """
    _, stderr = verbose_func.verbose_output(verbose)
    try:
        temp_cmd = 'docker version'.split()
        res = subprocess.run(
            temp_cmd,
            stdout=subprocess.PIPE,
            stderr=stderr,
            check=True)
        server_string = res.stdout.decode('utf-8').split('Server')[1]
        server_version = re.search(
            r'Version: *([\d]+\.[\d]+\.[\d]+)',
            server_string).group(1)
        temp_version = _get_gadget_version_from_gadgets(
            gadgets=temp_gadgets, name='docker-ce')
        if temp_version and server_version == temp_version:
            return True
        return False
    except (FileNotFoundError, AttributeError, IndexError, subprocess.CalledProcessError):
        return False

def whether_docker_newer_than_18_09(verbose=False):
    """Check whether Docker is newer than 18.09.

    Args:
        verbose: Verbose or not.

    Returns:
        If Docker >=18.09, return True, else False.
    """
    _, stderr = verbose_func.verbose_output(verbose)
    try:
        temp_cmd = 'docker version'.split()
        res = subprocess.run(
            temp_cmd,
            stdout=subprocess.PIPE,
            stderr=stderr,
            check=True)
        server_string = res.stdout.decode('utf-8').split('Server')[1]
        server_version = re.search(
            r'Version: *([\d]+\.[\d]+\.[\d]+)',
            server_string).group(1)
        if version.parse(server_version) >= version.parse('18.09'):
            return True
        return False
    except (FileNotFoundError, AttributeError, IndexError, subprocess.CalledProcessError):
        return False



def containerd_specified_installed(temp_gadgets, verbose=False):
    """Check whether Containerd with specified version has been installed.

    Args:
        temp_gadgets: Docker gadgets (e.g. containerd).
        verbose: Verbose or not.

    Returns:
        If Containerd with specified version has been installed, return True,
        else False.
    """
    _, stderr = verbose_func.verbose_output(verbose)
    try:
        temp_cmd = 'ctr version'.split()
        res = subprocess.run(
            temp_cmd,
            stdout=subprocess.PIPE,
            stderr=stderr,
            check=True)
        server_string = res.stdout.decode('utf-8').split('Server')[1]
        server_version = re.search(
            r'Version:\s*(.*)\s+',
            server_string).group(1)
        temp_version = _get_gadget_version_from_gadgets(
            gadgets=temp_gadgets, name='containerd')
        if temp_version and server_version.startswith(temp_version):
            return True
        return False
    except (FileNotFoundError, AttributeError, IndexError, subprocess.CalledProcessError):
        return False


def _get_gadget_version_from_gadgets(gadgets, name, verbose=False):
    for gadget in gadgets:
        if gadget['name'] == name:
            return gadget['version']
    return None


def gadget_in_gadgets(gadgets, name, verbose=False):
    for gadgets in gadgets:
        if gadgets['name'] == name:
            return True
    return False


def kernel_specified_installed(temp_gadget, verbose=False):
    """Check whether Linux kernel with specified version has been installed.

    Args:
        temp_gadget: Kernel gadgets (e.g. kernel).
        verbose: Verbose or not.

    Returns:
        If kernel with specified version has been installed, return True,
        else False.
    """
    try:
        _, stderr = verbose_func.verbose_output(verbose)
        temp_cmd = 'uname -r'.split()
        res = subprocess.run(
            temp_cmd,
            stdout=subprocess.PIPE,
            stderr=stderr,
            check=True)
        version_string = res.stdout.decode('utf-8')
        if version_string.startswith(temp_gadget[0]['version']):
            return True
        return False
    except (FileNotFoundError, AttributeError, IndexError, subprocess.CalledProcessError):
        return False


def kata_specified_installed(temp_gadget, kata_runtime_type, verbose=False):
    """Check whether kata-containers with specified version has been installed.

    Args:
        temp_gadget: Kata-containers gadgets (e.g. kata-containers).
        kata_runtime_type: Runtime of Kata (e.g. qemu/clh/...).
        verbose:

    Returns:
        If kata-containers with specified version has been installed, return True,
        else False.
    """
    try:
        _, stderr = verbose_func.verbose_output(verbose)
        temp_cmd = '{base_dir}/bin/kata-runtime --version'.format(
            base_dir=config.kata_tar_decompress_dest).split()
        res = subprocess.run(
            temp_cmd,
            stdout=subprocess.PIPE,
            stderr=stderr,
            check=True)
        version_string = res.stdout.decode('utf-8').split('\n')[0]
        server_version = re.search(
            r'.*([\d]+\.[\d]+\.[\d]+)',
            version_string).group(1)
        if server_version == temp_gadget[0]['version']:
            # check whether kata runtime type is also correct
            try:
                link_target = os.readlink(
                    '{kata_config_dir}/configuration.toml'.format(kata_config_dir=config.kata_config_dir))
                actual_runtime_type = link_target.split('.')[0].split('-')[-1]
                if actual_runtime_type != kata_runtime_type:
                    color_print.warning(
                        'your expected kata runtime type is {expected}, while current type is {actual}'.format(
                            expected=kata_runtime_type, actual=actual_runtime_type))
                    color_print.warning(
                        'you can configure runtime type manually')
            except (FileNotFoundError, OSError):
                color_print.warning(
                    'configuration.toml does not exist or is not an effective symbol link to real configurations')
                color_print.warning(
                    'please check configurations in {kata_config_dir} manually'.format(
                        kata_config_dir=config.kata_config_dir))
            return True
        return False
    except (IndexError, AttributeError, FileNotFoundError, subprocess.CalledProcessError):
        return False
