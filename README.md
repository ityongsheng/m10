# m10 基于 Spark 的光伏电站发电效率异常检测系统

本项目面向光伏电站运维数据的导入、清洗、工况聚类、异常检测和告警查看。当前工程从开题报告建立，演示数据为固定种子合成数据，已在 `data/dataset_manifest.json` 中标注，不代表真实场站测量。

## 当前状态

- 需求与数据基线：已完成。
- 前端工作台：已完成静态页面和离线 SVG 图表。
- 后端与本地处理：已完成 FastAPI、SQLite、清洗、K-Means 和孤立森林；真实 PVDAQ 切片已接入并完成本地运行；Docker Spark/HDFS/MySQL 集群已完成真实联调。
- Windows 10/11 x64 离线构建：尚未验证。
- 说明书：本机已生成可编辑 DOCX、35 页 PDF 预览和逐页渲染记录；公开仓库不包含带学生个人信息的成品，生成脚本和可公开的图表素材保留在代码中。

## 目录

```text
backend/       FastAPI 接口与运行服务
pipeline/      PySpark 数据处理和异常检测
database/      表结构及迁移
frontend/      静态操作页面
data/          数据源清单和演示 CSV
tests/         自动化测试
evidence/      运行、测试和交付证据
docker/        Docker 联调配置
scripts/       本地启动、检查和数据工具
```

## 运行方式

开发环境使用 Python 3.11+、Java 17、Docker Desktop。在项目根目录执行：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

然后打开 `http://127.0.0.1:8000/`。Windows 客户入口为根目录的 `start.cmd`，停止入口为 `stop.cmd`；启动器会在后端入口尚未构建时显示真实阻断原因。

## Docker 联调

```bash
cp docker/.env.example docker/.env
# 将 docker/.env 中的占位密码改为仅供本机使用的值
docker compose --env-file docker/.env -f docker/docker-compose.yml --profile cluster up --build
```

Docker 只用于开发和联调，不是 Windows 客户的安装前提。当前本地模式、真实 PVDAQ 数据和 Docker Spark/HDFS/MySQL 集群均已实测；Windows x64 客户验收仍待对应环境。

## 数据约定

导入 CSV 至少需要：`timestamp`、`station_id`、`irradiance_w_m2`、`ambient_temp_c`、`module_temp_c`、`power_kw`。无效记录、重复时间和清洗数量必须记录在运行结果中，不能静默删除。

真实数据切片位于 `data/real/pvdaq_2107_2022-06_normalized.csv`，来源为 NREL/DOE PVDAQ system 2107，许可 CC BY 4.0。该切片的原始文件、字段映射、下载日期和 SHA-256 见 `data/real/README.md`、`data/dataset_manifest.json` 和 `evidence/data/pvdaq_2107.sha256`。源数据没有模块温度通道，因此规范化文件中的 `module_temp_c` 明确使用环境温度代理。

## 论文和交付边界

论文说明书只引用真实运行版本、真实截图和实际测试结果。Docker、Mac ARM 或本地演示不等同于 Windows x64 验收；未执行项目保持“未验证”。

本机说明书交付物（含学生个人信息，未收入公开仓库）：

- `artifacts/thesis/m10_毕业设计说明书_河北工业职业技术大学_v1.0_本地实测稿.docx`
- `artifacts/thesis/m10_毕业设计说明书_河北工业职业技术大学_v1.0_本地实测稿.pdf`
- `evidence/thesis/RENDER_REPORT.md`

## 换电脑恢复

公开仓库保留全部项目源代码、依赖清单、测试、可公开数据、截图和论文生成脚本。克隆后按上面的运行方式重建 `.venv`；需要集群时按 `docker/.env.example` 新建 `docker/.env`。本机 `runtime/`、`.venv/`、`docker/.env`、`project_private.json`、原始开题报告和带个人信息的说明书成品不会公开上传，需要通过个人安全渠道单独转移。论文生成器在没有 `project_private.json` 时把封面姓名、学号和指导教师留作“待填写”。
