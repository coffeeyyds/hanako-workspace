#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Premium bilingual CV with photo, navy theme, two-column layout"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.platypus import (BaseDocTemplate, SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, Image, Frame, PageTemplate, NextPageTemplate,
                                 PageBreak)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os, copy

# ── Register fonts (must happen before any styles) ──
FD = r'C:\Windows\Fonts'
for tag, fname, idx in [
    ('ZH', 'msyh.ttc', 0),       # Microsoft YaHei
    ('ZHB', 'msyhbd.ttc', 0),    # Microsoft YaHei Bold
    ('EN', 'calibri.ttf', None),
    ('ENB', 'calibrib.ttf', None),
]:
    path = os.path.join(FD, fname)
    kw = {} if idx is None else {'subfontIndex': idx}
    try:
        pdfmetrics.registerFont(TTFont(tag, path, **kw))
    except Exception as e:
        print(f'Font {tag} error: {e}')

W, H = A4
LM, RM, TM, BM = 12*mm, 12*mm, 12*mm, 10*mm
CW = W - LM - RM

# ── Colors ──
NAVY  = HexColor('#0B2D52')
BLUE  = HexColor('#1A6FB5')
DGRAY = HexColor('#2D2D2D')
MGRAY = HexColor('#6B6B6B')
LGRAY = HexColor('#D5D5D5')
BGL   = HexColor('#F4F7FA')

# ── Paragraph Styles ──
st_name = ParagraphStyle('name', fontName='ZHB', fontSize=26, leading=32,
                          textColor=NAVY, alignment=TA_LEFT)
st_name_en = ParagraphStyle('nameEn', fontName='ENB', fontSize=11, leading=14,
                             textColor=MGRAY, alignment=TA_LEFT, spaceAfter=4)
st_contact = ParagraphStyle('contact', fontName='ZH', fontSize=7.5, leading=11,
                             textColor=MGRAY, alignment=TA_LEFT)
st_sect = ParagraphStyle('sect', fontName='ZHB', fontSize=12, leading=16,
                          textColor=NAVY, spaceBefore=8, spaceAfter=2)
st_sect_en = ParagraphStyle('sectEn', fontName='ENB', fontSize=8, leading=10,
                              textColor=BLUE, spaceAfter=5)
st_item = ParagraphStyle('item', fontName='ZHB', fontSize=9, leading=12,
                          textColor=DGRAY, spaceBefore=5, spaceAfter=1)
st_item_en = ParagraphStyle('itemEn', fontName='EN', fontSize=7.5, leading=10,
                             textColor=MGRAY, spaceAfter=1)
st_body = ParagraphStyle('body', fontName='ZH', fontSize=7.8, leading=12,
                          textColor=DGRAY, spaceAfter=2)
st_body_en = ParagraphStyle('bodyEn', fontName='EN', fontSize=7.2, leading=10,
                             textColor=MGRAY, spaceAfter=2)
st_bullet = ParagraphStyle('bullet', fontName='ZH', fontSize=7.5, leading=11.5,
                            textColor=DGRAY, leftIndent=6, spaceAfter=1)
st_bullet_en = ParagraphStyle('bulletEn', fontName='EN', fontSize=7, leading=10,
                               textColor=MGRAY, leftIndent=6, spaceAfter=1)
st_skill = ParagraphStyle('skill', fontName='ZH', fontSize=7.2, leading=10.5,
                           textColor=DGRAY, spaceAfter=3)
st_skill_en = ParagraphStyle('skillEn', fontName='EN', fontSize=6.8, leading=9.5,
                              textColor=MGRAY, spaceAfter=3)

# ── Helpers ──
def section(cn, en):
    return [
        Paragraph('&#9632;  <b>%s</b>' % cn, st_sect),
        Paragraph(en, st_sect_en),
    ]

def exp_item(date, org, org_en, title, title_en, bullets, bullets_en):
    res = []
    res.append(Paragraph(
        '<font color="#1A6FB5">%s</font>  |  <b>%s</b>  |  %s' % (date, org, title),
        st_item))
    res.append(Paragraph(
        '<font color="#1A6FB5">%s</font>  |  %s  |  %s' % (date, org_en, title_en),
        st_item_en))
    for i, (b, be) in enumerate(zip(bullets, bullets_en)):
        res.append(Paragraph('&#8226;  %s' % b, st_bullet))
        res.append(Paragraph('&#8226;  %s' % be, st_bullet_en))
    res.append(Spacer(1, 2.5*mm))
    return res

# ── Build content ──
L = []  # left column
R = []  # right column

# === HEADER (full width) ===
photo = Image(r'D:\xry\个人资料\大头照\23.8.31\白底大头照23.8.31.jpg',
              width=25*mm, height=33*mm)

header_data = [[
    photo,
    [
        Paragraph('肖 任 钺', st_name),
        Paragraph('XIAO Renyue', st_name_en),
        Paragraph('金融实习生  |  可随时到岗', st_contact),
        Paragraph('广州  |  15217336427  |  Xry_2003@126.com', st_contact),
    ]
]]
# We'll use header as part of left column

L.append(Spacer(1, 1*mm))
L.append(Table(header_data, colWidths=[29*mm, CW-29*mm], hAlign='LEFT',
               style=TableStyle([
                   ('VALIGN', (0,0), (0,0), 'TOP'),
                   ('VALIGN', (1,0), (1,0), 'MIDDLE'),
                   ('LEFTPADDING', (1,0), (1,0), 10),
                   ('TOPPADDING', (0,0), (-1,-1), 0),
                   ('BOTTOMPADDING', (0,0), (-1,-1), 0),
               ])))
L.append(Spacer(1, 3*mm))

# Top bar
bar = Table([['']], colWidths=[CW], rowHeights=[2.2*mm])
bar.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), NAVY)]))
L.append(bar)
L.append(Spacer(1, 3*mm))

# === LEFT COLUMN: Experience + Education ===

# EXPERIENCE
L += section('专业实践', 'PROFESSIONAL EXPERIENCE')

L += exp_item(
    '2025.07 - 2025.08',
    '国泰海通证券 四川分公司',
    'Guotai Haitong Securities, Sichuan Branch',
    '实习生', 'Intern',
    [
        '参与"川越星辰"暑期培训，系统学习数字金融运营、投顾、资配、企客、两融及职业礼仪',
        '于企业客户部学习投行类服务（融资财务顾问、并购重组、保荐承销、再融资等）及投资类全流程',
        '协助营业部柜台接待客户处理日常业务，参加例会掌握券商零售运营模式',
        '带领实习团队搭建优化线上直播间，独立策划拍摄剪辑"理财节"短视频',
        '赴国泰君安期货四川分公司研学，分析生猪产业链，参与碳酸锂、焦煤期货交易',
    ],
    [
        'Completed "Chuan Yue Xing Chen" summer program: digital finance, advisory, asset allocation, corporate services, margin trading',
        'Studied IB services (M&A advisory, underwriting, refinancing) & investment products at Corporate Client Department',
        'Assisted柜台 operations & client reception; attended branch meetings for retail ops know-how',
        'Led intern team to launch & optimize branch livestream studio; produced "Wealth Festival" video series',
        'Researched hog supply chain & traded lithium carbonate, coking coal futures at Guotai Junan Futures Sichuan',
    ])

L += exp_item(
    '2024.07 - 2024.08',
    '深圳前海国创投资咨询',
    'Qianhai Guochuang Investment Consulting',
    '实习生', 'Intern',
    ['参与项目策划执行，独立完成市场调研数据采集及商业分析报告'],
    ['Assisted in project planning; conducted market research & business analysis'])

L += exp_item(
    '2024.04 - 2025.04',
    '中国银河证券',
    'China Galaxy Securities',
    '会议助理', 'Conference Assistant',
    ['协助组织多场投资策略专题会议，整理汇总会议纪要及研究资料'],
    ['Coordinated investment strategy meetings; compiled minutes & research materials'])

L += exp_item(
    '2024.04 - 2024.05',
    '江苏某农业企业 政企合作项目',
    'Jiangsu Agricultural PPP Project',
    '策划助理', 'Planning Assistant',
    ['参与企业数字化转型升级及融资上市策划方案的调研与撰写'],
    ['Contributed to research & drafting of digital transformation and IPO planning proposals'])

L += exp_item(
    '2023.10 至今',
    '广东金融学院 模拟证券交易所',
    'GDUF Mock Stock Exchange',
    '研发部部长', 'Head of R&D',
    ['主导模拟交易平台运营，组织团队策略研究及定期复盘'],
    ['Led mock trading platform ops; organized strategy research & periodic reviews'])

L.append(Spacer(1, 2*mm))

# EDUCATION
L += section('教育背景', 'EDUCATION')
L.append(Paragraph(
    '<b>2023.09 至今</b>  |  广东金融学院  |  金融工程（本科）',
    st_item))
L.append(Paragraph(
    'Guangdong University of Finance  |  Financial Engineering, B.S.',
    st_item_en))
L.append(Paragraph(
    '主修：金融学、投资学、证券投资分析、固定收益证券、商业银行经营学', st_body))
L.append(Paragraph(
    'Core: Finance, Investment, Securities Analysis, Fixed Income, Commercial Banking', st_body_en))

# === RIGHT COLUMN: Photo + Skills + Self-Evaluation ===

# Photo
R.append(Spacer(1, 2*mm))

# SKILLS
R += section('专业技能', 'SKILLS')
R.append(Paragraph('<b>金融技能</b>', st_skill))
R.append(Paragraph(
    '六年证券交易经验，成熟的交易框架与资本市场认知；长期跟踪经济金融媒体，订阅《财新周刊》；擅长文书写作与会议内容转化',
    st_skill))
R.append(Paragraph('<b>6yr trading</b> · Market analysis · Financial writing · Caixin subscriber', st_skill_en))
R.append(Spacer(1, 2*mm))

R.append(Paragraph('<b>计算机技能</b>', st_skill))
R.append(Paragraph(
    '精通 Office 全套及 PPT 美化设计；熟练 Photoshop、Premiere、秀米等设计剪辑工具；具有数字金融线上运营实战经验',
    st_skill))
R.append(Paragraph('<b>MS Office</b> · PPT design · PS · Premiere · Xiùmǐ · Digital content ops', st_skill_en))
R.append(Spacer(1, 2*mm))

R.append(Paragraph('<b>语言能力</b>', st_skill))
R.append(Paragraph('英语 CET-4 / CET-6，具备良好英文阅读与书面表达能力', st_skill))
R.append(Paragraph('<b>English CET-4/6</b> · Chinese (native)', st_skill_en))
R.append(Spacer(1, 3*mm))

# SELF-EVALUATION
R += section('自我评价', 'SELF-EVALUATION')
R.append(Paragraph(
    '金融专业知识扎实，对经济、商业、科技前沿充满热情且涉猎广泛。性格开朗，团队协作能力强，执行力突出。',
    ParagraphStyle('eval', fontName='ZH', fontSize=7.2, leading=10.5,
                    textColor=DGRAY, spaceAfter=3, alignment=TA_JUSTIFY)))
R.append(Paragraph(
    '在国泰海通证券的系统化实习中，完整经历了零售、机构到衍生品交易的全业务链条，已建立对券商商业模式的立体认知。',
    ParagraphStyle('eval', fontName='ZH', fontSize=7.2, leading=10.5,
                    textColor=DGRAY, spaceAfter=4, alignment=TA_JUSTIFY)))
R.append(Paragraph(
    'A proactive finance student with 6yr real-market trading experience. Systematic internship at Guotai Haitong covering retail, institutional & derivatives business lines. Eager to bring analytical rigor and creative energy to the next opportunity.',
    ParagraphStyle('evalEn', fontName='EN', fontSize=6.8, leading=9.5,
                    textColor=MGRAY, spaceAfter=3, alignment=TA_JUSTIFY)))

# === ASSEMBLE TWO-COLUMN LAYOUT ===
LC = CW * 0.585
RC = CW * 0.415

main_table = Table([[L, R]], colWidths=[LC, RC], hAlign='LEFT')
main_table.setStyle(TableStyle([
    ('VALIGN', (0,0), (0,0), 'TOP'),
    ('VALIGN', (1,0), (1,0), 'TOP'),
    ('LEFTPADDING', (0,0), (0,0), 0),
    ('RIGHTPADDING', (0,0), (0,0), 0),
    ('LEFTPADDING', (1,0), (1,0), 5*mm),
    ('RIGHTPADDING', (1,0), (1,0), 0),
    ('TOPPADDING', (0,0), (-1,-1), 0),
    ('BOTTOMPADDING', (0,0), (-1,-1), 0),
]))

story = [main_table, Spacer(1, 4*mm)]

# Bottom bar
bottombar = Table([['']], colWidths=[CW], rowHeights=[1.5*mm])
bottombar.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), NAVY)]))
story.append(bottombar)

# === BUILD PDF ===
from reportlab.platypus.doctemplate import PageTemplate

frame = Frame(LM, BM, CW, H - TM - BM, id='main')

doc = BaseDocTemplate(
    '肖任钺_精美中英双语简历.pdf',
    pagesize=A4,
    leftMargin=LM, rightMargin=RM,
    topMargin=TM, bottomMargin=BM,
    title='XIAO Renyue - CV',
    author='XIAO Renyue',
)

doc.addPageTemplates([PageTemplate(id='Main', frames=frame)])
doc.build(story)
print('DONE: 肖任钺_精美中英双语简历.pdf')
