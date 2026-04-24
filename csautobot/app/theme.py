"""csautobot 공통 UI 테마.

ocppautomation 의 디자인 시스템(Tailwind v4 기반)을 Streamlit 위에 적용한다.
- 딥 블루 배경 (#0a0e1a) + 블루/그린 그라디언트 액센트
- 모던 Grid 배경 패턴
- 글래스모피즘 카드 (반투명 네이비 + blur + 얇은 보더)
- Inter (본문) / Outfit (헤딩) 폰트

모든 페이지는 진입 시 :func:`inject_global_css` 를 호출한다.
"""
from __future__ import annotations

import streamlit as st

BRAND_NAME = "csautobot"
BRAND_TAGLINE = "EV Infrastructure Technical Copilot"
BRAND_SUB = "전기차 충전소 AI 점검·AS 코파일럿"

# --- 디자인 토큰 (ocppautomation Tailwind 기준) ---
COLOR_PRIMARY = "#3478ff"    # 블루 (Brand-500)
COLOR_SECONDARY = "#1442e1"  # 다크 블루 (Brand-700)
COLOR_ACCENT = "#4ade80"     # 그린 (Accent-400)
COLOR_BG = "#0a0e1a"         # Base Background
COLOR_BG_SOFT = "#111827"    # Dark Soft
COLOR_TEXT = "#f1f5f9"       # Text Main
COLOR_MUTED = "#94a3b8"      # Text Muted
COLOR_MUTED_SOFT = "#64748b" # Text Muted Soft
COLOR_SUCCESS = "#22c55e"
COLOR_WARN = "#f97316"
COLOR_DANGER = "#ef4444"
GLASS_BG = "rgba(30, 41, 59, 0.6)"
GLASS_BORDER = "#1e293b"
GLASS_BORDER_STRONG = "#334155"

_CSS = f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=Outfit:wght@400;600;700;800&display=swap');
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
  --glass-border-strong: {GLASS_BORDER_STRONG};
  --success: {COLOR_SUCCESS};
  --warn: {COLOR_WARN};
  --danger: {COLOR_DANGER};
}}

/* 전체 배경 + 기본 타이포 */
html, body, [class*="stApp"] {{
  background: var(--bg) !important;
  background-image: 
    linear-gradient(rgba(52, 120, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(52, 120, 255, 0.03) 1px, transparent 1px) !important;
  background-size: 60px 60px !important;
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
  background: #060913 !important;
  border-right: 1px solid var(--glass-border);
}}
section[data-testid="stSidebar"] * {{ color: var(--text) !important; }}

/* ---------- 버튼 ---------- */
.stButton button, .stDownloadButton button, .stFormSubmitButton button {{
  background: rgba(255,255,255,0.06) !important;
  color: var(--text) !important;
  border: 1px solid rgba(255,255,255,0.18) !important;
  border-radius: 10px !important;
  font-weight: 600 !important;
  transition: all 0.3s ease;
}}
.stButton button p, .stDownloadButton button p, .stFormSubmitButton button p {{
  color: inherit !important;
  margin: 0 !important;
}}
.stButton button:hover, .stDownloadButton button:hover, .stFormSubmitButton button:hover {{
  border-color: var(--primary) !important;
  color: var(--primary) !important;
  background: rgba(52, 120, 255, 0.08) !important;
  box-shadow: 0 0 15px rgba(52, 120, 255, 0.2);
}}

/* Primary: Glow Button 느낌 */
.stButton button[kind="primary"], button[data-testid="baseButton-primary"],
.stFormSubmitButton button[kind="primary"] {{
  background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%) !important;
  color: #ffffff !important;
  border: none !important;
  font-weight: 600 !important;
  box-shadow: 0 4px 12px rgba(52, 120, 255, 0.3);
}}
.stButton button[kind="primary"] *,
.stFormSubmitButton button[kind="primary"] *,
button[data-testid="baseButton-primary"] * {{
  color: #ffffff !important;
}}
.stButton button[kind="primary"]:hover,
.stFormSubmitButton button[kind="primary"]:hover {{
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgba(52, 120, 255, 0.4);
  filter: brightness(1.1);
}}

/* ---------- 입력 위젯 라벨 ---------- */
.stTextInput label, .stTextArea label, .stSelectbox label, .stNumberInput label,
.stDateInput label, .stFileUploader label, .stSlider label, .stRadio label,
.stCheckbox label, .stMultiSelect label, .stTimeInput label, .stColorPicker label {{
  color: var(--text) !important;
  font-weight: 600 !important;
  font-size: 13.5px !important;
  opacity: 1 !important;
}}

/* ---------- 입력 위젯 박스 ---------- */
/* 최상단 wrapper 및 base-input 의 기본 테두리 제거 */
.stTextInput [data-baseweb="base-input"],
.stTextArea [data-baseweb="base-input"],
.stSelectbox [data-baseweb="select"],
.stNumberInput [data-baseweb="base-input"],
.stDateInput [data-baseweb="base-input"],
.stMultiSelect [data-baseweb="select"] {{
  background-color: transparent !important;
  border: none !important;
  box-shadow: none !important;
}}

/* 실제 입력창(input/textarea)에만 흰색 배경과 단일 테두리 적용 */
.stTextInput input, .stTextArea textarea, .stNumberInput input, .stDateInput input,
.stMultiSelect input, .stSelectbox div[role="combobox"] {{
  background-color: #ffffff !important;
  border: 1px solid #cbd5e1 !important;
  border-radius: 8px !important;
  color: #0f172a !important;
  caret-color: var(--primary);
  font-weight: 500 !important;
  box-shadow: none !important;
  padding: 8px 12px !important;
}}
.stFileUploader [data-testid="stFileUploadDropzone"] {{
  background-color: #ffffff !important;
  border: 1px solid #cbd5e1 !important;
  border-radius: 8px !important;
  color: #0f172a !important;
}}

.stTextInput input::placeholder,
.stTextArea textarea::placeholder,
.stNumberInput input::placeholder,
.stDateInput input::placeholder {{
  color: #94a3b8 !important;
  opacity: 1 !important;
}}

/* 포커스 강조 */
.stTextInput input:focus,
.stTextArea textarea:focus,
.stNumberInput input:focus,
.stDateInput input:focus,
.stMultiSelect input:focus,
.stSelectbox div[role="combobox"]:focus-within {{
  border-color: var(--primary) !important;
  box-shadow: 0 0 0 2px rgba(52, 120, 255, 0.25) !important;
  outline: none !important;
}}

/* NumberInput ± 증감 버튼 */
.stNumberInput button {{
  background: #f1f5f9 !important;
  color: #0f172a !important;
  border-color: #e2e8f0 !important;
}}
.stNumberInput button:hover {{
  background: rgba(52, 120, 255, 0.1) !important;
  color: var(--primary) !important;
}}

/* ---------- Slider ---------- */
.stSlider [data-baseweb="slider"] > div:nth-child(2),
.stSlider [data-baseweb="slider"] > div:nth-child(3) {{
  background: linear-gradient(90deg, var(--secondary), var(--primary)) !important;
}}
.stSlider [role="slider"] {{
  background: #ffffff !important;
  border: 3px solid var(--primary) !important;
  box-shadow: 0 4px 12px rgba(52, 120, 255, 0.35) !important;
}}
.stSlider [data-baseweb="slider"] + div,
.stSlider [data-testid="stTickBar"] {{
  color: var(--text-dim) !important;
}}
.stSlider [data-testid="stThumbValue"] {{
  color: var(--text) !important;
  font-weight: 700 !important;
  background: rgba(52, 120, 255, 0.15) !important;
  padding: 2px 8px !important;
  border-radius: 8px !important;
}}

/* ---------- Horizontal Radio (Tab Navigation) ---------- */
div[data-testid="stRadio"] > div[role="radiogroup"][aria-orientation="horizontal"] {{
  display: flex;
  gap: 12px;
  background: var(--card-bg);
  padding: 6px;
  border-radius: 12px;
  border: 1px solid var(--glass-border);
  width: fit-content;
}}
div[data-testid="stRadio"] > div[role="radiogroup"][aria-orientation="horizontal"] label[data-baseweb="radio"] {{
  background: transparent;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  margin: 0;
  transition: all 0.2s ease;
}}
div[data-testid="stRadio"] > div[role="radiogroup"][aria-orientation="horizontal"] label[data-baseweb="radio"] div:first-child {{
  display: none; /* Hide the actual radio circle */
}}
div[data-testid="stRadio"] > div[role="radiogroup"][aria-orientation="horizontal"] label[data-baseweb="radio"] div:last-child {{
  font-weight: 600;
  color: var(--text-dim);
  font-size: 14.5px;
}}
div[data-testid="stRadio"] > div[role="radiogroup"][aria-orientation="horizontal"] label[data-baseweb="radio"]:hover {{
  background: rgba(255,255,255,0.06);
}}
div[data-testid="stRadio"] > div[role="radiogroup"][aria-orientation="horizontal"] label[data-baseweb="radio"]:has(input:checked) {{
  background: rgba(52, 120, 255, 0.15);
  border: 1px solid rgba(52, 120, 255, 0.3);
  box-shadow: 0 4px 10px rgba(52, 120, 255, 0.15);
}}
div[data-testid="stRadio"] > div[role="radiogroup"][aria-orientation="horizontal"] label[data-baseweb="radio"]:has(input:checked) div:last-child {{
  color: var(--primary) !important;
}}

/* ---------- 메트릭 카드 (KPI 느낌) ---------- */
[data-testid="stMetric"] {{
  background: var(--card-bg);
  border: 1px solid var(--glass-border);
  border-radius: 16px;
  padding: 18px 20px;
  backdrop-filter: blur(16px);
  transition: all 0.3s ease;
}}
[data-testid="stMetric"]:hover {{
  transform: translateY(-3px);
  border-color: var(--glass-border-strong);
  box-shadow: 0 8px 20px rgba(52, 120, 255, 0.15);
}}
[data-testid="stMetricLabel"] {{
  color: var(--text-dim) !important;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 12px !important;
}}
[data-testid="stMetricValue"] {{
  color: var(--text) !important;
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
  backdrop-filter: blur(16px);
}}
[data-testid="stExpander"] {{ border: none; }}

/* ---------- Alerts ---------- */
.stAlert {{
  border-radius: 12px !important;
  border: 1px solid var(--glass-border) !important;
  background: rgba(30, 41, 59, 0.4) !important;
}}
.stAlert [data-testid="stMarkdownContainer"],
.stAlert [data-testid="stMarkdownContainer"] p,
.stAlert [data-testid="stMarkdownContainer"] div,
.stAlert [data-testid="stMarkdownContainer"] span {{
  color: var(--text) !important;
}}
.stAlert [data-testid="stMarkdownContainer"] strong {{
  color: #ffffff !important;
}}

/* ---------- DataFrame ---------- */
[data-testid="stDataFrame"] {{
  border: 1px solid var(--glass-border);
  border-radius: 14px;
  overflow: hidden;
}}

/* ---------- Code & Text Blocks ---------- */
code {{
  background-color: rgba(255, 255, 255, 0.08) !important;
  color: var(--accent) !important; /* 초록색 액센트로 가독성 확보 */
  padding: 3px 6px !important;
  border-radius: 6px !important;
  font-family: "JetBrains Mono", Consolas, monospace !important;
  font-size: 0.9em !important;
  word-break: break-all !important;
}}
[data-testid="stText"], pre, pre code {{
  color: var(--text-dim) !important;
  background-color: transparent !important;
  font-family: "Inter", "Pretendard", sans-serif !important;
  white-space: pre-wrap !important;
  line-height: 1.6 !important;
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
  background: var(--card-bg);
  border: 1px solid var(--glass-border);
  backdrop-filter: blur(16px);
  overflow: hidden;
  margin-bottom: 28px;
  text-align: center;
}}
.csa-hero .badge {{
  position: relative; z-index: 1;
  display: inline-block;
  padding: 0.45rem 1.2rem;
  background: rgba(52, 120, 255, 0.1);
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
  background: linear-gradient(135deg, #8ec1ff, #3478ff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  color: transparent;
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
  box-shadow: 0 0 8px 2px rgba(52, 120, 255, 0.6);
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
  backdrop-filter: blur(16px);
  transition: all 0.3s ease;
}}
.csa-kpi-card:hover {{
  transform: translateY(-4px);
  border-color: var(--glass-border-strong);
  box-shadow: 0 8px 20px rgba(52, 120, 255, 0.15);
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
  color: var(--text);
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
  backdrop-filter: blur(16px);
  transition: all 0.3s ease;
  display: flex; gap: 16px; align-items: flex-start;
}}
.csa-feature-card:hover {{
  transform: translateY(-3px);
  border-color: var(--glass-border-strong);
  box-shadow: 0 8px 20px rgba(52, 120, 255, 0.15);
}}
.csa-feature-card .icon {{
  width: 48px; height: 48px; flex-shrink: 0;
  border-radius: 14px;
  background: linear-gradient(135deg, var(--secondary), var(--primary));
  display: inline-flex; align-items: center; justify-content: center;
  color: #ffffff;
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
  background: var(--card-bg);
  border: 1px solid var(--glass-border);
  padding: 28px;
  border-radius: 22px;
  backdrop-filter: blur(16px);
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
  background: rgba(52, 120, 255, 0.1);
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
  backdrop-filter: blur(16px);
}}
.csa-card-title {{
  display: flex; align-items: center; gap: 10px;
  font-size: 15px; font-weight: 700; color: var(--text);
  margin-bottom: 14px;
}}
.csa-card-title .num {{
  width: 26px; height: 26px; border-radius: 8px;
  background: rgba(52, 120, 255, 0.1); color: var(--primary);
  display: inline-flex; align-items: center; justify-content: center;
  font-weight: 800; font-size: 13px;
  border: 1px solid rgba(52, 120, 255, 0.3);
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
    """페이지 진입 시 한 번 호출 — 전역 CSS 주입.

    Streamlit 의 markdown renderer 가 `<style>` 내부 CSS 셀렉터를
    텍스트 노드로 추가 렌더링하는 이슈가 있어 가능하면 `st.html` 로 주입한다.
    `st.html` 이 없는 구 버전이면 markdown fallback 을 사용하되,
    `<style>` 태그 앞뒤로 공백이 전혀 없어야 한다.
    """
    if hasattr(st, "html"):
        st.html(_CSS)
    else:
        st.markdown(_CSS, unsafe_allow_html=True)


def render_sidebar_brand() -> None:
    """사이드바 상단 브랜드 영역."""
    st.markdown(
        f"""
        <div style="padding: 6px 4px 14px 4px; border-bottom: 1px solid {GLASS_BORDER}; margin-bottom: 14px;">
          <a href="/?page=home" target="_self" style="text-decoration: none;">
            <div style="display:flex; align-items:center; gap:10px; cursor:pointer;">
              <div style="width:36px;height:36px;border-radius:10px;
                          background:linear-gradient(135deg,{COLOR_PRIMARY} 0%, {COLOR_SECONDARY} 100%);
                          display:flex;align-items:center;justify-content:center;
                          font-family:'Outfit',sans-serif;font-weight:800;color:#ffffff;
                          box-shadow: 0 4px 10px rgba(52,120,255,0.3);">cs</div>
              <div>
                <div style="font-family:'Outfit',sans-serif;font-weight:800;font-size:17px;letter-spacing:-0.02em;color:{COLOR_TEXT};">{BRAND_NAME}</div>
                <div style="font-size:10.5px;color:{COLOR_MUTED};letter-spacing:0.12em;text-transform:uppercase;">
                  EV · Ops Copilot
                </div>
              </div>
            </div>
          </a>
          <div style="font-size:12px;color:{COLOR_MUTED};margin-top:12px;line-height:1.6;">
            {BRAND_SUB}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
