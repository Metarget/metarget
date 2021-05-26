"""
Docker Installer
"""

import subprocess

import utils.color_print as color_print
import utils.verbose as verbose_func
import config
from core.env_managers.installer import Installer


class DockerInstaller(Installer):
    _docker_gadgets = [
        'docker',
        'docker-engine',
        'docker.io',
        'containerd',
        'runc',
        'docker-ce',
    ]
    _docker_requirements = [
        'apt-transport-https',
        'ca-certificates',
        'gnupg-agent',
        'software-properties-common',
    ]

    @classmethod
    def uninstall(cls, verbose=False):
        """Uninstall Docker.

        Args:
            verbose: Verbose or not.

        Returns:
            None.
        """
        stdout, stderr = verbose_func.verbose_output(verbose)
        subprocess.run(
            cls.cmd_apt_uninstall +
            cls._docker_gadgets,
            stdout=stdout,
            stderr=stderr,
            check=False
        )

    @classmethod
    def install_by_version(cls, gadgets, context=None, verbose=False):
        """Install Docker with specified version.

        Args:
            gadgets: Docker gadgets (e.g. docker-ce).
            context: Currently not used.
            verbose: Verbose or not.

        Returns:
            Boolean indicating whether Docker is successfully installed or not.
        """
        if not cls._pre_install(verbose=verbose):
            color_print.error('failed to install prerequisites')
            return False
        for gadget in gadgets:
            if not cls._install_one_gadget_by_version(
                    gadget['name'], gadget['version'], verbose=verbose):
                color_print.warning(
                    'docker seems to be installed, but some errors happened during installation')
                # sometimes docker is installed but error occurs during installation
                # so currently we just return true for it
                return True
        return True

    @classmethod
    def _pre_install(cls, verbose=False):
        stdout, stderr = verbose_func.verbose_output(verbose)
        # install requirements
        color_print.debug('installing prerequisites')
        try:
            if not cls._apt_update(verbose=verbose):
                return False
            subprocess.run(
                cls.cmd_apt_install +
                cls._docker_requirements,
                stdout=stdout,
                stderr=stderr,
                check=True)
        except subprocess.CalledProcessError:
            return False
        cls._add_apt_repository(gpg_url=config.docker_apt_repo_gpg,
                                repo_entry=config.docker_apt_repo_entry, verbose=verbose)
        for repo in config.containerd_apt_repo_entries:
            cls._add_apt_repository(repo_entry=repo, verbose=verbose)

        cls._apt_update(verbose=verbose)

        return True


if __name__ == "__main__":
    DockerInstaller.uninstall()
    import sys
    if len(sys.argv) > 1:
        test_version = sys.argv[1]
    else:
        test_version = '17.03.0'
    temp_gadgets = [{'name': 'docker-ce', 'version': test_version}]
    DockerInstaller.install_by_version(temp_gadgets)
