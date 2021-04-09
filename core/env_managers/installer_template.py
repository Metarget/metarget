"""
Installer Template
"""

from core.env_managers.installer import Installer


class XXXInstaller(Installer):

    @classmethod
    def uninstall(cls):
        pass

    @classmethod
    def install_by_version(cls, gadgets, context=None):
        pass


if __name__ == "__main__":
    XXXInstaller.uninstall()
    temp_gadgets = [
        {},
    ]
    temp_context = {

    }
    XXXInstaller.install_by_version(temp_gadgets, temp_context)
