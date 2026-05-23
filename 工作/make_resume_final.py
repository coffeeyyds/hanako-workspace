#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Premium Bilingual CV — single-page, elegant alignment, photo included.
Layout: Full-width header → 2-column body (L:57% experiences+edu, R:43% skills+profile)
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.platypus import (BaseDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, Image, Frame, PageTemplate, HRFlowable, KeepTogether)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# ── Fonts ──
FD = r'C:\Windows\Fonts'
pdfmetrics.registerFont(TTFont('ZH',  os.path.join(FD, 'msyh.ttc'),  subfontIndex=0))
pdfmetrics.registerFont(TTFont('ZHB', os.path.join(FD, 'msyhbd.ttc'), subfontIndex=0))
pdfmetrics.registerFont(TTFont('EN',  os.path.join(FD, 'calibri.ttf')))
pdfmetrics.registerFont(TTFont('ENB', os.path.join(FD, 'calibrib.ttf')))

W_page, H_page = A4
ML, MR, MT, MB = 13*mm, 13*mm, 12*mm, 10*mm
CW = W_page - ML - MR  # 184mm content width

# ── Palette ──
NAVY   = HexColor('#0A2647')
BLUE   = HexColor('#144272')
ACCENT = HexColor('#205295')
LBLUE  = HexColor('#2C74B3')
DGRAY  = HexColor('#2B2B2B')
MGRAY  = HexColor('#6E6E6E')
LGRAY  = HexColor('#B0B0B0')
BGL    = HexColor('#F8F9FC')

# ── Paragraph Styles ──
S = {
    'name':    ParagraphStyle('pn', fontName='ZHB', fontSize=24, leading=28, textColor=NAVY,
                               alignment=TA_LEFT, spaceAfter=0),
    'name_en': ParagraphStyle('pne',fontName='ENB', fontSize=10, leading=13, textColor=MGRAY,
                               alignment=TA_LEFT, spaceAfter=1),
    'contact': ParagraphStyle('pc', fontName='ZH', fontSize=7, leading=10, textColor=MGRAY,
                               alignment=TA_LEFT),
    'sect':    ParagraphStyle('ps', fontName='ZHB', fontSize=10.5, leading=14, textColor=NAVY,
                               spaceBefore=5, spaceAfter=1),
    'sect_en': ParagraphStyle('pse',fontName='ENB', fontSize=7, leading=9.5, textColor=LBLUE,
                               spaceAfter=3),
    'item':    ParagraphStyle('pi', fontName='ZHB', fontSize=8.5, leading=11, textColor=DGRAY,
                               spaceBefore=2.5, spaceAfter=0),
    'item_en': ParagraphStyle('pie',fontName='EN',  fontSize=6.8, leading=9.5, textColor=MGRAY,
                               spaceAfter=0.5),
    'body':    ParagraphStyle('pb', fontName='ZH',  fontSize=7, leading=10, textColor=DGRAY,
                               spaceAfter=1),
    'body_en': ParagraphStyle('pbe',fontName='EN',  fontSize=6.5, leading=9, textColor=MGRAY,
                               spaceAfter=1),
    'bullet':  ParagraphStyle('pbl',fontName='ZH',  fontSize=7, leading=10, textColor=DGRAY,
                               leftIndent=5, spaceAfter=0.3),
    'bullet_en':ParagraphStyle('pble',fontName='EN', fontSize=6.4, leading=8.8, textColor=MGRAY,
                               leftIndent=5, spaceAfter=0.3),
    'skill':   ParagraphStyle('psk',fontName='ZH',  fontSize=6.7, leading=9.5, textColor=DGRAY,
                               spaceAfter=1),
    'skill_en':ParagraphStyle('pske',fontName='EN', fontSize=6.2, leading=8.5, textColor=MGRAY,
                               spaceAfter=1),
    'eval':    ParagraphStyle('pev',fontName='ZH',  fontSize=6.7, leading=9.5, textColor=DGRAY,
                               spaceAfter=1.5, alignment=TA_JUSTIFY),
    'eval_en': ParagraphStyle('peve',fontName='EN', fontSize=6.2, leading=8.5, textColor=MGRAY,
                               spaceAfter=1.5, alignment=TA_JUSTIFY),
    'tag':     ParagraphStyle('ptag',fontName='ENB', fontSize=6.5, leading=8, textColor=white,
                               alignment=TA_CENTER),
}

# ── Helpers ──
def sect(cn, en):
    return [Paragraph('&#9654;  <b>%s</b>' % cn, S['sect']),
            Paragraph(en, S['sect_en'])]

def exp(date, org, org_en, title, title_en, bullets, bullets_en):
    r = [Paragraph('<font color="#2C74B3">%s</font>  |  <b>%s</b>  |  <i>%s</i>' % (date, org, title), S['item']),
         Paragraph('<font color="#2C74B3">%s</font>  |  %s  |  <i>%s</i>' % (date, org_en, title_en), S['item_en'])]
    for b, be in zip(bullets, bullets_en):
        r.append(Paragraph('&#8226; %s' % b, S['bullet']))
        r.append(Paragraph('  %s' % be, S['bullet_en']))
    r.append(Spacer(1, 0.8*mm))
    return r

def tag_pill(text, width=20*mm):
    """Small navy pill-shaped label."""
    t = Table([[Paragraph(text, S['tag'])]], colWidths=[width], rowHeights=[4.5*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), ACCENT),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 0.5*mm),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0.5*mm),
        ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('RIGHTPADDING', (0,0), (-1,-1), 3),
    ]))
    return t

# ── Build Story ──
L = []  # LEFT
R = []  # RIGHT

# ═══════════ HEADER (full width) ═══════════
photo = Image(r'D:\xry\个人资料\大头照\23.8.31\白底大头照23.8.31.jpg',
              width=23*mm, height=31*mm)

hdr_content = [
    Paragraph('肖 任 钺', S['name']),
    Paragraph('XIAO Renyue', S['name_en']),
    Spacer(1, 0.8*mm),
    Paragraph('求职意向：金融 / 投行 / 研究分析实习生', S['contact']),
    Paragraph('广州  |  15217336427  |  Xry_2003@126.com', S['contact']),
]

hdr = Table([[photo, '', hdr_content]],
            colWidths=[27*mm, 3*mm, CW-30*mm], hAlign='LEFT')
hdr.setStyle(TableStyle([
    ('VALIGN', (0,0), (0,0), 'TOP'),
    ('VALIGN', (2,0), (2,0), 'MIDDLE'),
    ('LEFTPADDING', (2,0), (2,0), 8),
    ('TOPPADDING', (0,0), (-1,-1), 0),
    ('BOTTOMPADDING', (0,0), (-1,-1), 0),
]))

# Navy top bar
bar = Table([['']], colWidths=[CW], rowHeights=[2.2*mm])
bar.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), NAVY)]))

L.append(hdr)
L.append(Spacer(1, 3.5*mm))
L.append(bar)
L.append(Spacer(1, 3.5*mm))

# ═══════ LEFT: EXPERIENCE ═══════
L += sect('专业实践', 'PROFESSIONAL EXPERIENCE')

L += exp('2025.07–2025.08  ·  成都',
    '国泰海通证券四川分公司',
    'Guotai Haitong Securities, Sichuan Branch',
    '实习生（全业务轮岗）', 'Intern (Full Business Rotation)',
    [
        '参与"川越星辰"暑期集训，系统学习数字金融线上运营、智能投顾、资产配置、企业客户服务、两融及衍生品业务、职业礼仪与公文写作等 12 门实战课程',
        '于企业客户部深入学习投行类服务（融资财务顾问、并购重组、保荐与承销、再融资等）、投资类服务（私募股权投资孵化、产业基金投资）与资产配置全流程',
        '协助营业部柜台接待日均 20+ 客户并处理日常业务；参加 8 次营业部例会，全面掌握客户分层、渠道管理运营模式',
        '带领 4 人实习生小组从零搭建线上直播间，完成 6 期"理财节"短视频的策划、拍摄与全流程后期剪辑',
        '于国泰君安期货四川分公司轮岗，深入研究生猪产业链供需模型，参与碳酸锂、焦煤等 3 个品种期货实盘交易',
    ],
    [
        'Completed "Chuan Yue Xing Chen" summer program: 12 courses covering digital finance, robo-advisory, asset allocation, corporate services, margin trading & derivatives',
        'At Corporate Client Dept: studied IB services (M&A, underwriting, refinancing), investment products (PE incubation, industrial funds), and asset allocation frameworks',
        'Assisted柜台 with 20+ daily walk-in clients; attended 8 branch meetings on client segmentation & channel management',
        'Led 4-person intern team to build livestream studio from scratch; produced 6 episodes of "Wealth Festival" video series',
        'Completed期货 rotation: built hog supply-chain model; traded lithium carbonate & coking coal futures positions live',
    ])

L += exp('2024.07–2024.08  ·  深圳',
    '深圳前海国创投资咨询有限公司',
    'Qianhai Guochuang Investment Consulting',
    '实习生', 'Intern',
    [
        '协同项目策划与推进执行，独立完成 5 份市场调研问卷设计与数据采集，输出 3 篇商业分析报告',
    ],
    [
        'Assisted project planning & execution; designed 5 market surveys, authored 3 business analysis reports',
    ])

L += exp('2024.04–2025.04  ·  广州',
    '中国银河证券',
    'China Galaxy Securities',
    '会议助理（远程）', 'Conference Assistant (Remote)',
    [
        '协助组织 30+ 场投资策略专题会议，整理输出会议纪要及研究资料，内容涵盖宏观策略、行业分析、资产配置等方向',
    ],
    [
        'Supported 30+ investment strategy meetings; produced minutes & research briefs covering macro, sector, and allocation topics',
    ])

L += exp('2024.04–2024.05  ·  江苏',
    '江苏某农业企业政企合作项目',
    'Jiangsu Agricultural Enterprise · PPP Initiative',
    '策划助理', 'Planning Assistant',
    [
        '参与企业数字化升级调研及 A 股上市策划方案撰写，覆盖行业对标、财务规范与整改路径等模块',
    ],
    [
        'Contributed to digital transformation audit & A-share IPO planning: industry benchmarking, financial compliance, remediation roadmap',
    ])

L += exp('2023.10 至今  ·  广州',
    '广东金融学院模拟证券交易所',
    'GDUF Mock Stock Exchange',
    '研发部部长', 'Head of Research & Development',
    [
        '主导模拟交易平台运营管理，组织 20+ 人研发团队开展量化策略研究、因子回测及周度市场复盘分析',
    ],
    [
        'Led 20-person R&D team: quantitative strategy development, factor backtesting, weekly market review & commentary',
    ])

# ═══════ LEFT: EDUCATION ═══════
L.append(Spacer(1, 2*mm))
L += sect('教育背景', 'EDUCATION')
L.append(Paragraph(
    '<b>2023.09 至今</b>  |  广东金融学院  |  金融工程 本科  |  GPA 3.5 / 4.0（前 15%）', S['item']))
L.append(Paragraph(
    'Guangdong University of Finance  |  B.S. Financial Engineering  |  GPA 3.5/4.0 (Top 15%)', S['item_en']))
L.append(Paragraph(
    '主修：金融学、投资学、证券投资分析、固定收益证券、商业银行经营学、金融计量学、金融市场学',
    S['body']))
L.append(Paragraph(
    'Core: Finance, Investment, Securities Analysis, Fixed Income, Commercial Banking, Financial Econometrics, Financial Markets',
    S['body_en']))

# ═══════ RIGHT COLUMN ═══════
R.append(Spacer(1, 1*mm))

# --- PROFILE ---
R += sect('个人简介', 'PROFILE')
R.append(Paragraph(
    '金融工程专业大三在读，GPA 前 15%。六年实盘交易经验，对资本市场有持续的兴趣与研究习惯。'
    '曾在头部券商完成系统化轮岗实习，覆盖零售、机构投行到期货衍生品全链条。'
    '长于内容创作与团队协作，具备数字化运营与新媒体传播能力。',
    S['eval']))
R.append(Paragraph(
    'Junior Financial Engineering student (Top 15%). 6yr live-market trading. '
    'Systematic internship rotation at a leading securities firm, covering '
    'retail, institutional, and derivatives business lines. Skilled in content creation, digital ops, and teamwork.',
    S['eval_en']))
R.append(Spacer(1, 2*mm))

# --- SKILLS ---
R += sect('核心能力', 'CORE COMPETENCIES')

def skill_item(label, label_en, content, content_en):
    return [
        Paragraph('<b>%s</b>  <font color="#6E6E6E">%s</font>' % (label, label_en), S['skill']),
        Paragraph(content, S['skill']),
        Paragraph(content_en, S['skill_en']),
        Spacer(1, 1*mm),
    ]

R += skill_item('投资研究', 'Investment Research',
    '6 年 A 股实盘交易经验，掌握技术分析、价值投资与事件驱动策略，具备独立研判与风控意识',
    '6yr A-share trading · Technical & fundamental analysis · Event-driven strategies · Risk management')
R += skill_item('数字化工具', 'Digital & Creative',
    '精通 MS Office / WPS 全系；高阶 PPT 设计与数据可视化；熟练 Adobe Ps / Pr / 秀米；具备直播运营与短视频全流程制作经验',
    'MS Office · Advanced PPT & data viz · Photoshop · Premiere · Livestream ops · Video production')

R += skill_item('研究与写作', 'Research & Writing',
    '擅长金融文书与商业报告撰写；长期订阅《财新周刊》及头部财经播客，累计阅读 500+ 篇深度报道与分析',
    'Financial writing & business reporting · 500+ long-form articles read · Caixin & top finance podcast subscriber')

R += skill_item('语言', 'Languages',
    '中文母语 · 英语 CET-4 / CET-6，具备流利英文阅读及书面表达能力',
    'Chinese (native) · English CET-4/6 · Proficient reading & written expression')

R.append(Spacer(1, 2*mm))

# ═══════ ASSEMBLE ═══════
LC = CW * 0.56
RC = CW * 0.44
GAP = 5*mm

body = Table([[L, R]], colWidths=[LC, RC], hAlign='LEFT')
body.setStyle(TableStyle([
    ('VALIGN', (0,0), (0,0), 'TOP'),
    ('VALIGN', (1,0), (1,0), 'TOP'),
    ('LEFTPADDING', (0,0), (0,0), 0),
    ('RIGHTPADDING', (0,0), (0,0), GAP/2),
    ('LEFTPADDING', (1,0), (1,0), GAP/2),
    ('RIGHTPADDING', (1,0), (1,0), 0),
    ('TOPPADDING', (0,0), (-1,-1), 0),
    ('BOTTOMPADDING', (0,0), (-1,-1), 0),
]))

story = [body, Spacer(1, 3*mm)]
story.append(Table([['']], colWidths=[CW], rowHeights=[1.5*mm],
                   style=TableStyle([('BACKGROUND', (0,0), (-1,-1), NAVY)])))

# ═══════ PDF ═══════
doc = BaseDocTemplate(
    '肖任钺_中英双语简历.pdf',
    pagesize=A4,
    leftMargin=ML, rightMargin=MR, topMargin=MT, bottomMargin=MB,
    title='XIAO Renyue - Curriculum Vitae',
    author='XIAO Renyue',
)
frame = Frame(ML, MB, CW, H_page - MT - MB, id='main')
doc.addPageTemplates([PageTemplate(id='Main', frames=frame)])
doc.build(story)
print('DONE: 肖任钺_中英双语简历.pdf')
