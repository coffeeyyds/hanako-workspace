#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate a beautifully formatted bilingual Chinese-English CV as PDF"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, Image, Frame, PageTemplate)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# ---------- Register fonts ----------
font_dir = r'C:\Windows\Fonts'
try:
    pdfmetrics.registerFont(TTFont('MSYH', os.path.join(font_dir, 'msyh.ttc'), subfontIndex=0))
    pdfmetrics.registerFont(TTFont('MSYHBD', os.path.join(font_dir, 'msyhbd.ttc'), subfontIndex=0))
except Exception:
    pdfmetrics.registerFont(TTFont('MSYH', os.path.join(font_dir, 'msyh.ttf')))
    pdfmetrics.registerFont(TTFont('MSYHBD', os.path.join(font_dir, 'msyhbd.ttf')))
pdfmetrics.registerFont(TTFont('CALIBRI', os.path.join(font_dir, 'calibri.ttf')))
pdfmetrics.registerFont(TTFont('CALIBRIB', os.path.join(font_dir, 'calibrib.ttf')))

pdfmetrics.registerFont(TTFont('SIMSUN', os.path.join(font_dir, 'simsun.ttc'), subfontIndex=0))

W, H = A4

# ---------- Colors ----------
DARK_BLUE  = HexColor('#1B3A5C')
ACCENT     = HexColor('#2E75B6')
GRAY       = HexColor('#444444')
MGRAY      = HexColor('#666666')

# ---------- Paragraph Styles ----------
s_name = ParagraphStyle('Name', fontName='MSYHBD', fontSize=24, leading=30,
                         textColor=DARK_BLUE, alignment=TA_CENTER, spaceAfter=2)
s_name_en = ParagraphStyle('NameEn', fontName='CALIBRIB', fontSize=13, leading=16,
                            textColor=MGRAY, alignment=TA_CENTER, spaceAfter=3)
s_contact = ParagraphStyle('Contact', fontName='MSYH', fontSize=8.5, leading=13,
                            textColor=MGRAY, alignment=TA_CENTER)
s_section = ParagraphStyle('Section', fontName='MSYHBD', fontSize=12, leading=16,
                            textColor=DARK_BLUE, spaceBefore=8, spaceAfter=2)
s_section_en = ParagraphStyle('SectionEn', fontName='CALIBRIB', fontSize=8, leading=10,
                               textColor=ACCENT, spaceAfter=4)
s_item = ParagraphStyle('Item', fontName='MSYHBD', fontSize=9, leading=12,
                         textColor=black, spaceBefore=4, spaceAfter=1)
s_item_en = ParagraphStyle('ItemEn', fontName='CALIBRI', fontSize=7.5, leading=10,
                            textColor=MGRAY, spaceAfter=1)
s_bullet = ParagraphStyle('Bullet', fontName='MSYH', fontSize=8, leading=11.5,
                           textColor=GRAY, leftIndent=10, spaceAfter=1.2)
s_body = ParagraphStyle('Body', fontName='MSYH', fontSize=8.5, leading=12.5,
                         textColor=GRAY, spaceAfter=2)
s_body_en = ParagraphStyle('BodyEn', fontName='CALIBRI', fontSize=7.5, leading=11,
                            textColor=MGRAY, spaceAfter=2)

# ---------- Helpers ----------
def section(cn, en):
    return [
        Paragraph('<font color="#1B3A5C">&#9642;</font>  ' + cn, s_section),
        Paragraph(en, s_section_en),
    ]

def exp_item(date, org_cn, org_en, title_cn, title_en, bullets):
    items = []
    items.append(Paragraph(
        '<font color="#2E75B6">%s</font>  |  <b>%s</b>  |  %s' % (date, org_cn, title_cn),
        s_item))
    items.append(Paragraph('%s  |  %s' % (org_en, title_en), s_item_en))
    for b in bullets:
        items.append(Paragraph('&#8226;  %s' % b, s_bullet))
    items.append(Spacer(1, 2*mm))
    return items

# ---------- Build document ----------
story = []

# --- Header with photo ---
photo = Image(r'D:\xry\个人资料\大头照\23.8.31\白底大头照23.8.31.jpg',
              width=26*mm, height=35*mm)
header = Table([[photo, [
    Paragraph('肖任钺', s_name),
    Paragraph('XIAO Renyue', s_name_en),
    Paragraph('求职意向：金融实习生  |  可实习时间：随时到岗', s_contact),
    Paragraph('广州  |  15217336427  |  Xry_2003@126.com', s_contact),
]]], colWidths=[35*mm, 125*mm])
header.setStyle(TableStyle([
    ('VALIGN', (0,0), (0,0), 'TOP'),
    ('VALIGN', (1,0), (1,0), 'MIDDLE'),
    ('LEFTPADDING', (1,0), (1,0), 12),
    ('TOPPADDING', (0,0), (-1,-1), 6),
    ('BOTTOMPADDING', (0,0), (-1,-1), 6),
]))
story.append(header)
story.append(Spacer(1, 3*mm))

# Blue accent line
line = Table([['']], colWidths=[160*mm], rowHeights=[1.5*mm])
line.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), DARK_BLUE)]))
story.append(line)
story.append(Spacer(1, 2*mm))

# ========== EDUCATION ==========
story += section('教育背景', 'EDUCATION')
story.append(Paragraph(
    '<b>2023.09 至今</b>  |  广东金融学院  |  金融工程（本科）', s_item))
story.append(Paragraph(
    'Guangdong University of Finance  |  Financial Engineering, B.S.', s_item_en))
story.append(Paragraph(
    '主修：金融学、投资学、证券投资分析、固定收益证券、商业银行经营学',
    s_body))
story.append(Paragraph(
    'Core: Finance, Investment, Securities Analysis, Fixed Income, Commercial Banking',
    s_body_en))
story.append(Spacer(1, 3*mm))

# ========== EXPERIENCE ==========
story += section('专业实践', 'PROFESSIONAL EXPERIENCE')

# --- Guotai Haitong ---
story += exp_item(
    '2025.07.14 - 2025.08.08',
    '国泰海通证券四川分公司',
    'Guotai Haitong Securities Sichuan Branch',
    '实习生', 'Intern',
    [
        '参与"川越星辰"暑期培训班，系统学习券商数字金融线上运营、投顾服务、资配方案、企业客户业务、两融业务及职业礼仪等实战知识体系',
        '于企业客户部深入学习投行类服务（融资财务顾问、并购重组、保荐承销、再融资）、投资类服务（私募股权投资、产业基金投资）及资产配置全流程',
        '协助营业部柜台接待客户、处理日常业务；参与营业部例会，全面掌握券商零售端运营模式',
        '带领实习生团队搭建并优化营业部线上直播间，独立完成"理财节"系列短视频的策划、拍摄与剪辑',
        '赴国泰君安期货四川分公司研学，深入分析生猪产业链供需格局，参与碳酸锂、焦煤等品种的期货交易实操',
    ])

# --- Qianhai Guochuang ---
story += exp_item(
    '2024.07 - 2024.08',
    '深圳前海国创投资咨询有限公司',
    'Shenzhen Qianhai Guochuang Investment Consulting',
    '实习生', 'Intern',
    ['参与项目策划执行，独立完成市场调研数据采集及商业分析报告撰写'])

# --- Galaxy Securities ---
story += exp_item(
    '2024.04 - 2025.04',
    '中国银河证券',
    'China Galaxy Securities',
    '会议助理', 'Conference Assistant',
    ['协助组织多场投资策略专题会议，整理汇总会议纪要及研究资料'])

# --- Jiangsu Agriculture ---
story += exp_item(
    '2024.04 - 2024.05',
    '江苏某农业企业政企合作项目',
    'Jiangsu Agricultural Enterprise, PPP Project',
    '策划助理', 'Planning Assistant',
    ['参与企业数字化转型升级及融资上市策划方案的调研与撰写工作'])

# --- Mock Exchange ---
story += exp_item(
    '2023.10 至今',
    '广东金融学院模拟证券交易所',
    'GDUF Mock Stock Exchange',
    '研发部部长', 'Head of R&D',
    ['主导模拟交易平台的日常运营，组织团队开展策略研究及定期复盘分析'])

# ========== SKILLS ==========
story += section('专业技能', 'SKILLS &amp; CERTIFICATIONS')
story.append(Paragraph(
    '<b>金融技能</b>  六年证券交易实操经验，拥有成熟的交易框架与敏锐的资本市场认知；长期跟踪经济金融类优质内容（公众号、播客），持续订阅《财新周刊》；擅长专业文书写作、会议总结及信息转化',
    s_body))
story.append(Paragraph(
    '<b>计算机技能</b>  精通 Office 全系套件，具备高水平的 PPT 设计与美化能力；熟练使用 Photoshop、Premiere、秀米等设计与剪辑工具；具有数字金融线上内容运营的实战经验',
    s_body))
story.append(Paragraph(
    '<b>语言能力</b>  英语 CET-4 / CET-6，具备良好的英文阅读与书面表达能力',
    s_body))
story.append(Spacer(1, 3*mm))

# ========== SELF-EVALUATION ==========
story += section('自我评价', 'SELF-EVALUATION')
story.append(Paragraph(
    '金融专业知识体系扎实，对经济、金融、商业及科技前沿保持持续热情与广泛涉猎。'
    '性格开朗，团队融入度高，工作细致认真且执行力突出。'
    '在国泰海通证券的系统化实习中，完整经历了从零售端到机构端、从传统经纪到衍生品交易的全业务链条，'
    '已构建起对证券公司商业模式与运作逻辑的多维度立体认知。',
    s_body))
story.append(Spacer(1, 1*mm))
story.append(Paragraph(
    'A proactive finance student with 6 years of real-market trading experience. '
    'The systematic internship at Guotai Haitong Securities provided comprehensive exposure across '
    'retail, institutional, and derivatives business lines. Proficient in financial analysis, digital content creation, '
    'and cross-functional teamwork. Eager to bring analytical rigor, creative energy, and a growth mindset to the next opportunity.',
    s_body_en))
story.append(Spacer(1, 3*mm))

# Footer accent
story.append(line)

# ---------- Build PDF ----------
doc = SimpleDocTemplate(
    '肖任钺_中英双语简历.pdf',
    pagesize=A4,
    leftMargin=15*mm,
    rightMargin=15*mm,
    topMargin=12*mm,
    bottomMargin=12*mm,
)
frame = Frame(15*mm, 12*mm, W - 30*mm, H - 24*mm, id='main')
doc.addPageTemplates([PageTemplate(id='Main', frames=frame)])
doc.build(story)
print('DONE: 肖任钺_中英双语简历.pdf')
