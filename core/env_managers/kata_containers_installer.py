"""
Kata-containers Installer
- see
- https://github.com/kata-containers/documentation/blob/master/design/VSocks.md#system-requirements
- for system requirements
- (maybe we should make it clear in README.md in the future)
"""

from shutil import rmtree
import json
from pathlib import Path
import subprocess

import utils.system as system_func
import utils.verbose as verbose_func
import utils.color_print as color_print
from core.env_managers.installer import Installer
import config


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
            kata_runtime_type: Runtime of Kata (e.g. qemu/clh/...)
            http_proxy: HTTP proxy.
            https_proxy: HTTPS proxy.
            no_proxy: Domains which should be visited without proxy.
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
            color_print.debug(
                '{kata_tar} is going to be downloaded'.format(
                    kata_tar=kata_static_tar_file))
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
                save_path=kata_static_save_path,
                proxies=proxies)
        else:
            color_print.debug(
                '{kata_tar} has been downloaded'.format(
                    kata_tar=kata_static_tar_file))

        # 2. decompress
        color_print.debug(
            'decompressing files into {dest}'.format(
                dest=config.kata_tar_decompress_dest))
        kata_decompress_dest = Path(config.kata_tar_decompress_dest)
        if kata_decompress_dest.exists():
            rmtree(config.kata_tar_decompress_dest)
        kata_decompress_dest.mkdir()
        # use --strip-components=2 because `opt/kata/` path from tar are not needed
        # also, we should not just decompress files into `/` root path
        # which might cause risks
        temp_cmd = 'tar xf {file} -C {dest} --strip-components=3'.format(
            file=kata_static_save_path, dest=config.kata_tar_decompress_dest)
        try:
            subprocess.run(
                temp_cmd.split(),
                stdout=stdout,
                stderr=stderr,
                check=True)
        except subprocess.CalledProcessError:
            color_print.error(
                'failed to decompress {kata_tar}'.format(
                    kata_tar=kata_static_tar_file))
            return False

        # 3. copy files
        color_print.debug('copying files to /etc/kata-containers')
        etc_kata = Path('/etc/kata-containers')
        if etc_kata.exists():  # rm -rf /etc/kata-containers
            rmtree('/etc/kata-containers')
        temp_cmd = 'cp -r {src} {dst}'.format(
            src=config.kata_tar_decompress_dest +
            'share/defaults/kata-containers',
            dst='/etc')
        try:
            subprocess.run(
                temp_cmd.split(),
                stdout=stdout,
                stderr=stderr,
                check=True)
        except subprocess.CalledProcessError:
            color_print.error('failed to copy files to /etc/kata-containers')
            return False

        # 4. configure runtime type
        color_print.debug('configuring kata runtime (type: {runtime_type})'.format(runtime_type=kata_runtime_type))
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
        # see
        # https://github.com/kata-containers/documentation/blob/master/how-to/run-kata-with-k8s.md
        color_print.debug('configuring docker with kata-containers')
        if not cls._configure_docker_with_kata(
                base_dir=config.kata_tar_decompress_dest):
            color_print.error('failed to configure docker with kata-containers')
            return False
        return cls.reload_and_restart_docker(verbose=verbose)

    @classmethod
    def _configure_docker_with_kata(cls, base_dir):
        # configure /etc/docker/daemon.json
        color_print.debug('writing /etc/docker/daemon.json')
        runtimes = {
            "kata-runtime": {
                "path": "{base_dir}/bin/kata-runtime".format(base_dir=base_dir)
            },
            "kata-clh": {
                "path": "{base_dir}/bin/kata-clh".format(base_dir=base_dir)
            },
            "kata-qemu": {
                "path": "{base_dir}/bin/kata-qemu".format(base_dir=base_dir)
            },
            "kata-fc": {
                "path": "{base_dir}/bin/kata-fc".format(base_dir=base_dir)
            },
        }
        system_func.create_file_if_not_exist('/etc/docker/daemon.json')
        try:
            with open('/etc/docker/daemon.json', 'r') as f:
                content = json.loads(f.read())
        except json.decoder.JSONDecodeError:
            content = dict()
        content['runtimes'] = runtimes
        with open('/etc/docker/daemon.json', 'w') as f:
            f.write(json.dumps(content))

        return True


if __name__ == "__main__":
    KataContainersInstaller.uninstall()
    temp_gadgets = [
        {'name': 'kata-containers', 'version': '1.10.0'},
    ]
    KataContainersInstaller.install_by_version(
        temp_gadgets, 'clh', verbose=True)
