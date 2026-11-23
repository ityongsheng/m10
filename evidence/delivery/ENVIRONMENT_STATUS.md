# m10 环境与交付状态

## 已验证

- 本机 macOS Apple Silicon arm64：Python 3.13.3、FastAPI、SQLite、本地算法管线。
- Docker Compose 配置语法：`docker compose -f docker/docker-compose.yml --profile cluster config` 通过。
- Docker Compose 集群已实测：MySQL 8.4、HDFS NameNode/DataNode、Spark master/worker 和 API 均运行；真实 PVDAQ 1686 行经 Spark 处理，HDFS 写入/回读 1686 行，MySQL 保存 1686 条记录与 85 条异常。详见 `evidence/runtime/api/cluster_integration.json`。
- 本地模式端到端：导入、清洗、K-Means、孤立森林、数据库写入、API 查询和静态页面资源。
- 自动化测试：8 项通过。

## 未验证

- Windows 10/11 x64 构建与客户机器验收。
- 无开发依赖环境的离线 ZIP。

未验证项目不写入论文的已完成结果，也不作为“客户双击即可使用”的证据。
