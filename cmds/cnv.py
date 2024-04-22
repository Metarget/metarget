"""
Cloud Native Vulnerabilities Commands
"""

import operator
import collections

import config
import utils.table as table
import utils.color_print as color_print
import utils.checkers as checkers
import utils.filters as filters
import utils.system as system_func
import cmds.internal as internal_cmds
from core.vuln_cn_manager import vuln_loader
from core.env_managers.docker_installer import DockerInstaller
from core.env_managers.kubernetes_installer import KubernetesInstaller
from core.env_managers.kernel_installer import KernelInstaller
from core.env_managers.kata_containers_installer import KataContainersInstaller


def install(args):
    """Install a cloud native vulnerability.

    Install a vulnerable cloud native gadget with one vulnerability
    specified by args.cnv.

    Args:
        args.cnv: Name of the specified cloud native vulnerability.
        args.verbose: Verbose or not.
        args.http_proxy: HTTP proxy.
        args.https_proxy: HTTPS proxy.
        args.no_proxy: Domains which should be visited without proxy.
      Args below only used when installing vulnerability related to Kubernetes:
        args.cni_plugin: Name of CNI plugin.
        args.pod_network_cidr: CIDR of pod network.
        args.domestic: Pull Kubernetes images from domestic source or not.
        args.taint_master: Taint the master node or not.

    Returns:
        None.
    """
    vulns = vuln_loader.load_vulns_by_dir(config.vuln_cn_dir_wildcard)
    vuln = filters.filter_vuln_by_name(vulns=vulns, name=args.cnv)
    if not vuln:
        color_print.error_and_exit(
            'no cloud native vulnerability named {cnv}'.format(
                cnv=args.cnv))

    # deploy vulnerability
    if vuln['class'] == 'config' or vuln['class'] == 'mount' or vuln['class'] == 'no-vuln':
        if not checkers.docker_kubernetes_installed(
                verbose=args.verbose):  # should install docker or k8s firstly
            return
        internal_cmds.deploy_vuln_resources_in_k8s(vuln, verbose=args.verbose)

    if vuln['class'].startswith('docker'):
        installed_flag = True  # add a flag because more than one gadgets may be checked
        if checkers.docker_specified_installed(
                vuln['dependencies'], verbose=args.verbose):
            if checkers.gadget_in_gadgets(
                    vuln['dependencies'], name='containerd', verbose=args.verbose):
                if not checkers.containerd_specified_installed(
                        vuln['dependencies'], verbose=args.verbose):
                    installed_flag = False
            if installed_flag:
                color_print.debug(
                    '{vuln} already installed'.format(
                        vuln=vuln['name']), 3)
                return
        color_print.debug(
            '{vuln} is going to be installed'.format(
                vuln=vuln['name']))
        color_print.debug('uninstalling current docker gadgets if applicable')
        DockerInstaller.uninstall(verbose=args.verbose)
        if not DockerInstaller.install_by_version(
                vuln['dependencies'], verbose=args.verbose):
            color_print.error(
                'failed to install {v}'.format(
                    v=vuln['name']))
        else:
            color_print.debug(
                '{v} successfully installed'.format(
                    v=vuln['name']), 1)

    if vuln['class'] == 'kubernetes':
        if checkers.kubernetes_specified_installed(
                vuln['dependencies'], verbose=args.verbose):
            color_print.debug(
                '{vuln} already installed'.format(
                    vuln=vuln['name']), 3)
            return
        if not checkers.docker_installed(verbose=args.verbose):
            color_print.error(
                'it seems docker is not installed or correctly configured')
            color_print.error_and_exit(
                'you can run `metarget gadget install docker --version 18.03.1` to install one')
        color_print.debug(
            '{vuln} is going to be installed'.format(
                vuln=vuln['name']))
        color_print.debug('uninstalling current kubernetes if applicable')
        KubernetesInstaller.uninstall(verbose=args.verbose)
        temp_pod_network_cidr = args.pod_network_cidr if args.pod_network_cidr else config.cni_plugin_cidrs[
            args.cni_plugin]

        if not KubernetesInstaller.install_by_version(
                vuln['dependencies'],
                cni_plugin=args.cni_plugin,
                pod_network_cidr=temp_pod_network_cidr,
                domestic=args.domestic,
                taint_master=args.taint_master,
                http_proxy=args.http_proxy,
                https_proxy=args.https_proxy,
                no_proxy=args.no_proxy,
                verbose=args.verbose):
            color_print.error(
                'failed to install {v}'.format(
                    v=vuln['name']))
        else:
            color_print.debug(
                '{v} successfully installed'.format(
                    v=vuln['name']), 1)

    if vuln['class'] == 'kernel':
        if checkers.kernel_specified_installed(
                vuln['dependencies'], verbose=args.verbose):
            color_print.debug(
                '{vuln} already installed'.format(
                    vuln=vuln['name']), 3)
            return
        color_print.debug(
            '{vuln} is going to be installed'.format(
                vuln=vuln['name']))

        if not KernelInstaller.install_by_version(
                gadgets=vuln['dependencies'], verbose=args.verbose):
            color_print.error(
                'failed to install {v}'.format(
                    v=vuln['name']))
        else:
            color_print.debug(
                '{v} successfully installed'.format(
                    v=vuln['name']), 1)
            # reboot
            reboot = color_print.debug_input('reboot system now? (y/n) ')
            if reboot == 'y' or reboot == 'Y':
                system_func.reboot_system(verbose=args.verbose)

    if vuln['class'] == 'kata-containers':
        if checkers.kata_specified_installed(
                temp_gadget=vuln['dependencies'],
                kata_runtime_type=vuln['annotations']['kata-runtime-type'],
                verbose=args.verbose):
            color_print.debug(
                '{vuln} already installed'.format(
                    vuln=vuln['name']), 3)
            return
        if not checkers.docker_installed(verbose=args.verbose):
            color_print.error(
                'it seems docker is not installed or correctly configured')
            color_print.error_and_exit(
                'you can run `metarget gadget install docker --version 18.03.1` to install one')

        color_print.debug(
            '{vuln} is going to be installed'.format(
                vuln=vuln['name']))

        color_print.debug('uninstalling current kata-containers if applicable')
        KataContainersInstaller.uninstall(verbose=args.verbose)

        if not KataContainersInstaller.install_by_version(
                gadgets=vuln['dependencies'],
                kata_runtime_type=vuln['annotations']['kata-runtime-type'],
                http_proxy=args.http_proxy,
                https_proxy=args.https_proxy,
                no_proxy=args.no_proxy,
                verbose=args.verbose):
            color_print.error(
                'failed to install {v}'.format(
                    v=vuln['name']))
        else:
            color_print.debug(
                '{v} successfully installed'.format(
                    v=vuln['name']), 1)


def remove(args):
    """Remove an installed cloud native vulnerability.

    Remove the vulnerable cloud native gadget with the cloud native vulnerability
    specified by args.cnv.

    Args:
        args.cnv: Name of the specified cloud native vulnerability.
        args.verbose: Verbose or not.

    Returns:
        None.
    """
    vulns = vuln_loader.load_vulns_by_dir(config.vuln_cn_dir_wildcard)
    vuln = filters.filter_vuln_by_name(vulns=vulns, name=args.cnv)
    if not vuln:
        color_print.error_and_exit(
            'no cloud native vulnerability named {cnv}'.format(
                cnv=args.cnv))

    if vuln['class'] == 'config' or vuln['class'] == 'mount' or vuln['class'] == 'no-vuln':
        vulns = vuln_loader.load_vulns_by_dir(config.vuln_cn_dir_wildcard)
        vuln = filters.filter_vuln_by_name(vulns=vulns, name=args.cnv)
        if not vuln:
            color_print.error_and_exit(
                'no vulnerability named {cnv}'.format(
                    cnv=args.cnv))

        internal_cmds.delete_vuln_resources_in_k8s(vuln, verbose=args.verbose)
        return

    color_print.debug(
        '{vuln} is going to be removed'.format(
            vuln=vuln['name']))

    if vuln['class'].startswith('docker'):
        DockerInstaller.uninstall(verbose=args.verbose)
        color_print.debug('{v} successfully removed'.format(v=vuln['name']), 2)

    if vuln['class'] == 'kubernetes':
        KubernetesInstaller.uninstall(verbose=args.verbose)
        color_print.debug('{v} successfully removed'.format(v=vuln['name']), 2)

    if vuln['class'] == 'kata-containers':
        if KataContainersInstaller.uninstall(verbose=args.verbose):
            color_print.debug(
                '{v} successfully removed'.format(
                    v=vuln['name']), 2)
        else:
            color_print.error('failed to remove {v}'.format(v=vuln['name']))

    if vuln['class'] == 'kernel':
        color_print.warning(
            'removal of vulnerabilities in class {vuln_class} is unsupported'.format(
                vuln_class=vuln['class']))
        return


def retrieve(args):
    """List supported cloud native vulnerabilities.

    Args:
        args: Actually not used.

    Returns:
        None.
    """
    vulns = vuln_loader.load_vulns_by_dir(config.vuln_cn_dir_wildcard)
    vulns_stripped = list()
    for vuln in vulns:
        vuln_stripped = collections.OrderedDict()
        vuln_stripped['name'] = vuln['name']
        vuln_stripped['class'] = vuln['class']
        vuln_stripped['type'] = vuln['type']
        vulns_stripped.append(vuln_stripped)
    table.show_table(
        vulns_stripped, sort_key=operator.itemgetter(
            2, 1), sortby='class')
