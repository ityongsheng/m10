# Docker 联调说明

`docker-compose.yml` 的 `cluster` profile 包含 MySQL 8.4、Hadoop HDFS 3.2.1、Spark 3.5.3 和 API 服务。镜像版本和镜像来源必须在 `THIRD_PARTY.md` 中维护。2026-11-22 已在本机 arm64 Docker Desktop 完成真实 PVDAQ 切片的 API→Spark→HDFS→MySQL 联调，证据见 `evidence/runtime/api/cluster_integration.json`。

首次使用先将 `docker/.env.example` 复制为 `docker/.env`，设置两个仅供本机联调的数据库密码。`docker/.env` 被 Git 忽略。

```bash
cp docker/.env.example docker/.env
docker compose --env-file docker/.env -f docker/docker-compose.yml --profile cluster up --build
```

如果主机的 8000 端口已被占用，可临时改 API 映射端口：

```bash
M10_API_HOST_PORT=18000 docker compose --env-file docker/.env -f docker/docker-compose.yml --profile cluster up --build
```

停止：

```bash
docker compose --env-file docker/.env -f docker/docker-compose.yml --profile cluster down
```

本次联调结果：Spark standalone 1 个 worker，真实 PVDAQ 1686 行经 Spark 处理并写入/回读 HDFS 1686 行，MySQL 保存 1686 条记录和 85 条异常。Docker 运行成功只证明当前 arm64 容器环境联调通过，不代表 Windows x64 客户验收通过；Hadoop 镜像在 arm64 主机上通过 Docker amd64 仿真运行。数据库密码仅为本地联调值，不得写入生产或共享环境。
