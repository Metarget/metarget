# 云原生组件漏洞（CNV）Writeups

为了方便大家将研究成果固化，本目录以脆弱场景为单位收集相关场景的writeups。

每新增一个场景，请在本目录下创建一个新的目录来放置writeup。目录的命名模式为`分类-脆弱场景名`，以实现扁平化，具体可参考本目录下已有目录的命名作为示例。

目录的基本内容暂定为：

```
.
├── README.md
├── images/
├── other_dirs/
└── other_files
```

后续如添加英文翻译，再进行统一变动。目前为便于导航，将writeup直接写入`README.md`即可。

建议Writeup的大纲及内容如下：

```markdown
# 题目

## 场景介绍

## 环境搭建

本部分给出使用Metarget搭建目标环境的方法。

## 漏洞复现

## 参考文献
```

其他诸如漏洞原理等额外内容可酌情附加。

可参考示例：[挂载宿主机Procfs系统导致容器逃逸](https://github.com/brant-ruan/metarget/tree/master/writeups_cnv/mount-host-procfs)。