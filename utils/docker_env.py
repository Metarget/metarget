"""
Helpers for Docker daemon environment (systemd) vs process environment.
"""

import copy
import os
import re
import subprocess


def get_docker_daemon_environment():
    """Read Environment= from the docker systemd unit."""
    try:
        res = subprocess.run(
            ['systemctl', 'show', 'docker', '--property=Environment'],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=True,
            text=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {}
    match = re.search(r'^Environment=(.*)$', res.stdout.strip(), re.MULTILINE)
    if not match or not match.group(1):
        return {}
    env = {}
    for part in match.group(1).split():
        if '=' in part:
            key, value = part.split('=', 1)
            env[key] = value
    return env


def user_env_has_proxy(env):
    if not env:
        return False
    for key in ('HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy'):
        if env.get(key):
            return True
    return False


def registry_pull_env(user_env=None):
    """
    Environment for skopeo/curl pulls in the install process.

    docker pull uses the daemon's proxy (systemd), not this env. When the
    daemon proxy is broken but direct access works, skopeo should bypass it
    unless the user explicitly passed --http-proxy to metarget.
    """
    env = copy.copy(user_env or os.environ)
    if user_env_has_proxy(env):
        return env
    daemon = get_docker_daemon_environment()
    if daemon.get('HTTP_PROXY') or daemon.get('HTTPS_PROXY'):
        for key in (
                'HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy',
                'NO_PROXY', 'no_proxy'):
            env.pop(key, None)
    return env


def docker_daemon_proxy_hint():
    daemon = get_docker_daemon_environment()
    http_proxy = daemon.get('HTTP_PROXY') or daemon.get('http_proxy')
    https_proxy = daemon.get('HTTPS_PROXY') or daemon.get('https_proxy')
    no_proxy = daemon.get('NO_PROXY') or daemon.get('no_proxy')
    if not http_proxy and not https_proxy:
        return None
    lines = [
        '检测到 Docker 守护进程配置了代理（systemd Environment），'
        'docker pull 会走该代理，与 curl/本机直连无关：',
    ]
    if http_proxy:
        lines.append('  HTTP_PROXY=%s' % http_proxy)
    if https_proxy:
        lines.append('  HTTPS_PROXY=%s' % https_proxy)
    if no_proxy:
        lines.append('  NO_PROXY=%s' % no_proxy)
    lines.extend([
        '若代理不可用会导致所有 registry 拉取超时。可任选其一：',
        '  1) 修复代理后: sudo systemctl restart docker',
        '  2) 取消代理: 删除 /etc/systemd/system/docker.service.d/*proxy* 后 daemon-reload && restart docker',
        '  3) 为镜像站加 NO_PROXY（示例）: .aliyuncs.com,m.daocloud.io,gcr.azk8s.cn,k8s.gcr.io,registry.k8s.io,.daocloud.io',
        '  4) 安装 skopeo 后 metarget 会在 docker pull 失败时用直连/ --http-proxy 重试',
        '  5) 手动拉取并 tag 到 k8s.gcr.io/... 后重新执行安装',
    ])
    return '\n'.join(lines)
