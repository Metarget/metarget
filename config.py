import platform


# metarget version
VERSION = '0.1'
# default CNI plugin
DEFAULT_CNI_PLUGIN = 'flannel'
# default kata runtime type
DEFAULT_KATA_RUNTIME_TYPE = 'qemu'

# currently supported gadgets
gadgets_supported = [
    'docker',
    'k8s',
    'kata',
    'kernel',
]

vuln_cn_dir_wildcard = "vulns_cn/*"
vuln_app_dir_wildcard = "vulns_app/*/*"
vuln_app_dir_prefix = "vulns_app/"
vuln_app_desc_file = 'desc.yaml'

runtime_data_dir = 'data/'
runtime_host_ports_usage_file = 'data/host_ports_usage.yaml'
runtime_host_port_lower_bound = 30000

k8s_metarget_namespace = 'metarget'
k8s_metarget_namespace_file = 'yamls/k8s_metarget_namespace.yaml'

# k8s worker
k8s_worker_template = 'tools/install_k8s_worker_template.sh'
k8s_worker_script = 'tools/install_k8s_worker.sh'
k8s_hash_generator = 'tools/generate_hash.sh'

# related to kernel
kernel_packages_list = 'yamls/kernel_packages_list.yaml'
ubuntu_kernel_repo = 'https://kernel.ubuntu.com/~kernel-ppa/mainline/'
kernel_packages_dir = '/tmp'

# kata containers
kata_static_tar_file = 'kata-static-%s-x86_64.tar.xz'
kata_tar_decompress_dest = '/opt/kata/'
kata_static_url_prefix = 'https://github.com/kata-containers/runtime/releases/download/%s/'
kata_config_dir = '/etc/kata-containers/'

# kubernetes components images sources
_k8s_images_prefix_aliyun = "registry.cn-hangzhou.aliyuncs.com/google_containers/"
_k8s_images_prefix_aliyun_2 = "registry.aliyuncs.com/google_containers/"

# quay.io images sources
_quay_images_prefix_ustc = "quay.mirrors.ustc.edu.cn/"

# docker.io images sources
_docker_image_prefix_ustc = "docker.mirrors.ustc.edu.cn/"


# k8s apt repositories
_k8s_apt_repo_gpg_aliyun = "https://mirrors.aliyun.com/kubernetes/apt/doc/apt-key.gpg"
_k8s_apt_repo_entry_aliyun = 'deb https://mirrors.aliyun.com/kubernetes/apt/ kubernetes-xenial main'

_k8s_apt_repo_entry_ustc = 'deb http://mirrors.ustc.edu.cn/kubernetes/apt kubernetes-xenial main'

# docker apt repositories
_docker_apt_repo_gpg_official = 'https://download.docker.com/linux/ubuntu/gpg'

try:
    release = platform.dist()[2]
except AttributeError:
    release = 'trusty'
_docker_apt_repo_entry_official = 'deb [arch=amd64] https://download.docker.com/linux/ubuntu {release} stable'.format(
    release=release)

# kernel apt repositories
_kernel_apt_repo_entry_xenial_official = 'deb http://security.ubuntu.com/ubuntu xenial-security main'
_kernel_apt_repo_entry_trusty_official = 'deb http://security.ubuntu.com/ubuntu trusty-security main'
_kernel_apt_repo_entry_bionic_official = 'deb http://security.ubuntu.com/ubuntu bionic-security main'

# active k8s components images source
k8s_images_prefix_official = "k8s.gcr.io/"
k8s_images_prefix_official_9 = "gcr.io/google_containers/"
k8s_images_prefix_candidate = _k8s_images_prefix_aliyun

# active quay images source
quay_images_prefix_official = "quay.io/"
quay_images_prefix_candidate = _quay_images_prefix_ustc

# docker images source
docker_images_prefix_official = "docker.io/"
docker_image_prefix_candidate = _docker_image_prefix_ustc

# active k8s apt repository
k8s_apt_repo_gpg = _k8s_apt_repo_gpg_aliyun
k8s_apt_repo_entry = _k8s_apt_repo_entry_aliyun

# active docker apt repository
docker_apt_repo_gpg = _docker_apt_repo_gpg_official
docker_apt_repo_entry = _docker_apt_repo_entry_official

# active kernel apt repository
kernel_apt_repo_entries = [
    _kernel_apt_repo_entry_trusty_official,
    _kernel_apt_repo_entry_xenial_official,
    _kernel_apt_repo_entry_bionic_official,
]

# CNI plugins
available_cni_plugins = [
    'flannel',
    'calico',
    'cilium',
]
cni_plugin_cidrs = {
    'flannel': '10.244.0.0/16',
    'calico': '10.10.0.0/16',
    'cilium': '10.10.0.0/16',
}
flannel_yaml_k8s_1_6_to_1_15_rbac = "yamls/flannel/kube-flannel-rbac.yml"
flannel_yaml_k8s_1_6_to_1_15 = "yamls/flannel/kube-flannel-legacy.yml"
flannel_yaml_k8s_16 = "yamls/flannel/kube-flannel-16.yml"
flannel_yaml_k8s_over_16 = "yamls/flannel/kube-flannel.yml"
flannel_image_k8s_1_6_to_1_15 = "quay.io/coreos/flannel:v0.10.0-amd64"
flannel_image_k8s_from_1_16 = "quay.io/coreos/flannel:v0.13.1-rc1"
calico_yaml_below_1_14 = "yamls/calico/calico-below-14.yaml"
calico_yaml_from_1_14 = "yamls/calico/calico-from-14.yaml"
calico_images = [
    "docker.io/calico/cni:v3.17.1",
    "docker.io/calico/pod2daemon-flexvol:v3.17.1",
    "docker.io/calico/node:v3.17.1",
    "docker.io/calico/kube-controllers:v3.17.1",
]
cilium_yaml = "yamls/cilium/cilium_quick_install.yaml"
cilium_images = [
    "quay.io/cilium/cilium:v1.9.0",
    "quay.io/cilium/operator-generic:v1.9.0",
]

k8s_images_base_from_12 = [
    'k8s.gcr.io/kube-proxy',
    'k8s.gcr.io/kube-controller-manager',
    'k8s.gcr.io/kube-apiserver',
    'k8s.gcr.io/kube-scheduler',
]

k8s_images_base_10_to_11 = [
    'k8s.gcr.io/kube-proxy-amd64',
    'k8s.gcr.io/kube-controller-manager-amd64',
    'k8s.gcr.io/kube-apiserver-amd64',
    'k8s.gcr.io/kube-scheduler-amd64',
]

k8s_images_base_9 = [
    'gcr.io/google_containers/kube-proxy-amd64',
    'gcr.io/google_containers/kube-controller-manager-amd64',
    'gcr.io/google_containers/kube-apiserver-amd64',
    'gcr.io/google_containers/kube-scheduler-amd64',
]

# get from
# https://storage.googleapis.com/kubernetes-release/release/stable-1.xx.txt
k8s_stable_versions = {
    # '1.7': 'v1.7.16',
    # '1.8': 'v1.8.15',
    '1.9': 'v1.9.11',
    '1.10': 'v1.10.13',
    '1.11': 'v1.11.10',
    '1.12': 'v1.12.10',
    '1.13': 'v1.13.12',
    '1.14': 'v1.14.10',
    '1.15': 'v1.15.12',
    '1.16': 'v1.16.15',
    '1.17': 'v1.17.16',
    '1.18': 'v1.18.14',
    '1.19': 'v1.19.6',
}

k8s_images_extra = {
    '1.19': [
        'k8s.gcr.io/pause:3.2',
        'k8s.gcr.io/etcd:3.4.13-0',
        'k8s.gcr.io/coredns:1.7.0',
    ],
    '1.18': [
        'k8s.gcr.io/pause:3.2',
        'k8s.gcr.io/etcd:3.4.3-0',
        'k8s.gcr.io/coredns:1.6.7',
    ],
    '1.17': [
        'k8s.gcr.io/pause:3.1',
        'k8s.gcr.io/etcd:3.4.3-0',
        'k8s.gcr.io/coredns:1.6.5',
    ],
    '1.16': [
        'k8s.gcr.io/pause:3.1',
        'k8s.gcr.io/etcd:3.3.15-0',
        'k8s.gcr.io/coredns:1.6.2',
    ],
    '1.15': [
        'k8s.gcr.io/pause:3.1',
        'k8s.gcr.io/etcd:3.3.10',
        'k8s.gcr.io/coredns:1.3.1',
    ],
    '1.14': [
        'k8s.gcr.io/pause:3.1',
        'k8s.gcr.io/etcd:3.3.10',
        'k8s.gcr.io/coredns:1.3.1',
    ],
    '1.13': [
        'k8s.gcr.io/pause:3.1',
        'k8s.gcr.io/etcd:3.2.24',
        'k8s.gcr.io/coredns:1.2.6',
    ],
    '1.12': [
        'k8s.gcr.io/pause:3.1',
        'k8s.gcr.io/etcd:3.2.24',
        'k8s.gcr.io/coredns:1.2.2',
    ],
    '1.11': [
        'k8s.gcr.io/pause:3.1',
        'k8s.gcr.io/etcd-amd64:3.2.18',
        'k8s.gcr.io/coredns:1.1.3',
    ],
    '1.10': [
        'k8s.gcr.io/pause-amd64:3.1',
        'k8s.gcr.io/etcd-amd64:3.1.12',
        # 'k8s.gcr.io/coredns:1.1.3',
        'k8s.gcr.io/k8s-dns-kube-dns-amd64:1.14.8',
        'k8s.gcr.io/k8s-dns-sidecar-amd64:1.14.8',
        'k8s.gcr.io/k8s-dns-dnsmasq-nanny-amd64:1.14.8',
    ],
    '1.9': [
        'gcr.io/google_containers/pause-amd64:3.0',
        'gcr.io/google_containers/etcd-amd64:3.1.11',
        'gcr.io/google_containers/k8s-dns-kube-dns-amd64:1.14.7',
        'gcr.io/google_containers/k8s-dns-sidecar-amd64:1.14.7',
        'gcr.io/google_containers/k8s-dns-dnsmasq-nanny-amd64:1.14.7',
    ]
}