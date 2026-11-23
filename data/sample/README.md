# m10 演示数据

`pv_demo.csv` 是固定随机种子生成的合成光伏时序数据，用于开发接口、图表和异常检测流程。

- 数据状态：`synthetic_demo=true`
- 不能代表真实光伏电站，也不能用于宣称现场性能或模型泛化能力。
- 字段：`timestamp`、`station_id`、`irradiance_w_m2`、`ambient_temp_c`、`module_temp_c`、`power_kw`、`known_issue_label`
- `known_issue_label` 仅用于测试结果对照，不参与无监督模型训练。
- 真实数据候选：NREL PVDAQ，许可和字段映射见 `data/dataset_manifest.json` 与 `THIRD_PARTY.md`。
