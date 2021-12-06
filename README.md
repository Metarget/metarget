<p align="center">
  <img src="images/metarget-logo.svg" alt="metarget-logo" height="250" />
</p>

[中文](README-zh.md) | [English](README.md)

## 1 Introduction

Metarget = `meta-` + `target`, a framework providing automatic constructions of vulnerable infrastructures, used to deploy simple or complicated vulnerable cloud native targets swiftly and automatically.

If you want to talk about Metarget with us and other security researchers, please contact us:

<img src="https://raw.githubusercontent.com/Metarget/metarget/master/images/metarget-wechat-group.png" width = "200" height = "200" alt="" />

We will invite you into Metarget Wechat group :-)

### 1.1 Why Metarget?

During security researches, we might find that the deployment of vulnerable environment often takes much time, while the time spent on testing PoC or ExP is comparatively short. In the field of cloud native security, thanks to the complexity of cloud native systems, this issue is more terrible.

There are already some excellent security projects like [Vulhub](https://github.com/vulhub/vulhub), [VulApps](https://github.com/Medicean/VulApps) in the open-source community, which pack vulnerable scenes into container images, so that researchers could utilize them and deploy scenes quickly.

However, these projects mainly focus on vulnerabilities in applications. What if we need to study the vulnerabilities in the infrastructures like Docker, Kubernetes and even Linux kernel?

Hence, we develop Metarget and hope to solve the deployment issue above to some extent. Furthermore, we also expect that Metarget could help to construct **multilayer** vulnerable cloud native scenes automatically.

### 1.2 Install Vulnerability!

In this project, we come up with concepts like *installing vulnerabilities* and *installing vulnerable scenes*. Why not install vulnerabilities just like installing softwares? We can do that, because our goals are security research and offensive security.

To be exact, we expect that:

- `metarget cnv install cve-2019-5736` will install Docker with CVE-2019-5736 onto the server.
- `metarget cnv install cve-2018-1002105` will install Kubernetes with CVE-2018-1002105 onto the server.
- `metarget cnv install kata-escape-2020` will install Kata-containers with CVE-2020-2023/2025/2026 onto the server.
- `metarget cnv install cve-2016-5195` will install a kernel with DirtyCoW into the server.

It's cool, right? No more steps. No RTFM. Execute one command and enjoy your coffee.

Furthermore, we expect that:

- with Metarget's help, ethical hackers are able to deploy simple or complicated cloud native targets swiftly and learn by hacking cloud native environments.
- `metarget appv install dvwa` will install a [DVWA](https://github.com/digininja/DVWA) target onto our vulnerable infrastructure.
- `metarget appv install thinkphp-5-0-23-rce --external` will install a ThinkPHP RCE vulnerability with `NodePort` service onto our vulnerable infrastructure.

You can just run 5 commands below after installing a new Ubuntu and obtain a multi-layer vulnerable scene:

```bash
./metarget cnv install cve-2016-5195 # container escape with dirtyCoW
./metarget cnv install cve-2019-5736 # container escape with docker
./metarget cnv install cve-2018-1002105 # kubernetes single-node cluster with cve-2018-1002105
./metarget cnv install privileged-container # deploy a privileged container
./metarget appv install dvwa --external # deploy dvwa target
```

RCE, container escape, lateral movement, persistence, they are yours now.

More awesome functions are coming! Stay tuned :)

Note:

This project aims to provide vulnerable scenes for security research. The security of scenes generated is not guaranteed. It is **NOT** recommended to deploy components or scenes with Metarget on the Internet.

## 2 Installation

### 2.1 Requirements

- Ubuntu 16.04 or 18.04
- **Python >= 3.6** (Python 2.x is unsupported!)
- pip3

### 2.2 From Source

Clone the repository and install requirements:

```bash
git clone https://github.com/brant-ruan/metarget.git
cd metarget/
pip install -r requirements.txt
```

Begin to use Metarget and construct vulnerable scenes. For example:

```bash
./metarget cnv install cve-2019-5736
```

### 2.3 From PyPI

Currently unsupported.

## 3 Usage

### 3.1 Basic Usage

```
usage: metarget [-h] [-v] subcommand ...

automatic constructions of vulnerable infrastructures

positional arguments:
  subcommand     description
    gadget       cloud native gadgets (docker/k8s/...) management
    cnv          cloud native vulnerabilities management
    appv         application vulnerabilities management

optional arguments:
  -h, --help     show this help message and exit
  -v, --version  show program's version number and exit
```

Run `./metarget gadget list` to see cloud native components supported currently.

### 3.2 Manage Cloud Native Components

```
usage: metarget gadget [-h] subcommand ...

positional arguments:
  subcommand  description
    list      list supported gadgets
    install   install gadgets
    remove    uninstall gadgets

optional arguments:
  -h, --help  show this help message and exit
```

#### 3.2.1 Case: Install Docker with Specified Version

Run:

```bash
./metarget gadget install docker --version 18.03.1
```

If the command above completes successfully, 18.03.1 Docker will be installed.

#### 3.2.2 Case: Install Kubernetes with Specified Version

Run:

```bash
./metarget gadget install k8s --version 1.16.5
```

If the command above completes successfully, 1.16.5 Kubernetes single-node cluster will be installed.

Note:

Usually, lots of options need to be configured in Kubernetes. As a security research project, Metarget provides some options for installation of Kubernetes:

```
  -v VERSION, --version VERSION
                        gadget version
  --cni-plugin CNI_PLUGIN
                        cni plugin, flannel by default
  --pod-network-cidr POD_NETWORK_CIDR
                        pod network cidr, default cidr for each plugin by
                        default
  --taint-master        taint master node or not
```

**Metarget supports deployment of multi-node cluster. If you want to add more nodes into the cluster, you can copy `tools/install_k8s_worker.sh` script and run it on each worker nodes after the successful installation of single-node cluster.**

#### 3.2.3 Case: Install Kata-containers with Specified Version

Run:

```bash
./metarget gadget install kata --version 1.10.0
```

If the command above completes successfully, 1.10.0 Kata-containers will be installed.

Note:

You can also specify the type of kata runtime (qemu/clh/fc/...) with `--kata-runtime-type` option, which is `qemu` by default.

#### 3.2.4 Case: Install Linux Kernel with Specified Version

Run:

```bash
./metarget gadget install kernel --version 5.7.5
```

If the command above completes successfully, 5.7.5 kernel will be installed.

Note:

Currently, Metarget installs kernels in 2 ways:

1. apt
2. if apt package is not available, download \*.deb remotely from Ubuntu and try to install

After successful installation of kernel, reboot of system is needed. Metarget will prompt to reboot automatically.

### 3.3 Manage Vulnerable Scenes Related to Cloud Native Components

```
usage: metarget cnv [-h] subcommand ...

positional arguments:
  subcommand  description
    list      list supported cloud native vulnerabilities
    install   install cloud native vulnerabilities
    remove    uninstall cloud native vulnerabilities

optional arguments:
  -h, --help  show this help message and exit
```

Run `./metarget cnv list` to see vulnerable scenes related to cloud native components supported currently.

#### 3.3.1 Case: CVE-2019-5736

Run: 

```bash
./metarget cnv install cve-2019-5736
```

If the command above completes successfully, Docker with CVE-2019-5736 will be installed。

#### 3.3.2 Case: CVE-2018-1002105

Run: 

```bash
./metarget cnv install cve-2018-1002105
```

If the command above completes successfully, Kubernetes with CVE-2018-1002105 will be installed。

#### 3.3.3 Case: Kata-containers Escape

Run:

```bash
./metarget cnv install kata-escape-2020
```

If the command above completes successfully, Kata-containers with CVE-2020-2023/2025/2026 will be installed。

#### 3.3.4 Case: CVE-2016-5195

Run: 

```bash
./metarget cnv install cve-2016-5195
```

If the command above completes successfully, kernel with CVE-2016-5195 will be installed。

### 3.4 Manage Vulnerable Scenes Related to Cloud Native Applications

```
usage: metarget appv [-h] subcommand ...

positional arguments:
  subcommand  description
    list      list supported application vulnerabilities
    install   install application vulnerabilities
    remove    uninstall application vulnerabilities

optional arguments:
  -h, --help  show this help message and exit
```

Run `./metarget appv list` to see vulnerable scenes related to cloud native applications supported currently.

Note:

Before deploying application vulnerable scenes, you should install Docker and Kubernetes firstly. You can use Metarget to install Docker and Kubernetes.

#### 3.4.1 Case: DVWA

Run:

```bash
./metarget appv install dvwa
```

If the command above completes successfully, [DVWA](https://github.com/digininja/DVWA) will be deployed as *Deployment* and *Service* resources in current Kubernetes.

Note:

- You can specify `--external` option, then the service will be exposed as `NodePort`, so that you can visit it by IP of the host node (By default, the type of service is `ClusterIP`).
- You can specify `--host-net` option, then the appv will share the host network namespace.
- You can specify `--host-pid` option, then the appv will share the host pid namespace.

### 3.5 Manage Vulnerable Cloud Native Target Cluster

Developing, currently not supported.

## 4 Scene List

### 4.1 Vulnerable Scenes Related to Cloud Native Components

If there is an asterisk (\*) following the name of one vulnerable scene, you need to read the note related to it below the whole table for further details.

|Name|Class|Type|CVSS 3.x|Writeup\*|
|:-:|:-:|:-:|:-:|:-:|
|[cve-2018-15664](vulns_cn/docker/cve-2018-15664.yaml)|docker|container_escape|[7.5](https://nvd.nist.gov/vuln/detail/CVE-2018-15664)||
|[cve-2019-13139](vulns_cn/docker/cve-2019-13139.yaml)|docker|command_execution|[8.4](https://nvd.nist.gov/vuln/detail/CVE-2019-13139)|[link](writeups_cnv/docker-cve-2019-13139)|
|[cve-2019-14271](vulns_cn/docker/cve-2019-14271.yaml)|docker|container_escape|[9.8](https://nvd.nist.gov/vuln/detail/CVE-2019-14271)|[link](writeups_cnv/docker-cve-2019-14271)|
|[cve-2020-15257](vulns_cn/docker/cve-2020-15257.yaml)|docker/containerd|container_escape|[5.2](https://nvd.nist.gov/vuln/detail/CVE-2020-15257)|[link](writeups_cnv/docker-containerd-cve-2020-15257)|
|[cve-2019-5736](vulns_cn/docker/cve-2019-5736.yaml)|docker/runc|container_escape|[8.6](https://nvd.nist.gov/vuln/detail/CVE-2019-5736)||
|[cve-2019-16884](vulns_cn/docker/cve-2019-16884.yaml)|docker/runc|container_escape|[7.5](https://nvd.nist.gov/vuln/detail/CVE-2019-16884)||
|[cve-2021-30465\*](vulns_cn/docker/cve-2021-30465.yaml)|docker/runc|container_escape|[7.6](https://nvd.nist.gov/vuln/detail/CVE-2021-30465)|[link](writeups_cnv/docker-runc-cve-2021-30465)|
|[cve-2017-1002101](vulns_cn/kubernetes/cve-2017-1002101.yaml)|k8s|container_escape|[9.6](https://nvd.nist.gov/vuln/detail/CVE-2017-1002101)|[link](https://github.com/brant-ruan/cloud-native-security-book/blob/main/appendix/CVE-2017-1002101：突破隔离访问宿主机文件系统.pdf)|
|[cve-2018-1002100](vulns_cn/kubernetes/cve-2018-1002100.yaml)|k8s/kubectl|container_escape|[5.5](https://nvd.nist.gov/vuln/detail/CVE-2018-1002100)||
|[cve-2018-1002105](vulns_cn/kubernetes/cve-2018-1002105.yaml)|k8s|privilege_escalation|[9.8](https://nvd.nist.gov/vuln/detail/CVE-2018-1002105)||
|[cve-2019-11253](vulns_cn/kubernetes/cve-2019-11253.yaml)|k8s|denial_of_service|[7.5](https://nvd.nist.gov/vuln/detail/CVE-2019-11253)||
|[cve-2019-9512](vulns_cn/kubernetes/cve-2019-9512.yaml)|k8s|denial_of_service|[7.5](https://nvd.nist.gov/vuln/detail/CVE-2019-9512)||
|[cve-2019-9514](vulns_cn/kubernetes/cve-2019-9514.yaml)|k8s|denial_of_service|[7.5](https://nvd.nist.gov/vuln/detail/CVE-2019-9514)||
|[cve-2019-9946](vulns_cn/kubernetes/cve-2019-9946.yaml)|k8s|traffic_interception|[7.5](https://nvd.nist.gov/vuln/detail/CVE-2019-9946)||
|[cve-2020-8554](vulns_cn/kubernetes/cve-2020-8554.yaml)|k8s|man_in_the_middle|[5.0](https://nvd.nist.gov/vuln/detail/CVE-2020-8554)||
|[cve-2020-8555](vulns_cn/kubernetes/cve-2020-8555.yaml)|k8s|server_side_request_forgery|[6.3](https://nvd.nist.gov/vuln/detail/CVE-2020-8555)||
|[cve-2020-8557](vulns_cn/kubernetes/cve-2020-8557.yaml)|k8s|denial_of_service|[5.5](https://nvd.nist.gov/vuln/detail/CVE-2020-8557)||
|[cve-2020-8558](vulns_cn/kubernetes/cve-2020-8558.yaml)|k8s|exposure_of_service|[8.8](https://nvd.nist.gov/vuln/detail/CVE-2020-8558)||
|[cve-2020-8559](vulns_cn/kubernetes/cve-2020-8559.yaml)|k8s|privilege_escalation|[6.8](https://nvd.nist.gov/vuln/detail/CVE-2020-8559)||
|[cve-2021-25741](vulns_cn/kubernetes/cve-2021-25741.yaml)|k8s|container_escape|[8.1](https://nvd.nist.gov/vuln/detail/CVE-2021-25741)||
|[cve-2016-5195](vulns_cn/kernel/cve-2016-5195.yaml)|kernel|container_escape|[7.8](https://nvd.nist.gov/vuln/detail/CVE-2016-5195)||
|[cve-2016-8655](vulns_cn/kernel/cve-2016-8655.yaml)|kernel|privilege_escalation|[7.8](https://nvd.nist.gov/vuln/detail/CVE-2016-8655)||
|[cve-2017-6074](vulns_cn/kernel/cve-2017-6074.yaml)|kernel|privilege_escalation|[7.8](https://nvd.nist.gov/vuln/detail/CVE-2017-6074)||
|[cve-2017-7308](vulns_cn/kernel/cve-2017-7308.yaml)|kernel|container_escape|[7.8](https://nvd.nist.gov/vuln/detail/CVE-2017-7308)|[link](writeups_cnv/kernel-cve-2017-7308)|
|[cve-2017-16995](vulns_cn/kernel/cve-2017-16995.yaml)|kernel|privilege_escalation|[7.8](https://nvd.nist.gov/vuln/detail/CVE-2017-16995)||
|[cve-2017-1000112](vulns_cn/kernel/cve-2017-1000112.yaml)|kernel|container_escape|[7.0](https://nvd.nist.gov/vuln/detail/CVE-2017-1000112)|[link](writeups_cnv/kernel-cve-2017-1000112)|
|[cve-2018-18955](vulns_cn/kernel/cve-2018-18955.yaml)|kernel|privilege_escalation|[7.0](https://nvd.nist.gov/vuln/detail/CVE-2018-18955)||
|[cve-2020-14386](vulns_cn/kernel/cve-2020-14386.yaml)|kernel|container_escape|[7.8](https://nvd.nist.gov/vuln/detail/CVE-2020-14386)||
|[cve-2021-22555](vulns_cn/kernel/cve-2021-22555.yaml)|kernel|container_escape|[7.8](https://nvd.nist.gov/vuln/detail/CVE-2021-22555)||
|[kata-escape-2020](vulns_cn/kata-containers/kata-escape-2020.yaml)|kata-containers|container_escape|[6.3](https://nvd.nist.gov/vuln/detail/CVE-2020-2023)/[8.8](https://nvd.nist.gov/vuln/detail/CVE-2020-2025)/[8.8](https://nvd.nist.gov/vuln/detail/CVE-2020-2026)||
|[cap_dac_read_search-container](vulns_cn/configs/cap_dac_read_search-container.yaml)|config|container_escape|-|[link](writeups_cnv/config-cap_dac_read_search-container)|
|[cap_sys_admin-container](vulns_cn/configs/cap_sys_admin-container.yaml)|config|container_escape|-||
|[cap_sys_ptrace-container](vulns_cn/configs/cap_sys_ptrace-container.yaml)|config|container_escape|-||
|[privileged-container](vulns_cn/configs/privileged-container.yaml)|config|container_escape|-|[link](writeups_cnv/config-privileged-container)|
|[mount-docker-sock](vulns_cn/mounts/mount-docker-sock.yaml)|mount|container_escape|-|[link](writeups_cnv/mount-docker-sock)|
|[mount-host-etc](vulns_cn/mounts/mount-host-etc.yaml)|mount|container_escape|-||
|[mount-host-procfs](vulns_cn/mounts/mount-host-procfs.yaml)|mount|container_escape|-|[link](writeups_cnv/mount-host-procfs)|
|[mount-var-log](vulns_cn/mounts/mount-var-log.yaml)|mount|container_escape|-|[link](writeups_cnv/mount-var-log)|



Note:

- Currently writeups are in Chinese.
- You might find that some kernel vulnerabilities are marked as `privilege_escalation`, while others `container_escape`. The essential difference is the payload (get a shell with high privilege or escape first).
    - Thanks to default security mechanisms (e.g. Seccomp, Capabilities) in containers, some kernel vulnerabilities may be hard or almost not to exploit.
    - Hence, vulnerabilities are marked as `container_escape` if we could reproduce the whole process with Metarget, others temporarily marked as `privilege_escalation`.
- For **cve-2021-30465**, after `cnv install cve-2021-30465` (which installs Docker),
    - you'd better install a K8s manually, for exploitation (e.g. `cnv install cve-2018-1002105` or `gadget install k8s --version 1.16.5` with Metarget).

### 4.2 Vulnerable Scenes Related to Cloud Native Applications

These scenes are mainly derived from other open-source projects:

- [Vulhub](https://github.com/vulhub/vulhub)
- [DVWA](https://github.com/digininja/DVWA)

We express sincere gratitude to projects above!

Metarget converts scenes in projects above to *Deployments* and *Services* resources in Kubernetes (thanks to [kompose](https://github.com/kubernetes/kompose)).

To list vulnerable scenes related to cloud native applications supported by Metarget, just run：

```bash
./metarget appv list
```

Note:

- For the deployment of [Confluence's vulnerability CVE-2019-3396](vulns_app/confluence/CVE-2019-3396), you may refer to [Vulhub](https://github.com/vulhub/vulhub/blob/master/confluence/CVE-2019-3396/README.zh-cn.md), while the address of PostgreSQL should be `cve-2019-3396-db`, not `db` in Vulhub.

## 5 DEMO

[![asciicast](https://asciinema.org/a/407107.svg)](https://asciinema.org/a/407107)

## 6 Development Plan

- [x] deployments of basic cloud native components (docker, k8s)
- [x] integrations of vulnerable scenes related to cloud native components
- [x] integrations of RCE scenes in containers
- [ ] automatic construction of multi-node cloud native target cluster
- integrations of other cloud native vulnerable scenes (long term)

## 7 Maintainers

- [@brant-ruan](https://github.com/brant-ruan)
- [@ListenerMoya](https://github.com/ListenerMoya)

## 8 Contribution

One of Metarget's goals is to facilitate more rapid construction of vulnerable environments when vulnerabilities occur. Also, it could be used to construct all the integrated vulnerable scenes whenever you want.

To keep Metarget up-to-date, the vulnerable scenes lists (both `cnv` and `appv`) will be maintained.

*YAML* is used in Metarget to describe & integrate vulnerable scenes. Currently, scenes in two layers, `cnv` (in `vulns_cn/`) and `appv` (in `vulns_app/`), are supported.

Maintenance from the community is appreciated and welcome. Hope that we can gather and share our knowledge and researches in the context of Metarget, and promote the development of cloud native security.

Currently, you can contribute to Metarget in two ways:

1. Submit YAML files of new cloud native vulnerabilities (cnv).
2. Submit YAML files of new cloud native application vulnerabilities (appv).

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## 9 About Logo

It is not a Kubernetes, but a vulnerable infrastructure with three gears which could not work well (vulnerable) :)

## 10 License

Metarget is licensed under Apache License 2.0. See [LICENSE](LICENSE) for the full license text.

## 11 Events

### KCon 2021 Arsenal

- URL: http://kcon.knownsec.com/2021/#/arsenal

### OpenInfra Days Asia 2021

- Topic: Metarget: Auto-construction of Vulnerable Cloud Native Infrastructure
- URL: https://2021.openinfra.asia/schedule.html
- Video: https://www.youtube.com/watch?v=43UvCHjn8wA

### OpenInfra Days China 2021

- Topic: Metarget：构建云原生基础设施靶场
- URL: https://pages.segmentfault.com/openinfra-2021/agenda
