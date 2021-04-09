"""

"""

import subprocess

import utils.color_print as color_print


def reboot_system():
    cmd_reboot = 'init 6'.split()
    try:
        subprocess.run(cmd_reboot, check=True)
    except subprocess.CalledProcessError:
        color_print.error('failed to reboot system')
        return False
