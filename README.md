# Business Insight Dashboard

A public-ready Streamlit dashboard for campaign, voucher, product, merchant,
and customer performance. The repository ships with demo data and a replaceable
repository interface so a backend team can connect SQL, a warehouse, or an API
without changing the dashboard UI.

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
from datetime import date
import os
import pandas as pd


class SqlDashboardRepository:
    def __init__(self) -> None:
        self.database_url = os.environ["DATABASE_URL"]

    def load_kpi_data(
        self, start_date: date, end_date: date
    ) -> pd.DataFrame:
        # Query with bound parameters and return the documented columns.
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

Every repository method receives the selected `start_date` and `end_date`.
Results are cached for five minutes. `validate_frame()` checks required
DataFrame columns and raises a clear error if the backend contract changes.
The authoritative method signatures and schemas are in
[`data_access.py`](data_access.py).

### Required datasets

- KPI: `metric_key`, `value`, `change_pct`, `comparison_label`
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
- Payment methods: `method`, `percentage`

The customer loyalty result is a dictionary containing
`average_transactions`, `repeat_customer_percentage`, `top_age_group`, and
`top_age_group_percentage`.

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
