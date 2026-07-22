"""
cri-dockerd Installer
Mirantis's CRI shim that lets Docker Engine be the Kubernetes CRI on k8s >= 1.24.
https://github.com/Mirantis/cri-dockerd
"""

import json
import os
import subprocess

import config
import utils.color_print as color_print
import utils.verbose as verbose_func
from core.env_managers.installer import Installer

# GitHub proxy services for environments where github.com is slow or blocked
_PROXY_URLS = [
    'https://github.moeyy.xyz',
    'https://gh-proxy.com',
    'https://ghproxy.net',
]

# cri-dockerd only publishes bionic/focal/jammy debs; newer Ubuntu releases can use jammy.
_UBUNTU_CODENAME_FALLBACKS = {
    'noble': ['jammy', 'focal'],
    'oracular': ['jammy', 'focal'],
    'plucky': ['jammy', 'focal'],
}


class CriDockerdInstaller(Installer):
    _binary = '/usr/bin/cri-dockerd'
    _service_name = 'cri-docker'

    @classmethod
    def installed(cls):
        return os.path.isfile(cls._binary)

    @classmethod
    def install(cls, version=None, verbose=False):
        """Download and install cri-dockerd .deb package, enable systemd services.

        Args:
            version: cri-dockerd version string (e.g. '0.3.15').  None → default.
            verbose: Print subprocess output.
        Returns:
            True on success, False on failure.
        """
        if not version:
            version = config.cri_dockerd_default_version
        codename = config._ubuntu_release
        arch = 'amd64'
        color_print.debug('installing cri-dockerd %s' % version)

        deb_path = '/tmp/cri-dockerd.deb'
        if not cls._download_deb(version, codename, arch, deb_path, verbose=verbose):
            color_print.error('failed to download cri-dockerd %s' % version)
            return False

        stdout, stderr = verbose_func.verbose_output(verbose)
        try:
            subprocess.run(['dpkg', '-i', deb_path], stdout=stdout, stderr=stderr, check=True)
        except subprocess.CalledProcessError:
            color_print.error('failed to install cri-dockerd deb package')
            return False

        # enable and start cri-docker.service + cri-docker.socket
        for unit in ('cri-docker.service', 'cri-docker.socket'):
            try:
                subprocess.run(
                    ['systemctl', 'enable', '--now', unit],
                    stdout=stdout, stderr=stderr, check=True)
            except subprocess.CalledProcessError:
                color_print.error('failed to enable %s' % unit)
                return False

        color_print.debug('cri-dockerd %s installed and running' % version)
        return True

    @classmethod
    def _effective_codename(cls, codename):
        """Return ordered list of codenames to try (native first, then fallbacks)."""
        return [codename] + _UBUNTU_CODENAME_FALLBACKS.get(codename, [])

    @classmethod
    def _download_deb(cls, version, codename, arch, dest, verbose=False):
        """Attempt to download the .deb from GitHub (direct + proxy fallback).

        If no build exists for the current Ubuntu codename, tries compatible older
        codenames defined in _UBUNTU_CODENAME_FALLBACKS (e.g. noble → jammy).
        """
        stdout, stderr = verbose_func.verbose_output(verbose)
        codenames = cls._effective_codename(codename)

        # Query GitHub API to find the best available asset across codename candidates
        api_url = (
            'https://api.github.com/repos/Mirantis/cri-dockerd/releases/tags/v%s' % version)
        api_asset_url, resolved_codename = cls._query_github_api(api_url, codenames, arch)
        if resolved_codename and resolved_codename != codename:
            color_print.debug(
                'no cri-dockerd build for %s, using %s package' % (codename, resolved_codename))

        candidates = []
        # API-resolved URL (most authoritative) — try via proxies then direct
        if api_asset_url:
            for proxy in _PROXY_URLS:
                candidates.append('%s/%s' % (proxy, api_asset_url))
            candidates.append(api_asset_url)

        # Fallback: construct direct URLs for each codename candidate
        for cn in codenames:
            direct_url = (
                'https://github.com/Mirantis/cri-dockerd/releases/download/v%s/%s'
                % (version, cls._deb_filename(version, cn, arch)))
            for proxy in _PROXY_URLS:
                candidates.append('%s/%s' % (proxy, direct_url))
            candidates.append(direct_url)

        for url in candidates:
            color_print.debug('downloading cri-dockerd from %s' % url)
            try:
                subprocess.run(
                    ['curl', '-fsSL', '--connect-timeout', '15', '-o', dest, url],
                    stdout=stdout, stderr=stderr, check=True)
                if os.path.getsize(dest) > 1024:
                    return True
            except (subprocess.CalledProcessError, OSError):
                continue
        return False

    @classmethod
    def _query_github_api(cls, api_url, codenames, arch):
        """Return (browser_download_url, matched_codename) for the best matching deb asset.

        Tries codenames in order; returns (None, None) if API is unreachable or no match.
        """
        try:
            res = subprocess.run(
                ['curl', '-fsSL', '--connect-timeout', '5', api_url],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            assets = json.loads(res.stdout).get('assets', [])
            for codename in codenames:
                for asset in assets:
                    name = asset.get('name', '')
                    if ('ubuntu-%s' % codename) in name and arch in name and name.endswith('.deb'):
                        return asset['browser_download_url'], codename
        except Exception:
            pass
        return None, None

    @classmethod
    def _deb_filename(cls, version, codename, arch):
        """Build the expected .deb filename from version, codename, and arch.

        The Mirantis packaging convention appends '.3-0' after the semver.
        e.g. v0.3.15 → cri-dockerd_0.3.15.3-0.ubuntu-jammy_amd64.deb
        """
        return 'cri-dockerd_%s.3-0.ubuntu-%s_%s.deb' % (version, codename, arch)

    @classmethod
    def build_download_cmds(cls, version, codename, arch='amd64'):
        """Return a bash snippet that downloads the cri-dockerd .deb with proxy fallback.

        Includes all codename fallback URLs so the worker script works even on
        Ubuntu releases that have no native cri-dockerd build.
        Used when generating the k8s worker join script.
        """
        codenames = cls._effective_codename(codename)
        urls = []
        for cn in codenames:
            direct_url = (
                'https://github.com/Mirantis/cri-dockerd/releases/download/v%s/%s'
                % (version, cls._deb_filename(version, cn, arch)))
            for proxy in _PROXY_URLS:
                urls.append('%s/%s' % (proxy, direct_url))
            urls.append(direct_url)
        lines = ['curl -fsSL --connect-timeout 15 -o /tmp/cri-dockerd.deb %s' % u for u in urls]
        return ' || \\\n'.join(lines)
