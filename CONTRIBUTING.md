# 参与者指南

Metarget的初衷之一是方便安全研究人员在漏洞出现的第一时间快速搭建漏洞环境（进一步地，随时随地搭建已集成的任意漏洞环境）。

为了保持靶场的“新鲜性”，Metarget的漏洞列表将持续更新。Metarget采用YAML文件的形式描述并集成漏洞环境，目前提供“云原生组件漏洞”和“云原生应用漏洞”两个层次的环境，对应描述文件分别位于`vulns_cn`和`vulns_app`目录下。

我们希望并鼓励大家参与维护Metarget，一起推进项目，借助Metarget沉淀、分享我们的研究所得，共同促进云原生安全研究发展。

目前来说，您可以通过以下两种方式参与到项目中：

1. 提交“云原生组件漏洞”的YAML描述文件。
2. 提交“云原生应用漏洞”的YAML描述文件。

为了帮助大家参与到项目中，我们为漏洞环境的描述文件提供了模板作为参照。

## “云原生组件漏洞”模板

以下是几个云原生组件漏洞YAML文件的示例：

### cve-2019-5736：runC相关容器逃逸漏洞

```yaml
name: cve-2019-5736		  # 漏洞名称（统一小写）
class: docker/runc		  # 漏洞相关组件（统一小写）
type: container_escape	# 漏洞类型
dependencies:			      # 漏洞依赖环境
  - name: docker-ce		  # 组件名称（默认使用apt-get安装）
    version: 18.03.1	  # 存在漏洞的版本
    versions:			
      - ~				        # 漏洞版本范围（该字段暂未使用，置 ~ 即可）
links:					        # 漏洞参考链接（可放置帮助了解该漏洞的链接，如漏洞库信息、issue信息、首发博客等）
  - https://nvd.nist.gov/vuln/detail/CVE-2019-5736
  - https://github.com/Frichetten/CVE-2019-5736-PoC
```

### cve-2017-1002101：Kubernetes的文件系统逃逸漏洞

```yaml
name: cve-2017-1002101	# 漏洞名称（统一小写）
class: kubernetes		    # 漏洞相关组件（统一小写）
type: container_escape	# 漏洞类型
dependencies:			      # 漏洞依赖环境
  - name: kubectl		    # Kubernetes相关组件名称
    version: 1.9.3		  # 存在漏洞的版本，kubectl、kubelet、kubeadm三者版本一致
    versions: ~			    # 漏洞版本范围（该字段暂未使用，置 ~ 即可）
  - name: kubelet
    version: 1.9.3
    versions: ~
  - name: kubeadm
    version: 1.9.3
    versions: ~
links:					        # 漏洞参考链接（可放置帮助了解该漏洞的链接，如漏洞库信息、issue信息、首发博客等）
  - https://nvd.nist.gov/vuln/detail/CVE-2017-1002101
  - https://makocchi.medium.com/kubernetes-cve-2017-1002101-en-5a30bf701a3e
```

### mount-docker-sock：docker.sock危险挂载导致容器逃逸

这类危险配置、危险挂载脆弱场景由两个文件组成：`mount-docker-sock.yaml`（漏洞说明文件）和`pods/`目录下的同名文件（Kubernetes资源文件）：

```yaml
# 漏洞说明文件
name: mount-docker-sock		# 漏洞名称
class: mount				      # 漏洞相关行为
type: container_escape		# 漏洞类型
dependencies:				
  yamls:					        # pods/ 目录下的资源声明文件路径
    - pods/mount-docker-sock.yaml
```

```yaml
# pods/ 目录下的资源声明文件
apiVersion: v1
kind: Pod
metadata:
  name: mount-docker-sock
  namespace: metarget
spec:
  containers:
  - name: ubuntu
    image: ubuntu:latest
    imagePullPolicy: IfNotPresent
    # Just spin & wait forever
    command: [ "/bin/bash", "-c", "--" ]
    args: [ "while true; do sleep 30; done;" ]
    volumeMounts:
    - name: docker-sock
      mountPath: /var/run/docker.sock
  volumes:
    - name: docker-sock
      hostPath:
        path: /var/run/docker.sock
```

## “云原生应用漏洞”模板

Metarget中对接了许多[Vulhub](https://github.com/vulhub/vulhub)项目中的漏洞环境（以RCE环境为主），再次对其表示感谢！

[Vulhub](https://github.com/vulhub/vulhub)中的漏洞环境以`docker-compose.yml`文件启动，我们使用[kompose](https://github.com/kubernetes/kompose)将其转换为Kubernetes环境下的资源声明文件。下面是一个转换示例。

您可以以类似的方式将其他优秀容器化漏洞环境开源项目的内容提交至Metarget（在原项目开源许可证允许的前提下），借助Metarget来对所有这些环境进行统一管理（在一个集群中进行创建和销毁）。

### CVE-2012-1823

原`docker-compose.yaml`文件如下：

```yaml
version: '2'
services:
 php:
   image: vulhub/php:5.4.1-cgi
   volumes:
    - ./www:/var/www/html
   ports:
    - "8080:80"
```

为了满足Metarget搭建复杂漏洞环境的需求，需要更改创建的services资源，使其具有唯一性，方法是在漏洞的services名称前加上漏洞编号，如php更改为cve-2012-1823-php（所有字符均为小写），修改后的`docker-compose.yml`文件内容为：

```yaml
version: '2'
services:
 cve-2012-1823-php:
   image: vulhub/php:5.4.1-cgi
   volumes:
    - ./www:/var/www/html
   ports:
    - "8080:80"
```

然后使用tools下的`docker_to_k8s.sh`快速将其转换为Kubernetes资源文件，运行后会在`vul_app`目录下生成service、deployment和`desc.yaml`文件：

```
bash docker_to_k8s.sh list.txt
INFO Kubernetes file "vul_app/cve-2012-1823/cve-2012-1823-php-service.yaml" created
INFO Kubernetes file "vul_app/cve-2012-1823/cve-2012-1823-php-deployment.yaml" created
```

`desc.yaml`文件内容如下：

```
name: cve-2012-1823		# 漏洞名称
class: php				    # 漏洞组件
hostPath: true			  # 是否存在卷挂载
type: rce				      # 漏洞类型
dependencies:			    # 漏洞搭建依赖文件
  yamls:
    - cve-2012-1823-php-deployment.yaml
    - cve-2012-1823-php-service.yaml
links:					      # 漏洞参考文献
  - https://github.com/vulhub/vulhub/tree/master/php/CVE-2012-1823
```

注意：

- deployment文件中`hostPath`内容会生成程序相关路径，删除前缀部分使其为`php/CVE-2012-1823/www`。
- 原目录下文件——即`www/`目录内容应一同拷贝至`desc.yaml`文件同目录下。

最终文件目录结构如下：

```
.
└── php
    └── CVE-2012-1823
        ├── cve-2012-1823-php-deployment.yaml
        ├── cve-2012-1823-php-service.yaml
        ├── desc.yaml
        └── www
            ├── index.php
            └── info.php
```

## 提交PR

在完成描述文件的准备工作后，就可以将上述描述文件放入对应的目录中（云原生组件漏洞在`vulns_cn/`目录下，云原生应用漏洞在`vulns_app`目录下，放在具体的分类路径下面即可）。

我们鼓励贡献者按照社区规范PR流程进行贡献，在PR时请写好备注说明。

十分感谢大家对Metarget项目的关注，我们将认真对待大家的PR并及时反馈。

