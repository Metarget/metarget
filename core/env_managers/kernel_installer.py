"""
Linux Kernel Installer
"""

import copy
import subprocess
import os
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
    cmd_dpkg_uninstall = 'apt-get --purge remove'.split()

    @classmethod
    def uninstall(cls, gadgets, context=None, verbose=False):
        """Uninstall Linux kernel.

        Args:
            gadgets: Kernel gadgets (e.g. kernel).
            context: Currently not used.
            verbose: Verbose or not.

        Returns:
            None.
        """
        version = gadgets[0]['version']
        color_print.debug('uninstalling kernel')
        for repo in config.kernel_apt_repo_entries:
            cls._add_apt_repository(repo_entry=repo, verbose=verbose)
        apt_package = cls._is_version_available_in_apt(version, verbose=verbose)
        if apt_package:
            cls._uninstall_by_version_with_apt(version, apt_package, verbose=verbose)
        else:
            cls._uninstall_by_version_with_download(version, verbose=verbose)   
        return True         

    @classmethod
    def _uninstall_by_version_with_apt(cls, version, package_name, verbose=False):
        color_print.debug('uninstalling kernel version with apt')
        stdout, stderr = verbose_func.verbose_output(verbose)
        try:
            # uninstall image package
            color_print.debug('uninstalling kernel package %s' % package_name)
            if 'extra' in package_name:
                version_suffix = package_name.lstrip('linux-image-extra-')
            else:
                version_suffix = package_name.lstrip('linux-image-')
            temp_cmd = copy.copy(cls.cmd_dpkg_uninstall)
            temp_cmd.append(package_name)
            subprocess.run(temp_cmd, stdout=stdout, stderr=stderr, check=True)
            subprocess.run(
                cls.cmd_update_grub,
                stdout=stdout,
                stderr=stderr,
                check=True)
            return True
        except subprocess.CalledProcessError:
            return False

    @classmethod
    def _uninstall_by_version_with_download(cls, version, verbose=False):
        color_print.debug('uninstalling kernel version with downloading packages')
        stdout, stderr = verbose_func.verbose_output(verbose)
        try:
            debs = cls._fetch_package_list_by_version(version, verbose=verbose)
            if not debs:
                if version.endswith('.0'):
                    version = version.rstrip('.0') + '-'
                    debs = cls._fetch_package_list_by_version(
                        version, verbose=verbose)
                    color_print.debug('oh! kernel package list found by another way~')
                    if not debs:
                        return
                else:
                    return
            # uninstall necessary *.deb
            temp_cmd = copy.copy(cls.cmd_dpkg_uninstall)
            version_suffix = None
            for deb in debs:
                filename = deb.split('/')[-1]
                # cls.download_file(
                #     url=deb, save_path=os.path.join(
                #         config.kernel_packages_dir, filename))
                temp_list = [substr.start() for substr in re.finditer(version,filename)]
                temp_cmd.append(
                    '{filename}'.format(filename=filename[:temp_list[1]])+"*")
                if 'linux-image-' in filename:  # get full version for further modification in grub
                    try:
                        version_suffix = re.search(
                            r'linux-image-[a-z]*-?([\d].*?)_', filename).group(1)
                    except AttributeError:  # failed to derive complete kernel version
                        pass
            color_print.debug('uninstalling kernel packages')
            # installation of kernel may return nonzero, currently ignore them
            subprocess.run(temp_cmd, stdout=stdout, stderr=stderr, check=False)
            if version_suffix:
                subprocess.run(
                cls.cmd_update_grub,
                stdout=stdout,
                stderr=stderr,
                check=True)
            else:
                color_print.warning('failed to derive complete kernel version')
                color_print.warning('please update grub manually')
            return True
        except subprocess.CalledProcessError:
            return False

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

        apt_package = cls._is_version_available_in_apt(version, verbose=verbose)
        if apt_package:
            return cls._install_by_version_with_apt(version, apt_package, verbose=verbose)
        else:
            color_print.warning(
                'no apt package for kernel %s' %
                version)
            return cls._install_by_version_with_download(
                version, verbose=verbose)

    @classmethod
    def _install_by_version_with_apt(cls, version, package_name, verbose=False):
        color_print.debug('switching kernel version with apt')
        stdout, stderr = verbose_func.verbose_output(verbose)
        try:
            # install image package
            color_print.debug('installing kernel package %s' % package_name)
            if 'extra' in package_name:
                version_suffix = package_name.lstrip('linux-image-extra-')
            else:
                version_suffix = package_name.lstrip('linux-image-')
            temp_cmd = copy.copy(cls.cmd_apt_install)
            temp_cmd.append(package_name)
            subprocess.run(temp_cmd, stdout=stdout, stderr=stderr, check=True)
            cls._modify_grub(version=version_suffix, verbose=verbose)
            return True
        except subprocess.CalledProcessError:
            return False

    # @classmethod
    # def _install_by_version_with_build_sourcecode(cls, version, verbose=False):
    #     color_print.debug('switching kernel version with building from source code')
    #     stdout, stderr = verbose_func.verbose_output(verbose)
    #     kernel_source_dir = f"/usr/src/linux-{kernel_version}"
    #     try:
    #         # download source code
    #         color_print.debug('downloading kernel source code')
    #         download_command = f"wget http://mirrors.163.com/kernel/v{version.split('.')[0]}.x/linux-{version}.tar.xz -P /tmp"
    #         subprocess.run(download_command, shell=True)
    #         extract_command = f"tar -xvf /tmp/linux-{version}.tar.xz -C /usr/src"
    #         subprocess.run(extract_command, shell=True)
    #         os.chdir(kernel_source_dir)
    #         # build
    #         color_print.debug('building kernel')
    #         config_command = "make menuconfig"  # 使用 make menuconfig 来配置内核选项
    #         subprocess.run(config_command, shell=True)
    #         compile_command = "make"  # 使用 make 编译内核
    #         subprocess.run(compile_command, shell=True)
    #         # install
    #         color_print.debug('installing kernel')
    #         install_command = "make modules_install install"  # 安装内核和模块
    #         subprocess.run(install_command, shell=True)
    #         # update grub
    #         color_print.debug('updating grub')
    #         subprocess.run(
    #             cls.cmd_update_grub,
    #             stdout=stdout,
    #             stderr=stderr,
    #             check=True)
    #         return True
    #     except subprocess.CalledProcessError:
    #         return False

    @classmethod
    def _install_by_version_with_download(cls, version, verbose=False):
        color_print.debug('switching kernel version with downloading packages')
        stdout, stderr = verbose_func.verbose_output(verbose)
        try:
            debs = cls._fetch_package_list_by_version(version, verbose=verbose)
            if not debs:
                if version.endswith('.0'):
                    version = version.rstrip('.0') + '-'
                    debs = cls._fetch_package_list_by_version(
                        version, verbose=verbose)
                    if not debs:
                        return
                else:
                    return
            # download necessary *.deb and install
            temp_cmd = copy.copy(cls.cmd_dpkg_install)
            version_suffix = None
            for deb in debs:
                filename = deb.split('/')[-1]
                cls.download_file(
                    url=deb, save_path=os.path.join(
                        config.kernel_packages_dir, filename))
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
                '%s does not exist.' %
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
        signed_package = cls._get_apt_complete_package(
            'linux-image', ['linux-image-{version}'.format(version=version), 'generic'], verbose=verbose)
        return signed_package if signed_package else cls._get_apt_complete_package(
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
