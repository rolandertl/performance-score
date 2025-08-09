import os
import requests
import streamlit as st
from urllib.parse import quote
from typing import Optional

st.set_page_config(page_title="GTMetrix-ähnlicher Checker", page_icon="🚀", layout="centered")

# --- API-Key aus Streamlit Secrets (Cloud) oder ENV (Fallback) ---
def get_api_key() -> str:
    try:
        key = st.secrets["api_keys"]["pagespeed"]
        if isinstance(key, str) and key.strip():
            return key.strip()
    except Exception:
        pass
    return os.getenv("PSI_API_KEY", "").strip()

API_KEY = get_api_key()

st.title("Webseiten-Check (MVP)")
st.caption("Py + Streamlit + PageSpeed Insights (Lighthouse)")

# --- Eingaben mit Keys, damit Callbacks zugreifen können ---
url = st.text_input("URL prüfen", placeholder="https://example.com", key="input_url")
strategy = st.radio("Gerät", ["mobile", "desktop"], horizontal=True, index=1, key="input_strategy")

if not API_KEY:
    st.info("Hinweis: Kein API-Key gesetzt. In Streamlit Cloud unter **Manage app → Settings → Secrets** "
            "folgendes eintragen:\n\n[api_keys]\npagespeed = \"DEIN_PSI_API_KEY_HIER\"")

@st.cache_data(show_spinner=False)
def run_pagespeed(url: str, strategy: str, api_key: Optional[str]):
    base = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    query = (
        f"{base}?url={quote(url)}"
        f"&strategy={strategy}"
        f"&category=PERFORMANCE&category=BEST_PRACTICES&category=SEO"
    )
    if api_key:
        query += f"&key={api_key}"
    resp = requests.get(query, timeout=60)
    resp.raise_for_status()
    return resp.json()

def pct(score: Optional[float]) -> Optional[int]:
    if score is None:
        return None
    return round(score * 100)

def grade_from_performance(perf_score_pct: Optional[int]) -> str:
    if perf_score_pct is None:
        return "—"
    if perf_score_pct >= 90: return "A"
    if perf_score_pct >= 80: return "B"
    if perf_score_pct >= 70: return "C"
    if perf_score_pct >= 60: return "D"
    return "E"

# --- Session-State vorbereiten ---
if "last_json" not in st.session_state:
    st.session_state["last_json"] = None
if "last_error" not in st.session_state:
    st.session_state["last_error"] = None

def analyze_cb():
    u = st.session_state.get("input_url", "")
    s = st.session_state.get("input_strategy", "desktop")
    if not u:
        st.session_state["last_error"] = "Bitte eine URL eingeben."
        st.session_state["last_json"] = None
        return
    try:
        data = run_pagespeed(u, s, API_KEY if API_KEY else None)
        st.session_state["last_json"] = data
        st.session_state["last_error"] = None
    except Exception as e:
        st.session_state["last_error"] = f"Fehler beim Abruf: {e}"
        st.session_state["last_json"] = None

st.button("Analysieren", type="primary", on_click=analyze_cb)

# --- Anzeige: verwendet immer die zuletzt berechneten Daten aus Session State ---
if st.session_state["last_error"]:
    st.error(st.session_state["last_error"])

data = st.session_state["last_json"]
if data:
    lh = data.get("lighthouseResult", {}) or {}
    cats = lh.get("categories", {}) or {}
    perf = pct((cats.get("performance") or {}).get("score"))
    structure = pct((cats.get("best-practices") or {}).get("score"))

    audits = lh.get("audits", {}) or {}
    lcp = (audits.get("largest-contentful-paint") or {}).get("displayValue")
    tbt_display = (audits.get("total-blocking-time") or {}).get("displayValue")
    cls = (audits.get("cumulative-layout-shift") or {}).get("displayValue")
    fs = (audits.get("final-screenshot") or {}).get("details", {}).get("data")

    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Performance", f"{perf if perf is not None else '—'}")
    with col2: st.metric("Struktur (Platzhalter)", f"{structure if structure is not None else '—'}")
    with col3: st.metric("Gesamtnote (Platzhalter)", grade_from_performance(perf))

    st.subheader("Web Vitals")
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Largest Contentful Paint", lcp or "—")
    with c2: st.metric("Total Blocking Time", tbt_display or "—")
    with c3: st.metric("Cumulative Layout Shift", cls or "—")

    st.divider()
    st.subheader("Screenshot")
    if fs and fs.startswith("data:image/jpeg;base64,"):
        st.image(fs, caption="Final Screenshot (Lighthouse)", use_column_width=True)
    else:
        st.info("Kein Screenshot vorhanden.")

    with st.expander("Rohdaten (JSON)"):
        st.json(data)
else:
    st.info("Gib eine URL ein und klicke auf **Analysieren**. Ergebnisse bleiben nach dem Lauf sichtbar.")
