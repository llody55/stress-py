# Python Resource Stresser (Multi-Arch)

一个 **极轻量、纯 Python 实现** 的 CPU + 内存**系统资源压力测试工具**，用于模拟CPU和内存的高负载场景，完美用于压测、混沌工程、资源争抢测试！。

- **镜像仅 41MB**
- **原生支持 `amd64` 和 `arm64`**
- **精确控制 CPU 使用率（1%~99%）**
- **常驻内存，防 swap**
- **通过环境变量零配置**
- **docker-compose 一键启动**

---

## 特性对比

| 特性                          | 支持情况       |
| ----------------------------- | -------------- |
| 多核 CPU 精确百分比           | Yes            |
| 内存常驻（RSS）               | Yes            |
| 定时自动退出                  | Yes            |
| 零依赖（纯标准库）            | Yes            |
| 跨平台（Linux/macOS/Windows） | Yes            |
| 多架构（x86_64/aarch64）      | Yes            |
| 启动时间                      | < 0.3s         |
| 镜像大小                      | **41MB** |



## 环境变量

* CPU_PERCENT：CPU占用百分比（0-100，默认50）。
* MEM_MB：内存占用MB（默认1024）。
* DURATION：运行秒数（默认无限，直到Ctrl+C）。

---

## 快速开始（docker-compose）

### 1. 项目结构

```bash
stress-py/
├── Dockerfile
├── stress-py.yaml
└── stress-py.py
```

### 2.构建打包方法

```bash
root@VM-0-3-ubuntu:~/stress-py# docker buildx build --push --platform linux/amd64,linux/arm64 --tag llody/stress-py:latest --tag llody/stress-py:v0.2 .
```

### 3.部署启动方式

```bash
# 测试启动
root@VM-0-3-ubuntu:~/stress-py# export CPU_PERCENT=80; export MEM_MB=2048; export DURATION=300; python3 stress-py.py 

# 容器启动
root@VM-0-3-ubuntu:~/stress-py# docker-compose -p stress-py -f stress-py.yaml up -d
```
