# Klikko Merchant Intelligence

A responsive Streamlit prototype for a future authenticated merchant dashboard. The first module, **Executive Overview**, follows the specification in `Advanced Dashboard.xlsx` and includes:

- ten executive KPI cards with changes, targets, and mini trends;
- four 12-month growth charts;
- top, bottom, and operating-signal snapshots;
- an interactive Indonesia map that switches between revenue, consumers, and vouchers;
- 30-day forecast cards;
- a compact filter panel for business owner, brand, merchant, campaign, program type, machine, geography, product, and consumer attributes;
- KPI export for partner reporting.

The main content width is tuned for a **1092 × 1200** embedded frame. The page remains vertically scrollable and the filter panel collapses to preserve first-view dashboard space.

The other four requested intelligence tabs are included as prepared module shells in the requested order.

## Run locally

The project already has a local environment on this computer. Start the verified preview with:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Streamlit normally opens the dashboard at `http://localhost:8501`.

On a different computer, create a Python virtual environment and install `requirements.txt` first.

## Web embedding

`load_dashboard_data(user_id)` is the integration boundary. Replace its demo body with your authenticated API or database call while retaining the returned field names, or add a normalization layer before rendering.

For production embedding, deploy the app behind HTTPS and allow framing only from the voucher app's trusted domain. Pass the authenticated merchant identity through a short-lived server-side token rather than a query-string user ID.
