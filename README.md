# Business Insight Dashboard

A public-ready Streamlit dashboard for campaign, voucher, product, merchant,
and customer performance. The repository ships with demo data and a replaceable
repository interface so a backend team can connect SQL, a warehouse, or an API
without changing the dashboard UI.

## Public demo and embedding

- Live dashboard: <https://soera99-merchant-insights-v2.streamlit.app/>
- GitHub repository: <https://github.com/Soera99/merchant-insights-v2>
- Embed URL: <https://soera99-merchant-insights-v2.streamlit.app/?embed=true>

Streamlit Community Cloud supports embedding public apps in an iframe. The web
team can start with:

```html
<iframe
  src="https://soera99-merchant-insights-v2.streamlit.app/?embed=true&embed_options=light_theme"
  title="Business Insight Dashboard"
  loading="lazy"
  style="width: 100%; height: 1200px; border: 0;"
></iframe>
```

The host page controls the iframe height. Increase `height` if the dashboard
should display more sections before scrolling.

## Run locally

Requires Python 3.10 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

## Data architecture

`app.py` contains presentation and chart code. `data_access.py` owns the data
contract, demo repository, schema validation, and repository selection.

The app uses `MockDashboardRepository` by default. To connect a backend:

1. Create a Python module that implements every method in
   `DashboardRepository`.
2. Add a zero-argument factory that returns that repository.
3. Set `DASHBOARD_REPOSITORY_FACTORY` to `module.path:factory_name`.
4. Put database credentials in environment variables or Streamlit secrets,
   never in source control.

Example:

```python
# backend/repository.py
import os
import pandas as pd

from data_access import DashboardFilters


class SqlDashboardRepository:
    def __init__(self) -> None:
        self.database_url = os.environ["DATABASE_URL"]

    def load_filter_options(self) -> dict[str, list[str]]:
        # Query distinct provinces and cities available to this user.
        ...

    def load_kpi_data(self, filters: DashboardFilters) -> pd.DataFrame:
        # Bind filters.province, filters.city, filters.start_date, and
        # filters.end_date as query parameters. Never concatenate SQL strings.
        ...

    # Implement the remaining DashboardRepository methods.


def create_repository() -> SqlDashboardRepository:
    return SqlDashboardRepository()
```

Then configure:

```bash
export DASHBOARD_REPOSITORY_FACTORY=backend.repository:create_repository
export DATABASE_URL='your-secret-connection-string'
streamlit run app.py
```

Every business-data method receives one immutable `DashboardFilters` object
containing `province`, `city`, `start_date`, and `end_date`. The Province and
City selector values come from `load_filter_options()`, allowing the internal
database to control which locations a user can select.

Results are cached for five minutes. `validate_frame()` checks required
DataFrame columns and raises a clear error if the backend contract changes.
The authoritative method signatures and schemas are in
[`data_access.py`](data_access.py).

### Required datasets

- KPI: `metric_key`, `value`, `change_pct`, `comparison_label`
- Campaign metrics: `metric_key`, `value`, `change_pct`, `comparison_label`
- Campaign funnel: `stage`, `count`, `percentage`, `stage_order`
- Trend: `period`, `vouchers_redeemed`, `redemption_value`,
  `average_transaction_value`
- Channel: `channel`, `redemptions`
- Category performance: `category`, `redeemed`, `sampling`
- Sampled and redeemed products: `product`, `count`
- Category overview: `category`, `vouchers_redeemed`, `redeemed_share`,
  `redemption_value`, `unique_customers`, `conversion_rate`
- Hourly redemptions: `hour`, `redemptions`, `time_range`, `selected_label`
- Outlet, campaign, and location leaderboards: `name`, `redemptions`
- Customer segments: `segment`, `customers`
- Gender: `gender`, `percentage`
- Age groups: `age_group`, `age_range`, `percentage`

The customer loyalty result is a dictionary containing
`average_transactions` and `repeat_customer_percentage`.

The KPI dataset must return these nine `metric_key` values in any order:
`active_campaigns`, `completed_campaigns`, `vouchers_claimed`,
`vouchers_redeemed`, `total_consumers`, `new_consumers`,
`stores_participated`, `redemption_rate`, and `redemption_value`.

The Campaign Performance dataset must return `campaign_views`,
`campaign_clicks`, `click_through_rate`, `claim_rate`,
`total_vouchers_redeemed`, `total_redemption_value`, and
`average_transaction_value`. Funnel rows should be ordered using `stage_order`,
making it safe for the backend to return stages in any database order.

## Secrets

The repository intentionally contains no credentials. Local `.env` files,
private keys, certificates, and `.streamlit/secrets.toml` are ignored by Git.
For Streamlit Community Cloud, add production secrets in the app's **Advanced
settings** or **Secrets** page.

Before publishing future changes, check staged content:

```bash
git diff --cached
git grep -nEi '(api[_-]?key|secret|password|token|private[_-]?key)'
```

## Deploy

Push the repository to GitHub, then create an app in Streamlit Community Cloud
using:

- Repository: this GitHub repository
- Branch: `main`
- Main file path: `app.py`

Streamlit installs the packages in `requirements.txt`. Each push to `main`
automatically updates the deployed app.
