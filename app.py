import re
import io
from datetime import date

import requests
import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER

# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Drug Detail Aid Generator",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 1.2rem 3rem !important; max-width: 860px !important; }

.portal-header {
    display: flex; justify-content: space-between; align-items: flex-end;
    padding-bottom: 1.2rem; border-bottom: 1px solid #e0e4ea;
    margin-bottom: 1.5rem; flex-wrap: wrap; gap: 12px;
}
.main-title {
    font-family: 'DM Serif Display', serif;
    font-size: clamp(1.6rem, 5vw, 2.2rem);
    color: #042C53; margin: 0; font-weight: 400;
}
.badge-clinical {
    background: #042C53; color: #B5D4F4;
    padding: 3px 10px; border-radius: 4px;
    font-size: 0.68rem; letter-spacing: 0.12em;
    font-weight: 500; display: inline-block; margin-bottom: 6px;
}
.subtitle { font-size: 0.82rem; color: #888; margin-top: 3px; }
.fda-logo { font-family: 'DM Serif Display', serif; font-size: 1.5rem; color: #042C53; }
.fda-sub  { font-size: 0.68rem; color: #aaa; letter-spacing: 0.05em; }

.drug-header {
    background: linear-gradient(135deg, #042C53 0%, #0C447C 100%);
    border-radius: 10px 10px 0 0;
    padding: clamp(1rem,4vw,1.6rem) clamp(1rem,4vw,1.8rem);
    color: #E6F1FB;
}
.drug-name {
    font-family: 'DM Serif Display', serif;
    font-size: clamp(1.3rem,4vw,1.9rem);
    font-weight: 400; margin: 0; word-break: break-word;
}
.drug-brand { font-size: 0.78rem; color: #85B7EB; margin-top: 5px; }
.route-tag {
    background: rgba(183,212,244,0.18); color: #B5D4F4;
    font-size: 0.7rem; padding: 3px 10px; border-radius: 4px;
    display: inline-block;
}

.banner-class {
    background: #EBF4FD; padding: 0.6rem 1.2rem;
    font-size: 0.82rem; color: #0C447C;
    border-bottom: 1px solid #C5DCEF;
}
.banner-warning {
    background: #FEF3F2; border-left: 4px solid #E24B4A;
    padding: 0.6rem 1rem; font-size: 0.82rem;
    color: #791F1F; margin-bottom: 0.75rem;
}
.banner-india {
    background: #FFF8E7; border-left: 4px solid #F0A500;
    padding: 0.6rem 1rem; font-size: 0.82rem;
    color: #7A4F00; margin-bottom: 0.75rem; border-radius: 0 4px 4px 0;
}

.section-card {
    background: #fff; border: 1px solid #e8eaed;
    border-radius: 8px; padding: 1rem 1.2rem;
    margin-bottom: 0.75rem; height: 100%;
}
.section-label {
    font-size: 0.68rem; font-weight: 500;
    letter-spacing: 0.13em; text-transform: uppercase;
    color: #185FA5; margin-bottom: 0.5rem;
}
.section-content { font-size: 0.86rem; color: #2c2c2c; line-height: 1.7; }
.section-content ul { padding-left: 16px; margin: 0; }
.section-content li { margin-bottom: 3px; }

.card-footer {
    background: #f7f8fa; border: 1px solid #e8eaed; border-top: none;
    border-radius: 0 0 10px 10px; padding: 0.75rem 1.2rem;
    font-size: 0.72rem; color: #aaa;
    display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px;
}
.err-box {
    background: #FEF3F2; border-left: 4px solid #E24B4A;
    border-radius: 0 6px 6px 0; padding: 1rem 1.2rem;
    font-size: 0.88rem; color: #791F1F;
}
.quick-label { font-size: 0.78rem; color: #888; margin-bottom: 4px; }

@media (max-width: 600px) {
    .block-container { padding: 1rem 0.6rem 2rem !important; }
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def clean_text(text: str) -> str:
    """Strip leading section numbers like '1 ', '2.2 ', '5.1 ' and inline refs '( 5.1 )'."""
    if not text:
        return text
    text = re.sub(r'(?m)^\s*\d+(\.\d+)*\s+(?=[A-Z])', '', text)
    text = re.sub(r'\(\s*\d+(\.\d+)*\s*\)', '', text)
    text = re.sub(r'  +', ' ', text).strip()
    return text


def truncate(field, max_chars=400):
    if not field:
        return None
    t = field[0] if isinstance(field, list) else field
    t = clean_text(t)
    if len(t) <= max_chars:
        return t
    return t[:max_chars].rsplit(' ', 1)[0] + '…'


def to_bullets(field, max_items=6):
    if not field:
        return None
    raw = field[0] if isinstance(field, list) else field
    raw = clean_text(raw)
    items = [s.strip() for s in re.split(r'\n+|•|\u2022', raw) if s.strip()]
    items = [re.sub(r'^\d+(\.\d+)*\s*', '', i) for i in items][:max_items]
    if len(items) <= 1:
        return truncate(raw, 320)
    rows = ''.join(
        f"<li>{i[:140]}{'…' if len(i)>140 else ''}</li>"
        for i in items
    )
    return f"<ul>{rows}</ul>"


def fetch_drug(name: str):
    """OpenFDA exact search → broad fallback."""
    for query, broad in [
        (f'openfda.generic_name:"{name}"+OR+openfda.brand_name:"{name}"', False),
        (f'"{name}"', True),
    ]:
        url = f"https://api.fda.gov/drug/label.json?search={query}&limit=1"
        try:
            r = requests.get(url, timeout=12)
            data = r.json()
            if 'results' in data and data['results']:
                return data['results'][0], broad
        except Exception:
            pass
    return None, False


def render_section(title, content, icon):
    if not content:
        return ''
    return f"""
<div class="section-card">
  <div class="section-label">{icon}&nbsp; {title}</div>
  <div class="section-content">{content}</div>
</div>"""


# ─────────────────────────────────────────────────────────────────────────────
# PDF GENERATION
# ─────────────────────────────────────────────────────────────────────────────
NAVY   = colors.HexColor('#042C53')
BLUE   = colors.HexColor('#185FA5')
LTBLUE = colors.HexColor('#E6F1FB')
WARN_B = colors.HexColor('#FEF3F2')
WARN_R = colors.HexColor('#E24B4A')
BORDER = colors.HexColor('#e8eaed')
WHITE  = colors.white
DARK   = colors.HexColor('#2c2c2c')


def make_pdf(d: dict, drug_name: str) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=18*mm, rightMargin=18*mm,
                            topMargin=16*mm, bottomMargin=16*mm)

    def sty(name, **kw):
        return ParagraphStyle(name, fontName='Helvetica', **kw)

    title_sty  = sty('T',  fontName='Helvetica-Bold', fontSize=20, textColor=WHITE, leading=26)
    brand_sty  = sty('Br', fontSize=9,  textColor=colors.HexColor('#85B7EB'), leading=14)
    label_sty  = sty('L',  fontName='Helvetica-Bold', fontSize=7.5,
                     textColor=BLUE, leading=11, spaceAfter=3)
    body_sty   = sty('Bo', fontSize=8.5, textColor=DARK, leading=13)
    warn_sty   = sty('W',  fontSize=8.5, textColor=colors.HexColor('#791F1F'), leading=13)
    class_sty  = sty('C',  fontSize=8.5, textColor=colors.HexColor('#0C447C'), leading=13)
    foot_sty   = sty('F',  fontSize=7,   textColor=colors.HexColor('#aaaaaa'),
                     alignment=TA_CENTER, leading=10)

    openfda      = d.get('openfda', {})
    generic_name = (openfda.get('generic_name', [drug_name])[0]).title()
    brand_names  = ', '.join(set(openfda.get('brand_name', [])[:4])) or 'N/A'
    manufacturer = openfda.get('manufacturer_name', ['N/A'])[0][:50]
    route        = openfda.get('route', ['N/A'])[0]
    drug_class   = (openfda.get('pharm_class_epc', [None])[0]
                    or openfda.get('pharm_class_cs', [None])[0] or '')
    has_warning  = any([d.get('boxed_warning'),
                        d.get('warnings_and_cautions'), d.get('warnings')])

    W     = doc.width
    story = []

    # Header
    htbl = Table(
        [[
            [Paragraph(generic_name, title_sty),
             Paragraph(f'Brand(s): {brand_names}', brand_sty)],
            [Paragraph(f'<font color="#B5D4F4"><b>{route}</b></font>', brand_sty),
             Paragraph(f'<font color="#85B7EB">{manufacturer}</font>', brand_sty)],
        ]],
        colWidths=[W*0.68, W*0.32]
    )
    htbl.setStyle(TableStyle([
        ('BACKGROUND',   (0,0),(-1,-1), NAVY),
        ('VALIGN',       (0,0),(-1,-1), 'TOP'),
        ('LEFTPADDING',  (0,0),(-1,-1), 10),
        ('RIGHTPADDING', (0,0),(-1,-1), 10),
        ('TOPPADDING',   (0,0),(-1,-1), 10),
        ('BOTTOMPADDING',(0,0),(-1,-1), 10),
        ('ALIGN',        (1,0),(1,0),   'RIGHT'),
    ]))
    story.append(htbl)

    if drug_class:
        ct = Table([[Paragraph(f'Drug Class: {drug_class}', class_sty)]], colWidths=[W])
        ct.setStyle(TableStyle([
            ('BACKGROUND',   (0,0),(-1,-1), LTBLUE),
            ('LEFTPADDING',  (0,0),(-1,-1), 10),
            ('TOPPADDING',   (0,0),(-1,-1), 6),
            ('BOTTOMPADDING',(0,0),(-1,-1), 6),
        ]))
        story.append(ct)

    if has_warning:
        wt = Table([[Paragraph('WARNING: Boxed Warning / Important Safety Information included below', warn_sty)]], colWidths=[W])
        wt.setStyle(TableStyle([
            ('BACKGROUND',   (0,0),(-1,-1), WARN_B),
            ('LEFTPADDING',  (0,0),(-1,-1), 10),
            ('TOPPADDING',   (0,0),(-1,-1), 6),
            ('BOTTOMPADDING',(0,0),(-1,-1), 6),
        ]))
        story.append(wt)

    story.append(Spacer(1, 6))

    sections = [
        ('Indications & Usage',     to_bullets(d.get('indications_and_usage'), 6)),
        ('Dosage & Administration',  truncate(d.get('dosage_and_administration'), 500)),
        ('Contraindications',        to_bullets(d.get('contraindications'), 5)),
        ('Warnings & Precautions',   truncate(d.get('boxed_warning') or
                                              d.get('warnings_and_cautions') or
                                              d.get('warnings'), 500)),
        ('Adverse Reactions',        to_bullets(d.get('adverse_reactions'), 6)),
        ('Drug Interactions',        truncate(d.get('drug_interactions'), 400)),
        ('Pregnancy',                truncate(d.get('pregnancy'), 320)),
        ('Storage & Handling',       truncate(d.get('storage_and_handling'), 260)),
    ]

    def cell(title, content):
        if not content:
            return [Paragraph('', body_sty)]
        plain = re.sub(r'<[^>]+>', ' ', content).strip()
        return [Paragraph(title.upper(), label_sty), Paragraph(plain, body_sty)]

    CELL_STYLE = [
        ('VALIGN',       (0,0),(-1,-1), 'TOP'),
        ('LEFTPADDING',  (0,0),(-1,-1), 10),
        ('RIGHTPADDING', (0,0),(-1,-1), 10),
        ('TOPPADDING',   (0,0),(-1,-1), 9),
        ('BOTTOMPADDING',(0,0),(-1,-1), 9),
        ('BACKGROUND',   (0,0),(-1,-1), WHITE),
    ]

    # Full-width indications
    if sections[0][1]:
        t = Table([[cell(sections[0][0], sections[0][1])]], colWidths=[W])
        t.setStyle(TableStyle(CELL_STYLE + [('BOX',(0,0),(-1,-1),0.5,BORDER)]))
        story.append(t)
        story.append(Spacer(1, 4))

    half = (W - 4) / 2
    for i in range(1, len(sections), 2):
        l = sections[i]
        r = sections[i+1] if i+1 < len(sections) else (None, None)
        lc = cell(l[0], l[1])
        rc = cell(r[0], r[1]) if r[0] else [Paragraph('', body_sty)]
        t = Table([[lc, rc]], colWidths=[half, half])
        t.setStyle(TableStyle(CELL_STYLE + [
            ('BOX', (0,0),(0,-1), 0.5, BORDER),
            ('BOX', (1,0),(1,-1), 0.5, BORDER),
        ]))
        story.append(t)
        story.append(Spacer(1, 4))

    story.append(Spacer(1, 8))
    story.append(HRFlowable(width='100%', thickness=0.5, color=BORDER))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        f'Source: FDA OpenFDA Drug Label API  ·  Generated: {date.today().strftime("%d %b %Y")}  ·  For professional use only',
        foot_sty
    ))

    doc.build(story)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="portal-header">
  <div>
    <div class="badge-clinical">CLINICAL REFERENCE</div>
    <div class="main-title">Drug Detail Aid</div>
    <div class="subtitle">Structured prescribing information from FDA labeling data</div>
  </div>
  <div style="text-align:right;">
    <div class="fda-logo">FDA</div>
    <div class="fda-sub">OpenFDA · DailyMed</div>
  </div>
</div>
""", unsafe_allow_html=True)

col_in, col_btn = st.columns([5, 1])
with col_in:
    drug_name = st.text_input('drug', label_visibility='collapsed',
        placeholder='Enter generic or brand name (e.g. Metformin, Augmentin, Keytruda, Paracetamol…)')
with col_btn:
    search = st.button('Generate Aid', use_container_width=True, type='primary')

st.markdown('<div class="quick-label">Quick picks:</div>', unsafe_allow_html=True)
quick_drugs = [
    'Metformin','Amoxicillin','Lisinopril','Atorvastatin',
    'Omeprazole','Amlodipine','Sertraline',
    'Paracetamol','Azithromycin','Pantoprazole','Ciprofloxacin','Ivermectin',
]
qcols = st.columns(6)
for i, drug in enumerate(quick_drugs):
    with qcols[i % 6]:
        if st.button(drug, key=f'q_{drug}', use_container_width=True):
            drug_name = drug
            search = True

st.markdown('---')

ICONS = {
    'Indications & Usage':     '✅',
    'Dosage & Administration': '💧',
    'Contraindications':       '🚫',
    'Warnings & Precautions':  '⚠️',
    'Adverse Reactions':       '📊',
    'Drug Interactions':       '🔄',
    'Pregnancy':               '❤️',
    'Storage & Handling':      '📦',
}

if search and drug_name.strip():
    with st.spinner(f'Fetching FDA data for **{drug_name}**…'):
        try:
            d, broad_match = fetch_drug(drug_name.strip())
        except Exception as e:
            st.error(f'Network error: {e}')
            d, broad_match = None, False

    if d is None:
        st.markdown(f"""
<div class="err-box">
  <strong>No results found for '{drug_name}'.</strong><br><br>
  Try the active ingredient instead of the brand name:<br>
  &nbsp;• <code>Paracetamol</code> instead of Crocin / Calpol / Dolo<br>
  &nbsp;• <code>Amoxicillin Clavulanate</code> instead of Augmentin<br>
  &nbsp;• <code>Azithromycin</code> instead of Azee / Zithromax<br><br>
  Note: Indian-only brands are not in the FDA database.
</div>""", unsafe_allow_html=True)
    else:
        openfda      = d.get('openfda', {})
        generic_name = (openfda.get('generic_name', [drug_name])[0]).title()
        brand_names  = ', '.join(set(openfda.get('brand_name', [])[:4])) or 'N/A'
        manufacturer = openfda.get('manufacturer_name', ['N/A'])[0][:48]
        route        = openfda.get('route', ['N/A'])[0]
        drug_class   = (openfda.get('pharm_class_epc', [None])[0]
                        or openfda.get('pharm_class_cs', [None])[0] or 'N/A')
        has_warning  = any([d.get('boxed_warning'),
                            d.get('warnings_and_cautions'), d.get('warnings')])

        st.markdown(f"""
<div class="drug-header">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:10px;">
    <div>
      <div class="drug-name">{generic_name}</div>
      <div class="drug-brand">Brand(s): {brand_names}</div>
    </div>
    <div style="text-align:right;">
      <div class="route-tag">{route}</div>
      <div style="font-size:.75rem;color:#85B7EB;margin-top:6px;">{manufacturer}</div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

        if drug_class != 'N/A':
            st.markdown(f'<div class="banner-class">🧬 &nbsp;<strong>Drug Class:</strong> {drug_class}</div>',
                        unsafe_allow_html=True)
        if broad_match:
            st.markdown("""
<div class="banner-india">
  🇮🇳 &nbsp;<strong>Note:</strong> Retrieved via broad search — likely an Indian / alternate brand name.
  Always verify against local CDSCO prescribing information.
</div>""", unsafe_allow_html=True)
        if has_warning:
            st.markdown("""
<div class="banner-warning">
  ⚠️ &nbsp;<strong>Boxed Warning / Important Safety Information included below</strong>
</div>""", unsafe_allow_html=True)

        sections = [
            ('Indications & Usage',    to_bullets(d.get('indications_and_usage'), 6)),
            ('Dosage & Administration', truncate(d.get('dosage_and_administration'), 480)),
            ('Contraindications',       to_bullets(d.get('contraindications'), 5)),
            ('Warnings & Precautions',  truncate(d.get('boxed_warning') or
                                                  d.get('warnings_and_cautions') or
                                                  d.get('warnings'), 480)),
            ('Adverse Reactions',       to_bullets(d.get('adverse_reactions'), 6)),
            ('Drug Interactions',       truncate(d.get('drug_interactions'), 400)),
            ('Pregnancy',               truncate(d.get('pregnancy'), 320)),
            ('Storage & Handling',      truncate(d.get('storage_and_handling'), 240)),
        ]

        # Full-width indications
        ind = sections[0]
        if ind[1]:
            st.markdown(render_section(ind[0], ind[1], ICONS[ind[0]]), unsafe_allow_html=True)

        # 2-column pairs
        for i in range(1, len(sections), 2):
            left  = sections[i]
            right = sections[i+1] if i+1 < len(sections) else None
            c1, c2 = st.columns(2)
            if left[1]:
                with c1:
                    st.markdown(render_section(left[0], left[1], ICONS[left[0]]), unsafe_allow_html=True)
            if right and right[1]:
                with c2:
                    st.markdown(render_section(right[0], right[1], ICONS[right[0]]), unsafe_allow_html=True)

        st.markdown(f"""
<div class="card-footer">
  <span>Source: FDA OpenFDA Drug Label API · {date.today().strftime('%d %b %Y')}</span>
  <span>For professional use only</span>
</div>""", unsafe_allow_html=True)

        st.markdown('<br>', unsafe_allow_html=True)

        with st.spinner('Preparing PDF…'):
            pdf_bytes = make_pdf(d, drug_name)

        st.download_button(
            label='⬇️  Download Detail Aid as PDF',
            data=pdf_bytes,
            file_name=f"{generic_name.replace(' ', '_')}_Detail_Aid.pdf",
            mime='application/pdf',
            use_container_width=True,
        )

else:
    st.markdown("""
<div style="text-align:center;padding:3rem 1rem;color:#bbb;">
  <div style="font-size:2.5rem;margin-bottom:10px;">💊</div>
  <div style="font-size:0.9rem;">Enter a drug name above and click <strong>Generate Aid</strong></div>
</div>""", unsafe_allow_html=True)
