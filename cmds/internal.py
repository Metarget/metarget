"""
Internal Commands
"""

import utils.color_print as color_print
from core.env_managers.kubernetes_resource_deployer import KubernetesResourceDeployer
from core.vuln_app_manager import port_manager
from core.vuln_app_manager import yaml_modifier


def deploy_vuln_resources_in_k8s(vuln, external=False, verbose=False):
    """Deploy resources related to one vulnerability.

     Deploy resources related to one vulnerability specified by args.vuln
     in the current Kubernetes cluster.

    Args:
        vuln: Information dict about one vulnerability and its resources' locations.
        external: Expose service through NodePort or not (ClusterIP by default)..
        verbose: Verbose or not.

    Returns:
        None.
    """
    color_print.debug(
        '{vuln} is going to be installed'.format(
            vuln=vuln['name']))
    yamls = [(vuln['path'] + '/' + dependency)
             for dependency in vuln['dependencies']['yamls']]
    # if services need to be exposed externally, modify yaml
    # and change type from ClusterIP to NodePort
    if external:
        yamls_svc = [yaml for yaml in yamls if yaml.endswith('-service.yaml')]
        if yamls_svc:
            # remove services from yamls
            yamls = [yaml for yaml in yamls if yaml.endswith('-service.yaml')]
            # allocate ports on host
            host_ports = port_manager.allocate_ports(entries=yamls_svc)
            # generate new yamls using nodeport in svc yamls
            new_yamls_svc = yaml_modifier.generate_svcs_with_clusterip_to_nodeport(yamls=yamls, ports=host_ports)
            # add updated services into original yamls
            yamls.extend(new_yamls_svc)

    if not KubernetesResourceDeployer.apply(yamls, verbose=verbose):
        color_print.error(
            'error: failed to install {v}'.format(
                v=vuln['name']))
    else:
        color_print.debug('{v} successfully installed'.format(v=vuln['name']))
        pod_name = vuln['name'].replace('_', '-')
        color_print.debug(
            'run `kubectl exec -it {pod_name} /bin/bash` to have a try :)'.format(pod_name=pod_name))


def delete_vuln_resources_in_k8s(vuln, verbose=False):
    """Delete resources related to one vulnerability.

    Delete resources related to one vulnerability specified by args.vuln
    from the current Kubernetes cluster.

    Args:
        vuln: Information dict about one vulnerability and its resources' locations.
        verbose: Verbose or not.

    Returns:
        None.
    """
    color_print.debug(
        '{vuln} is going to be removed'.format(
            vuln=vuln['name']))
    yamls = [(vuln['path'] + '/' + dependency)
             for dependency in vuln['dependencies']['yamls']]

    if not KubernetesResourceDeployer.delete(yamls, verbose=verbose):
        color_print.error('error: failed to remove {v}'.format(v=vuln['name']))
    else:
        # remove port record if applicable
        yamls_svc = [yaml for yaml in yamls if yaml.endswith('-service.yaml')]
        if yamls_svc:  # release ports not used any more
            port_manager.release_ports(yamls_svc)

        color_print.debug('{v} successfully removed'.format(v=vuln['name']))
