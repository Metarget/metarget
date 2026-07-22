#!/bin/bash
#run as root
set -e  # 确保如果任何命令失败，脚本会立即退出

DEBIAN_FRONTEND=noninteractive
TZ=Asia/Shanghai

apt-get install -y \
    qemu-system-x86 \
    wget \
    genisoimage \
    && apt-get clean

#思路：/root/ubuntu-cloud.img是刚下载好的，只是扩容了，没有做任何修改，用来当作基础镜像,后续复制到对应cve文件夹
# /root/cloud-init每个cve都不一样，运行脚本后会把cloud-init.iso复制到对应cve文件夹 eg:/root/images/gfkd-mall
# /root/tools.iso每个cve都一样，运行脚本后会放到/root/images/tools.iso
IMG=/root/ubuntu-cloud.img
MAX_SIZE=$((50 * 1024 * 1024 * 1024)) # 50G，字节
EXPAND_SIZE=20G

if [ ! -f "$IMG" ]; then
    wget -O "$IMG" https://cloud-images.ubuntu.com/bionic/current/bionic-server-cloudimg-amd64.img
    qemu-img resize "$IMG" +$EXPAND_SIZE
else
    echo "$IMG already exists, checking size..."
    CUR_SIZE=$(qemu-img info "$IMG" | grep 'virtual size' | awk -F'[()]' '{print $2}' | awk '{print $1}')
    # CUR_SIZE 单位字节
    if [ "$CUR_SIZE" -lt "$MAX_SIZE" ]; then
        echo "Current size: $((CUR_SIZE/1024/1024/1024))G, expanding by $EXPAND_SIZE..."
        qemu-img resize "$IMG" +$EXPAND_SIZE
    else
        echo "Current size already >= 50G ($((CUR_SIZE/1024/1024/1024))G), skipping resize."
    fi
fi

rm -rf /root/cloud-init 

mkdir -p /root/cloud-init && \
    printf '#cloud-config
users:
  - name: ubuntu
    sudo: ALL=(ALL) NOPASSWD:ALL
    lock_passwd: false
    plain_text_passwd: ubuntu
packages:
  - ubuntu-desktop
  - gnome
  - xserver-xorg
  - chromium-browser
  - apt-transport-https
  - ca-certificates
  - curl
  - gnupg
  - network-manager
  - lsb-release
  - software-properties-common
  - gnupg-agent
  - tmux
bootcmd:
  - mount -o loop /dev/cdrom /mnt
runcmd:
  - sed -i "s/^#*PasswordAuthentication.*/PasswordAuthentication yes/" /etc/ssh/sshd_config
  - sed -i "s/^#*PermitRootLogin.*/PermitRootLogin yes/" /etc/ssh/sshd_config
  - sed -i "s/^#*UsePAM.*/UsePAM yes/" /etc/ssh/sshd_config
  - systemctl restart ssh
  - sudo systemctl enable NetworkManager
  - sudo systemctl start NetworkManager
  - mkdir /tools
  - cp -r /mnt/* /tools/
  - curl -fsSL https://mirrors.aliyun.com/docker-ce/linux/ubuntu/gpg | sudo apt-key add
  - sudo add-apt-repository "deb [arch=amd64] https://mirrors.aliyun.com/docker-ce/linux/ubuntu $(lsb_release -cs) stable"
  - curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo tee /etc/apt/trusted.gpg.d/docker.asc
  - echo "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list
  - echo "deb https://mirrors.ustc.edu.cn/ubuntu/ bionic main restricted universe multiverse" | sudo tee -a /etc/apt/sources.list
  - echo "deb-src https://mirrors.ustc.edu.cn/ubuntu/ bionic main restricted universe multiverse" | sudo tee -a /etc/apt/sources.list
  - echo "deb https://mirrors.ustc.edu.cn/ubuntu/ bionic-security main restricted universe multiverse" | sudo tee -a /etc/apt/sources.list
  - echo "deb-src https://mirrors.ustc.edu.cn/ubuntu/ bionic-security main restricted universe multiverse" | sudo tee -a /etc/apt/sources.list
  - echo "deb https://mirrors.ustc.edu.cn/ubuntu/ bionic-updates main restricted universe multiverse" | sudo tee -a /etc/apt/sources.list
  - echo "deb-src https://mirrors.ustc.edu.cn/ubuntu/ bionic-updates main restricted universe multiverse" | sudo tee -a /etc/apt/sources.list
  - echo "deb https://mirrors.ustc.edu.cn/ubuntu/ bionic-backports main restricted universe multiverse" | sudo tee -a /etc/apt/sources.list
  - echo "deb-src https://mirrors.ustc.edu.cn/ubuntu/ bionic-backports main restricted universe multiverse" | sudo tee -a /etc/apt/sources.list
  - apt-get update
  - apt-get -y --allow-downgrades install docker-ce=5:19.03.6~3-0~ubuntu-bionic
  - apt-get -y --allow-downgrades install docker-ce-cli=5:19.03.6~3-0~ubuntu-bionic
  - systemctl enable docker
  - systemctl start docker
  - docker load -i tools/images/ubuntu_latest.tar
  - for img in tools/n8n/docker_images/*.tar; do docker load -i "$img"; done
  - apt-get -y --allow-downgrades install containerd.io=1.2.6-3
  - systemctl daemon-reload
  - systemctl restart docker
  - cp /tools/update-netplan.service /etc/systemd/system/
  - sudo systemctl daemon-reload
  - sudo systemctl enable update-netplan.service
  - sudo systemctl start update-netplan.service
  - sudo systemctl restart docker
  - dpkg -i /tools/kernel-5.9.10/*.deb
  - echo "Initialized successfully!"' > /root/cloud-init/user-data && \
    touch /root/cloud-init/meta-data && \
    rm -f /root/cloud-init.iso && \
    genisoimage -output /root/cloud-init.iso -volid cidata -joliet -rock \
    /root/cloud-init/user-data /root/cloud-init/meta-data

echo "/root/cloud-init.iso created."

genisoimage -output /root/tools.iso -volid tools -joliet -rock /root/tools
echo "/root/tools.iso created."

mkdir -p /images/n8n
echo 'folder : /images/n8n created.'
cp /root/ubuntu-cloud.img /images/n8n/n8n.img
echo '/root/ubuntu-cloud.img copied to /images/n8n/n8n.img'
cp /root/cloud-init.iso /images/n8n/
echo '/root/cloud-init.iso copied to /images/n8n/cloud-init.iso'
echo 'now you can run the following commands to initialize the image:'
echo 
echo 'qemu-system-x86_64 \
    -drive file=/images/n8n/n8n.img,format=qcow2,if=virtio,cache=none \
    -drive file=/images/n8n/cloud-init.iso,format=raw,if=virtio \
    -cdrom /root/tools.iso \
    -m 8G \
    -nographic \
    -cpu host \
    -enable-kvm \
    -no-reboot \
    -smp 8 \
    -net nic \
    -net user,hostfwd=tcp::2222-:22'
