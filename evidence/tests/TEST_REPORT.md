# m10 本地模式测试记录

执行日期：2026-11-22（Asia/Shanghai）

## 自动化测试

命令：

```bash
.venv/bin/pytest -q
```

结果：`8 passed`。

覆盖内容：

- 演示 CSV 576 行读取、清洗和处理。
- K-Means 工况聚类结果存在。
- 孤立森林异常结果存在。
- 缺少必需字段时拒绝输入。
- 重复时间保留最后记录并计数。
- 负辐照度/功率记录被拒绝并计数。
- 前端文件、页面模块、启动入口和使用说明存在。
- PVDAQ 真实数据规范化切片符合同一输入契约（1686 行有效记录），并完成本地算法处理断言。

## API 端到端冒烟

使用 FastAPI TestClient 和临时 SQLite 数据目录验证：

- `/api/health`、首页、`/static/app.js`、`/static/app.css`、`/data/sample/pv_demo.csv` 返回 200。
- 导入演示 CSV：576 行有效记录。
- 本地处理：3 类工况，576 条结果，29 条异常。
- 运行总览、记录列表和告警列表可查询。
- 告警数量：29 条。

## 真实数据本地联调

使用 `data/real/pvdaq_2107_2022-06_normalized.csv` 在临时 SQLite 数据库中运行同一处理链：

- 导入：1686 行有效记录，0 行无效，0 行重复。
- 运行：3 类工况，85 条异常，85 条告警。
- 详细证据：`evidence/runtime/api/real_pvdaq_local_integration.json`。

## Docker 集群联调

- Docker Compose 集群启动成功：MySQL 8.4、HDFS NameNode/DataNode、Spark master/worker、API。
- PVDAQ 1686 行经 Spark 处理，HDFS 写入/回读 1686 行，MySQL 持久化 1686 条 records、85 条 alerts。
- 详细证据：evidence/runtime/api/cluster_integration.json（最终回归 run_id=7，HDFS probe 20261122T082612Z）。

## 未验证
- Windows 10/11 x64 原生构建、解压、双击启动和停止。
- 长期并发、真实场站数据泛化效果。
