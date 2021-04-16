"""
Applications YAML Modifier
"""

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
    for yaml_path, port in yamls, ports:
        with open(yaml_path, 'r') as fr:
            resource = yaml.load(fr, Loader=yaml.SafeLoader)
            # cluster -> nodeport
            resource['spec']['type'] = 'NodePort'
            resource['spec']['ports']['nodePort'] = int(port)
            new_yaml_path = config.runtime_data_dir + '/' + yaml_path.split('/')[-1]
            # save new yaml under data/
            with open(new_yaml_path, 'w') as fw:
                yaml.dump(resource, fw)
            new_yamls.append(new_yaml_path)
    return new_yamls
