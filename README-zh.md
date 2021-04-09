<p align="center">
  <img src="images/metarget-logo.svg" alt="metarget-logo" height="250" />
</p>

[中文](README-zh.md) | [English](README.md)

## 1 项目介绍

Metarget的名称来源于`meta-`（元）加`target`（目标，靶机），是一个脆弱基础设施自动化构建框架，主要用于快速、自动化搭建从简单到复杂的脆弱云原生靶机环境。

### 1.1 项目的缘起

在研究漏洞时，我们经常会发现“环境搭建”这一步骤本身就会占用大量的时间，与之相比，真正测试PoC、ExP的时间可能非常短。由于许多官方镜像在国内的网络环境下并不方便获得，加上云原生组件自身的复杂性，在云原生安全领域，前述问题尤为明显。

与此同时，我们也能看到，开源社区涌现出一些优秀的安全项目，如[Vulhub](https://github.com/vulhub/vulhub)、[VulApps](https://github.com/Medicean/VulApps)等，将漏洞场景打包成镜像，方便研究人员开箱即用。

然而，这些项目主要针对应用程序漏洞。那么，如果我们需要研究的是Docker、Kubernetes、操作系统内核等底层基础自身的漏洞呢？这又回到了前面的环境搭建问题。

我们希望Metarget能够在一定程度上解决这个问题，致力于底层基础设施的脆弱场景自动化构建。在此之上，我们还希望Metarget实现对云原生环境多层次脆弱场景的自动化构建。

### 1.2 “安装漏洞”

在Metarget项目中，我们提出“安装漏洞”、“安装脆弱场景”的概念。漏洞为什么不能像软件一样直接安装呢？程序为实，漏洞为虚；软件为满，漏洞为缺。那么只需换一种视角，视虚为实，以缺为满，我们完全可以像安装软件一样安装漏洞——以安全研究、攻防实战为目的。

具体来说，我们希望：

- 执行`metarget cnv install cve-2019-5736`直接将带有CVE-2019-5736漏洞的Docker安装在服务器上
- 执行`metarget cnv install cve-2018-1002105`直接将带有CVE-2018-1002105漏洞的Kubernetes安装在服务器上
- 执行`metarget cnv install cve-2016-5195`直接将系统切换为带有脏牛漏洞的内核

有点酷了，是不是？不要讲那么多，不要RTFM，我只想一键搞定环境泡杯咖啡，然后开始漏洞研究。

在这个基础上，我们还希望：

- 攻防相关的同学能够借助Metarget快速搭建从简单到复杂的云原生靶场环境，从而积累云原生环境下的渗透经验
- 执行`metarget appv install dvwa`直接安装一个[DVWA](https://github.com/digininja/DVWA)靶机到脆弱的底层基础设施上
- 执行`metarget appv install thinkphp-5-0-23-rce`直接安装一个ThinkPHP RCE漏洞环境到脆弱的底层基础设施上

在一个刚刚装好的Ubuntu操作系统上，安装Metarget，然后简单执行五条指令就能完成一个多层次脆弱靶机场景搭建：

```bash
./metarget cnv install cve-2016-5195 # 内核漏洞层面容器逃逸
./metarget cnv install cve-2019-5736 # Docker层面容器逃逸
./metarget cnv install cve-2018-1002105 --domestic # Kubernetes单节点集群（包含权限提升漏洞）
./metarget cnv install privileged-container # 部署一个特权容器
./metarget appv install dvwa # 部署一个DVWA靶机
```

RCE、容器逃逸、横向移动、隐蔽持久化，统统打包送给你。

在这个基础上，我们还希望......

先留个悬念，请拭目以待 :)

注意：

本项目目的在于自动化构建**用于信息安全研究的脆弱场景**，不保证生成的场景（如自动化安装的Kubernetes）的安全性，不推荐将本项目用于正常业务组件、集群的安装和部署。

## 2 使用方法

### 2.1 基本操作

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

执行`./metarget gadget list`了解当前支持的云原生组件。

### 2.2 管理云原生组件

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

#### 2.2.1 示例：安装指定版本Docker

执行以下命令：

```bash
./metarget gadget install docker --version 18.03.1
```

执行成功后，版本为18.03.1的Docker将被安装在当前Linux系统上。

#### 2.2.2 示例：安装指定版本Kubernetes

执行以下命令：

```bash
./metarget gadget install k8s --version 1.16.5
```

执行成功后，版本为1.16.5的单节点Kubernetes将被安装在当前Linux系统上。

注意：

Kubernetes通常需要配置大量参数，Metarget项目提供了部分参数供指定：

```
  -v VERSION, --version VERSION
                        gadget version
  --cni CNI             cni plugin, flannel by default
  --pod-network-cidr POD_NETWORK_CIDR
                        pod network cidr, default cidr for each plugin by
                        default
  --taint-master        taint master node or not
  --domestic            magic
  --http-proxy HTTP_PROXY
                        set proxy
  --no-proxy NO_PROXY   do not proxy for some sites
```

**考虑到特殊的网络环境，国内的朋友需要指定以下两个参数之一，以顺利完成Kubernetes的部署：**

- http-proxy：用于从官方源下载Kubernetes系统组件镜像的代理
- domestic：当使用该选项时，Metarget将自动从国内源（阿里云）下载Kubernetes系统组件镜像，无需代理

如果主机能够直接访问Kubernetes官方源，则不必指定这些参数。

**Metarget支持部署多节点Kubernetes集群环境，如果想要部署多节点，在单节点部署成功后，将`tools`目录下生成的`install_k8s_worker.sh`脚本复制到每个工作节点上执行即可。**

#### 2.2.3 示例：安装指定版本Linux内核

执行以下命令：

```bash
./metarget gadget install kernel --version 5.7.5
```

执行成功后，版本为5.7.5的内核将被安装在当前Linux系统上。

注意：

当前Metarget采用两种方法安装内核：

1. apt
2. 在apt无备选包的情况下，直接远程下载Ubuntu deb内核包进行安装

内核安装成功后需要重新启动系统以生效，Metarget会提醒是否自动重启系统。

### 2.3 管理“云原生组件”的脆弱场景

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

执行`./metarget cnv list`了解当前支持的云原生组件脆弱场景。

#### 2.3.1 示例：CVE-2019-5736

执行以下命令：

```bash
./metarget cnv install cve-2019-5736
```

执行成功后，存在CVE-2019-5736漏洞的Docker将被安装在当前Linux系统上。

#### 2.3.2 示例：CVE-2018-1002105

执行以下命令：

```bash
./metarget cnv install cve-2018-1002105
```

执行成功后，存在CVE-2018-1002105漏洞的Kubernetes单节点集群将被安装在当前Linux系统上。

**考虑到特殊的网络环境，国内的朋友需要指定以下两个参数之一，以顺利完成Kubernetes相关脆弱环境的部署：**

- http-proxy：用于从官方源下载Kubernetes系统组件镜像的代理
- domestic：当使用该选项时，Metarget将自动从国内源（阿里云）下载Kubernetes系统组件镜像，无需代理

如果主机能够直接访问Kubernetes官方源，则不必指定这些参数。

#### 2.3.3 示例：CVE-2016-5195

执行以下命令：

```bash
./metarget cnv install cve-2016-5195
```

执行成功后，存在CVE-2016-5195漏洞的Linux内核将被安装在当前系统上。

### 2.4 管理“云原生应用”的脆弱场景

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

执行`./metarget appv list`了解当前支持的云原生应用脆弱场景。

注意：

在构建云原生应用的脆弱场景前，需要先安装Docker及Kubernetes，可以使用Metarget相关命令来完成。

#### 2.4.1 示例：DVWA

执行以下命令：

```bash
./metarget appv install dvwa
```

执行成功后，DVWA将以Deployment和Service资源的形式被部署在当前集群中。

### 2.5 管理“云原生靶机集群”的脆弱场景

正在开发，暂不支持。

## 3 安装方法

### 3.1 依赖项

- Ubuntu 16.04或18.04（未测试）
- Python >= 3.5
- pip3

### 3.2 从源码安装

拉取仓库，安装必要库文件：

```bash
git clone https://github.com/brant-ruan/metarget.git
cd metarget/
pip install -r requirements.txt
```

使用Metarget，搭建脆弱场景，例如：

```bash
./metarget cnv install cve-2019-5736
```

### 3.3 从PyPI安装

暂不支持。

## 4 场景列表

### 4.1 云原生组件脆弱场景

|场景名称|涉及组件|场景类型|状态|
|:-:|:-:|:-:|:-:|
|[cve-2018-15664](vulns_cn/docker/cve-2018-15664.yaml)|docker|容器逃逸|✅|
|[cve-2019-13139](vulns_cn/docker/cve-2019-13139.yaml)|docker|命令执行|✅|
|[cve-2019-14271](vulns_cn/docker/cve-2019-14271.yaml)|docker|容器逃逸|✅|
|[cve-2020-15257](vulns_cn/docker/cve-2020-15257.yaml)|docker/containerd|容器逃逸|✅|
|[cve-2019-5736](vulns_cn/docker/cve-2019-5736.yaml)|docker/runc|容器逃逸|✅|
|[cve-2017-1002101](vulns_cn/kubernetes/cve-2017-1002101.yaml)|kubernetes|容器逃逸|✅|
|[cve-2018-1002105](vulns_cn/kubernetes/cve-2018-1002105.yaml)|kubernetes|权限提升|✅|
|[cve-2019-11253](vulns_cn/kubernetes/cve-2019-11253.yaml)|kubernetes|拒绝服务|✅|
|[cve-2019-9512](vulns_cn/kubernetes/cve-2019-9512.yaml)|kubernetes|拒绝服务|✅|
|[cve-2019-9514](vulns_cn/kubernetes/cve-2019-9514.yaml)|kubernetes|拒绝服务|✅|
|[cve-2020-8558](vulns_cn/kubernetes/cve-2020-8558.yaml)|kubernetes|服务暴露|✅|
|[cve-2016-5195](vulns_cn/kernel/cve-2016-5195.yaml)|kernel|容器逃逸|✅|
|[cve-2020-14386](vulns_cn/kernel/cve-2020-14386.yaml)|kernel|容器逃逸|✅|
|cap_dac_read_search-container|危险配置|容器逃逸||
|cap_sys_admin-container|危险配置|容器逃逸||
|cap_sys_ptrace-container|危险配置|容器逃逸||
|[privileged-container](vulns_cn/configs/privileged-container.yaml)|危险配置|容器逃逸|✅|
|[mount-docker-sock](vulns_cn/mounts/mount-docker-sock.yaml)|危险挂载|容器逃逸|✅|
|[mount-host-etc](vulns_cn/mounts/mount-host-etc.yaml)|危险挂载|容器逃逸|✅|
|[mount-host-procfs](vulns_cn/mounts/mount-host-procfs.yaml)|危险挂载|容器逃逸|✅|
|kata-escape-2020|kata-containers|容器逃逸||

### 4.2 云原生应用脆弱场景

应用脆弱场景主要集成自开源社区中的其他项目：

- [Vulhub](https://github.com/vulhub/vulhub)
- [DVWA](https://github.com/digininja/DVWA)

真诚感谢以上开源项目为安全社区做出的贡献！

Metarget将以上项目中的靶机统一转化为Kubernetes中的Deployment和Service资源，使管理更加方便（感谢[kompose](https://github.com/kubernetes/kompose)）。

可执行以下命令查看Metarget支持构建的应用脆弱场景：

```bash
./metarget appv list
```

## 5 开发计划

- [x] 实现基本云原生组件安装部署
- [x] 实现经典云原生漏洞场景集成
- [x] 实现容器内RCE脆弱场景集成
- [ ] 实现其他云原生脆弱场景集成
- [ ] 实现多节点云原生靶场集群自动化生成

## 6 关于Logo

Metarget logo的灵感来源于Kubernetes的logo，我们将Kubernetes的舵作为齿轮，三个齿轮组成一个正在运转的基础设施系统。然而，如果仔细观察，会发现齿轮的方向是矛盾的，系统无法正常运转（vulnerable）。
