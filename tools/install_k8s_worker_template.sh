#!/bin/bash

# run as root
# currently docker should be installed

# clear potential old components

if kubeadm reset --help | grep force &> /dev/null; then
  kubeadm reset --force
else
  kubeadm reset
fi
apt-get -y remove kubeadm kubelet

# pre_configure
modprobe br_netfilter
echo "net.bridge.bridge-nf-call-ip6tables = 1" > /etc/sysctl.d/k8s.conf
echo "net.bridge.bridge-nf-call-iptables = 1" >> /etc/sysctl.d/k8s.conf
swapoff -a

# pre_install
apt-get update
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

# join
kubeadm join ${master_ip}:6443 --token ${token} \
    --discovery-token-ca-cert-hash sha256:${ca_cert_hash} ${kubeadm_options}


