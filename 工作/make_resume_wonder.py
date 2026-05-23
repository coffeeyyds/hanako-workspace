#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WonderCV-style single-column resume. Clean, professional, ATS-friendly.
Photo at top-right, sections with icons, consistent alignment throughout.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (BaseDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, Image, Frame, PageTemplate, HRFlowable)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# ── Fonts ──
FD = r'C:\Windows\Fonts'
pdfmetrics.registerFont(TTFont('ZH',  os.path.join(FD, 'msyh.ttc'),  subfontIndex=0))
pdfmetrics.registerFont(TTFont('ZHB', os.path.join(FD, 'msyhbd.ttc'), subfontIndex=0))

W, H = A4
ML, MR, MT, MB = 16*mm, 16*mm, 14*mm, 12*mm
CW = W - ML - MR

# ── Colors ──
NAVY  = HexColor('#1A3A5C')
GRAY  = HexColor('#444444')
LGRAY = HexColor('#999999')
LINE  = HexColor('#E0E0E0')
WHITE = HexColor('#FFFFFF')

# ── Styles ──
def ps(name, **kw):
    defaults = {'fontName': 'ZH', 'fontSize': 9, 'leading': 13, 'textColor': GRAY}
    defaults.update(kw)
    return ParagraphStyle(name, **defaults)

S = {
    'name':    ps('name', fontName='ZHB', fontSize=26, leading=30, textColor=NAVY),
    'contact': ps('contact', fontSize=8, leading=11, textColor=LGRAY),
    'hdrline': ps('hdrline', fontSize=7.5, leading=10, textColor=LGRAY, alignment=TA_CENTER),
    'sect':    ps('sect', fontName='ZHB', fontSize=12, leading=16, textColor=NAVY, spaceBefore=8, spaceAfter=2),
    'item_title': ps('it', fontName='ZHB', fontSize=10, leading=13, textColor=GRAY, spaceBefore=5, spaceAfter=0),
    'item_sub':   ps('is', fontSize=8, leading=10, textColor=LGRAY, spaceAfter=2),
    'bullet':   ps('bl', fontSize=8.5, leading=12, textColor=GRAY, leftIndent=8, spaceAfter=1),
    'body':     ps('b',  fontSize=8.5, leading=12, textColor=GRAY, spaceAfter=1.5),
    'skill_item': ps('ski', fontSize=8, leading=11.5, textColor=GRAY, spaceAfter=1),
    'eval':     ps('ev', fontSize=8, leading=12, textColor=GRAY, spaceAfter=2),
}

# ── Helpers ──
def section(title):
    return [
        HRFlowable(width="100%", thickness=0.5, color=LINE, spaceBefore=4, spaceAfter=1),
        Paragraph('<b>%s</b>' % title, S['sect']),
    ]

def exp_item(company, role, date, bullets, location=None):
    """Standard: company · role · date [location]"""
    items = []
    if location:
        header_text = '<b>%s</b>  ·  %s  ·  %s  ·  %s' % (company, role, date, location)
    else:
        header_text = '<b>%s</b>  ·  %s  ·  %s' % (company, role, date)
    items.append(Paragraph(header_text, S['item_title']))
    for b in bullets:
        items.append(Paragraph('•  %s' % b, S['bullet']))
    items.append(Spacer(1, 1.5*mm))
    return items

# ── Story ──
S_list = []

# ═══════ HEADER ═══════
photo = Image(r'D:\xry\个人资料\大头照\23.8.31\白底大头照23.8.31.jpg',
              width=22*mm, height=30*mm)

hdr_left = [
    Paragraph('肖 任 钺', S['name']),
    Paragraph('XIAO Renyue', ps('en', fontName='ZHB', fontSize=11, leading=14, textColor=LGRAY)),
    Spacer(1, 1*mm),
    Paragraph('应聘方向：金融 / 投行 / 研究分析  ·  可随时到岗', S['contact']),
    Paragraph('广州  |  15217336427  |  Xry_2003@126.com', S['contact']),
]
hdr_right = photo

hdr = Table([[hdr_left, hdr_right]],
            colWidths=[CW - 26*mm, 26*mm], hAlign='LEFT')
hdr.setStyle(TableStyle([
    ('VALIGN', (0,0), (0,0), 'TOP'),
    ('VALIGN', (1,0), (1,0), 'TOP'),
    ('TOPPADDING', (0,0), (-1,-1), 0),
    ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ('RIGHTPADDING', (1,0), (1,0), 0),
]))
S_list.append(hdr)
S_list.append(Spacer(1, 3*mm))

# Full-width navy line
S_list.append(HRFlowable(width="100%", thickness=2, color=NAVY, spaceAfter=3))

# ═══════ EDUCATION ═══════
S_list += section('教育背景')
S_list.append(Paragraph(
    '<b>广东金融学院</b>  ·  金融工程（本科）  ·  2023.09 – 2027.06',
    S['item_title']))
S_list.append(Paragraph(
    'GPA 3.5 / 4.0（前 15%）  ·  金融与投资学院',
    S['item_sub']))
S_list.append(Paragraph(
    '核心课程：金融学、证券投资分析、固定收益证券、投资学、商业银行经营学、金融计量学、金融市场学',
    S['body']))

# ═══════ EXPERIENCE ═══════
S_list += section('实习与实践经历')

S_list += exp_item('国泰海通证券 四川分公司', '实习生（暑期全业务轮岗）',
    '2025.07 – 2025.08',
    [
        '参与"川越星辰"暑期集训，系统完成数字金融运营、智能投顾、资产配置、企业客户服务、两融及衍生品、职业礼仪与公文写作等 12 门实战课程',
        '于企业客户部学习投行类服务（融资财务顾问、并购重组、保荐与承销、再融资）及投资类（私募股权投资孵化、产业基金投资）业务全流程',
        '协助营业部柜台日均处理 20+ 客户咨询；参加 8 次营业部例会，系统掌握客户分层、渠道管理及零售运营模式',
        '带领 4 人实习生小组从零搭建线上直播间，独立完成「理财节」6 期短视频的策划、拍摄与全流程后期制作',
        '于国泰君安期货四川分公司轮岗，深入分析生猪产业链供需格局，参与碳酸锂、焦煤等品种的期货实盘交易',
    ], location='成都')

S_list += exp_item('深圳前海国创投资咨询有限公司', '实习生',
    '2024.07 – 2024.08',
    [
        '参与项目策划与推进执行，独立设计 5 份市场调研问卷，输出 3 篇商业分析报告',
    ], location='深圳')

S_list += exp_item('中国银河证券', '会议助理（远程）',
    '2024.04 – 2025.04',
    [
        '协助组织并跟进 30+ 场投资策略专题会议，整理输出会议纪要及研究资料，覆盖宏观策略、行业分析与资产配置等方向',
    ], location='广州')

S_list += exp_item('江苏某农业企业政企合作项目', '策划助理',
    '2024.04 – 2024.05',
    [
        '参与企业数字化升级调研及 A 股 IPO 策划方案撰写，覆盖行业对标、财务规范与整改路径等模块',
    ], location='江苏')

S_list += exp_item('广东金融学院模拟证券交易所', '研发部部长',
    '2023.10 至今',
    [
        '主导模拟交易平台日常运营，管理 20+ 人研发团队，组织量化策略开发、因子回测与周度市场复盘分析',
    ], location='广州')

# ═══════ CAMPUS ═══════
S_list += section('校园与实践')
S_list.append(Paragraph(
    '•  广东金融学院燎原文学社 副社长  ·  组织校级"燎原杯"文学创作大赛，覆盖 500+ 参赛者',
    S['bullet']))
S_list.append(Paragraph(
    '•  高中期间曾任经济社社长、学生公司负责人；获区级素质教育实践活动一等奖、青马工程结业',
    S['bullet']))

# ═══════ SKILLS ═══════
S_list += section('技能与证书')
S_list.append(Paragraph(
    '<b>投资研究</b>  六年 A 股实盘交易经验，掌握技术分析、价值投资与事件驱动策略；独立研判，具备风控意识',
    S['skill_item']))
S_list.append(Paragraph(
    '<b>数字化工具</b>  精通 MS Office / WPS 全系，高阶 PPT 设计与数据可视化；熟练 Adobe Ps、Pr、秀米；具备直播运营与短视频全流程制作经验',
    S['skill_item']))
S_list.append(Paragraph(
    '<b>研究写作</b>  擅长金融文书与商业报告撰写；长期订阅《财新周刊》及头部财经播客，累计阅读深度报道与分析 500+ 篇',
    S['skill_item']))
S_list.append(Paragraph(
    '<b>语言与证书</b>  英语 CET-4 / CET-6，具备良好英文阅读与书面表达能力；基金从业资格备考中',
    S['skill_item']))

# ═══════ SELF-EVAL ═══════
S_list += section('自我评价')
S_list.append(Paragraph(
    '金融工程专业大三在读，GPA 前 15%。六年实盘交易经验，对资本市场有持续的兴趣与研究习惯。'
    '曾在头部券商完成系统化全业务轮岗实习，覆盖零售经纪、机构投行到期货衍生品全链条。'
    '性格开朗，团队融入度高，工作严谨细致且执行力突出；擅长内容创作与新媒体运营，具备数字化工作能力。',
    S['eval']))

# Bottom navy line
S_list.append(Spacer(1, 2*mm))
S_list.append(HRFlowable(width="100%", thickness=2, color=NAVY))

# ═══════ BUILD ═══════
doc = BaseDocTemplate(
    '肖任钺_简历.pdf',
    pagesize=A4,
    leftMargin=ML, rightMargin=MR, topMargin=MT, bottomMargin=MB,
    title='肖任钺 - 简历',
)
frame = Frame(ML, MB, CW, H - MT - MB, id='main')
doc.addPageTemplates([PageTemplate(id='Main', frames=frame)])
doc.build(S_list)
print('DONE')
