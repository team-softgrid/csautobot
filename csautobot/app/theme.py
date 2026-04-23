"""csautobot 공통 UI 테마.

참조 프로토타입(``prototype.html``)의 디자인 토큰을 Streamlit 위에 적용한다.
- 딥 다크 배경 (#0b0e14) + 시안/스카이/핑크 그라디언트 액센트
- 글래스모피즘 카드 (반투명 + blur + 얇은 보더)
- Inter (본문) / Outfit (헤딩) 폰트
- floating blur orb 와 radial-gradient 배경 레이어

모든 페이지는 진입 시 :func:`inject_global_css` 를 호출한다.
"""
from __future__ import annotations

import streamlit as st

BRAND_NAME = "csautobot"
BRAND_TAGLINE = "EV Infrastructure Technical Copilot"
BRAND_SUB = "전기차 충전소 AI 점검·AS 코파일럿"

# --- 디자인 토큰 (prototype.html :root 와 동기화) ---
COLOR_PRIMARY = "#00f2fe"    # 일렉트릭 시안
COLOR_SECONDARY = "#4facfe"  # 스카이 블루
COLOR_ACCENT = "#f093fb"     # 핑크 (하이라이트)
COLOR_BG = "#0b0e14"
COLOR_BG_SOFT = "#11151f"
COLOR_TEXT = "#e0e0e0"
COLOR_MUTED = "#a0a0a0"
COLOR_SUCCESS = "#10b981"
COLOR_WARN = "#f59e0b"
COLOR_DANGER = "#ef4444"
GLASS_BG = "rgba(255,255,255,0.05)"
GLASS_BORDER = "rgba(255,255,255,0.10)"
GLASS_BORDER_STRONG = "rgba(255,255,255,0.18)"

_CSS = f"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=Outfit:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
:root {{
  --primary: {COLOR_PRIMARY};
  --secondary: {COLOR_SECONDARY};
  --accent: {COLOR_ACCENT};
  --bg: {COLOR_BG};
  --bg-soft: {COLOR_BG_SOFT};
  --text: {COLOR_TEXT};
  --text-dim: {COLOR_MUTED};
  --card-bg: {GLASS_BG};
  --glass-border: {GLASS_BORDER};
  --success: {COLOR_SUCCESS};
  --warn: {COLOR_WARN};
  --danger: {COLOR_DANGER};
}}

/* 전체 배경 + 기본 타이포 */
html, body, [class*="stApp"] {{
  background:
    radial-gradient(900px 520px at 90% -10%, rgba(79,172,254,0.14), transparent 60%),
    radial-gradient(800px 480px at 0% 110%, rgba(240,147,251,0.10), transparent 60%),
    {COLOR_BG} !important;
  color: var(--text) !important;
  font-family: "Inter", "Pretendard", "Apple SD Gothic Neo", "Noto Sans KR",
               -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
  line-height: 1.6;
}}

.main .block-container {{
  padding-top: 1.3rem;
  padding-bottom: 3rem;
  max-width: 1240px;
}}

h1, h2, h3, h4 {{
  font-family: "Outfit", "Inter", "Pretendard", sans-serif !important;
  color: var(--text) !important;
  letter-spacing: -0.01em;
}}
h1 {{ font-weight: 800; }}
h2 {{ font-weight: 700; }}
h3 {{ font-weight: 700; }}
h4 {{ font-weight: 600; }}

/* ---------- 사이드바 ---------- */
section[data-testid="stSidebar"] > div {{
  background: linear-gradient(180deg, #0a0d14 0%, #0d1220 100%) !important;
  border-right: 1px solid var(--glass-border);
}}
section[data-testid="stSidebar"] * {{ color: var(--text) !important; }}
section[data-testid="stSidebar"] .stRadio label {{
  padding: 6px 8px; border-radius: 8px;
  transition: background-color 0.15s ease;
}}
section[data-testid="stSidebar"] .stRadio label:hover {{
  background: rgba(255,255,255,0.04);
}}
section[data-testid="stSidebar"] .stRadio [data-baseweb="radio"] {{
  margin-right: 6px;
}}

/* ---------- 버튼 ---------- */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {{
  background: var(--card-bg) !important;
  color: var(--text) !important;
  border: 1px solid var(--glass-border) !important;
  border-radius: 10px !important;
  font-weight: 600 !important;
  backdrop-filter: blur(8px);
  transition: all 0.2s ease;
}}
.stButton > button:hover, .stDownloadButton > button:hover, .stFormSubmitButton > button:hover {{
  border-color: var(--primary) !important;
  color: var(--primary) !important;
  box-shadow: 0 0 0 1px rgba(0,242,254,0.4) inset,
              0 10px 24px -10px rgba(0,242,254,0.35);
}}

.stButton > button[kind="primary"], button[data-testid="baseButton-primary"],
.stFormSubmitButton > button[kind="primary"] {{
  background: linear-gradient(135deg, var(--secondary), var(--primary)) !important;
  color: #00141a !important;
  border: none !important;
  font-weight: 700 !important;
  box-shadow: 0 10px 24px -8px rgba(0,242,254,0.35);
}}
.stButton > button[kind="primary"]:hover {{
  transform: translateY(-2px);
  box-shadow: 0 16px 32px -10px rgba(0,242,254,0.55);
  filter: brightness(1.05);
}}

/* ---------- 입력 위젯 ---------- */
.stTextInput > div > div,
.stTextArea textarea,
.stSelectbox > div > div,
.stNumberInput > div > div,
.stDateInput > div > div,
.stFileUploader > div {{
  background: rgba(255,255,255,0.04) !important;
  border: 1px solid var(--glass-border) !important;
  border-radius: 12px !important;
  color: var(--text) !important;
}}
.stTextInput input, .stTextArea textarea {{
  color: var(--text) !important;
}}
.stTextInput input:focus, .stTextArea textarea:focus,
.stSelectbox > div > div:focus-within,
.stNumberInput > div > div:focus-within {{
  border-color: var(--primary) !important;
}}
.stSlider [data-baseweb="slider"] > div > div > div {{
  background: linear-gradient(90deg, var(--secondary), var(--primary)) !important;
}}

/* ---------- 메트릭 카드 (KPI 느낌) ---------- */
[data-testid="stMetric"] {{
  background: var(--card-bg);
  border: 1px solid var(--glass-border);
  border-radius: 16px;
  padding: 18px 20px;
  backdrop-filter: blur(10px);
  transition: transform 0.25s ease, border-color 0.25s ease;
}}
[data-testid="stMetric"]:hover {{
  transform: translateY(-3px);
  border-color: var(--secondary);
}}
[data-testid="stMetricLabel"] {{
  color: var(--text-dim) !important;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 12px !important;
}}
[data-testid="stMetricValue"] {{
  color: var(--primary) !important;
  font-family: "Outfit", sans-serif !important;
  font-weight: 700 !important;
}}
[data-testid="stMetricDelta"] {{ color: var(--success) !important; }}

/* ---------- Expander ---------- */
.streamlit-expanderHeader, [data-testid="stExpander"] summary {{
  background: var(--card-bg) !important;
  border: 1px solid var(--glass-border) !important;
  border-radius: 12px !important;
  color: var(--text) !important;
  backdrop-filter: blur(6px);
}}
[data-testid="stExpander"] {{ border: none; }}

/* ---------- Alerts ---------- */
.stAlert {{
  border-radius: 12px !important;
  border: 1px solid var(--glass-border) !important;
  background: rgba(255,255,255,0.03) !important;
}}

/* ---------- DataFrame ---------- */
[data-testid="stDataFrame"] {{
  border: 1px solid var(--glass-border);
  border-radius: 14px;
  overflow: hidden;
}}

/* ---------- Tabs ---------- */
[data-baseweb="tab-list"] {{ gap: 4px; }}
[data-baseweb="tab"] {{
  background: transparent !important;
  color: var(--text-dim) !important;
  border-radius: 10px !important;
  padding: 8px 14px !important;
}}
[data-baseweb="tab"][aria-selected="true"] {{
  background: var(--card-bg) !important;
  color: var(--primary) !important;
  border: 1px solid var(--glass-border) !important;
}}

/* ---------- Hero / Landing ---------- */
.csa-hero {{
  position: relative;
  padding: 72px 48px 64px 48px;
  border-radius: 28px;
  background:
    radial-gradient(circle at 85% -10%, rgba(79,172,254,0.18), transparent 60%),
    radial-gradient(circle at 10% 120%, rgba(240,147,251,0.13), transparent 60%),
    linear-gradient(180deg, #0d1220 0%, #0a0e18 100%);
  border: 1px solid var(--glass-border);
  overflow: hidden;
  margin-bottom: 28px;
  text-align: center;
}}
.csa-hero::before {{
  content: "";
  position: absolute; inset: 0;
  background: url('https://www.transparenttextures.com/patterns/carbon-fibre.png');
  opacity: 0.08;
  pointer-events: none;
}}
.csa-hero .orb {{
  position: absolute;
  width: 180px; height: 180px;
  border-radius: 50%;
  background: var(--primary);
  filter: blur(90px);
  opacity: 0.22;
  z-index: 0;
}}
.csa-hero .badge {{
  position: relative; z-index: 1;
  display: inline-block;
  padding: 0.45rem 1.2rem;
  background: rgba(0,242,254,0.1);
  border: 1px solid var(--primary);
  color: var(--primary);
  border-radius: 50px;
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  margin-bottom: 22px;
}}
.csa-hero h1 {{
  position: relative; z-index: 1;
  font-family: "Outfit", sans-serif;
  font-size: 54px;
  line-height: 1.1;
  margin: 0 auto 18px auto;
  max-width: 820px;
  background: linear-gradient(to right, #fff, var(--secondary), var(--primary));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}}
.csa-hero p.lead {{
  position: relative; z-index: 1;
  color: var(--text-dim);
  max-width: 720px;
  margin: 0 auto 28px auto;
  font-size: 17px;
  line-height: 1.7;
}}
.csa-hero .chip-row {{
  position: relative; z-index: 1;
  display: flex; gap: 10px; justify-content: center; flex-wrap: wrap;
}}
.csa-chip {{
  display: inline-flex; align-items: center; gap: 8px;
  padding: 7px 14px;
  border-radius: 999px;
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--glass-border);
  color: var(--text);
  font-size: 13px;
}}
.csa-chip .dot {{
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--primary);
  box-shadow: 0 0 8px 2px rgba(0,242,254,0.6);
}}

/* ---------- KPI grid ---------- */
.csa-kpi-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 18px;
  margin: 6px 0 24px 0;
}}
.csa-kpi-card {{
  background: var(--card-bg);
  border: 1px solid var(--glass-border);
  padding: 22px 22px;
  border-radius: 18px;
  backdrop-filter: blur(10px);
  transition: transform 0.25s ease, border-color 0.25s ease;
}}
.csa-kpi-card:hover {{
  transform: translateY(-4px);
  border-color: var(--secondary);
}}
.csa-kpi-card .label {{
  color: var(--text-dim);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 6px;
}}
.csa-kpi-card .value {{
  font-family: "Outfit", sans-serif;
  font-size: 34px;
  font-weight: 800;
  color: var(--primary);
  line-height: 1.15;
}}
.csa-kpi-card .trend {{
  margin-top: 10px;
  font-size: 12px;
  color: var(--text-dim);
}}
.csa-kpi-card .trend .up {{ color: var(--success); }}
.csa-kpi-card .trend .down {{ color: var(--danger); }}

/* ---------- Feature grid ---------- */
.csa-feature-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 22px;
  margin: 8px 0 24px 0;
}}
.csa-feature-card {{
  background: var(--card-bg);
  border: 1px solid var(--glass-border);
  border-radius: 18px;
  padding: 24px 22px;
  backdrop-filter: blur(10px);
  transition: transform 0.2s ease, border-color 0.2s ease;
  display: flex; gap: 16px; align-items: flex-start;
}}
.csa-feature-card:hover {{
  transform: translateY(-3px);
  border-color: var(--secondary);
}}
.csa-feature-card .icon {{
  width: 48px; height: 48px; flex-shrink: 0;
  border-radius: 14px;
  background: linear-gradient(135deg, var(--secondary), var(--primary));
  display: inline-flex; align-items: center; justify-content: center;
  color: #00141a;
  font-size: 22px;
  font-weight: 800;
}}
.csa-feature-card h4 {{
  margin: 0 0 6px 0;
  font-size: 17px;
  font-weight: 700;
  color: var(--text);
}}
.csa-feature-card p {{
  margin: 0;
  color: var(--text-dim);
  font-size: 14px;
  line-height: 1.65;
}}

/* ---------- Section title ---------- */
.csa-section-title {{
  text-align: center;
  margin: 36px 0 22px 0;
}}
.csa-section-title h2 {{
  font-size: 30px;
  margin: 0 0 8px 0;
  color: var(--text);
}}
.csa-section-title p {{
  color: var(--text-dim);
  margin: 0;
  font-size: 14px;
}}
.csa-section-title .eyebrow {{
  display: inline-block;
  font-size: 12px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--accent);
  margin-bottom: 8px;
}}

/* ---------- Architecture steps ---------- */
.csa-arch-card {{
  background: rgba(255,255,255,0.02);
  border: 1px solid var(--glass-border);
  padding: 28px;
  border-radius: 22px;
  backdrop-filter: blur(8px);
}}
.csa-arch-step {{
  display: flex; align-items: flex-start; gap: 18px;
  position: relative; margin-bottom: 22px;
}}
.csa-arch-step:last-child {{ margin-bottom: 0; }}
.csa-arch-step:not(:last-child)::after {{
  content: "";
  position: absolute;
  left: 19px; top: 42px;
  width: 2px; height: 22px;
  background: linear-gradient(to bottom, var(--primary), transparent);
}}
.csa-arch-step .num {{
  width: 40px; height: 40px;
  background: rgba(0,242,254,0.08);
  border: 1px solid var(--primary);
  border-radius: 50%;
  display: inline-flex; align-items: center; justify-content: center;
  font-weight: 700;
  color: var(--primary);
  flex-shrink: 0;
}}
.csa-arch-step .title {{
  font-weight: 700;
  color: var(--text);
  margin-bottom: 2px;
}}
.csa-arch-step .desc {{
  color: var(--text-dim);
  font-size: 13.5px;
  line-height: 1.6;
}}

/* ---------- Tech tags ---------- */
.csa-tech-tags {{
  display: flex; flex-wrap: wrap; gap: 8px;
  margin-top: 16px;
}}
.csa-tech-tag {{
  padding: 5px 12px;
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--glass-border);
  border-radius: 8px;
  font-size: 12.5px;
  color: var(--text-dim);
}}
.csa-tech-tag.accent {{
  border-color: var(--accent);
  color: var(--accent);
}}

/* ---------- Card (input form wrapper) ---------- */
.csa-card {{
  background: var(--card-bg);
  border: 1px solid var(--glass-border);
  border-radius: 18px;
  padding: 22px 24px;
  margin-bottom: 18px;
  backdrop-filter: blur(10px);
}}
.csa-card-title {{
  display: flex; align-items: center; gap: 10px;
  font-size: 15px; font-weight: 700; color: var(--text);
  margin-bottom: 14px;
}}
.csa-card-title .num {{
  width: 26px; height: 26px; border-radius: 8px;
  background: rgba(0,242,254,0.1); color: var(--primary);
  display: inline-flex; align-items: center; justify-content: center;
  font-weight: 800; font-size: 13px;
  border: 1px solid rgba(0,242,254,0.3);
}}

/* ---------- Footer note ---------- */
.csa-footer-note {{
  margin-top: 32px;
  padding: 16px 20px;
  border-radius: 14px;
  border: 1px dashed var(--glass-border);
  color: var(--text-dim);
  font-size: 13px;
  line-height: 1.7;
  text-align: center;
}}

/* ---------- Hide default streamlit clutter ---------- */
header[data-testid="stHeader"] {{ background: transparent !important; }}
#MainMenu, footer {{ visibility: hidden; }}

/* ---------- Responsive ---------- */
@media (max-width: 900px) {{
  .main .block-container {{ padding-left: 0.9rem; padding-right: 0.9rem; }}
  .csa-hero {{ padding: 44px 22px 40px 22px; border-radius: 20px; }}
  .csa-hero h1 {{ font-size: 34px; }}
  .csa-hero p.lead {{ font-size: 15px; }}
  .csa-kpi-grid, .csa-feature-grid {{ grid-template-columns: 1fr; gap: 14px; }}
  .csa-kpi-card .value {{ font-size: 28px; }}
  .csa-section-title h2 {{ font-size: 24px; }}
  .csa-card {{ padding: 18px 18px; }}
}}
@media (max-width: 520px) {{
  .csa-hero h1 {{ font-size: 28px; }}
  .csa-chip {{ font-size: 12px; padding: 6px 10px; }}
  .csa-feature-card {{ flex-direction: column; }}
  [data-testid="stMetric"] {{ padding: 14px 16px; }}
}}
</style>
"""


def inject_global_css() -> None:
    """페이지 진입 시 한 번 호출 — 전역 CSS 주입."""
    st.markdown(_CSS, unsafe_allow_html=True)


def render_sidebar_brand() -> None:
    """사이드바 상단 브랜드 영역."""
    st.markdown(
        f"""
        <div style="padding: 6px 4px 14px 4px; border-bottom: 1px solid {GLASS_BORDER}; margin-bottom: 14px;">
          <div style="display:flex; align-items:center; gap:10px;">
            <div style="width:36px;height:36px;border-radius:10px;
                        background:linear-gradient(135deg,{COLOR_SECONDARY} 0%, {COLOR_PRIMARY} 100%);
                        display:flex;align-items:center;justify-content:center;
                        font-family:'Outfit',sans-serif;font-weight:800;color:#00141a;">cs</div>
            <div>
              <div style="font-family:'Outfit',sans-serif;font-weight:800;font-size:17px;letter-spacing:-0.02em;color:{COLOR_TEXT};">{BRAND_NAME}</div>
              <div style="font-size:10.5px;color:{COLOR_MUTED};letter-spacing:0.12em;text-transform:uppercase;">
                EV · Ops Copilot
              </div>
            </div>
          </div>
          <div style="font-size:12px;color:{COLOR_MUTED};margin-top:12px;line-height:1.6;">
            {BRAND_SUB}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
