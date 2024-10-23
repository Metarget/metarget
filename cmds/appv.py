"""
Application Vulnerabilities Commands
"""

import collections
import operator
import utils.table as table
import utils.color_print as color_print
import utils.checkers as checkers
import utils.filters as filters
import config
import cmds.internal as internal_cmds
from core.vuln_app_manager import vuln_loader

def install(args):
    """Install an application vulnerability.

    Install an application vulnerability specified by args.appv in the current
    Kubernetes cluster.

    Args:
        args.appv: Name of the specified application vulnerability.
        args.external: Expose service through NodePort or not (ClusterIP by default).
        args.host_net: Share host network namespace or not.
        args.host_pid: Share host PID namespace or not.
        args.verbose: Verbose or not.

    Returns:
        None.
    """
    vulns = vuln_loader.load_vulns_by_dir(config.vuln_app_dir_wildcard)
    vuln = filters.filter_vuln_by_name(vulns=vulns, name=args.appv)
    if not vuln:
        color_print.error_and_exit(
            'no application vulnerability named {appv}'.format(
                appv=args.appv))
    if not checkers.docker_kubernetes_installed(
            verbose=args.verbose):  # should install docker or k8s firstly
        return

    internal_cmds.deploy_vuln_resources_in_k8s(
        vuln,
        external=args.external,
        host_net=args.host_net,
        host_pid=args.host_pid,
        verbose=args.verbose)


def remove(args):
    """Remove an installed application vulnerability.

    Remove an installed application vulnerability specified by args.appv from the
    current Kubernetes cluster.

    Args:
        args.appv: Name of the specified application vulnerability.
        args.verbose: Verbose or not.

    Returns:
        None.
    """
    vulns = vuln_loader.load_vulns_by_dir(config.vuln_app_dir_wildcard)
    vuln = filters.filter_vuln_by_name(vulns=vulns, name=args.appv)
    if not vuln:
        color_print.error_and_exit(
            'no vulnerability named {appv}'.format(
                appv=args.appv))

    internal_cmds.delete_vuln_resources_in_k8s(vuln, verbose=args.verbose)


def retrieve(args):
    """List supported application vulnerabilities.

    Args:
        args: Actually not used.

    Returns:
        None.
    """
    vulns = vuln_loader.load_vulns_by_dir(config.vuln_app_dir_wildcard)
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

def show_running(args):
    """
    Show running application vulnerabilities.

    Args:
        args: Command-line arguments (not used).

    Returns:
        None.
    """
    running_vulns = internal_cmds.get_running_vulns_in_k8s()
    if not running_vulns:
        color_print.warn('No running application vulnerabilities found.')
        return

    running_vulns_stripped = []
    for vuln in running_vulns:
        vuln_stripped = collections.OrderedDict()
        vuln_stripped['name'] = vuln['name']
        vuln_stripped['class'] = vuln['class']
        vuln_stripped['status'] = vuln['status']
        running_vulns_stripped.append(vuln_stripped)

    table.show_table(
        running_vulns_stripped, sort_key=operator.itemgetter(
            2, 1), sortby='class')
