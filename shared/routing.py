"""Public presentation routing; this module does not authorize merchant access."""

DASHBOARDS = {
    "free": ("dashboards/free.py", "Merchant Insights"),
    "advanced": ("dashboards/advanced.py", "Advanced Merchant Dashboard"),
}


def resolve_dashboard(value: str | None) -> str:
    """Keep legacy URLs on free and reject unknown routes rather than execute paths."""
    name = (value or "free").strip().lower()
    if name not in DASHBOARDS:
        raise ValueError("Dashboard tidak dikenal. Gunakan dashboard=free atau dashboard=advanced.")
    return name
