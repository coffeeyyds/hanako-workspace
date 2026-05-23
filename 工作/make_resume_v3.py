#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Premium bilingual CV v3 - Full-width header + two-column body with photo"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.platypus import (BaseDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, Image, Frame, PageTemplate, KeepTogether)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# ───── FONTS ─────
FD = r'C:\Windows\Fonts'
for tag, fname, idx in [
    ('ZH', 'msyh.ttc', 0),
    ('ZHB', 'msyhbd.ttc', 0),
    ('EN', 'calibri.ttf', None),
    ('ENB', 'calibrib.ttf', None),
]:
    path = os.path.join(FD, fname)
    kw = {} if idx is None else {'subfontIndex': idx}
    pdfmetrics.registerFont(TTFont(tag, path, **kw))

W, H = A4
LM = 13*mm; RM = 13*mm; TM = 12*mm; BM = 10*mm
CW = W - LM - RM  # content width

# ───── COLORS ─────
N  = HexColor('#0B2D52')  # navy
B  = HexColor('#1976D2')  # blue accent
DG = HexColor('#2D2D2D')
MG = HexColor('#707070')
LG = HexColor('#E8E8E8')

# ───── STYLES ─────
ST = {  # font sizes reduced for density
    'name':    ParagraphStyle('n',  fontName='ZHB', fontSize=26, leading=30, textColor=N, alignment=TA_LEFT),
    'name_en': ParagraphStyle('ne', fontName='ENB', fontSize=11, leading=14, textColor=MG, alignment=TA_LEFT, spaceAfter=2),
    'contact': ParagraphStyle('c',  fontName='ZH',  fontSize=7.5, leading=11, textColor=MG, alignment=TA_LEFT),
    'sect':    ParagraphStyle('s',  fontName='ZHB', fontSize=11.5, leading=15, textColor=N, spaceBefore=7, spaceAfter=1),
    'sect_en': ParagraphStyle('se', fontName='ENB', fontSize=7.5, leading=10, textColor=B, spaceAfter=4),
    'item':    ParagraphStyle('i',  fontName='ZHB', fontSize=9, leading=12, textColor=DG, spaceBefore=4, spaceAfter=0),
    'item_en': ParagraphStyle('ie', fontName='EN',  fontSize=7.2, leading=10, textColor=MG, spaceAfter=1),
    'body':    ParagraphStyle('b',  fontName='ZH',  fontSize=7.5, leading=11, textColor=DG, spaceAfter=2),
    'body_en': ParagraphStyle('be', fontName='EN',  fontSize=7, leading=10, textColor=MG, spaceAfter=2),
    'bullet':  ParagraphStyle('bl', fontName='ZH',  fontSize=7.3, leading=11, textColor=DG, leftIndent=6, spaceAfter=0.8),
    'bullet_en':ParagraphStyle('ble',fontName='EN', fontSize=6.8, leading=9.5, textColor=MG, leftIndent=6, spaceAfter=0.8),
    'skill':   ParagraphStyle('sk', fontName='ZH',  fontSize=7, leading=10, textColor=DG, spaceAfter=2),
    'skill_en':ParagraphStyle('ske',fontName='EN',  fontSize=6.5, leading=9, textColor=MG, spaceAfter=2),
    'eval':    ParagraphStyle('ev', fontName='ZH',  fontSize=7, leading=10, textColor=DG, spaceAfter=3, alignment=TA_JUSTIFY),
    'eval_en': ParagraphStyle('eve',fontName='EN',  fontSize=6.5, leading=9, textColor=MG, spaceAfter=3, alignment=TA_JUSTIFY),
}

# ───── HELPERS ─────
def section(cn, en):
    return [Paragraph('&#9632;  <b>%s</b>' % cn, ST['sect']),
            Paragraph(en, ST['sect_en'])]

def exp(date, org, org_en, title, title_en, bullets, bullets_en):
    r = [
        Paragraph('<font color="#1976D2">%s</font>  |  <b>%s</b>  |  %s' % (date, org, title), ST['item']),
        Paragraph('<font color="#1976D2">%s</font>  |  %s  |  %s' % (date, org_en, title_en), ST['item_en']),
    ]
    for b, be in zip(bullets, bullets_en):
        r.append(Paragraph('&#8226; %s' % b, ST['bullet']))
        r.append(Paragraph('&#8226; %s' % be, ST['bullet_en']))
    r.append(Spacer(1, 2*mm))
    return r

# ───── BUILD ─────
L = []  # left column (experiences + education)
R = []  # right column (skills + self-eval)

# === LEFT: HEADER ===
photo = Image(r'D:\xry\个人资料\大头照\23.8.31\白底大头照23.8.31.jpg', width=24*mm, height=32*mm)
hdr = Table([
    [photo, '', [
        Paragraph('肖 任 钺', ST['name']),
        Paragraph('XIAO Renyue', ST['name_en']),
        Paragraph('金融实习生  |  可随时到岗工作', ST['contact']),
        Paragraph('广州  |  15217336427  |  Xry_2003@126.com', ST['contact']),
    ]]
], colWidths=[28*mm, 4*mm, CW-32*mm], hAlign='LEFT')
hdr.setStyle(TableStyle([
    ('VALIGN', (0,0), (0,0), 'TOP'),
    ('VALIGN', (2,0), (2,0), 'MIDDLE'),
    ('TOPPADDING', (0,0), (-1,-1), 0),
    ('BOTTOMPADDING', (0,0), (-1,-1), 0),
]))
L.append(hdr)
L.append(Spacer(1, 3*mm))

# Navy bar (FULL WIDTH)
bar = Table([['']], colWidths=[CW], rowHeights=[2.2*mm])
bar.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), N)]))
L.append(bar)
L.append(Spacer(1, 3*mm))

# === EXPERIENCE ===
L += section('专业实践', 'PROFESSIONAL EXPERIENCE')

L += exp('2025.07 - 2025.08',
    '国泰海通证券 四川分公司',
    'Guotai Haitong Securities, Sichuan Branch',
    '实习生', 'Intern',
    ['参与"川越星辰"暑期培训班，系统学习数字金融线上运营、投顾、资配、企客服务、两融、职业礼仪与公文写作等实战知识体系',
     '于企业客户部深入学习投行类服务（融资财务顾问、并购重组、保荐承销、再融资）、投资类服务（私募股权、产业基金投资）及资产配置全流程',
     '协助营业部柜台接待客户、处理日常业务；参与营业部例会，掌握券商零售端运营模式',
     '带领实习生团队搭建并优化线上直播间，独立策划、拍摄并剪辑"理财节"短视频',
     '于国泰君安期货四川分公司研学，深入分析生猪产业链供需格局，参与碳酸锂、焦煤期货交易'],
    ['Completed "Chuan Yue Xing Chen" summer training: digital finance ops, advisory, asset allocation, corporate services, margin trading',
     'Studied IB services (M&A advisory, underwriting, refinancing) & investment products (PE, industrial funds) at Corporate Client Dept.',
     'Assisted柜台 operations & client reception; attended branch meetings for comprehensive retail knowledge',
     'Led intern team to build & optimize livestream studio; independently produced "Wealth Festival" video series',
     'Researched hog supply chain dynamics; traded lithium carbonate & coking coal futures at Guotai Junan Futures Sichuan'])

L += exp('2024.07 - 2024.08',
    '深圳前海国创投资咨询有限公司',
    'Qianhai Guochuang Investment Consulting',
    '实习生', 'Intern',
    ['参与项目策划与执行，独立完成市场调研数据采集与商业分析报告撰写'],
    ['Assisted in project planning & execution; conducted market research & drafted business analysis reports'])

L += exp('2024.04 - 2025.04',
    '中国银河证券',
    'China Galaxy Securities',
    '会议助理', 'Conference Assistant',
    ['协助组织多场投资策略专题会议，负责整理汇总会议纪要及相关研究资料'],
    ['Coordinated investment strategy meetings; compiled meeting minutes & research materials'])

L += exp('2024.04 - 2024.05',
    '江苏某农业企业 政企合作项目',
    'Jiangsu Agricultural Enterprise, PPP Project',
    '策划助理', 'Planning Assistant',
    ['参与企业数字化转型升级及融资上市策划方案的调研与撰写'],
    ['Contributed to research & drafting of digital transformation & IPO planning proposals'])

L += exp('2023.10 至今',
    '广东金融学院 模拟证券交易所',
    'GDUF Mock Stock Exchange',
    '研发部部长', 'Head of R&D',
    ['主导模拟交易平台日常运营，组织团队开展策略研究、定期复盘分析'],
    ['Led platform operations; organized research and periodic strategy reviews'])

L.append(Spacer(1, 2*mm))

# === EDUCATION ===
L += section('教育背景', 'EDUCATION')
L.append(Paragraph('<b>2023.09 至今</b>  |  广东金融学院  |  金融工程（本科）', ST['item']))
L.append(Paragraph('Guangdong University of Finance  |  Financial Engineering, B.S.', ST['item_en']))
L.append(Paragraph('主修：金融学、投资学、证券投资分析、固定收益证券、商业银行经营学', ST['body']))
L.append(Paragraph('Core: Finance, Investment, Securities Analysis, Fixed Income, Commercial Banking', ST['body_en']))

# === RIGHT COLUMN ===
R.append(Spacer(1, 1*mm))

R += section('专业技能', 'SKILLS & EXPERTISE')

R.append(Paragraph('<b>金融与投资</b>', ST['skill']))
R.append(Paragraph('六年证券实盘交易经验，成熟的交易框架与敏锐的资本市场认知；长期跟踪经济金融类优质内容（公众号、播客），持续订阅《财新周刊》；擅长专业文书写作、会议总结与深度内容转化', ST['skill']))
R.append(Paragraph('<b>Investment & Trading</b>  6yr stock trading · Market analysis · Financial writing · Caixin subscriber', ST['skill_en']))
R.append(Spacer(1, 1.5*mm))

R.append(Paragraph('<b>数字工具</b>', ST['skill']))
R.append(Paragraph('精通 Office 全系套件及 PPT 设计美化；熟练操作 Photoshop、Premiere、秀米等设计与剪辑工具；具备数字金融线上运营与短视频内容创作经验', ST['skill']))
R.append(Paragraph('<b>Digital Tools</b>  MS Office · Photoshop · Premiere · Xiùmǐ · Digital content ops · Video production', ST['skill_en']))
R.append(Spacer(1, 1.5*mm))

R.append(Paragraph('<b>语言能力</b>', ST['skill']))
R.append(Paragraph('英语 CET-4 / CET-6，具备良好的英文阅读与书面表达能力', ST['skill']))
R.append(Paragraph('<b>Languages</b>  English (CET-4/6) · Chinese (native)', ST['skill_en']))
R.append(Spacer(1, 2*mm))

# === SELF-EVALUATION ===
R += section('自我评价', 'SELF-EVALUATION')
R.append(Paragraph(
    '金融专业知识扎实，对经济、商业、科技前沿保持持续热忱与广泛涉猎。'
    '性格开朗，团队融入度高，工作严谨细致且执行力突出。'
    '在国泰海通的系统化实习中，完整经历零售→机构→衍生品全业务链条，'
    '已构建起对券商商业模式与业务运作逻辑的立体化认知。',
    ST['eval']))
R.append(Paragraph(
    'A proactive finance student with 6 years of real-market trading experience. '
    'The systematic internship at Guotai Haitong provided comprehensive exposure '
    'across retail, institutional, and derivatives business lines. '
    'Bringing analytical rigor, creative content skills, and a growth mindset to the next opportunity.',
    ST['eval_en']))

# === ASSEMBLE ===
LC = CW * 0.57
RC = CW * 0.43
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
# Bottom bar
story.append(Table([['']], colWidths=[CW], rowHeights=[1.5*mm],
                   style=TableStyle([('BACKGROUND', (0,0), (-1,-1), N)])))

# === BUILD PDF ===
doc = BaseDocTemplate(
    '肖任钺_中英双语简历.pdf',
    pagesize=A4,
    leftMargin=LM, rightMargin=RM, topMargin=TM, bottomMargin=BM,
    title='XIAO Renyue - CV',
)

frame = Frame(LM, BM, CW, H - TM - BM, id='main')
doc.addPageTemplates([PageTemplate(id='Main', frames=frame)])
doc.build(story)
print('DONE')
