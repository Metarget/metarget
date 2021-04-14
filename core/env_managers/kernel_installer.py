"""
Linux Kernel Installer
"""

import copy
import subprocess
import yaml
import yaml.scanner
import re
import json

from core.env_managers.installer import Installer
import utils.color_print as color_print
import utils.verbose as verbose_func
import core.env_managers.package_list_downloader as package_list_downloader
import config


class KernelInstaller(Installer):
    cmd_update_grub = 'update-grub'.split()
    cmd_dpkg_install = 'dpkg -i'.split()

    @classmethod
    def install_by_version(cls, gadgets, context=None, verbose=False):
        """Install Linux kernel with specified version.

        Args:
            gadgets: Kernel gadgets (e.g. kernel).
            context: Currently not used.
            verbose: Verbose or not.

        Returns:
            Boolean indicating whether kernel is successfully installed or not.
        """
        # refer to
        # https://blog.csdn.net/u013431916/article/details/82530523
        # https://wiki.ubuntu.com/KernelTeam/KernelMaintenance
        # and
        # https://en.wikipedia.org/wiki/Linux_kernel#Version_numbering
        version = gadgets[0]['version']
        color_print.debug('switching kernel by version')
        for repo in config.kernel_apt_repo_entries:
            cls._add_apt_repository(repo_entry=repo, verbose=verbose)
        if cls._is_version_available_in_apt(version, verbose=verbose):
            return cls._install_by_version_with_apt(version, verbose=verbose)
        else:
            color_print.warning(
                'warning: no apt package for kernel %s' %
                version)
            if version.endswith('.0'):
                version = version.rstrip('.0') + '-'
            return cls._install_by_version_with_download(
                version, verbose=verbose)

    @classmethod
    def _install_by_version_with_apt(cls, version, verbose=False):
        color_print.debug('switching kernel version with apt')
        stdout, stderr = verbose_func.verbose_output(verbose)
        try:
            # install image package
            package_name = cls._get_apt_complete_package(
                'linux-image', ['linux-image-extra-{version}'.format(version=version), 'generic'], verbose=verbose)
            color_print.debug('installing kernel package %s' % package_name)
            version_suffix = package_name.lstrip('linux-image-extra-')
            temp_cmd = copy.copy(cls.cmd_apt_install)
            temp_cmd.append(package_name)
            subprocess.run(temp_cmd, stdout=stdout, stderr=stderr, check=True)
            cls._modify_grub(version=version_suffix, verbose=verbose)
            return True
        except subprocess.CalledProcessError:
            return False

    @classmethod
    def _install_by_version_with_download(cls, version, verbose=False):
        color_print.debug('switching kernel version with downloading packages')
        stdout, stderr = verbose_func.verbose_output(verbose)
        try:
            debs = cls._fetch_package_list_by_version(version, verbose=verbose)
            if not debs:
                return
            # download necessary *.deb and install
            temp_cmd = copy.copy(cls.cmd_dpkg_install)
            version_suffix = None
            for deb in debs:
                cls.download_file(deb, config.kernel_packages_dir)
                filename = deb.split('/')[-1]
                temp_cmd.append(
                    '{prefix}/{filename}'.format(prefix=config.kernel_packages_dir, filename=filename))
                if 'linux-image-' in filename:  # get full version for further modification in grub
                    try:
                        version_suffix = re.search(
                            r'linux-image-[a-z]*-?([\d].*?)_', filename).group(1)
                    except AttributeError:  # failed to derive complete kernel version
                        pass
            color_print.debug('installing kernel packages')
            # installation of kernel may return nonzero, currently ignore them
            subprocess.run(temp_cmd, stdout=stdout, stderr=stderr, check=False)
            if version_suffix:
                color_print.debug('kernel version: %s' % version_suffix)
                cls._modify_grub(version=version_suffix)
            else:
                color_print.warning('failed to derive complete kernel version')
                color_print.warning('please update grub manually')
            return True
        except subprocess.CalledProcessError:
            return False

    @classmethod
    def _modify_grub(cls, version=None, recover=False, verbose=False):
        stdout, stderr = verbose_func.verbose_output(verbose)
        # edit grub
        color_print.debug('modifying grub config file')
        if recover:  # recover grub
            grub_option = '0'
        else:
            grub_option = '\"Advanced options for Ubuntu>Ubuntu, with Linux {version}\"'.format(
                version=version)

        cmd_modify_grub = 'sed\n-i\ns/^GRUB_DEFAULT=.*$/' \
                          'GRUB_DEFAULT={grub_option}/\n/etc/default/grub'.format(
                              grub_option=grub_option).split('\n')
        subprocess.run(
            cmd_modify_grub,
            stdout=stdout,
            stderr=stderr,
            check=True)
        # update grub
        color_print.debug('updating grub')
        subprocess.run(
            cls.cmd_update_grub,
            stdout=stdout,
            stderr=stderr,
            check=True)

    @classmethod
    def _fetch_package_list_by_version(cls, version, verbose=False):
        color_print.debug('retrieving package list for kernel %s' % version)
        try:
            f = open(config.kernel_packages_list, 'r')
        except FileNotFoundError:
            color_print.warning(
                'warning: %s does not exist.' %
                config.kernel_packages_list)
            package_list_downloader.download_package_list()
            f = open(config.kernel_packages_list, 'r')
        try:
            packages = yaml.load(f, Loader=yaml.SafeLoader)
            for key in packages.keys():
                if version in key:
                    color_print.debug('kernel package list found:')
                    color_print.debug(json.dumps(packages[key]))
                    return packages[key]
        except yaml.scanner.ScannerError:
            return None
        color_print.error('kernel package list not found')
        return None

    @classmethod
    def _is_version_available_in_apt(cls, version, verbose=False):
        return cls._get_apt_complete_package(
            'linux-image', ['linux-image-extra-{version}'.format(version=version), 'generic'], verbose=verbose)


if __name__ == "__main__":
    temp_gadgets = [
        {'name': 'kernel', 'version': '4.2.0'},
    ]
    import sys
    if len(sys.argv) > 1:
        temp_gadgets[0]['version'] = sys.argv[1]
    else:
        temp_gadgets[0]['version'] = '4.2.0'

    KernelInstaller.install_by_version(temp_gadgets)
