import os
import requests
import streamlit as st
from urllib.parse import quote
from typing import Optional

# --- Config ---
st.set_page_config(page_title="GTMetrix-ähnlicher Checker", page_icon="🚀", layout="centered")

def get_api_key() -> str:
    # 1) Streamlit secrets.toml -> [api_keys].pagespeed
    try:
        key = st.secrets["api_keys"]["pagespeed"]
        if isinstance(key, str) and key.strip():
            return key.strip()
    except Exception:
        pass
    # 2) Fallback: Umgebungsvariable
    return os.getenv("PSI_API_KEY", "").strip()

API_KEY = get_api_key()

st.title("Webseiten-Check (MVP)")
st.caption("Py + Streamlit + PageSpeed Insights (Lighthouse)")

url = st.text_input("URL prüfen", placeholder="https://example.com", value="")
col_strategy1, _ = st.columns(2)
with col_strategy1:
    strategy = st.radio("Gerät", ["mobile", "desktop"], horizontal=True, index=1)

if not API_KEY:
    st.info("Hinweis: Kein API-Key gesetzt. Ohne Key ist das Google-Quota stark begrenzt und Anfragen können fehlschlagen. "
            "Hinterlege den Key in `.streamlit/secrets.toml` unter `[api_keys].pagespeed` oder als Umgebungsvariable `PSI_API_KEY`.")

run = st.button("Analysieren", type="primary")

@st.cache_data(show_spinner=False)
def run_pagespeed(url: str, strategy: str, api_key: Optional[str]):
    base = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    # Kategorien: Performance (für Score + Audits), Best Practices (für „Struktur“), SEO (optional für spätere Gewichtung)
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
    # Lighthouse liefert 0..1
    return round(score * 100)

def grade_from_performance(perf_score_pct: Optional[int]) -> str:
    if perf_score_pct is None:
        return "—"
    if perf_score_pct >= 90:
        return "A"
    if perf_score_pct >= 80:
        return "B"
    if perf_score_pct >= 70:
        return "C"
    if perf_score_pct >= 60:
        return "D"
    return "E"

if run and url:
    with st.spinner("Lighthouse läuft…"):
        try:
            data = run_pagespeed(url, strategy, API_KEY if API_KEY else None)
        except Exception as e:
            st.error(f"Fehler beim Abruf: {e}")
            st.stop()

    lh = data.get("lighthouseResult", {}) or {}

    # Scores
    cats = lh.get("categories", {}) or {}
    perf = pct((cats.get("performance") or {}).get("score"))
    # „Struktur“ (Platzhalter): Lighthouse Best Practices
    structure = pct((cats.get("best-practices") or {}).get("score"))

    # Audits
    audits = lh.get("audits", {}) or {}
    lcp = (audits.get("largest-contentful-paint") or {}).get("displayValue")      # z. B. "1.8 s"
    tbt_display = (audits.get("total-blocking-time") or {}).get("displayValue")   # z. B. "65 ms"
    cls = (audits.get("cumulative-layout-shift") or {}).get("displayValue")       # z. B. "0.03"

    # Screenshot (Base64 aus final-screenshot)
    fs = (audits.get("final-screenshot") or {}).get("details", {}).get("data")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Performance", f"{perf if perf is not None else '—'}")
    with col2:
        st.metric("Struktur (Platzhalter)", f"{structure if structure is not None else '—'}")
    with col3:
        st.metric("Gesamtnote (Platzhalter)", grade_from_performance(perf))

    st.subheader("Web Vitals")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Largest Contentful Paint", lcp if lcp else "—")
    with c2:
        st.metric("Total Blocking Time", tbt_display if tbt_display else "—")
    with c3:
        st.metric("Cumulative Layout Shift", cls if cls else "—")

    st.divider()
    st.subheader("Screenshot")
    if fs and fs.startswith("data:image/jpeg;base64,"):
        st.image(fs, caption="Final Screenshot (Lighthouse)", use_column_width=True)
    else:
        st.info("Kein Screenshot vorhanden.")

    with st.expander("Rohdaten (JSON)"):
        st.json(data)

else:
    st.info("Gib eine URL ein und klicke auf **Analysieren**. Den API-Key kannst du in `.streamlit/secrets.toml` "
            "unter `[api_keys].pagespeed` oder als Umgebungsvariable `PSI_API_KEY` hinterlegen.")
