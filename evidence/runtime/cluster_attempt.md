# Cluster 联调过程记录（2026-11-22）

- Docker Desktop 服务可用：Docker Engine 29.9.3，Compose v5.7.0，主机架构 arm64。
- 失败尝试 1：`bitnami/spark:3.5.3` manifest unknown；改用官方 `apache/spark:3.5.3-python3`。
- 失败尝试 2：`python:3.11-slim` 在 Debian trixie 中无法找到 `openjdk-17-jre-headless`；API 镜像改为 Spark 官方镜像，并使用 Python 3.8 兼容依赖集。
- 失败尝试 3：容器内 pypi.org TLS 连接不稳定；构建使用公开清华 PyPI 镜像完成依赖安装。
- 失败尝试 4：Spark 基础镜像未默认暴露 PySpark 到 API Python 路径；补充 `PYTHONPATH`。
- 失败尝试 5：MySQL 8.4 的 caching_sha2_password 需要 `cryptography`；补充依赖；MySQL 索引涉及 TEXT 字段，改为 VARCHAR 后启动成功。
- 端口冲突：主机 8000 曾被占用，Compose 支持 `M10_API_HOST_PORT` 覆盖；本次成功验证最终使用 8000。

成功证据详见同目录 `cluster_integration.json`：API 真实 PVDAQ 数据集 1686 行经 Spark standalone 处理，HDFS 写入并回读 1686 行，MySQL 保存 1686 条记录与 85 条异常，Spark UI 显示 1 个 worker。
