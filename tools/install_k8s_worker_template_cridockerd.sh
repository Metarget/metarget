#!/bin/bash

# run as root
# worker node join script for docker+cri-dockerd runtime + new pkgs.k8s.io apt repo (k8s >= 1.24)
# Assumes Docker is already installed on the worker node.

# clear potential old components
if kubeadm reset --help | grep force &> /dev/null; then
  kubeadm reset --force
else
  kubeadm reset
fi
apt-get -y remove kubeadm kubelet

# install cri-dockerd (download .deb with proxy fallback)
${cri_dockerd_download_cmd}
dpkg -i /tmp/cri-dockerd.deb
systemctl daemon-reload
systemctl enable --now cri-docker.service cri-docker.socket

# pre_install kubernetes (new signed-by apt keyring format)
apt-get -y --allow-downgrades install apt-transport-https curl gnupg
mkdir -p /etc/apt/keyrings
curl -fsSL ${gpg_url} | gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
cat > /etc/apt/sources.list.d/kubernetes.list <<'APTSOURCESEOF'
${repo_entry}
APTSOURCESEOF
apt-get update

# install kubernetes-cni kubeadm kubelet
apt-get -y --allow-downgrades install kubernetes-cni=${kubernetes_cni_version}
apt-get -y --allow-downgrades install kubelet=${kubelet_version}
apt-get -y --allow-downgrades install kubeadm=${kubeadm_version}

# pull images (docker manages images when using cri-dockerd)
${cmds_pull_images}

# join cluster via cri-dockerd socket
kubeadm join ${master_ip}:6443 --token ${token} \
    --discovery-token-ca-cert-hash sha256:${ca_cert_hash} ${kubeadm_options} \
    --cri-socket unix:///var/run/cri-dockerd.sock
