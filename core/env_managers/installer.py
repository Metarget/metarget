"""
Basic Installer
- supplies some common useful functions
- specific installers should inherit this class to reuse common functions if necessary
"""

import copy
import subprocess
import docker
import socket
import requests
from tqdm import tqdm

import config
import utils.verbose as verbose_func
import utils.color_print as color_print


class Installer:
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
            res = subprocess.run(temp_cmd, stdout=subprocess.PIPE, stderr=stderr, check=True)
        except subprocess.CalledProcessError:
            return None
        entries = res.stdout.decode('utf-8').split('\n')
        complete_version = None
        for entry in entries:
            if version in entry:
                complete_version = entry.split('|')[1].strip()
                break
        return complete_version

    @classmethod
    def _get_apt_complete_package(cls, name, keywords, verbose=False):
        _, stderr = verbose_func.verbose_output(verbose)
        temp_cmd = copy.copy(cls.cmd_apt_search)
        temp_cmd.append(name)
        try:
            res = subprocess.run(temp_cmd, stdout=subprocess.PIPE, stderr=stderr, check=True)
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
    def _install_one_gadget_by_version(cls, name, version, mappings=None, verbose=False):
        stdout, stderr = verbose_func.verbose_output(verbose)
        # get complete version, e.g. 18.03.1~ce-0~ubuntu
        complete_version = cls._get_apt_complete_version(name, version, verbose=verbose)
        if complete_version:
            color_print.debug('installing {gadget} with {version} version'.format(gadget=name, version=complete_version))
            # install with the specified version
            temp_cmd = copy.copy(cls.cmd_apt_install)
            temp_cmd.append(
                '{name}={version}'.format(
                    name=name,
                    version=complete_version))
            try:
                subprocess.run(temp_cmd, stderr=stderr, stdout=stdout, check=True)
            except subprocess.CalledProcessError:
                return False
            if mappings:
                mappings[name] = complete_version
            return True
        color_print.warning('warning: no candidate version for %s' % name)
        return False

    @classmethod
    def _add_apt_repository(cls, repo_entry, gpg_url=None, verbose=False):
        stdout, stderr = verbose_func.verbose_output(verbose)
        color_print.debug('adding apt repository %s' % repo_entry)
        try:
            if gpg_url:
                cmd_curl_gpg = 'curl -fsSL {gpg_url}'.format(
                    gpg_url=gpg_url).split()
                res = subprocess.run(
                    cmd_curl_gpg,
                    stdout=subprocess.PIPE,
                    stderr=stderr,
                    check=True)
                subprocess.run(cls.cmd_apt_add_key, input=res.stdout, stdout=stdout, stderr=stderr, check=True)

            # add apt repository
            cmd_apt_add_repository = 'add-apt-repository\n' \
                                     '{repo_entry}'.format(
                                         repo_entry=repo_entry).split('\n')
            subprocess.run(cmd_apt_add_repository, stdout=stdout, stderr=stderr, check=True)
            subprocess.run(cls.cmd_apt_update, stdout=stdout, stderr=stderr, check=True)
            return True
        except subprocess.CalledProcessError:
            return False

    @classmethod
    def _pull_images(cls, images, mappings=None, verbose=False):
        for image in images:
            cls._pull_image(image, mappings, verbose)

    @classmethod
    def _pull_image(cls, image, mappings=None, verbose=False):
        stdout, stderr = verbose_func.verbose_output(verbose)
        if mappings:
            mappings[image] = None
        if not cls._image_exist(image):
            color_print.debug('pulling %s' % image)
            temp_cmd = 'docker pull {image}'.format(image=image).split()
            try:
                subprocess.run(temp_cmd, stdout=stdout, stderr=stderr, check=True)
                return True
            except subprocess.CalledProcessError:
                return False
        else:
            color_print.debug('%s already pulled' % image)

    @classmethod
    def _pull_domestic_images(cls, images, ori_prefix,
                              new_prefix, mappings=None, verbose=False):
        for image in images:
            cls._pull_domestic_image(image, ori_prefix, new_prefix, mappings, verbose=verbose)

    @classmethod
    def _pull_domestic_image(cls, image, ori_prefix,
                             new_prefix, mappings=None, verbose=False):
        temp_image = image.replace(ori_prefix, new_prefix)
        if mappings:
            mappings[temp_image] = image
        if not cls._image_exist(image):
            cls._pull_image(temp_image, verbose=verbose)
            cls._tag_image(temp_image, image)
        else:
            color_print.debug('%s already pulled' % image)

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
    def _pull_quay_image(cls, image, domestic=False, mappings=None, verbose=False):
        if domestic:
            cls._pull_domestic_image(
                image,
                ori_prefix=config.quay_images_prefix_official,
                new_prefix=config.quay_images_prefix_candidate,
                mappings=mappings,
                verbose=verbose)
        else:
            cls._pull_image(image, mappings=mappings, verbose=verbose)

    @classmethod
    def _pull_docker_image(cls, image, domestic=False, mappings=None, verbose=False):
        if domestic:
            cls._pull_domestic_image(
                image,
                ori_prefix=config.docker_images_prefix_official,
                new_prefix=config.docker_image_prefix_candidate,
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
    def download_file(url, save_dir):
        # refer to
        # https://zhuanlan.zhihu.com/p/106309634
        color_print.debug(
            'downloading {url} to {dst}'.format(
                url=url, dst=save_dir))
        res = requests.get(url, stream=True)
        total_length = int(int(res.headers.get('content-length')) / 1024) + 1
        file_name = url.split('/')[-1]
        dst = save_dir + '/' + file_name
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
