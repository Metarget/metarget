#!/bin/bash
set -e -x

# download package
# (you can download it manually and comment the wget command below)
mkdir -p /tmp/kata
wget -P /tmp/kata https://github.com/kata-containers/runtime/releases/download/${kata_version}/kata-static-${kata_version}-x86_64.tar.xz
tar xf /tmp/kata/kata-static-${kata_version}-x86_64.tar.xz
rm -rf /opt/kata
mv /tmp/kata/opt/kata /opt
rm -rf /tmp/kata
rm -rf /etc/kata-containers
cp -r /opt/kata/share/defaults/kata-containers /etc/
# use Cloud Hypervisor as Hypervisor
rm /etc/kata-containers/configuration.toml
ln -s /etc/kata-containers/configuration-${kata_runtime_type}.toml /etc/kata-containers/configuration.toml
# configure Docker
mkdir -p /etc/docker/
cat << EOF > /etc/docker/daemon.json
{
  "runtimes": {
    "kata-runtime": {
      "path": "/opt/kata/bin/kata-runtime"
    },
    "kata-clh": {
      "path": "/opt/kata/bin/kata-clh"
    },
    "kata-qemu": {
      "path": "/opt/kata/bin/kata-qemu"
    }
  },
  "registry-mirrors": ["https://docker.mirrors.ustc.edu.cn/"]
}
EOF
mkdir -p /etc/systemd/system/docker.service.d/
cat << EOF > /etc/systemd/system/docker.service.d/kata-containers.conf
[Service]
ExecStart=
ExecStart=/usr/bin/dockerd -D --add-runtime kata-runtime=/opt/kata/bin/kata-runtime --add-runtime kata-clh=/opt/kata/bin/kata-clh --add-runtime kata-qemu=/opt/kata/bin/kata-qemu --default-runtime=kata-runtime
EOF
# reload configurations & restart Docker
systemctl daemon-reload && systemctl restart docker