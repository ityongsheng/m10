# PVDAQ 真实数据切片

本目录保存从 NREL/DOE PVDAQ 公共数据湖下载的 system 2107（Farm Solar Array）原始文件，以及一个可复现的规范化切片。

## 来源与许可

- 数据集：Photovoltaic Data Acquisition (PVDAQ) Public Datasets
- 系统：2107，Farm Solar Array，Arbuckle, California
- 数据湖：<https://oedi-data-lake.s3.amazonaws.com/pvdaq/2023-solar-data-prize/2107_OEDI/>
- 数据集入口：<https://data.openei.org/submissions/4568>
- DOI：10.25984/1846021
- 许可：CC BY 4.0，保留 NREL/DOE 署名和来源链接
- 下载日期：2026-11-22

## 文件

- `pvdaq_2107_meter_15m_data.csv`：AC 电表输出，源单位 kW。
- `pvdaq_2107_environment_data.csv`：环境温度、风速和风向；环境温度源单位 °F。
- `pvdaq_2107_irradiance_data.csv`：POA 辐照度，源单位 W/m²。
- `pvdaq_2107_system_metadata.json`：系统、站点和指标元数据。
- `pvdaq_2107_2022-06_normalized.csv`：由上述三个文件按 timestamp 内连接生成的 m10 输入切片。

规范化脚本：`scripts/normalize_pvdaq.py`。默认切片为 2022-06-01（含）至 2022-07-01（不含）。环境温度已从 °F 转换为 °C。PVDAQ system 2107 在元数据中没有 module temperature 指标，因此 `module_temp_c` 采用 `ambient_temp_c` 代理；这不是源站实测模块温度，已在清单和论文证据中明确标记。

原始文件 SHA-256 保存在 `evidence/data/pvdaq_2107.sha256`，规范化切片 SHA-256 保存在同目录的同名校验文件中。

## 追加审计切片

`pvdaq_system10_2006-07-10.csv` 是同一 PVDAQ 数据湖中 system 10 的单日切片，来源和字段映射见同目录的 `pvdaq_system10_2006-07-10.manifest.json`。源文件保留在 `data/real/raw/`；源数据 96 行中 55 行满足 m10 当前非负辐照度/功率输入约束，其他夜间或负功率行只记录为丢弃，不冒充有效观测。
