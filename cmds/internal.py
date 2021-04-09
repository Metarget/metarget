"""
Internal Commands
"""

import utils.color_print as color_print
from core.env_managers.kubernetes_resource_deployer import KubernetesResourceDeployer


def deploy_vuln_resources_in_k8s(vuln):
    color_print.debug(
        '{vuln} is going to be installed'.format(
            vuln=vuln['name']))
    yamls = [(vuln['path'] + '/' + dependency)
             for dependency in vuln['dependencies']['yamls']]
    if not KubernetesResourceDeployer.apply(yamls):
        color_print.error('error: failed to install {v}'.format(v=vuln['name']))
    else:
        color_print.debug('{v} successfully installed'.format(v=vuln['name']))


def delete_vuln_resources_in_k8s(vuln):
    color_print.debug(
        '{vuln} is going to be removed'.format(
            vuln=vuln['name']))
    yamls = [(vuln['path'] + '/' + dependency)
             for dependency in vuln['dependencies']['yamls']]
    if not KubernetesResourceDeployer.delete(yamls):
        color_print.error('error: failed to remove {v}'.format(v=vuln['name']))
    else:
        color_print.debug('{v} successfully removed'.format(v=vuln['name']))
