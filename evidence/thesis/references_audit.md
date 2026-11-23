# m10 参考文献核验审计

核验日期：2026-11-22  
对象：`artifacts/thesis/m10_毕业设计说明书_河北工业职业技术大学_v1.0_本地实测稿.docx`  
约束：河北工业职业技术大学论文规则 v1.0 要求参考文献不少于 18 条，且至少 4 条英文文献。

## 结论

本轮已形成 18 条闭合候选清单，并将这 18 条写入当前 build_thesis.py、DOCX 和 PDF：中文 10 条来自 CNKI 合作期刊门户或参考文献页，英文 8 条来自 Springer、Elsevier 或 MDPI 出版社/DOI 页面。正文参考文献区已按 1-18 顺序重排，PDF 渲染和文本计数均为 18 条。

2026-11-22 已通过 CQVIP 公开检索页逐条复核中文 1-10 条：10 个查询均返回 HTTP 200，并在结果文本中找到作者、期刊、年份和起止页码。逐条 URL、返回字节数、字段命中结果和上下文片段保存在 evidence/thesis/vip_audit.json。公开检索页证明书目信息可在维普检索到；学校账号导出 GB/T 7714 或下载凭证仍可作为正式提交前的增强证据。CNKI 官方期刊门户可公开读取的条目记录了作者、题名、卷期、页码、DOI（如有）和摘要；来源链接与访问日期均保留在下表。

## 维普公开检索页已核验

中文 1-10 条均通过维普公开检索页复核。每条记录的作者、期刊、年份、起始页和结束页字段均命中；检索结果与完整上下文见 evidence/thesis/vip_audit.json。以下仅证明公开检索元数据可获得，不把未登录的机构导出格式写成已取得。

## CNKI 官方期刊门户已核验

以下 7 条可在 CNKI 合作期刊门户直接打开并读取完整书目信息，可作为新增中文 J 文献：

1. 马天东, 耿天翔, 李峰, 等. 光伏电站功率数据异常检测技术研究综述[J]. 微型电脑应用, 2024, 40(07): 72-75, 92. [CNKI 期刊页](https://wxdy.cbpt.cnki.net/portal/journal/portal/client/paper/134bc84dd17d5404dd32aa91b2f9334c)（访问：2026-11-22）
2. 马天东, 耿天翔, 李峰, 钟海亮. 基于优化变点-四分位法的光伏异常数据检测[J]. 微型电脑应用, 2024, 40(06): 105-108. [CNKI 期刊页](https://wxdy.cbpt.cnki.net/portal/journal/portal/client/paper/2408270ec9168672919d469472233ca3)（访问：2026-11-22）
3. 裘愉涛, 张磊, 周开运, 等. 基于图像特征检测的光伏异常数据识别算法[J]. 浙江电力, 2025, 44(05): 42-52. DOI: 10.19585/j.zjdl.202505005. [CNKI 期刊页](https://zjdl.cbpt.cnki.net/portal/journal/portal/client/paper/e847186596e3c2aa95fe901e60c6a720)（访问：2026-11-22）
4. 祁炜雯, 张俊, 吴洋, 等. 基于改进BP-Bagging算法的光伏电站故障诊断方法[J]. 浙江电力, 2024, 43(03): 65-74. DOI: 10.19585/j.zjdl.202403008. [CNKI 期刊页](https://zjdl.cbpt.cnki.net/portal/journal/portal/client/paper/d6142e6859b3b276d360ae87f98efb0e)（访问：2026-11-22）
5. 徐恒辉, 姚杰, 周萍, 等. 基于运行数据的光伏电站状态评估方法研究[J]. 电力科技与环保, 2023, 39(05): 450-456. [CNKI 期刊页](https://dlhb.cbpt.cnki.net/portal/journal/portal/client/paper/5ae7f631f32ddc8eceefd4e30e587db5)（访问：2026-11-22）
6. 程航, 张晖, 代家昆, 等. 基于数据驱动和概率神经网络的光伏阵列智能故障诊断与监控[J]. 微型电脑应用, 2026, 42(07): 21-24, 29. [CNKI 期刊页](https://wxdy.cbpt.cnki.net/portal/journal/portal/client/paper/93ed5a9a89d628ffbbe42eb51d8899ea)（访问：2026-11-22）
7. 徐志保, 张认成. 结合小波变换与支持向量机的光伏阵列故障检测算法[J]. 吉林大学学报（信息科学版）, 2026, 44(05): 1169-1176. DOI: 10.19292/j.cnki.jdxxp.2026.05.010. [CNKI 期刊页](https://ccyd.cbpt.cnki.net/portal/journal/portal/client/paper/1d39cb93e4a491d0d0ea9fe347fe7cd3)（访问：2026-11-22）

沈春明等《基于RCET–TGatedGCN的光伏系统故障鲁棒诊断模型》仍作为备选研究线索保留在检索记录中，但因正式卷期页码尚未显示，本轮不计入 18 条闭合清单。

下列 3 条在 CNKI 合作期刊的全文参考文献/引用信息中被完整列出，题名、作者、期刊、卷期和页码可核对；提交前建议再打开其独立 CNKI 条目导出 GB/T 7714：

8. 龚莺飞, 鲁宗相, 乔颖, 等. 基于Copula理论的光伏功率高比例异常数据机器识别算法[J]. 电力系统自动化, 2016, 40(09): 16-22. 来源页：[浙江电力文章参考文献](https://zjdl.cbpt.cnki.net/portal/journal/portal/client/paper/e847186596e3c2aa95fe901e60c6a720)（访问：2026-11-22）
9. 杨茂, 孟玲建, 李大勇, 等. 基于类3σ准则的光伏功率异常数据识别[J]. 可再生能源, 2018, 36(10): 1443-1448. 来源页：[浙江电力文章参考文献](https://zjdl.cbpt.cnki.net/portal/journal/portal/client/paper/e847186596e3c2aa95fe901e60c6a720)（访问：2026-11-22）
10. 杨茂, 黄鑫. 基于光照过程特征分析的光伏功率异常数据识别算法[J]. 电力系统自动化, 2019, 43(06): 64-69. 来源页：[CNKI 参考文献检索页](https://wxdy.cbpt.cnki.net/portal/journal/portal/client/paper/1e50e4ca4d7714cb01a29c34a9814d81)（访问：2026-11-22）

## 出版社/DOI 页面已核验的英文 J 文献

以下条目均为英文期刊文献，具有出版社页面或 DOI，可用于满足“英文不少于 4 条”要求：

11. Wang X, Du J, Zhang G, et al. State space model for anomaly detection of distributed photovoltaic power generation systems[J]. Energy Informatics, 2025, 8: 141. DOI: 10.1186/s42162-025-00598-2. [Springer Nature](https://link.springer.com/article/10.1186/s42162-025-00598-2)（访问：2026-11-22）
12. Miraftabzadeh S M, Longo M, Leva S, et al. Data anomaly detection in photovoltaic power time-series via unsupervised deep learning with insufficient information[J]. Sustainable Energy, Grids and Networks, 2025, 43: 101769. DOI: 10.1016/j.segan.2025.101769. [Elsevier](https://www.sciencedirect.com/science/article/pii/S2352467725001511)（访问：2026-11-22）
13. Li D, Zhang Y, Yang Z, et al. Sensing anomaly of photovoltaic systems with sequential conditional variational autoencoder[J]. Applied Energy, 2024, 353: 122124. DOI: 10.1016/j.apenergy.2023.122124. [Elsevier](https://www.sciencedirect.com/science/article/pii/S0306261923014885)（访问：2026-11-22）
14. El-Banby G M, Moawad N M, Abouzalm B A, et al. Photovoltaic system fault detection techniques: a review[J]. Neural Computing and Applications, 2023, 35: 24829-24842. DOI: 10.1007/s00521-023-09041-7. [Springer Nature](https://link.springer.com/article/10.1007/s00521-023-09041-7)（访问：2026-11-22）
15. Ibrahim M, Alsheikh A, Awaysheh F M, et al. Machine learning schemes for anomaly detection in solar power plants[J]. Energies, 2022, 15(03): 1082. DOI: 10.3390/en15031082. [MDPI](https://www.mdpi.com/1996-1073/15/3/1082)（访问：2026-11-22）
16. Branco P, Gonçalves F, Costa A C. Tailored algorithms for anomaly detection in photovoltaic systems[J]. Energies, 2020, 13(01): 225. DOI: 10.3390/en13010225. [MDPI](https://www.mdpi.com/1996-1073/13/1/225)（访问：2026-11-22）
17. Vlaminck M, Heidbuchel R, Philips W, Luong H. Region-based CNN for anomaly detection in PV power plants using aerial imagery[J]. Sensors, 2022, 22(03): 1244. DOI: 10.3390/s22031244. [MDPI](https://www.mdpi.com/1424-8220/22/3/1244)（访问：2026-11-22）
18. Osmani K, Haddad A, Lemenand T, et al. A critical review of PV systems’ faults with the relevant detection methods[J]. Energy Nexus, 2023, 12: 100257. DOI: 10.1016/j.nexus.2023.100257. [Elsevier](https://doi.org/10.1016/j.nexus.2023.100257)（访问：2026-11-22）

## 提交前复核建议

- 当前 DOCX/PDF 已使用上面 1-18 条；提交前可用学校账号导出 VIP/CNKI GB/T 7714 记录并检查正文引注顺序。
- 中文 1-10 条已有 CNKI 合作门户/参考页与 CQVIP 公开检索页双重元数据证据；英文 11-18 条已有出版社/DOI 证据。若学校要求机构账号导出凭证，提交前再补导出文件。
- 当前说明书已加入上述 18 条，已重新生成 DOCX/PDF、复核静态目录页码，并通过 16 页 A4 渲染、文本和可访问性审计；提交前可按学校账号导出 VIP/CNKI 记录并检查正文引注顺序。

## 现有开题报告 12 条

开题报告原有 12 条不再作为本轮 18 条闭合清单的唯一依据；本审计中的 1-18 条是当前说明书使用的参考文献基础。正式提交前仍应按作者、题名、期刊/学位授予单位、年份、卷期页码和 DOI/数据库链接逐项复核。
