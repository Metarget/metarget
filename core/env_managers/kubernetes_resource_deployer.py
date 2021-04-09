"""
Kubernetes Resource Deployer
- we do not use official python client for kubernetes API
- because some version are not supported, according to
- https://github.com/kubernetes-client/python#compatibility
"""

import copy
import subprocess

import utils.color_print as color_print


class KubernetesResourceDeployer:
    @classmethod
    def apply(cls, resources_list):
        return cls._act(resources_list=resources_list, action='apply')

    @classmethod
    def delete(cls, resources_list):
        return cls._act(resources_list=resources_list, action='delete')

    @classmethod
    def _act(cls, resources_list, action=None):
        cmd_kubectl_create = 'kubectl {action} -f'.format(action=action).split()
        for res in resources_list:
            temp_cmd = copy.copy(cmd_kubectl_create)
            temp_cmd.append(res)
            try:
                subprocess.run(temp_cmd, check=True)
            except subprocess.CalledProcessError:
                color_print.error('error: failed to {action} resources in {res}'.format(action=action, res=res))
                return False
        return True


if __name__ == '__main__':
    pass
