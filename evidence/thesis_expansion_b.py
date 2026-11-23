def expand_chapter3(add_heading, add_para, add_table):
    add_heading('3.1.1 请求、处理与持久化的数据流', 3)
    add_para('本地一次运行的路径可以拆成六步。第一步，浏览器向导入接口上传文件，后端读取字节并计算 SHA-256；第二步，read_csv_bytes 完成字段检查、解析、去重和排序，服务写入 datasets 并把原始字节保存到 runtime/uploads；第三步，创建 processing_runs 记录并写入 k、污染率、seed 和 mode；第四步，local 管线计算特征、聚类和异常分数，cluster 管线则由 Spark 执行并进行 HDFS 探针回读；第五步，服务逐条写入 records，并为异常记录生成 alerts；第六步，页面通过 overview、records 和 alerts 接口重新加载结果。')
    add_para('数据流中最重要的边界是“原始输入”和“派生结果”分离。原始 CSV 以 dataset-{id}.csv 保存，datasets 表保留文件名、行数、清洗统计和哈希；records 表只保存处理后的字段和模型输出；processing_runs 记录一次处理的参数与状态；alerts 记录需要复核的异常。这样重新查看历史运行时，不需要依赖前端内存，也能判断结果来自哪一个数据集和哪一组参数。')
    add_heading('3.1.2 本地模式与集群模式的差异', 3)
    add_table('表 3.2 两种运行模式对照', ['维度','local 本地模式','cluster 集群模式'], [
        ('执行引擎','Python 本地管线','Spark standalone'),('数据入口','runtime/uploads 本地文件','API 与 Spark worker 共享运行卷'),('中间证据','清洗统计、SQLite 记录','Parquet 探针、HDFS 回读行数'),('持久化','SQLite','MySQL 8.4'),('适用目的','便携演示、单元测试、失败路径','真实数据分布式联调'),('验收边界','macOS Apple Silicon 本地环境','macOS Docker Desktop arm64 集群，非 Windows x64')])
    add_heading('3.2.1 模块边界与调用责任', 3)
    add_para('backend.main 只负责路由、请求模型和 HTTP 错误转换，backend.service 负责数据集、运行、查询和数据库写入，pipeline.local_pipeline 负责输入清洗和本地算法，pipeline.spark_pipeline 负责可选的 PySpark 执行。前端不直接访问数据库，只通过 API 获取数据；数据库模块集中处理 SQLite 和 MySQL 的连接适配。这样的边界可以让算法测试不依赖 Web 服务，也让页面测试不需要真正启动 Spark。')
    add_para('模块图中的数据接入对应 UploadFile 和项目内 demo/real 预置数据；清洗与特征计算对应 read_csv_bytes 和 _features；工况聚类对应 kmeans；异常检测对应 isolation_scores 和 process_rows；结果查询和曲线分析对应 records 与 SVG 绘制；告警管理对应异常记录写入 alerts。每个模块都能在代码、接口和测试中找到对应对象，未实现的账号权限和现场控制没有被画入功能模块。')
    add_heading('3.2.2 接口合同与返回数据', 3)
    add_table('表 3.3 主要 API 接口合同', ['接口','方法','输入重点','成功输出','失败语义'], [
        ('/api/health','GET','无','status、service、mode','启动目录或数据库不可用时服务报错'),('/api/datasets/import','POST','multipart CSV、synthetic_demo','dataset id、sha256、clean stats','400，包含具体字段或编码错误'),('/api/runs','POST','dataset_id、k、contamination、mode','run id、状态、行数、异常数','400，数据集或模式不合法'),('/api/runs/{id}/overview','GET','运行编号','运行信息、指标、工况分布','404，运行不存在'),('/api/runs/{id}/records','GET','异常筛选、站点、limit','逐条检测记录','空结果或查询参数错误'),('/api/runs/{id}/alerts','GET','运行编号','告警列表','运行不存在时服务错误')])
    add_heading('3.3.1 数据集表 datasets', 3)
    add_para('datasets 是数据生命周期的入口表。filename 保留用户上传或项目预置文件名；imported_at 用于追踪导入时间；row_count、valid_count、invalid_count 和 duplicate_count 分别记录输入、有效、无效和重复数量；synthetic_demo 用于把固定种子演示与真实公开数据区分开；source_sha256 用于判断文件来源是否被改变；metadata_json 保留 negative_rows 等扩展统计。该表不保存算法结果，因此同一源文件可以被不同参数重复运行。')
    add_table('表 3.4 数据集表 datasets 结构', ['字段名','类型','约束/含义','来源或用途'], [
        ('id','INTEGER','主键，自增','供运行和源文件路径关联'),('filename','TEXT','非空','原始文件名'),('imported_at','TEXT','非空，ISO 时间','导入时间'),('row_count','INTEGER','非空','输入行数'),('valid_count','INTEGER','非空','清洗后有效行数'),('invalid_count','INTEGER','非空','解析失败或负值行数'),('duplicate_count','INTEGER','默认 0','重复时间站点组合数'),('synthetic_demo','INTEGER','0/1','合成演示标记'),('source_sha256','TEXT','可空','原始字节哈希'),('metadata_json','TEXT','默认 {}','扩展质量统计')])
    add_heading('3.3.2 运行表 processing_runs', 3)
    add_para('processing_runs 表把一次“点击开始处理”变成可追踪的业务对象。创建时写入 dataset_id、mode、status=running、started_at 和 params_json；成功后写入 completed_at、total_rows 和 anomaly_count；异常时写入 failed 和 error_message。params_json 中固定保存 k、contamination 和 seed，避免仅凭页面当前值猜测历史结果。dataset_id 关联数据集表，但便携 SQLite 与 MySQL 适配层都通过应用代码和外键约束共同维护关系。')
    add_table('表 3.5 运行表 processing_runs 结构', ['字段名','类型','约束/含义','业务解释'], [
        ('id','INTEGER','主键，自增','运行编号'),('dataset_id','INTEGER','关联 datasets.id','运行使用的数据集'),('mode','TEXT','local 或 cluster','执行模式'),('status','TEXT','running/completed/failed','状态机状态'),('started_at','TEXT','非空','开始时间'),('completed_at','TEXT','可空','完成或失败时间'),('params_json','TEXT','非空 JSON','k、污染率、随机种子'),('total_rows','INTEGER','默认 0','结果行数'),('anomaly_count','INTEGER','默认 0','异常数量'),('error_message','TEXT','可空','失败原因')])
    add_heading('3.3.3 检测记录表 records', 3)
    add_para('records 是页面曲线、异常表格和聚类统计的共同来源。除了六个输入字段外，它保存 efficiency_proxy、cluster_id、anomaly_score、is_anomaly 和 known_issue_label。efficiency_proxy 是程序计算的代理值，不表示经过仪器标定的效率百分比；cluster_id 是工况标签，不是故障类别；is_anomaly 是在当前运行污染率和阈值下形成的筛查结果。论文和页面都把这些字段解释为分析线索，而不是已经完成现场诊断。')
    add_table('表 3.6 检测记录表 records 结构', ['字段名','类型','单位/取值','说明'], [
        ('timestamp','TEXT/VARCHAR','ISO 时间','记录时刻'),('station_id','TEXT/VARCHAR','站点编号','站点边界'),('irradiance_w_m2','REAL','W/m²，非负','辐照度'),('ambient_temp_c','REAL','℃','环境温度'),('module_temp_c','REAL','℃，公开源为代理','模块温度字段契约'),('power_kw','REAL','kW，非负','输出功率'),('efficiency_proxy','REAL','无量纲代理','power/max(irradiance,1)'),('cluster_id','INTEGER','0..k-1','工况标签'),('anomaly_score','REAL','0..1 归一化','异常分数'),('is_anomaly','INTEGER','0/1','阈值标记'),('known_issue_label','INTEGER','可空','公开或演示数据标签')])
    add_heading('3.3.4 告警表 alerts 与索引', 3)
    add_para('alerts 只为 is_anomaly 为真的记录生成消息，包含运行编号、记录编号、severity、message、acknowledged 和 created_at。分数达到 0.85 时显示 high，否则异常记录显示 medium；非异常记录在记录查询中显示 low。records 表建立 (run_id, timestamp) 和 (run_id, is_anomaly) 索引，分别服务时间序列排序和异常筛选。当前没有实现告警确认写入接口，acknowledged 字段为后续扩展保留，论文不把它描述成已经完成的闭环。')
    add_table('表 3.7 告警表 alerts 结构', ['字段名','类型','约束/含义','用途'], [
        ('id','INTEGER','主键，自增','告警编号'),('run_id','INTEGER','关联 processing_runs.id','来源运行'),('record_id','INTEGER','关联 records.id','异常记录'),('severity','TEXT','high/medium','等级'),('message','TEXT','非空','面向复核人员的说明'),('acknowledged','INTEGER','默认 0','预留处理状态'),('created_at','TEXT','非空','生成时间')])
    add_heading('3.3.5 数据一致性与 3NF 讨论', 3)
    add_para('在关系型存储中，datasets、processing_runs、records 和 alerts 以逐级关联的方式拆分，避免将一个运行的参数、每一条检测记录和每一条告警重复写入同一宽表。records 中的输入字段和派生字段属于一次处理结果，不能跨运行复用；alerts 通过 record_id 指向具体记录，避免把告警消息复制到所有查询结果中。该结构满足本项目对实体职责分离的工程需要，但论文不把 SQLite/MySQL 的当前建表脚本夸大为经过形式化范式证明的复杂生产数据库。')
