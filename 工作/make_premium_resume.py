#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Premium bilingual CV: Awesome-CV inspired design with Chinese + English, photo, accent colors."""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white, black, Color
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, Image, Frame, PageTemplate, Flowable,
                                 KeepTogether)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os, math

# ── Fonts ──────────────────────────────────────────
FD = r'C:\Windows\Fonts'
for name, fname, idx in [
    ('MSYH', 'msyh.ttc', 0), ('MSYHBD', 'msyhbd.ttc', 0),
    ('SIMSUN', 'simsun.ttc', 0),
    ('CAL', 'calibri.ttf', None), ('CALB', 'calibrib.ttf', None),
    ('CALL', 'calibril.ttf', None),
]:
    try:
        path = os.path.join(FD, fname)
        kw = {} if idx is None else {'subfontIndex': idx}
        pdfmetrics.registerFont(TTFont(name, path, **kw))
    except Exception:
        pass

W, H = A4
LM = 14*mm; RM = 14*mm; TM = 14*mm; BM = 10*mm
CW = W - LM - RM

# ── Palette ────────────────────────────────────────
PRIMARY   = HexColor('#0D2B4E')   # deep navy
ACCENT    = HexColor('#1A6FB5')   # bright blue
LIGHT_BG  = HexColor('#F0F5FB')   # soft blue bg
DARK_TEXT  = HexColor('#1A1A1A')
BODY_TEXT  = HexColor('#3A3A3A')
MUTED      = HexColor('#777777')
LINE_CLR   = HexColor('#CCCCCC')
SECTION_BG  = HexColor('#EAF1F8')

# ── Styles ─────────────────────────────────────────
s_name = ParagraphStyle('Name', fontName='MSYHBD', fontSize=26, leading=32,
                        textColor=PRIMARY, alignment=TA_LEFT, spaceAfter=0)
s_name_en = ParagraphStyle('NameEn', fontName='CALB', fontSize=12, leading=15,
                            textColor=MUTED, alignment=TA_LEFT, spaceAfter=3)
s_contact = ParagraphStyle('Contact', fontName='MSYH', fontSize=7.5, leading=11,
                            textColor=MUTED, alignment=TA_LEFT)
s_section = ParagraphStyle('Section', fontName='MSYHBD', fontSize=11, leading=15,
                            textColor=PRIMARY, spaceBefore=10, spaceAfter=2)
s_subsection = ParagraphStyle('Sub', fontName='CALB', fontSize=7.5, leading=9,
                               textColor=ACCENT, spaceAfter=4)
s_item = ParagraphStyle('Item', fontName='MSYHBD', fontSize=9, leading=12,
                         textColor=DARK_TEXT, spaceBefore=4, spaceAfter=0)
s_item_sub = ParagraphStyle('ItemSub', fontName='MSYH', fontSize=7.5, leading=10,
                             textColor=MUTED, spaceAfter=1)
s_body = ParagraphStyle('Body', fontName='MSYH', fontSize=7.8, leading=12,
                         textColor=BODY_TEXT, spaceAfter=1.5)
s_bullet = ParagraphStyle('Bullet', fontName='MSYH', fontSize=7.5, leading=11,
                           textColor=BODY_TEXT, leftIndent=8, spaceAfter=1,
                           bulletIndent=2)
s_body_en = ParagraphStyle('BodyEn', fontName='CAL', fontSize=7.2, leading=10,
                            textColor=MUTED, spaceAfter=1.5)
s_bullet_en = ParagraphStyle('BulletEn', fontName='CAL', fontSize=7, leading=10,
                              textColor=MUTED, leftIndent=8, spaceAfter=1)

# ── Helpers ────────────────────────────────────────
class HRule(Flowable):
    """Horizontal rule."""
    def __init__(self, width, color=LINE_CLR, thickness=0.5*mm):
        Flowable.__init__(self)
        self.width = width
        self.color = color
        self.thickness = thickness

    def wrap(self, availWidth, availHeight):
        return (min(self.width, availWidth), self.thickness)

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 0, self.width, 0)

class SectionBlock:
    """A section with coloured left bar."""
    def __init__(self, cn, en):
        self.cn = cn
        self.en = en

    def render(self):
        return [
            Table([
                [Paragraph(
                    '<font color="#0D2B4E" size="14">&#9642;</font>'
                    '  <b>%s</b>' % self.cn, s_section),
                 Paragraph(self.en, s_subsection)]
            ], colWidths=[CW * 0.48, CW * 0.52], hAlign='LEFT'),
            Spacer(1, 1*mm),
        ]

def exp_block(date, org_cn, org_en, title_cn, title_en, bullets, bullets_en):
    items = []
    items.append(Paragraph(
        '<font color="#1A6FB5">%s</font>  |  <b>%s</b>  |  %s' % (date, org_cn, title_cn),
        s_item))
    items.append(Paragraph(
        '<font color="#1A6FB5">%s</font>  |  %s  |  %s' % (date, org_en, title_en),
        s_item_sub))
    for i, b in enumerate(bullets):
        items.append(Paragraph('&#8226;  %s' % b, s_bullet))
        if i < len(bullets_en):
            items.append(Paragraph('&#8226;  %s' % bullets_en[i], s_bullet_en))
    items.append(Spacer(1, 2.5*mm))
    return items

# ── Story ──────────────────────────────────────────
S = []

# ═══════ HEADER ═══════
photo = Image(r'D:\xry\个人资料\大头照\23.8.31\白底大头照23.8.31.jpg',
              width=24*mm, height=32*mm)
header = Table([[photo, '', [
    Paragraph('肖 任 钺', s_name),
    Paragraph('XIAO Renyue', s_name_en),
    Spacer(1, 1*mm),
    Paragraph('金融实习生  |  可随时到岗', s_contact),
    Paragraph('广州  |  15217336427  |  Xry_2003@126.com', s_contact),
]]], colWidths=[28*mm, 5*mm, CW - 33*mm])
header.setStyle(TableStyle([
    ('VALIGN', (0,0), (0,0), 'TOP'),
    ('VALIGN', (2,0), (2,0), 'MIDDLE'),
    ('TOPPADDING', (0,0), (-1,-1), 0),
    ('BOTTOMPADDING', (0,0), (-1,-1), 0),
]))
S.append(header)
S.append(Spacer(1, 4*mm))

# top accent bar
bar = Table([['']], colWidths=[CW], rowHeights=[2.5*mm])
bar.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), PRIMARY)]))
S.append(bar)
S.append(Spacer(1, 3*mm))

# ═══════ MAIN: TWO COLUMNS ═══════
LC = CW * 0.60  # left column width
RC = CW * 0.40  # right column width
GAP = 6*mm

L = []  # left story
R = []  # right story

# ── LEFT COLUMN ──
L += SectionBlock('专业实践', 'PROFESSIONAL EXPERIENCE').render()

# 国泰海通
L += exp_block(
    '2025.07 - 2025.08',
    '国泰海通证券 四川分公司',
    'Guotai Haitong Securities, Sichuan Branch',
    '实习生', 'Intern',
    [
        '参与"川越星辰"暑期培训，系统学习数字金融运营、投顾服务、资配方案、企业客户业务、两融及职业礼仪',
        '于企业客户部学习投行类服务（融资财务顾问、并购重组、保荐承销、再融资等）与投资类全流程',
        '协助营业部柜台接待客户，处理日常业务；参加例会掌握券商零售运营模式',
        '带领实习团队搭建并优化线上直播间，独立策划拍摄剪辑"理财节"短视频',
        '赴国泰君安期货四川分公司研学，分析生猪产业链，参与碳酸锂、焦煤期货交易',
    ],
    [
        'Completed "Chuan Yue Xing Chen" summer program covering digital finance, advisory, asset allocation, corporate services, margin trading &amp; business etiquette',
        'Studied investment banking services (M&amp;A advisory, underwriting, refinancing) and investment products (PE, industrial funds) at Corporate Client Dept.',
        'Assisted柜台 staff in client reception; attended branch meetings to learn retail operations',
        'Led intern team to launch and optimize branch livestream studio; produced "Wealth Festival" video series',
        'Researched hog supply chain and traded lithium carbonate &amp; coking coal futures at Guotai Junan Futures Sichuan',
    ])

# 前海国创
L += exp_block(
    '2024.07 - 2024.08',
    '深圳前海国创投资咨询',
    'Shenzhen Qianhai Guochuang Investment Consulting',
    '实习生', 'Intern',
    ['参与项目策划执行，独立完成市场调研数据采集及商业分析报告'],
    ['Assisted in project planning &amp; execution; conducted market research &amp; business analysis'])

# 银河证券
L += exp_block(
    '2024.04 - 2025.04',
    '中国银河证券',
    'China Galaxy Securities',
    '会议助理', 'Conference Assistant',
    ['协助组织多场投资策略专题会议，整理汇总会议纪要及研究资料'],
    ['Coordinated investment strategy meetings; compiled minutes &amp; research materials'])

# 江苏农业
L += exp_block(
    '2024.04 - 2024.05',
    '江苏某农业企业 政企合作项目',
    'Jiangsu Agricultural PPP Project',
    '策划助理', 'Planning Assistant',
    ['参与企业数字化转型升级及融资上市策划方案的调研与撰写'],
    ['Contributed to research &amp; drafting of digital transformation and IPO planning proposals'])

# 模拟交易所
L += exp_block(
    '2023.10 至今',
    '广东金融学院 模拟证券交易所',
    'GDUF Mock Stock Exchange',
    '研发部部长', 'Head of R&amp;D',
    ['主导模拟交易平台运营，组织团队策略研究及定期复盘'],
    ['Led daily operations of mock trading platform; organized strategy research &amp; reviews'])

L.append(Spacer(1, 2*mm))
L += SectionBlock('教育背景', 'EDUCATION').render()
L.append(Paragraph(
    '<b>2023.09 至今</b>  |  广东金融学院  |  金融工程（本科）', s_item))
L.append(Paragraph(
    'Guangdong University of Finance  |  Financial Engineering, B.S.', s_item_sub))
L.append(Paragraph(
    '主修：金融学、投资学、证券投资分析、固定收益证券、商业银行经营学',
    s_body))
L.append(Paragraph(
    'Core: Finance, Investment, Securities Analysis, Fixed Income, Commercial Banking',
    s_body_en))
L.append(Spacer(1, 3*mm))

# ── RIGHT COLUMN ──
R += SectionBlock('个人照片', '').render()
R.append(Spacer(1, 1*mm))

R += SectionBlock('专业技能', 'SKILLS').render()
R.append(Paragraph(
    '<b>金融技能</b><br/>六年证券交易经验，成熟的交易框架与资本市场认知；跟踪经济金融媒体，订阅《财新周刊》；擅长文书写作与会议总结',
    ParagraphStyle('RSkill', fontName='MSYH', fontSize=7.2, leading=10.5,
                   textColor=BODY_TEXT, spaceAfter=3)))
R.append(Paragraph(
    '<b>计算机技能</b><br/>精通 Office 全套及 PPT 美化；熟练 Photoshop、Premiere、秀米；具备数字金融运营经验',
    ParagraphStyle('RSkill', fontName='MSYH', fontSize=7.2, leading=10.5,
                   textColor=BODY_TEXT, spaceAfter=3)))
R.append(Paragraph(
    '<b>语言能力</b><br/>英语 CET-4 / CET-6<br/>良好英文阅读与书面表达',
    ParagraphStyle('RSkill', fontName='MSYH', fontSize=7.2, leading=10.5,
                   textColor=BODY_TEXT, spaceAfter=5)))
R.append(Paragraph(
    '<b>Finance</b><br/>6yr stock trading · Capital market analysis · Financial writing · Caixin subscriber',
    ParagraphStyle('RSkillEn', fontName='CAL', fontSize=6.8, leading=9.5,
                   textColor=MUTED, spaceAfter=3)))
R.append(Paragraph(
    '<b>Technical</b><br/>MS Office · PPT design · Photoshop · Premiere · Xiùmǐ · Digital content ops',
    ParagraphStyle('RSkillEn', fontName='CAL', fontSize=6.8, leading=9.5,
                   textColor=MUTED, spaceAfter=3)))
R.append(Paragraph(
    '<b>Languages</b><br/>Chinese (native) · English (CET-4/6)',
    ParagraphStyle('RSkillEn', fontName='CAL', fontSize=6.8, leading=9.5,
                   textColor=MUTED, spaceAfter=5)))

R += SectionBlock('自我评价', 'SELF-EVALUATION').render()
R.append(Paragraph(
    '金融知识扎实，对经济、商业、科技前沿充满热情。性格开朗，团队协作能力强，执行力突出。',
    ParagraphStyle('REval', fontName='MSYH', fontSize=7.2, leading=10.5,
                   textColor=BODY_TEXT, spaceAfter=3, alignment=TA_JUSTIFY)))
R.append(Paragraph(
    '在国泰海通的系统化实习中，完整经历了零售、机构到衍生品交易的全业务链条，建立了对券商商业模式的立体认知。',
    ParagraphStyle('REval', fontName='MSYH', fontSize=7.2, leading=10.5,
                   textColor=BODY_TEXT, spaceAfter=4, alignment=TA_JUSTIFY)))
R.append(Paragraph(
    'A proactive finance student with 6yr trading experience. Systematic internship at Guotai Haitong covering retail, institutional and derivatives business lines. Eager to bring analytical rigor and creative energy.',
    ParagraphStyle('REvalEn', fontName='CAL', fontSize=6.8, leading=9.5,
                   textColor=MUTED, spaceAfter=3, alignment=TA_JUSTIFY)))

# ═══════ BUILD TWO-COLUMN PDF ═══════
class TwoColDocTemplate(SimpleDocTemplate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def handle_pageBegin(self):
        super().handle_pageBegin()
        # subtle sidebar background on right
        self._currPageTemplate = self.pageTemplates[0]

    def afterFlowable(self, flowable):
        pass

doc = SimpleDocTemplate(
    '肖任钺_精美中英双语简历.pdf',
    pagesize=A4,
    leftMargin=LM, rightMargin=RM,
    topMargin=TM, bottomMargin=BM,
    title='肖任钺 - 金融实习生简历',
    author='XIAO Renyue',
)

# Build as single-column -> actually we use a table to simulate two columns
main_table_data = [[
    L,  # left
    R,  # right
]]
main_table = Table(main_table_data, colWidths=[LC, RC],
                    hAlign='LEFT')
main_table.setStyle(TableStyle([
    ('VALIGN', (0,0), (0,0), 'TOP'),
    ('VALIGN', (1,0), (1,0), 'TOP'),
    ('LEFTPADDING', (0,0), (0,0), 0),
    ('RIGHTPADDING', (0,0), (0,0), 0),
    ('LEFTPADDING', (1,0), (1,0), 4*mm),
    ('RIGHTPADDING', (1,0), (1,0), 0),
    ('TOPPADDING', (0,0), (-1,-1), 0),
    ('BOTTOMPADDING', (0,0), (-1,-1), 0),
]))

story = []
story.append(main_table)

# Bottom bar
story.append(Spacer(1, 4*mm))
bottombar = Table([['']], colWidths=[CW], rowHeights=[1.5*mm])
bottombar.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), PRIMARY)]))
story.append(bottombar)

# Frame
frame = Frame(LM, BM, CW, H - TM - BM, id='main')
doc.addPageTemplates([PageTemplate(id='Main', frames=frame)])
doc.build(story)
print('DONE: 肖任钺_精美中英双语简历.pdf')
