"""
Kata-containers Installer
"""

from shutil import rmtree
from pathlib import Path
import subprocess

from core.env_managers.installer import Installer

import utils.color_print as color_print
import config
import utils.verbose as verbose_func


class KataContainersInstaller(Installer):
    @classmethod
    def uninstall(cls, verbose=False):
        """Uninstall Kata-containers.

        Args:
            verbose: Verbose or not.

        Returns:
            None.
        """
        pass

    @classmethod
    def install_by_version(cls, gadgets, kata_runtime_type,
                           http_proxy=None, https_proxy=None, no_proxy=None, verbose=False):
        """Install Kata-containers with specified version.

        Args:
            gadgets: Kata-containers gadgets (e.g. kata-containers).
            kata_runtime_type:
            http_proxy:
            https_proxy:
            no_proxy:
            verbose: Verbose or not.

        Returns:
            Boolean indicating whether Kata-containers is successfully installed or not.
        """
        stdout, stderr = verbose_func.verbose_output(verbose)

        kata_static_tar_file = config.kata_static_tar_file % gadgets[0]['version']
        kata_static_save_path = config.runtime_data_dir + kata_static_tar_file
        kata_static_tar = Path(kata_static_save_path)
        # 1. download kata tar if necessary
        if not kata_static_tar.exists():
            kata_static_url = (
                config.kata_static_url_prefix %
                gadgets[0]['version']) + kata_static_tar_file
            proxies = {
                'http': http_proxy,
                'https': https_proxy,
                'no_proxy': no_proxy,
            }
            cls.download_file(
                url=kata_static_url,
                save_dir=kata_static_save_path,
                proxies=proxies)
        # 2. decompress
        kata_decompress_dest = Path(config.kata_tar_decompress_dest)
        if kata_decompress_dest.exists():
            rmtree(kata_decompress_dest)
        kata_decompress_dest.mkdir()
        temp_cmd = 'tar xf {file} -C {dest}'.format(
            file=kata_static_save_path, dest=config.kata_tar_decompress_dest)
        try:
            subprocess.run(
                temp_cmd.split(),
                stdout=stdout,
                stderr=stderr,
                check=True)
        except subprocess.CalledProcessError:
            return False
        # 3. copy files
        etc_kata = Path('/etc/kata-containers')
        if etc_kata.exists():  # rm -rf /etc/kata-containers
            rmtree(etc_kata)
        temp_cmd = 'cp -r {src} {dst}'.format(
            src=config.kata_tar_decompress_dest +
            'opt/kata/share/defaults/kata-containers',
            dst='etc')
        try:
            subprocess.run(
                temp_cmd.split(),
                stdout=stdout,
                stderr=stderr,
                check=True)
        except subprocess.CalledProcessError:
            return False
        # 4. configure runtime type
        kata_configuration_file = Path(
            '/etc/kata-containers/configuration.toml')
        if kata_configuration_file.exists():
            kata_configuration_file.unlink()
        kata_configuration_file.symlink_to(
            '/etc/kata-containers/configuration-{runtime_type}.toml'.format(
                runtime_type=kata_runtime_type))
        # [5]. if docker is installed,
        # modify docker's configuration and restart docker
        # currently, metarget only supports docker
        # in the future more CRIs will be supported
        # see https://github.com/kata-containers/documentation/blob/master/how-to/run-kata-with-k8s.md
        # todo
        cls.restart_docker()


if __name__ == "__main__":
    KataContainersInstaller.uninstall()
    temp_gadgets = [
        {'name': 'kata-containers', 'version': '1.10.0'},
    ]
    KataContainersInstaller.install_by_version(
        temp_gadgets, 'clh', verbose=True)
