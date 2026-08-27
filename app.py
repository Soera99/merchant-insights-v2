import base64
from datetime import date
from html import escape
from importlib import reload
from pathlib import Path
from textwrap import dedent

import altair as alt
import pandas as pd
import streamlit as st

import data_access as data_access_module


# Streamlit reruns app.py without always re-importing changed local modules.
# Reload the data layer when its schema contract is older than this UI version.
if "age_groups" not in data_access_module.REQUIRED_COLUMNS:
    data_access_module = reload(data_access_module)

DashboardFilters = data_access_module.DashboardFilters
create_dashboard_repository = data_access_module.create_dashboard_repository
validate_frame = data_access_module.validate_frame


# -----------------------------------------------------------------------------
# Streamlit page configuration
# This controls the browser title, icon, width, and initial sidebar state.
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Merchant Insights",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# -----------------------------------------------------------------------------
# App constants and local assets
# Change shared dimensions here instead of searching through the rendering code.
# -----------------------------------------------------------------------------
APP_DIR = Path(__file__).parent
ASSET_DIR = APP_DIR / "assets"
# Change this one value to resize all four Customer Insights cards.
CUSTOMER_INSIGHTS_CARD_HEIGHT = 250

# Shared campaign-chart palette. Updating these values changes both the
# Redemption & Sales Trend chart and the Conversion Funnel together.
CAMPAIGN_CHART_BLUE = "#506ac5"
CAMPAIGN_CHART_LIGHT_BLUE = "#edf1fa"
# Extra tonal steps let multi-series charts stay in the same blue family.
CAMPAIGN_CHART_TONES = ["#506ac5", "#7487d0", "#9daadd", "#c7cfeb"]


# -----------------------------------------------------------------------------
# Image and SVG helpers
# These helpers embed local artwork directly into custom HTML components.
# -----------------------------------------------------------------------------
def image_data_uri(filename: str) -> str:
    """Return a local PNG as an embeddable data URI."""
    encoded = base64.b64encode((ASSET_DIR / filename).read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def trend_chart_data_uri() -> str:
    """Build the responsive trend chart as a self-contained SVG image."""
    x_positions = [137, 287, 437, 587, 737]
    periods = ["1 – 4 Mei", "5 – 11 Mei", "12 – 18 Mei", "19 – 25 Mei", "26 – 31 Mei"]
    blue_tops = [242, 216, 229, 192, 189]
    purple_tops = [171, 138, 155, 116, 115]
    line_y = [119, 87, 126, 84, 87]

    grid = "".join(
        f'<line class="grid" x1="55" y1="{y}" x2="825" y2="{y}"/>'
        for y in [325, 255, 185, 115, 45]
    )
    left_labels = "".join(
        f'<text x="{x}" y="{y}">{label}</text>'
        for x, y, label in [
            (28, 330, "0"),
            (18, 260, "2K"),
            (18, 190, "4K"),
            (18, 120, "6K"),
            (18, 50, "8K"),
        ]
    )
    right_labels = "".join(
        f'<text x="{x}" y="{y}">{label}</text>'
        for x, y, label in [
            (842, 330, "0"),
            (835, 260, "10M"),
            (835, 190, "20M"),
            (835, 120, "30M"),
            (835, 50, "40M"),
        ]
    )
    bars = "".join(
        (
            f'<rect class="blue" x="{x - 32}" y="{blue_y}" '
            f'width="64" height="{325 - blue_y}"/>'
            f'<rect class="purple" x="{x - 32}" y="{purple_y}" '
            f'width="64" height="{blue_y - purple_y}" rx="3"/>'
        )
        for x, blue_y, purple_y in zip(x_positions, blue_tops, purple_tops)
    )
    points = " ".join(f"{x},{y}" for x, y in zip(x_positions, line_y))
    markers = "".join(
        f'<circle class="point" cx="{x}" cy="{y}" r="6"/>'
        for x, y in zip(x_positions, line_y)
    )
    period_labels = "".join(
        f'<text class="period" text-anchor="middle" x="{x}" y="360">{period}</text>'
        for x, period in zip(x_positions, periods)
    )

    svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 880 390">
        <style>
            text {{
                fill: #626875;
                font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                font-size: 13px;
            }}
            .grid {{ stroke: #edf0f5; stroke-width: 1; }}
            .blue {{ fill: #3564e8; }}
            .purple {{ fill: #a895e5; }}
            .average {{
                fill: none;
                stroke: #2f62c9;
                stroke-linecap: round;
                stroke-linejoin: round;
                stroke-width: 3;
            }}
            .point {{ fill: #2f62c9; stroke: #ffffff; stroke-width: 2; }}
        </style>
        {grid}
        {left_labels}
        {right_labels}
        {bars}
        <polyline class="average" points="{points}"/>
        {markers}
        {period_labels}
    </svg>
    """
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


# -----------------------------------------------------------------------------
# KPI presentation configuration
# Backend data supplies values; this mapping controls labels and number formats.
# -----------------------------------------------------------------------------
METRIC_PRESENTATION = {
    "active_campaigns": {
        "label": "Active Campaigns",
        "format": lambda value: f"{value:,.0f}",
    },
    "completed_campaigns": {
        "label": "Completed Campaigns",
        "format": lambda value: f"{value:,.0f}",
    },
    "vouchers_claimed": {
        "label": "Vouchers Claimed",
        "format": lambda value: f"{value:,.0f}",
    },
    "vouchers_redeemed": {
        "label": "Vouchers Redeemed",
        "format": lambda value: f"{value:,.0f}",
    },
    "total_consumers": {
        "label": "Total Consumers",
        "format": lambda value: f"{value:,.0f}",
    },
    "new_consumers": {
        "label": "New Consumers",
        "format": lambda value: f"{value:,.0f}",
    },
    "stores_participated": {
        "label": "Total Stores Participated",
        "format": lambda value: f"{value:,.0f}",
    },
    "redemption_rate": {
        "label": "Redemption Rate",
        "format": lambda value: f"{value:.1f}%",
    },
    "redemption_value": {
        "label": "Total Redemption Value (Rp)",
        "format": lambda value: f"Rp{value / 1_000_000:.1f}M",
    },
}

# Campaign cards reuse the same visual component but have their own backend keys.
CAMPAIGN_METRIC_PRESENTATION = {
    "campaign_views": {
        "label": "Campaign Views",
        "format": lambda value: f"{value:,.0f}",
    },
    "campaign_clicks": {
        "label": "Campaign Clicks",
        "format": lambda value: f"{value:,.0f}",
    },
    "click_through_rate": {
        "label": "Click-Through Rate (CTR)",
        "format": lambda value: f"{value:.1f}%",
    },
    "claim_rate": {
        "label": "Claim Rate",
        "format": lambda value: f"{value:.1f}%",
    },
    "total_vouchers_redeemed": {
        "label": "Total Vouchers Redeemed",
        "format": lambda value: f"{value:,.0f}",
    },
    "total_redemption_value": {
        "label": "Total Redemption Value",
        "format": lambda value: f"Rp{value / 1_000_000:.1f}M",
    },
    "average_transaction_value": {
        "label": "Average Transaction Value",
        "format": lambda value: f"Rp{value / 1_000:.1f}K",
    },
}

CAMPAIGN_TOP_METRICS = [
    "campaign_views",
    "campaign_clicks",
    "click_through_rate",
    "claim_rate",
]
CAMPAIGN_SUMMARY_METRICS = [
    "total_vouchers_redeemed",
    "total_redemption_value",
    "average_transaction_value",
]

# Increment this number whenever the DashboardRepository protocol gains or
# changes a method. It prevents Streamlit from reusing an older cached object.
REPOSITORY_CONTRACT_VERSION = 9


# -----------------------------------------------------------------------------
# Cached data-access wrappers
# The UI calls these functions; the active repository handles mock or real data.
# -----------------------------------------------------------------------------
@st.cache_resource
def get_dashboard_repository(contract_version: int):
    """Create one repository instance per Streamlit process."""
    # The argument intentionally participates in Streamlit's cache key.
    del contract_version
    return create_dashboard_repository()


@st.cache_data(ttl=300)
def load_filter_options() -> dict[str, list[str]]:
    """Load Province-to-City choices from the active backend repository."""
    return get_dashboard_repository(
        REPOSITORY_CONTRACT_VERSION
    ).load_filter_options()


@st.cache_data(ttl=300)
def load_kpi_data(filters: DashboardFilters) -> pd.DataFrame:
    return validate_frame(
        get_dashboard_repository(REPOSITORY_CONTRACT_VERSION).load_kpi_data(
            filters
        ),
        "kpi",
    )


@st.cache_data(ttl=300)
def load_dashboard_data(
    filters: DashboardFilters,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    trend_data, channel_data = get_dashboard_repository(
        REPOSITORY_CONTRACT_VERSION
    ).load_dashboard_data(filters)
    return (
        validate_frame(trend_data, "trend"),
        validate_frame(channel_data, "channel"),
    )


@st.cache_data(ttl=300)
def load_campaign_performance_data(
    filters: DashboardFilters,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load campaign cards and funnel stages for the selected filters."""
    campaign_metrics, funnel_data = (
        get_dashboard_repository(
            REPOSITORY_CONTRACT_VERSION
        ).load_campaign_performance_data(filters)
    )
    return (
        validate_frame(campaign_metrics, "campaign_metrics"),
        validate_frame(funnel_data, "campaign_funnel"),
    )


@st.cache_data(ttl=300)
def load_product_performance_data(
    filters: DashboardFilters,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    category_data, sampled_products, redeemed_products = (
        get_dashboard_repository(
            REPOSITORY_CONTRACT_VERSION
        ).load_product_performance_data(filters)
    )
    return (
        validate_frame(category_data, "category_performance"),
        validate_frame(sampled_products, "sampled_products"),
        validate_frame(redeemed_products, "redeemed_products"),
    )


@st.cache_data(ttl=300)
def load_product_detail_data(
    filters: DashboardFilters,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    category_overview, hourly_redemptions = (
        get_dashboard_repository(
            REPOSITORY_CONTRACT_VERSION
        ).load_product_detail_data(filters)
    )
    return (
        validate_frame(category_overview, "category_overview"),
        validate_frame(hourly_redemptions, "hourly_redemptions"),
    )


@st.cache_data(ttl=300)
def load_merchant_performance_data(
    filters: DashboardFilters,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    outlets, campaigns, locations = (
        get_dashboard_repository(
            REPOSITORY_CONTRACT_VERSION
        ).load_merchant_performance_data(filters)
    )
    return (
        validate_frame(outlets, "leaderboard"),
        validate_frame(campaigns, "leaderboard"),
        validate_frame(locations, "leaderboard"),
    )


@st.cache_data(ttl=300)
def load_customer_insights_data(
    filters: DashboardFilters,
) -> tuple[
    pd.DataFrame,
    dict[str, float | str],
    pd.DataFrame,
    pd.DataFrame,
]:
    customer_segments, loyalty, gender, age_groups = (
        get_dashboard_repository(
            REPOSITORY_CONTRACT_VERSION
        ).load_customer_insights_data(filters)
    )
    return (
        validate_frame(customer_segments, "customer_segments"),
        loyalty,
        validate_frame(gender, "gender"),
        validate_frame(age_groups, "age_groups"),
    )


# -----------------------------------------------------------------------------
# Reusable KPI card renderer
# Both overview and campaign sections share this HTML to stay visually aligned.
# -----------------------------------------------------------------------------
def metric_card_html(metric, presentation: dict[str, object]) -> str:
    """Return one KPI card using a repository row and presentation settings."""
    change_sign = "+" if metric.change_pct >= 0 else ""
    change_class = "" if metric.change_pct >= 0 else " negative"
    change_arrow = "↑" if metric.change_pct >= 0 else "↓"
    label = str(presentation["label"])
    formatter = presentation["format"]
    formatted_value = formatter(metric.value)
    return dedent(
        f"""
        <article class="kpi-card" aria-label="{escape(label)}">
            <div class="kpi-content">
                <div class="kpi-label">{escape(label)}</div>
                <div class="kpi-value-row">
                    <div class="kpi-value">{escape(str(formatted_value))}</div>
                    <div class="kpi-change{change_class}">
                        <span aria-hidden="true">{change_arrow}</span>
                        {change_sign}{metric.change_pct:.1f}%
                    </div>
                </div>
                <div class="kpi-comparison">
                    {escape(str(metric.comparison_label))}
                </div>
            </div>
        </article>
        """
    ).strip()


# -----------------------------------------------------------------------------
# Global dashboard styling
# CSS defines shared typography, cards, responsive layouts, and chart spacing.
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
        :root {
            --ink: #151729;
            --muted: #858a9c;
            --brand: #5f5bd8;
            --brand-soft: #f1f0ff;
            --positive: #2dbb78;
            --border: #e9eaf0;
        }

        .stApp {
            background: #ffffff;
        }

        [data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stSidebarCollapsedControl"] {
            display: none;
        }

        .block-container {
            max-width: 1720px;
            padding: 2.25rem 2rem 3rem;
        }

        .dashboard-title {
            color: var(--ink);
            font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont,
                "Segoe UI", sans-serif;
            font-size: 1.65rem;
            font-weight: 700;
            letter-spacing: -0.03em;
            line-height: 1.2;
        }

        .dashboard-description {
            margin-top: 0.42rem;
            color: #787d87;
            font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont,
                "Segoe UI", sans-serif;
            font-size: 0.84rem;
            font-weight: 400;
            line-height: 1.4;
        }

        .dashboard-header-spacer {
            height: 1.65rem;
        }

        .dashboard-filter-heading {
            margin: 1.4rem 0 0.55rem;
            color: #787d87;
            font-size: 0.76rem;
            font-weight: 600;
        }

        div[data-testid="stSelectbox"] [data-baseweb="select"] > div,
        div[data-testid="stDateInput"] {
            width: 100%;
        }

        div[data-testid="stSelectbox"] [data-baseweb="select"] > div,
        div[data-testid="stDateInput"] [data-baseweb="input"] {
            background: #ffffff !important;
            border: 1px solid var(--border) !important;
            border-radius: 12px !important;
            box-shadow: 0 2px 7px rgba(25, 28, 55, 0.035);
        }

        div[data-testid="stSelectbox"] [data-baseweb="select"] [value] {
            color: #424754 !important;
            opacity: 1 !important;
        }

        div[data-testid="stSelectbox"] [data-baseweb="select"] svg {
            color: #787d87 !important;
            fill: #787d87 !important;
        }

        div[data-testid="stDateInput"] input {
            background: transparent !important;
            color: #424754;
            font-size: 0.8rem;
        }

        div[data-testid="stDateInput"] svg {
            color: #787d87 !important;
            fill: #787d87 !important;
        }

        div[data-testid="stSelectbox"] label,
        div[data-testid="stDateInput"] label {
            color: #4f5563 !important;
            font-size: 0.78rem !important;
            font-weight: 600 !important;
        }

        .kpi-section {
            width: 100%;
        }

        .kpi-heading {
            color: var(--ink);
            font-family: "Source Sans", sans-serif;
            font-size: 1.15rem;
            font-weight: 650;
            letter-spacing: -0.02em;
            line-height: 1.25;
            margin: 0 0 1.45rem;
        }

        .kpi-grid {
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }

        .kpi-row {
            display: grid;
            gap: 1rem;
        }

        .kpi-row-four {
            grid-template-columns: repeat(4, minmax(0, 1fr));
        }

        .kpi-row-five {
            grid-template-columns: repeat(5, minmax(0, 1fr));
        }

        .kpi-card {
            box-sizing: border-box;
            min-height: 166px;
            padding: 1.4rem 1.5rem;
            background: #f7f8fa;
            border: 1px solid #f2f3f6;
            border-radius: 24px;
            box-shadow: none;
            transition: border-color 160ms ease, box-shadow 160ms ease,
                transform 160ms ease;
        }

        .kpi-card:hover {
            border-color: #dcdde8;
            box-shadow: 0 10px 24px rgba(25, 28, 55, 0.075);
            transform: translateY(-2px);
        }

        .kpi-content {
            min-width: 0;
        }

        .kpi-label {
            color: #374151;
            font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont,
                "Segoe UI", sans-serif;
            font-size: 0.9rem;
            font-weight: 650;
            line-height: 1.3;
            margin: 0;
            white-space: nowrap;
        }

        .kpi-value-row {
            display: flex;
            align-items: center;
            gap: 0.8rem;
            margin-top: 0.9rem;
        }

        .kpi-value {
            color: var(--ink);
            font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont,
                "Segoe UI", sans-serif;
            font-size: clamp(1.7rem, 2vw, 2.2rem);
            font-weight: 760;
            letter-spacing: -0.035em;
            line-height: 1.1;
            margin: 0;
            white-space: nowrap;
        }

        .kpi-change {
            display: inline-flex;
            align-items: center;
            gap: 0.32rem;
            padding: 0.42rem 0.66rem;
            border-radius: 999px;
            background: #eafbf2;
            color: #20bd67;
            font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont,
                "Segoe UI", sans-serif;
            font-size: 0.88rem;
            font-weight: 700;
            line-height: 1.25;
            margin: 0;
            white-space: nowrap;
        }

        .kpi-change.negative {
            background: #fff0f0;
            color: #e05252;
        }

        .kpi-comparison {
            color: #a1a6b2;
            font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont,
                "Segoe UI", sans-serif;
            font-size: 0.8rem;
            font-weight: 400;
            line-height: 1.25;
            margin: 1rem 0 0;
        }

        .campaign-performance-heading {
            color: var(--ink);
            font-family: "Source Sans", sans-serif;
            font-size: 1.15rem;
            font-weight: 650;
            letter-spacing: -0.02em;
            line-height: 1.25;
            margin: 0 0 1.15rem;
        }

        .campaign-metric-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 1rem;
            margin-bottom: 1rem;
        }

        .campaign-metric-grid .kpi-card,
        .campaign-summary-grid .kpi-card {
            min-height: 138px;
            padding: 1.1rem 1.2rem;
            border-radius: 20px;
        }

        .campaign-metric-grid .kpi-label,
        .campaign-summary-grid .kpi-label {
            font-size: 0.82rem;
        }

        .campaign-metric-grid .kpi-value,
        .campaign-summary-grid .kpi-value {
            font-size: clamp(1.45rem, 1.8vw, 1.85rem);
        }

        .campaign-metric-grid .kpi-value-row,
        .campaign-summary-grid .kpi-value-row {
            margin-top: 0.7rem;
        }

        .campaign-metric-grid .kpi-comparison,
        .campaign-summary-grid .kpi-comparison {
            margin-top: 0.78rem;
            font-size: 0.75rem;
        }

        .campaign-summary-grid {
            width: min(100%, 850px);
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 1rem;
            margin: 1rem auto 0;
        }

        .campaign-chart-title {
            margin-bottom: 0.45rem;
        }

        .analytics-section {
            width: 100%;
            margin-top: 1.25rem;
            font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont,
                "Segoe UI", sans-serif;
        }

        .analytics-grid {
            display: grid;
            grid-template-columns: minmax(0, 3fr) minmax(300px, 1fr);
            gap: 1rem;
        }

        .analytics-card {
            box-sizing: border-box;
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 20px;
            box-shadow: 0 2px 7px rgba(25, 28, 55, 0.035);
        }

        .analytics-title {
            color: var(--ink);
            font-size: 1.15rem;
            font-weight: 650;
            letter-spacing: -0.02em;
            line-height: 1.25;
        }

        .trend-card {
            min-height: 460px;
            padding: 1.55rem 1.55rem 1.35rem;
        }

        .trend-card-body {
            display: grid;
            grid-template-columns: minmax(0, 4fr) minmax(210px, 1.1fr);
            gap: 1.4rem;
            margin-top: 1.15rem;
        }

        .trend-chart-column {
            min-width: 0;
        }

        .chart-legend {
            display: flex;
            align-items: center;
            justify-content: center;
            flex-wrap: wrap;
            gap: 1.6rem;
            margin-bottom: 0.45rem;
            color: #555b68;
            font-size: 0.78rem;
        }

        .legend-item {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            white-space: nowrap;
        }

        .legend-swatch {
            width: 24px;
            height: 12px;
            border-radius: 2px;
        }

        .legend-swatch.blue {
            background: #3564d8;
        }

        .legend-swatch.purple {
            background: #9b85df;
        }

        .legend-line {
            position: relative;
            width: 25px;
            height: 2px;
            background: #2f62c9;
        }

        .legend-line::after {
            position: absolute;
            top: 50%;
            left: 50%;
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: #2f62c9;
            content: "";
            transform: translate(-50%, -50%);
        }

        .trend-chart {
            display: block;
            width: 100%;
            height: auto;
            overflow: visible;
        }

        .trend-chart text {
            fill: #626875;
            font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont,
                "Segoe UI", sans-serif;
            font-size: 13px;
        }

        .trend-chart .grid-line {
            stroke: #edf0f5;
            stroke-width: 1;
        }

        .trend-chart .bar-blue {
            fill: #3564e8;
        }

        .trend-chart .bar-purple {
            fill: #a895e5;
        }

        .trend-chart .average-line {
            fill: none;
            stroke: #2f62c9;
            stroke-linecap: round;
            stroke-linejoin: round;
            stroke-width: 3;
        }

        .trend-chart .average-point {
            fill: #2f62c9;
            stroke: #ffffff;
            stroke-width: 2;
        }

        .trend-summary {
            display: flex;
            flex-direction: column;
            justify-content: center;
            padding: 0.2rem 0;
        }

        .summary-item {
            padding: 1.15rem 0;
            border-bottom: 1px solid var(--border);
        }

        .summary-item:last-child {
            border-bottom: 0;
        }

        .summary-value {
            color: var(--ink);
            font-size: clamp(1.5rem, 2vw, 2rem);
            font-weight: 750;
            letter-spacing: -0.03em;
            line-height: 1.15;
            white-space: nowrap;
        }

        .summary-label {
            color: #787d87;
            font-size: 0.8rem;
            font-weight: 400;
            line-height: 1.3;
            margin-top: 0.55rem;
        }

        .native-chart-title {
            margin: 0.15rem 0 0.45rem;
        }

        .section-spacer {
            height: 1.5rem;
        }

        .trend-chart-spacer {
            height: 0.75rem;
        }

        /* Vega-Lite emits a zero-width stroke for the custom line legend.
           This restores the intended campaign-blue border on that square. */
        div[data-testid="stVegaLiteChart"]
            path[stroke="#506ac5"][stroke-width="0"] {
            stroke-width: 2px;
        }

        div[data-testid="stVerticalBlock"]:has(
            > div[data-testid="stElementContainer"] .native-chart-title
        ) {
            padding: 1.35rem !important;
            overflow: hidden !important;
            background: #ffffff !important;
            border: 1px solid var(--border) !important;
            border-radius: 20px !important;
            box-shadow: 0 2px 7px rgba(25, 28, 55, 0.035) !important;
        }

        .native-summary {
            display: flex;
            min-height: 365px;
            flex-direction: column;
            justify-content: center;
        }

        .native-summary .summary-item {
            padding: 1.25rem 0;
        }

        .channel-card {
            min-height: 460px;
            padding: 1.55rem 1.6rem 1.4rem;
        }

        .donut-wrap {
            position: relative;
            width: min(220px, 76%);
            aspect-ratio: 1;
            margin: 1.55rem auto 1.35rem;
        }

        .donut-chart {
            position: absolute;
            inset: 0;
            border-radius: 50%;
            background: conic-gradient(
                #365bc8 0% 48%,
                #765acb 48% 76%,
                #fb9844 76% 92%,
                #3aaed1 92% 100%
            );
            box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.12);
        }

        .donut-chart::after {
            position: absolute;
            inset: 29%;
            border-radius: 50%;
            background: #ffffff;
            content: "";
        }

        .donut-percent {
            position: absolute;
            z-index: 1;
            color: #ffffff;
            font-size: 0.82rem;
            font-weight: 700;
            transform: translate(-50%, -50%);
        }

        .donut-percent.p48 { left: 81%; top: 51%; }
        .donut-percent.p28 { left: 32%; top: 78%; }
        .donut-percent.p16 { left: 19%; top: 37%; }
        .donut-percent.p8  { left: 44%; top: 15%; }

        .channel-list {
            display: grid;
            gap: 0.85rem;
        }

        .channel-row {
            display: grid;
            grid-template-columns: 10px 1fr auto;
            align-items: center;
            gap: 0.7rem;
            color: #454b59;
            font-size: 0.84rem;
        }

        .channel-dot {
            width: 9px;
            height: 9px;
            border-radius: 50%;
        }

        .channel-dot.blue { background: #365bc8; }
        .channel-dot.purple { background: #765acb; }
        .channel-dot.orange { background: #fb9844; }
        .channel-dot.cyan { background: #3aaed1; }

        .channel-value {
            color: #555b68;
            font-variant-numeric: tabular-nums;
        }

        .product-section-heading {
            margin: 0 0 1rem;
            font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont,
                "Segoe UI", sans-serif;
        }

        .product-section-title {
            color: var(--ink);
            font-size: 1.15rem;
            font-weight: 650;
            letter-spacing: -0.02em;
            line-height: 1.25;
        }

        .product-section-description {
            margin-top: 0.32rem;
            color: #787d87;
            font-size: 0.82rem;
            font-weight: 400;
            line-height: 1.35;
        }

        .product-card-title {
            margin-bottom: 0.75rem;
        }

        .customer-card-title {
            margin-bottom: 0.2rem;
        }

        /* Adds breathing room below selected titles while keeping the fixed
           card height and moving their visual content closer to the bottom. */
        .customer-content-offset {
            height: 0.55rem;
        }

        div[data-testid="stVerticalBlock"]:has(
            > div[data-testid="stElementContainer"] .customer-card-title
        ) {
            gap: 0.35rem !important;
        }

        .product-list {
            display: grid;
            margin-top: 0.3rem;
            font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont,
                "Segoe UI", sans-serif;
        }

        .product-row {
            display: grid;
            grid-template-columns: 1.6rem minmax(0, 1fr) auto;
            align-items: center;
            min-height: 3.65rem;
            gap: 0.55rem;
            border-bottom: 1px solid var(--border);
        }

        .product-rank {
            color: #787d87;
            font-size: 0.82rem;
            font-variant-numeric: tabular-nums;
        }

        .product-name {
            min-width: 0;
            overflow: hidden;
            color: #303441;
            font-size: 0.86rem;
            font-weight: 500;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .product-count {
            color: #787d87;
            font-size: 0.8rem;
            font-variant-numeric: tabular-nums;
            white-space: nowrap;
        }

        .merchant-list {
            display: grid;
            margin-top: 0.25rem;
            font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont,
                "Segoe UI", sans-serif;
        }

        .merchant-row {
            display: grid;
            grid-template-columns: 1.5rem minmax(0, 1fr) auto;
            align-items: center;
            min-height: 3.55rem;
            gap: 0.55rem;
            border-bottom: 1px solid var(--border);
        }

        .merchant-row:last-child {
            border-bottom: 0;
        }

        .merchant-rank {
            color: #787d87;
            font-size: 0.8rem;
            font-variant-numeric: tabular-nums;
        }

        .merchant-name {
            min-width: 0;
            color: #303441;
            font-size: 0.79rem;
            font-weight: 500;
            line-height: 1.25;
            white-space: normal;
        }

        .merchant-count {
            color: #4a66bf;
            font-size: 0.76rem;
            font-variant-numeric: tabular-nums;
            white-space: nowrap;
        }

        .location-pin {
            position: relative;
            display: inline-flex;
            width: 1.05rem;
            height: 1.05rem;
            align-items: center;
            justify-content: center;
            color: #4f70d7;
        }

        .location-pin::before {
            width: 0.68rem;
            height: 0.68rem;
            border: 2px solid currentColor;
            border-radius: 50% 50% 50% 0;
            content: "";
            transform: rotate(-45deg);
        }

        .location-pin::after {
            position: absolute;
            width: 0.18rem;
            height: 0.18rem;
            border-radius: 50%;
            background: currentColor;
            content: "";
            transform: translateY(-1px);
        }

        .customer-mix-legend {
            display: flex;
            min-height: 160px;
            flex-direction: column;
            justify-content: flex-start;
            gap: 1.05rem;
            padding-top: 0.55rem;
            font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont,
                "Segoe UI", sans-serif;
        }

        .customer-legend-item {
            display: grid;
            grid-template-columns: 9px minmax(0, 1fr);
            gap: 0.55rem;
        }

        .customer-legend-dot {
            width: 8px;
            height: 8px;
            margin-top: 0.26rem;
            border-radius: 50%;
            box-shadow: inset 0 0 0 1px rgba(74, 102, 191, 0.12);
        }

        .customer-legend-name {
            color: #424754;
            font-size: 0.78rem;
            font-weight: 500;
            line-height: 1.3;
        }

        .customer-legend-detail {
            margin-top: 0.38rem;
            color: #303441;
            font-size: 0.76rem;
            font-variant-numeric: tabular-nums;
            font-weight: 600;
            white-space: nowrap;
        }

        .loyalty-metrics {
            display: flex;
            min-height: 178px;
            flex-direction: column;
            justify-content: flex-start;
            font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont,
                "Segoe UI", sans-serif;
        }

        .loyalty-metric {
            padding: 0.35rem 0 0.85rem;
            border-bottom: 1px solid var(--border);
        }

        .loyalty-metric:last-child {
            padding: 0.85rem 0 0;
            border-bottom: 0;
        }

        .customer-insight-value {
            color: var(--ink);
            font-size: 1.85rem;
            font-variant-numeric: tabular-nums;
            font-weight: 700;
            letter-spacing: -0.03em;
            line-height: 1.1;
        }

        .customer-insight-description {
            margin-top: 0.55rem;
            color: #787d87;
            font-size: 0.76rem;
            line-height: 1.35;
        }

        .gender-breakdown,
        .payment-breakdown {
            display: grid;
            font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont,
                "Segoe UI", sans-serif;
        }

        .gender-breakdown {
            gap: 0.35rem;
            padding-top: 0.05rem;
        }

        .gender-donut-legend {
            display: flex;
            min-height: 145px;
            flex-direction: column;
            justify-content: center;
            gap: 0.6rem;
            font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont,
                "Segoe UI", sans-serif;
        }

        .age-group-list {
            display: grid;
            margin-top: 0.55rem;
            font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont,
                "Segoe UI", sans-serif;
        }

        .age-group-row {
            display: grid;
            grid-template-columns: minmax(88px, 1fr) minmax(58px, 0.85fr) auto;
            align-items: center;
            min-height: 2.55rem;
            gap: 0.55rem;
            border-bottom: 1px solid var(--border);
        }

        .age-group-row:last-child {
            border-bottom: 0;
        }

        .age-group-name {
            color: #303441;
            font-size: 0.7rem;
            font-weight: 650;
            line-height: 1.2;
        }

        .age-group-range {
            display: block;
            margin-top: 0.15rem;
            color: #858c99;
            font-size: 0.61rem;
            font-weight: 400;
            white-space: nowrap;
        }

        .age-group-track {
            height: 8px;
            overflow: hidden;
            border-radius: 999px;
            background: #edf1fa;
        }

        .age-group-fill {
            display: block;
            height: 100%;
            border-radius: inherit;
            background: #506ac5;
        }

        .age-group-percentage {
            color: #4a66bf;
            font-size: 0.68rem;
            font-variant-numeric: tabular-nums;
            font-weight: 650;
            white-space: nowrap;
        }

        .age-group-percentage.placeholder {
            color: #9aa1af;
        }

        .insight-progress-label {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.75rem;
            color: #424754;
            font-size: 0.78rem;
            line-height: 1.3;
        }

        .insight-progress-value {
            color: #303441;
            font-variant-numeric: tabular-nums;
            font-weight: 600;
        }

        .insight-progress-track {
            height: 7px;
            margin-top: 0.48rem;
            overflow: hidden;
            border-radius: 999px;
            background: #e7e2f8;
        }

        .insight-progress-fill {
            height: 100%;
            border-radius: inherit;
            background: #3564e8;
        }

        .top-age-group {
            margin-top: 0.2rem;
            padding-top: 0.58rem;
            border-top: 1px solid var(--border);
        }

        .top-age-label {
            color: #787d87;
            font-size: 0.72rem;
        }

        .top-age-value {
            margin-top: 0.22rem;
            color: #303441;
            font-size: 0.95rem;
            font-variant-numeric: tabular-nums;
            font-weight: 600;
        }

        .payment-breakdown {
            gap: 0.78rem;
            padding-top: 0.38rem;
        }

        .payment-row {
            display: grid;
            grid-template-columns: 5.2rem minmax(0, 1fr) 2.2rem;
            align-items: center;
            gap: 0.65rem;
        }

        .payment-method,
        .payment-percentage {
            color: #555b68;
            font-size: 0.75rem;
        }

        .payment-percentage {
            font-variant-numeric: tabular-nums;
            font-weight: 600;
            text-align: right;
        }

        .payment-row .insight-progress-track {
            margin-top: 0;
        }

        .product-detail-spacer {
            height: 1rem;
        }

        .category-overview-wrap {
            width: 100%;
            overflow-x: auto;
            font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont,
                "Segoe UI", sans-serif;
        }

        .category-overview-table {
            min-width: 590px;
        }

        .category-overview-row {
            display: grid;
            grid-template-columns:
                minmax(0, 0.9fr)
                minmax(0, 1.6fr)
                minmax(0, 1.65fr)
                minmax(0, 1.15fr)
                minmax(0, 0.95fr);
            align-items: center;
            min-height: 3.15rem;
            border-bottom: 1px solid var(--border);
            column-gap: 0.5rem;
        }

        .category-overview-row:last-child {
            border-bottom: 0;
        }

        .category-overview-header {
            min-height: 2.65rem;
            color: #555b68;
            font-size: 0.69rem;
            font-weight: 600;
        }

        .category-overview-cell {
            min-width: 0;
            color: #424754;
            font-size: 0.72rem;
            font-variant-numeric: tabular-nums;
        }

        .category-overview-category {
            color: #303441;
            font-weight: 600;
        }

        .category-overview-rate {
            padding-right: 0.25rem;
            text-align: right;
        }

        .category-metric {
            display: flex;
            align-items: center;
            min-width: 0;
            gap: 0.45rem;
        }

        .category-metric-value {
            flex: 0 0 auto;
            white-space: nowrap;
        }

        .category-inline-track {
            width: 48px;
            height: 6px;
            overflow: hidden;
            flex: 0 0 48px;
            border-radius: 999px;
            background: #f0f1f5;
        }

        .category-inline-fill {
            height: 100%;
            border-radius: inherit;
        }

        .category-inline-fill.blue {
            background: #506ac5;
        }

        .category-inline-fill.purple {
            background: #edf1fa;
        }

        .category-compact-table {
            width: 100%;
            font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont,
                "Segoe UI", sans-serif;
        }

        .category-compact-row {
            display: grid;
            grid-template-columns: minmax(110px, 0.85fr) minmax(220px, 1.55fr);
            align-items: center;
            min-height: 3.15rem;
            gap: 0.9rem;
            border-bottom: 1px solid var(--border);
        }

        .category-compact-row:last-child {
            border-bottom: 0;
        }

        .category-compact-header {
            min-height: 2.65rem;
            color: #6d7482;
            font-size: 0.72rem;
            font-weight: 600;
        }

        .category-compact-name {
            color: #303441;
            font-size: 0.77rem;
            font-weight: 600;
        }

        .category-compact-metric {
            display: grid;
            grid-template-columns: auto minmax(70px, 1fr);
            align-items: center;
            gap: 0.7rem;
            color: #737b8b;
            font-size: 0.74rem;
            font-variant-numeric: tabular-nums;
        }

        .category-compact-track {
            height: 7px;
            overflow: hidden;
            border-radius: 999px;
            background: #f0f2f7;
        }

        .category-compact-fill {
            display: block;
            height: 100%;
            border-radius: inherit;
            background: #506ac5;
        }

        .product-channel-legend {
            display: grid;
            align-content: center;
            gap: 0.78rem;
            min-height: 235px;
            font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont,
                "Segoe UI", sans-serif;
        }

        .product-channel-row {
            display: grid;
            grid-template-columns: 10px minmax(72px, 1fr) auto;
            align-items: center;
            gap: 0.55rem;
            color: #3f4654;
            font-size: 0.75rem;
        }

        .product-channel-dot {
            width: 9px;
            height: 9px;
            border-radius: 50%;
        }

        .product-channel-value {
            color: #303744;
            font-variant-numeric: tabular-nums;
            font-weight: 600;
            white-space: nowrap;
        }

        @media (max-width: 1320px) {
            .kpi-row-four,
            .kpi-row-five {
                grid-template-columns: repeat(3, minmax(0, 1fr));
            }

            .campaign-metric-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }

        @media (max-width: 1080px) {
            .analytics-grid {
                grid-template-columns: 1fr;
            }

            .channel-card {
                min-height: auto;
            }

            .donut-wrap {
                width: min(220px, 55%);
            }
        }

        @media (max-width: 820px) {
            .block-container {
                padding: 1.5rem 1rem 2rem;
            }

            .kpi-row-four,
            .kpi-row-five {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }

            .trend-card-body {
                grid-template-columns: 1fr;
            }

            .trend-summary {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 0.8rem;
            }

            .summary-item {
                padding: 0.9rem 0;
                border-right: 1px solid var(--border);
                border-bottom: 0;
            }

            .summary-item:last-child {
                border-right: 0;
            }
        }

        @media (max-width: 560px) {
            .kpi-heading {
                font-size: 1.15rem;
            }

            .kpi-row-four,
            .kpi-row-five {
                grid-template-columns: 1fr;
            }

            .campaign-metric-grid,
            .campaign-summary-grid {
                grid-template-columns: 1fr;
            }

            .kpi-card {
                min-height: 150px;
            }

            .trend-card,
            .channel-card {
                padding: 1.2rem 1rem;
            }

            .chart-legend {
                justify-content: flex-start;
                gap: 0.75rem 1rem;
            }

            .trend-summary {
                grid-template-columns: 1fr;
            }

            .summary-item {
                border-right: 0;
                border-bottom: 1px solid var(--border);
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# Dashboard header and global filters
# Province controls the City choices, and all three filters reach every query.
# -----------------------------------------------------------------------------
st.html(
    """
    <div>
        <div class="dashboard-title">Business Insight Dashboard</div>
        <div class="dashboard-description">
            Monitor campaign, voucher, product, and merchant performance
            in real-time.
        </div>
    </div>
    """
)

filter_options = load_filter_options()
if not filter_options or any(not cities for cities in filter_options.values()):
    raise ValueError("Filter options must contain at least one Province and City")
province_column, city_column, date_column = st.columns(
    [1, 1, 1.35],
    gap="medium",
    vertical_alignment="bottom",
)

with province_column:
    selected_province = st.selectbox(
        "Province",
        options=list(filter_options),
        key="dashboard_province",
    )

with city_column:
    selected_city = st.selectbox(
        "City",
        options=filter_options[selected_province],
        key=f"dashboard_city_{selected_province}",
    )

with date_column:
    selected_date_range = st.date_input(
        "Date",
        value=(date(2026, 8, 1), date(2026, 8, 18)),
        format="DD/MM/YYYY",
        key="dashboard_date_range",
    )

if isinstance(selected_date_range, (tuple, list)):
    dashboard_start_date = selected_date_range[0]
    dashboard_end_date = (
        selected_date_range[1]
        if len(selected_date_range) > 1
        else dashboard_start_date
    )
else:
    dashboard_start_date = selected_date_range
    dashboard_end_date = selected_date_range

dashboard_filters = DashboardFilters(
    province=selected_province,
    city=selected_city,
    start_date=dashboard_start_date,
    end_date=dashboard_end_date,
)

# -----------------------------------------------------------------------------
# Key Performance Overview
# Values come from the repository; the UI only formats and arranges the cards.
# -----------------------------------------------------------------------------
kpi_data = load_kpi_data(dashboard_filters)
kpi_rows = {row.metric_key: row for row in kpi_data.itertuples(index=False)}
cards = []
for metric_key, presentation in METRIC_PRESENTATION.items():
    if metric_key not in kpi_rows:
        raise ValueError(f"KPI data is missing metric_key: {metric_key}")
    cards.append(metric_card_html(kpi_rows[metric_key], presentation))

st.html('<div class="dashboard-header-spacer" aria-hidden="true"></div>')

st.markdown(
    dedent(
        f"""
    <main class="kpi-section">
        <div class="analytics-title kpi-heading" role="heading" aria-level="1">
            Key Performance Overview
        </div>
        <div class="kpi-grid">
            <div class="kpi-row kpi-row-four">
                {''.join(cards[:4])}
            </div>
            <div class="kpi-row kpi-row-five">
                {''.join(cards[4:])}
            </div>
        </div>
    </main>
    """
    ),
    unsafe_allow_html=True,
)


if False:  # Legacy static prototype kept temporarily for design reference.
    st.html(
    dedent(
        f"""
        <section class="analytics-section" aria-label="Redemption and sales analytics">
            <div class="analytics-grid">
                <article class="analytics-card trend-card">
                    <div class="analytics-title" role="heading" aria-level="2">
                        Redemption &amp; Sales Trend
                    </div>
                    <div class="trend-card-body">
                        <div class="trend-chart-column">
                            <div class="chart-legend" aria-label="Chart legend">
                                <span class="legend-item">
                                    <span class="legend-swatch blue"></span>
                                    Voucher Redeemed
                                </span>
                                <span class="legend-item">
                                    <span class="legend-swatch purple"></span>
                                    Redemption Value (Rp)
                                </span>
                                <span class="legend-item">
                                    <span class="legend-line"></span>
                                    Average Transaction Value (Rp)
                                </span>
                            </div>
                            <img
                                class="trend-chart"
                                src="{trend_chart_uri}"
                                alt="Voucher redemption and sales trend from 1 to 31 May"
                            />
                            <svg
                                class="trend-chart"
                                viewBox="0 0 880 390"
                                role="img"
                                aria-label="Voucher redemption and sales trend from 1 to 31 May"
                            >
                                <line class="grid-line" x1="55" y1="325" x2="825" y2="325"/>
                                <line class="grid-line" x1="55" y1="255" x2="825" y2="255"/>
                                <line class="grid-line" x1="55" y1="185" x2="825" y2="185"/>
                                <line class="grid-line" x1="55" y1="115" x2="825" y2="115"/>
                                <line class="grid-line" x1="55" y1="45" x2="825" y2="45"/>

                                <text x="28" y="330">0</text>
                                <text x="18" y="260">2K</text>
                                <text x="18" y="190">4K</text>
                                <text x="18" y="120">6K</text>
                                <text x="18" y="50">8K</text>

                                <text x="842" y="330">0</text>
                                <text x="835" y="260">10M</text>
                                <text x="835" y="190">20M</text>
                                <text x="835" y="120">30M</text>
                                <text x="835" y="50">40M</text>

                                <rect class="bar-blue" x="105" y="242" width="64" height="83">
                                    <title>1–4 May: 2,400 vouchers</title>
                                </rect>
                                <rect class="bar-purple" x="105" y="171" width="64" height="71" rx="3">
                                    <title>1–4 May: Rp 10.2M redemption value</title>
                                </rect>

                                <rect class="bar-blue" x="255" y="216" width="64" height="109">
                                    <title>5–11 May: 3,100 vouchers</title>
                                </rect>
                                <rect class="bar-purple" x="255" y="138" width="64" height="78" rx="3">
                                    <title>5–11 May: Rp 11.1M redemption value</title>
                                </rect>

                                <rect class="bar-blue" x="405" y="229" width="64" height="96">
                                    <title>12–18 May: 2,750 vouchers</title>
                                </rect>
                                <rect class="bar-purple" x="405" y="155" width="64" height="74" rx="3">
                                    <title>12–18 May: Rp 10.6M redemption value</title>
                                </rect>

                                <rect class="bar-blue" x="555" y="192" width="64" height="133">
                                    <title>19–25 May: 3,800 vouchers</title>
                                </rect>
                                <rect class="bar-purple" x="555" y="116" width="64" height="76" rx="3">
                                    <title>19–25 May: Rp 10.9M redemption value</title>
                                </rect>

                                <rect class="bar-blue" x="705" y="189" width="64" height="136">
                                    <title>26–31 May: 3,900 vouchers</title>
                                </rect>
                                <rect class="bar-purple" x="705" y="115" width="64" height="74" rx="3">
                                    <title>26–31 May: Rp 10.7M redemption value</title>
                                </rect>

                                <path
                                    class="average-line"
                                    d="M137 119 L287 87 L437 126 L587 84 L737 87"
                                />
                                <circle class="average-point" cx="137" cy="119" r="6">
                                    <title>Average transaction: Rp 7,950</title>
                                </circle>
                                <circle class="average-point" cx="287" cy="87" r="6">
                                    <title>Average transaction: Rp 8,510</title>
                                </circle>
                                <circle class="average-point" cx="437" cy="126" r="6">
                                    <title>Average transaction: Rp 7,820</title>
                                </circle>
                                <circle class="average-point" cx="587" cy="84" r="6">
                                    <title>Average transaction: Rp 8,580</title>
                                </circle>
                                <circle class="average-point" cx="737" cy="87" r="6">
                                    <title>Average transaction: Rp 8,550</title>
                                </circle>

                                <text text-anchor="middle" x="137" y="360">1 – 4 Mei</text>
                                <text text-anchor="middle" x="287" y="360">5 – 11 Mei</text>
                                <text text-anchor="middle" x="437" y="360">12 – 18 Mei</text>
                                <text text-anchor="middle" x="587" y="360">19 – 25 Mei</text>
                                <text text-anchor="middle" x="737" y="360">26 – 31 Mei</text>
                            </svg>
                        </div>
                        <aside class="trend-summary" aria-label="Trend totals">
                            <div class="summary-item">
                                <div class="summary-value">18,746</div>
                                <div class="summary-label">Total Voucher Redeemed</div>
                            </div>
                            <div class="summary-item">
                                <div class="summary-value">Rp 156.8M</div>
                                <div class="summary-label">Total Redemption Value</div>
                            </div>
                            <div class="summary-item">
                                <div class="summary-value">Rp 8,362</div>
                                <div class="summary-label">Average Transaction Value</div>
                            </div>
                        </aside>
                    </div>
                </article>

                <article class="analytics-card channel-card">
                    <div class="analytics-title" role="heading" aria-level="2">
                        Redemption by Channel
                    </div>
                    <div
                        class="donut-wrap"
                        role="img"
                        aria-label="In-store 48 percent, Klikko-Hub 28 percent, QR Payment 16 percent, Other 8 percent"
                    >
                        <div class="donut-chart"></div>
                        <span class="donut-percent p48">48%</span>
                        <span class="donut-percent p28">28%</span>
                        <span class="donut-percent p16">16%</span>
                        <span class="donut-percent p8">8%</span>
                    </div>
                    <div class="channel-list">
                        <div class="channel-row">
                            <span class="channel-dot blue"></span>
                            <span>In-store</span>
                            <span class="channel-value">9,028</span>
                        </div>
                        <div class="channel-row">
                            <span class="channel-dot purple"></span>
                            <span>Klikko-Hub</span>
                            <span class="channel-value">5,245</span>
                        </div>
                        <div class="channel-row">
                            <span class="channel-dot orange"></span>
                            <span>QR Payment</span>
                            <span class="channel-value">3,075</span>
                        </div>
                        <div class="channel-row">
                            <span class="channel-dot cyan"></span>
                            <span>Other</span>
                            <span class="channel-value">1,398</span>
                        </div>
                    </div>
                </article>
            </div>
        </section>
        """
        )
    )


# -----------------------------------------------------------------------------
# Interactive chart builders
# Each function turns one validated backend DataFrame into an Altair chart.
# -----------------------------------------------------------------------------
def build_trend_chart(data: pd.DataFrame) -> alt.Chart:
    """Create the live voucher-redemption and redemption-value trend chart."""
    period_order = data["period"].tolist()
    bars = (
        alt.Chart(data)
        .mark_bar(
            color=CAMPAIGN_CHART_BLUE,
            size=46,
            cornerRadiusTopLeft=3,
            cornerRadiusTopRight=3,
        )
        .encode(
            x=alt.X(
                "period:N",
                sort=period_order,
                title=None,
                axis=alt.Axis(labelAngle=0, labelPadding=10, tickSize=0),
            ),
            y=alt.Y(
                "vouchers_redeemed:Q",
                title="Vouchers",
                axis=alt.Axis(format=",", grid=True, tickCount=5),
                scale=alt.Scale(zero=True),
            ),
            tooltip=[
                alt.Tooltip("period:N", title="Period"),
                alt.Tooltip(
                    "vouchers_redeemed:Q",
                    title="Vouchers Redeemed",
                    format=",",
                ),
            ],
        )
    )

    redemption_line = (
        alt.Chart(data)
        .mark_line(
            color=CAMPAIGN_CHART_TONES[1],
            point=alt.OverlayMarkDef(
                color=CAMPAIGN_CHART_TONES[1],
                filled=True,
                size=65,
                stroke="white",
                strokeWidth=2,
            ),
            strokeWidth=2.5,
        )
        .encode(
            x=alt.X("period:N", sort=period_order, title=None),
            y=alt.Y(
                "redemption_value:Q",
                title="Redemption Value (Rp)",
                axis=alt.Axis(
                    orient="right",
                    format="~s",
                    grid=False,
                    tickCount=5,
                ),
                scale=alt.Scale(zero=True),
            ),
            tooltip=[
                alt.Tooltip("period:N", title="Period"),
                alt.Tooltip(
                    "redemption_value:Q",
                    title="Redemption Value (Rp)",
                    format=",.0f",
                ),
                alt.Tooltip(
                    "average_transaction_value:Q",
                    title="Average Transaction (Rp)",
                    format=",.0f",
                ),
            ],
        )
    )

    return (
        alt.layer(bars, redemption_line)
        .resolve_scale(y="independent")
        .properties(height=340)
        .configure(background="#ffffff")
        .configure_view(stroke=None, fill="#ffffff")
        .configure_axis(
            domain=False,
            labelColor="#626875",
            labelFontSize=11,
            title=None,
            gridColor="#edf0f5",
        )
    )


def build_conversion_funnel_chart(data: pd.DataFrame) -> alt.Chart:
    """Create an interactive horizontal conversion funnel from View to Redeem."""
    chart_data = data.sort_values("stage_order").copy()
    chart_data["full_percentage"] = 100.0
    chart_data["zero"] = 0.0
    chart_data["percentage_label"] = chart_data["percentage"].map(
        lambda value: f"{value:.0f}%"
    )
    chart_data["count_label"] = chart_data["count"].map(
        lambda value: f"{value:,.0f}"
    )
    stage_order = chart_data["stage"].tolist()

    background = (
        alt.Chart(chart_data)
        .mark_bar(size=38, color=CAMPAIGN_CHART_LIGHT_BLUE, cornerRadius=5)
        .encode(
            y=alt.Y(
                "stage:N",
                sort=stage_order,
                title=None,
                axis=alt.Axis(labelPadding=12, labelFontSize=12, tickSize=0),
            ),
            x=alt.X(
                "full_percentage:Q",
                scale=alt.Scale(domain=[0, 100]),
                axis=None,
            ),
        )
    )
    filled = (
        alt.Chart(chart_data)
        .mark_bar(size=38, color=CAMPAIGN_CHART_BLUE, cornerRadius=5)
        .encode(
            y=alt.Y("stage:N", sort=stage_order, title=None),
            x=alt.X("percentage:Q", scale=alt.Scale(domain=[0, 100]), axis=None),
            tooltip=[
                alt.Tooltip("stage:N", title="Stage"),
                alt.Tooltip("count:Q", title="Consumers", format=","),
                alt.Tooltip("percentage:Q", title="Conversion", format=".1f"),
            ],
        )
    )
    percentage_text = (
        alt.Chart(chart_data)
        .mark_text(align="left", baseline="middle", dx=9, color="white", fontWeight=700)
        .encode(
            y=alt.Y("stage:N", sort=stage_order, title=None),
            x=alt.X("zero:Q", scale=alt.Scale(domain=[0, 100]), axis=None),
            text="percentage_label:N",
        )
    )
    count_text = (
        alt.Chart(chart_data)
        .mark_text(
            align="right",
            baseline="middle",
            dx=-8,
            color="#343a48",
            fontWeight=600,
        )
        .encode(
            y=alt.Y("stage:N", sort=stage_order, title=None),
            x=alt.X("full_percentage:Q", scale=alt.Scale(domain=[0, 100]), axis=None),
            text="count_label:N",
        )
    )

    return (
        alt.layer(background, filled, percentage_text, count_text)
        .properties(height=300)
        .configure(background="#ffffff")
        .configure_view(stroke=None, fill="#ffffff")
        .configure_axis(domain=False, labelColor="#7a8190", grid=False)
    )


def build_channel_chart(data: pd.DataFrame) -> alt.Chart:
    """Create the compact Product Performance redemption-channel donut."""
    chart_data = data.copy()
    channel_total = float(chart_data["redemptions"].sum())
    chart_data["percentage"] = (
        chart_data["redemptions"] / channel_total if channel_total else 0.0
    )
    chart_data["sort_order"] = range(len(chart_data))
    channel_order = chart_data["channel"].tolist()
    channel_colors = [
        CAMPAIGN_CHART_TONES[index % len(CAMPAIGN_CHART_TONES)]
        for index in range(len(channel_order))
    ]

    arcs = (
        alt.Chart(chart_data)
        .mark_arc(innerRadius=48, outerRadius=76, stroke="white", strokeWidth=1)
        .encode(
            theta=alt.Theta("redemptions:Q", stack=True),
            color=alt.Color(
                "channel:N",
                scale=alt.Scale(domain=channel_order, range=channel_colors),
                legend=None,
            ),
            order=alt.Order("sort_order:Q", sort="ascending"),
            tooltip=[
                alt.Tooltip("channel:N", title="Channel"),
                alt.Tooltip("redemptions:Q", title="Redemptions", format=","),
                alt.Tooltip("percentage:Q", title="Share", format=".1%"),
            ],
        )
    )
    center_label = (
        alt.Chart(pd.DataFrame({"label": ["100%" if channel_total else "0%"]}))
        .mark_text(color="#242b39", fontSize=16, fontWeight=700)
        .encode(text="label:N")
    )
    return (
        (arcs + center_label)
        .properties(height=235)
        .configure(background="#ffffff")
        .configure_view(stroke=None, fill="#ffffff")
    )


def build_category_performance_chart(data: pd.DataFrame) -> alt.Chart:
    """Create the stacked category redemption and sampling chart."""
    category_order = data["category"].tolist()
    series_order = ["Redeemed", "Sampling"]
    chart_data = data.melt(
        id_vars="category",
        value_vars=["redeemed", "sampling"],
        var_name="series",
        value_name="count",
    )
    chart_data["series"] = chart_data["series"].map(
        {"redeemed": "Redeemed", "sampling": "Sampling"}
    )
    chart_data["stack_order"] = chart_data["series"].map(
        {"Redeemed": 1, "Sampling": 2}
    )

    totals = data.assign(total=data["redeemed"] + data["sampling"])
    raw_maximum = totals["total"].max()
    chart_maximum = (
        max(float(raw_maximum) * 1.16, 1.0)
        if pd.notna(raw_maximum)
        else 1.0
    )

    bars = (
        alt.Chart(chart_data)
        .mark_bar(size=22)
        .encode(
            y=alt.Y(
                "category:N",
                sort=category_order,
                title=None,
                axis=alt.Axis(ticks=False, labelPadding=10),
            ),
            x=alt.X(
                "count:Q",
                stack="zero",
                title=None,
                scale=alt.Scale(domain=[0, chart_maximum]),
                axis=alt.Axis(format="~s", grid=True, tickCount=5),
            ),
            color=alt.Color(
                "series:N",
                title=None,
                scale=alt.Scale(
                    domain=series_order,
                    range=[CAMPAIGN_CHART_BLUE, CAMPAIGN_CHART_LIGHT_BLUE],
                ),
                legend=alt.Legend(
                    orient="top",
                    direction="horizontal",
                    symbolType="square",
                    symbolStrokeColor="transparent",
                    symbolStrokeWidth=0,
                    offset=12,
                ),
            ),
            order=alt.Order("stack_order:Q"),
            tooltip=[
                alt.Tooltip("category:N", title="Category"),
                alt.Tooltip("series:N", title="Metric"),
                alt.Tooltip("count:Q", title="Count", format=","),
            ],
        )
    )

    total_labels = (
        alt.Chart(totals)
        .mark_text(align="left", baseline="middle", dx=10, color="#555b68", fontSize=11)
        .encode(
            y=alt.Y("category:N", sort=category_order),
            x=alt.X("total:Q"),
            text=alt.Text("total:Q", format=","),
        )
    )

    return (
        (bars + total_labels)
        .properties(height=285)
        .configure(background="#ffffff")
        .configure_view(stroke=None, fill="#ffffff")
        .configure_axis(
            domain=False,
            labelColor="#555b68",
            labelFontSize=11,
            gridColor="#edf0f5",
            title=None,
        )
        .configure_legend(
            labelColor="#555b68",
            labelFontSize=11,
            padding=0,
        )
    )


def build_time_of_day_chart(data: pd.DataFrame) -> alt.Chart:
    """Create the compact hourly bar chart used in Product Performance."""
    # Hour 24 is the endpoint from the previous line-chart design. The bar
    # layout displays the 24 complete hourly buckets from 00:00 through 23:00.
    chart_data = data.loc[data["hour"] < 24].copy()
    raw_maximum = chart_data["redemptions"].max()
    maximum_redemptions = (
        float(raw_maximum) if pd.notna(raw_maximum) else 0.0
    )
    y_axis_maximum = max(maximum_redemptions * 1.1, maximum_redemptions + 1, 2)
    selected_hour = alt.selection_point(
        name="selected_hour",
        fields=["hour"],
        on="click",
        empty=False,
    )

    base = alt.Chart(chart_data).encode(
        x=alt.X(
            "hour:Q",
            title=None,
            scale=alt.Scale(domain=[-0.5, 23.5], nice=False),
            axis=alt.Axis(
                values=[0, 5, 10, 15, 20],
                format=".0f",
                labelPadding=10,
                tickSize=0,
                grid=False,
            ),
        ),
        y=alt.Y(
            "redemptions:Q",
            title=None,
            scale=alt.Scale(domain=[0, y_axis_maximum], nice=False),
            axis=alt.Axis(
                format="~s",
                tickCount=5,
                tickMinStep=1,
                tickSize=0,
                grid=True,
            ),
        ),
    )

    bars = (
        base.mark_bar(
            size=13,
            cornerRadiusTopLeft=5,
            cornerRadiusTopRight=5,
        )
        .encode(
            color=alt.condition(
                selected_hour,
                alt.value(CAMPAIGN_CHART_BLUE),
                alt.value(CAMPAIGN_CHART_BLUE),
            ),
            opacity=alt.condition(selected_hour, alt.value(1), alt.value(0.92)),
            tooltip=[
                alt.Tooltip("time_range:N", title="Time"),
                alt.Tooltip("redemptions:Q", title="Redemptions", format=","),
            ],
        )
        .add_params(selected_hour)
    )
    selected_label = (
        base.transform_filter(selected_hour)
        .mark_text(
            dy=-19,
            color="#303441",
            fontSize=11,
            fontWeight=600,
        )
        .encode(text="selected_label:N")
    )

    return (
        alt.layer(bars, selected_label)
        .properties(height=260)
        .configure(background="#ffffff")
        .configure_view(stroke=None, fill="#ffffff")
        .configure_axis(
            domain=False,
            labelColor="#626875",
            labelFontSize=11,
            gridColor="#edf0f5",
            title=None,
        )
    )


def build_customer_mix_chart(data: pd.DataFrame) -> alt.Chart:
    """Create the Consumer Type donut chart."""
    chart_data = data.copy()
    customer_total = float(chart_data["customers"].sum())
    chart_data["percentage"] = (
        chart_data["customers"] / customer_total * 100
        if customer_total
        else 0.0
    )
    segment_order = chart_data["segment"].tolist()

    return (
        alt.Chart(chart_data)
        .mark_arc(
            # Adjust these radii later if the donut itself needs resizing.
            innerRadius=30,
            outerRadius=55,
            stroke="#ffffff",
            strokeWidth=1,
        )
        .encode(
            theta=alt.Theta("customers:Q", stack=True),
            color=alt.Color(
                "segment:N",
                scale=alt.Scale(
                    domain=segment_order,
                    range=[CAMPAIGN_CHART_BLUE, CAMPAIGN_CHART_LIGHT_BLUE],
                ),
                legend=None,
            ),
            order=alt.Order("segment:N", sort="ascending"),
            tooltip=[
                alt.Tooltip("segment:N", title="Customer Type"),
                alt.Tooltip("customers:Q", title="Customers", format=","),
                alt.Tooltip("percentage:Q", title="Share", format=".1f"),
            ],
        )
        # Lower this height to move the donut upward; raise it to move it down.
        .properties(height=150)
        .configure(background="#ffffff")
        .configure_view(stroke=None, fill="#ffffff")
    )


def build_gender_chart(data: pd.DataFrame) -> alt.Chart:
    """Create the compact male-versus-female redemption donut chart."""
    chart_data = data.copy()
    gender_order = chart_data["gender"].tolist()

    return (
        alt.Chart(chart_data)
        .mark_arc(
            innerRadius=30,
            outerRadius=55,
            stroke="#ffffff",
            strokeWidth=1,
        )
        .encode(
            theta=alt.Theta("percentage:Q", stack=True),
            color=alt.Color(
                "gender:N",
                scale=alt.Scale(
                    domain=gender_order,
                    range=[CAMPAIGN_CHART_BLUE, CAMPAIGN_CHART_LIGHT_BLUE],
                ),
                legend=None,
            ),
            order=alt.Order("gender:N", sort="ascending"),
            tooltip=[
                alt.Tooltip("gender:N", title="Gender"),
                alt.Tooltip("percentage:Q", title="Redemptions", format=".1f"),
            ],
        )
        .properties(height=145)
        .configure(background="#ffffff")
        .configure_view(stroke=None, fill="#ffffff")
    )


# -----------------------------------------------------------------------------
# Filtered dataset loading and chart preparation
# One filter object keeps every dashboard section synchronized.
# -----------------------------------------------------------------------------
trend_data, channel_data = load_dashboard_data(dashboard_filters)
trend_chart = build_trend_chart(trend_data)
channel_chart = build_channel_chart(channel_data)
campaign_metrics, funnel_data = load_campaign_performance_data(dashboard_filters)
funnel_chart = build_conversion_funnel_chart(funnel_data)
campaign_metric_rows = {
    row.metric_key: row for row in campaign_metrics.itertuples(index=False)
}
missing_campaign_metrics = set(CAMPAIGN_METRIC_PRESENTATION).difference(
    campaign_metric_rows
)
if missing_campaign_metrics:
    missing_labels = ", ".join(sorted(missing_campaign_metrics))
    raise ValueError(f"Campaign data is missing metric_key values: {missing_labels}")

campaign_top_cards = [
    metric_card_html(
        campaign_metric_rows[metric_key],
        CAMPAIGN_METRIC_PRESENTATION[metric_key],
    )
    for metric_key in CAMPAIGN_TOP_METRICS
]
campaign_summary_cards = [
    metric_card_html(
        campaign_metric_rows[metric_key],
        CAMPAIGN_METRIC_PRESENTATION[metric_key],
    )
    for metric_key in CAMPAIGN_SUMMARY_METRICS
]
category_data, sampled_products, redeemed_products = load_product_performance_data(
    dashboard_filters
)
category_chart = build_category_performance_chart(category_data)
category_overview, hourly_redemptions = load_product_detail_data(dashboard_filters)
time_of_day_chart = build_time_of_day_chart(hourly_redemptions)
outlets, campaigns, locations = load_merchant_performance_data(dashboard_filters)
customer_segments, loyalty, gender, age_groups = load_customer_insights_data(
    dashboard_filters
)
customer_mix_chart = build_customer_mix_chart(customer_segments)
gender_chart = build_gender_chart(gender)

# -----------------------------------------------------------------------------
# Campaign Performance section
# Shows engagement KPIs, trend and funnel charts, then three value summaries.
# -----------------------------------------------------------------------------
st.html('<div class="section-spacer" aria-hidden="true"></div>')
st.html(
    f"""
    <section aria-label="Campaign Performance">
        <div class="campaign-performance-heading">Campaign Performance</div>
        <div class="campaign-metric-grid">
            {''.join(campaign_top_cards)}
        </div>
    </section>
    """
)

campaign_trend_column, funnel_column = st.columns([1, 1], gap="medium")

with campaign_trend_column:
    with st.container(border=True, height=430):
        st.html(
            '<div class="analytics-title native-chart-title campaign-chart-title">'
            "Redemption &amp; Sales Trend</div>"
        )
        st.altair_chart(trend_chart, width="stretch")

with funnel_column:
    with st.container(border=True, height=430):
        st.html(
            '<div class="analytics-title native-chart-title campaign-chart-title">'
            "Conversion Funnel</div>"
        )
        st.altair_chart(funnel_chart, width="stretch")

st.html(
    f"""
    <div class="campaign-summary-grid" aria-label="Campaign value summary">
        {''.join(campaign_summary_cards)}
    </div>
    """
)


# -----------------------------------------------------------------------------
# Product Performance section
# Combines category comparison, top-product lists, detailed KPIs, and time use.
# -----------------------------------------------------------------------------
st.html('<div class="section-spacer" aria-hidden="true"></div>')
st.html(
    """
    <div class="product-section-heading">
        <div class="product-section-title">Product Performance</div>
    </div>
    """
)

category_column, sampled_column, redeemed_column = st.columns(
    [1.45, 1, 1],
    gap="medium",
)

with category_column:
    with st.container(border=True, height=430):
        st.html(
            '<div class="analytics-title native-chart-title product-card-title">'
            "Top Categories by Redemption</div>"
        )
        st.altair_chart(category_chart, width="stretch")

with sampled_column:
    with st.container(border=True, height=430):
        st.html(
            '<div class="analytics-title native-chart-title product-card-title">'
            "Top Sampled Products</div>"
        )
        sampled_rows = "".join(
            f"""
            <div class="product-row">
                <span class="product-rank">{rank}</span>
                <span class="product-name">{escape(str(row.product))}</span>
                <span class="product-count">{row.count:,} samples</span>
            </div>
            """
            for rank, row in enumerate(
                sampled_products.itertuples(index=False),
                start=1,
            )
        )
        st.html(f'<div class="product-list">{sampled_rows}</div>')

with redeemed_column:
    with st.container(border=True, height=430):
        st.html(
            '<div class="analytics-title native-chart-title product-card-title">'
            "Top Products by Redemption</div>"
        )
        redeemed_rows = "".join(
            f"""
            <div class="product-row">
                <span class="product-rank">{rank}</span>
                <span class="product-name">{escape(str(row.product))}</span>
                <span class="product-count">{row.count:,} redeemed</span>
            </div>
            """
            for rank, row in enumerate(
                redeemed_products.itertuples(index=False),
                start=1,
            )
        )
        st.html(f'<div class="product-list">{redeemed_rows}</div>')


st.html('<div class="product-detail-spacer" aria-hidden="true"></div>')
overview_column, time_column, channel_column = st.columns(
    [1, 1, 1],
    gap="medium",
)

with overview_column:
    with st.container(border=True, height=390):
        st.html(
            '<div class="analytics-title native-chart-title product-card-title">'
            "Category Performance Overview</div>"
        )
        raw_maximum_vouchers = category_overview["vouchers_redeemed"].max()
        maximum_vouchers = (
            max(float(raw_maximum_vouchers), 1.0)
            if pd.notna(raw_maximum_vouchers)
            else 1.0
        )
        overview_rows = "".join(
            f"""
            <div class="category-compact-row">
                <div class="category-compact-name">
                    {escape(str(row.category))}
                </div>
                <div class="category-compact-metric">
                    <span>
                        {row.vouchers_redeemed:,} ({row.redeemed_share:.1f}%)
                    </span>
                    <span class="category-compact-track">
                        <span
                            class="category-compact-fill"
                            style="display:block;width:{row.vouchers_redeemed / maximum_vouchers * 100:.1f}%"
                        ></span>
                    </span>
                </div>
            </div>
            """
            for row in category_overview.itertuples(index=False)
        )
        st.html(
            f"""
            <div class="category-compact-table">
                    <div class="category-compact-row category-compact-header">
                        <div>Category</div>
                        <div>Voucher Redeemed</div>
                    </div>
                    {overview_rows}
            </div>
            """
        )

with time_column:
    with st.container(border=True, height=390):
        st.html(
            '<div class="analytics-title native-chart-title product-card-title">'
            "Redemption by Time of Day</div>"
        )
        st.altair_chart(time_of_day_chart, width="stretch")

with channel_column:
    with st.container(border=True, height=390):
        st.html(
            '<div class="analytics-title native-chart-title product-card-title">'
            "Redemption by Channel</div>"
        )
        channel_total = float(channel_data["redemptions"].sum())
        channel_denominator = channel_total or 1.0
        channel_legend_rows = "".join(
            f"""
            <div class="product-channel-row">
                <span
                    class="product-channel-dot"
                    style="background:{CAMPAIGN_CHART_TONES[index % len(CAMPAIGN_CHART_TONES)]}"
                ></span>
                <span>{escape(str(row.channel))}</span>
                <span class="product-channel-value">
                    {row.redemptions:,}
                    ({row.redemptions / channel_denominator * 100:.0f}%)
                </span>
            </div>
            """
            for index, row in enumerate(channel_data.itertuples(index=False))
        )
        donut_column, legend_column = st.columns([0.9, 1.25], gap="small")
        with donut_column:
            st.altair_chart(channel_chart, width="stretch")
        with legend_column:
            st.html(
                f'<div class="product-channel-legend">{channel_legend_rows}</div>'
            )


# -----------------------------------------------------------------------------
# Merchant Performance section
# Ranks outlets, campaigns, and cities by redeemed-voucher volume.
# -----------------------------------------------------------------------------
st.html('<div class="section-spacer" aria-hidden="true"></div>')
st.html(
    """
    <div class="product-section-heading">
        <div class="product-section-title">Merchant Performance</div>
    </div>
    """
)

outlet_column, campaign_column, location_column = st.columns(
    [1, 1, 1],
    gap="medium",
)

with outlet_column:
    with st.container(border=True, height=390):
        st.html(
            '<div class="analytics-title native-chart-title product-card-title">'
            "Best Performing Outlets</div>"
        )
        outlet_rows = "".join(
            f"""
            <div class="merchant-row">
                <span class="merchant-rank">{rank}</span>
                <span class="merchant-name" title="{escape(str(row.name))}">
                    {escape(str(row.name))}
                </span>
                <span class="merchant-count">{row.redemptions:,} redeemed</span>
            </div>
            """
            for rank, row in enumerate(outlets.itertuples(index=False), start=1)
        )
        st.html(f'<div class="merchant-list">{outlet_rows}</div>')

with campaign_column:
    with st.container(border=True, height=390):
        st.html(
            '<div class="analytics-title native-chart-title product-card-title">'
            "Best Performing Campaigns</div>"
        )
        campaign_rows = "".join(
            f"""
            <div class="merchant-row">
                <span class="merchant-rank">{rank}</span>
                <span class="merchant-name" title="{escape(str(row.name))}">
                    {escape(str(row.name))}
                </span>
                <span class="merchant-count">{row.redemptions:,} redeemed</span>
            </div>
            """
            for rank, row in enumerate(campaigns.itertuples(index=False), start=1)
        )
        st.html(f'<div class="merchant-list">{campaign_rows}</div>')

with location_column:
    with st.container(border=True, height=390):
        st.html(
            '<div class="analytics-title native-chart-title product-card-title">'
            "Top Redeeming Locations</div>"
        )
        location_rows = "".join(
            f"""
            <div class="merchant-row">
                <span class="location-pin" aria-hidden="true"></span>
                <span class="merchant-name" title="{escape(str(row.name))}">
                    {escape(str(row.name))}
                </span>
                <span class="merchant-count">{row.redemptions:,} redeemed</span>
            </div>
            """
            for row in locations.itertuples(index=False)
        )
        st.html(f'<div class="merchant-list">{location_rows}</div>')


# -----------------------------------------------------------------------------
# Customer Insights section
# Summarizes customer mix, loyalty, gender, and age-group performance.
# -----------------------------------------------------------------------------
st.html('<div class="section-spacer" aria-hidden="true"></div>')
st.html(
    """
    <div class="product-section-heading">
        <div class="product-section-title">Customer Insights</div>
    </div>
    """
)

customer_mix_column, loyalty_column, gender_column, age_column = st.columns(
    [1.35, 1, 1.15, 1],
    gap="medium",
    vertical_alignment="top",
)

with customer_mix_column:
    with st.container(border=True, height=CUSTOMER_INSIGHTS_CARD_HEIGHT):
        st.html(
            '<div class="analytics-title native-chart-title product-card-title '
            'customer-card-title">'
            "Consumer Type</div>"
        )
        st.html('<div class="customer-content-offset" aria-hidden="true"></div>')
        donut_column, customer_legend_column = st.columns(
            [0.78, 1.22],
            gap="small",
            vertical_alignment="top",
        )
        with donut_column:
            st.altair_chart(customer_mix_chart, width="stretch")
        with customer_legend_column:
            segment_total = float(customer_segments["customers"].sum())
            segment_denominator = segment_total or 1.0
            customer_palette = [CAMPAIGN_CHART_BLUE, CAMPAIGN_CHART_LIGHT_BLUE]
            customer_colors = {
                segment: customer_palette[index % len(customer_palette)]
                for index, segment in enumerate(customer_segments["segment"])
            }
            customer_legend_rows = "".join(
                f"""
                <div class="customer-legend-item">
                    <span
                        class="customer-legend-dot"
                        style="background:{customer_colors[row.segment]}"
                    ></span>
                    <div>
                        <div class="customer-legend-name">
                            {escape(str(row.segment))}
                        </div>
                        <div class="customer-legend-detail">
                            {row.customers:,}
                            ({row.customers / segment_denominator * 100:.1f}%)
                        </div>
                    </div>
                </div>
                """
                for row in customer_segments.itertuples(index=False)
            )
            st.html(
                f'<div class="customer-mix-legend">{customer_legend_rows}</div>'
            )

with loyalty_column:
    with st.container(border=True, height=CUSTOMER_INSIGHTS_CARD_HEIGHT):
        st.html(
            '<div class="analytics-title native-chart-title product-card-title '
            'customer-card-title">'
            "Customer Loyalty</div>"
        )
        if "repeat_customer_count" in loyalty:
            loyalty_primary_value = f'{int(loyalty["repeat_customer_count"]):,}'
            loyalty_primary_label = "Repeat Customers"
            loyalty_secondary_label = "Share of Repeat Customers"
        else:
            loyalty_primary_value = f'{float(loyalty["average_transactions"]):.1f}'
            loyalty_primary_label = "Avg. Transactions / Customer"
            loyalty_secondary_label = "Customers redeemed more than 2x this month"
        st.html(
            f"""
            <div class="loyalty-metrics">
                <div class="loyalty-metric">
                    <div class="customer-insight-value">
                        {loyalty_primary_value}
                    </div>
                    <div class="customer-insight-description">
                        {loyalty_primary_label}
                    </div>
                </div>
                <div class="loyalty-metric">
                    <div class="customer-insight-value">
                        {float(loyalty["repeat_customer_percentage"]):.0f}%
                    </div>
                    <div class="customer-insight-description">
                        {loyalty_secondary_label}
                    </div>
                </div>
            </div>
            """
        )

with gender_column:
    with st.container(border=True, height=CUSTOMER_INSIGHTS_CARD_HEIGHT):
        st.html(
            '<div class="analytics-title native-chart-title product-card-title '
            'customer-card-title">'
            "Redemption by Gender</div>"
        )
        st.html('<div class="customer-content-offset" aria-hidden="true"></div>')
        gender_palette = [CAMPAIGN_CHART_BLUE, CAMPAIGN_CHART_LIGHT_BLUE]
        gender_colors = {
            label: gender_palette[index % len(gender_palette)]
            for index, label in enumerate(gender["gender"])
        }
        gender_legend_rows = "".join(
            f"""
            <div class="customer-legend-item">
                <span
                    class="customer-legend-dot"
                    style="background:{gender_colors[row.gender]}"
                ></span>
                <div>
                    <div class="customer-legend-name">
                        {escape(str(row.gender))}
                    </div>
                    <div class="customer-legend-detail">
                        {row.percentage:.0f}%
                    </div>
                </div>
            </div>
            """
            for row in gender.itertuples(index=False)
        )
        gender_donut_column, gender_legend_column = st.columns(
            [0.82, 1.18],
            gap="small",
            vertical_alignment="top",
        )
        with gender_donut_column:
            st.altair_chart(gender_chart, width="stretch")
        with gender_legend_column:
            st.html(
                f'<div class="gender-donut-legend">{gender_legend_rows}</div>'
            )
with age_column:
    with st.container(border=True, height=CUSTOMER_INSIGHTS_CARD_HEIGHT):
        st.html(
            '<div class="analytics-title native-chart-title product-card-title '
            'customer-card-title">'
            "Age Group</div>"
        )
        age_group_definitions = [
            ("Generation Z", "18 – 29", {"generation z", "gen z", "18-29"}),
            ("Millennials", "30 – 45", {"millennials", "millennial", "30-45"}),
            ("Generation X", "46 – 61", {"generation x", "gen x", "46-61"}),
            ("Baby Boomers", "62+", {"baby boomers", "boomer", "62+"}),
        ]

        def normalize_age_group_label(value: object) -> str:
            return (
                str(value)
                .strip()
                .lower()
                .replace(" years", "")
                .replace("–", "-")
                .replace("—", "-")
                .replace(" ", "")
            )

        age_percentage_lookup: dict[str, float] = {}
        for row in age_groups.itertuples(index=False):
            percentage = float(row.percentage)
            for source_label in (row.age_group, row.age_range):
                normalized_label = normalize_age_group_label(source_label)
                if normalized_label:
                    age_percentage_lookup[normalized_label] = percentage

        age_group_display_rows: list[dict[str, object]] = []
        for group_name, age_range, aliases in age_group_definitions:
            normalized_aliases = {
                normalize_age_group_label(alias) for alias in aliases
            }
            percentage = next(
                (
                    age_percentage_lookup[alias]
                    for alias in normalized_aliases
                    if alias in age_percentage_lookup
                ),
                None,
            )
            age_group_display_rows.append(
                {
                    "age_group": group_name,
                    "age_range": age_range,
                    "percentage": percentage,
                }
            )

        available_age_percentages = [
            float(row["percentage"])
            for row in age_group_display_rows
            if row["percentage"] is not None
        ]
        raw_maximum_age = max(available_age_percentages, default=0.0)
        maximum_age_percentage = (
            max(float(raw_maximum_age), 1.0)
            if pd.notna(raw_maximum_age)
            else 1.0
        )
        age_group_rows = "".join(
            f"""
            <div class="age-group-row">
                <div class="age-group-name">
                    {escape(str(row["age_group"]))}
                    <span class="age-group-range">
                        ({escape(str(row["age_range"]))})
                    </span>
                </div>
                <div class="age-group-track" aria-hidden="true">
                    <span
                        class="age-group-fill"
                        style="width:{(
                            float(row["percentage"]) / maximum_age_percentage * 100
                            if row["percentage"] is not None
                            else 0.0
                        ):.1f}%"
                    ></span>
                </div>
                <div class="age-group-percentage{(
                    ' placeholder' if row["percentage"] is None else ''
                )}">
                    {(
                        f'{float(row["percentage"]):.0f}%'
                        if row["percentage"] is not None
                        else '—'
                    )}
                </div>
            </div>
            """
            for row in age_group_display_rows
        )
        st.html(
            f'<div class="age-group-list" aria-label="Age group redemption">'
            f"{age_group_rows}</div>"
        )
