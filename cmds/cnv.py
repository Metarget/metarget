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
from packaging import version

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
            # if containerd.io is specified in the dependencies, check if it is installed
            if checkers.gadget_in_gadgets(
                    vuln['dependencies'], name='containerd.io', verbose=args.verbose):
                if not checkers.containerd_specified_installed(
                        vuln['dependencies'], verbose=args.verbose):
                    installed_flag = False
            # if runc is specified in the dependencies, check if it is installed
            if checkers.gadget_in_gadgets(
                    vuln['dependencies'], name='runc', verbose=args.verbose):
                if not checkers.runc_specified_installed(
                        vuln['dependencies'], verbose=args.verbose):
                    installed_flag = False
            # if kernel is specified in the dependencies, check if it is installed
            if checkers.gadget_in_gadgets(
                    vuln['dependencies'], name='kernel', verbose=args.verbose):
                if not checkers.kernel_specified_installed(
                        vuln['dependencies'], verbose=args.verbose):
                    installed_flag = False
            if installed_flag:
                color_print.debug(
                    '{vuln} already installed'.format(
                        vuln=vuln['name']))
                return
        color_print.debug(
            '{vuln} is going to be installed'.format(
                vuln=vuln['name']))
        color_print.debug('uninstalling current docker gadgets if applicable')
        
        # ask user whether to uninstall current docker
        loop_count = 0
        while True:
            if loop_count > 10:
                color_print.error_and_exit('too many invalid inputs')
            uninstall = color_print.debug_input(
                'uninstall current docker gadgets? (y/n) ')
            if uninstall == 'y' or uninstall == 'Y':
                DockerInstaller.uninstall(verbose=args.verbose)
                break
            elif uninstall == 'n' or uninstall == 'N':
                break
            else:
                color_print.error('invalid input')
                loop_count += 1
        """
        there ia an error below(the commented part):
        the error is that "DockerInstaller.install_by_version" can only install docker-ce/docker-cli/containerd.io
        but runc/kernel is also needed to be installed in some occasions(
        temporarily cnvs dont have runc,runc is only for gadget installation,
        but we still consider this situation anyway, of course for furture)
        """
        # if not DockerInstaller.install_by_version(
        #         vuln['dependencies'], verbose=args.verbose):
        #     color_print.error(
        #         'failed to install {v}'.format(
        #             v=vuln['name']))
        # else:
        #     color_print.debug(
        #         '{v} successfully installed'.format(
        #             v=vuln['name']))
        success_flag=True # true only if all gadgets successfully installed
        temp_gadgets=[]# gadgets only include docker/containerd,without runc/kernel
        for gadget in vuln['dependencies']:
            if gadget['name']=='docker-ce':
                install_version=gadget['version']
        if version.parse(install_version) < version.parse('18.09.0'):
            temp_gadgets = [{
                'name': 'docker-ce',
                'version': install_version,
            }]
        else:
            temp_gadgets = [{
                'name': 'docker-ce',
                'version': install_version,
            }, {
                'name': 'docker-ce-cli',
                'version': install_version,
            }]  
        for gadget in vuln['dependencies']:
            if gadget['name']=='containerd.io':
                temp_gadgets.append(gadget)
        if not DockerInstaller.install_by_version(
                temp_gadgets, verbose=args.verbose):
            color_print.error(
                'failed to install {v} during docker installation.'.format(
                    v=vuln['name']))
            success_flag=False
        #else:
            # color_print.debug(
            #     '{v} successfully installed'.format(
            #         v=vuln['name']))
        kernel_flag=False # if kernel in gadget ,we use this flag to determine whether to reboot
        # next we consider runc/kernel
        for gadget in vuln['dependencies']:
            if gadget['name']=='runc':
                runc_version=gadget['version']
                checkers.runc_executable(verbose=args.verbose)
                if DockerInstaller.install_runc(runc_version, verbose=args.verbose):
                    color_print.debug('runc with version {version} successfully installed'.format(
                    version=runc_version))
                else:
                    color_print.error(
                            'failed to install {v} during runc installation'.format(
                                v=vuln['name']))
                    success_flag=False
            elif gadget['name']=='kernel':
                kernel_flag=True
                kernel_gadgets=[]
                kernel_gadgets.append(gadget)
                if checkers.kernel_specified_installed(
                        kernel_gadgets, verbose=args.verbose):
                    color_print.debug(
                        'kernel already installed.')
                    kernel_flag=False
                else:
                    color_print.debug(
                        'kernel is going to be installed')
                    if not KernelInstaller.install_by_version(
                            kernel_gadgets, verbose=args.verbose):
                        color_print.error(
                            'failed to install {v} during kernel installation'.format(
                                v=vuln['name']))
                        success_flag=False
        # right now all  installation finished
        if success_flag==True:
            color_print.debug(
                '{v} successfully installed'.format(
                    v=vuln['name']))
        if kernel_flag==True:
            reboot = color_print.debug_input('reboot system now? (y/n) ')
            if reboot == 'y' or reboot == 'Y':
                system_func.reboot_system(verbose=args.verbose)


    if vuln['class'] == 'kubernetes':
        if checkers.kubernetes_specified_installed(
                vuln['dependencies'], verbose=args.verbose):
            color_print.debug(
                '{vuln} already installed'.format(
                    vuln=vuln['name']))
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
                    v=vuln['name']))

    if vuln['class'] == 'kernel':
        if checkers.kernel_specified_installed(
                vuln['dependencies'], verbose=args.verbose):
            color_print.debug(
                '{vuln} already installed'.format(
                    vuln=vuln['name']))
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
                    v=vuln['name']))
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
                    vuln=vuln['name']))
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
                    v=vuln['name']))


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
        color_print.debug('{v} successfully removed'.format(v=vuln['name']))

    if vuln['class'] == 'kubernetes':
        KubernetesInstaller.uninstall(verbose=args.verbose)
        color_print.debug('{v} successfully removed'.format(v=vuln['name']))

    if vuln['class'] == 'kata-containers':
        if KataContainersInstaller.uninstall(verbose=args.verbose):
            color_print.debug(
                '{v} successfully removed'.format(
                    v=vuln['name']))
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
