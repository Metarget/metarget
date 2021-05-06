"""
Kubernetes Installer
- https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/
"""

import subprocess
import os
import re
from string import Template
import shutil
from packaging import version
import copy

import config
import utils.color_print as color_print
import utils.verbose as verbose_func
from core.env_managers.installer import Installer
from core.env_managers.cni_plugin_installer import CNIPluginInstaller


class KubernetesInstaller(Installer):
    _kubernetes_gadgets = [
        'kubeadm',
        'kubectl',
        'kubelet',
        'kubernetes-cni',
    ]
    _kubernetes_requirements = [
        'apt-transport-https',
        'curl',
    ]
    _cmd_modprobe = "modprobe br_netfilter".split()
    _cmd_swapoff = 'swapoff -a'.split()
    _cmd_kubeadm_list_image = 'kubeadm config images list'.split()
    _cmd_kubeadm_reset = 'kubeadm reset'.split()
    _cmd_enable_schedule_master = 'kubectl taint nodes --all node-role.kubernetes.io/master-'.split()
    _kubeadm_common_options = '--ignore-preflight-errors=NumCPU,cri'

    @classmethod
    def uninstall(cls, verbose=False):
        """Uninstall Kubernetes.

        Args:
            verbose: Verbose or not.

        Returns:
            None.
        """
        stdout, stderr = verbose_func.verbose_output(verbose)
        try:
            subprocess.run(
                cls._cmd_kubeadm_reset,
                input='y\n'.encode('utf-8'),
                stdout=stdout,
                stderr=stderr,
                check=False)
        except FileNotFoundError:
            pass
        subprocess.run(
            cls.cmd_apt_uninstall +
            cls._kubernetes_gadgets,
            stdout=stdout,
            stderr=stderr,
            check=False)

    @classmethod
    def install_by_version(cls, gadgets, cni_plugin, pod_network_cidr,
                           taint_master=False, domestic=False, http_proxy='',
                           https_proxy='', no_proxy='', verbose=False):
        """Install Kubernetes with specified version.

        Args:
            gadgets: Kubernetes gadgets (e.g. kubeadm, kubelet).
            cni_plugin: Name of CNI plugin.
            pod_network_cidr: CIDR of pod network.
            taint_master: Taint the master node or not.
            domestic: Pull Kubernetes images from domestic source or not.
            http_proxy: HTTP proxy used when pulling official images.
            https_proxy: HTTPS proxy if necessary.
            no_proxy: Domains which should be visited without proxy.
            verbose: Verbose or not.

        Returns:
            Boolean indicating whether Kubernetes is successfully installed or not.
        """
        temp_envs = copy.copy(dict(os.environ))
        temp_envs['http_proxy'] = http_proxy
        temp_envs['https_proxy'] = https_proxy
        temp_envs['no_proxy'] = no_proxy
        context = {
            'envs': temp_envs,
            'domestic': domestic,
            'pod_network_cidr': pod_network_cidr if pod_network_cidr else config.cni_plugin_cidrs[cni_plugin],
            'cni_plugin': cni_plugin,
            'taint_master': taint_master,
        }
        return cls._install_with_context(gadgets, context, verbose=verbose)

    @classmethod
    def _install_with_context(cls, gadgets, context=None, verbose=False):
        stdout, stderr = verbose_func.verbose_output(verbose)
        worker_template_mappings = dict()  # used to generate install_k8s_worker_script
        worker_template_mappings['domestic'] = context.get('domestic', False)
        cls._pre_configure(verbose=verbose)
        cls._pre_install(worker_template_mappings, verbose=verbose)
        # firstly install kubernetes-cni, because of:
        # issue: https://github.com/kubernetes/kubernetes/issues/75701
        # note that the solution below is unstable and ugly to some extent...
        kubernetes_cni_version = cls._get_kubernetes_cni_version(
            'kubelet', gadgets[0]['version'], verbose=verbose)
        if kubernetes_cni_version:
            cls._install_one_gadget_by_version(
                'kubernetes-cni', kubernetes_cni_version, worker_template_mappings, verbose=verbose)
        # install kubelet, kubeadm, kubectl
        for gadget in gadgets:
            cls._install_one_gadget_by_version(
                gadget['name'], gadget['version'], worker_template_mappings, verbose=verbose)

        # pull necessary k8s images
        k8s_version = gadgets[0]['version']
        images_base, images_extra = cls._get_k8s_images_list_by_version(
            k8s_version)
        cls._pull_k8s_images(
            k8s_version=k8s_version,
            images_base=images_base,
            images_extra=images_extra,
            domestic=context.get(
                'domestic', False),
            mappings=worker_template_mappings,
            verbose=verbose)

        # run kubeadm
        if not cls._run_kubeadm(
                k8s_version, context, mappings=worker_template_mappings, verbose=verbose):
            return False

        # configure kube config
        cls._config_auth()
        # delete master's taint if needed
        if not context.get('taint_master', None):
            subprocess.run(
                cls._cmd_enable_schedule_master,
                stdout=stdout,
                stderr=stderr,
                check=False)
        # install CNI plugin
        cls._install_cni_plugin(
            k8s_version,
            context,
            worker_template_mappings,
            verbose=verbose)
        # generate install-script for worker
        cls._update_k8s_worker_script(
            worker_template_mappings, context, verbose=verbose)
        return True

    @classmethod
    def _install_cni_plugin(cls, k8s_version, context,
                            mappings=None, verbose=False):
        CNIPluginInstaller.install_cni_plugin(
            k8s_version, context, mappings=mappings, verbose=verbose)

    @classmethod
    def _config_auth(cls):
        # mkdir -p $HOME /.kube
        # cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
        # chown $(id -u):$(id -g) $HOME/.kube/config
        home = os.environ.get('HOME')
        kube_dir = home + '/.kube'
        kube_config = kube_dir + '/config'
        shutil.rmtree(kube_dir, ignore_errors=True)
        os.mkdir(kube_dir)
        shutil.copy('/etc/kubernetes/admin.conf', kube_config)
        os.chown(kube_config, uid=os.getuid(), gid=os.getgid())

    @classmethod
    def _run_kubeadm(cls, k8s_version, context, mappings=None, verbose=False):
        color_print.debug('running kubeadm')
        stdout, stderr = verbose_func.verbose_output(verbose)
        temp_cmd = 'kubeadm init'.split()
        temp_cmd.append(
            '--kubernetes-version={k8s_version}'.format(k8s_version=k8s_version))
        temp_cmd.append(cls._kubeadm_common_options)
        if mappings:
            mappings['kubeadm_options'] = cls._kubeadm_common_options
        pod_network_cidr = context.get('pod_network_cidr', None)
        if pod_network_cidr:
            temp_cmd.append(
                '--pod-network-cidr={cidr}'.format(cidr=pod_network_cidr))
        try:
            subprocess.run(
                temp_cmd,
                stdout=stdout,
                stderr=stderr,
                check=True,
                env=context.get(
                    'envs',
                    None))
            return True
        except subprocess.CalledProcessError:
            color_print.error('failed to run kubeadm')
            return False

    @classmethod
    def _pull_k8s_images(cls, k8s_version, images_base,
                         images_extra, domestic=False, mappings=None, verbose=False):
        if domestic:  # pull from domestic sources
            if version.parse(k8s_version) <= version.parse(
                    config.k8s_stable_versions['1.9']):
                cls._pull_domestic_images(
                    images_base,
                    ori_prefix=config.k8s_images_prefix_official_9,
                    new_prefix=config.k8s_images_prefix_candidate,
                    mappings=mappings,
                    verbose=verbose)
                cls._pull_domestic_images(
                    images_extra,
                    ori_prefix=config.k8s_images_prefix_official_9,
                    new_prefix=config.k8s_images_prefix_candidate,
                    mappings=mappings,
                    verbose=verbose)
            else:
                cls._pull_domestic_images(
                    images_base,
                    ori_prefix=config.k8s_images_prefix_official,
                    new_prefix=config.k8s_images_prefix_candidate,
                    mappings=mappings,
                    verbose=verbose)
                cls._pull_domestic_images(
                    images_extra,
                    ori_prefix=config.k8s_images_prefix_official,
                    new_prefix=config.k8s_images_prefix_candidate,
                    mappings=mappings,
                    verbose=verbose)
        else:
            cls._pull_images(images_extra, mappings=mappings, verbose=verbose)
            cls._pull_images(images_base, mappings=mappings, verbose=verbose)

    @classmethod
    def _get_k8s_images_list(cls, k8s_version, images_base_version):
        images_base = [':v'.join((image, k8s_version))
                       for image in images_base_version]
        major_minor = re.search(r'^([\d]+\.[\d]+)', k8s_version).group(1)
        images_extra = config.k8s_images_extra[major_minor]
        return images_base, images_extra

    @classmethod
    def _get_k8s_images_list_by_version(cls, k8s_version):
        # k8s version > 1.11
        if version.parse(k8s_version) > version.parse(
                config.k8s_stable_versions['1.11']):
            images_base, images_extra = cls._get_k8s_images_list(
                k8s_version, config.k8s_images_base_from_12)
        # 1.10 <= k8s version <= 1.11
        elif version.parse('1.10') \
                <= version.parse(k8s_version) \
                <= version.parse(config.k8s_stable_versions['1.11']):
            images_base, images_extra = cls._get_k8s_images_list(
                k8s_version, config.k8s_images_base_10_to_11)
        # k8s version == 1.9 (versions lower than 1.9 are not supported)
        else:
            images_base, images_extra = cls._get_k8s_images_list(
                k8s_version, config.k8s_images_base_9)
        return images_base, images_extra

    @classmethod
    def _get_kubernetes_cni_version(cls, name, k8s_cni_version, verbose=False):
        _, stderr = verbose_func.verbose_output(verbose)
        kubelet_complete_version = cls._get_apt_complete_version(
            name, k8s_cni_version, verbose=verbose)
        res = subprocess.run(['apt', 'show', '{name}={version}'.format(
            name=name, version=kubelet_complete_version)], stdout=subprocess.PIPE, stderr=stderr, check=True)
        depends = None
        for entry in res.stdout.decode('utf-8').split('\n'):
            if entry.startswith('Depends:'):
                depends = entry
                break
        temp_version = None
        if depends:
            for depend in depends.split(','):
                if 'kubernetes-cni' in depend:
                    # maybe regex is better...
                    temp_version = depend.split(
                        '(')[-1].split(')')[0].split(' ')[-1]
                    # OK, regex (thanks to lzx):
                    # temp_version = re.search(r' kubernetes-cni \(= ([\d.]+)\)', depend).group(1)
                    break
        if temp_version:
            return cls._get_apt_complete_version(
                'kubernetes-cni', temp_version, verbose=verbose)
        else:
            return None

    @classmethod
    def _pre_configure(cls, verbose=False):
        color_print.debug('pre-configuring')
        stdout, stderr = verbose_func.verbose_output(verbose)
        # make sure br_netfilter is loaded.
        subprocess.run(
            cls._cmd_modprobe,
            stdout=stdout,
            stderr=stderr,
            check=True)

        # ensure net.bridge.bridge-nf-call-iptables
        with open('/etc/sysctl.d/k8s.conf', 'a') as f:
            f.write('net.bridge.bridge-nf-call-ip6tables = 1\n')
            f.write('net.bridge.bridge-nf-call-iptables = 1\n')

        # temporarily turn off swap
        subprocess.run(
            cls._cmd_swapoff,
            stdout=stdout,
            stderr=stderr,
            check=True)

    @classmethod
    def _pre_install(cls, mappings=None, verbose=False):
        color_print.debug('pre-installing')
        stdout, stderr = verbose_func.verbose_output(verbose)
        # install requirements
        subprocess.run(
            cls.cmd_apt_update,
            stdout=stdout,
            stderr=stderr,
            check=True)
        subprocess.run(
            cls.cmd_apt_install +
            cls._kubernetes_requirements,
            stdout=stdout,
            stderr=stderr,
            check=True)
        cls._add_apt_repository(gpg_url=config.k8s_apt_repo_gpg,
                                repo_entry=config.k8s_apt_repo_entry, verbose=verbose)
        # incompatible with ustc repo because it has no gpg currently
        mappings['gpg_url'] = config.k8s_apt_repo_gpg
        mappings['repo_entry'] = config.k8s_apt_repo_entry

    @classmethod
    def _update_k8s_worker_script(cls, mappings, context, verbose=False):
        color_print.debug('generating kubernetes worker script')
        final_mappings = {
            'gpg_url': mappings.pop('gpg_url'),
            'repo_entry': mappings.pop('repo_entry'),
            'kubernetes_cni_version': mappings.pop('kubernetes-cni'),
            'kubelet_version': mappings.pop('kubelet'),
            'kubeadm_version': mappings.pop('kubeadm'),
        }
        domestic = mappings.pop('domestic')
        cmds_pull_images = ''
        if domestic:
            for key, value in mappings.items():
                if 'pause' in key or 'proxy' in key or context.get(
                        'cni_plugin') in key:
                    cmds_pull_images += '\ndocker pull {image}\n'.format(
                        image=key)
                    cmds_pull_images += '\ndocker tag {old_name} {new_name}\n'.format(
                        old_name=key, new_name=value)
        else:
            for key, value in mappings.items():
                if value is None:  # official images
                    if 'pause' in key or 'proxy' in key or context.get(
                            'cni_plugin') in key:
                        cmds_pull_images += '\ndocker pull {image}\n'.format(
                            image=key)
        final_mappings['cmds_pull_images'] = cmds_pull_images
        final_mappings['master_ip'] = cls.get_host_ip()
        token, ca_cert_hash = cls._get_kubeadm_token_and_hash(verbose=verbose)
        final_mappings['token'], final_mappings['ca_cert_hash'] = token, ca_cert_hash
        final_mappings['kubeadm_options'] = mappings['kubeadm_options']
        with open(config.k8s_worker_template, 'r') as fr:
            with open(config.k8s_worker_script, 'w') as fw:
                worker_template = fr.read()
                data = Template(worker_template)
                res = data.safe_substitute(final_mappings)
                fw.write(res)
        color_print.debug(
            'kubernetes worker script generated at %s' %
            config.k8s_worker_script)

    @classmethod
    def _get_kubeadm_token_and_hash(cls, verbose=False):
        _, stderr = verbose_func.verbose_output(verbose)
        res = subprocess.run(
            'kubeadm token list'.split(),
            stdout=subprocess.PIPE,
            stderr=stderr,
            check=True)
        res = res.stdout.decode('utf-8')
        token = re.search(r'([a-z0-9]{6}\.[a-z0-9]{16})', res).group(1)
        res = subprocess.run(
            'bash {script}'.format(
                script=config.k8s_hash_generator).split(),
            stdout=subprocess.PIPE,
            stderr=stderr,
            check=True)
        res = res.stdout.decode('utf-8').strip()
        ca_cert_hash = res
        return token, ca_cert_hash


if __name__ == "__main__":
    KubernetesInstaller.uninstall()
    import sys
    if len(sys.argv) > 1:
        test_version = sys.argv[1]
    else:
        test_version = '1.11.10'
    temp_gadgets = [
        {'name': 'kubelet', 'version': test_version},
        {'name': 'kubeadm', 'version': test_version},
        {'name': 'kubectl', 'version': test_version},
    ]
    if len(sys.argv) > 2 and sys.argv[2] in config.available_cni_plugins:
        test_cni_plugin = sys.argv[2]
    else:
        test_cni_plugin = 'flannel'

    KubernetesInstaller.install_by_version(
        temp_gadgets,
        pod_network_cidr=config.cni_plugin_cidrs[test_cni_plugin],
        cni_plugin=test_cni_plugin,
        domestic=True,
        taint_master=False)
