"""
CNI Plugin Installer
"""

from packaging import version

import config
import utils.color_print as color_print
from core.env_managers.installer import Installer


class CNIPluginInstaller(Installer):
    @classmethod
    def install_cni_plugin(cls, k8s_version, context,
                           mappings=None, verbose=False):
        """Install CNI plugin.

        Install a CNI plugin specified in context for the current Kubernetes cluster.

        Args:
            k8s_version: Version of the current Kubernetes cluster.
            context: Context of installation process.
            mappings: Dict used to store info which will be used to generate worker script later.
            verbose: Verbose or not.

        Returns:
            None.
        """
        color_print.debug('installing cni plugin')
        if context.get('cni_plugin', None) == 'flannel':
            CNIPluginInstaller._install_flannel(
                k8s_version=k8s_version, context=context, mappings=mappings, verbose=verbose)
        if context.get('cni_plugin', None) == 'calico':
            CNIPluginInstaller._install_calico(
                k8s_version=k8s_version, context=context, mappings=mappings, verbose=verbose)
        if context.get('cni_plugin', None) == 'cilium':
            CNIPluginInstaller._install_cilium(
                k8s_version=k8s_version, context=context, mappings=mappings, verbose=verbose)

    @classmethod
    def _install_flannel(cls, k8s_version, context,
                         mappings=None, verbose=False):
        # refer to
        # https://github.com/coreos/flannel/blob/master/Documentation/kubernetes.md#older-versions-of-kubernetes
        # and
        # https://github.com/coreos/flannel#getting-started-on-kubernetes
        color_print.debug('installing flannel')
        k8s_version = version.parse(k8s_version)
        if version.parse('1.6') <= k8s_version <= version.parse('1.15'):
            cls._pull_quay_image(
                config.flannel_image_k8s_1_6_to_1_15,
                domestic=context.get(
                    'domestic',
                    False),
                mappings=mappings,
                verbose=verbose)
            cls._create_k8s_resources(
                config.flannel_yaml_k8s_1_6_to_1_15_rbac,
                verbose=verbose)
            cls._create_k8s_resources(
                config.flannel_yaml_k8s_1_6_to_1_15,
                verbose=verbose)
        else:
            cls._pull_quay_image(
                config.flannel_image_k8s_from_1_16,
                domestic=context.get(
                    'domestic',
                    False),
                mappings=mappings,
                verbose=verbose)
            if k8s_version.minor == version.parse(
                    '1.16').minor and k8s_version.major == version.parse('1.16').major:
                cls._create_k8s_resources(
                    config.flannel_yaml_k8s_16, verbose=verbose)
            elif k8s_version > version.parse('1.16'):
                cls._create_k8s_resources(
                    config.flannel_yaml_k8s_over_16, verbose=verbose)

    @classmethod
    def _install_calico(cls, k8s_version, context,
                        mappings=None, verbose=False):
        # refer to
        # https://github.com/operator-framework/operator-lifecycle-manager/issues/1818
        # calico only work for k8s 1.16+? (it is true in my cluster)
        # refer to
        # https://docs.projectcalico.org/getting-started/kubernetes/self-managed-onprem/onpremises
        color_print.debug('installing calico')
        for image in config.calico_images:
            cls._pull_docker_image(
                image, domestic=context.get(
                    'domestic', False), mappings=mappings, verbose=verbose)
        k8s_version = version.parse(k8s_version)
        # seems not to work below 1.14
        if k8s_version < version.parse('1.14'):
            cls._create_k8s_resources(
                config.calico_yaml_below_1_14, verbose=verbose)
        else:
            cls._create_k8s_resources(
                config.calico_yaml_from_1_14, verbose=verbose)

    @classmethod
    def _install_cilium(cls, k8s_version, context,
                        mappings=None, verbose=False):
        # refer to
        # https://docs.cilium.io/en/stable/concepts/kubernetes/requirements/#k8s-requirements
        # https://docs.cilium.io/en/stable/gettingstarted/k8s-install-default/
        # requirements:
        # Linux kernel >= 4.9
        # Kubernetes >= 1.12
        color_print.debug('installing cilium')
        for image in config.cilium_images:
            cls._pull_quay_image(
                image, domestic=context.get(
                    'domestic', False), mappings=mappings, verbose=verbose)

        cls._create_k8s_resources(config.cilium_yaml, verbose=verbose)
