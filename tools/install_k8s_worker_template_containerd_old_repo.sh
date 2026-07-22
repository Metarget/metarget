#!/bin/bash

# run as root
# worker node join script for containerd runtime + old kubernetes-xenial apt repo (k8s < 1.24)

# clear potential old components
if kubeadm reset --help | grep force &> /dev/null; then
  kubeadm reset --force
else
  kubeadm reset
fi
apt-get -y remove kubeadm kubelet

# pre_configure
modprobe overlay
modprobe br_netfilter
cat > /etc/modules-load.d/containerd.conf <<EOF
overlay
br_netfilter
EOF
cat > /etc/sysctl.d/99-kubernetes-cri.conf <<EOF
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF
sysctl --system
swapoff -a

# install containerd
apt-get update
apt-get -y install apt-transport-https ca-certificates curl gnupg software-properties-common
# add docker apt repo (contains containerd.io)
curl -fsSL https://mirrors.aliyun.com/docker-ce/linux/ubuntu/gpg | apt-key add -
add-apt-repository "deb [arch=amd64] https://mirrors.aliyun.com/docker-ce/linux/ubuntu $(lsb_release -cs) stable"
apt-get update
apt-get -y install containerd.io

# configure containerd
mkdir -p /etc/containerd
containerd config default > /etc/containerd/config.toml
sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml
systemctl daemon-reload
systemctl enable containerd
systemctl restart containerd

# pre_install kubernetes (old apt-key format)
apt-get -y --allow-downgrades install apt-transport-https curl

curl -fsSL ${gpg_url} | apt-key add -
add-apt-repository "${repo_entry}"
apt-get update

# install kubernetes-cni kubeadm kubelet
apt-get -y --allow-downgrades install kubernetes-cni=${kubernetes_cni_version}
apt-get -y --allow-downgrades install kubelet=${kubelet_version}
apt-get -y --allow-downgrades install kubeadm=${kubeadm_version}

# pull images
${cmds_pull_images}

# join cluster
kubeadm join ${master_ip}:6443 --token ${token} \
    --discovery-token-ca-cert-hash sha256:${ca_cert_hash} ${kubeadm_options} \
    --cri-socket unix:///run/containerd/containerd.sock
