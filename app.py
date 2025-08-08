
import os
import base64
import requests
import streamlit as st
from urllib.parse import quote

# --- Config ---
st.set_page_config(page_title="GTMetrix-ähnlicher Checker", page_icon="🚀", layout="centered")

API_KEY = os.getenv("PSI_API_KEY", "").strip()  # optional; ohne Key gibts ein niedriges Quota

st.title("Webseiten-Check (MVP)")
st.caption("Py + Streamlit + PageSpeed Insights (Lighthouse)")

url = st.text_input("URL prüfen", placeholder="https://example.com", value="")
col_strategy1, col_strategy2 = st.columns(2)
with col_strategy1:
    strategy = st.radio("Gerät", ["mobile", "desktop"], horizontal=True, index=1)

run = st.button("Analysieren", type="primary")

@st.cache_data(show_spinner=False)
def run_pagespeed(url: str, strategy: str, api_key: str | None):
    base = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    params = {
        "url": url,
        "strategy": strategy,
        "category": "PERFORMANCE",
    }
    # Mehr Kategorien für mögliche "Structure"-Definition
    # (SEO/Best Practices liefern bereits Scores)
    # Doppelt anhängen ist egal – die API akzeptiert mehrere category-Parameter.
    params["category"] = "PERFORMANCE"
    # Note: Wir hängen weitere Kategorien per Liste an:
    query = f"{base}?url={quote(url)}&strategy={strategy}&category=PERFORMANCE&category=BEST_PRACTICES&category=SEO"
    if api_key:
        query += f"&key={api_key}"
    resp = requests.get(query, timeout=60)
    resp.raise_for_status()
    return resp.json()

def pct(score: float | None) -> float | None:
    if score is None:
        return None
    # Lighthouse liefert 0..1
    return round(score * 100)

def to_ms(value):
    if value is None:
        return None
    # Einige Werte kommen als ms, andere als s. LCP ist in s, TBT in ms, CLS ist unitless.
    return value

def grade_from_performance(perf_score_pct: int | None) -> str:
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

    lh = data.get("lighthouseResult", {})

    # Scores
    perf = pct(lh.get("categories", {}).get("performance", {}).get("score"))
    # "Structure" (Platzhalter): Wir nehmen zunächst den Best-Practices-Score.
    # Später können wir das in eine eigene Gewichtung aus SEO/Best Practices/und Audits überführen.
    structure = pct(lh.get("categories", {}).get("best-practices", {}).get("score"))

    # Audits
    audits = lh.get("audits", {})
    lcp = audits.get("largest-contentful-paint", {}).get("displayValue")  # typ. z.B. "1.8 s"
    tbt = audits.get("total-blocking-time", {}).get("numericValue")  # in ms
    tbt_display = audits.get("total-blocking-time", {}).get("displayValue")  # z.B. "65 ms"
    cls = audits.get("cumulative-layout-shift", {}).get("displayValue")  # z.B. "0.03"

    # Screenshot (Base64 aus final-screenshot)
    fs = audits.get("final-screenshot", {}).get("details", {}).get("data")

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
    st.info("Geben Sie eine URL ein und klicken Sie auf **Analysieren**. Optional können Sie einen *PSI_API_KEY* als Umgebungsvariable setzen, um mehr Abrufe zu erlauben.")
