"""
Host Ports Manager
"""

import yaml

import config


def allocate_ports(entries):
    """Allocate new node ports for services.

    Args:
        entries: List of services names or paths.

    Returns:
        List of ports allocated.
    """
    ports = list()
    with open(config.runtime_host_ports_usage, 'r') as f:
        content = yaml.load(f, Loader=yaml.SafeLoader)
        ports_usage = content if content else []
        ports_used_list = [svc['port'] for svc in ports_usage]
        for entry in entries:
            port_to_be_allocated = _get_next_available_port(config.runtime_host_port_lower_bound, ports_used_list)
            ports.append(port_to_be_allocated)  # will be returned
            ports_usage.append({  # will be write back into host_ports_usage file
                'name': entry,
                'port': port_to_be_allocated,
            })
            ports_used_list.append(port_to_be_allocated)  # will not be allocated in the next iteration
    with open(config.runtime_host_ports_usage, 'w') as f:
        yaml.dump(ports_usage, f)
    return ports


def _get_next_available_port(low_bound, ports_usage):
    temp_port = low_bound
    while True:
        if temp_port not in ports_usage:
            return temp_port
        else:
            temp_port += 1


def release_ports(entries):
    """Release ports not used any more.

    Args:
        entries: List of services names or paths.

    Returns:
        None.
    """
    with open(config.runtime_host_ports_usage, 'r') as f:
        content = yaml.load(f, Loader=yaml.SafeLoader)
        ports_usage = content if content else []
        services_using_ports = [port_usage['name'] for port_usage in ports_usage]
        for entry in entries:
            try:
                index = services_using_ports.index(entry)
                ports_usage.pop(index)
                services_using_ports.pop(index)
            except ValueError:
                continue
    with open(config.runtime_host_ports_usage, 'w') as f:
        yaml.dump(ports_usage, f)


if __name__ == '__main__':
    ports_test = allocate_ports(['svc1', 'svc2', 'svc3'])
    print("allocate 3 ports:", ports_test[0], ports_test[1], ports_test[2])
    release_ports(['svc1', 'svc2', 'svc3'])
    print('release 3 ports')
