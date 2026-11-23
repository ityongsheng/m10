# m10 第三方来源与许可记录

本文件只记录已经确认或待核验的来源，不把示例代码、搜索结果或计划依赖写成已采用实现。

PVDAQ 目录核验入口：`https://catalog.data.gov/dataset/photovoltaic-data-acquisition-pvdaq-public-datasets`（核验日期：2026-11-22）。

| 来源 | 用途 | 许可/来源状态 | 采用边界 |
|---|---|---|---|
| NREL / DOE PVDAQ Public Datasets | 真实光伏时序数据 | Data.gov/OEDI 目录记录公开访问、CC BY 4.0；system 2107 的原始 CSV、元数据、下载日期和 SHA-256 保存在 `data/real/` 与 `evidence/data/pvdaq_2107.sha256` | 已下载并规范化 2022-06 切片；`module_temp_c` 是因源数据没有模块温度通道而采用的 ambient proxy，论文中单独标注 |
| Apache Spark 3.x | 分布式清洗、特征处理、K-Means | Apache License 2.0 | 使用 `apache/spark:3.5.3-python3`；本机 arm64 联调显示 1 个 worker，证据见 `evidence/runtime/cluster_integration.json` |
| Apache Hadoop 3.x | HDFS 开发联调 | Apache License 2.0 | 使用 `bde2020/hadoop-namenode/datanode:2.0.0-hadoop3.2.1-java8`；仅作为开发/联调服务，不把 Docker 验证写成 Windows 验收 |
| MySQL Community Server 8.4 | 关系型持久化 | GPLv2；按发行条款使用 | Docker 联调真实保存 1686 条记录；便携模式的回退存储单独说明 |
| FastAPI | 本地 API 和静态资源服务 | MIT | 只使用公开发行版，锁定版本并保存依赖清单 |
| pandas / scikit-learn | 数据适配和孤立森林实现支持 | BSD 3-Clause | 便携模式按 `requirements.txt`，集群镜像按 Python 3.8 兼容的 `docker/requirements-cluster.txt` |

## 当前未采用

- 未复制任何未核实许可证的 GitHub 项目代码。
- 未把其他项目（例如 m09）的业务代码、数据或论文内容复制到 m10。
- 未把 PVDAQ 原始文件冒充现场自有数据；系统同时保留 `synthetic_demo` 标记和真实数据来源标记。
