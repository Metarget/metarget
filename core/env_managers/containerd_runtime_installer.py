"""
Containerd Runtime Installer for Kubernetes CRI
Configures containerd.io as the CRI runtime for kubeadm-based K8s clusters.
"""

import os
import re
import subprocess

import utils.color_print as color_print
import utils.verbose as verbose_func
from core.env_managers.installer import Installer


class ContainerdRuntimeInstaller(Installer):
    _ctr_ns = 'k8s.io'
    _containerd_config_dir = '/etc/containerd'
    _containerd_config_file = '/etc/containerd/config.toml'
    _modules_load_file = '/etc/modules-load.d/containerd.conf'
    _sysctl_file = '/etc/sysctl.d/99-kubernetes-cri.conf'

    # pause image per k8s minor version (containerd sandbox_image config)
    # derived from kubeadm config images list for each minor version
    _pause_images = {
        '1.9':  'gcr.io/google_containers/pause-amd64:3.0',
        '1.10': 'k8s.gcr.io/pause-amd64:3.1',
        '1.11': 'k8s.gcr.io/pause-amd64:3.1',
        '1.12': 'k8s.gcr.io/pause:3.1',
        '1.13': 'k8s.gcr.io/pause:3.1',
        '1.14': 'k8s.gcr.io/pause:3.1',
        '1.15': 'k8s.gcr.io/pause:3.1',
        '1.16': 'k8s.gcr.io/pause:3.1',
        '1.17': 'k8s.gcr.io/pause:3.1',
        '1.18': 'k8s.gcr.io/pause:3.2',
        '1.19': 'k8s.gcr.io/pause:3.2',
        '1.20': 'k8s.gcr.io/pause:3.2',
        '1.21': 'k8s.gcr.io/pause:3.4.1',
        '1.22': 'registry.k8s.io/pause:3.5',
        '1.23': 'registry.k8s.io/pause:3.6',
        '1.24': 'registry.k8s.io/pause:3.7',
        '1.25': 'registry.k8s.io/pause:3.8',
        '1.26': 'registry.k8s.io/pause:3.9',
        '1.27': 'registry.k8s.io/pause:3.9',
        '1.28': 'registry.k8s.io/pause:3.9',
        '1.29': 'registry.k8s.io/pause:3.9',
        '1.30': 'registry.k8s.io/pause:3.9',
        '1.31': 'registry.k8s.io/pause:3.10',
        '1.32': 'registry.k8s.io/pause:3.10',
    }

    @classmethod
    def install_and_configure(cls, k8s_version=None, containerd_version=None, verbose=False):
        """Install containerd.io and configure it as a K8s CRI.

        Args:
            k8s_version: K8s version string used to set the correct sandbox_image.
            containerd_version: Pin a specific containerd.io apt version (e.g. '1.6.28').
                                None installs the latest available from the apt repo.
            verbose: Print subprocess output.
        """
        from core.env_managers.docker_installer import DockerInstaller
        if not DockerInstaller._pre_install(verbose=verbose):
            color_print.error('failed to set up docker apt repo for containerd.io')
            return False
        stdout, stderr = verbose_func.verbose_output(verbose)

        if containerd_version:
            # get the complete apt package version string (e.g. '1.6.28-1')
            from core.env_managers.installer import Installer as _Inst
            complete_ver = _Inst._get_apt_complete_version('containerd.io', containerd_version, verbose=verbose)
            pkg_spec = 'containerd.io=%s' % complete_ver if complete_ver else 'containerd.io'
        else:
            pkg_spec = 'containerd.io'

        color_print.debug('installing %s' % pkg_spec)
        try:
            subprocess.run(
                cls.cmd_apt_install + [pkg_spec],
                stdout=stdout, stderr=stderr, check=True)
        except subprocess.CalledProcessError:
            color_print.error('failed to install containerd.io')
            return False
        return cls.configure_for_k8s(k8s_version=k8s_version, verbose=verbose)

    @classmethod
    def configure_for_k8s(cls, k8s_version=None, verbose=False):
        """Configure containerd with SystemdCgroup=true for K8s CRI."""
        stdout, stderr = verbose_func.verbose_output(verbose)
        color_print.debug('configuring containerd for kubernetes CRI')

        cls._setup_kernel_modules(verbose=verbose)

        os.makedirs(cls._containerd_config_dir, exist_ok=True)
        try:
            res = subprocess.run(
                ['containerd', 'config', 'default'],
                stdout=subprocess.PIPE, stderr=stderr, check=True)
            cfg = res.stdout.decode('utf-8')
        except subprocess.CalledProcessError:
            color_print.error('failed to generate containerd default config')
            return False

        cfg = cfg.replace('SystemdCgroup = false', 'SystemdCgroup = true')

        if k8s_version:
            pause_img = cls._get_pause_image(k8s_version)
            if pause_img:
                cfg = re.sub(
                    r'sandbox_image\s*=\s*"[^"]*"',
                    'sandbox_image = "%s"' % pause_img,
                    cfg)

        with open(cls._containerd_config_file, 'w') as f:
            f.write(cfg)

        try:
            subprocess.run(['systemctl', 'daemon-reload'], stdout=stdout, stderr=stderr, check=True)
            subprocess.run(['systemctl', 'enable', 'containerd'], stdout=stdout, stderr=stderr, check=True)
            subprocess.run(['systemctl', 'restart', 'containerd'], stdout=stdout, stderr=stderr, check=True)
            return True
        except subprocess.CalledProcessError:
            color_print.error('failed to restart containerd')
            return False

    @classmethod
    def _setup_kernel_modules(cls, verbose=False):
        stdout, stderr = verbose_func.verbose_output(verbose)
        with open(cls._modules_load_file, 'w') as f:
            f.write('overlay\nbr_netfilter\n')
        for mod in ('overlay', 'br_netfilter'):
            subprocess.run(['modprobe', mod], stdout=stdout, stderr=stderr, check=False)
        with open(cls._sysctl_file, 'w') as f:
            f.write('net.bridge.bridge-nf-call-iptables  = 1\n')
            f.write('net.bridge.bridge-nf-call-ip6tables = 1\n')
            f.write('net.ipv4.ip_forward                 = 1\n')
        subprocess.run(['sysctl', '--system'], stdout=stdout, stderr=stderr, check=False)

    @classmethod
    def _get_pause_image(cls, k8s_version):
        minor = '.'.join(k8s_version.split('.')[:2])
        if minor in cls._pause_images:
            return cls._pause_images[minor]
        from packaging import version as pkg_version
        # for unknown future versions, use the latest known entry
        known = sorted(cls._pause_images.keys(), key=lambda x: pkg_version.parse(x))
        return cls._pause_images[known[-1]]

    # ---- image operations via ctr -n k8s.io ----

    @classmethod
    def image_exist_ctr(cls, image, verbose=False):
        _, stderr = verbose_func.verbose_output(verbose)
        try:
            res = subprocess.run(
                ['ctr', '-n', cls._ctr_ns, 'images', 'ls', '-q'],
                stdout=subprocess.PIPE, stderr=stderr, check=True)
            return image in res.stdout.decode('utf-8')
        except subprocess.CalledProcessError:
            return False

    @classmethod
    def pull_image_ctr(cls, image, env=None, verbose=False, timeout=300):
        stdout, stderr = verbose_func.verbose_output(verbose)
        color_print.debug('pulling %s via ctr' % image)
        try:
            subprocess.run(
                ['timeout', str(timeout), 'ctr', '-n', cls._ctr_ns, 'images', 'pull', image],
                stdout=stdout, stderr=stderr, check=True,
                env=env or os.environ)
            return True
        except subprocess.CalledProcessError:
            color_print.error('ctr pull failed for %s' % image)
            return False

    @classmethod
    def tag_image_ctr(cls, old_name, new_name, verbose=False):
        stdout, stderr = verbose_func.verbose_output(verbose)
        try:
            subprocess.run(
                ['ctr', '-n', cls._ctr_ns, 'images', 'tag', old_name, new_name],
                stdout=stdout, stderr=stderr, check=True)
            subprocess.run(
                ['ctr', '-n', cls._ctr_ns, 'images', 'rm', old_name],
                stdout=stdout, stderr=stderr, check=False)
            return True
        except subprocess.CalledProcessError:
            return False
