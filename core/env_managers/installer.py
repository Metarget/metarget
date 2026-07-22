"""
Basic Installer
- supplies some common useful functions
- specific installers should inherit this class to reuse common functions if necessary
"""

import copy
import os
import shutil
import subprocess
import docker
import socket
import requests
from tqdm import tqdm

import config
import utils.system as system_func
import utils.verbose as verbose_func
import utils.color_print as color_print
import utils.docker_env as docker_env


class Installer(object):
    _docker_pull_hint_shown = False
    cmd_apt_uninstall = "apt-get -y remove".split()
    cmd_apt_update = "apt-get update".split()
    cmd_apt_install = 'apt-get -y --allow-downgrades install'.split()
    cmd_apt_madison = 'apt-cache madison'.split()
    cmd_apt_search = 'apt-cache search'.split()
    cmd_apt_add_key = 'apt-key add -'.split()
    try:
        docker_client = docker.from_env()
    except BaseException:
        pass

    @classmethod
    def _get_apt_complete_version(cls, name, version, verbose=False):
        _, stderr = verbose_func.verbose_output(verbose)
        temp_cmd = copy.copy(cls.cmd_apt_madison)
        temp_cmd.append(name)
        try:
            res = subprocess.run(
                temp_cmd,
                stdout=subprocess.PIPE,
                stderr=stderr,
                check=True)
        except subprocess.CalledProcessError:
            return None
        entries = res.stdout.decode('utf-8').split('\n')
        complete_version = None
        entries.pop(-1)  # remove ''
        version_candidates = [entry.split('|')[1].strip() for entry in entries]
        version_candidates.sort()
        for candidate in version_candidates:
            if version in candidate:
                complete_version = candidate
                break
        return complete_version

    @classmethod
    def _get_apt_complete_package(cls, name, keywords, verbose=False):
        _, stderr = verbose_func.verbose_output(verbose)
        temp_cmd = copy.copy(cls.cmd_apt_search)
        temp_cmd.append(name)
        try:
            res = subprocess.run(
                temp_cmd,
                stdout=subprocess.PIPE,
                stderr=stderr,
                check=True)
        except subprocess.CalledProcessError:
            return None
        entries = res.stdout.decode('utf-8').split('\n')
        for entry in entries:
            for keyword in keywords:
                if keyword not in entry:
                    break
            else:
                return entry.split()[0]
        return None

    @classmethod
    def _install_one_gadget_by_version(
            cls, name, version, mappings=None, verbose=False):
        stdout, stderr = verbose_func.verbose_output(verbose)
        # get complete version, e.g. 18.03.1~ce-0~ubuntu
        complete_version = cls._get_apt_complete_version(
            name, version, verbose=verbose)
        if complete_version:
            color_print.debug(
                'installing {gadget} with {version} version'.format(
                    gadget=name, version=complete_version))
            # install with the specified version
            temp_cmd = copy.copy(cls.cmd_apt_install)
            temp_cmd.append(
                '{name}={version}'.format(
                    name=name,
                    version=complete_version))
            try:
                subprocess.run(
                    temp_cmd,
                    stderr=stderr,
                    stdout=stdout,
                    check=True)
            except subprocess.CalledProcessError:
                return False
            if mappings:
                mappings[name] = complete_version
            return True
        color_print.warning('no candidate version for %s' % name)
        return False

    @classmethod
    def _apt_update(cls, verbose=False):
        stdout, stderr = verbose_func.verbose_output(verbose)
        try:
            subprocess.run(
                cls.cmd_apt_update,
                stdout=stdout,
                stderr=stderr,
                check=True)
            return True
        except subprocess.CalledProcessError:
            return False

    @classmethod
    def _probe_url(cls, url, timeout=10, verbose=False):
        _, stderr = verbose_func.verbose_output(verbose)
        try:
            subprocess.run(
                ['curl', '-fsSL', '--connect-timeout', str(timeout),
                 '--max-time', str(timeout), '-o', '/dev/null', url],
                stdout=subprocess.DEVNULL,
                stderr=stderr,
                check=True)
            return True
        except subprocess.CalledProcessError:
            return False

    @classmethod
    def _domestic_mirror_image(cls, image, ori_prefix, new_prefix):
        temp_image = image.replace(ori_prefix, new_prefix)
        if 'coredns/coredns:v' in temp_image:
            temp_image = temp_image.replace('coredns/coredns:v', 'coredns:')
        return temp_image

    @classmethod
    def _build_k8s_domestic_mirror_candidates(cls, image, ori_prefix):
        """Accel prefixes first: curl may reach a registry while docker cannot."""
        candidates = []
        seen = set()
        for accel in config.k8s_images_accel_prefix_candidates:
            mirrored = accel + image
            if mirrored not in seen:
                seen.add(mirrored)
                candidates.append(mirrored)
        for prefix in config.k8s_images_prefix_candidates:
            mirrored = cls._domestic_mirror_image(image, ori_prefix, prefix)
            if mirrored not in seen:
                seen.add(mirrored)
                candidates.append(mirrored)
        return candidates

    @classmethod
    def _add_k8s_apt_repository(cls, verbose=False):
        reachable = [
            (gpg_url, repo_entry)
            for gpg_url, repo_entry in config.k8s_apt_repo_candidates
            if cls._probe_url(gpg_url, verbose=verbose)]
        candidates = reachable or list(config.k8s_apt_repo_candidates)
        for gpg_url, repo_entry in candidates:
            if cls._add_apt_repository(
                    gpg_url=gpg_url, repo_entry=repo_entry, verbose=verbose):
                color_print.debug(
                    'using k8s apt repository %s' % repo_entry)
                return gpg_url, repo_entry
        return None, None

    @classmethod
    def _add_apt_repository(cls, repo_entry, gpg_url=None, verbose=False):
        stdout, stderr = verbose_func.verbose_output(verbose)
        color_print.debug('adding apt repository %s' % repo_entry)
        try:
            if gpg_url:
                #eg:curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
                cmd_curl_gpg = 'curl -fsSL {gpg_url}'.format(
                    gpg_url=gpg_url).split()
                res = subprocess.run(
                    cmd_curl_gpg,
                    stdout=subprocess.PIPE,
                    stderr=stderr,
                    check=True)
                subprocess.run(
                    cls.cmd_apt_add_key,
                    input=res.stdout,
                    stdout=stdout,
                    stderr=stderr,
                    check=True)

            # add apt repository
            cmd_apt_add_repository = 'add-apt-repository\n' \
                                     '{repo_entry}'.format(
                                         repo_entry=repo_entry).split('\n')
            subprocess.run(
                cmd_apt_add_repository,
                stdout=stdout,
                stderr=stderr,
                check=True)
            return True
        except subprocess.CalledProcessError:
            return False

    @classmethod
    def _add_apt_repository_signed_by(cls, gpg_url, keyring_file, repo_entry,
                                      sources_file, verbose=False):
        """Add apt repository using gpg --dearmor + signed-by (new pkgs.k8s.io format)."""
        stdout, stderr = verbose_func.verbose_output(verbose)
        color_print.debug('adding signed-by apt repository %s' % repo_entry)
        try:
            os.makedirs(os.path.dirname(keyring_file), exist_ok=True)
            res = subprocess.run(
                ['curl', '-fsSL', gpg_url],
                stdout=subprocess.PIPE, stderr=stderr, check=True)
            subprocess.run(
                ['gpg', '--yes', '--dearmor', '-o', keyring_file],
                input=res.stdout, stdout=stdout, stderr=stderr, check=True)
            with open(sources_file, 'w') as f:
                f.write(repo_entry + '\n')
            return True
        except subprocess.CalledProcessError:
            return False

    @classmethod
    def _pull_images(cls, images, mappings=None, env=None, verbose=False):
        for image in images:
            if not cls._pull_image(image, mappings, env=env, verbose=verbose):
                return False
        return True

    @classmethod
    def _warn_docker_pull_network(cls, env=None):
        if cls._docker_pull_hint_shown:
            return
        hint = docker_env.docker_daemon_proxy_hint()
        if hint:
            color_print.warning(hint)
        if not docker_env.user_env_has_proxy(env) and not hint:
            color_print.debug(
                'tip: if docker pull times out, check systemd proxy for docker')
        cls._docker_pull_hint_shown = True

    @classmethod
    def _pull_image_skopeo(cls, image, env=None, verbose=False):
        if not shutil.which('skopeo'):
            return False
        stdout, stderr = verbose_func.verbose_output(verbose)
        skopeo_env = docker_env.registry_pull_env(env)
        repo, tag = image.rsplit(':', 1)
        try:
            subprocess.run(
                ['skopeo', 'copy', '--retry-times', '3',
                 'docker://' + image,
                 'docker-daemon:' + repo + ':' + tag],
                stdout=stdout,
                stderr=stderr,
                check=True,
                env=skopeo_env)
            return True
        except subprocess.CalledProcessError:
            return False

    @classmethod
    def _pull_image(cls, image, mappings=None, env=None, verbose=False,
                    pull_timeout=300):
        stdout, stderr = verbose_func.verbose_output(verbose)
        if mappings is not None:
            mappings[image] = None
        if not cls._image_exist(image):
            color_print.debug('pulling %s' % image)
            temp_cmd = ['timeout', str(pull_timeout), 'docker', 'pull', image]
            try:
                subprocess.run(
                    temp_cmd,
                    stdout=stdout,
                    stderr=stderr,
                    check=True,
                    env=env or os.environ)
                return True
            except subprocess.CalledProcessError:
                color_print.debug(
                    'docker pull failed for %s, trying skopeo' % image)
                if cls._pull_image_skopeo(image, env=env, verbose=verbose):
                    return True
                cls._warn_docker_pull_network(env)
                return False
        else:
            color_print.debug('%s already pulled' % image)
            return True

    @classmethod
    def _pull_domestic_images(cls, images, ori_prefix,
                              mappings=None, env=None, verbose=False):
        for image in images:
            if not cls._pull_domestic_image(
                    image, ori_prefix,
                    mappings=mappings, env=env, verbose=verbose):
                return False
        return True

    @classmethod
    def _pull_domestic_image(cls, image, ori_prefix,
                             prefix_order=None, mappings=None, env=None,
                             verbose=False, fallback_official=True):
        if cls._image_exist(image):
            color_print.debug('%s already pulled' % image)
            return True
        if prefix_order is None:
            mirror_order = cls._build_k8s_domestic_mirror_candidates(
                image, ori_prefix)
        else:
            mirror_order = []
            for new_prefix in prefix_order:
                mirror_order.append(
                    cls._domestic_mirror_image(image, ori_prefix, new_prefix))
        for temp_image in mirror_order:
            color_print.debug(
                'pulling %s via %s' % (image, temp_image))
            if mappings is not None:
                mappings[temp_image] = image
            if cls._pull_image(temp_image, env=env, verbose=verbose):
                cls._tag_image(temp_image, image)
                return True
        if fallback_official:
            color_print.debug(
                'domestic mirrors failed for %s, trying official registry' %
                image)
            if cls._pull_image(image, env=env, verbose=verbose):
                return True
        cls._warn_docker_pull_network(env)
        color_print.error('failed to pull %s' % image)
        return False

    @classmethod
    def _tag_images(cls, old_names, new_names):
        for old_name, new_name in zip(old_names, new_names):
            cls._tag_image(old_name, new_name)

    @classmethod
    def _tag_image(cls, old_name, new_name):
        try:
            image = cls.docker_client.images.get(old_name)
            repo = new_name.split(':')[0]
            tag = new_name.split(':')[1]
            image.tag(repo, tag=tag)
            cls.docker_client.images.remove(image=old_name)
        except docker.errors.ImageNotFound:
            return

    @classmethod
    def _images_exist(cls, images):
        for image in images:
            if not cls._image_exist(image):
                return False
        return True

    @classmethod
    def _image_exist(cls, image):
        try:
            cls.docker_client.images.get(image)
        except docker.errors.ImageNotFound:
            return False
        return True

    @classmethod
    def _create_k8s_resources(cls, desc_file, verbose=False):
        stdout, stderr = verbose_func.verbose_output(verbose)
        temp_cmd = "kubectl create -f".split()
        temp_cmd.append(desc_file)
        try:
            subprocess.run(temp_cmd, stdout=stdout, stderr=stderr, check=True)
        except subprocess.CalledProcessError:
            raise

    @classmethod
    def _pull_quay_image(cls, image, domestic=False,
                         mappings=None, verbose=False):
        if domestic:
            cls._pull_domestic_image(
                image,
                ori_prefix=config.quay_images_prefix_official,
                prefix_order=[config.quay_images_prefix_candidate],
                mappings=mappings,
                verbose=verbose)
        else:
            cls._pull_image(image, mappings=mappings, verbose=verbose)

    @classmethod
    def _pull_docker_image(cls, image, domestic=False,
                           mappings=None, verbose=False):
        if domestic:
            cls._pull_domestic_image(
                image,
                ori_prefix=config.docker_images_prefix_official,
                prefix_order=[config.docker_image_prefix_candidate],
                mappings=mappings,
                verbose=verbose
            )
        else:
            cls._pull_image(image, mappings=mappings, verbose=verbose)

    @classmethod
    def _pull_ghcr_image(cls, image, domestic=False,
                         mappings=None, verbose=False):
        if domestic:
            cls._pull_domestic_image(
                image,
                ori_prefix=config.ghcr_images_prefix_official,
                prefix_order=[config.ghcr_images_prefix_candidate],
                mappings=mappings,
                verbose=verbose
            )
        else:
            cls._pull_image(image, mappings=mappings, verbose=verbose)

    @staticmethod
    def get_host_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
        finally:
            s.close()
        return ip

    @staticmethod
    def download_file(url, save_path, proxies=None):
        """Download file from URL.

        Download file from URL and save it locally.

        Args:
            url: File's URL.
            save_path: Path where file will be saved.
            proxies: HTTP proxy if necessary.

        Returns:
            None.
        """
        # refer to
        # https://zhuanlan.zhihu.com/p/106309634
        color_print.debug(
            'downloading {url} to {dst}'.format(
                url=url, dst=save_path))
        res = requests.get(url, stream=True, proxies=proxies)
        content_length = res.headers.get('content-length')
        if content_length:
            total_length = int(int(content_length) / 1024) + 1 
        else:
            print("error to get content-length,please check url or internet")
        dst = save_path
        with open(dst, 'wb') as f:
            bar = tqdm(
                iterable=res.iter_content(
                    chunk_size=1024),
                total=total_length,
                unit='k',
                desc='downloading process',
                ncols=80)
            for chunk in bar:
                if chunk:
                    f.write(chunk)

    @staticmethod
    def reload_and_restart_docker(verbose=False):
        """Reload configurations and restart Docker.

        systemctl daemon-reload && systemctl restart docker

        Args:
            verbose: Verbose or not.

        Returns:
            Boolean indicating whether configurations is successfully reload and
            Docker is successfully restarted or not.
        """
        # reload docker daemon configurations
        if not system_func.reload_daemon_config(verbose=verbose):
            return False
        stdout, stderr = verbose_func.verbose_output(verbose)
        color_print.debug('restarting docker')
        try:
            subprocess.run(
                'systemctl restart docker'.split(),
                stdout=stdout,
                stderr=stderr,
                check=True)
            return True
        except subprocess.CalledProcessError:
            color_print.error('failed to restart docker')
            return False
