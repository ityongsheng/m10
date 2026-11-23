# m10 交付清单

## 程序

- 本地启动入口：`start.cmd`、`stop.cmd`、`launcher.json`
- FastAPI 服务：`backend/`
- 本地处理与 Spark 适配：`pipeline/`
- SQLite/MySQL 数据访问和表结构：`backend/db.py`、`database/schema.sql`
- 离线前端工作台：`frontend/`
- 固定种子合成演示数据：`data/sample/pv_demo.csv`
- NREL/DOE PVDAQ 真实数据与字段映射：`data/real/`
- Docker 联调配置：`docker/docker-compose.yml`

## 说明书

- 本机可编辑文档：`thesis/m10_毕业设计说明书_河北工业职业技术大学_v1.0_本地实测稿.docx`
- 本机 PDF 预览：`thesis/m10_毕业设计说明书_河北工业职业技术大学_v1.0_本地实测稿.pdf`
- 本机逐页渲染记录：`../evidence/thesis/RENDER_REPORT.md`
- 这些文件和开题报告含学生个人信息，未收入公开 GitHub 仓库；需通过个人安全渠道单独转移。公开仓库保留论文生成脚本、扩写内容源码和可公开素材。

## 验收边界

本地模式已完成两条端到端实测：576 条固定种子合成记录（3 类工况、29 条异常、29 条告警）和 1686 条 PVDAQ system 2107 真实公开记录（3 类工况、85 条异常、85 条告警），8 项 pytest 通过。Spark/HDFS/MySQL Docker 集群已在本机 arm64 联调验证（最终 run_id=7，证据见 evidence/runtime/api/cluster_integration.json）；Windows x64 原生构建和客户验收仍未验证。说明书已改为 18 条有来源参考文献；中文 1-10 条已完成 CNKI/CQVIP 公开元数据核验，学校账号导出可在提交前补充。
