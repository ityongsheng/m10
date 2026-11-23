# m10 项目实施计划

## 课题与来源

- 题目：基于Spark的光伏电站发电效率异常检测系统的设计与实现
- 学生个人信息保存在本地忽略文件 `project_private.json`，公开仓库不包含姓名、学号和开题报告原件。
- 原始需求：本机开题报告 DOCX；公开仓库保留按该材料实现的项目计划、代码和测试证据。
- 学校论文工作约束：河北工业职业技术大学 v1.0，规则 138 条；规则包官方学校政策尚未独立核实，按用户采用的工作约束执行。

## 需求与验收

系统面向光伏电站运维人员，完成 CSV 时序数据导入、清洗、特征计算、工况聚类、异常检测、曲线展示、异常查询和告警查看。核心演示流程为：导入数据 → 执行处理 → 查看发电曲线与工况 → 查询异常 → 查看告警和运行记录。

必须保留以下可追溯关系：需求 → API/模块 → 测试用例 → 真实运行证据 → 说明书章节与截图。演示数据若为合成数据，必须在界面、清单和论文中明确标注，不能写成真实场站测量。

验收至少覆盖：

1. 合法 CSV 能完成导入和运行，结果写入数据库并可查询。
2. 缺字段、空文件、非法数值、重复时间、辐照度为零等输入有明确错误或清洗记录。
3. Spark 本地模式与 Docker 联调模式使用同一处理逻辑；HDFS 不可用时不得伪装成已写入 HDFS。
4. 页面能展示 KPI、发电曲线、聚类分布、异常列表、分数和告警状态。
5. 重复运行、服务重启、移动项目目录和端口冲突有可解释行为。
6. Windows x64 构建、解压、双击启动和停止分别记录实际环境；Mac 或 Linux 容器结果不替代 Windows 验收。

## 技术路线

- 后端：Python FastAPI，统一提供 API、静态页面和运行状态。
- 数据处理：PySpark 3.x；Spark MLlib K-Means；孤立森林按工况分组执行，保持参数、随机种子和输出可复核。
- 存储：开发联调使用 MySQL 8.4 与 HDFS；便携本地模式使用 SQLite/本地文件回退，并在运行报告中标明模式。
- 前端：本地 HTML/CSS/JavaScript，使用可离线加载的图表实现，不依赖 CDN 才能显示核心页面。
- 运行模式：`local`（轻量演示）和 `cluster`（Docker Spark/HDFS/MySQL 联调）。

### 数据处理口径

1. 必需字段：`timestamp`、`station_id`、`irradiance_w_m2`、`ambient_temp_c`、`module_temp_c`、`power_kw`。
2. 校验时间格式和数值类型；去除无法解析的行；记录缺失、重复、非法值数量。
3. 负辐照度、负功率和明显越界值按项目配置处理，不能静默删除；重复时间保留最后一条并记录。
4. 计算 `efficiency_proxy = power_kw / max(irradiance_w_m2, 1)`，增加时间周期特征。
5. K-Means 默认 `k=3`、随机种子固定，可在界面调整 2–8。
6. 孤立森林默认污染率 0.05、随机种子固定；输出异常标记、异常分数和运行参数。

## 实施顺序与文件边界

1. 需求/数据基线：本文件、`PROJECT_CONTEXT.json`、`THIRD_PARTY.md`、`data/`。
2. 后端/算法：`backend/`、`pipeline/`、`database/`。
3. 前端/交付：`frontend/`、`tests/`、`scripts/`、Docker 配置、启动入口。
4. 集成验证：`evidence/`、运行日志、截图、测试报告。
5. 说明书：`artifacts/thesis/`，只引用已经运行和记录的版本。

## Docker 与 Windows 环境

- Docker 状态：已评估，适合服务联调和 Spark/HDFS 复现；基础镜像、平台、卷和版本在实现后固定并记录。
- Mac 开发环境：Apple Silicon；不能作为 Windows x64 构建或客户验收证据。
- Windows 目标：Windows 10/11 x64，普通用户权限优先；最终包需包含 `start.cmd`、`stop.cmd`、`launcher.json` 和运行所需资源。
- Docker 不成为客户安装前提。若 Windows 离线包尚未完成，启动器必须显示真实阻断原因。

## 说明书交付

使用河北工业职业技术大学模板原件和 v1.0 规则，生成可编辑 DOCX、PDF 预览和逐页检查记录。说明书至少包含摘要、需求、架构、功能模块、流程、数据库结构、算法实现、测试与局限；至少 10 幅有效正文图，其中至少 4 幅来自不同功能的真实运行界面。参考文献只纳入已核实的 J/D 条目，目标不少于 18 篇、英文不少于 4 篇。

## 当前缺口与风险

- NREL PVDAQ system 2107 的公开 CC BY 4.0 数据已下载、哈希固定、字段映射并完成 1686 行本地联调；module_temp_c 仍是明确标注的环境温度代理。
- `data/sample/pv_demo.csv` 仅为固定种子合成演示数据，不能代表真实场站性能或算法泛化能力。
- Windows x64 构建、离线包和目标软件排版检查待取得对应环境后验证。

## 2026-11-22 实际执行记录

- 本地模式已完成：FastAPI、SQLite、CSV 清洗、K-Means、孤立森林、告警 API 和离线 SVG 页面。
- `.venv/bin/pytest -q`：8 项通过；API TestClient 冒烟覆盖健康检查、首页、静态资源、演示数据、真实 PVDAQ 数据、导入、运行、总览、记录和告警。
- 实测演示运行：576 条记录、3 类工况、29 条异常、29 条告警；真实 PVDAQ 运行：1686 条记录、3 类工况、85 条异常、85 条告警。
- 已生成 5 张本地运行界面截图，存放在 `evidence/screenshots/`，均标记为合成演示数据。
- 18 条参考文献已替换并写入说明书；中文 1-10 条已完成 CNKI/CQVIP 公开元数据双重核验，详细记录在 `evidence/thesis/references_audit.md`；逐条结果见 evidence/thesis/vip_audit.json。
- Spark/HDFS/MySQL 集群已完成本机 arm64 Docker Desktop 联调：真实 PVDAQ 1686 行经 Spark standalone 处理，HDFS 写入/回读 1686 行，MySQL 保存 1686 条记录和 85 条异常；证据见 `evidence/runtime/api/cluster_integration.json`。Windows x64 构建和最终客户验收仍未验证。
