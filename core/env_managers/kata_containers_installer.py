"""
Kata-containers Installer
"""

from string import Template
import subprocess

from core.env_managers.installer import Installer
import config
import utils.verbose as verbose_func


class KataContainersInstaller(Installer):

    cmd_install_kata = 'bash {install_script}'.format(
        install_script=config.kata_install_script).split()

    @classmethod
    def uninstall(cls, verbose=False):
        pass

    @classmethod
    def install_by_version(cls, gadgets, context=None, verbose=False):
        """Install Kata-containers with specified version.

        Args:
            gadgets: Kata-containers gadgets (e.g. kata-containers).
            context: Context of installation process.
            verbose: Verbose or not.

        Returns:
            Boolean indicating whether Kata-containers is successfully installed or not.
        """
        stdout, stderr = verbose_func.verbose_output(verbose)
        mappings = {
            'kata_version': gadgets[0]['version'],
            'kata_runtime_type': context['annotations']['kata-runtime-type'],
        }
        with open(config.kata_install_template, 'r') as fr:
            with open(config.kata_install_script, 'w') as fw:
                worker_template = fr.read()
                data = Template(worker_template)
                res = data.safe_substitute(mappings)
                fw.write(res)
        try:
            subprocess.run(
                cls.cmd_install_kata,
                stdout=stdout,
                stderr=stderr,
                check=True)
            return True
        except subprocess.CalledProcessError:
            return False


if __name__ == "__main__":
    KataContainersInstaller.uninstall()
    temp_gadgets = [
        {'name': 'kata-containers', 'version': '1.10.0'},
    ]
    temp_context = {
        'annotations': {
            'kata-runtime-type': 'clh',
        }
    }
    KataContainersInstaller.install_by_version(temp_gadgets, temp_context)
