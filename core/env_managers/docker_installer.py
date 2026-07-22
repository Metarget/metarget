"""
Docker Installer
"""
import copy
import subprocess
import os
import utils.color_print as color_print
import utils.verbose as verbose_func
import config
import utils.checkers as checkers
from core.env_managers.installer import Installer


class DockerInstaller(Installer):
    # _docker_gadgets is only for uninstall process
    _docker_gadgets = [
        'docker-ce',
        'docker-ce-cli',
        'docker',
        'docker-engine',
        'docker.io',
        'containerd.io',
        'runc',
    ]
    _docker_requirements = [
        'apt-transport-https',
        'ca-certificates',
        'gnupg-agent',
        'software-properties-common',
    ]

    @classmethod
    def uninstall(cls, verbose=False):
        """Uninstall Docker.

        Args:
            verbose: Verbose or not.

        Returns:
            None.
        """
        stdout, stderr = verbose_func.verbose_output(verbose)
        for gadget in cls._docker_gadgets:
            temp_cmd = copy.copy(cls.cmd_apt_uninstall)
            temp_cmd.append(gadget)
            subprocess.run(
                temp_cmd,
                stdout=stdout,
                stderr=stderr,
                check=False
            )
            
    #uninstall_containerd_only
    @classmethod
    def uninstall_containerd_only(cls, verbose=False):
        """Uninstall containerd only.

        Args:
            verbose: Verbose or not.

        Returns:
            None.
        """
        stdout, stderr = verbose_func.verbose_output(verbose)
        temp_cmd = copy.copy(cls.cmd_apt_uninstall)
        temp_cmd.append('containerd.io')
        subprocess.run(
            temp_cmd,
            stdout=stdout,
            stderr=stderr,
            check=False
        )        # uninstall containerd only

    #DockerInstaller.uninstall_runc(verbose=args.verbose)
    @classmethod
    def uninstall_runc(cls, verbose=False):
        """Uninstall runc.

        Args:
            verbose: Verbose or not.

        Returns:
            None.
        """
        stdout, stderr = verbose_func.verbose_output(verbose)
        color_print.debug('uninstalling runc')
        # currently we just remove the runc binary
        runc_commands = [
                'rm /usr/bin/runc'        # 重启 docker 服务
            ]
        for command in runc_commands:
            subprocess.run(
                command.split(),
                stdout=stdout,
                stderr=stderr,
                check=True
            )
        

    @classmethod
    def install_by_version(cls, gadgets, context=None, verbose=False):
        """Install Docker with specified version.

        Args:
            gadgets: Docker gadgets (e.g. docker-ce/docker-ce-cli/containerd, but no runc).
            context: Currently not used.
            verbose: Verbose or not.

        Returns:
            Boolean indicating whether Docker is successfully installed or not.
        """
        if not cls._pre_install(verbose=verbose):
            color_print.error('failed to install prerequisites')
            return False
        for gadget in gadgets:
            if not cls._install_one_gadget_by_version(
                    gadget['name'], gadget['version'], verbose=verbose):
                color_print.error(
                    'some errors happened during docker installation')
                return False
        return True

    @classmethod
    def _pre_install(cls, verbose=False):
        stdout, stderr = verbose_func.verbose_output(verbose)
        # install requirements
        color_print.debug('installing prerequisites')
        try:
            # need to comment "https://download.docker.com/linux/ubuntu bionic stable" in following files before apt-get update
            cls._comment_source(verbose=verbose)
            if not cls._apt_update(verbose=verbose):
                return False
            subprocess.run(
                cls.cmd_apt_install +
                cls._docker_requirements,
                stdout=stdout,
                stderr=stderr,
                check=True)
        except subprocess.CalledProcessError:
            return False
        # Add ONE Docker apt source — probe both candidates and pick the first reachable one
        # to avoid having two simultaneous sources (which causes apt-get update to fail if
        # one mirror has a temporary sync issue).
        _docker_apt_candidates = [
            (config.docker_apt_repo_gpg, config.docker_apt_repo_entry),
            (config._docker_apt_repo_gpg_aliyun, config._docker_apt_repo_entry_aliyun),
        ]
        _reachable = [
            (g, e) for g, e in _docker_apt_candidates if cls._probe_url(g, verbose=verbose)
        ]
        for _gpg_url, _repo_entry in (_reachable or _docker_apt_candidates[:1]):
            if cls._add_apt_repository(gpg_url=_gpg_url, repo_entry=_repo_entry, verbose=verbose):
                break

        cls._apt_update(verbose=verbose)

        return True


    @classmethod
    def _comment_source(cls, verbose=False):
        stdout, stderr = verbose_func.verbose_output(verbose)
        for file in config.files_to_check:
            if os.path.isfile(file):
                color_print.debug('commenting docker source in %s' % file)
                command = [
                    'sed', '-i',
                    f"s|.*download.docker.com.*|# &|",  # 匹配包含 "download.docker.com" 的任何行并在其前面加上 "#"
                    file
                ]
                try:
                    subprocess.run(
                        command,
                        stdout=stdout,
                        stderr=stderr,
                        check=True
                    )
                    color_print.debug(f"Successfully commented out repository URL in {file}")
                except subprocess.CalledProcessError as e:
                    color_print.error(f"Error while modifying {file}: {e}")

    #DockerInstaller.install_runc(install_version, verbose=args.verbose)
    @classmethod
    def install_runc(cls, install_version, verbose=False):
        """Install runc.

        Args:
            install_version: Version of runc.
            verbose: Verbose or not.

        Returns:
            Boolean indicating whether runc is successfully installed or not.
        """
        stdout, stderr = verbose_func.verbose_output(verbose)
        color_print.debug('installing runc with version {version}'.format(version=install_version))
        
        # 代理网址列表
        proxy_urls = [
            'https://github.moeyy.xyz',
            'https://gh-proxy.com',
            'https://ghproxy.net'
        ]

        url = f'https://github.com/opencontainers/runc/releases/download/v{install_version}/runc.amd64'

        # 尝试每个代理网址
        for proxy_url in proxy_urls:
            download_url = f'{proxy_url}/{url}'
            try:
                # 构建更新命令
                runc_commands = [
                    'mv /usr/bin/runc /usr/bin/runc.bak',
                    f'curl -L -o /usr/bin/runc {download_url}',
                    'chmod +x /usr/bin/runc',
                    'systemctl daemon-reload',
                    'systemctl restart docker',
                ]
                color_print.warning(f'Attempting to download runc from {download_url}')
                for command in runc_commands:
                    subprocess.run(
                        command.split(),
                        stdout=stdout,
                        stderr=stderr,
                        check=True
                    )
                return True  # 如果下载和安装成功，则返回 True
            except subprocess.CalledProcessError:
                color_print.error(f'Failed to download runc from {download_url}. Trying next proxy...')
                continue  # 如果当前代理下载失败，则尝试下一个代理
        
        # 如果所有代理都失败了
        color_print.error('All download attempts failed. Restoring the original runc.')
        try:
            subprocess.run(
                'mv /usr/bin/runc.bak /usr/bin/runc'.split(),
                stdout=stdout,
                stderr=stderr,
                check=True
            )
            checkers.runc_executable(verbose=verbose)
        except subprocess.CalledProcessError:
            color_print.error('Failed to restore original runc.')
        
        return False

if __name__ == "__main__":
    DockerInstaller.uninstall()
    import sys
    if len(sys.argv) > 1:
        test_version = sys.argv[1]
    else:
        test_version = '17.03.0'
    temp_gadgets = [{'name': 'docker-ce', 'version': test_version}]
    DockerInstaller.install_by_version(temp_gadgets)
