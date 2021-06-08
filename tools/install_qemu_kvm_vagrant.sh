#!/bin/bash

apt-get install qemu
apt-get install qemu-kvm libvirt-bin ubuntu-vm-builder bridge-utils
adduser `id -un` libvirt
adduser `id -un` kvm

curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
apt-get update && apt-get install vagrant

apt-get build-dep vagrant ruby-libvirt
apt-get install qemu libvirt-bin ebtables dnsmasq-base
apt-get install libxslt-dev libxml2-dev libvirt-dev zlib1g-dev ruby-dev
vagrant plugin install vagrant-libvirt