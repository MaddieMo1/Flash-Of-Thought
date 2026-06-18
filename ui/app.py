import streamlit as st
import requests
import json
import os
import time
import hashlib
import html
from datetime import datetime, timedelta, timezone
import plotly.graph_objects as go
import networkx as nx
import pandas as pd
import numpy as np
from pathlib import Path
import streamlit.components.v1 as components
from streamlit_echarts import st_echarts
from utils import save_analysis_result, parse_list_from_doc
# from streamlit_agraph import agraph, Node, Edge, Config # Replaced with PyDeck for 3D

try:
    from streamlit_autorefresh import st_autorefresh
except Exception:
    st_autorefresh = None

# Backend API URL
def normalize_api_base_url(raw_url):
    base_url = raw_url.rstrip("/")
    if not base_url.endswith("/api/v1"):
        base_url = f"{base_url}/api/v1"
    return base_url


BEIJING_TIMEZONE = timezone(timedelta(hours=8))


def format_beijing_time(value):
    if not value:
        return ""
    try:
        text = str(value).strip()
        if text.isdigit():
            parsed = datetime.fromtimestamp(int(text), tz=timezone.utc)
        else:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(BEIJING_TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")
    except (OSError, OverflowError, TypeError, ValueError):
        return str(value)


API_BASE_URL = normalize_api_base_url(os.getenv("API_BASE_URL", "http://localhost:8000/api/v1"))
API_SESSION = requests.Session()
API_SESSION.trust_env = False
APP_ICON_PATH = Path(__file__).resolve().parents[1] / "Icon" / "1460.png"
AUTH_COOKIE_NAME = "flash_of_thought_token"
AUTH_QUERY_PARAM = "auth_token"

def mask_email(email):
    if not email or "@" not in email:
        return email or ""
    name, domain = email.split("@", 1)
    if len(name) <= 6:
        return email
    return f"{name[:3]}...{name[-3:]}@{domain}"

def api_request(method, path, **kwargs):
    kwargs.setdefault("timeout", 60)
    headers = kwargs.pop("headers", {}) or {}
    access_token = st.session_state.get("access_token")
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    if headers:
        kwargs["headers"] = headers
    return API_SESSION.request(method, f"{API_BASE_URL}{path}", **kwargs)


@st.cache_data(ttl=300, show_spinner=False)
def fetch_graph_data_cached(access_token):
    headers = {}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    res = API_SESSION.request("GET", f"{API_BASE_URL}/graph", headers=headers, timeout=60)
    if res.status_code != 200:
        raise RuntimeError(auth_error_message(res))
    res.encoding = 'utf-8'
    return res.json()


def run_auth_cookie_script(token=None, clear=False, reload_page=False):
    if clear:
        cookie_script = (
            f"document.cookie = '{AUTH_COOKIE_NAME}=; path=/; max-age=0; SameSite=Lax';"
            f"try {{ window.parent.document.cookie = '{AUTH_COOKIE_NAME}=; path=/; max-age=0; SameSite=Lax'; }} catch (e) {{}}"
        )
    else:
        token_text = json.dumps(token or "")
        cookie_script = (
            f"const token = {token_text};"
            f"document.cookie = '{AUTH_COOKIE_NAME}=' + encodeURIComponent(token) + '; path=/; max-age=604800; SameSite=Lax';"
            f"try {{ window.parent.document.cookie = '{AUTH_COOKIE_NAME}=' + encodeURIComponent(token) + '; path=/; max-age=604800; SameSite=Lax'; }} catch (e) {{}}"
        )
    reload_script = "window.parent.location.reload();" if reload_page else ""
    components.html(f"<script>{cookie_script}{reload_script}</script>", height=0)

st.set_page_config(
    page_title="FlashOfThought",
    page_icon=str(APP_ICON_PATH),
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1180px;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    h1 {
        background: linear-gradient(90deg, #00D4FF 0%, #7B61FF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        letter-spacing: -0.03em;
        margin-bottom: 1.5rem;
    }

    h2 {
        color: #FFFFFF !important;
        font-weight: 700;
        letter-spacing: -0.02em;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }

    h3 {
        color: #E2E8F0 !important;
        font-weight: 600;
    }

    .stMarkdown p {
        color: #A0AEC0;
        font-size: 1rem;
        line-height: 1.6;
    }

    .stButton>button {
        border-radius: 12px;
        font-weight: 600;
        border: 1px solid rgba(255, 255, 255, 0.1);
        background-color: rgba(255, 255, 255, 0.05);
        color: #E2E8F0;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover {
        border-color: rgba(0, 212, 255, 0.4);
        background-color: rgba(0, 212, 255, 0.1);
        color: #00D4FF;
        transform: translateY(-1px);
    }

    div[data-testid="stButton"] button[kind="primary"] {
        background: linear-gradient(135deg, #00D4FF 0%, #0096FF 100%) !important;
        color: #FFFFFF !important;
        border: none;
        box-shadow: 0 4px 14px rgba(0, 212, 255, 0.3);
    }
    div[data-testid="stButton"] button[kind="primary"]:hover {
        background: linear-gradient(135deg, #2EE0FF 0%, #00A6FF 100%) !important;
        box-shadow: 0 6px 20px rgba(0, 212, 255, 0.4);
        transform: translateY(-2px);
    }

    .stExpander {
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        background: linear-gradient(145deg, rgba(30, 33, 43, 0.9) 0%, rgba(20, 22, 28, 0.9) 100%);
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: border-color 0.2s ease;
    }
    .stExpander:hover {
        border-color: rgba(255, 255, 255, 0.15);
    }

    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        border-radius: 12px;
        background-color: rgba(14, 17, 23, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.12);
        color: #FFFFFF;
        font-size: 1rem;
        padding: 0.75rem 1rem;
        transition: all 0.2s ease;
    }
    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
        border-color: #00D4FF;
        box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.2);
        background-color: rgba(14, 17, 23, 0.9);
    }
    div[data-testid="InputInstructions"] {
        display: none;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }
    .stTabs [data-baseweb="tab"] {
        padding-top: 1rem;
        padding-bottom: 1rem;
        color: #A0AEC0;
    }
    .stTabs [aria-selected="true"] {
        color: #00D4FF !important;
        font-weight: 600;
    }

    div[data-testid="stAlertContainer"] {
        border-radius: 14px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        background: rgba(30, 33, 43, 0.8);
        backdrop-filter: blur(10px);
    }
    div[data-testid="stAlertContainer"] [data-testid="stAlertContentError"] {
        color: #FFD1D1;
    }

    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.2);
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.3);
    }

    code {
        color: #E2E8F0 !important;
        background-color: rgba(255, 255, 255, 0.08) !important;
        border-radius: 6px;
        font-family: 'JetBrains Mono', 'Fira Code', monospace;
        border: 1px solid rgba(255, 255, 255, 0.05);
        padding: 0.2em 0.4em;
    }

    .stToast {
        background: rgba(30, 33, 43, 0.95) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        color: #FFFFFF !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    }

    hr {
        border-color: rgba(255, 255, 255, 0.08) !important;
        margin: 2rem 0;
    }

    [data-testid="stSidebar"] {
        background-color: #0B0E14;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: #E2E8F0;
    }

    [data-testid="stMetricValue"] {
        color: #00D4FF;
        font-weight: 700;
    }

    .page-head {
        margin: 0 0 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }
    .page-kicker {
        color: #00D4FF;
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 0.45rem;
    }
    .page-title {
        color: #F8FAFC;
        font-size: clamp(1.85rem, 3vw, 2.8rem);
        font-weight: 850;
        line-height: 1.05;
        letter-spacing: 0;
        margin-bottom: 0.45rem;
    }
    .page-copy {
        color: #94A3B8;
        max-width: 46rem;
        font-size: 0.98rem;
        line-height: 1.65;
    }
    .work-surface {
        padding: 1.1rem 1.15rem;
        border-radius: 14px;
        background: rgba(18, 22, 30, 0.72);
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    .section-label {
        color: #F8FAFC;
        font-size: 1rem;
        font-weight: 800;
        margin: 0 0 0.2rem;
    }
    .section-copy {
        color: #94A3B8;
        font-size: 0.88rem;
        line-height: 1.55;
        margin-bottom: 0.75rem;
    }
    .capture-strip {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.8rem;
        margin-bottom: 1rem;
    }
    .capture-stat {
        padding: 0.85rem;
        border-radius: 12px;
        background: rgba(0, 212, 255, 0.06);
        border: 1px solid rgba(0, 212, 255, 0.14);
    }
    .capture-stat strong {
        display: block;
        color: #F8FAFC;
        font-size: 0.95rem;
        margin-bottom: 0.2rem;
    }
    .capture-stat span {
        color: #8EA4B8;
        font-size: 0.82rem;
    }
    .note-count {
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.55rem;
        border-radius: 999px;
        color: #CFFAFE;
        background: rgba(0, 212, 255, 0.09);
        border: 1px solid rgba(0, 212, 255, 0.18);
        font-size: 0.78rem;
        font-weight: 800;
    }
    .graph-toolbar {
        margin: 0.75rem 0 1rem;
    }

    .auth-kicker {
        color: #00D4FF;
        font-size: 0.82rem;
        font-weight: 800;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 1rem;
    }
    .auth-title {
        color: #F8FAFC;
        font-size: clamp(2.5rem, 6vw, 4.5rem);
        font-weight: 850;
        line-height: 0.96;
        letter-spacing: 0;
        margin: 0 0 1.15rem;
    }
    .auth-title span {
        color: #00D4FF;
    }
    .auth-subtitle {
        max-width: 34rem;
        color: #94A3B8;
        font-size: 1.02rem;
        line-height: 1.7;
        margin-bottom: 2rem;
    }
    .auth-feature-list {
        display: grid;
        gap: 0.85rem;
        margin-top: 1.5rem;
    }
    .auth-feature {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        color: #CBD5E1;
        font-size: 0.95rem;
    }
    .auth-feature-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 2rem;
        height: 2rem;
        border-radius: 10px;
        background: rgba(0, 212, 255, 0.1);
        border: 1px solid rgba(0, 212, 255, 0.2);
        color: #67E8F9;
        font-weight: 800;
    }
    .auth-panel-title {
        color: #F8FAFC;
        font-size: 1.4rem;
        font-weight: 800;
        margin: 0.1rem 0 0.25rem;
    }
    .auth-panel-copy {
        color: #94A3B8;
        font-size: 0.92rem;
        margin-bottom: 0.85rem;
    }
    .auth-footnote {
        margin-top: 0.85rem;
        color: #64748B;
        font-size: 0.82rem;
        text-align: center;
    }

    [data-testid="stSidebar"] .block-container {
        padding-top: 1.35rem;
        padding-bottom: 1.25rem;
    }
    .sidebar-brand {
        margin-top: 0.35rem;
        margin-bottom: 0.15rem;
        font-size: 1.05rem;
        font-weight: 800;
        color: #F8FAFC;
        letter-spacing: 0;
    }
    .sidebar-account {
        margin: 0.15rem 0 1rem;
        color: #718096;
        font-size: 0.84rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .sidebar-section-title {
        margin: 1.35rem 0 0.65rem;
        color: #F8FAFC;
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }
    [data-testid="stSidebar"] hr {
        margin: 1.25rem 0;
        border-color: rgba(255, 255, 255, 0.08) !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] {
        gap: 0.35rem;
    }
    [data-testid="stSidebar"] div[data-testid="stRadio"] > div,
    [data-testid="stSidebar"] div[role="radiogroup"] {
        width: 100%;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] label {
        width: 100%;
        min-height: 2.45rem;
        padding: 0.45rem 0.7rem;
        border-radius: 10px;
        border: 1px solid transparent;
        background: transparent;
        transition: background 0.16s ease, border-color 0.16s ease, color 0.16s ease;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background: rgba(255, 255, 255, 0.05);
        border-color: rgba(255, 255, 255, 0.08);
    }
    [data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
        background: linear-gradient(90deg, rgba(0, 212, 255, 0.18), rgba(123, 97, 255, 0.08));
        border-color: rgba(0, 212, 255, 0.28);
        box-shadow: inset 3px 0 0 #00D4FF;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child {
        display: none;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] label p {
        color: #CBD5E1 !important;
        font-weight: 650;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p {
        color: #FFFFFF !important;
    }
    .sidebar-footer {
        margin-top: 1.3rem;
        color: #64748B;
        font-size: 0.78rem;
    }
    .quota-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        margin: 0.25rem 0 0.15rem;
        padding: 0.35rem 0.55rem;
        border-radius: 999px;
        color: #CFFAFE;
        background: rgba(0, 212, 255, 0.1);
        border: 1px solid rgba(0, 212, 255, 0.18);
        font-size: 0.78rem;
        font-weight: 700;
    }
    .plan-card {
        min-height: 13.25rem;
        padding: 1.05rem;
        border-radius: 14px;
        background: linear-gradient(145deg, rgba(30, 33, 43, 0.95), rgba(14, 17, 23, 0.9));
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    .plan-name {
        color: #F8FAFC;
        font-size: 1rem;
        font-weight: 800;
        margin-bottom: 0.35rem;
    }
    .plan-price {
        color: #00D4FF;
        font-size: 1.45rem;
        font-weight: 850;
        margin: 0.35rem 0;
    }
    .plan-desc {
        min-height: 2.6rem;
        color: #94A3B8;
        font-size: 0.86rem;
        line-height: 1.5;
    }
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.8rem;
        margin: 0.9rem 0 1.2rem;
    }
    .metric-card {
        min-height: 5.2rem;
        padding: 0.9rem 1rem;
        border-radius: 12px;
        background: linear-gradient(145deg, rgba(15, 23, 42, 0.82), rgba(18, 22, 30, 0.72));
        border: 1px solid rgba(148, 163, 184, 0.14);
    }
    .metric-card.primary {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.16), rgba(20, 184, 166, 0.08));
        border-color: rgba(0, 212, 255, 0.28);
    }
    .metric-card span {
        display: block;
        color: #94A3B8;
        font-size: 0.78rem;
        font-weight: 750;
        margin-bottom: 0.35rem;
    }
    .metric-card strong {
        color: #F8FAFC;
        font-size: 1.35rem;
        font-weight: 850;
    }
    .metric-card small {
        display: block;
        color: #64748B;
        margin-top: 0.35rem;
        font-size: 0.76rem;
        line-height: 1.4;
    }
    .tool-card {
        min-height: 7.4rem;
        padding: 1rem;
        border-radius: 12px;
        background: rgba(15, 23, 42, 0.58);
        border: 1px solid rgba(148, 163, 184, 0.14);
    }
    .tool-card strong {
        display: block;
        color: #F8FAFC;
        font-size: 1rem;
        margin-bottom: 0.35rem;
    }
    .tool-card span {
        color: #94A3B8;
        font-size: 0.86rem;
        line-height: 1.55;
    }
    .empty-panel {
        padding: 1rem;
        border-radius: 12px;
        color: #94A3B8;
        background: rgba(15, 23, 42, 0.56);
        border: 1px dashed rgba(148, 163, 184, 0.24);
    }
    .note-list-row {
        padding: 0.85rem 0.95rem;
        border-radius: 12px;
        background: rgba(15, 23, 42, 0.58);
        border: 1px solid rgba(148, 163, 184, 0.14);
        margin-bottom: 0.55rem;
    }
    .note-list-row.active {
        border-color: rgba(0, 212, 255, 0.45);
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.13), rgba(15, 23, 42, 0.62));
    }
    .note-row-top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.7rem;
        margin-bottom: 0.3rem;
    }
    .note-row-title {
        color: #F8FAFC;
        font-weight: 850;
        line-height: 1.35;
    }
    .note-row-time {
        color: #64748B;
        font-size: 0.78rem;
        white-space: nowrap;
    }
    .note-row-summary {
        color: #94A3B8;
        font-size: 0.86rem;
        line-height: 1.55;
        margin-bottom: 0.5rem;
    }
    .note-row-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 0.4rem;
        align-items: center;
    }
    .note-chip {
        display: inline-flex;
        align-items: center;
        padding: 0.18rem 0.45rem;
        border-radius: 999px;
        color: #BAE6FD;
        background: rgba(14, 165, 233, 0.11);
        border: 1px solid rgba(14, 165, 233, 0.18);
        font-size: 0.74rem;
        font-weight: 700;
    }
    .analysis-chip {
        color: #C4B5FD;
        background: rgba(124, 58, 237, 0.13);
        border-color: rgba(124, 58, 237, 0.22);
    }
    .transaction-row {
        display: grid;
        grid-template-columns: 7rem 1fr 7rem 10rem;
        gap: 0.8rem;
        align-items: center;
        padding: 0.75rem 0.85rem;
        border-radius: 10px;
        background: rgba(15, 23, 42, 0.48);
        border: 1px solid rgba(148, 163, 184, 0.12);
        margin-bottom: 0.45rem;
    }
    .transaction-amount {
        font-weight: 850;
    }
    .transaction-amount.positive {
        color: #86EFAC;
    }
    .transaction-amount.negative {
        color: #FDA4AF;
    }
    .transaction-meta {
        color: #94A3B8;
        font-size: 0.82rem;
    }
    div[data-testid="stFileUploader"] section {
        border-radius: 14px;
        border: 1px dashed rgba(0, 212, 255, 0.28);
        background: rgba(0, 212, 255, 0.05);
    }
    div[data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid rgba(148, 163, 184, 0.12);
    }
    .admin-status-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.8rem;
        margin: 0.85rem 0 1.15rem;
    }
    .admin-status {
        min-height: 5.4rem;
        padding: 0.85rem 0.95rem;
        border-radius: 12px;
        background: rgba(15, 23, 42, 0.78);
        border: 1px solid rgba(148, 163, 184, 0.16);
    }
    .admin-status span {
        display: block;
        color: #94A3B8;
        font-size: 0.78rem;
        font-weight: 700;
        margin-bottom: 0.4rem;
    }
    .admin-status strong {
        color: #F8FAFC;
        font-size: 1.28rem;
        font-weight: 850;
    }
    .admin-status.accent {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.14), rgba(20, 184, 166, 0.08));
        border-color: rgba(0, 212, 255, 0.28);
    }
    .admin-panel {
        margin: 1rem 0;
        padding: 1rem;
        border-radius: 12px;
        background: rgba(15, 23, 42, 0.55);
        border: 1px solid rgba(148, 163, 184, 0.14);
    }
    .admin-panel-title {
        color: #F8FAFC;
        font-size: 1rem;
        font-weight: 850;
        margin-bottom: 0.2rem;
    }
    .admin-panel-copy {
        color: #94A3B8;
        font-size: 0.86rem;
        line-height: 1.55;
    }
    .admin-user-chip {
        display: inline-flex;
        align-items: center;
        max-width: 100%;
        margin: 0.25rem 0 0.8rem;
        padding: 0.45rem 0.7rem;
        border-radius: 999px;
        color: #CFFAFE;
        background: rgba(0, 212, 255, 0.09);
        border: 1px solid rgba(0, 212, 255, 0.22);
        font-size: 0.84rem;
        font-weight: 750;
    }
    .danger-panel {
        margin-top: 0.75rem;
        padding: 1rem;
        border-radius: 12px;
        background: rgba(127, 29, 29, 0.24);
        border: 1px solid rgba(248, 113, 113, 0.35);
    }
    .danger-panel strong {
        color: #FEE2E2;
    }
    .graph-legend {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.75rem;
        margin: 0.4rem 0 1rem;
    }
    .graph-legend-item {
        display: flex;
        gap: 0.55rem;
        align-items: flex-start;
        padding: 0.75rem 0.85rem;
        border-radius: 10px;
        background: rgba(15, 23, 42, 0.55);
        border: 1px solid rgba(148, 163, 184, 0.14);
        color: #94A3B8;
        font-size: 0.84rem;
        line-height: 1.45;
    }
    .graph-dot {
        width: 0.72rem;
        height: 0.72rem;
        flex: 0 0 0.72rem;
        margin-top: 0.2rem;
        border-radius: 999px;
        box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.05);
    }
    .graph-dot.core { background: #00D4FF; }
    .graph-dot.note { background: #7C3AED; }
    .graph-dot.tag { background: #22C55E; }
    @media (max-width: 900px) {
        .admin-status-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
        .metric-grid,
        .capture-strip {
            grid-template-columns: 1fr;
        }
        .transaction-row {
            grid-template-columns: 1fr;
        }
    }
    @media (max-width: 640px) {
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
        .page-title {
            font-size: 2rem;
            line-height: 1.12;
        }
        .metric-grid,
        .admin-status-grid,
        .graph-legend {
            grid-template-columns: 1fr !important;
        }
        .metric-card,
        .tool-card,
        .admin-status,
        .plan-card {
            min-height: auto;
        }
        .transaction-row {
            gap: 0.35rem;
        }
        .note-row-top {
            align-items: flex-start;
            flex-direction: column;
            gap: 0.25rem;
        }
        .note-row-time {
            white-space: normal;
        }
    }

    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

def initialize_auth_state():
    defaults = {
        "access_token": None,
        "current_user": None,
        "auth_checked": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def auth_error_message(response):
    try:
        detail = response.json().get("detail", response.text)
        if isinstance(detail, dict):
            return str(detail.get("message", detail))
        if isinstance(detail, list):
            return "；".join([item.get("msg", str(item)) for item in detail])
        return str(detail)
    except Exception:
        return response.text


def clear_auth_state(reload_page=False):
    if AUTH_QUERY_PARAM in st.query_params:
        del st.query_params[AUTH_QUERY_PARAM]
    for key in [
        "access_token",
        "current_user",
        "auth_checked",
        "current_note",
        "current_raw_text",
        "current_file_url",
        "chat_history",
        "weekly_summary",
        "billing_account_cache",
        "billing_plans_cache",
        "billing_auto_loaded",
        "notes_list_cache",
        "notes_auto_loaded",
        "graph_data_cache",
        "graph_auto_loaded",
        "processed_audio_signatures",
    ]:
        st.session_state.pop(key, None)
    for key in list(st.session_state.keys()):
        if key.startswith(("analysis_cache_", "active_analysis_", "edit_mode_")):
            st.session_state.pop(key, None)
    st.session_state.auth_logged_out = True
    run_auth_cookie_script(clear=True, reload_page=reload_page)
    initialize_auth_state()


def restore_auth_state_from_cookie():
    if st.session_state.get("auth_logged_out"):
        return
    if st.session_state.access_token:
        return
    token = st.context.cookies.get(AUTH_COOKIE_NAME)
    if not token:
        token = st.query_params.get(AUTH_QUERY_PARAM)
    if token:
        st.session_state.access_token = token
        st.session_state.auth_checked = False


def verify_saved_session():
    if st.session_state.auth_checked or not st.session_state.access_token:
        return

    try:
        res = api_request("GET", "/auth/me", timeout=10)
        if res.status_code == 200:
            st.session_state.current_user = res.json()
        else:
            clear_auth_state()
    except Exception:
        clear_auth_state()
    finally:
        st.session_state.auth_checked = True


def render_auth_page():
    st.markdown('<div style="height: 3.5rem;"></div>', unsafe_allow_html=True)
    hero_col, form_col = st.columns([1.05, 0.95], gap="large")

    with hero_col:
        st.markdown(
            """
            <div class="auth-kicker">FlashOfThought</div>
            <div class="auth-title">把一闪而过的想法<span>接住</span></div>
            <div class="auth-subtitle">
                录音、整理、扩展、路线图和评分都会绑定到你的账号。下一次回来，灵感还在原处。
            </div>
            <div class="auth-feature-list">
                <div class="auth-feature"><span class="auth-feature-icon">1</span><span>语音和文字快速整理成结构化笔记</span></div>
                <div class="auth-feature"><span class="auth-feature-icon">2</span><span>用 AI 扩展想法、生成路线并评估可行性</span></div>
                <div class="auth-feature"><span class="auth-feature-icon">3</span><span>搜索、图谱和周报围绕你的知识库持续沉淀</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with form_col:
        with st.container(border=True):
            st.markdown('<div class="auth-panel-title">进入工作台</div>', unsafe_allow_html=True)
            st.markdown('<div class="auth-panel-copy">使用邮箱登录，或创建一个新账号。</div>', unsafe_allow_html=True)

            login_tab, register_tab = st.tabs(["登录", "注册"])

            with login_tab:
                with st.form("login_form"):
                    email = st.text_input("邮箱", key="login_email", placeholder="you@example.com")
                    password = st.text_input("密码", type="password", key="login_password")
                    submitted = st.form_submit_button("登录", type="primary", use_container_width=True)

                if submitted:
                    try:
                        res = api_request(
                            "POST",
                            "/auth/login",
                            json={"email": email, "password": password},
                            timeout=20,
                        )
                        if res.status_code == 200:
                            data = res.json()
                            st.session_state.pop("auth_logged_out", None)
                            st.session_state.access_token = data["access_token"]
                            st.session_state.current_user = data["user"]
                            st.session_state.auth_checked = True
                            st.query_params[AUTH_QUERY_PARAM] = data["access_token"]
                            st.toast("登录成功")
                            run_auth_cookie_script(data["access_token"], reload_page=True)
                            st.stop()
                        else:
                            st.error(f"登录失败：{auth_error_message(res)}")
                    except Exception as e:
                        st.error(f"无法连接后端服务：{str(e)}")

            with register_tab:
                with st.form("register_form"):
                    email = st.text_input("邮箱", key="register_email", placeholder="you@example.com")
                    password = st.text_input("密码（至少 8 位）", type="password", key="register_password")
                    confirm_password = st.text_input("确认密码", type="password", key="register_confirm_password")
                    submitted = st.form_submit_button("注册并登录", type="primary", use_container_width=True)

                if submitted:
                    if password != confirm_password:
                        st.error("两次输入的密码不一致")
                    else:
                        try:
                            res = api_request(
                                "POST",
                                "/auth/register",
                                json={"email": email, "password": password},
                                timeout=20,
                            )
                            if res.status_code == 200:
                                data = res.json()
                                st.session_state.pop("auth_logged_out", None)
                                st.session_state.access_token = data["access_token"]
                                st.session_state.current_user = data["user"]
                                st.session_state.auth_checked = True
                                st.query_params[AUTH_QUERY_PARAM] = data["access_token"]
                                st.toast("注册成功")
                                run_auth_cookie_script(data["access_token"], reload_page=True)
                                st.stop()
                            else:
                                st.error(f"注册失败：{auth_error_message(res)}")
                        except Exception as e:
                            st.error(f"无法连接后端服务：{str(e)}")

            st.markdown('<div class="auth-footnote">你的数据会绑定到当前账号，便于跨设备继续回顾。</div>', unsafe_allow_html=True)


def format_price(amount_cents, currency="CNY"):
    amount = amount_cents / 100
    if currency == "CNY":
        return f"¥{amount:.0f}"
    return f"{currency} {amount:.2f}"


def load_billing_account(use_cache=True):
    cache_key = "billing_account_cache"
    now = time.time()
    cached = st.session_state.get(cache_key)
    if use_cache and cached and now - cached.get("loaded_at", 0) < 30:
        return cached["data"]

    res = api_request("GET", "/billing/account", timeout=20)
    if res.status_code != 200:
        raise RuntimeError(auth_error_message(res))
    data = res.json()
    st.session_state[cache_key] = {"data": data, "loaded_at": now}
    return data


def refresh_billing_account_silently():
    st.session_state.pop("billing_account_cache", None)
    try:
        return load_billing_account(use_cache=False)
    except Exception:
        return None


def get_cached_billing_account():
    cached = st.session_state.get("billing_account_cache")
    return cached.get("data") if cached else None


def get_cached_billing_plans():
    return st.session_state.get("billing_plans_cache")


def invalidate_billing_cache():
    st.session_state.pop("billing_account_cache", None)
    st.session_state.pop("billing_plans_cache", None)
    st.session_state.pop("billing_auto_loaded", None)


def invalidate_notes_cache():
    st.session_state.pop("notes_list_cache", None)
    st.session_state.pop("graph_data_cache", None)
    st.session_state.pop("notes_auto_loaded", None)
    st.session_state.pop("graph_auto_loaded", None)
    fetch_graph_data_cached.clear()


def load_notes(limit=20, use_cache=True):
    cache_key = "notes_list_cache"
    cached = st.session_state.get(cache_key)
    if use_cache and cached and cached.get("limit") == limit:
        return cached["data"]

    list_res = api_request("GET", "/notes", params={"limit": limit})
    if list_res.status_code != 200:
        raise RuntimeError(auth_error_message(list_res))
    notes = list_res.json()
    st.session_state[cache_key] = {"limit": limit, "data": notes}
    return notes


def split_tags_text(tags_text):
    if isinstance(tags_text, list):
        return [str(tag).strip() for tag in tags_text if str(tag).strip()]
    return [tag.strip() for tag in str(tags_text).replace("，", ",").split(",") if tag.strip()]


def tags_to_text(tags_value):
    return ", ".join(split_tags_text(tags_value))


def build_note_update_payload(note, tags):
    meta = note.get("metadata", {}) or {}
    document_text = note.get("document", "")
    return {
        "title": meta.get("title", ""),
        "summary": meta.get("summary", ""),
        "core_ideas": parse_list_from_doc(document_text, "Core Ideas"),
        "key_features": parse_list_from_doc(document_text, "Key Features"),
        "possible_applications": parse_list_from_doc(document_text, "Applications"),
        "tags": tags,
    }


def load_graph_data(use_cache=True):
    cache_key = "graph_data_cache"
    cached = st.session_state.get(cache_key)
    if use_cache and cached:
        return cached["data"]

    if use_cache:
        data = fetch_graph_data_cached(st.session_state.get("access_token") or "")
    else:
        fetch_graph_data_cached.clear()
        res = api_request("GET", "/graph", params={"refresh": True})
        if res.status_code != 200:
            raise RuntimeError(auth_error_message(res))
        res.encoding = 'utf-8'
        data = res.json()
    st.session_state[cache_key] = {"data": data}
    return data


def render_page_header(kicker, title, copy):
    st.markdown(
        f"""
        <div class="page-head">
            <div class="page-kicker">{kicker}</div>
            <div class="page-title">{title}</div>
            <div class="page-copy">{copy}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_grid(items, columns=3):
    cells = []
    for idx, item in enumerate(items):
        variant = " primary" if idx == 0 else ""
        note = f"<small>{item.get('note', '')}</small>" if item.get("note") else ""
        cells.append(
            f'<div class="metric-card{variant}">'
            f'<span>{item.get("label", "")}</span>'
            f'<strong>{item.get("value", "")}</strong>'
            f'{note}'
            f'</div>'
        )
    st.markdown(
        f'<div class="metric-grid" style="grid-template-columns: repeat({columns}, minmax(0, 1fr));">{"".join(cells)}</div>',
        unsafe_allow_html=True,
    )


def render_tool_cards(items):
    cells = []
    for item in items:
        cells.append(
            f'<div class="tool-card">'
            f'<strong>{item.get("title", "")}</strong>'
            f'<span>{item.get("copy", "")}</span>'
            f'</div>'
        )
    st.markdown(f'<div class="capture-strip">{"".join(cells)}</div>', unsafe_allow_html=True)


def render_billing_page():
    render_page_header(
        "Account",
        "额度管理",
        "查看额度余额、使用流水，并通过本地模拟支付完成充值。",
    )

    account = get_cached_billing_account()
    plans = get_cached_billing_plans()
    load_billing_now = not st.session_state.get("billing_auto_loaded")

    col_status, col_action = st.columns([4, 1])
    with col_status:
        st.markdown(
            '<div class="section-copy">额度信息会读取账户余额和最近流水；加载后切换页面会复用缓存。</div>',
            unsafe_allow_html=True,
        )
    with col_action:
        button_label = "加载额度" if not account or not plans else "🔄 刷新"
        if st.button(button_label, use_container_width=True):
            load_billing_now = True

    if load_billing_now:
        invalidate_billing_cache()
        with st.spinner("正在加载额度信息..."):
            try:
                account = load_billing_account(use_cache=False)
                plans_res = api_request("GET", "/billing/plans", timeout=20)
                if plans_res.status_code != 200:
                    st.error(f"加载套餐失败：{auth_error_message(plans_res)}")
                    return
                plans = plans_res.json().get("plans", [])
                st.session_state.billing_plans_cache = plans
                st.session_state.billing_auto_loaded = True
            except Exception as e:
                st.error(f"加载额度信息失败：{str(e)}")
                return

    if not account or not plans:
        st.info("点击“加载额度”后查看余额、套餐和最近流水。")
        return

    render_metric_grid([
        {"label": "当前余额", "value": f"{account.get('balance', 0)} 点", "note": "用于录入、分析、问答和周报"},
        {"label": "累计充值", "value": f"{account.get('total_purchased', 0)} 点", "note": "包含模拟支付和后台调整"},
        {"label": "累计消耗", "value": f"{account.get('total_spent', 0)} 点", "note": "记录所有扣费操作"},
    ])

    st.markdown("### 充值套餐")
    plan_cols = st.columns(len(plans) or 1)
    for idx, plan in enumerate(plans):
        with plan_cols[idx]:
            st.markdown(
                f"""
                <div class="plan-card">
                    <div class="plan-name">{plan.get('name')}</div>
                    <div class="plan-price">{format_price(plan.get('amount_cents', 0), plan.get('currency', 'CNY'))}</div>
                    <div><b>{plan.get('credits')} 点额度</b></div>
                    <div class="plan-desc">{plan.get('description', '')}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("模拟支付并充值", key=f"buy_{plan.get('id')}", type="primary", use_container_width=True):
                pay_res = api_request("POST", "/billing/payments/mock", json={"plan_id": plan.get("id")}, timeout=20)
                if pay_res.status_code == 200:
                    invalidate_billing_cache()
                    st.toast("充值成功")
                    st.rerun()
                else:
                    st.error(f"充值失败：{auth_error_message(pay_res)}")

    st.markdown("### 最近流水")
    transactions = account.get("recent_transactions", [])
    if not transactions:
        st.markdown('<div class="empty-panel">暂无流水。完成录入、分析或充值后会显示最近记录。</div>', unsafe_allow_html=True)
        return

    for item in transactions:
        amount = int(item.get("amount", 0))
        amount_text = f"+{amount}" if amount > 0 else str(amount)
        amount_class = "positive" if amount > 0 else "negative"
        created_at = format_beijing_time(item.get("created_at"))
        st.markdown(
            f'<div class="transaction-row">'
            f'<div class="transaction-amount {amount_class}">{amount_text} 点</div>'
            f'<div>{item.get("description", "")}</div>'
            f'<div class="transaction-meta">余额 {item.get("balance_after", 0)}</div>'
            f'<div class="transaction-meta">{created_at}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

 

def render_admin_page():
    render_page_header(
        "后台管理",
        "用户数据管理",
        "面向运营维护的控制台：快速定位用户、调整额度、导出记录，并用双确认保护删除操作。",
    )

    if not st.session_state.current_user.get("is_admin"):
        st.error("需要管理员权限。")
        return

    top_left, top_right = st.columns([5, 1])
    with top_left:
        st.markdown(
            '<div class="section-copy">用户列表来自账号数据库。导出内容包含笔记、额度账户和交易流水，不包含原始音频文件字节。</div>',
            unsafe_allow_html=True,
        )
    with top_right:
        if st.button("刷新数据", use_container_width=True):
            st.session_state.pop("admin_users_cache", None)
            st.session_state.pop("admin_user_detail", None)

    users_payload = st.session_state.get("admin_users_cache")
    if users_payload is None:
        with st.spinner("正在加载用户..."):
            res = api_request("GET", "/admin/users", timeout=60)
            if res.status_code != 200:
                st.error(f"加载用户失败：{auth_error_message(res)}")
                return
            users_payload = res.json()
            st.session_state.admin_users_cache = users_payload

    users = users_payload.get("users", [])
    if not users:
        st.info("暂无用户。")
        return

    total_notes = sum(int(user.get("note_count") or 0) for user in users)
    total_balance = sum(int(user.get("balance") or 0) for user in users)
    admin_count = sum(1 for user in users if user.get("is_admin"))
    st.markdown(
        f"""
        <div class="admin-status-grid">
            <div class="admin-status accent"><span>用户总数</span><strong>{len(users)}</strong></div>
            <div class="admin-status"><span>管理员</span><strong>{admin_count}</strong></div>
            <div class="admin-status"><span>笔记总数</span><strong>{total_notes}</strong></div>
            <div class="admin-status"><span>剩余额度</span><strong>{total_balance}</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    search_text = st.text_input("搜索用户", placeholder="输入邮箱或用户 ID", key="admin_user_search")
    visible_users = users
    if search_text.strip():
        keyword = search_text.strip().lower()
        visible_users = [
            user for user in users
            if keyword in str(user.get("email", "")).lower()
            or keyword in str(user.get("id", "")).lower()
        ]

    if not visible_users:
        st.info("没有匹配的用户。")
        return

    table_rows = [
        {
            "邮箱": user.get("email"),
            "用户ID": user.get("id"),
            "笔记数": user.get("note_count", 0),
            "当前额度": user.get("balance"),
            "累计消耗": user.get("total_spent"),
            "管理员": user.get("is_admin", False),
            "创建时间": format_beijing_time(user.get("created_at")),
        }
        for user in visible_users
    ]
    st.dataframe(table_rows, use_container_width=True, hide_index=True)

    st.markdown(
        '<div class="admin-panel"><div class="admin-panel-title">选择用户</div>'
        '<div class="admin-panel-copy">先加载详情，再进行额度修改、数据导出或删除账号。</div></div>',
        unsafe_allow_html=True,
    )
    user_options = {f"{user.get('email')} ({user.get('id')[:8]})": user.get("id") for user in visible_users}
    selected_label = st.selectbox("选择用户", options=list(user_options.keys()))
    selected_user_id = user_options[selected_label]

    load_col, hint_col = st.columns([1, 3])
    with load_col:
        load_clicked = st.button("加载详情", type="primary", use_container_width=True)
    with hint_col:
        st.caption("详情不会自动切换，避免误操作到刚刚搜索出来的其他用户。")

    if load_clicked:
        with st.spinner("正在加载用户详情..."):
            res = api_request("GET", f"/admin/users/{selected_user_id}", timeout=60)
            if res.status_code == 200:
                st.session_state.admin_user_detail = res.json()
            else:
                st.error(f"加载详情失败：{auth_error_message(res)}")

    detail = st.session_state.get("admin_user_detail")
    if not detail or detail.get("user", {}).get("id") != selected_user_id:
        return

    user = detail.get("user", {})
    notes = detail.get("notes", [])
    billing = detail.get("billing", {})
    account = billing.get("account") or {}
    transactions = billing.get("transactions", [])
    payments = billing.get("payments", [])
    audio_file_count = sum(
        1 for note in notes
        if (note.get("metadata") or {}).get("source_url")
    )

    st.markdown(f'<div class="admin-user-chip">当前操作用户 · {user.get("email", "")}</div>', unsafe_allow_html=True)
    col_email, col_notes, col_balance = st.columns(3)
    col_email.metric("邮箱", user.get("email", ""))
    col_notes.metric("笔记数", len(notes))
    col_balance.metric("当前额度", account.get("balance", 0))

    tab_account, tab_records, tab_danger = st.tabs(["账户操作", "数据记录", "危险操作"])

    with tab_account:
        st.markdown(
            '<div class="admin-panel"><div class="admin-panel-title">额度调整</div>'
            '<div class="admin-panel-copy">设置用户新的当前额度，系统会自动写入 admin_adjust 流水，便于之后追踪。</div></div>',
            unsafe_allow_html=True,
        )
        with st.form(f"credit_form_{selected_user_id}"):
            col_balance_input, col_reason = st.columns([1, 2])
            with col_balance_input:
                new_balance = st.number_input(
                    "新的当前额度",
                    min_value=0,
                    value=int(account.get("balance", 0) or 0),
                    step=1,
                )
            with col_reason:
                reason = st.text_input("调整原因", value="管理员调整额度")
            submitted = st.form_submit_button("保存额度修改", type="primary", use_container_width=True)
            if submitted:
                res = api_request(
                    "PATCH",
                    f"/admin/users/{selected_user_id}/credits",
                    json={"balance": int(new_balance), "reason": reason},
                    timeout=30,
                )
                if res.status_code == 200:
                    st.success("额度已更新。")
                    detail_res = api_request("GET", f"/admin/users/{selected_user_id}", timeout=60)
                    if detail_res.status_code == 200:
                        st.session_state.admin_user_detail = detail_res.json()
                    st.session_state.pop("admin_users_cache", None)
                    st.rerun()
                else:
                    st.error(f"额度更新失败：{auth_error_message(res)}")

        st.download_button(
            "下载用户数据导出",
            data=json.dumps(detail, ensure_ascii=False, indent=2),
            file_name=f"flashofthought-user-{selected_user_id}.json",
            mime="application/json",
            use_container_width=True,
        )

    with tab_records:
        with st.expander("额度流水", expanded=True):
            if transactions:
                display_transactions = [
                    {**item, "created_at": format_beijing_time(item.get("created_at"))}
                    for item in transactions
                ]
                st.dataframe(display_transactions, use_container_width=True, hide_index=True)
            else:
                st.info("暂无额度流水。")

        with st.expander("笔记", expanded=False):
            if notes:
                for note in notes:
                    meta = note.get("metadata", {})
                    st.markdown(f"**{meta.get('title', '无标题')}**")
                    st.caption(f"{note.get('id')} | {format_beijing_time(meta.get('created_at'))}")
                    st.write(meta.get("summary", ""))
            else:
                st.info("暂无笔记。")

    with tab_danger:
        st.markdown(
            '<div class="danger-panel"><strong>永久删除账号</strong>'
            '<div class="admin-panel-copy">删除后会移除该用户账号、笔记、额度数据和已存储的音频文件。这个操作不能撤销。</div></div>',
            unsafe_allow_html=True,
        )
        impact_cols = st.columns(4)
        impact_cols[0].metric("将删除账号", "1 个")
        impact_cols[1].metric("将删除笔记", f"{len(notes)} 条")
        impact_cols[2].metric("将删除额度记录", f"{len(transactions) + len(payments)} 条")
        impact_cols[3].metric("将删除音频文件", f"{audio_file_count} 个")
        confirm_email = st.text_input(
            f"输入用户邮箱确认：{user.get('email', '')}",
            key=f"delete_email_confirm_{selected_user_id}",
        )
        confirm_delete = st.text_input(
            "再输入 DELETE 启用删除按钮。",
            key=f"delete_confirm_{selected_user_id}",
        )
        delete_disabled = (
            confirm_email != user.get("email", "")
            or confirm_delete != "DELETE"
            or user.get("id") == st.session_state.current_user.get("id")
        )
        if user.get("id") == st.session_state.current_user.get("id"):
            st.caption("不能在这里删除当前登录的管理员账号。")
        if st.button("永久删除账号和关联数据", disabled=delete_disabled, use_container_width=True):
            res = api_request("DELETE", f"/admin/users/{selected_user_id}", timeout=60)
            if res.status_code == 200:
                st.success("用户数据已删除。")
                st.session_state.pop("admin_users_cache", None)
                st.session_state.pop("admin_user_detail", None)
                st.rerun()
            else:
                st.error(f"删除失败：{auth_error_message(res)}")


initialize_auth_state()
restore_auth_state_from_cookie()
verify_saved_session()

if not st.session_state.current_user:
    render_auth_page()
    st.stop()

# Sidebar for navigation
with st.sidebar:
    sidebar_balance = None
    cached_account = get_cached_billing_account()
    if not cached_account:
        cached_account = refresh_billing_account_silently()
    if cached_account:
        sidebar_balance = cached_account.get("balance")

    st.image(str(APP_ICON_PATH), width=54)
    st.markdown(
        f"""
        <div class="sidebar-brand">FlashOfThought</div>
        <div class="sidebar-account">已登录 · {mask_email(st.session_state.current_user.get('email'))}</div>
        {f'<div class="quota-pill">额度 {sidebar_balance} 点</div>' if sidebar_balance is not None else ''}
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown('<div class="sidebar-section-title">功能导航</div>', unsafe_allow_html=True)
    
    # Page Option Mapping
    page_options = {
        "record_idea": "🎙️ 录入想法",
        "knowledge_review": "🔍 知识回顾",
        "knowledge_graph": "🕸️ 知识图谱",
        "billing": "💳 额度管理",
    }
    if st.session_state.current_user.get("is_admin"):
        page_options["admin"] = "🛠️ 后台管理"
    requested_page = st.session_state.pop("nav_page", None)
    page_index = list(page_options.keys()).index(requested_page) if requested_page in page_options else 0
    page_selection = st.radio(
        "选择模式", 
        options=list(page_options.keys()), 
        format_func=lambda x: page_options[x],
        index=page_index,
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown('<div class="sidebar-footer">v0.1.0 · Maddie 技术支持</div>', unsafe_allow_html=True)
    if st.button("退出登录", use_container_width=True):
        clear_auth_state(reload_page=True)
        st.stop()

def get_audio_payload_and_signature(audio_data):
    if hasattr(audio_data, "seek"):
        audio_data.seek(0)
    if hasattr(audio_data, "getvalue"):
        payload = audio_data.getvalue()
    else:
        payload = audio_data.read()
    if hasattr(audio_data, "seek"):
        audio_data.seek(0)
    return payload, hashlib.sha256(payload).hexdigest()


def process_uploaded_file(file_data, file_name, file_type="application/octet-stream"):
    """
    Handle file processing: Upload -> Extract text -> Structure -> Display
    """
    with st.spinner("🚀 正在上传并读取文件..."):
        try:
            payload, audio_signature = get_audio_payload_and_signature(file_data)
            processed_signatures = st.session_state.setdefault("processed_audio_signatures", set())
            if audio_signature in processed_signatures:
                st.warning("这个文件已经处理过，避免重复扣额度。需要重新处理请重新选择文件。")
                return

            # 1. Upload
            files = {"file": (file_name, payload, file_type)}
            upload_res = api_request("POST", "/upload", files=files)
            
            if upload_res.status_code == 200:
                upload_data = upload_res.json()
                raw_text = upload_data.get("raw_text", "")
                file_url = upload_data.get("file_url", "")
                if not raw_text.strip():
                    st.error("没有提取到可整理的文字")
                    return
                
                st.toast("✅ 文件读取完成!", icon="🎉")
                
                # 2. Structure
                with st.spinner("🧠 正在整理笔记结构..."):
                    process_res = api_request(
                        "POST",
                        "/process",
                        json={"raw_text": raw_text}
                    )
                    
                    if process_res.status_code == 200:
                        st.session_state.current_note = process_res.json()
                        st.session_state.current_raw_text = raw_text
                        st.session_state.current_file_url = file_url
                        processed_signatures.add(audio_signature)
                        st.rerun()
                    else:
                        st.error(f"整理失败: {auth_error_message(process_res)}")
            else:
                st.error(f"上传失败: {auth_error_message(upload_res)}")
        except Exception as e:
            st.error(f"发生错误: {str(e)}")


def process_audio(audio_data, file_name, file_type="audio/mp3"):
    process_uploaded_file(audio_data, file_name, file_type)

def process_text_input(text):
    """
    Handle text input processing: Structure -> Display -> Save
    """
    if not text.strip():
        st.warning("请输入内容")
        return

    with st.spinner("🧠 正在整理笔记结构..."):
        try:
            process_res = api_request(
                "POST",
                "/process",
                json={"raw_text": text}
            )
            
            if process_res.status_code == 200:
                st.session_state.current_note = process_res.json()
                st.session_state.current_raw_text = text
                st.session_state.current_file_url = ""
                st.toast("✅ 整理成功！", icon="✨")
                st.rerun()
            else:
                st.error(f"整理失败: {auth_error_message(process_res)}")
        except Exception as e:
            st.error(f"发生错误: {str(e)}")

def get_related_notes(query, current_id=None):
    """
    Fetch related notes using semantic search
    """
    try:
        search_res = api_request("POST", "/search", json={"query": query, "limit": 4})
        if search_res.status_code == 200:
            results = search_res.json()
            # Filter out the current note itself if current_id is provided
            if current_id:
                results = [r for r in results if r.get('id') != current_id]
            return results[:3] # Return top 3 unique related notes
    except:
        pass
    return []

def display_note():
    """
    Display the structured note and save button from session state
    """
    if "current_note" not in st.session_state or not st.session_state.current_note:
        return

    note_data = st.session_state.current_note
    raw_text = st.session_state.current_raw_text
    file_url = st.session_state.current_file_url

    st.divider()
    
    col_main, col_sidebar = st.columns([2, 1])

    with col_main:
        with st.container(border=True):
            st.subheader(f"📝 {note_data.get('title', '无标题')}")
            
            # Enhanced Tags Display
            tags = note_data.get('tags', [])
            if tags:
                st.markdown(" ".join([f"`#{t}`" for t in tags]))
            
            st.markdown("### 💡 核心摘要")
            st.info(note_data.get('summary', '暂无摘要'))
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 🎯 核心观点")
                for item in note_data.get('core_ideas', []):
                    st.markdown(f"- {item}")
                
                st.markdown("### 🛠️ 关键功能")
                for item in note_data.get('key_features', []):
                    st.markdown(f"- {item}")
            
            with col2:
                st.markdown("### 🚀 可能应用")
                for item in note_data.get('possible_applications', []):
                    st.markdown(f"- {item}")
            
            with st.expander("查看原始文本"):
                st.text_area("原始文本", value=raw_text, height=100, disabled=True)

    with col_sidebar:
        st.markdown("### 🧠 第二大脑关联")
        related = get_related_notes(note_data.get('summary', '') + " " + note_data.get('title', ''))
        if related:
            st.success("发现相关想法：")
            for r in related:
                meta = r.get('metadata', {})
                with st.expander(f"🔗 {meta.get('title', '无标题')}"):
                    st.caption(f"相似度: {r.get('score', 0):.2f}")
                    st.write(meta.get('summary', ''))
        else:
            st.info("暂无直接关联的想法，继续记录以构建你的知识图谱！")
    
    # 3. Save
    st.write("")
    col_save, col_clear, _ = st.columns([1, 1, 3])
    with col_save:
        if st.button("💾 保存到知识库", type="primary", use_container_width=True):
            with st.spinner("正在保存..."):
                try:
                    save_payload = {
                        "note": note_data,
                        "raw_text": raw_text,
                        "source_url": file_url
                    }
                    save_res = api_request("POST", "/save", json=save_payload)
                    if save_res.status_code == 200:
                        refresh_billing_account_silently()
                        invalidate_notes_cache()
                        st.balloons()
                        st.toast("保存成功!", icon="💾")
                        # Clear current note
                        st.session_state.current_note = None
                        st.session_state.current_raw_text = ""
                        st.session_state.current_file_url = ""
                        time.sleep(1) 
                        st.rerun() 
                    else:
                        st.error(f"保存失败: {auth_error_message(save_res)}")
                except Exception as e:
                    st.error(f"连接失败: {str(e)}")
    
    with col_clear:
        if st.button("🗑️ 放弃并清除", use_container_width=False):
            with st.spinner("Discarding..."):
                discard_res = api_request("POST", "/discard", json={"source_url": file_url})
                if discard_res.status_code == 200:
                    refresh_billing_account_silently()
                    st.session_state.current_note = None
                    st.session_state.current_raw_text = ""
                    st.session_state.current_file_url = ""
                    st.rerun()
                else:
                    st.error(f"Discard failed: {auth_error_message(discard_res)}")

if page_selection == "billing":
    render_billing_page()

elif page_selection == "admin":
    render_admin_page()

elif page_selection == "record_idea":
    render_page_header(
        "Capture",
        "记录灵感",
        "把语音、文件或文字整理成结构化笔记，再保存进你的个人知识库。",
    )
    
    # Always try to display current note if exists
    display_note()
    
    if "current_note" not in st.session_state or not st.session_state.current_note:
        render_tool_cards([
            {"title": "文字输入", "copy": "适合直接整理脑中的想法草稿，片段、要点或随手记都可以。"},
            {"title": "麦克风录音", "copy": "适合现场快速记录，录完确认后再处理，不满意可以重新录制。"},
            {"title": "上传文件", "copy": "适合会议录音、语音备忘和已有音频，上传后自动转写再结构化。"},
        ])
        tab1, tab2, tab3 = st.tabs(["📝 文字输入", "🎤 麦克风录音", "📤 上传文件"])
    
        with tab1:
            st.markdown('<div class="section-label">直接写下想法</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-copy">不用写完整，片段、要点或随手记都可以整理成笔记。</div>', unsafe_allow_html=True)
            # Use session state to persist text input, or clear it if needed
            if "text_input_val" not in st.session_state:
                st.session_state.text_input_val = ""
                
            text_input = st.text_area("输入想法...", value=st.session_state.text_input_val, height=200, key="idea_text_area")
            
            if st.button("开始整理 (文字)", type="primary"):
                # Clear previous state
                if "text_input_val" in st.session_state:
                     st.session_state.text_input_val = ""
                process_text_input(text_input)

        with tab2:
            st.markdown('<div class="section-label">现场录一段想法</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-copy">录完后确认处理；不满意可以重新录音。</div>', unsafe_allow_html=True)
            
            # Initialize session state for audio key if not exists
            if 'audio_key' not in st.session_state:
                st.session_state.audio_key = 0

            # Audio Input with dynamic key
            audio_input = st.audio_input("录制语音", key=f"audio_input_{st.session_state.audio_key}")
            
            if audio_input:
                col_process, col_rerecord = st.columns([1, 1])
                
                with col_process:
                    if st.button("开始处理 (录音)", type="primary"):
                        # Generate a filename for the recording
                        timestamp = int(time.time())
                        filename = f"recording_{timestamp}.wav"
                        process_audio(audio_input, filename, "audio/wav")
                        st.rerun()
                
                with col_rerecord:
                    if st.button("🔄 重新录音"):
                        st.session_state.audio_key += 1
                        st.rerun()

        with tab3:
            st.markdown('<div class="section-label">从文件开始</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-copy">音频会先转写；txt、md、pdf、docx 会先提取文字，再整理为标题、摘要、要点和应用场景。</div>', unsafe_allow_html=True)
            uploaded_file = st.file_uploader("拖拽或选择文件", type=['mp3', 'wav', 'm4a', 'aac', 'txt', 'md', 'pdf', 'docx', 'doc'])
            if uploaded_file:
                file_extension = uploaded_file.name.rsplit(".", 1)[-1].lower() if "." in uploaded_file.name else ""
                if file_extension in {"mp3", "wav", "m4a", "aac"}:
                    st.audio(uploaded_file)
                else:
                    st.caption(f"已选择：{uploaded_file.name}")
                if st.button("开始处理 (文件)", type="primary"):
                    process_uploaded_file(uploaded_file, uploaded_file.name, uploaded_file.type or "application/octet-stream")
                    st.rerun()

elif page_selection == "knowledge_review":
    render_page_header(
        "Library",
        "知识回顾",
        "浏览最近笔记，按需搜索、对话或生成周报。这里是你的灵感沉淀区。",
    )
    
    # Chat Review Mode
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    notes_cache = st.session_state.get("notes_list_cache")
    notes = notes_cache.get("data") if notes_cache and notes_cache.get("limit") == 20 else None
    load_notes_now = notes is None and not st.session_state.get("notes_auto_loaded")

    col_header, col_refresh = st.columns([4, 1])
    with col_header:
        if notes is None:
            st.markdown('<div class="section-label">最近笔记</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="section-copy">点击加载最近笔记；加载后切换页面会直接使用缓存。</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="section-label">最近笔记 <span class="note-count">{len(notes)} 条</span></div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div class="section-copy">最近记录的灵感会优先显示；先扫列表，再选择一条查看详情、编辑或继续做 AI 分析。</div>',
                unsafe_allow_html=True,
            )
    with col_refresh:
        button_label = "加载笔记" if notes is None else "🔄 刷新"
        if st.button(button_label, use_container_width=True):
            st.session_state.pop("notes_list_cache", None)
            for k in list(st.session_state.keys()):
                if k.startswith("active_analysis_"):
                    del st.session_state[k]
            load_notes_now = True

    if load_notes_now:
        with st.spinner("正在加载笔记列表..."):
            try:
                notes = load_notes(limit=20, use_cache=False)
                st.session_state.notes_auto_loaded = True
            except Exception as e:
                notes = None
                st.error(f"加载笔记失败: {str(e)}")

    if notes is not None:
        if not notes:
            st.markdown('<div class="empty-panel">还没有笔记。去“录入想法”捕捉第一条灵感后，这里会出现可搜索、可分析的知识库。</div>', unsafe_allow_html=True)
        else:
            tag_set = set()
            analyzed_count = 0
            for item in notes:
                meta = item.get("metadata", {}) or {}
                tags_value = meta.get("tags", "")
                if isinstance(tags_value, str):
                    tag_set.update([tag.strip() for tag in tags_value.split(",") if tag.strip()])
                if any(key in meta for key in ["expanded_idea", "roadmap", "score"]):
                    analyzed_count += 1
            render_metric_grid([
                {"label": "最近笔记", "value": f"{len(notes)} 条", "note": "按创建时间倒序展示"},
                {"label": "标签数", "value": f"{len(tag_set)} 个", "note": "来自当前加载的最近笔记"},
                {"label": "已分析", "value": f"{analyzed_count} 条", "note": "包含扩展、路线或评分"},
            ])
            note_rows = []
            note_lookup = {}
            for note in notes:
                meta = note.get("metadata", {}) or {}
                note_id = note.get("id")
                tags_value = meta.get("tags", "")
                if isinstance(tags_value, str):
                    tags_list = [tag.strip() for tag in tags_value.split(",") if tag.strip()]
                elif isinstance(tags_value, list):
                    tags_list = [str(tag).strip() for tag in tags_value if str(tag).strip()]
                else:
                    tags_list = []
                analysis_status = []
                if meta.get("expanded_idea"):
                    analysis_status.append("扩展")
                if meta.get("roadmap"):
                    analysis_status.append("路线")
                if meta.get("score"):
                    analysis_status.append("评分")
                note_lookup[note_id] = note
                note_rows.append({
                    "标题": meta.get("title", "无标题"),
                    "标签": tags_list,
                    "创建时间": format_beijing_time(meta.get("created_at")),
                    "摘要": meta.get("summary", ""),
                    "正文": note.get("document", ""),
                    "分析": analysis_status,
                    "ID": note_id,
                })

            filter_col_search, filter_col_tag, filter_col_status = st.columns([2, 2, 1])
            with filter_col_search:
                review_query = st.text_input(
                    "搜索笔记",
                    placeholder="搜索标题、摘要、正文或标签",
                    key="review_note_query",
                )
            with filter_col_tag:
                selected_tags = st.multiselect(
                    "按标签筛选",
                    options=sorted(tag_set),
                    key="review_note_tags",
                )
            with filter_col_status:
                analysis_filter = st.selectbox(
                    "分析状态",
                    ["全部", "已分析", "未分析"],
                    key="review_note_analysis_filter",
                )

            query = review_query.strip().lower()
            filtered_note_rows = []
            for row in note_rows:
                haystack = " ".join([
                    str(row["标题"]),
                    str(row["摘要"]),
                    str(row["正文"]),
                    " ".join(row["标签"]),
                ]).lower()
                matches_query = not query or query in haystack
                matches_tags = not selected_tags or all(tag in row["标签"] for tag in selected_tags)
                matches_analysis = (
                    analysis_filter == "全部"
                    or (analysis_filter == "已分析" and row["分析"])
                    or (analysis_filter == "未分析" and not row["分析"])
                )
                if matches_query and matches_tags and matches_analysis:
                    filtered_note_rows.append(row)

            if not filtered_note_rows:
                st.markdown('<div class="empty-panel">没有找到匹配的笔记。换个关键词、减少标签筛选，或去录入新的想法。</div>', unsafe_allow_html=True)
                selected_note_id = None
            else:
                st.caption(f"已筛选出 {len(filtered_note_rows)} / {len(note_rows)} 条笔记")
                if len(filtered_note_rows) > 5:
                    st.caption("列表最多显示 5 条，继续向下滚动可查看更多笔记。")
                filtered_note_ids = [row["ID"] for row in filtered_note_rows]
                if st.session_state.get("selected_review_note_id") not in filtered_note_ids:
                    st.session_state.selected_review_note_id = filtered_note_ids[0]

                list_height = min(len(filtered_note_rows), 5) * 123 + 8
                with st.container(height=list_height, border=False):
                    for row in filtered_note_rows:
                        is_active = row["ID"] == st.session_state.get("selected_review_note_id")
                        row_class = "note-list-row active" if is_active else "note-list-row"
                        tags_html = "".join([f'<span class="note-chip">#{html.escape(tag)}</span>' for tag in row["标签"][:5]])
                        analysis_html = "".join([f'<span class="note-chip analysis-chip">{html.escape(status)}</span>' for status in row["分析"]])
                        if not analysis_html:
                            analysis_html = '<span class="note-chip analysis-chip">未分析</span>'
                        summary = html.escape(str(row["摘要"] or "暂无摘要"))
                        if len(summary) > 120:
                            summary = f"{summary[:120]}..."
                        col_note, col_open, col_tags = st.columns([5, 1, 1])
                        with col_note:
                            st.markdown(
                                f'<div class="{row_class}">'
                                f'<div class="note-row-top"><div class="note-row-title">{html.escape(str(row["标题"]))}</div><div class="note-row-time">{html.escape(str(row["创建时间"]))}</div></div>'
                                f'<div class="note-row-summary">{summary}</div>'
                                f'<div class="note-row-meta">{tags_html}{analysis_html}</div>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )
                        with col_open:
                            st.write("")
                            if st.button("查看", key=f"select_review_note_{row['ID']}", disabled=is_active, use_container_width=True):
                                st.session_state.selected_review_note_id = row["ID"]
                        with col_tags:
                            st.write("")
                            quick_tag_key = f"quick_tag_edit_{row['ID']}"
                            if st.button("标签", key=f"toggle_quick_tags_{row['ID']}", use_container_width=True):
                                st.session_state[quick_tag_key] = not st.session_state.get(quick_tag_key, False)
                                st.session_state.selected_review_note_id = row["ID"]
                                st.rerun()

                        if st.session_state.get(f"quick_tag_edit_{row['ID']}", False):
                            with st.form(key=f"quick_tag_form_{row['ID']}"):
                                quick_tags = st.text_input(
                                    "标签 (逗号分隔)",
                                    value=tags_to_text(row["标签"]),
                                    key=f"quick_tags_input_{row['ID']}",
                                )
                                save_tags, cancel_tags = st.columns([1, 1])
                                with save_tags:
                                    submitted_tags = st.form_submit_button("保存标签", use_container_width=True)
                                with cancel_tags:
                                    cancelled_tags = st.form_submit_button("取消", use_container_width=True)

                                if submitted_tags:
                                    try:
                                        updated_note = build_note_update_payload(note_lookup[row["ID"]], split_tags_text(quick_tags))
                                        upd_res = api_request("PUT", f"/notes/{row['ID']}", json=updated_note)
                                        if upd_res.status_code == 200:
                                            invalidate_notes_cache()
                                            st.toast("标签已保存!")
                                            st.session_state[quick_tag_key] = False
                                            time.sleep(1)
                                            st.rerun()
                                        else:
                                            st.error("标签保存失败")
                                    except Exception as e:
                                        st.error(str(e))
                                elif cancelled_tags:
                                    st.session_state[quick_tag_key] = False
                                    st.rerun()

                selected_note_id = st.session_state.selected_review_note_id
            for note in ([note_lookup[selected_note_id]] if selected_note_id else []):
                        meta = note.get("metadata", {})
                        with st.expander(f"📝 当前笔记：{meta.get('title', '无标题')}", expanded=True):
                            st.caption(f"📅 创建时间: {format_beijing_time(meta.get('created_at')) or '未知'}")
                            
                            # Edit Mode Toggle
                            if f"edit_mode_{note.get('id')}" not in st.session_state:
                                st.session_state[f"edit_mode_{note.get('id')}"] = False
                                
                            col_btns = st.columns([1, 1, 4])
                            with col_btns[0]:
                                if st.button("🗑️ 删除", key=f"del_{note.get('id')}"):
                                    try:
                                        del_res = api_request("DELETE", f"/notes/{note.get('id')}")
                                        if del_res.status_code == 200:
                                            invalidate_notes_cache()
                                            st.toast("删除成功!")
                                            time.sleep(1)
                                            st.rerun()
                                    except Exception as e:
                                        st.error(str(e))
                            
                            with col_btns[1]:
                                if st.button("✏️ 编辑", key=f"edit_{note.get('id')}"):
                                    st.session_state[f"edit_mode_{note.get('id')}"] = not st.session_state[f"edit_mode_{note.get('id')}"]
                                    st.rerun()

                            if st.session_state[f"edit_mode_{note.get('id')}"]:
                                with st.form(key=f"form_{note.get('id')}"):
                                    new_title = st.text_input("标题", value=meta.get('title', ''))
                                    new_summary = st.text_area("摘要", value=meta.get('summary', ''))
                                    new_tags = st.text_input("标签 (逗号分隔)", value=meta.get('tags', ''))
                                    
                                    # Try to extract core_ideas etc from document if possible, or just leave empty for now
                                    # Since we don't store them in metadata individually, we can't easily edit them without parsing document text
                                    # For MVP, we only support editing title, summary, tags.
                                    
                                    if st.form_submit_button("保存修改"):
                                        updated_note = {
                                            "title": new_title,
                                            "summary": new_summary,
                                            "core_ideas": [], 
                                            "key_features": [],
                                            "possible_applications": [],
                                            "tags": [t.strip() for t in new_tags.split(',')]
                                        }
                                        try:
                                            upd_res = api_request("PUT", f"/notes/{note.get('id')}", json=updated_note)
                                            if upd_res.status_code == 200:
                                                invalidate_notes_cache()
                                                st.toast("修改成功!")
                                                st.session_state[f"edit_mode_{note.get('id')}"] = False
                                                time.sleep(1)
                                                st.rerun()
                                            else:
                                                st.error("修改失败")
                                        except Exception as e:
                                            st.error(str(e))
                            else:
                                # Normal Display
                                st.markdown(f"**摘要**: {meta.get('summary', '')}")
                                
                                tags = meta.get('tags', '')
                                if tags:
                                    # Check if it's a list or string
                                    if isinstance(tags, str):
                                        tags = [t.strip() for t in tags.split(',') if t.strip()]
                                    st.markdown(" ".join([f"`#{t}`" for t in tags]))
                                
                                st.divider()
                                
                                # Deep Analysis Buttons
                                col_an1, col_an2, col_an3 = st.columns(3)
                                
                                # Initialize cache structure if not exists
                                if f"analysis_cache_{note.get('id')}" not in st.session_state:
                                    st.session_state[f"analysis_cache_{note.get('id')}"] = {}
                                
                                # Pre-populate cache from persisted metadata
                                if 'expanded_idea' in meta:
                                    st.session_state[f"analysis_cache_{note.get('id')}"]["expand"] = meta['expanded_idea']
                                    
                                if 'roadmap' in meta:
                                    st.session_state[f"analysis_cache_{note.get('id')}"]["roadmap"] = meta['roadmap']
                                if 'score' in meta:
                                    st.session_state[f"analysis_cache_{note.get('id')}"]["score"] = meta['score']

                                clicked_action = None

                                with col_an1:
                                    has_expanded = "expand" in st.session_state[f"analysis_cache_{note.get('id')}"]
                                    btn_label = "✨ 查看扩展" if has_expanded else "✨ 扩展想法"
                                    
                                    if st.button(btn_label, key=f"exp_{note.get('id')}"):
                                        clicked_action = "expand"
                                
                                with col_an2:
                                    has_roadmap = "roadmap" in st.session_state[f"analysis_cache_{note.get('id')}"]
                                    btn_label = "📅 查看路线" if has_roadmap else "📅 生成路线"
                                    
                                    if st.button(btn_label, key=f"road_{note.get('id')}"):
                                        clicked_action = "roadmap"
                                
                                with col_an3:
                                    has_score = "score" in st.session_state[f"analysis_cache_{note.get('id')}"]
                                    btn_label = "📊 查看评分" if has_score else "📊 灵感评分"
                                    
                                    if st.button(btn_label, key=f"score_{note.get('id')}"):
                                        clicked_action = "score"

                                active_key = f"active_analysis_{note.get('id')}"
                                cache_key = f"analysis_cache_{note.get('id')}"

                                if clicked_action:
                                    if st.session_state.get(active_key) == clicked_action:
                                        st.session_state.pop(active_key, None)
                                    else:
                                        st.session_state[active_key] = clicked_action

                                analysis_slot = st.empty()

                                active_type = st.session_state.get(active_key)
                                cache = st.session_state.get(cache_key, {})
                                force_regenerate = False

                                if active_type and active_type in cache:
                                    if st.button("🔄 重新生成", key=f"regen_{note.get('id')}_{active_type}", use_container_width=True):
                                        force_regenerate = True

                                if active_type and (force_regenerate or active_type not in cache):
                                    analysis_slot.empty()
                                    if active_type == "expand":
                                        with analysis_slot.container():
                                            with st.spinner("AI正在扩展想法..."):
                                                try:
                                                    res = api_request(
                                                        "POST",
                                                        "/analyze/expand",
                                                        json={"raw_text": note.get("document", "")},
                                                    )
                                                    if res.status_code == 200:
                                                        result_data = res.json()
                                                        st.session_state[cache_key]["expand"] = result_data
                                                        save_analysis_result(note.get('id'), note, 'expand', result_data, st.session_state.get("access_token"))
                                                        refresh_billing_account_silently()
                                                        st.rerun()
                                                    else:
                                                        st.error("扩展失败")
                                                except Exception as e:
                                                    st.error(str(e))
                                    elif active_type == "roadmap":
                                        with analysis_slot.container():
                                            with st.spinner("AI正在规划路线..."):
                                                try:
                                                    res = api_request(
                                                        "POST",
                                                        "/analyze/roadmap",
                                                        json={"raw_text": note.get("document", "")},
                                                    )
                                                    if res.status_code == 200:
                                                        result_data = res.json()
                                                        st.session_state[cache_key]["roadmap"] = result_data
                                                        save_analysis_result(note.get('id'), note, 'roadmap', result_data, st.session_state.get("access_token"))
                                                        refresh_billing_account_silently()
                                                        st.rerun()
                                                    else:
                                                        st.error("生成失败")
                                                except Exception as e:
                                                    st.error(str(e))
                                    elif active_type == "score":
                                        with analysis_slot.container():
                                            with st.spinner("AI正在评分..."):
                                                try:
                                                    res = api_request(
                                                        "POST",
                                                        "/analyze/score",
                                                        json={"raw_text": note.get("document", "")},
                                                    )
                                                    if res.status_code == 200:
                                                        result_data = res.json()
                                                        st.session_state[cache_key]["score"] = result_data
                                                        save_analysis_result(note.get('id'), note, 'score', result_data, st.session_state.get("access_token"))
                                                        refresh_billing_account_silently()
                                                        st.rerun()
                                                    else:
                                                        st.error("评分失败")
                                                except Exception as e:
                                                    st.error(str(e))
                                    cache = st.session_state.get(cache_key, {})
                                
                                if active_type and active_type in cache:
                                    data = cache[active_type]
                                    with analysis_slot.container():
                                        with st.container(border=True):
                                            st.caption(f"🤖 AI分析: {active_type}")
                                            
                                            if active_type == 'score':
                                                col_s1, col_s2, col_s3, col_s4 = st.columns(4)
                                                col_s1.metric("创新性", f"{data.get('innovation')}/5")
                                                col_s2.metric("商业价值", f"{data.get('business_value')}/5")
                                                col_s3.metric("技术难度", f"{data.get('tech_difficulty')}/5")
                                                col_s4.metric("可行性", f"{data.get('feasibility')}/5")
                                                
                                                reason_text = data.get('reason', '')
                                                for marker in ["\n- ", "\n•", "\n* ", "\n1.", "\n2.", "\n3."]:
                                                    idx = reason_text.find(marker)
                                                    if idx != -1:
                                                        reason_text = reason_text[:idx].strip()
                                                        break
                                                st.info(f"💡 理由: {reason_text}")

                                            elif active_type == 'expand':
                                                st.markdown("### 💡 AI扩展建议")
                                                st.markdown("**1. 功能**:")
                                                for f in data.get('features', []):
                                                    st.markdown(f"- {f}")
                                                st.markdown(f"**2. 产品形态**: {data.get('product_form')}")
                                                st.markdown(f"**3. 商业模式**: {data.get('business_model')}")
                                                st.markdown(f"**4. 技术实现**: {data.get('tech_implementation')}")
                                                    
                                            elif active_type == 'roadmap':
                                                for phase in data.get('roadmap', []):
                                                    st.markdown(f"**{phase.get('phase', '阶段')}**")
                                                    for task in phase.get('tasks', []):
                                                        st.markdown(f"- [ ] {task}")

                                st.divider()

                                with st.container(border=True):
                                    st.caption("📌 笔记要点")
                                    document_text = note.get("document", "")
                                    sections = {
                                        "Core Ideas": "🎯 核心观点",
                                        "Key Features": "🛠️ 关键功能",
                                        "Applications": "🚀 可能应用",
                                        "Raw": "📝 原始记录"
                                    }
                                    
                                    for key, label in sections.items():
                                        start_marker = f"{key}: "
                                        if start_marker in document_text:
                                            start_idx = document_text.find(start_marker) + len(start_marker)
                                            content_end = len(document_text)
                                            
                                            for next_key in ["Title:", "Summary:", "Core Ideas:", "Key Features:", "Applications:", "Raw:"]:
                                                if next_key.strip() == key.strip() + ":":
                                                    continue
                                                    
                                                next_marker = f"\n{next_key}" 
                                                next_idx = document_text.find(next_marker, start_idx)
                                                if next_idx != -1 and next_idx < content_end:
                                                    content_end = next_idx
                                            
                                            section_content = document_text[start_idx:content_end].strip()
                                            
                                            if section_content and key == "Raw":
                                                st.markdown(f"**{label}**")
                                                st.text_area(
                                                    "原始记录",
                                                    value=section_content,
                                                    height=120,
                                                    disabled=True,
                                                    label_visibility="collapsed",
                                                    key=f"raw_text_{note.get('id')}",
                                                )
                                            elif section_content:
                                                st.markdown(f"**{label}**")
                                                if "," in section_content:
                                                    for item in section_content.split(","):
                                                        if item.strip():
                                                            st.markdown(f"- {item.strip()}")
                                                else:
                                                    st.markdown(section_content)
                                                st.write("")

    st.divider()
    st.markdown('<div class="section-label">知识工具</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-copy">搜索、聊天和周报不会自动刷新笔记列表；需要更新时点击上方刷新。</div>', unsafe_allow_html=True)
    render_tool_cards([
        {"title": "智能搜索", "copy": "用自然语言找回相关笔记，适合定位某个旧想法或会议片段。"},
        {"title": "聊天回顾", "copy": "基于你的知识库问答，回答会带上参考笔记，方便追溯来源。"},
        {"title": "AI 周报", "copy": "按 7、14 或 30 天汇总主题、重点想法和阶段性关注点。"},
    ])

    tab_search, tab_chat, tab_summary = st.tabs(["🔎 智能搜索", "💬 聊天回顾", "📊 AI周报"])

    with tab_summary:
        st.subheader("📅 AI灵感周报")
        st.caption("自动生成本周灵感总结，助你复盘思考")
        
        col_sum_1, col_sum_2 = st.columns([1, 3])
        with col_sum_1:
            days_option = st.selectbox("时间范围", [7, 14, 30], format_func=lambda x: f"最近 {x} 天")
            if st.button("✨ 生成周报", type="primary", use_container_width=True):
                with st.spinner("AI正在分析你的灵感..."):
                    try:
                        res = api_request("POST", "/analyze/weekly_summary", json={"days": days_option})
                        if res.status_code == 200:
                            st.session_state.weekly_summary = res.json()
                        else:
                            st.error(f"生成失败: {auth_error_message(res)}")
                    except Exception as e:
                        st.error(f"连接失败: {str(e)}")
        
        with col_sum_2:
            if "weekly_summary" in st.session_state and st.session_state.weekly_summary:
                summary = st.session_state.weekly_summary
                data = summary.get("data", {})
                
                st.markdown(f"### 🗓️ 周报 ({summary.get('start_date')} ~ {summary.get('end_date')})")
                
                # 1. Overview
                st.info(f"**本周共记录 {data.get('total_count', 0)} 条想法**")
                
                st.markdown("#### 🧠 本周关注点")
                st.write(data.get('weekly_synthesis', '暂无总结'))
                
                st.divider()
                
                # 2. Breakdown
                col_bd1, col_bd2 = st.columns(2)
                with col_bd1:
                    st.markdown("#### 🏷️ 主题分布")
                    topics = data.get('topic_breakdown', [])
                    if topics:
                        for t in topics:
                            st.markdown(f"- **{t.get('topic')}**: {t.get('count')}")
                    else:
                        st.caption("暂无分类数据")
                        
                with col_bd2:
                    st.markdown("#### ⭐ 重点想法")
                    highlights = data.get('key_highlights', [])
                    if highlights:
                        for h in highlights:
                            st.markdown(f"- {h}")
                    else:
                        st.caption("暂无重点想法")
            else:
                st.info("👈 点击左侧按钮生成你的灵感周报")

    with tab_search:
        with st.container(border=True):
            st.subheader("🔍 智能搜索")
            query = st.text_input("输入关键词或问题", placeholder="例如：我上次关于AI的计划是什么？")
            
            if query:
                with st.spinner("正在搜索..."):
                    try:
                        search_res = api_request("POST", "/search", json={"query": query, "limit": 5})
                        
                        if search_res.status_code == 200:
                            results = search_res.json()
                            
                            if not results:
                                st.warning("没有找到相关笔记。")
                            
                            st.markdown("### 搜索结果")
                            for res in results:
                                meta = res.get("metadata", {})
                                score = res.get("score", 0)
                                
                                with st.expander(f"📄 {meta.get('title', '无标题')} (相似度: {score:.2f})"):
                                    st.caption(f"📅 创建时间: {format_beijing_time(meta.get('created_at')) or '未知'}")
                                    st.markdown(f"**摘要**: {meta.get('summary', '')}")
                                    st.markdown(f"**标签**: {meta.get('tags', '')}")
                                    st.markdown("---")
                                    st.markdown(res.get("document", ""))
                        else:
                            st.error(f"搜索失败: {auth_error_message(search_res)}")
                    except Exception as e:
                        st.error(f"连接失败: {str(e)}")

    with tab_chat:
        st.subheader("💬 与你的知识库对话")
        st.caption("AI将基于你的所有笔记回答问题")
        
        # Display chat history
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if "context" in msg:
                    with st.expander("📚 参考笔记"):
                        for note in msg["context"]:
                            meta = note.get('metadata', {})
                            st.markdown(f"- **{meta.get('title')}**: {meta.get('summary')}")

        # Chat Input
        if prompt := st.chat_input("问我关于你笔记的问题..."):
            # Add user message
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Generate response
            with st.chat_message("assistant"):
                with st.spinner("思考中..."):
                    try:
                        res = api_request("POST", "/chat", json={"query": prompt})
                        if res.status_code == 200:
                            data = res.json()
                            answer = data.get("answer", "我不知道怎么回答。")
                            context = data.get("context", [])
                            
                            st.markdown(answer)
                            if context:
                                with st.expander("📚 参考笔记"):
                                    for note in context:
                                        meta = note.get('metadata', {})
                                        st.markdown(f"- **{meta.get('title')}**: {meta.get('summary')}")
                            
                            st.session_state.chat_history.append({
                                "role": "assistant", 
                                "content": answer,
                                "context": context
                            })
                        else:
                            st.error("AI服务暂时不可用")
                    except Exception as e:
                        st.error(f"连接错误: {str(e)}")

elif page_selection == "knowledge_graph":
    render_page_header(
        "Graph",
        "知识图谱",
        "用关系图查看灵感、标签和笔记之间的连接，适合发现隐藏主题。",
    )

    graph_cache = st.session_state.get("graph_data_cache")
    data = graph_cache.get("data") if graph_cache else None
    load_graph_now = data is None and not st.session_state.get("graph_auto_loaded")
    force_graph_refresh = False

    col_graph_status, col_graph_action = st.columns([4, 1])
    with col_graph_status:
        st.markdown(
            '<div class="section-copy">图谱构建会读取全部笔记；已有缓存时切换页面会直接复用。</div>',
            unsafe_allow_html=True,
        )
    with col_graph_action:
        graph_button_label = "构建图谱" if data is None else "🔄 刷新"
        if st.button(graph_button_label, use_container_width=True):
            st.session_state.pop("graph_data_cache", None)
            load_graph_now = True
            force_graph_refresh = True

    if load_graph_now:
        with st.spinner("正在构建知识图谱..."):
            try:
                data = load_graph_data(use_cache=not force_graph_refresh)
                st.session_state.graph_auto_loaded = True
            except Exception as e:
                data = None
                st.error(f"加载图谱时发生错误: {str(e)}")

    if data is None:
        st.info("点击“构建图谱”后加载知识关系；切换回来会保留缓存。")
    else:
        try:
            nodes_data = data.get("nodes", [])
            edges_data = data.get("edges", [])

            if not nodes_data:
                st.markdown(
                    '<div class="empty-panel">暂无图谱数据。先录入一条想法，系统会根据笔记标题、摘要和标签生成可探索的关系图。</div>',
                    unsafe_allow_html=True,
                )
                if st.button("去录入想法", type="primary"):
                    st.session_state.nav_page = "record_idea"
                    st.rerun()
            else:
                tag_nodes = [node for node in nodes_data if node.get("category") == "Tag"]
                note_nodes = [node for node in nodes_data if node.get("category") == "Note"]
                render_metric_grid([
                    {"label": "笔记节点", "value": f"{len(note_nodes)} 个", "note": "知识图谱中的内容实体"},
                    {"label": "标签节点", "value": f"{len(tag_nodes)} 个", "note": "用于发现主题聚类"},
                    {"label": "关系连接", "value": f"{len(edges_data)} 条", "note": "笔记、标签与核心节点的连接"},
                ])
                st.markdown(
                    '<div class="graph-legend">'
                    '<div class="graph-legend-item"><span class="graph-dot core"></span><span><b>核心节点</b><br>整张图的中心，帮助聚合全部知识关系。</span></div>'
                    '<div class="graph-legend-item"><span class="graph-dot note"></span><span><b>笔记节点</b><br>每条录入内容，点击后可查看它连接到哪些主题。</span></div>'
                    '<div class="graph-legend-item"><span class="graph-dot tag"></span><span><b>标签节点</b><br>从笔记标签抽取的主题，用来发现重复关注点。</span></div>'
                    '</div>',
                    unsafe_allow_html=True,
                )
                # Layout Control
                st.markdown('<div class="graph-toolbar">', unsafe_allow_html=True)
                col_controls = st.columns([1, 1, 1, 3])
                with col_controls[0]:
                    layout_type = st.selectbox("布局模式", ["force", "circular"], format_func=lambda x: "力导向图" if x == "force" else "环形布局")
                with col_controls[1]:
                    show_labels = st.toggle("显示标签", value=True)
                with col_controls[2]:
                    repulsion = st.slider("排斥力", 100, 2000, 1000) if layout_type == "force" else None
                st.markdown('</div>', unsafe_allow_html=True)

                # Process nodes for ECharts
                echart_nodes = []
                categories = []
                seen_categories = set()

                for node in nodes_data:
                    group = node.get("group", "level3")
                    label = node.get("label", "")
                    category = node.get("category", "其他")
                    
                    # Size mapping
                    symbol_size = 15
                    if group == "level1":
                        symbol_size = 60
                        category = "Core"
                    elif group == "level2":
                        symbol_size = 25 # Note size
                        category = "Note"
                    else:
                        symbol_size = 15 # Tag size
                        category = "Tag"

                    # Color mapping
                    item_color = node.get("color", "#A0E0FF")

                    # Tooltip content
                    tooltip_title = node.get("full_title") or label
                    tooltip_desc = node.get("summary", "")
                    
                    echart_nodes.append({
                        "id": node.get("id"),
                        "name": label,
                        "symbolSize": symbol_size,
                        "value": symbol_size,
                        "category": category, # This is used for legend mapping
                        "itemStyle": {
                            "color": item_color,
                            "borderColor": "#fff",
                            "borderWidth": 1 if group == "level3" else 2,
                            "shadowBlur": 10 if group != "level3" else 0,
                            "shadowColor": item_color
                        },
                        "label": {
                            "show": show_labels if group != "level1" else True,
                            "position": "right" if layout_type == "force" else "top",
                            "color": "#fff"
                        },
                        "tooltip": {
                            "formatter": f"<b>{tooltip_title}</b><br/>{tooltip_desc}"
                        }
                    })

                # Define legend categories
                categories = [
                    {"name": "Core"},
                    {"name": "Tag"},
                    {"name": "Note"}
                ]

                # Process edges
                echart_edges = []
                for edge in edges_data:
                    echart_edges.append({
                        "source": edge.get("source"),
                        "target": edge.get("target"),
                        "lineStyle": {
                            "width": 1,
                            "curveness": 0.3,
                            "opacity": 0.5
                        }
                    })

                # ECharts Option
                option = {
                    "backgroundColor": "#0E1117", # Match Streamlit dark theme
                    "title": {
                        "text": "",
                        "textStyle": {"color": "#fff"}
                    },
                    "tooltip": {
                        "trigger": "item",
                        "enterable": True
                    },
                    "legend": {
                        "data": ["Core", "Tag", "Note"],
                        "textStyle": {"color": "#fff"},
                        "top": "bottom"
                    },
                    "series": [
                        {
                            "type": "graph",
                            "layout": layout_type,
                            "data": echart_nodes,
                            "links": echart_edges,
                            "categories": categories,
                            "roam": True,
                            "zoom": 0.576,
                            "scaleLimit": {
                                "min": 0.4,
                                "max": 4
                            },
                            "label": {
                                "show": show_labels,
                                "position": "right",
                                "formatter": "{b}"
                            },
                            "lineStyle": {
                                "color": "source",
                                "curveness": 0.3
                            },
                            "emphasis": {
                                "focus": "adjacency",
                                "lineStyle": {
                                    "width": 4
                                }
                            },
                            "force": {
                                "repulsion": repulsion if layout_type == "force" else 1000,
                                "edgeLength": [50, 200],
                                "gravity": 0.1
                            },
                            "circular": {
                                "rotateLabel": True
                            }
                        }
                    ]
                }

                # Render Graph
                st_echarts(options=option, height="570px", theme="dark")
                
                # Help text
                st.caption("💡 操作提示：滚轮缩放 | 拖拽移动 | 点击节点高亮连接关系 | 悬停查看详情")

        except Exception as e:
            st.error(f"加载图谱时发生错误: {str(e)}")
