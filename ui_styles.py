"""AutoNQ AI — Premium Design System"""

THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --bg-primary: #0f1117;
    --bg-card: #1a1d29;
    --bg-card-hover: #22263a;
    --border-subtle: rgba(255,255,255,0.06);
    --accent: #667eea;
    --accent-end: #764ba2;
    --success: #10b981;
    --warning: #f59e0b;
    --danger: #ef4444;
    --text-primary: #f1f5f9;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
}

html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
.block-container { padding-top: 1rem !important; max-width: 1200px; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f1117 0%, #1a1d29 100%) !important;
    border-right: 1px solid rgba(255,255,255,0.06);
}
[data-testid="stSidebar"] .stRadio > label { display: none; }
[data-testid="stSidebar"] .stRadio > div {
    display: flex; flex-direction: column; gap: 4px;
}
[data-testid="stSidebar"] .stRadio > div > label {
    background: transparent; padding: 10px 16px; border-radius: 10px;
    font-weight: 500; font-size: 14px; cursor: pointer;
    transition: all 0.2s ease; border: 1px solid transparent;
}
[data-testid="stSidebar"] .stRadio > div > label:hover {
    background: rgba(102,126,234,0.1); border-color: rgba(102,126,234,0.2);
}
[data-testid="stSidebar"] .stRadio > div > label[data-checked="true"],
[data-testid="stSidebar"] .stRadio > div [aria-checked="true"] {
    background: linear-gradient(135deg, rgba(102,126,234,0.15), rgba(118,75,162,0.15));
    border-color: rgba(102,126,234,0.3);
}

/* Buttons */
div.stButton > button {
    background: linear-gradient(135deg, #667eea, #764ba2); color: white;
    border: none; border-radius: 10px; font-weight: 600;
    padding: 0.55rem 1.2rem; transition: all 0.3s ease;
}
div.stButton > button:hover {
    transform: translateY(-2px); box-shadow: 0 6px 20px rgba(102,126,234,0.35);
}

/* Metrics */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, rgba(102,126,234,0.08), rgba(118,75,162,0.08));
    padding: 18px; border-radius: 14px;
    border: 1px solid rgba(255,255,255,0.06);
}

/* Expander */
.streamlit-expanderHeader { font-weight: 600 !important; font-size: 14px !important; }
</style>
"""

SIDEBAR_LOGO = """
<div style="text-align:center; padding: 20px 10px 10px;">
  <div style="font-size: 2.2rem; margin-bottom: 2px;">🤖</div>
  <h2 style="background: linear-gradient(135deg,#667eea,#764ba2);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    font-size: 1.5rem; font-weight: 800; margin: 0;">AutoNQ AI</h2>
  <p style="color: #64748b; font-size: 0.75rem; margin-top: 2px;">Audit Intelligence Platform</p>
</div>
"""

def kpi_card(icon, label, value, color="#667eea"):
    return f"""
    <div style="background: linear-gradient(135deg, {color}12, {color}08);
        border: 1px solid {color}25; border-radius: 14px; padding: 20px;
        text-align: center;">
        <div style="font-size: 1.5rem;">{icon}</div>
        <div style="color: #94a3b8; font-size: 0.8rem; margin: 6px 0 2px;">{label}</div>
        <div style="color: #f1f5f9; font-size: 1.6rem; font-weight: 700;">{value}</div>
    </div>"""

def section_header(icon, title, subtitle=""):
    sub = f'<p style="color:#94a3b8;font-size:0.9rem;margin:2px 0 0;">{subtitle}</p>' if subtitle else ""
    return f"""
    <div style="margin-bottom: 16px;">
        <h2 style="color:#f1f5f9;font-size:1.4rem;font-weight:700;margin:0;">
            {icon} {title}</h2>{sub}
    </div>"""

def ai_output_card(title, content):
    return f"""
    <div style="background:#1a1d29; border:1px solid rgba(255,255,255,0.06);
        border-radius:14px; padding:24px; margin:12px 0;">
        <div style="color:#667eea; font-weight:600; font-size:0.9rem;
            margin-bottom:12px;">🤖 {title}</div>
        <div style="color:#e2e8f0; font-size:0.92rem; line-height:1.7;
            white-space:pre-wrap;">{content}</div>
    </div>"""

def status_badge(connected=True):
    if connected:
        return '<span style="color:#10b981;font-size:0.85rem;">🟢 System Online</span>'
    return '<span style="color:#ef4444;font-size:0.85rem;">🔴 Disconnected</span>'

def empty_state(message):
    return f"""
    <div style="text-align:center; padding:60px 20px; color:#64748b;">
        <div style="font-size:2.5rem; margin-bottom:12px;">📭</div>
        <p style="font-size:1rem;">{message}</p>
    </div>"""

NAV_ITEMS = [
    "📝 Audit Entry",
    "📊 Summary",
    "📋 Audit Plan",
    "✅ Daily Q-Check",
    "🧾 Process Audit",
    "📌 Follow-up",
    "🌍 External Tracker",
    "📊 Repeatability"
] for Button set (On click(Action==Dialy.Quecheck())
