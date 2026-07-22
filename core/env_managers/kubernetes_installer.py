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
from core.env_managers.docker_installer import DockerInstaller
from core.env_managers.cni_plugin_installer import CNIPluginInstaller
from core.env_managers.containerd_runtime_installer import ContainerdRuntimeInstaller
from core.env_managers.cri_dockerd_installer import CriDockerdInstaller


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
        'gnupg',
    ]
    _cmd_modprobe = "modprobe br_netfilter".split()
    _cmd_swapoff = 'swapoff -a'.split()
    _cmd_swapoff_fstab = ['sed', '-i', '/\\/swapfile/s/^/#/', '/etc/fstab']
    _cmd_swapoff_fstab_img = ['sed', '-i', '/\\/swap.img/s/^/#/', '/etc/fstab']
    _cmd_kubeadm_reset = 'kubeadm reset'.split()
    _cmd_rm_kube = 'rm -rf $HOME/.kube'.split()
    # k8s < 1.24 uses master taint; >= 1.24 uses control-plane taint
    _cmd_enable_schedule_master = 'kubectl taint nodes --all node-role.kubernetes.io/master-'.split()
    _cmd_enable_schedule_control_plane = 'kubectl taint nodes --all node-role.kubernetes.io/control-plane-'.split()
    _kubeadm_common_options = '--ignore-preflight-errors=NumCPU,cri,SystemVerification'

    # class-level runtime, set during install to route image operations correctly
    _current_runtime = 'docker'

    # ---- image operation overrides (dispatch to ctr when runtime=containerd) ----

    @classmethod
    def _image_exist(cls, image):
        if cls._current_runtime == 'containerd':
            return ContainerdRuntimeInstaller.image_exist_ctr(image)
        return super()._image_exist(image)

    @classmethod
    def _pull_image(cls, image, mappings=None, env=None, verbose=False,
                    pull_timeout=300):
        if cls._current_runtime == 'containerd':
            if mappings is not None:
                mappings[image] = None
            if not cls._image_exist(image):
                return ContainerdRuntimeInstaller.pull_image_ctr(
                    image, env=env, verbose=verbose, timeout=pull_timeout)
            color_print.debug('%s already pulled' % image)
            return True
        return super()._pull_image(image, mappings=mappings, env=env,
                                   verbose=verbose, pull_timeout=pull_timeout)

    @classmethod
    def _tag_image(cls, old_name, new_name):
        if cls._current_runtime == 'containerd':
            ContainerdRuntimeInstaller.tag_image_ctr(old_name, new_name)
            return
        return super()._tag_image(old_name, new_name)

    # ---- public API ----

    @classmethod
    def uninstall(cls, verbose=False):
        stdout, stderr = verbose_func.verbose_output(verbose)
        try:
            subprocess.run(
                cls._cmd_kubeadm_reset,
                input='y\n'.encode('utf-8'),
                stdout=stdout,
                stderr=stderr,
                check=False)
            subprocess.run(
                cls._cmd_rm_kube,
                stdout=stdout,
                stderr=stderr,
                check=False)
        except FileNotFoundError:
            pass
        subprocess.run(
            cls.cmd_apt_uninstall + cls._kubernetes_gadgets,
            stdout=stdout,
            stderr=stderr,
            check=False)

    @classmethod
    def install_by_version(cls, gadgets, cni_plugin, pod_network_cidr,
                           taint_master=False, domestic=False, http_proxy='',
                           https_proxy='', no_proxy='', runtime='auto',
                           runtime_version=None, verbose=False):
        """Install Kubernetes with specified version.

        Args:
            gadgets: Kubernetes gadgets (e.g. kubeadm, kubelet).
            cni_plugin: Name of CNI plugin.
            pod_network_cidr: CIDR of pod network.
            taint_master: Taint the master node or not.
            domestic: Pull Kubernetes images from domestic source or not.
            http_proxy: HTTP proxy.
            https_proxy: HTTPS proxy.
            no_proxy: Domains which should be visited without proxy.
            runtime: Container runtime ('docker', 'containerd', or 'auto').
            runtime_version: Version of the container runtime to install.
                - containerd: containerd.io apt version (e.g. '1.6.28'); None → latest.
                - docker + k8s>=1.24: cri-dockerd version (e.g. '0.3.15'); None → default.
            verbose: Verbose or not.
        """
        k8s_version = gadgets[0]['version']
        if runtime == 'auto':
            if version.parse(k8s_version) >= version.parse(config.k8s_containerd_cutoff):
                runtime = 'containerd'
            else:
                runtime = 'docker'
        # image operations always go through docker SDK for the 'docker' runtime
        # (whether using legacy dockershim or cri-dockerd)
        cls._current_runtime = runtime

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
            'runtime': runtime,
            'runtime_version': runtime_version,
        }
        return cls._install_with_context(gadgets, context, verbose=verbose)

    @classmethod
    def _resolve_installed_k8s_version(cls, k8s_version, verbose=False):
        """Return the full patch version of the installed kubelet.

        If k8s_version already contains a patch component (two dots), return it
        unchanged (strip leading 'v').  Otherwise query the installed kubelet binary
        to get the exact version (e.g. '1.33' → '1.33.13').
        """
        k8s_version = k8s_version.lstrip('v')
        if k8s_version.count('.') >= 2:
            return k8s_version
        _, stderr = verbose_func.verbose_output(verbose)
        try:
            res = subprocess.run(
                ['kubelet', '--version'],
                stdout=subprocess.PIPE, stderr=stderr, check=True)
            m = re.search(r'v([\d]+\.[\d]+\.[\d]+)', res.stdout.decode('utf-8'))
            if m:
                return m.group(1)
        except Exception:
            pass
        # Fallback: look up in k8s_stable_versions
        stable = config.k8s_stable_versions.get(k8s_version)
        if stable:
            return stable.lstrip('v')
        return k8s_version

    @classmethod
    def _install_with_context(cls, gadgets, context=None, verbose=False):
        stdout, stderr = verbose_func.verbose_output(verbose)
        runtime = context.get('runtime', 'docker')
        worker_template_mappings = dict()
        worker_template_mappings['domestic'] = context.get('domestic', False)

        cls._pre_configure(runtime=runtime, verbose=verbose)

        k8s_version = gadgets[0]['version']
        runtime_version = context.get('runtime_version')
        needs_cri_dockerd = (
            runtime == 'docker'
            and version.parse(k8s_version) >= version.parse(config.k8s_containerd_cutoff))

        # Install and configure the chosen CRI runtime BEFORE k8s packages
        if runtime == 'containerd':
            color_print.debug('setting up containerd as CRI runtime')
            if not ContainerdRuntimeInstaller.install_and_configure(
                    k8s_version=k8s_version,
                    containerd_version=runtime_version,
                    verbose=verbose):
                color_print.error_and_exit('failed to set up containerd runtime')
        elif needs_cri_dockerd:
            color_print.debug('k8s >= 1.24 + docker runtime: installing cri-dockerd')
            if not CriDockerdInstaller.install(version=runtime_version, verbose=verbose):
                color_print.error_and_exit('failed to install cri-dockerd')

        if not cls._pre_install(k8s_version, worker_template_mappings, verbose=verbose):
            color_print.error_and_exit('failed to finish pre-installation')

        kubernetes_cni_version = cls._get_kubernetes_cni_version(
            'kubelet', gadgets[0]['version'], verbose=verbose)
        if kubernetes_cni_version:
            cls._install_one_gadget_by_version(
                'kubernetes-cni', kubernetes_cni_version, worker_template_mappings, verbose=verbose)

        for gadget in gadgets:
            cls._install_one_gadget_by_version(
                gadget['name'], gadget['version'], worker_template_mappings, verbose=verbose)

        # Resolve the exact installed patch version for image pulling and kubeadm
        # (user may pass only a minor version like '1.33'; actual install may be '1.33.13')
        k8s_version = cls._resolve_installed_k8s_version(k8s_version, verbose=verbose)
        color_print.debug('resolved k8s version: %s' % k8s_version)

        images_base, images_extra = cls._get_k8s_images_list_by_version(k8s_version)
        if not cls._pull_k8s_images(
                k8s_version=k8s_version,
                images_base=images_base,
                images_extra=images_extra,
                domestic=context.get('domestic', False),
                env=context.get('envs'),
                mappings=worker_template_mappings,
                verbose=verbose):
            return False

        if not cls._run_kubeadm(k8s_version, context, mappings=worker_template_mappings, verbose=verbose):
            return False

        cls._config_auth()

        if not context.get('taint_master', None):
            cls._untaint_control_plane(k8s_version, stdout=stdout, stderr=stderr)

        cls._install_cni_plugin(k8s_version, context, worker_template_mappings, verbose=verbose)
        cls._update_k8s_worker_script(worker_template_mappings, context, verbose=verbose)
        return True

    @classmethod
    def _untaint_control_plane(cls, k8s_version, stdout=None, stderr=None):
        """Remove scheduling taint from the control-plane/master node."""
        if version.parse(k8s_version) >= version.parse(config.k8s_containerd_cutoff):
            # k8s >= 1.24 uses control-plane taint
            subprocess.run(
                cls._cmd_enable_schedule_control_plane,
                stdout=stdout, stderr=stderr, check=False)
            # also try old taint name in case both exist during transition
            subprocess.run(
                cls._cmd_enable_schedule_master,
                stdout=stdout, stderr=stderr, check=False)
        else:
            subprocess.run(
                cls._cmd_enable_schedule_master,
                stdout=stdout, stderr=stderr, check=False)

    @classmethod
    def _install_cni_plugin(cls, k8s_version, context, mappings=None, verbose=False):
        CNIPluginInstaller.install_cni_plugin(
            k8s_version, context, mappings=mappings, verbose=verbose)

    @classmethod
    def _config_auth(cls):
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
        temp_cmd.append('--kubernetes-version={k8s_version}'.format(k8s_version=k8s_version))
        temp_cmd.append(cls._kubeadm_common_options)
        if mappings:
            mappings['kubeadm_options'] = cls._kubeadm_common_options
        pod_network_cidr = context.get('pod_network_cidr', None)
        if pod_network_cidr:
            temp_cmd.append('--pod-network-cidr={cidr}'.format(cidr=pod_network_cidr))
        runtime = context.get('runtime', 'docker')
        if runtime == 'containerd':
            temp_cmd.append('--cri-socket=%s' % config.containerd_cri_socket)
        elif runtime == 'docker' and version.parse(k8s_version) >= version.parse(config.k8s_containerd_cutoff):
            # dockershim was removed in 1.24; cri-dockerd provides the shim socket
            temp_cmd.append('--cri-socket=%s' % config.cri_dockerd_cri_socket)
        try:
            subprocess.run(
                temp_cmd, stdout=stdout, stderr=stderr, check=True,
                env=context.get('envs', None))
            return True
        except subprocess.CalledProcessError:
            color_print.error('failed to run kubeadm')
            return False

    @classmethod
    def _pull_k8s_images(cls, k8s_version, images_base,
                         images_extra, domestic=False, env=None,
                         mappings=None, verbose=False):
        if domestic:
            cls._warn_docker_pull_network(env)
            if version.parse(k8s_version) <= version.parse(config.k8s_stable_versions['1.9']):
                ori_prefix = config.k8s_images_prefix_official_9
            elif version.parse(k8s_version) >= version.parse(config.k8s_stable_versions['1.22']):
                ori_prefix = config.k8s_images_prefix_official_22
            else:
                ori_prefix = config.k8s_images_prefix_official
            if not cls._pull_domestic_images(
                    images_base, ori_prefix=ori_prefix,
                    mappings=mappings, env=env, verbose=verbose):
                return False
            if not cls._pull_domestic_images(
                    images_extra, ori_prefix=ori_prefix,
                    mappings=mappings, env=env, verbose=verbose):
                return False
        else:
            if not cls._pull_images(images_extra, mappings=mappings, env=env, verbose=verbose):
                return False
            if not cls._pull_images(images_base, mappings=mappings, env=env, verbose=verbose):
                return False
        return True

    @classmethod
    def _get_k8s_images_list(cls, k8s_version, images_base_version):
        images_base = [':v'.join((image, k8s_version)) for image in images_base_version]
        major_minor = re.search(r'^([\d]+\.[\d]+)', k8s_version).group(1)
        extra = config.k8s_images_extra.get(major_minor)
        if extra is None:
            color_print.warning('no image list for k8s %s, using latest known' % major_minor)
            # fallback: use the highest version defined
            latest_key = sorted(
                config.k8s_images_extra.keys(),
                key=lambda x: version.parse(x))[-1]
            extra = config.k8s_images_extra[latest_key]
        return images_base, extra

    @classmethod
    def _get_k8s_images_list_by_version(cls, k8s_version):
        if version.parse(k8s_version) >= version.parse(config.k8s_stable_versions['1.22']):
            return cls._get_k8s_images_list(k8s_version, config.k8s_images_base_from_22)
        elif version.parse(k8s_version) > version.parse(
                config.k8s_stable_versions['1.11']) and version.parse(
                k8s_version) < version.parse(config.k8s_stable_versions['1.22']):
            return cls._get_k8s_images_list(k8s_version, config.k8s_images_base_from_12)
        elif (version.parse('1.10') <= version.parse(k8s_version)
              <= version.parse(config.k8s_stable_versions['1.11'])):
            return cls._get_k8s_images_list(k8s_version, config.k8s_images_base_10_to_11)
        else:
            return cls._get_k8s_images_list(k8s_version, config.k8s_images_base_9)

    @classmethod
    def _get_kubernetes_cni_version(cls, name, k8s_cni_version, verbose=False):
        _, stderr = verbose_func.verbose_output(verbose)
        kubelet_complete_version = cls._get_apt_complete_version(
            name, k8s_cni_version, verbose=verbose)
        if not kubelet_complete_version:
            return None
        color_print.debug('resolving kubernetes-cni version for kubelet %s' % kubelet_complete_version)
        res = subprocess.run(
            ['apt', 'show', '{name}={version}'.format(
                name=name, version=kubelet_complete_version)],
            stdout=subprocess.PIPE, stderr=stderr, check=False)
        if res.returncode != 0:
            return None
        depends = None
        for entry in res.stdout.decode('utf-8').split('\n'):
            if entry.startswith('Depends:'):
                depends = entry
                break
        temp_version = None
        if depends:
            for depend in depends.split(','):
                if 'kubernetes-cni' in depend:
                    temp_version = depend.split('(')[-1].split(')')[0].split(' ')[-1]
                    break
        if temp_version:
            return cls._get_apt_complete_version('kubernetes-cni', temp_version, verbose=verbose)
        return None

    @classmethod
    def _pre_configure(cls, runtime='docker', verbose=False):
        color_print.debug('pre-configuring')
        stdout, stderr = verbose_func.verbose_output(verbose)
        subprocess.run(cls._cmd_modprobe, stdout=stdout, stderr=stderr, check=False)
        with open('/etc/sysctl.d/k8s.conf', 'a') as f:
            f.write('net.bridge.bridge-nf-call-ip6tables = 1\n')
            f.write('net.bridge.bridge-nf-call-iptables = 1\n')
            if runtime == 'containerd':
                f.write('net.ipv4.ip_forward = 1\n')
        subprocess.run(['sysctl', '--system'], stdout=stdout, stderr=stderr, check=False)
        subprocess.run(cls._cmd_swapoff, stdout=stdout, stderr=stderr, check=True)
        subprocess.run(cls._cmd_swapoff_fstab, stdout=stdout, stderr=stderr, check=True)
        subprocess.run(cls._cmd_swapoff_fstab_img, stdout=stdout, stderr=stderr, check=True)

    @classmethod
    def _pre_install(cls, k8s_version, mappings=None, verbose=False):
        color_print.debug('pre-installing')
        stdout, stderr = verbose_func.verbose_output(verbose)
        DockerInstaller._comment_source(verbose=verbose)
        if not cls._apt_update(verbose=verbose):
            return False
        try:
            subprocess.run(
                cls.cmd_apt_install + cls._kubernetes_requirements,
                stdout=stdout, stderr=stderr, check=True)
        except subprocess.CalledProcessError:
            return False

        # Choose apt repo format based on k8s version
        if version.parse(k8s_version) >= version.parse(config.k8s_new_apt_repo_cutoff):
            gpg_url, repo_entry = cls._add_k8s_apt_repository_new(k8s_version, verbose=verbose)
        else:
            gpg_url, repo_entry = cls._add_k8s_apt_repository(verbose=verbose)

        if not gpg_url:
            return False
        if mappings is not None:
            mappings['gpg_url'] = gpg_url
            mappings['repo_entry'] = repo_entry
            mappings['new_repo_format'] = version.parse(k8s_version) >= version.parse(
                config.k8s_new_apt_repo_cutoff)

        if not cls._apt_update(verbose=verbose):
            return False
        return True

    @classmethod
    def _add_k8s_apt_repository_new(cls, k8s_version, verbose=False):
        """Add k8s apt repo using new pkgs.k8s.io signed-by format (k8s >= 1.24)."""
        minor = '.'.join(k8s_version.split('.')[:2])
        candidates = [
            (tpl_gpg.format(minor=minor), tpl_entry.format(minor=minor))
            for tpl_gpg, tpl_entry in config.k8s_new_apt_repo_candidates
        ]
        reachable = [
            (gpg, entry) for gpg, entry in candidates
            if cls._probe_url(gpg, verbose=verbose)
        ]
        for gpg_url, repo_entry in (reachable or candidates):
            if cls._add_apt_repository_signed_by(
                    gpg_url=gpg_url,
                    keyring_file=config.k8s_new_apt_keyring_file,
                    repo_entry=repo_entry,
                    sources_file='/etc/apt/sources.list.d/kubernetes.list',
                    verbose=verbose):
                color_print.debug('using k8s apt repository (new format) %s' % repo_entry)
                return gpg_url, repo_entry
        return None, None

    @classmethod
    def _update_k8s_worker_script(cls, mappings, context, verbose=False):
        color_print.debug('generating kubernetes worker script')
        runtime = context.get('runtime', 'docker')
        new_repo = mappings.pop('new_repo_format', False)

        final_mappings = {
            'gpg_url': mappings.pop('gpg_url'),
            'repo_entry': mappings.pop('repo_entry'),
            'kubernetes_cni_version': mappings.pop('kubernetes-cni', ''),
            'kubelet_version': mappings.pop('kubelet', ''),
            'kubeadm_version': mappings.pop('kubeadm', ''),
        }
        domestic = mappings.pop('domestic')

        def _ctr_pull(img):
            return '\nctr -n k8s.io images pull {image}\n'.format(image=img)

        def _ctr_tag(old, new):
            return '\nctr -n k8s.io images tag {old} {new}\nctr -n k8s.io images rm {old}\n'.format(
                old=old, new=new)

        cmds_pull_images = ''
        if domestic:
            for key, value in mappings.items():
                if 'pause' in key or 'proxy' in key or context.get('cni_plugin') in key:
                    if runtime == 'containerd':
                        cmds_pull_images += _ctr_pull(key)
                        cmds_pull_images += _ctr_tag(key, value)
                    else:
                        cmds_pull_images += '\ndocker pull {image}\n'.format(image=key)
                        cmds_pull_images += '\ndocker tag {old} {new}\n'.format(old=key, new=value)
        else:
            for key, value in mappings.items():
                if value is None:
                    if 'pause' in key or 'proxy' in key or context.get('cni_plugin') in key:
                        if runtime == 'containerd':
                            cmds_pull_images += _ctr_pull(key)
                        else:
                            cmds_pull_images += '\ndocker pull {image}\n'.format(image=key)

        final_mappings['cmds_pull_images'] = cmds_pull_images
        final_mappings['master_ip'] = cls.get_host_ip()
        token, ca_cert_hash = cls._get_kubeadm_token_and_hash(verbose=verbose)
        final_mappings['token'] = token
        final_mappings['ca_cert_hash'] = ca_cert_hash
        final_mappings['kubeadm_options'] = mappings.get('kubeadm_options', '')

        if runtime == 'containerd' and new_repo:
            template_path = config.k8s_worker_template_containerd
        elif runtime == 'containerd' and not new_repo:
            template_path = config.k8s_worker_template_containerd_old_repo
        elif runtime == 'docker' and new_repo:
            # k8s >= 1.24 + docker: workers also need cri-dockerd
            cri_dockerd_ver = context.get('runtime_version') or config.cri_dockerd_default_version
            final_mappings['cri_dockerd_download_cmd'] = CriDockerdInstaller.build_download_cmds(
                cri_dockerd_ver, config._ubuntu_release)
            template_path = config.k8s_worker_template_cridockerd
        else:
            template_path = config.k8s_worker_template

        with open(template_path, 'r') as fr:
            with open(config.k8s_worker_script, 'w') as fw:
                data = Template(fr.read())
                fw.write(data.safe_substitute(final_mappings))
        color_print.debug('kubernetes worker script generated at %s' % config.k8s_worker_script)

    @classmethod
    def _get_kubeadm_token_and_hash(cls, verbose=False):
        _, stderr = verbose_func.verbose_output(verbose)
        res = subprocess.run(
            'kubeadm token list'.split(),
            stdout=subprocess.PIPE, stderr=stderr, check=True)
        token = re.search(r'([a-z0-9]{6}\.[a-z0-9]{16})', res.stdout.decode('utf-8')).group(1)
        res = subprocess.run(
            'bash {script}'.format(script=config.k8s_hash_generator).split(),
            stdout=subprocess.PIPE, stderr=stderr, check=True)
        ca_cert_hash = res.stdout.decode('utf-8').strip()
        return token, ca_cert_hash


if __name__ == "__main__":
    KubernetesInstaller.uninstall()
    import sys
    if len(sys.argv) > 1:
        test_version = sys.argv[1]
    else:
        test_version = '1.28.4'
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
