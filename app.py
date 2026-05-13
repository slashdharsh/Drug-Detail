import streamlit as st
import requests

st.set_page_config(
    page_title="Drug Detail Aid Generator",
    page_icon="💊",
    layout="wide",
)

# ── Styling ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

.header-wrap {
    display: flex; justify-content: space-between; align-items: flex-end;
    padding: 1.5rem 0 1rem; border-bottom: 1px solid #e0e0e0; margin-bottom: 1.5rem;
}
.main-title {
    font-family: 'DM Serif Display', serif;
    font-size: 2.2rem; color: #042C53; margin: 0; font-weight: 400;
}
.sub-title { font-size: 0.85rem; color: #888; margin-top: 4px; }
.fda-badge {
    background: #042C53; color: #B5D4F4;
    padding: 6px 14px; border-radius: 6px;
    font-size: 0.75rem; letter-spacing: 0.1em; font-weight: 500;
}

.drug-header {
    background: #042C53; border-radius: 10px 10px 0 0;
    padding: 1.4rem 1.8rem; color: #E6F1FB;
}
.drug-title {
    font-family: 'DM Serif Display', serif;
    font-size: 2rem; font-weight: 400; margin: 0; text-transform: capitalize;
}
.drug-brand { font-size: 0.8rem; color: #85B7EB; margin-top: 4px; }

.section-card {
    background: #ffffff; border: 1px solid #e8e8e8;
    border-radius: 8px; padding: 1rem 1.2rem; margin-bottom: 0.75rem;
    height: 100%;
}
.section-label {
    font-size: 0.7rem; font-weight: 500; letter-spacing: 0.12em;
    text-transform: uppercase; color: #185FA5; margin-bottom: 0.5rem;
}
.section-content { font-size: 0.88rem; color: #333; line-height: 1.65; }

.warning-banner {
    background: #FCEBEB; border-left: 4px solid #E24B4A;
    border-radius: 0 6px 6px 0; padding: 0.7rem 1rem;
    font-size: 0.82rem; color: #791F1F; margin-bottom: 0.75rem;
}
.class-banner {
    background: #E6F1FB; border-radius: 6px;
    padding: 0.65rem 1rem; font-size: 0.82rem;
    color: #0C447C; margin-bottom: 0.75rem;
}
.footer-note {
    font-size: 0.75rem; color: #aaa; text-align: center;
    padding: 1rem 0 0.5rem; border-top: 1px solid #eee; margin-top: 1rem;
}
.pill-btn button {
    background: #f0f0f0 !important; border: 1px solid #ddd !important;
    border-radius: 20px !important; font-size: 0.8rem !important;
    padding: 4px 14px !important; color: #444 !important;
}
</style>
""", unsafe_allow_html=True)


# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-wrap">
  <div>
    <div style="background:#042C53;color:#B5D4F4;font-size:0.7rem;letter-spacing:0.1em;
         font-weight:500;padding:3px 10px;border-radius:4px;display:inline-block;margin-bottom:6px;">
      CLINICAL REFERENCE
    </div>
    <div class="main-title">Drug Detail Aid</div>
    <div class="sub-title">Structured prescribing information from FDA labeling data</div>
  </div>
  <div style="text-align:right;">
    <div style="font-family:'DM Serif Display',serif;font-size:1.6rem;color:#042C53;">FDA</div>
    <div style="font-size:0.7rem;color:#888;">OpenFDA · DailyMed</div>
  </div>
</div>
""", unsafe_allow_html=True)


# ── Search ────────────────────────────────────────────────────────────────────
col_input, col_btn = st.columns([5, 1])
with col_input:
    drug_name = st.text_input(
        label="Drug name",
        placeholder="Enter generic or brand name (e.g. Metformin, Lisinopril, Amoxicillin)",
        label_visibility="collapsed",
    )
with col_btn:
    search = st.button("Generate Aid", use_container_width=True, type="primary")

# Quick picks
st.markdown("**Quick picks:**")
quick_cols = st.columns(7)
quick_drugs = ["Metformin", "Amoxicillin", "Lisinopril", "Atorvastatin", "Omeprazole", "Amlodipine", "Sertraline"]
for i, drug in enumerate(quick_drugs):
    with quick_cols[i]:
        if st.button(drug, key=f"q_{drug}", use_container_width=True):
            drug_name = drug
            search = True

st.markdown("---")


# ── Helpers ───────────────────────────────────────────────────────────────────
def truncate(text, max_chars=380):
    if not text:
        return None
    t = text[0] if isinstance(text, list) else text
    if len(t) <= max_chars:
        return t
    return t[:max_chars].rsplit(" ", 1)[0] + "…"


def to_bullets(text, max_items=6):
    if not text:
        return None
    raw = text[0] if isinstance(text, list) else text
    import re
    items = [s.strip() for s in re.split(r'\n+|•|\u2022', raw) if s.strip()]
    items = [re.sub(r'^\d+\.\s*', '', i) for i in items][:max_items]
    if len(items) <= 1:
        return truncate(raw, 320)
    return "\n".join(f"• {i[:130]}{'…' if len(i)>130 else ''}" for i in items)


def fetch_drug(name):
    url = (
        f"https://api.fda.gov/drug/label.json"
        f"?search=openfda.generic_name:\"{name}\"+OR+openfda.brand_name:\"{name}\""
        f"&limit=1"
    )
    r = requests.get(url, timeout=10)
    data = r.json()
    if "results" not in data or not data["results"]:
        return None
    return data["results"][0]


def render_section(title, content, icon=""):
    if not content:
        return ""
    return f"""
<div class="section-card">
  <div class="section-label">{icon} {title}</div>
  <div class="section-content">{content.replace(chr(10), '<br>')}</div>
</div>"""


# ── Result ────────────────────────────────────────────────────────────────────
if search and drug_name.strip():
    with st.spinner(f"Fetching FDA data for **{drug_name}**…"):
        try:
            d = fetch_drug(drug_name.strip())
        except Exception as e:
            st.error(f"Network error: {e}")
            d = None

    if d is None:
        st.error(
            f"**No results found for '{drug_name}'.**  \n"
            "Try the generic name (e.g. `metformin` instead of `Glucophage`), or check spelling."
        )
    else:
        openfda = d.get("openfda", {})
        generic_name = (openfda.get("generic_name", [drug_name])[0]).title()
        brand_names   = ", ".join(set(openfda.get("brand_name", [])[:4])) or "N/A"
        manufacturer  = openfda.get("manufacturer_name", ["N/A"])[0][:45]
        route         = openfda.get("route", ["N/A"])[0]
        drug_class    = (
            openfda.get("pharm_class_epc", [None])[0]
            or openfda.get("pharm_class_cs", [None])[0]
            or "N/A"
        )

        has_warning = any([d.get("boxed_warning"), d.get("warnings_and_cautions"), d.get("warnings")])

        # Drug header
        st.markdown(f"""
<div class="drug-header">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;">
    <div>
      <div class="drug-title">{generic_name}</div>
      <div class="drug-brand">Brand(s): {brand_names}</div>
    </div>
    <div style="text-align:right;">
      <div style="background:rgba(183,212,244,0.18);color:#85B7EB;
           font-size:0.75rem;padding:3px 10px;border-radius:4px;display:inline-block;">
        {route}
      </div>
      <div style="font-size:0.75rem;color:#85B7EB;margin-top:6px;">{manufacturer}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

        # Banners
        if drug_class != "N/A":
            st.markdown(f'<div class="class-banner">🧬 <strong>Drug Class:</strong> {drug_class}</div>', unsafe_allow_html=True)
        if has_warning:
            st.markdown('<div class="warning-banner">⚠️ <strong>Boxed Warning / Important Safety Information included below</strong></div>', unsafe_allow_html=True)

        # Sections — 2-column grid
        sections = [
            ("Indications & Usage",       to_bullets(d.get("indications_and_usage"), 5),       "✅"),
            ("Dosage & Administration",    truncate(d.get("dosage_and_administration"), 420),    "💧"),
            ("Contraindications",          to_bullets(d.get("contraindications"), 5),            "🚫"),
            ("Warnings & Precautions",     truncate(d.get("boxed_warning") or d.get("warnings_and_cautions") or d.get("warnings"), 380), "⚠️"),
            ("Adverse Reactions",          to_bullets(d.get("adverse_reactions"), 6),            "📊"),
            ("Drug Interactions",          truncate(d.get("drug_interactions"), 340),            "🔄"),
            ("Pregnancy",                  truncate(d.get("pregnancy"), 280),                    "❤️"),
            ("Storage & Handling",         truncate(d.get("storage_and_handling"), 220),         "📦"),
        ]
        # Full-width indications
        ind = sections[0]
        if ind[1]:
            st.markdown(render_section(ind[0], ind[1], ind[2]), unsafe_allow_html=True)

        # Remaining in 2-cols
        pairs = [(sections[i], sections[i+1] if i+1 < len(sections) else None) for i in range(1, len(sections), 2)]
        for left, right in pairs:
            c1, c2 = st.columns(2)
            if left[1]:
                with c1:
                    st.markdown(render_section(left[0], left[1], left[2]), unsafe_allow_html=True)
            if right and right[1]:
                with c2:
                    st.markdown(render_section(right[0], right[1], right[2]), unsafe_allow_html=True)

        # Footer
        from datetime import date
        st.markdown(
            f'<div class="footer-note">Source: FDA OpenFDA Drug Label API · {date.today().strftime("%d %b %Y")}</div>',
            unsafe_allow_html=True
        )

elif not drug_name.strip() and not search:
    st.info("👆 Enter a drug name above and click **Generate Aid** to get started.")
