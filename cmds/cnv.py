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
from core.vuln_cn_manager import load_vulns
from core.env_managers.docker_installer import DockerInstaller
from core.env_managers.kubernetes_installer import KubernetesInstaller
from core.env_managers.kernel_installer import KernelInstaller
from core.env_managers.kata_containers_installer import KataContainersInstaller


def install(args):
    vulns = load_vulns.load_vulns_by_dir(config.vuln_cn_dir_wildcard)
    vuln = filters.filter_vuln_by_name(vulns=vulns, name=args.cnv)
    if not vuln:
        color_print.error_and_exit(
            'error: no cloud native vulnerability named {cnv}'.format(
                cnv=args.cnv))
    # deploy vulnerability
    if vuln['class'] == 'config' or vuln['class'] == 'mount' or vuln['class'] == 'no-vuln':
        if not checkers.docker_kubernetes_installed(
                verbose=args.verbose):  # should install docker or k8s firstly
            return
        internal_cmds.deploy_vuln_resources_in_k8s(vuln, verbose=args.verbose)

    if vuln['class'].startswith('docker'):
        if checkers.docker_specified_installed(
                vuln['dependencies'], verbose=args.verbose):
            color_print.debug(
                '{vuln} already installed'.format(
                    vuln=vuln['name']))
            return
        color_print.debug(
            '{vuln} is going to be installed'.format(
                vuln=vuln['name']))
        color_print.debug('uninstall current docker if applicable')
        DockerInstaller.uninstall(verbose=args.verbose)
        if not DockerInstaller.install_by_version(
                vuln['dependencies'], verbose=args.verbose):
            color_print.error(
                'error: failed to install {v}'.format(
                    v=vuln['name']))
        else:
            color_print.debug(
                '{v} successfully installed'.format(
                    v=vuln['name']))

    if vuln['class'] == 'kubernetes':
        if checkers.kubernetes_specified_installed(
                vuln['dependencies'], verbose=args.verbose):
            color_print.debug(
                '{vuln} already installed'.format(
                    vuln=vuln['name']))
            return
        if not checkers.docker_installed(verbose=args.verbose):
            color_print.error(
                'error: it seems docker is not installed or correctly configured')
            color_print.error_and_exit(
                'you can run `metarget gadget install docker --version 18.03.1` to install one')
        color_print.debug(
            '{vuln} is going to be installed'.format(
                vuln=vuln['name']))
        color_print.debug('uninstall current kubernetes if applicable')
        KubernetesInstaller.uninstall(verbose=args.verbose)
        temp_pod_network_cidr = args.pod_network_cidr if args.pod_network_cidr else config.cni_plugin_cidrs[
            args.cni]

        if not KubernetesInstaller.install_by_version(vuln['dependencies'],
                                                      cni_plugin=args.cni,
                                                      pod_network_cidr=temp_pod_network_cidr,
                                                      domestic=args.domestic,
                                                      taint_master=args.taint_master,
                                                      http_proxy=args.http_proxy,
                                                      no_proxy=args.no_proxy,
                                                      verbose=args.verbose):
            color_print.error(
                'error: failed to install {v}'.format(
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
                'error: failed to install {v}'.format(
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
        pass


def remove(args):
    vulns = load_vulns.load_vulns_by_dir(config.vuln_cn_dir_wildcard)
    vuln = filters.filter_vuln_by_name(vulns=vulns, name=args.cnv)
    if not vuln:
        color_print.error_and_exit(
            'error: no cloud native vulnerability named {cnv}'.format(
                cnv=args.cnv))

    if vuln['class'] == 'config' or vuln['class'] == 'mount' or vuln['class'] == 'no-vuln':
        vulns = load_vulns.load_vulns_by_dir(config.vuln_cn_dir_wildcard)
        vuln = filters.filter_vuln_by_name(vulns=vulns, name=args.cnv)
        if not vuln:
            color_print.error_and_exit(
                'error: no vulnerability named {cnv}'.format(
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

    if vuln['class'] == 'kernel':
        color_print.warning(
            'removal of vulnerabilities in class {vuln_class} is unsupported'.format(
                vuln_class=vuln['class']))
        return

    if vuln['class'] == 'kata-containers':
        pass


def retrieve(args):
    vulns = load_vulns.load_vulns_by_dir(config.vuln_cn_dir_wildcard)
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
