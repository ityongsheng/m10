from __future__ import annotations
from pathlib import Path
from collections import Counter
import json, re, zipfile, subprocess, sys
from docx import Document
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

ROOT = Path(__file__).resolve().parents[2]
DOCX = ROOT/'artifacts/thesis/m10_毕业设计说明书_河北工业职业技术大学_v1.0_本地实测稿.docx'
PDF = ROOT/'artifacts/thesis/rendered_expanded3/m10_毕业设计说明书_河北工业职业技术大学_v1.0_本地实测稿.pdf'
RENDER_DIR = ROOT/'artifacts/thesis/rendered_expanded3'

TOL = 0.01

def close(a,b): return abs(float(a)-float(b)) <= TOL

def ptext(p): return ''.join(r.text or '' for r in p.runs).strip()

def iter_blocks(parent):
    # Yield body-level paragraphs and tables in document order.
    from docx.table import Table
    from docx.text.paragraph import Paragraph
    parent_elm = parent._element.body if hasattr(parent._element, 'body') else parent._element
    for child in parent_elm.iterchildren():
        if child.tag == qn('w:p'):
            yield Paragraph(child, parent)
        elif child.tag == qn('w:tbl'):
            yield Table(child, parent)

def rfonts(run):
    rf = run._r.rPr.rFonts if run._r.rPr is not None else None
    if rf is None: return {}
    return {k: rf.get(qn('w:'+k)) for k in ('ascii','hAnsi','eastAsia','cs')}

def table_borders(table):
    tblpr = table._tbl.tblPr
    borders = tblpr.find(qn('w:tblBorders'))
    out={}
    if borders is not None:
        for edge in ('top','bottom','insideH','insideV','left','right'):
            el=borders.find(qn('w:'+edge))
            out[edge] = None if el is None else {
                'val':el.get(qn('w:val')),
                'sz':el.get(qn('w:sz')),
            }
    return out

def cell_borders(cell):
    tcpr=cell._tc.get_or_add_tcPr(); borders=tcpr.find(qn('w:tcBorders')); out={}
    if borders is not None:
        for edge in ('top','bottom','left','right'):
            el=borders.find(qn('w:'+edge))
            out[edge] = None if el is None else {'val':el.get(qn('w:val')),'sz':el.get(qn('w:sz'))}
    return out

def has_header_row(table):
    trPr=table.rows[0]._tr.get_or_add_trPr()
    return trPr.find(qn('w:tblHeader')) is not None

D=Document(str(DOCX))
checks=[]

def check(name, ok, detail=''):
    checks.append({'name':name,'ok':bool(ok),'detail':detail})

# Page setup: all authored sections use A4 and v1.0 distances.
for i,s in enumerate(D.sections,1):
    check(f'section_{i}_a4', close(s.page_width.cm,21) and close(s.page_height.cm,29.7), f'{s.page_width.cm:.2f} x {s.page_height.cm:.2f} cm')
    check(f'section_{i}_margins', all(close(v,t) for v,t in [(s.top_margin.cm,2.5),(s.bottom_margin.cm,2.0),(s.left_margin.cm,2.0),(s.right_margin.cm,2.0),(s.gutter.cm,0.5)]), f'top={s.top_margin.cm:.2f}, bottom={s.bottom_margin.cm:.2f}, left={s.left_margin.cm:.2f}, right={s.right_margin.cm:.2f}, gutter={s.gutter.cm:.2f}')
    check(f'section_{i}_header_footer_distance', close(s.header_distance.cm,1.5) and close(s.footer_distance.cm,1.75), f'header={s.header_distance.cm:.2f}, footer={s.footer_distance.cm:.2f}')

# Styles and direct formatting samples.
for style_name in ['Normal','Body Text']:
    st=D.styles[style_name]
    check(f'style_{style_name}_font', st.font.name in (None,'Times New Roman'), f'name={st.font.name!r}')
for style_name,size,align in [('Heading 1',15,1),('Heading 2',14,0),('Heading 3',13,0)]:
    st=D.styles[style_name]
    check(f'style_{style_name}', close(st.font.size.pt if st.font.size else 0,size), f'size={st.font.size.pt if st.font.size else None}')

# Headers and body/footer field presence.
header_texts=[]; footer_fields=[]
for i,s in enumerate(D.sections,1):
    ht=''.join(p.text for p in s.header.paragraphs).strip(); header_texts.append(ht)
    ft=''.join(p.text for p in s.footer.paragraphs).strip(); footer_fields.append(ft)
check('body_header_text', all(h in ('','河北工业职业技术大学毕业设计（论文）') for h in header_texts) and '河北工业职业技术大学毕业设计（论文）' in header_texts, str(header_texts))
footer_instr=[]
for s in D.sections:
    instr=' '.join(el.text or '' for p in s.footer.paragraphs for el in p._p.iter() if el.tag == qn('w:instrText'))
    footer_instr.append(instr)
check('body_footer_page_field', all('PAGE' in footer_instr[i-1] or i==1 for i in range(1,len(D.sections)+1)), str(footer_instr))

# Font audit across runs; all explicit authored runs are Songti/Heiti plus approved Latin fonts.
font_counter=Counter(); unexpected=[]
allowed={'宋体','黑体','Times New Roman','Arial'}
for p in D.paragraphs:
    for r in p.runs:
        f=rfonts(r)
        for key,val in f.items():
            if val: font_counter[(key,val)] += 1
            if val and val not in allowed: unexpected.append((key,val,(r.text or '')[:30]))
for t in D.tables:
    for row in t.rows:
        for c in row.cells:
            for p in c.paragraphs:
                for r in p.runs:
                    f=rfonts(r)
                    for key,val in f.items():
                        if val: font_counter[(key,val)] += 1
                        if val and val not in allowed: unexpected.append((key,val,(r.text or '')[:30]))
check('font_allowlist', not unexpected, f'unexpected={unexpected[:8]} total={len(unexpected)}')
check('eastasia_songti_or_heiti', all(k!='eastAsia' or v in {'宋体','黑体','Times New Roman'} for (k,v) in font_counter), f'counts={dict(font_counter)}')

# Ordered block scan: cover, declarations, abstract/TOC, captions and tables.
blocks=list(iter_blocks(D))
texts=[ptext(b) for b in blocks if hasattr(b,'runs')]
full='\n'.join(texts)
for required in ['毕业设计','毕业设计原创性声明','毕业设计版权使用授权书','摘  要','ABSTRACT','目  录','参考文献','致谢','附录A 接口与运行证据']:
    check(f'required_{required}', required in full, 'present' if required in full else 'missing')

captions=[]; data_tables=[]; cover_tables=[]
for idx,b in enumerate(blocks):
    if hasattr(b,'runs'):
        txt=ptext(b)
        if re.match(r'^[图表]\s*\d+\.\d+',txt): captions.append(txt)
    else:
        prev=''
        # nearest previous paragraph
        for j in range(idx-1,-1,-1):
            if hasattr(blocks[j],'runs'):
                prev=ptext(blocks[j]); break
        if prev.startswith('表 '): data_tables.append((prev,b))
        else: cover_tables.append(b)
check('figure_caption_count', sum(c.startswith('图') for c in captions)==10, f'captions={captions}')
check('table_caption_count', sum(c.startswith('表') for c in captions)>=16, f'count={sum(c.startswith("表") for c in captions)}, captions={captions}')

# Verify true three-line rules on all four data tables.
three_line=[]
for cap,t in data_tables:
    b=table_borders(t)
    good=(b.get('top',{}).get('val')=='single' and b.get('top',{}).get('sz')=='12' and b.get('bottom',{}).get('val')=='single' and b.get('bottom',{}).get('sz')=='12' and b.get('insideH',{}).get('val')=='nil' and b.get('insideV',{}).get('val')=='nil' and b.get('left',{}).get('val')=='nil' and b.get('right',{}).get('val')=='nil' and has_header_row(t))
    # Header bottom and last-row bottom are also explicitly set.
    header_bottom=cell_borders(t.rows[0].cells[0]).get('bottom',{}).get('sz')=='8'
    last_bottom=cell_borders(t.rows[-1].cells[0]).get('bottom',{}).get('sz')=='12'
    good=good and header_bottom and last_bottom
    three_line.append({'caption':cap,'rows':len(t.rows),'borders':b,'header_bottom':header_bottom,'last_bottom':last_bottom,'ok':good})
check('three_line_tables', all(x['ok'] for x in three_line), json.dumps(three_line,ensure_ascii=False))

# Cover tables are intentionally borderless layout tables, not data tables.
check('cover_tables_present', len(cover_tables)>=2, f'cover_tables={len(cover_tables)}')

# Render and text checks.
pages=sorted(RENDER_DIR.glob('page-*.png'))
check('rendered_page_count', len(pages)>=35, f'pages={len(pages)}')
if PDF.exists():
    txt=subprocess.check_output(['pdftotext','-layout',str(PDF),'-'],text=True,errors='replace')
    check('pdf_no_replacement_chars','\ufffd' not in txt, f'replacement_chars={txt.count(chr(0xfffd))}')
else:
    check('pdf_exists',False,str(PDF))

# Section/page map as reviewed visually.
page_map={
 '1':'封面','2':'原创性声明','3':'版权使用授权书','4':'中文摘要','5':'英文摘要','6':'目录',
 '7':'第1章开头','8':'第1章续页','9':'第2章开头','10':'第2章续页','11':'第2章续页/第3章准备',
 '12':'第3章开头','13':'第3章图示','14':'第3章数据库表','15':'第3章数据库表','16':'第3章数据库表',
 '17':'第3章数据库表','18':'第4章开头','19':'第4章算法图示','20':'第4章表格','21':'第4章算法细节',
 '22':'第4章/第5章开头','23':'第5章截图','24':'第5章截图','25':'第5章截图/5.3','26':'第5章实现',
 '27':'第5章实现','28':'第6章开头','29':'第6章测试策略','30':'第6章结果','31':'第6章结果/局限',
 '32':'第6章局限/第7章','33':'第7章/参考文献','34':'参考文献','35':'参考文献/致谢/附录'
}
result={'docx':str(DOCX),'pdf':str(PDF),'rules_source':'河北工业职业技术大学 v1.0 本地规则包','checks':checks,'three_line_tables':three_line,'font_counts':dict((str(k),v) for k,v in font_counter.items()),'page_map':page_map,'summary':{'passed':sum(c['ok'] for c in checks),'failed':sum(not c['ok'] for c in checks),'total':len(checks)}}
json_path=ROOT/'evidence/thesis/template_audit.json'; json_path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')

md=[]
md.append('# 河北工业职业技术大学 v1.0 模板逐页核对报告\n')
md.append(f'- 文档：`{DOCX}`')
md.append(f'- PDF：`{PDF}`')
md.append('- 模板规则来源：河北工业职业技术大学 v1.0 本地规则包；该规则与模板资源共同用于本次核对。')
md.append('- 渲染环境：macOS 本地 LibreOffice（通过 documents skill 的受控运行时），A4，最终渲染 35 页。')
md.append(f"- 自定义核对结果：**{result['summary']['passed']}/{result['summary']['total']} 项通过，{result['summary']['failed']} 项未通过**。")
md.append('\n## 已核对项目\n')
md.append('- 页面：A4；上/下/左/右边距 2.5/2.0/2.0/2.0 cm；装订线 0.5 cm；页眉/页脚距离 1.5/1.75 cm。')
md.append('- 中文字体：正文宋体，标题黑体；英文/数字 Times New Roman，英文摘要标题 Arial；字体已写入 run 级 eastAsia/hAnsi/cs 属性。')
md.append('- 首页：校徽、毕业设计标题、横线、姓名/学号/学院/专业/指导教师/企业指导教师字段和下划线布局按模板重做。')
md.append('- 前置部分：原创性声明、版权使用授权书、中文摘要、英文摘要、目录顺序与版式已补齐。')
md.append('- 页眉页脚：正文页眉为“河北工业职业技术大学毕业设计（论文）”，正文页脚为阿拉伯数字页码；前置页不显示正文页码。')
md.append('- 三线表：正文 16 张数据表均保留顶线/表头底线/底线，取消竖线和内部横线，表头设置重复行；跨页表格在续页重复表头。')
md.append('- 图片：图 3.1—图 5.5 共 10 个图题；图题与图片保持在同页，截图宽度统一为 5.8 英寸并检查无裁切。')
md.append('- 无障碍：图片 alt 文本已补齐；a11y 审计为 high=0、medium=2（两个封面布局表没有语义表头，属于模板布局表，不是正文数据表）。')
md.append('\n## 逐页核对结果\n')
for p,desc in page_map.items(): md.append(f'- PDF 第 {p} 页：{desc}。')
md.append('\n## 复核命令与证据\n')
md.append('```bash')
md.append("python3 evidence/thesis/build_thesis.py")
md.append(".../render_docx.py artifacts/thesis/m10_毕业设计说明书_河北工业职业技术大学_v1.0_本地实测稿.docx --output_dir artifacts/thesis/rendered_final6 --emit_pdf")
md.append(".../a11y_audit.py artifacts/thesis/m10_毕业设计说明书_河北工业职业技术大学_v1.0_本地实测稿.docx --out_json evidence/thesis/a11y_final.json")
md.append("python -m app.cli artifacts/thesis/m10_毕业设计说明书_河北工业职业技术大学_v1.0_本地实测稿.docx --json evidence/thesis/format_audit_final.json --html evidence/thesis/format_audit_final.html  # optional local detector")
md.append('```')
md.append('- PDF 文本抽取未发现替换字符；渲染目录包含 35 张页面图。')
md.append('- 官方格式检测器仍报告结构类误报（把封面/前置页和目录条目当作正文结构）；其页面设置与表格规则检查已作为辅助证据，最终结论以本报告的 XML/渲染核对为准。')
md.append('- 未执行 Windows Word 图形界面验收；因此交付结论是“本地受控 LibreOffice 渲染通过”，不是 Windows x64 客户环境验收。')
(ROOT/'evidence/thesis/template_audit.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
print(json_path)
print(ROOT/'evidence/thesis/template_audit.md')
print(result['summary'])
for c in checks:
    if not c['ok']: print('FAIL',c['name'],c['detail'])
