"""Local count report for the thesis acceptance target."""
from pathlib import Path
import json
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[2]
DOCX = ROOT / 'artifacts/thesis/m10_毕业设计说明书_河北工业职业技术大学_v1.0_本地实测稿.docx'

def blocks(doc):
    for el in doc.element.body.iterchildren():
        if el.tag == qn('w:p'):
            yield Paragraph(el, doc).text
        elif el.tag == qn('w:tbl'):
            table = Table(el, doc)
            yield '\n'.join(c.text for row in table.rows for c in row.cells)

def stats(text):
    return {'chars': len(text), 'nonspace': sum(not c.isspace() for c in text), 'cjk': sum('\u4e00' <= c <= '\u9fff' for c in text)}

def last_pos(text, marker, start=0):
    pos = text.rfind(marker)
    return pos if pos >= start else -1

doc = Document(str(DOCX))
text = '\n'.join(blocks(doc))
abstract_start = text.find('摘  要')
body_start = last_pos(text, '第1章 绪论', 2500)
refs_start = last_pos(text, '参考文献', 20000)
ack_start = last_pos(text, '致谢', refs_start)
appendix_start = last_pos(text, '附录A 接口与运行证据', ack_start)
if min(abstract_start, body_start, refs_start, ack_start, appendix_start) < 0:
    raise SystemExit('required section marker not found')
parts = {
    'abstract': text[abstract_start:body_start],
    'body': text[body_start:refs_start],
    'references': text[refs_start:ack_start],
    'acknowledgements': text[ack_start:appendix_start],
    'appendix': text[appendix_start:],
}
counted = text[abstract_start:]
report = {
    'document': str(DOCX),
    'acceptance_target': '用户本轮要求：计数内容至少 20000 字；历史手册口径同时要求正文不少于约 15000 字。',
    'counting_scope': '摘要、正文（含图题和表内文字）、参考文献、致谢、附录；排除封面、原创性声明、版权授权书、目录、页眉和页脚。',
    'local_auxiliary_note': '这是 python-docx 的非空字符辅助统计，不替代 Word/LibreOffice 的字数对话框；正文范围包含题注和表内文字。',
    'sections': {name: stats(value) for name, value in parts.items()},
    'counted_total': stats(counted),
    'pass_total_20000': stats(counted)['nonspace'] >= 20000,
    'pass_body_15000': stats(parts['body'])['nonspace'] >= 15000,
}
out = ROOT / 'evidence/thesis/wordcount_audit.json'
out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
md = ROOT / 'evidence/thesis/WORDCOUNT_REPORT.md'
lines = [
    '# 说明书字数核对', '',
    '- 本轮项目验收目标：按用户明确要求，计数内容至少 20,000 字；历史手册口径同时要求正文不少于约 15,000 字。',
    '- 统计范围：摘要、正文（含图题和表内文字）、参考文献、致谢、附录；排除封面、声明、授权书、目录、页眉和页脚。',
    '- 统计说明：以下为 python-docx 的非空字符辅助统计，最终提交前仍可在 Word/LibreOffice 字数对话框中复核。', '',
    '| 部分 | 非空字符 | 中文字符 |', '|---|---:|---:|',
]
for name, value in report['sections'].items():
    label = {'abstract':'摘要','body':'正文（含题注和表内文字）','references':'参考文献','acknowledgements':'致谢','appendix':'附录'}[name]
    lines.append(f"| {label} | {value['nonspace']} | {value['cjk']} |")
lines += [f"| **计数合计** | **{report['counted_total']['nonspace']}** | **{report['counted_total']['cjk']}** |", '', f"- 20,000 字目标：{'通过' if report['pass_total_20000'] else '未通过'}。", f"- 正文约 15,000 字目标：{'通过' if report['pass_body_15000'] else '未通过'}。"]
md.write_text('\n'.join(lines) + '\n', encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
