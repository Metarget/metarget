"""
Applications YAML Modifier
"""
import os
import yaml

import config


def generate_svcs_with_clusterip_to_nodeport(yamls, ports):
    """Generate NodePort services' YAMLs.

    Generate services' YAMLs of type NodePort based on the original
    ClusterIP ones.

    Args:
        yamls: Paths list of services' YAMLs.
        ports: Ports allocated to services defined in YAMLs above.

    Returns:
        New YAMLs' paths.
    """
    # yaml_path is like:
    # vulns_app/dvwa/dvwa//dvwa-service.yaml
    new_yamls = list()
    for yaml_path, port in zip(yamls, ports):
        with open(yaml_path, 'r') as fr:
            resource = yaml.load(fr, Loader=yaml.SafeLoader)
            # cluster -> nodeport
            resource['spec']['type'] = 'NodePort'
            # assuming that the service only uses one port!
            # if service uses more than one port,
            # only one of ports it uses is exposed through node port
            resource['spec']['ports'][0]['nodePort'] = int(port)
            new_yaml_path = os.path.join(
                config.runtime_data_dir, yaml_path.split('/')[-1])
            # save new yaml under data/
            with open(new_yaml_path, 'w') as fw:
                yaml.dump(resource, fw)
            new_yamls.append(new_yaml_path)
    return new_yamls


def generate_deployments_with_modifications(
        yamls, host_path=False, host_net=False, host_pid=False):
    """Generate deployments' YAMLs with modifications.

    Args:
        yamls: Paths list of deployments' YAMLs.
        host_path: Add hostPath volume or not.
        host_net: Share host network namespace or not.
        host_pid: Share host PID namespace or not.

    Returns:
        New YAMLs' paths.
    """
    # yaml_path is like:
    # vulns_app/php/CVE-2018-19518/cve-2018-19518-deployment.yaml
    new_yamls = list()
    for yaml_path in yamls:
        with open(yaml_path, 'r') as fr:
            resource = yaml.load(fr, Loader=yaml.SafeLoader)
            try:
                if host_path:
                    volumes = resource['spec']['template']['spec']['volumes']
                    for volume in volumes:
                        # e.g. php/CVE-2018-19518/www
                        dest = volume['hostPath']['path']
                        # e.g. /root/metarget/vulns_app
                        base_path = os.getcwd()
                        # e.g. /root/metarget/vulns_app/php/CVE-2018-19518/www
                        volume['hostPath']['path'] = os.path.join(
                            base_path, config.vuln_app_dir_prefix, dest)
                resource['spec']['template']['spec']['hostNetwork'] = host_net
                resource['spec']['template']['spec']['hostPID'] = host_pid
            except (TypeError, IndexError, KeyError):
                continue
            new_yaml_path = os.path.join(
                config.runtime_data_dir, yaml_path.split('/')[-1])
            # save new yaml under data/
            with open(new_yaml_path, 'w') as fw:
                yaml.dump(resource, fw)
            new_yamls.append(new_yaml_path)
    return new_yamls
