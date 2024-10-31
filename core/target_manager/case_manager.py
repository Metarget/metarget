from kubernetes import client, config
import os

# 加载 Kubernetes 配置文件（通常是 $HOME/.kube/config）
config.load_kube_config()

# 创建核心 API 客户端对象
api_instance = client.CoreV1Api()

# 指定要传输的脚本文件名和路径
script_file = "install_k8s_worker.sh"
script_path = "../../../tools/"  # 这里填写脚本所在的目录路径

# 读取脚本内容
with open(os.path.join(script_path, script_file), "r") as file:
    script_content = file.read()

# 创建 Pod 对象
pod = client.V1Pod(
    metadata=client.V1ObjectMeta(name="run-script"),
    spec=client.V1PodSpec(
        containers=[
            client.V1Container(
                name="run-script-container",
                image="busybox",  # 这里选择一个带有 sh 的镜像，如 busybox
                command=["sh", "-c", f"echo '{script_content}' > /mnt/{script_file} && sh /mnt/{script_file}"],
                volume_mounts=[client.V1VolumeMount(mount_path="/mnt", name="script-volume")],
            )
        ],
        volumes=[client.V1Volume(name="script-volume", empty_dir=client.V1EmptyDirVolumeSource())],
        restart_policy="Never",
    ),
)


# 创建 Pod
api_instance.create_namespaced_pod(namespace="default", body=pod)
