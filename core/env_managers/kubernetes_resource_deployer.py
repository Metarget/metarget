"""
Kubernetes Resource Deployer
- we do not use official python client for kubernetes API
- because some version are not supported, according to
- https://github.com/kubernetes-client/python#compatibility
"""

import copy
import subprocess

import utils.verbose as verbose_func
import utils.color_print as color_print


class KubernetesResourceDeployer:
    @classmethod
    def apply(cls, resources_list, verbose=False):
        return cls._act(resources_list=resources_list, action='apply', verbose=verbose)

    @classmethod
    def delete(cls, resources_list, verbose=False):
        return cls._act(resources_list=resources_list, action='delete', verbose=verbose)

    @classmethod
    def _act(cls, resources_list, action=None, verbose=False):
        stdout, stderr = verbose_func.verbose_output(verbose)
        cmd_kubectl_create = 'kubectl {action} -f'.format(action=action).split()
        for res in resources_list:
            temp_cmd = copy.copy(cmd_kubectl_create)
            temp_cmd.append(res)
            try:
                subprocess.run(temp_cmd, stdout=stdout, stderr=stderr, check=True)
            except subprocess.CalledProcessError:
                color_print.error('error: failed to {action} resources in {res}'.format(action=action, res=res))
                return False
        return True


if __name__ == '__main__':
    pass
