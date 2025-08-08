
# GTM-Lite (MVP)

Ein sehr einfacher GTmetrix-ähnlicher Checker mit **Python + Streamlit**. Verwendet die **Google PageSpeed Insights API** (Lighthouse), um

- Performance-Score
- (Platzhalter) Structure-Score – aktuell `best-practices`-Score aus Lighthouse
- Largest Contentful Paint (LCP)
- Total Blocking Time (TBT)
- Cumulative Layout Shift (CLS)
- Final Screenshot

zu zeigen.

## Lokale Nutzung

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export PSI_API_KEY=DEIN_KEY # optional
streamlit run app.py
```

## Deployment

- **Streamlit Community Cloud**: Repo nach GitHub pushen und App verbinden.
- Oder **Docker / Cloud Run** / eigener Server.

## Hinweise

- Ohne API-Key gilt ein strenges Quota der PageSpeed Insights API.
- "Structure" ist aktuell ein Platzhalter (Lighthouse *Best Practices*). Wir können das später durch eine eigene Gewichtung (z. B. SEO + Best Practices + ausgewählte Audits) ersetzen.
- Die Gesamtnote ist ebenfalls ein Platzhalter und leitet sich derzeit nur grob aus dem Performance-Score ab.
