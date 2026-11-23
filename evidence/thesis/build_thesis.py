from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from PIL import Image, ImageDraw, ImageFont
import sys
import json

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'artifacts/thesis'
IMG=ROOT/'evidence/thesis/images'
OUT.mkdir(parents=True,exist_ok=True); IMG.mkdir(parents=True,exist_ok=True)
sys.path.insert(0, str(ROOT / 'evidence'))
from thesis_expansion_a import expand_chapter1, expand_chapter2
from thesis_expansion_b import expand_chapter3
from thesis_expansion_c import expand_chapter4, expand_chapter5, expand_chapter6, expand_chapter7
private_path = ROOT / 'project_private.json'
private = json.loads(private_path.read_text(encoding='utf-8')) if private_path.exists() else {}
student = private.get('student', {})
student_name = student.get('name') or '待填写'
student_id = student.get('student_id') or '待填写'
advisor = private.get('advisor') or '待填写'
FONT='/System/Library/Fonts/Supplemental/Songti.ttc'
LOGO=IMG/'hebei_logo.jpeg'
BODY_EA='宋体'
HEAD_EA='黑体'
ASCII='Times New Roman'
EN_TITLE='Arial'
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

def set_run_font(run, east=BODY_EA, ascii_font=ASCII, size=12, bold=None, italic=None):
    """Set all Word font slots explicitly so Word/LibreOffice do not substitute fonts."""
    run.font.name=ascii_font
    run.font.size=Pt(size)
    run.font.color.rgb=RGBColor(0,0,0)
    if bold is not None: run.bold=bold
    if italic is not None: run.italic=italic
    rpr=run._element.get_or_add_rPr()
    rfonts=rpr.find(qn('w:rFonts'))
    if rfonts is None:
        rfonts=OxmlElement('w:rFonts'); rpr.insert(0,rfonts)
    for attr,value in [('ascii',ascii_font),('hAnsi',ascii_font),('eastAsia',east),('cs',ascii_font)]:
        rfonts.set(qn(f'w:{attr}'),value)
    return run

def set_para_format(p, alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, before=0, after=0, line=20, first=24, left=None):
    pf=p.paragraph_format
    pf.alignment=alignment
    pf.space_before=Pt(before)
    pf.space_after=Pt(after)
    pf.line_spacing=Pt(line)
    pf.first_line_indent=Pt(first) if first is not None else None
    if left is not None: pf.left_indent=Cm(left)
    return p

def set_cell_border(cell, **kwargs):
    """Apply a border to one cell; used to make explicit, portable three-line tables."""
    tcPr=cell._tc.get_or_add_tcPr()
    tcBorders=tcPr.first_child_found_in('w:tcBorders')
    if tcBorders is None:
        tcBorders=OxmlElement('w:tcBorders'); tcPr.append(tcBorders)
    for edge,edge_data in kwargs.items():
        tag='w:{}'.format(edge)
        element=tcBorders.find(qn(tag))
        if element is None:
            element=OxmlElement(tag); tcBorders.append(element)
        for key,value in edge_data.items(): element.set(qn('w:{}'.format(key)),str(value))

def apply_three_line_table(table):
    """Top rule + header rule + bottom rule, with all vertical/internal rules removed."""
    tblPr=table._tbl.tblPr
    tblBorders=tblPr.first_child_found_in('w:tblBorders')
    if tblBorders is None:
        tblBorders=OxmlElement('w:tblBorders'); tblPr.append(tblBorders)
    specs={'top':('single','12'),'bottom':('single','12'),'insideH':('nil','0'),'insideV':('nil','0'),'left':('nil','0'),'right':('nil','0')}
    for edge,(val,sz) in specs.items():
        el=tblBorders.find(qn(f'w:{edge}'))
        if el is None: el=OxmlElement(f'w:{edge}'); tblBorders.append(el)
        el.set(qn('w:val'),val); el.set(qn('w:sz'),sz); el.set(qn('w:space'),'0'); el.set(qn('w:color'),'000000')
    for ri,row in enumerate(table.rows):
        for cell in row.cells:
            edges={}
            if ri==0: edges['top']={'val':'single','sz':'12','space':'0','color':'000000'}
            if ri==0: edges['bottom']={'val':'single','sz':'8','space':'0','color':'000000'}
            if ri==len(table.rows)-1: edges['bottom']={'val':'single','sz':'12','space':'0','color':'000000'}
            edges.update({'left':{'val':'nil','sz':'0'},'right':{'val':'nil','sz':'0'}})
            set_cell_border(cell, **edges)

def set_cell_text(cell,text,bold=False):
    cell.text=''
    p=cell.paragraphs[0]
    set_para_format(p, alignment=WD_ALIGN_PARAGRAPH.CENTER, before=0, after=0, line=16, first=0)
    r=p.add_run(str(text)); set_run_font(r, BODY_EA, ASCII, 11, bold=bold)
    cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER

def add_table(doc, caption, headers, rows):
    # Keep a table title attached to its table so a page break never leaves a
    # caption stranded at the bottom of the previous page.
    table_caption = add_caption(doc, caption)
    table_caption.paragraph_format.keep_with_next = True
    table=doc.add_table(rows=1, cols=len(headers)); table.alignment=WD_TABLE_ALIGNMENT.CENTER
    try: table.style='Table Normal'
    except Exception: pass
    # Mark the first row as a repeating/header row for editable DOCX readers.
    trPr = table.rows[0]._tr.get_or_add_trPr()
    tblHeader = OxmlElement('w:tblHeader'); tblHeader.set(qn('w:val'), 'true'); trPr.append(tblHeader)
    for i,h in enumerate(headers): set_cell_text(table.rows[0].cells[i],h,True)
    for row in rows:
        cells=table.add_row().cells
        for i,v in enumerate(row): set_cell_text(cells[i],v)
    apply_three_line_table(table)
    spacer=doc.add_paragraph(); set_para_format(spacer, alignment=WD_ALIGN_PARAGRAPH.LEFT, before=0, after=0, line=12, first=0)
    return table

def add_caption(doc, text):
    p=doc.add_paragraph(); set_para_format(p, alignment=WD_ALIGN_PARAGRAPH.CENTER, before=3, after=3, line=16, first=0)
    r=p.add_run(text); set_run_font(r, HEAD_EA, ASCII, 11, bold=False)
    return p

def add_fig(doc, path, caption, width=6.2):
    p=doc.add_paragraph(); set_para_format(p, alignment=WD_ALIGN_PARAGRAPH.CENTER, before=0, after=0, line=16, first=0)
    # Inline figures must not inherit an exact 16 pt line box, otherwise LibreOffice clips
    # the image to a thin strip. A single-line box lets the image determine its own height.
    p.paragraph_format.line_spacing=1.0
    # Keep the figure and its caption together when a page break is needed.
    p.paragraph_format.keep_with_next = True
    run = p.add_run(); inline = run.add_picture(str(path),width=Inches(width))
    # Keep captions visible while also adding descriptive metadata for screen
    # readers and accessibility auditors.
    doc_pr = inline._inline.docPr
    doc_pr.set('title', caption)
    doc_pr.set('descr', caption)
    add_caption(doc,caption)

def add_para(doc,text,style=None):
    p=doc.add_paragraph(style=style)
    set_para_format(p, alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, before=0, after=0, line=20, first=24)
    r=p.add_run(text); set_run_font(r, BODY_EA, ASCII, 12)
    return p

def add_en_para(doc,text):
    p=doc.add_paragraph(); set_para_format(p, alignment=WD_ALIGN_PARAGRAPH.JUSTIFY, before=0, after=0, line=20, first=0)
    r=p.add_run(text); set_run_font(r, ASCII, ASCII, 12)
    return p

def add_heading(doc,text,level):
    p=doc.add_paragraph(style=f'Heading {level}')
    cfg={1:(WD_ALIGN_PARAGRAPH.CENTER,40,20,15),2:(WD_ALIGN_PARAGRAPH.LEFT,24,6,14),3:(WD_ALIGN_PARAGRAPH.LEFT,12,6,13)}[level]
    set_para_format(p, alignment=cfg[0], before=cfg[1], after=cfg[2], line=20, first=0)
    p.paragraph_format.keep_with_next=True
    r=p.add_run(text); set_run_font(r, HEAD_EA, ASCII, cfg[3], bold=True)
    return p

def add_toc(doc):
    p=doc.add_paragraph(); set_para_format(p, alignment=WD_ALIGN_PARAGRAPH.CENTER, before=40, after=20, line=20, first=0)
    r=p.add_run('目  录'); set_run_font(r, HEAD_EA, ASCII, 15, bold=True)
    entries=[
        ('第1章 绪论','1'),('1.1 研究背景','1'),('1.2 研究内容','1'),('1.3 论文组织','1'),
        ('第2章 相关技术与需求分析','3'),('2.1 相关技术','3'),('2.2 功能需求','3'),('2.3 非功能需求','3'),
        ('第3章 系统总体设计','6'),('3.1 总体架构','6'),('3.2 功能模块设计','6'),('3.3 数据库设计','7'),
        ('第4章 数据处理与异常检测算法设计','12'),('4.1 数据清洗与特征计算','12'),('4.2 K-Means 工况聚类','13'),('4.3 孤立森林异常检测','13'),
        ('第5章 系统实现','16'),('5.1 后端接口实现','16'),('5.2 前端工作台实现','16'),('5.3 启动与交付实现','19'),
        ('第6章 系统测试与结果分析','22'),('6.1 测试环境','22'),('6.2 功能测试结果','22'),('6.3 局限与未验证项','23'),
        ('第7章 总结与展望','26'),('参考文献','27'),('致谢','29'),('附录A 接口与运行证据','29')]
    for title,page in entries:
        p=doc.add_paragraph(); set_para_format(p, alignment=WD_ALIGN_PARAGRAPH.LEFT, before=0, after=0, line=20, first=0, left=0.4)
        r=p.add_run(f'{title}'+'.'*(max(3,52-len(title)*2))+page); set_run_font(r, HEAD_EA if title.startswith('第') or title in ('参考文献','致谢') or title.startswith('附录') else BODY_EA, ASCII, 12)
    doc.add_page_break()

# document
D=Document()

def configure_section(section, body=False):
    section.page_width=Cm(21); section.page_height=Cm(29.7)
    section.top_margin=Cm(2.5); section.bottom_margin=Cm(2.0)
    section.left_margin=Cm(2.0); section.right_margin=Cm(2.0)
    section.gutter=Cm(0.5); section.header_distance=Cm(1.5); section.footer_distance=Cm(1.75)
    section.header.is_linked_to_previous=False; section.footer.is_linked_to_previous=False
    for p in section.header.paragraphs + section.footer.paragraphs:
        p.clear()
    if body:
        hp=section.header.paragraphs[0]
        set_para_format(hp, alignment=WD_ALIGN_PARAGRAPH.CENTER, before=0, after=0, line=20, first=0)
        set_run_font(hp.add_run('河北工业职业技术大学毕业设计（论文）'), BODY_EA, ASCII, 10.5)
        fp=section.footer.paragraphs[0]
        set_para_format(fp, alignment=WD_ALIGN_PARAGRAPH.CENTER, before=0, after=0, line=20, first=0)
        add_field(fp, 'PAGE', '1')
        sectPr=section._sectPr
        pgNum=sectPr.find(qn('w:pgNumType'))
        if pgNum is None:
            pgNum=OxmlElement('w:pgNumType'); sectPr.append(pgNum)
        pgNum.set(qn('w:start'),'1'); pgNum.set(qn('w:fmt'),'decimal')

def add_field(paragraph, instruction, display='1'):
    for kind, value in [('begin',None),('instr',instruction),('separate',None),('text',display),('end',None)]:
        run=paragraph.add_run(); set_run_font(run, ASCII, ASCII, 10.5)
        if kind=='instr':
            el=OxmlElement('w:instrText'); el.set(qn('xml:space'),'preserve'); el.text=value; run._r.append(el)
        elif kind in ('begin','separate','end'):
            el=OxmlElement('w:fldChar'); el.set(qn('w:fldCharType'),kind); run._r.append(el)
        else:
            run.text=value

configure_section(D.sections[0], body=False)
styles=D.styles
for name in ['Normal','Body Text']:
    st=styles[name]; st.font.name=ASCII; st.font.size=Pt(12)
    rpr=st._element.get_or_add_rPr(); rf=rpr.rFonts
    if rf is None: rf=OxmlElement('w:rFonts'); rpr.insert(0,rf)
    rf.set(qn('w:ascii'),ASCII); rf.set(qn('w:hAnsi'),ASCII); rf.set(qn('w:eastAsia'),BODY_EA); rf.set(qn('w:cs'),ASCII)
    pf=st.paragraph_format; pf.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY; pf.first_line_indent=Pt(24); pf.line_spacing=Pt(20); pf.space_before=Pt(0); pf.space_after=Pt(0)
for i,(align,before,after,size) in {1:(WD_ALIGN_PARAGRAPH.CENTER,40,20,15),2:(WD_ALIGN_PARAGRAPH.LEFT,24,6,14),3:(WD_ALIGN_PARAGRAPH.LEFT,12,6,13)}.items():
    st=styles[f'Heading {i}']; st.font.name=ASCII; st.font.size=Pt(size); st.font.bold=True
    rpr=st._element.get_or_add_rPr(); rf=rpr.rFonts
    if rf is None: rf=OxmlElement('w:rFonts'); rpr.insert(0,rf)
    rf.set(qn('w:ascii'),ASCII); rf.set(qn('w:hAnsi'),ASCII); rf.set(qn('w:eastAsia'),HEAD_EA); rf.set(qn('w:cs'),ASCII)
    pf=st.paragraph_format; pf.alignment=align; pf.first_line_indent=Pt(0); pf.line_spacing=Pt(20); pf.space_before=Pt(before); pf.space_after=Pt(after)

# Cover follows the v1.0 template's logo, centered title block, rule and student-information block.
for _ in range(1): D.add_paragraph('')
if LOGO.exists():
    p=D.add_paragraph(); set_para_format(p,alignment=WD_ALIGN_PARAGRAPH.CENTER,before=0,after=12,line=20,first=0)
    p.paragraph_format.line_spacing=1.0
    run=p.add_run(); logo_inline = run.add_picture(str(LOGO),width=Inches(3.7))
    logo_doc_pr = logo_inline._inline.docPr
    logo_doc_pr.set('title', '河北工业职业技术大学校徽')
    logo_doc_pr.set('descr', '河北工业职业技术大学校徽')
for _ in range(1): D.add_paragraph('')
title_block=D.add_table(rows=2, cols=1); title_block.alignment=WD_TABLE_ALIGNMENT.CENTER
try: title_block.style='Table Normal'
except Exception: pass
for row in title_block.rows:
    for cell in row.cells:
        set_cell_border(cell, top={'val':'nil','sz':'0'}, bottom={'val':'nil','sz':'0'}, left={'val':'nil','sz':'0'}, right={'val':'nil','sz':'0'})
        cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
title_block.cell(0,0).paragraphs[0].clear(); p=title_block.cell(0,0).paragraphs[0]; set_para_format(p,alignment=WD_ALIGN_PARAGRAPH.CENTER,before=0,after=0,line=28,first=0); set_run_font(p.add_run('毕业设计'),HEAD_EA,ASCII,42,bold=True)
title_block.cell(1,0).paragraphs[0].clear(); p=title_block.cell(1,0).paragraphs[0]; set_para_format(p,alignment=WD_ALIGN_PARAGRAPH.CENTER,before=0,after=0,line=28,first=0); set_run_font(p.add_run('基于Spark的光伏电站发电效率异常检测系统的设计与实现'),HEAD_EA,ASCII,26,bold=True)
rule=D.add_paragraph(); set_para_format(rule,alignment=WD_ALIGN_PARAGRAPH.CENTER,before=10,after=12,line=8,first=0)
pPr=rule._p.get_or_add_pPr(); pBdr=OxmlElement('w:pBdr'); bottom=OxmlElement('w:bottom'); bottom.set(qn('w:val'),'single'); bottom.set(qn('w:sz'),'4'); bottom.set(qn('w:space'),'1'); bottom.set(qn('w:color'),'000000'); pBdr.append(bottom); pPr.append(pBdr)
cover_table=D.add_table(rows=7, cols=4); cover_table.alignment=WD_TABLE_ALIGNMENT.CENTER; cover_table.autofit=False
try: cover_table.style='Table Normal'
except Exception: pass
widths=[Cm(3.0),Cm(2.3),Cm(1.8),Cm(3.5)]
for row in cover_table.rows:
    row.height=Cm(0.72)
    for i,cell in enumerate(row.cells):
        cell.width=widths[i]; cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
        set_cell_border(cell,top={'val':'nil','sz':'0'},bottom={'val':'nil','sz':'0'},left={'val':'nil','sz':'0'},right={'val':'nil','sz':'0'})
def cover_cell(cell,text,bold=False,underline=False):
    cell.text=''; p=cell.paragraphs[0]; set_para_format(p,alignment=WD_ALIGN_PARAGRAPH.CENTER,before=0,after=0,line=20,first=0)
    set_run_font(p.add_run(text),BODY_EA,ASCII,13,bold=bold)
    if underline: set_cell_border(cell,bottom={'val':'single','sz':'4','space':'0','color':'000000'})
cover_rows=[('姓    名',student_name,'', ''),('学    号',student_id,'', ''),('学    院','人工智能学院','', ''),('专    业','大数据工程技术','', ''),('指导教师',advisor,'职  称',''),('企业指导教师','','职  称',''),('企业指导教师单位','','','')]
for ri,(a,b,c,e) in enumerate(cover_rows):
    cover_cell(cover_table.cell(ri,0),a,True)
    if ri==6:
        merged=cover_table.cell(ri,1).merge(cover_table.cell(ri,3)); cover_cell(merged,'',False,True)
    elif c:
        cover_cell(cover_table.cell(ri,1),b,False,True); cover_cell(cover_table.cell(ri,2),c,True); cover_cell(cover_table.cell(ri,3),e,False,True)
    else:
        merged=cover_table.cell(ri,1).merge(cover_table.cell(ri,3)); cover_cell(merged,b,False,True)
D.add_paragraph('')
D.add_page_break()
# declaration
add_heading(D,'毕业设计原创性声明',1)
add_para(D,'本人所提交的毕业设计《基于Spark的光伏电站发电效率异常检测系统的设计与实现》，是在指导教师指导下完成的设计工作。除文中已经注明引用的内容外，本说明书不包含其他个人或集体已经发表或撰写过的研究成果。本文同时使用项目固定种子合成演示数据和注明来源的 NREL/DOE PVDAQ 公共数据，数据性质、许可和字段代理关系均已在正文与证据材料中标明。')
add_para(D,'本人承诺对本说明书内容的真实性和完整性负责。')
D.add_paragraph('')
p=D.add_paragraph(); set_para_format(p,alignment=WD_ALIGN_PARAGRAPH.LEFT,before=0,after=0,line=20,first=0,left=3.5); set_run_font(p.add_run('作者签名：________________    指导教师签名：________________'),BODY_EA,ASCII,12)
p=D.add_paragraph(); set_para_format(p,alignment=WD_ALIGN_PARAGRAPH.LEFT,before=0,after=0,line=20,first=0,left=3.5); set_run_font(p.add_run('年   月   日                 年   月   日'),BODY_EA,ASCII,12)
D.add_page_break()
# copyright authorization page from the v1.0 template
add_heading(D,'毕业设计版权使用授权书',1)
add_para(D,'本毕业设计作者完全了解河北工业职业技术大学有权保留并向国家有关部门或机构送交毕业设计的复印件和磁盘，允许毕业设计被查阅和借阅。本人授权河北工业职业技术大学可以将毕业设计的全部或部分内容编入有关数据库进行检索，可以采用影印、缩印或其他复制手段保存、汇编毕业设计。')
add_para(D,'本毕业设计属于：')
p=D.add_paragraph(); set_para_format(p,alignment=WD_ALIGN_PARAGRAPH.LEFT,before=0,after=0,line=20,first=48); set_run_font(p.add_run('□ 公开'),BODY_EA,ASCII,12)
p=D.add_paragraph(); set_para_format(p,alignment=WD_ALIGN_PARAGRAPH.LEFT,before=0,after=0,line=20,first=48); set_run_font(p.add_run('□     个月后公开，公开后适用本授权书'),BODY_EA,ASCII,12)
p=D.add_paragraph(); set_para_format(p,alignment=WD_ALIGN_PARAGRAPH.LEFT,before=0,after=0,line=20,first=48); set_run_font(p.add_run('（请在以上方框内打“√”）'),BODY_EA,ASCII,12)
p=D.add_paragraph(); set_para_format(p,alignment=WD_ALIGN_PARAGRAPH.LEFT,before=24,after=0,line=20,first=0,left=3.5); set_run_font(p.add_run('作者签名：________________    指导教师签名：________________'),BODY_EA,ASCII,12)
p=D.add_paragraph(); set_para_format(p,alignment=WD_ALIGN_PARAGRAPH.LEFT,before=0,after=0,line=20,first=0,left=3.5); set_run_font(p.add_run('年   月   日                 年   月   日'),BODY_EA,ASCII,12)
D.add_page_break()
# abstracts
add_heading(D,'摘  要',1)
add_para(D,'针对光伏电站监测数据规模增长、环境因素导致发电波动明显以及人工巡检难以及时定位低效记录的问题，本文设计并实现了一套基于 Spark 的光伏电站发电效率异常检测系统。系统以 CSV 时序数据为输入，完成字段校验、重复记录处理、数值清洗和效率代理特征计算；在本地模式中使用固定种子实现 K-Means 工况聚类和孤立森林异常检测，并通过 FastAPI 与静态 Web 页面展示发电曲线、工况分布、异常记录和告警信息。当前本地实测覆盖两类数据：576 条固定种子合成演示记录形成 3 类工况、29 条异常和 29 条告警；NREL/DOE PVDAQ system 2107 的 2022 年 6 月规范化切片包含 1686 条真实公开记录，形成 3 类工况、85 条异常和 85 条告警。Docker Desktop 集群联调已验证 Spark 读取、HDFS 写入回读和 MySQL 持久化；Windows x64 客户环境仍需独立验收；PVDAQ 源数据未提供模块温度通道，规范化文件将环境温度代理写入 module_temp_c 并单独标注。')
p=D.add_paragraph(); set_para_format(p,alignment=WD_ALIGN_PARAGRAPH.LEFT,before=0,after=0,line=20,first=0); set_run_font(p.add_run('关键词：光伏电站；Spark；K-Means；孤立森林；异常检测'),BODY_EA,ASCII,12)
D.add_page_break()
add_heading(D,'ABSTRACT',1)
add_en_para(D,'To address the difficulty of processing photovoltaic monitoring records and locating inefficient operating records under changing environmental conditions, this project designs and implements a photovoltaic generation efficiency anomaly detection system based on Spark. The system validates and cleans CSV time-series data, calculates an efficiency proxy, performs operating-condition clustering with K-Means, and detects anomalies with an isolation-forest implementation in local mode. A FastAPI service and an offline static web interface provide trend charts, cluster summaries, anomaly records, and alerts. Two data paths were verified: 576 deterministic synthetic records produced three clusters, 29 anomaly records, and 29 alerts; a 1,686-record June 2022 slice from NREL/DOE PVDAQ system 2107 produced three clusters, 85 anomaly records, and 85 alerts. The public source does not publish a module-temperature channel for this system, so the normalized input records the ambient-temperature proxy explicitly. Docker Desktop cluster rehearsal verified Spark execution, HDFS write/read-back, and MySQL persistence; Windows x64 acceptance remains pending.')
p=D.add_paragraph(); set_para_format(p,alignment=WD_ALIGN_PARAGRAPH.LEFT,before=0,after=0,line=20,first=0); set_run_font(p.add_run('Key words: photovoltaic power station; Spark; K-Means; isolation forest; anomaly detection'),ASCII,ASCII,12,bold=False)
D.add_page_break(); add_toc(D)
# Body section starts with the official header and page-number field.
body_section=D.add_section(WD_SECTION.NEW_PAGE); configure_section(body_section, body=True)
# chapters
add_heading(D,'第1章 绪论',1)
add_heading(D,'1.1 研究背景',2)
add_para(D,'光伏电站的辐照度、环境温度、组件温度和输出功率具有明显的时序波动。相同设备在不同天气和时段下会产生不同的输出水平，使用单一固定阈值容易把正常的气象变化判断为设备异常。运维人员需要一种能够整理多字段监测记录、区分运行工况并给出异常线索的工具。')
add_heading(D,'1.2 研究内容',2)
add_para(D,'本项目围绕数据导入与清洗、效率代理特征计算、工况聚类、异常检测、结果查询和告警展示展开。实现阶段优先完成不依赖外部设备的 CSV 工作流，并把 Spark/HDFS/MySQL 集群作为可切换的联调路线。')
add_heading(D,'1.3 论文组织',2)
add_para(D,'全文依次介绍需求与相关技术、系统设计、数据处理与算法、系统实现、测试结果以及结论和局限。系统截图与测试结果均指向本地运行证据，合成演示数据、Docker 集群结果和仍未验证的 Windows 环境分别说明。')
expand_chapter1(lambda text, level: add_heading(D, text, level), lambda text: add_para(D, text))
add_heading(D,'第2章 相关技术与需求分析',1)
add_heading(D,'2.1 相关技术',2)
add_para(D,'Spark 用于表达分布式数据处理路线，K-Means 用于把输入记录划分为若干运行工况，孤立森林通过随机切分形成路径长度差异，用于识别相对孤立的记录。FastAPI 提供轻量 HTTP 接口，HTML、CSS 和 JavaScript 提供无需 CDN 的本地页面。SQLite 用于便携模式，数据库结构保留向 MySQL 迁移的表和字段边界。')
add_heading(D,'2.2 功能需求',2)
add_table(D,'表 2.1 功能需求表',['编号','需求','输入','输出'],[
 ('R1','导入数据集','UTF-8 CSV','数据集记录与清洗统计'),('R2','处理运行','数据集、k、污染率','运行状态与算法结果'),('R3','结果查询','运行编号、过滤条件','曲线、异常记录、告警'),('R4','运行追溯','历史运行','参数、数据规模与状态')])
add_heading(D,'2.3 非功能需求',2)
add_para(D,'页面应能在普通浏览器中打开，核心展示不依赖公网 CDN；输入错误应有可读提示；重复运行不清空已有记录；Docker 开发集群、客户 Windows 环境和论文结果的验证边界分开记录。')
expand_chapter2(lambda text, level: add_heading(D, text, level), lambda text: add_para(D, text), lambda caption, headers, rows: add_table(D, caption, headers, rows))
add_heading(D,'第3章 系统总体设计',1)
add_heading(D,'3.1 总体架构',2); add_para(D,'系统由浏览器表示层、FastAPI 接口层、本地或 Spark 处理层、SQLite/MySQL 数据层和 CSV/HDFS 文件层组成。本地模式使用 SQLite 和本地文件；Docker 集群模式已实测 Spark、HDFS 与 MySQL 的联动。')
add_fig(D,arch,'图3.1 系统总体架构图')
add_heading(D,'3.2 功能模块设计',2); add_para(D,'系统功能按数据接入、清洗与特征计算、工况聚类、异常检测、结果查询、曲线分析和告警管理划分。模块之间的执行先后由处理流程表达，模块图只表达职责边界。')
add_fig(D,mod,'图3.2 系统功能模块图')
add_heading(D,'3.3 数据库设计',2)
add_para(D,'数据库核心对象包括 datasets、processing_runs、records 和 alerts。数据集记录来源文件和清洗统计，处理运行记录模式与参数，检测记录保存输入字段、效率代理值、工况编号和异常分数，告警记录关联异常记录并保存等级和提示。')
add_fig(D,er,'图3.3 核心实体关系图')
add_table(D,'表 3.1 核心数据库对象',['表名','主要字段','用途'],[
 ('datasets','id、filename、row_count、source_sha256','记录数据集来源和清洗统计'),('processing_runs','id、dataset_id、mode、params_json、status','追踪一次处理运行'),('records','timestamp、station_id、power_kw、cluster_id、anomaly_score','保存逐条检测结果'),('alerts','run_id、record_id、severity、message','保存需要复核的告警')])
expand_chapter3(lambda text, level: add_heading(D, text, level), lambda text: add_para(D, text), lambda caption, headers, rows: add_table(D, caption, headers, rows))
add_heading(D,'第4章 数据处理与异常检测算法设计',1)
add_heading(D,'4.1 数据清洗与特征计算',2)
add_para(D,'系统要求 timestamp、station_id、irradiance_w_m2、ambient_temp_c、module_temp_c 和 power_kw 六个字段。程序解析时间和数值，拒绝无法解析的记录以及负辐照度和负功率，按时间与站点去重并保留最后一条记录。效率代理值定义为 power_kw / max(irradiance_w_m2, 1)，同时加入小时周期特征。')
add_fig(D,flow,'图4.1 本地处理流程图')
add_heading(D,'4.2 K-Means 工况聚类',2)
add_para(D,'系统默认使用 k=3，界面允许在 2 到 8 之间调整。算法以归一化后的辐照度、温度、功率、效率代理值和时间周期特征构成向量，使用固定随机种子 42 保持演示结果可复现。聚类结果用于后续分工况计算异常分数。')
add_heading(D,'4.3 孤立森林异常检测',2)
add_para(D,'系统在每个工况内部构建随机切分树，以记录的平均路径长度计算异常分数，再按照污染率 0.05 选取高分记录作为异常。当前实现为项目内可复核的纯 Python 版本；Spark 适配器在集群模式中读取输入并将 Parquet 写入 HDFS 后回读校验行数，处理结果继续使用同一契约落入 MySQL。')
add_fig(D,alg,'图4.2 异常检测算法流程图')
expand_chapter4(lambda text, level: add_heading(D, text, level), lambda text: add_para(D, text), lambda caption, headers, rows: add_table(D, caption, headers, rows))
add_heading(D,'第5章 系统实现',1)
add_heading(D,'5.1 后端接口实现',2)
add_para(D,'FastAPI 服务提供健康检查、数据集导入、运行创建、运行列表、总览、记录和告警查询接口。上传数据先写入 runtime/uploads，再创建数据集记录；运行完成后将结果写入 SQLite。异常分数和告警等级由同一运行结果产生，便于页面追溯；Docker 集群运行时结果持久化到 MySQL。')
add_heading(D,'5.2 前端工作台实现',2)
add_para(D,'前端采用静态 HTML、CSS 和 JavaScript，使用 SVG 绘制曲线，避免核心页面依赖外部网络。页面包括运行总览、导入与运行、曲线分析、异常记录、告警中心和运行记录。页面可导入合成演示 CSV，也可导入 PVDAQ 规范化真实数据；数据来源和 module_temp_c 代理关系在运行证据中持续标明，避免把不同数据性质混为一谈。')
for path,cap in [(ROOT/'evidence/screenshots/dashboard-overview-local.png','图5.1 运行总览界面'),(ROOT/'evidence/screenshots/dashboard-run-local.png','图5.2 导入与运行界面'),(ROOT/'evidence/screenshots/dashboard-curve-local.png','图5.3 曲线分析界面'),(ROOT/'evidence/screenshots/dashboard-anomalies-local.png','图5.4 异常记录界面'),(ROOT/'evidence/screenshots/dashboard-alerts-local.png','图5.5 告警中心界面')]: add_fig(D,path,cap,5.8)
add_heading(D,'5.3 启动与交付实现',2)
add_para(D,'项目根目录提供 start.cmd 和 stop.cmd。启动入口检查项目目录、日志目录和后端入口，使用本地 Python 环境启动 Uvicorn；停止入口只结束 runtime/m10.pid 记录的进程。当前 Windows x64 原生构建和无开发依赖离线包尚未完成，因此说明书将其标记为未验证。')
expand_chapter5(lambda text, level: add_heading(D, text, level), lambda text: add_para(D, text), lambda caption, headers, rows: add_table(D, caption, headers, rows))
add_heading(D,'第6章 系统测试与结果分析',1)
add_heading(D,'6.1 测试环境',2)
add_table(D,'表 6.1 测试环境',['项目','实测环境'],[
 ('本地运行','macOS 27.0.1、Apple Silicon arm64、Python 3.13.3'),('接口服务','FastAPI 0.115.6、Uvicorn 0.34.0、SQLite'),('Docker 集群','Spark 3.5.3、HDFS 3.2.1、MySQL 8.4，API 运行成功'),('自动化测试','pytest 8.3.4，8 项通过'),('合成数据','固定种子演示 CSV，576 行'),('真实数据','NREL/DOE PVDAQ system 2107，2022-06 切片，1686 行')])
add_heading(D,'6.2 功能测试结果',2)
add_table(D,'表 6.2 功能测试结果',['测试项','预期结果','实际结果','状态'],[
 ('合成 CSV 导入','记录进入数据集','576 行有效记录','通过'),('合成处理运行','产生聚类和异常结果','3 类工况、29 条异常','通过'),('真实 CSV 导入','真实记录符合输入契约','1686 行有效记录','通过'),('真实处理运行','真实记录完成同一处理链','3 类工况、85 条异常','通过'),('告警查询','异常记录生成告警','29/85 条告警可查询','通过'),('缺少字段','返回可读错误','测试通过','通过'),('重复与负值','统计并拒绝无效行','测试通过','通过'),('静态资源','首页、脚本和样式可访问','返回 200','通过')])
add_heading(D,'6.3 局限与未验证项',2)
add_para(D,'本轮结果证明合成数据和一个许可清晰的 PVDAQ 公开数据切片都能完成导入、处理和告警生成；Docker Desktop 集群还验证了 Spark 执行、HDFS 写入回读和 MySQL 持久化。但这些结果不能推导真实场站的识别准确率，也不能证明算法降低了现场误报。PVDAQ system 2107 未发布模块温度通道，规范化文件以环境温度代理 module_temp_c，这一映射会影响特征解释。长期并发和 Windows x64 客户验收仍未执行。')
expand_chapter6(lambda text, level: add_heading(D, text, level), lambda text: add_para(D, text), lambda caption, headers, rows: add_table(D, caption, headers, rows))
add_heading(D,'第7章 总结与展望',1)
add_para(D,'本文完成了一个面向光伏监测 CSV 的本地异常检测工作台，实现了数据导入、清洗、效率代理特征计算、K-Means 工况聚类、孤立森林异常检测、结果查询和告警展示。系统分别使用 576 条固定种子合成记录和 1686 条 PVDAQ system 2107 真实公开记录完成了本地接口、数据库和页面联调，并在 Docker Desktop 集群中完成 Spark、HDFS 与 MySQL 的真实链路验证。')
add_para(D,'后续工作包括在 Windows 10/11 x64 环境构建离线包，补充独立样本上的人工标注或可解释评价指标，并在获得模块温度实测通道后替换当前环境温度代理。')
expand_chapter7(lambda text, level: add_heading(D, text, level), lambda text: add_para(D, text))
add_heading(D,'参考文献',1)
refs=[
 '马天东, 耿天翔, 李峰, 等. 光伏电站功率数据异常检测技术研究综述[J]. 微型电脑应用, 2024, 40(07): 72-75, 92.',
 '马天东, 耿天翔, 李峰, 钟海亮. 基于优化变点-四分位法的光伏异常数据检测[J]. 微型电脑应用, 2024, 40(06): 105-108.',
 '裘愉涛, 张磊, 周开运, 等. 基于图像特征检测的光伏异常数据识别算法[J]. 浙江电力, 2025, 44(05): 42-52. DOI:10.19585/j.zjdl.202505005.',
 '祁炜雯, 张俊, 吴洋, 等. 基于改进BP-Bagging算法的光伏电站故障诊断方法[J]. 浙江电力, 2024, 43(03): 65-74. DOI:10.19585/j.zjdl.202403008.',
 '徐恒辉, 姚杰, 周萍, 等. 基于运行数据的光伏电站状态评估方法研究[J]. 电力科技与环保, 2023, 39(05): 450-456.',
 '程航, 张晖, 代家昆, 等. 基于数据驱动和概率神经网络的光伏阵列智能故障诊断与监控[J]. 微型电脑应用, 2026, 42(07): 21-24, 29.',
 '徐志保, 张认成. 结合小波变换与支持向量机的光伏阵列故障检测算法[J]. 吉林大学学报（信息科学版）, 2026, 44(05): 1169-1176. DOI:10.19292/j.cnki.jdxxp.2026.05.010.',
 '龚莺飞, 鲁宗相, 乔颖, 等. 基于Copula理论的光伏功率高比例异常数据机器识别算法[J]. 电力系统自动化, 2016, 40(09): 16-22.',
 '杨茂, 孟玲建, 李大勇, 等. 基于类3σ准则的光伏功率异常数据识别[J]. 可再生能源, 2018, 36(10): 1443-1448.',
 '杨茂, 黄鑫. 基于光照过程特征分析的光伏功率异常数据识别算法[J]. 电力系统自动化, 2019, 43(06): 64-69.',
 'Wang X, Du J, Zhang G, et al. State space model for anomaly detection of distributed photovoltaic power generation systems[J]. Energy Informatics, 2025, 8: 141. DOI:10.1186/s42162-025-00598-2.',
 'Miraftabzadeh S M, Longo M, Leva S, et al. Data anomaly detection in photovoltaic power time-series via unsupervised deep learning with insufficient information[J]. Sustainable Energy, Grids and Networks, 2025, 43: 101769. DOI:10.1016/j.segan.2025.101769.',
 'Li D, Zhang Y, Yang Z, et al. Sensing anomaly of photovoltaic systems with sequential conditional variational autoencoder[J]. Applied Energy, 2024, 353: 122124. DOI:10.1016/j.apenergy.2023.122124.',
 'El-Banby G M, Moawad N M, Abouzalm B A, et al. Photovoltaic system fault detection techniques: a review[J]. Neural Computing and Applications, 2023, 35: 24829-24842. DOI:10.1007/s00521-023-09041-7.',
 'Ibrahim M, Alsheikh A, Awaysheh F M, et al. Machine learning schemes for anomaly detection in solar power plants[J]. Energies, 2022, 15(03): 1082. DOI:10.3390/en15031082.',
 'Branco P, Gonçalves F, Costa A C. Tailored algorithms for anomaly detection in photovoltaic systems[J]. Energies, 2020, 13(01): 225. DOI:10.3390/en13010225.',
 'Vlaminck M, Heidbuchel R, Philips W, Luong H. Region-based CNN for anomaly detection in PV power plants using aerial imagery[J]. Sensors, 2022, 22(03): 1244. DOI:10.3390/s22031244.',
 'Osmani K, Haddad A, Lemenand T, et al. A critical review of PV systems’ faults with the relevant detection methods[J]. Energy Nexus, 2023, 12: 100257. DOI:10.1016/j.nexus.2023.100257.'
]
for i,ref in enumerate(refs,1):
 if i==16:
  # Start the final reference block in a fresh body section so the repeated
  # header remains visible in both Word and LibreOffice renders.
  ref_sec = D.add_section(WD_SECTION.NEW_PAGE)
  configure_section(ref_sec, body=True)
  pg_num = ref_sec._sectPr.find(qn('w:pgNumType'))
  if pg_num is not None: pg_num.set(qn('w:start'), '29')
 p=D.add_paragraph(); set_para_format(p,alignment=WD_ALIGN_PARAGRAPH.LEFT,before=3,after=0,line=16,first=-21.0,left=0.74); r=p.add_run(f'[{i}] {ref}'); set_run_font(r,BODY_EA,ASCII,10.5)
add_para(D,'文献说明：本稿参考文献共 18 条，其中 10 条中文条目同时有 CNKI 合作期刊门户/参考文献页和 CQVIP 公开检索页元数据，8 条英文条目来自 Springer、Elsevier 或 MDPI 出版社/DOI 页面；核验链接、访问日期和条目边界见 evidence/thesis/references_audit.md 与 evidence/thesis/vip_audit.json。正式提交前可按学校账号导出 GB/T 7714 记录并检查正文引注顺序。')
add_heading(D,'致谢',1)
add_para(D,'感谢指导教师在课题方向、技术路线和实现过程中的指导。感谢学校提供的学习与实验条件。')
add_heading(D,'附录A 接口与运行证据',1)
add_para(D,'合成数据本地运行证据保存在项目 evidence/runtime/api/local_integration.json，PVDAQ 真实数据证据保存在 evidence/runtime/api/real_pvdaq_local_integration.json，测试记录保存在 evidence/tests/TEST_REPORT.md，界面截图保存在 evidence/screenshots/，原始数据和字段映射保存在 data/real/。上述文件与本说明书使用同一轮本地运行结果。')
# save
out=OUT/'m10_毕业设计说明书_河北工业职业技术大学_v1.0_本地实测稿.docx'
D.save(out)
print(out)
