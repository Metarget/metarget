# Contributing Guidelines

One of Metarget's goals is to facilitate more rapid construction of vulnerable environments when vulnerabilities occur. Also, it could be used to construct all the integrated vulnerable scenes whenever you want.

To keep Metarget up-to-date, the vulnerable scenes lists (both `cnv` and `appv`) will be maintained. *YAML* is used in Metarget to describe & integrate vulnerable scenes. Currently, scenes in two layers, `cnv` (in `vulns_cn/`) and `appv` (in `vulns_app/`), are supported.

Maintenance from the community is appreciated and welcome. Hope that we can gather and share our knowledge and researches in the context of Metarget, and promote the development of cloud native security.

Currently, you can contribute to Metarget in two ways:

1. Submit YAML files of new cloud native vulnerabilities (cnv).
2. Submit YAML files of new cloud native application vulnerabilities (appv).

You may find templates below useful while contributing.

## Templates of Cloud Native Vulnerable Scenes


### cve-2019-5736: Container Escape Related to runC

```yaml
name: cve-2019-5736			# vulnerability name (lowercase)
class: docker/runc			# vulnerable component (lowercase)
type: container_escape			# vulnerability type
dependencies:				
  - name: docker-ce			# component's name (installed with apt-get by default)
    version: 18.03.1			# vulnerable version
    versions:			
      - ~				# vulnerable version range (currently unused; set to ~)
links:					# references
  - https://nvd.nist.gov/vuln/detail/CVE-2019-5736
  - https://github.com/Frichetten/CVE-2019-5736-PoC
```

### cve-2017-1002101: Container Escape Related to Kubernetes

```yaml
name: cve-2017-1002101			# vulnerability name (lowercase)
class: kubernetes			# vulnerable component (lowercase)
type: container_escape			# vulnerability type
dependencies:				
  - name: kubectl		    	# name of K8s component (installed with apt-get by default)
    version: 1.9.3		  	# vulnerable version
    versions: ~				# vulnerable version range (currently unused; set to ~)
  - name: kubelet
    version: 1.9.3
    versions: ~
  - name: kubeadm
    version: 1.9.3
    versions: ~
links:					# references
  - https://nvd.nist.gov/vuln/detail/CVE-2017-1002101
  - https://makocchi.medium.com/kubernetes-cve-2017-1002101-en-5a30bf701a3e
```

### mount-docker-sock: Container Escape with mounted docker.sock

All vulnerable scenes related to danger mount or danger configurations compose of two files:

1. description file, e.g. `mount-docker-sock.yaml`
2. resource file, e.g. `pods/mount-docker-sock.yaml`

```yaml
# description file
name: mount-docker-sock		# vulnerability name (lowercase)
class: mount			# vulnerable behavior (lowercase, mount or config)
type: container_escape		# vulnerability type
dependencies:				
  yamls:			# resource file in pods/
    - pods/mount-docker-sock.yaml
```

```yaml
# resource file in pods/
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

## Templates of Cloud Native Applications Scenes

Many application vulnerabilities (mainly RCE) in Metarget come from [Vulhub](https://github.com/vulhub/vulhub).

Vulnerabilities in [Vulhub](https://github.com/vulhub/vulhub) start up from `docker-compose.yml` file. We use [kompose](https://github.com/kubernetes/kompose) to convert that file into resource files in Kubernetes.

You could also integrate other excellent containerized vulnerability environment into Metarget (if the origin license allows), and unify the managements with Metarget (e.g. manage all scenes in the same cluster).

### CVE-2012-1823

`docker-compose.yaml` before modification:

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

Prefix service name with vulnerability ID, e.g. php -> cve-2012-1823-php (lowercase).

`docker-compose.yml` after modification:

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

Then use `docker_to_k8s.sh` in `tools/` to convert the file above into Kubernetes resource files. `docker-compose-yaml-backup.yaml` including Service and deployment, and `desc.yaml` files will be generated in `vul_app/`:

```
bash docker_to_k8s.sh list.txt
INFO Kubernetes file "vul_app/cve-2012-1823/docker-compose-yaml-backup.yaml" created
```

`desc.yaml`:

```
name: cve-2012-1823		# vulnerability name (lowercase)
class: php			# vulnerable component (lowercase)
hostPath: true			# need volume mount or not
type: rce			# vulnerability type
dependencies:			
  yamls:
    - cve-2012-1823-php-deployment.yaml
    - cve-2012-1823-php-service.yaml
links:				# references
  - https://github.com/vulhub/vulhub/tree/master/php/CVE-2012-1823
```

Note:

- Prefix of `hostPath` in deployment file should be stripped and finally become something like `php/CVE-2012-1823/www`.
- Files to be mounted (e.g. `www/`) should be put into the same directory of `desc.yaml`.
- Split `docker-compose-yaml-backup.yaml` into service and deployment files, and add fields like namespace if needed.

Files structure:

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

## Submit PR

After preparations of description files, you can put them into `vulns_cn/` or `vulns_app/` directories.

Contributions following the standardized PR process in open-source community are encouraged. Please attach enough and exact descriptions.

Thanks for your interest on Metarget. We will take your PRs seriously.

