"""
Docker Installer
"""

import subprocess

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
        'curl',
        'gnupg-agent',
        'software-properties-common',
    ]

    @classmethod
    def uninstall(cls):
        subprocess.run(
            cls.cmd_apt_uninstall +
            cls._docker_gadgets,
            check=False)

    @classmethod
    def install_by_version(cls, gadgets, context=None):
        cls._pre_install()
        for gadget in gadgets:
            if not cls._install_one_gadget_by_version(gadget['name'], gadget['version']):
                return False
        return True

    @classmethod
    def _pre_install(cls):
        # install requirements
        subprocess.run(cls.cmd_apt_update, check=True)
        subprocess.run(
            cls.cmd_apt_install +
            cls._docker_requirements,
            check=True)
        cls._add_apt_repository(gpg_url=config.docker_apt_repo_gpg,
                                repo_entry=config.docker_apt_repo_entry)


if __name__ == "__main__":
    DockerInstaller.uninstall()
    import sys
    if len(sys.argv) > 1:
        test_version = sys.argv[1]
    else:
        test_version = '17.03.0'
    temp_gadgets = [{'name': 'docker-ce', 'version': test_version}]
    DockerInstaller.install_by_version(temp_gadgets)
