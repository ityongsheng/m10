from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from PIL import Image, ImageDraw, ImageFont
import json

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'artifacts/thesis'
IMG=ROOT/'evidence/thesis/images'
OUT.mkdir(parents=True,exist_ok=True); IMG.mkdir(parents=True,exist_ok=True)
private_path=ROOT/'project_private.json'
private=json.loads(private_path.read_text(encoding='utf-8')) if private_path.exists() else {}
student=private.get('student', {})
student_name=student.get('name') or '待填写'
student_id=student.get('student_id') or '待填写'
advisor=private.get('advisor') or '待填写'
FONT='/System/Library/Fonts/Supplemental/Songti.ttc'
try:
    def f(size): return ImageFont.truetype(FONT,size,index=0)
except Exception:
    def f(size): return ImageFont.load_default()

def diagram(name, title, boxes, arrows):
    im=Image.new('RGB',(1600,900),'white'); d=ImageDraw.Draw(im)
    d.text((800,40),title,font=f(42),fill='black',anchor='ma')
    for x,y,w,h,text in boxes:
        d.rectangle((x,y,x+w,y+h),outline='black',width=4)
        d.multiline_text((x+w/2,y+h/2),text,font=f(28),fill='black',anchor='mm',align='center',spacing=8)
    for x1,y1,x2,y2 in arrows:
        d.line((x1,y1,x2,y2),fill='black',width=4)
        import math
        ang=math.atan2(y2-y1,x2-x1); L=18
        p1=(x2-L*math.cos(ang-0.5),y2-L*math.sin(ang-0.5)); p2=(x2-L*math.cos(ang+0.5),y2-L*math.sin(ang+0.5))
        d.polygon([(x2,y2),p1,p2],fill='black')
    path=IMG/name; im.save(path,dpi=(180,180)); return path

arch=diagram('fig_architecture.png','系统总体架构',[
 (90,280,270,180,'运维人员\n浏览器'),(430,180,320,180,'表示层\nHTML CSS JavaScript'),(430,500,320,180,'接口层\nFastAPI'),(950,120,300,160,'处理层\nSpark / 本地管线'),(950,360,300,160,'数据层\nSQLite / MySQL'),(950,600,300,160,'文件层\nCSV / HDFS')],
 [(360,370,430,270),(590,360,590,500),(750,590,950,200),(750,590,950,440),(750,590,950,680)])
mod=diagram('fig_modules.png','系统功能模块',[(100,250,260,180,'数据接入'),(450,120,260,180,'数据清洗与\n特征计算'),(800,120,260,180,'工况聚类'),(1150,120,260,180,'异常检测'),(450,520,260,180,'结果查询'),(800,520,260,180,'曲线分析'),(1150,520,260,180,'告警管理')],[(360,340,450,210),(710,210,800,210),(1060,210,1150,210),(930,300,580,520),(930,300,930,520),(1060,610,1150,610)])
flow=diagram('fig_flow.png','本地处理流程',[(110,330,220,120,'开始'),(410,300,260,180,'导入 CSV\n字段校验'),(850,300,260,180,'清洗与特征\n计算'),(1290,300,220,180,'聚类与\n异常检测'),(1290,600,220,120,'保存结果'),(850,600,260,120,'结束')],[(330,390,410,390),(670,390,850,390),(1110,390,1290,390),(1400,480,1400,600),(1290,660,1110,660)])
er=diagram('fig_er.png','核心实体关系',[(100,300,300,200,'datasets\n数据集'),(650,180,300,200,'processing_runs\n处理运行'),(1180,300,300,200,'records\n检测记录'),(650,600,300,180,'alerts\n告警事件')],[(400,400,650,280),(950,280,1180,400),(1330,500,950,660)])
alg=diagram('fig_algorithm.png','异常检测算法流程',[(100,300,250,160,'标准化特征'),(480,260,280,240,'K-Means\n工况聚类'),(900,260,280,240,'按工况训练\n孤立森林'),(1310,300,220,160,'异常分数\n与告警')],[(350,380,480,380),(760,380,900,380),(1180,380,1310,380)])

# Helpers

def shade(cell, fill='E8F0EC'):
    tcPr=cell._tc.get_or_add_tcPr(); shd=OxmlElement('w:shd'); shd.set(qn('w:fill'),fill); tcPr.append(shd)
def set_cell_text(cell,text,bold=False):
    cell.text=''; p=cell.paragraphs[0]; p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    r=p.add_run(str(text)); r.bold=bold; r.font.name='宋体'; r._element.rPr.rFonts.set(qn('w:eastAsia'),'宋体'); r.font.size=Pt(10.5)
    cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER

def add_table(doc, headers, rows):
    table=doc.add_table(rows=1, cols=len(headers)); table.alignment=WD_TABLE_ALIGNMENT.CENTER; table.style='Table Grid'
    for i,h in enumerate(headers): set_cell_text(table.rows[0].cells[i],h,True); shade(table.rows[0].cells[i])
    for row in rows:
        cells=table.add_row().cells
        for i,v in enumerate(row): set_cell_text(cells[i],v)
    doc.add_paragraph('')
    return table

def add_caption(doc, text):
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    r=p.add_run(text); r.bold=True; r.font.name='黑体'; r._element.rPr.rFonts.set(qn('w:eastAsia'),'黑体'); r.font.size=Pt(10.5)

def add_fig(doc, path, caption, width=6.2):
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(path),width=Inches(width)); add_caption(doc,caption)

def add_para(doc,text,style=None):
    p=doc.add_paragraph(style=style)
    p.paragraph_format.first_line_indent=Cm(0.74); p.paragraph_format.line_spacing=Pt(20); p.paragraph_format.space_after=Pt(0)
    r=p.add_run(text); r.font.name='宋体'; r._element.rPr.rFonts.set(qn('w:eastAsia'),'宋体'); r.font.size=Pt(12)
    return p

def add_heading(doc,text,level):
    p=doc.add_paragraph(style=f'Heading {level}')
    p.paragraph_format.keep_with_next=True
    r=p.add_run(text); r.font.name='黑体'; r._element.rPr.rFonts.set(qn('w:eastAsia'),'黑体'); r.font.size=Pt({1:15,2:14,3:13}[level]); r.bold=True
    return p

def add_toc(doc):
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; r=p.add_run('目录'); r.bold=True; r.font.size=Pt(15); r.font.name='黑体'; r._element.rPr.rFonts.set(qn('w:eastAsia'),'黑体')
    p=doc.add_paragraph(); fld=OxmlElement('w:fldSimple'); fld.set(qn('w:instr'),'TOC \\o "1-3" \\h \\z \\u'); p._p.append(fld)
    doc.add_page_break()

# document
D=Document()
sec=D.sections[0]; sec.page_width=Cm(21); sec.page_height=Cm(29.7); sec.top_margin=Cm(2.5); sec.bottom_margin=Cm(2.5); sec.left_margin=Cm(3); sec.right_margin=Cm(2.5)
styles=D.styles
for name in ['Normal','Body Text']:
    st=styles[name]; st.font.name='宋体'; st._element.rPr.rFonts.set(qn('w:eastAsia'),'宋体'); st.font.size=Pt(12)
for i in [1,2,3]:
    st=styles[f'Heading {i}']; st.font.name='黑体'; st._element.rPr.rFonts.set(qn('w:eastAsia'),'黑体'); st.font.color.rgb=None
# header/footer
for section in D.sections:
    hp=section.header.paragraphs[0]; hp.alignment=WD_ALIGN_PARAGRAPH.CENTER; rr=hp.add_run('河北工业职业技术大学毕业设计'); rr.font.name='宋体'; rr._element.rPr.rFonts.set(qn('w:eastAsia'),'宋体'); rr.font.size=Pt(9)
    fp=section.footer.paragraphs[0]; fp.alignment=WD_ALIGN_PARAGRAPH.CENTER; rr=fp.add_run('m10 光伏电站发电效率异常检测系统'); rr.font.size=Pt(9)
# cover
for _ in range(5): D.add_paragraph('')
p=D.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; r=p.add_run('毕业设计说明书'); r.font.size=Pt(24); r.bold=True; r.font.name='黑体'; r._element.rPr.rFonts.set(qn('w:eastAsia'),'黑体')
D.add_paragraph('')
p=D.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; r=p.add_run('基于Spark的光伏电站发电效率异常检测系统的设计与实现'); r.font.size=Pt(18); r.bold=True; r.font.name='黑体'; r._element.rPr.rFonts.set(qn('w:eastAsia'),'黑体')
for _ in range(7): D.add_paragraph('')
for line in [f'学生姓名：{student_name}',f'学号：{student_id}','学院：人工智能学院','专业：大数据工程技术',f'指导教师：{advisor}','完成日期：2026年11月22日']:
 p=D.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; r=p.add_run(line); r.font.size=Pt(14); r.font.name='宋体'; r._element.rPr.rFonts.set(qn('w:eastAsia'),'宋体')
D.add_page_break()
# declaration
add_heading(D,'毕业设计原创性声明',1)
add_para(D,'本人所提交的毕业设计《基于Spark的光伏电站发电效率异常检测系统的设计与实现》，是在指导教师指导下完成的设计工作。除文中已经注明引用的内容外，本说明书不包含其他个人或集体已经发表或撰写过的研究成果。当前说明书中的本地运行结果来自项目固定种子合成演示数据，已在正文和证据材料中标明数据性质。')
add_para(D,'本人承诺对本说明书内容的真实性和完整性负责。')
D.add_paragraph('\n\n作者签名：________________    指导教师签名：________________')
D.add_paragraph('日期：________________        日期：________________')
D.add_page_break()
# abstracts
add_heading(D,'摘  要',1)
add_para(D,'针对光伏电站监测数据规模增长、环境因素导致发电波动明显以及人工巡检难以及时定位低效记录的问题，本文设计并实现了一套基于 Spark 的光伏电站发电效率异常检测系统。系统以 CSV 时序数据为输入，完成字段校验、重复记录处理、数值清洗和效率代理特征计算；在本地模式中使用固定种子实现 K-Means 工况聚类和孤立森林异常检测，并通过 FastAPI 与静态 Web 页面展示发电曲线、工况分布、异常记录和告警信息。系统还保留 Spark、HDFS 与 MySQL 的 Docker 联调入口，便于后续在目标环境中进行分布式验证。当前本地实测使用 576 条固定种子合成演示记录，形成 3 类工况，标记 29 条异常并生成 29 条告警，接口、数据库写入和页面展示均完成联调。由于真实公开光伏数据子集、集群运行和 Windows x64 客户环境尚未完成验证，本文将这些内容列为后续工作。')
D.add_paragraph('关键词：光伏电站；Spark；K-Means；孤立森林；异常检测')
D.add_page_break()
add_heading(D,'ABSTRACT',1)
add_para(D,'To address the difficulty of processing photovoltaic monitoring records and locating inefficient operating records under changing environmental conditions, this project designs and implements a photovoltaic generation efficiency anomaly detection system based on Spark. The system validates and cleans CSV time-series data, calculates an efficiency proxy, performs operating-condition clustering with K-Means, and detects anomalies with an isolation-forest implementation in local mode. A FastAPI service and an offline static web interface provide trend charts, cluster summaries, anomaly records, and alerts. A Docker entry for Spark, HDFS, and MySQL is reserved for later cluster verification. In the current local rehearsal, 576 deterministic synthetic records produced three clusters, 29 anomaly records, and 29 alerts. The synthetic nature of the fixture, the unverified cluster deployment, and the pending Windows x64 acceptance are explicitly reported.')
D.add_paragraph('Key words: photovoltaic power station; Spark; K-Means; isolation forest; anomaly detection')
D.add_page_break(); add_toc(D)
# chapters
add_heading(D,'第1章 绪论',1)
add_heading(D,'1.1 研究背景',2)
add_para(D,'光伏电站的辐照度、环境温度、组件温度和输出功率具有明显的时序波动。相同设备在不同天气和时段下会产生不同的输出水平，使用单一固定阈值容易把正常的气象变化判断为设备异常。运维人员需要一种能够整理多字段监测记录、区分运行工况并给出异常线索的工具。')
add_heading(D,'1.2 研究内容',2)
add_para(D,'本项目围绕数据导入与清洗、效率代理特征计算、工况聚类、异常检测、结果查询和告警展示展开。实现阶段优先完成不依赖外部设备的 CSV 工作流，并把 Spark/HDFS/MySQL 集群作为可切换的联调路线。')
add_heading(D,'1.3 论文组织',2)
add_para(D,'全文依次介绍需求与相关技术、系统设计、数据处理与算法、系统实现、测试结果以及结论和局限。系统截图与测试结果均指向本地运行证据，合成演示数据和未验证环境单独说明。')
add_heading(D,'第2章 相关技术与需求分析',1)
add_heading(D,'2.1 相关技术',2)
add_para(D,'Spark 用于表达分布式数据处理路线，K-Means 用于把输入记录划分为若干运行工况，孤立森林通过随机切分形成路径长度差异，用于识别相对孤立的记录。FastAPI 提供轻量 HTTP 接口，HTML、CSS 和 JavaScript 提供无需 CDN 的本地页面。SQLite 用于便携模式，数据库结构保留向 MySQL 迁移的表和字段边界。')
add_heading(D,'2.2 功能需求',2)
add_table(D,['编号','需求','输入','输出'],[
 ('R1','导入数据集','UTF-8 CSV','数据集记录与清洗统计'),('R2','处理运行','数据集、k、污染率','运行状态与算法结果'),('R3','结果查询','运行编号、过滤条件','曲线、异常记录、告警'),('R4','运行追溯','历史运行','参数、数据规模与状态')])
add_heading(D,'2.3 非功能需求',2)
add_para(D,'页面应能在普通浏览器中打开，核心展示不依赖公网 CDN；输入错误应有可读提示；重复运行不清空已有记录；开发环境、客户 Windows 环境和论文结果的验证边界分开记录。')
add_heading(D,'第3章 系统总体设计',1)
add_heading(D,'3.1 总体架构',2); add_para(D,'系统由浏览器表示层、FastAPI 接口层、本地或 Spark 处理层、SQLite/MySQL 数据层和 CSV/HDFS 文件层组成。当前本地模式使用 SQLite 和本地文件；Docker 集群配置只作为待验证联调入口。')
add_fig(D,arch,'图3.1 系统总体架构图')
add_heading(D,'3.2 功能模块设计',2); add_para(D,'系统功能按数据接入、清洗与特征计算、工况聚类、异常检测、结果查询、曲线分析和告警管理划分。模块之间的执行先后由处理流程表达，模块图只表达职责边界。')
add_fig(D,mod,'图3.2 系统功能模块图')
add_heading(D,'3.3 数据库设计',2)
add_para(D,'数据库核心对象包括 datasets、processing_runs、records 和 alerts。数据集记录来源文件和清洗统计，处理运行记录模式与参数，检测记录保存输入字段、效率代理值、工况编号和异常分数，告警记录关联异常记录并保存等级和提示。')
add_fig(D,er,'图3.3 核心实体关系图')
add_table(D,['表名','主要字段','用途'],[
 ('datasets','id、filename、row_count、source_sha256','记录数据集来源和清洗统计'),('processing_runs','id、dataset_id、mode、params_json、status','追踪一次处理运行'),('records','timestamp、station_id、power_kw、cluster_id、anomaly_score','保存逐条检测结果'),('alerts','run_id、record_id、severity、message','保存需要复核的告警')])
add_heading(D,'第4章 数据处理与异常检测算法设计',1)
add_heading(D,'4.1 数据清洗与特征计算',2)
add_para(D,'系统要求 timestamp、station_id、irradiance_w_m2、ambient_temp_c、module_temp_c 和 power_kw 六个字段。程序解析时间和数值，拒绝无法解析的记录以及负辐照度和负功率，按时间与站点去重并保留最后一条记录。效率代理值定义为 power_kw / max(irradiance_w_m2, 1)，同时加入小时周期特征。')
add_fig(D,flow,'图4.1 本地处理流程图')
add_heading(D,'4.2 K-Means 工况聚类',2)
add_para(D,'系统默认使用 k=3，界面允许在 2 到 8 之间调整。算法以归一化后的辐照度、温度、功率、效率代理值和时间周期特征构成向量，使用固定随机种子 42 保持演示结果可复现。聚类结果用于后续分工况计算异常分数。')
add_heading(D,'4.3 孤立森林异常检测',2)
add_para(D,'系统在每个工况内部构建随机切分树，以记录的平均路径长度计算异常分数，再按照污染率 0.05 选取高分记录作为异常。当前实现为项目内可复核的纯 Python 版本；Spark 适配器在集群模式中负责读取输入并保持相同的处理契约，待安装 PySpark 和实际集群后再补充分布式运行证据。')
add_fig(D,alg,'图4.2 异常检测算法流程图')
add_heading(D,'第5章 系统实现',1)
add_heading(D,'5.1 后端接口实现',2)
add_para(D,'FastAPI 服务提供健康检查、数据集导入、运行创建、运行列表、总览、记录和告警查询接口。上传数据先写入 runtime/uploads，再创建数据集记录；运行完成后将结果写入 SQLite。异常分数和告警等级由同一运行结果产生，便于页面追溯。')
add_heading(D,'5.2 前端工作台实现',2)
add_para(D,'前端采用静态 HTML、CSS 和 JavaScript，使用 SVG 绘制曲线，避免核心页面依赖外部网络。页面包括运行总览、导入与运行、曲线分析、异常记录、告警中心和运行记录。合成演示数据提示在页面中持续显示，避免把演示数据误认为现场测量。')
for path,cap in [(ROOT/'evidence/screenshots/dashboard-overview-local.png','图5.1 运行总览界面'),(ROOT/'evidence/screenshots/dashboard-run-local.png','图5.2 导入与运行界面'),(ROOT/'evidence/screenshots/dashboard-curve-local.png','图5.3 曲线分析界面'),(ROOT/'evidence/screenshots/dashboard-anomalies-local.png','图5.4 异常记录界面'),(ROOT/'evidence/screenshots/dashboard-alerts-local.png','图5.5 告警中心界面')]: add_fig(D,path,cap,6.3)
add_heading(D,'5.3 启动与交付实现',2)
add_para(D,'项目根目录提供 start.cmd 和 stop.cmd。启动入口检查项目目录、日志目录和后端入口，使用本地 Python 环境启动 Uvicorn；停止入口只结束 runtime/m10.pid 记录的进程。当前 Windows x64 原生构建和无开发依赖离线包尚未完成，因此说明书将其标记为未验证。')
add_heading(D,'第6章 系统测试与结果分析',1)
add_heading(D,'6.1 测试环境',2)
add_table(D,['项目','实测环境'],[
 ('本地运行','macOS 27.0.1、Apple Silicon arm64、Python 3.13.3'),('接口服务','FastAPI 0.115.6、Uvicorn 0.34.0、SQLite'),('自动化测试','pytest 8.3.4，6 项通过'),('数据','固定种子合成演示 CSV，576 行')])
add_heading(D,'6.2 功能测试结果',2)
add_table(D,['测试项','预期结果','实际结果','状态'],[
 ('合法 CSV 导入','记录进入数据集','576 行有效记录','通过'),('处理运行','产生聚类和异常结果','3 类工况、29 条异常','通过'),('告警查询','异常记录生成告警','29 条告警可查询','通过'),('缺少字段','返回可读错误','测试通过','通过'),('重复与负值','统计并拒绝无效行','测试通过','通过'),('静态资源','首页、脚本和样式可访问','返回 200','通过')])
add_heading(D,'6.3 局限与未验证项',2)
add_para(D,'本轮结果只说明固定种子合成数据在本地模式中的处理链路能够运行，不能推导真实场站的识别准确率，也不能证明算法降低了现场误报。Spark/HDFS/MySQL 集群、真实公开数据子集、长期并发和 Windows x64 客户验收尚未执行。')
add_heading(D,'第7章 总结与展望',1)
add_para(D,'本文完成了一个面向光伏监测 CSV 的本地异常检测工作台，实现了数据导入、清洗、效率代理特征计算、K-Means 工况聚类、孤立森林异常检测、结果查询和告警展示。通过 576 条固定种子合成记录完成了接口、数据库和页面的端到端验证。')
add_para(D,'后续工作包括核验并接入具备明确许可的真实公开光伏数据，完成 Spark/HDFS/MySQL 容器联调，在 Windows 10/11 x64 环境构建离线包，并在独立样本上补充人工标注或可解释的评价指标。')
add_heading(D,'参考文献',1)
refs=[
 '苏立伟, 刘振华, 杜礼锋, 等. 基于GPU+Spark的电力大数据分析算法[J]. 沈阳工业大学学报, 2023, 45(4): 371-375.',
 '李磊, 王云, 邓洪波, 等. Spark云平台电力负载预测系统的设计与实现[J]. 实验室研究与探索, 2023, 42(5): 41-45.',
 '何志锋, 吴煜晖, 邹海青. 基于元数据模型的双面光伏发电系统发电量预测方法研究[J]. 太阳能, 2026(8): 61-68.',
 '李飞, 尹小平, 刘东旭, 等. 发电数据与告警数据驱动的光伏电站健康状态智能分析[J]. 中国信息化, 2025(6): 52-56.',
 '孔令宽, 周旭东, 张经纬. 基于大数据挖掘的光伏发电与储能电站安全智能控制系统[J]. 电子设计工程, 2025, 33(18): 96-100.',
 '李杰. 基于气象数据的光伏组件积灰损失评估方法研究[J]. 太阳能, 2024(9): 76-83.',
 '肖凤军, 白帆. 基于数据云平台的分布式光伏大数据平台开发与应用[J]. 吉林电力, 2023, 51(4): 39-41.',
 '徐俊峰. 基于Spark的光伏大数据分析平台设计与实现[D]. 南昌大学, 2023.',
 '王雪. 面向光伏应用的大数据处理研究[D]. 华北电力大学, 2023.',
 'Wang H, Chong W. Exploration on the Construction of Intelligent Big Data Platform of Ningxia Solar Photovoltaic Industry based on NB-IoT[J]. Journal of Electronic Research and Application, 2025, 9(2): 29-34.',
 'Armin Amiri Darban, Mohammad Rajabi Nasab, Arya Abdollahi. Anomaly detection in solar farms with a hybrid CNN-ViT model to enhance accuracy and efficiency[J]. International Journal of Ambient Energy, 2025, 46(1): 112-121.',
 'Gaurav Sharma, Savita Khurana, Bhawna Sharma, Geetanjali Sharma. A Self-Tuning Reinforcement Learning-Driven Isolation Forest Framework for Scalable and Efficient Anomaly Detection in Solar Power Plants[J]. International Journal of Computational Intelligence Systems, 2026, 19(3): 456-470.'
]
for i,ref in enumerate(refs,1):
 p=D.add_paragraph(); p.paragraph_format.left_indent=Cm(0.74); p.paragraph_format.first_line_indent=Cm(-0.74); p.paragraph_format.line_spacing=Pt(16); r=p.add_run(f'[{i}] {ref}'); r.font.name='宋体'; r._element.rPr.rFonts.set(qn('w:eastAsia'),'宋体'); r.font.size=Pt(10.5)
add_para(D,'文献说明：以上条目来自开题报告原始材料，当前稿件尚未完成 CNKI/VIP 逐条核验，也未补足规则要求的 18 篇合格条目。提交前需完成元数据、类型、年份和正文引注顺序审查。')
add_heading(D,'致谢',1)
add_para(D,'感谢指导教师在课题方向、技术路线和实现过程中的指导。感谢学校提供的学习与实验条件。')
add_heading(D,'附录A 接口与运行证据',1)
add_para(D,'本地运行证据保存在项目 evidence/runtime/api/local_integration.json，测试记录保存在 evidence/tests/TEST_REPORT.md，界面截图保存在 evidence/screenshots/。上述文件与本说明书使用同一轮本地运行结果。')
# save
out=OUT/'m10_毕业设计说明书_河北工业职业技术大学_v1.0_本地实测稿.docx'
D.save(out)
print(out)
