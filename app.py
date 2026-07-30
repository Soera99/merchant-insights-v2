import base64
from datetime import date
from html import escape
from pathlib import Path
from textwrap import dedent

import altair as alt
import pandas as pd
import streamlit as st

from data_access import create_dashboard_repository, validate_frame


st.set_page_config(
    page_title="Merchant Insights",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)


APP_DIR = Path(__file__).parent
ASSET_DIR = APP_DIR / "assets"
# Change this one value to resize all four Customer Insights cards.
CUSTOMER_INSIGHTS_CARD_HEIGHT = 250


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


METRIC_PRESENTATION = {
    "vouchers_redeemed": {
        "label": "Total Vouchers Redeemed",
        "icon": "checked.png",
        "format": lambda value: f"{value:,.0f}",
    },
    "redemption_value": {
        "label": "Total Redemption Value",
        "icon": "redeem.png",
        "format": lambda value: f"Rp {value / 1_000_000:.1f}M",
    },
    "campaigns": {
        "label": "Total Campaigns",
        "icon": "marketing.png",
        "format": lambda value: f"{value:,.0f}",
    },
    "customers": {
        "label": "Total Customers",
        "icon": "team.png",
        "format": lambda value: f"{value:,.0f}",
    },
    "new_customers": {
        "label": "New Customers",
        "icon": "add-group.png",
        "format": lambda value: f"{value:,.0f}",
    },
}


@st.cache_resource
def get_dashboard_repository():
    """Create one repository instance per Streamlit process."""
    return create_dashboard_repository()


@st.cache_data(ttl=300)
def load_kpi_data(start_date: date, end_date: date) -> pd.DataFrame:
    return validate_frame(
        get_dashboard_repository().load_kpi_data(start_date, end_date),
        "kpi",
    )


@st.cache_data(ttl=300)
def load_dashboard_data(
    start_date: date,
    end_date: date,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    trend_data, channel_data = get_dashboard_repository().load_dashboard_data(
        start_date,
        end_date,
    )
    return (
        validate_frame(trend_data, "trend"),
        validate_frame(channel_data, "channel"),
    )


@st.cache_data(ttl=300)
def load_product_performance_data(
    start_date: date,
    end_date: date,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    category_data, sampled_products, redeemed_products = (
        get_dashboard_repository().load_product_performance_data(
            start_date,
            end_date,
        )
    )
    return (
        validate_frame(category_data, "category_performance"),
        validate_frame(sampled_products, "sampled_products"),
        validate_frame(redeemed_products, "redeemed_products"),
    )


@st.cache_data(ttl=300)
def load_product_detail_data(
    start_date: date,
    end_date: date,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    category_overview, hourly_redemptions = (
        get_dashboard_repository().load_product_detail_data(
            start_date,
            end_date,
        )
    )
    return (
        validate_frame(category_overview, "category_overview"),
        validate_frame(hourly_redemptions, "hourly_redemptions"),
    )


@st.cache_data(ttl=300)
def load_merchant_performance_data(
    start_date: date,
    end_date: date,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    outlets, campaigns, locations = (
        get_dashboard_repository().load_merchant_performance_data(
            start_date,
            end_date,
        )
    )
    return (
        validate_frame(outlets, "leaderboard"),
        validate_frame(campaigns, "leaderboard"),
        validate_frame(locations, "leaderboard"),
    )


@st.cache_data(ttl=300)
def load_customer_insights_data(
    start_date: date,
    end_date: date,
) -> tuple[
    pd.DataFrame,
    dict[str, float | str],
    pd.DataFrame,
    pd.DataFrame,
]:
    customer_segments, loyalty, gender, payment_methods = (
        get_dashboard_repository().load_customer_insights_data(
            start_date,
            end_date,
        )
    )
    return (
        validate_frame(customer_segments, "customer_segments"),
        loyalty,
        validate_frame(gender, "gender"),
        validate_frame(payment_methods, "payment_methods"),
    )


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

        div[data-testid="stDateInput"] {
            width: min(100%, 330px);
            margin-left: auto;
        }

        div[data-testid="stDateInput"] [data-baseweb="input"] {
            background: #ffffff !important;
            border: 1px solid var(--border) !important;
            border-radius: 12px !important;
            box-shadow: 0 2px 7px rgba(25, 28, 55, 0.035);
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
            display: grid;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            gap: 1rem;
        }

        .kpi-card {
            box-sizing: border-box;
            min-height: 150px;
            padding: 1.15rem 1.25rem;
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 20px;
            box-shadow: 0 2px 7px rgba(25, 28, 55, 0.035);
            display: grid;
            grid-template-columns: 56px minmax(0, 1fr);
            column-gap: 0.65rem;
            transition: border-color 160ms ease, box-shadow 160ms ease,
                transform 160ms ease;
        }

        .kpi-card:hover {
            border-color: #dcdde8;
            box-shadow: 0 10px 24px rgba(25, 28, 55, 0.075);
            transform: translateY(-2px);
        }

        .kpi-icon-wrap {
            width: 56px;
            height: 56px;
            border-radius: 50%;
            background: var(--brand-soft);
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .kpi-icon {
            width: 30px;
            height: 30px;
            object-fit: contain;
            filter: invert(40%) sepia(82%) saturate(1193%) hue-rotate(207deg)
                brightness(86%) contrast(91%);
        }

        .kpi-content {
            min-width: 0;
            display: grid;
            grid-template-rows: auto auto auto;
            align-content: start;
        }

        .kpi-label {
            color: #787d87;
            font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont,
                "Segoe UI", sans-serif;
            font-size: 0.76rem;
            font-weight: 400;
            line-height: 1.3;
            margin: 0;
            white-space: nowrap;
        }

        .kpi-value {
            color: var(--ink);
            font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont,
                "Segoe UI", sans-serif;
            font-size: clamp(1.7rem, 2vw, 2.1rem);
            font-weight: 760;
            letter-spacing: -0.035em;
            line-height: 1.1;
            /* First value: label-to-value gap. Third value: value-to-trend gap. */
            margin: 0.55rem 0 0.65rem;
            white-space: nowrap;
        }

        .kpi-trend {
            display: flex;
            flex-direction: column;
            align-items: flex-start;
            gap: 0.1rem;
            white-space: nowrap;
        }

        .kpi-change {
            color: var(--positive);
            font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont,
                "Segoe UI", sans-serif;
            font-size: 0.92rem;
            font-weight: 700;
            line-height: 1.25;
            margin: 0;
        }

        .kpi-comparison {
            color: #787d87;
            font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont,
                "Segoe UI", sans-serif;
            font-size: 0.84rem;
            font-weight: 400;
            line-height: 1.25;
            margin: 0;
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
           This restores the intended blue border on that empty square. */
        div[data-testid="stVegaLiteChart"]
            path[stroke="#2f62c9"][stroke-width="0"] {
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
            color: #787d87;
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
            min-height: 178px;
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
            gap: 0.75rem;
            padding-top: 0.3rem;
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
            padding-top: 0.95rem;
            border-top: 1px solid var(--border);
        }

        .top-age-label {
            color: #787d87;
            font-size: 0.72rem;
        }

        .top-age-value {
            margin-top: 0.35rem;
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
            background: #3564e8;
        }

        .category-inline-fill.purple {
            background: #a895e5;
        }

        @media (max-width: 1320px) {
            .kpi-grid {
                grid-template-columns: repeat(3, minmax(0, 1fr));
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

            .kpi-grid {
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

            .kpi-grid {
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


dashboard_title_column, dashboard_date_column = st.columns(
    [3, 1],
    gap="medium",
    vertical_alignment="center",
)

with dashboard_title_column:
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

with dashboard_date_column:
    selected_date_range = st.date_input(
        "Dashboard date range",
        value=(date(2025, 5, 1), date(2025, 5, 31)),
        format="DD/MM/YYYY",
        label_visibility="collapsed",
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

kpi_data = load_kpi_data(dashboard_start_date, dashboard_end_date)
kpi_rows = {row.metric_key: row for row in kpi_data.itertuples(index=False)}
cards = []
for metric_key, presentation in METRIC_PRESENTATION.items():
    if metric_key not in kpi_rows:
        raise ValueError(f"KPI data is missing metric_key: {metric_key}")
    metric = kpi_rows[metric_key]
    change_sign = "+" if metric.change_pct >= 0 else ""
    label = presentation["label"]
    cards.append(
        dedent(
            f"""
        <article class="kpi-card" aria-label="{label}">
            <div class="kpi-icon-wrap">
                <img
                    class="kpi-icon"
                    src="{image_data_uri(presentation['icon'])}"
                    alt=""
                />
            </div>
            <div class="kpi-content">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{presentation['format'](metric.value)}</div>
                <div class="kpi-trend">
                    <div class="kpi-change">{change_sign}{metric.change_pct:.1f}%</div>
                    <div class="kpi-comparison">{escape(str(metric.comparison_label))}</div>
                </div>
            </div>
        </article>
        """
        ).strip()
    )

st.html('<div class="dashboard-header-spacer" aria-hidden="true"></div>')

st.markdown(
    dedent(
        f"""
    <main class="kpi-section">
        <div class="analytics-title kpi-heading" role="heading" aria-level="1">
            Key Performance Overview
        </div>
        <div class="kpi-grid">
            {''.join(cards)}
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


def build_trend_chart(data: pd.DataFrame) -> alt.Chart:
    """Create the interactive stacked-bar and transaction-value trend chart."""
    period_order = data["period"].tolist()
    bar_series_order = [
        "Voucher Redeemed",
        "Redemption Value (Rp)",
    ]
    voucher_bars = pd.DataFrame(
        {
            "period": data["period"],
            "series": "Voucher Redeemed",
            "plot_value": data["vouchers_redeemed"],
            "display_value": data["vouchers_redeemed"].map(lambda value: f"{value:,}"),
            "stack_order": 0,
        }
    )
    redemption_bars = pd.DataFrame(
        {
            "period": data["period"],
            "series": "Redemption Value (Rp)",
            # Scale currency for a readable stacked visual; tooltips retain Rp.
            "plot_value": data["redemption_value"] / 10_000,
            "display_value": data["redemption_value"].map(
                lambda value: f"Rp {value / 1_000_000:.1f}M"
            ),
            "stack_order": 1,
        }
    )
    bar_data = pd.concat([voucher_bars, redemption_bars], ignore_index=True)

    bars = (
        alt.Chart(bar_data)
        .mark_bar(size=46, cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X(
                "period:N",
                sort=period_order,
                title=None,
                axis=alt.Axis(labelAngle=0, labelPadding=10, tickSize=0),
            ),
            y=alt.Y(
                "plot_value:Q",
                stack="zero",
                title=None,
                axis=alt.Axis(format="~s", grid=True, tickCount=5),
                scale=alt.Scale(domain=[0, 9000]),
            ),
            color=alt.Color(
                "series:N",
                title=None,
                scale=alt.Scale(
                    domain=bar_series_order,
                    range=["#3564e8", "#a895e5"],
                ),
                legend=alt.Legend(
                    orient="top",
                    direction="horizontal",
                    symbolType="square",
                    symbolStrokeColor="transparent",
                    symbolStrokeWidth=0,
                    # Increase this value for more legend-to-chart spacing.
                    offset=24,
                ),
            ),
            order=alt.Order("stack_order:Q"),
            tooltip=[
                alt.Tooltip("period:N", title="Period"),
                alt.Tooltip("series:N", title="Metric"),
                alt.Tooltip("display_value:N", title="Value"),
            ],
        )
    )

    line_data = data.copy()
    line_data["series"] = "Average Transaction Value (Rp)"
    average_line = (
        alt.Chart(line_data)
        .mark_line(
            color="#2f62c9",
            point=alt.OverlayMarkDef(
                color="#2f62c9",
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
                "average_transaction_value:Q",
                title=None,
                axis=alt.Axis(
                    orient="right",
                    format="~s",
                    grid=False,
                    tickCount=5,
                ),
                # Lower this maximum to move the line higher; raise it to move
                # the line closer to the bars.
                scale=alt.Scale(domain=[0, 8_600]),
            ),
            tooltip=[
                alt.Tooltip("period:N", title="Period"),
                alt.Tooltip(
                    "average_transaction_value:Q",
                    title="Average Transaction",
                    format=",.0f",
                ),
            ],
        )
    )

    # This off-canvas point creates a square outline specifically for the
    # line legend, while the actual chart line stays solid.
    line_legend = (
        alt.Chart(pd.DataFrame({"series": ["Average Transaction Value (Rp)"]}))
        .mark_point(
            shape="square",
            filled=True,
            fill="#ffffff",
            stroke="#2f62c9",
            strokeWidth=2,
            size=150,
            clip=True,
        )
        .encode(
            x=alt.value(-100),
            y=alt.value(-100),
            stroke=alt.Stroke(
                "series:N",
                title=None,
                scale=alt.Scale(
                    domain=["Average Transaction Value (Rp)"],
                    range=["#2f62c9"],
                ),
                legend=alt.Legend(
                    orient="top",
                    direction="horizontal",
                    offset=24,
                    symbolType="square",
                    symbolSize=150,
                    symbolFillColor="#ffffff",
                    symbolStrokeColor="#2f62c9",
                    symbolStrokeWidth=2,
                ),
            ),
        )
    )

    return (
        alt.layer(bars, average_line, line_legend)
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
        .configure_legend(
            labelColor="#555b68",
            labelFontSize=11,
            padding=0,
        )
    )


def build_channel_chart(data: pd.DataFrame) -> alt.Chart:
    """Create the interactive redemption-channel donut chart."""
    chart_data = data.copy()
    chart_data["percentage"] = chart_data["redemptions"] / chart_data["redemptions"].sum()
    raw_percentages = chart_data["percentage"] * 100
    rounded_percentages = raw_percentages.astype(int)
    remaining_points = 100 - int(rounded_percentages.sum())
    largest_remainders = (raw_percentages - rounded_percentages).nlargest(
        remaining_points
    )
    rounded_percentages.loc[largest_remainders.index] += 1
    chart_data["percentage_label"] = rounded_percentages.map(
        lambda value: f"{value}%"
    )
    chart_data["sort_order"] = range(len(chart_data))
    channel_order = chart_data["channel"].tolist()
    channel_colors = ["#365bc8", "#765acb", "#fb9844", "#3aaed1"]

    base = alt.Chart(chart_data).encode(
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
    arcs = base.mark_arc(innerRadius=58, outerRadius=105, stroke="white", strokeWidth=1)
    labels = base.mark_text(
        radius=82,
        color="white",
        fontSize=13,
        fontWeight=700,
    ).encode(
        text="percentage_label:N",
        # Override the channel color inherited from the shared base chart.
        color=alt.value("#ffffff"),
    )
    return (
        (arcs + labels)
        .properties(height=245)
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
    chart_maximum = float(totals["total"].max()) * 1.16

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
                    range=["#3564e8", "#a895e5"],
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
    """Create an hourly redemption chart with clickable data points."""
    selected_hour = alt.selection_point(
        name="selected_hour",
        fields=["hour"],
        on="click",
        nearest=True,
        empty=False,
    )

    base = alt.Chart(data).encode(
        x=alt.X(
            "hour:Q",
            title=None,
            scale=alt.Scale(domain=[0, 24]),
            axis=alt.Axis(
                values=[0, 4, 8, 12, 16, 20, 24],
                labelExpr="datum.value + ':00'",
                labelPadding=10,
                tickSize=0,
                grid=False,
            ),
        ),
        y=alt.Y(
            "redemptions:Q",
            title=None,
            scale=alt.Scale(domain=[0, 4_000]),
            axis=alt.Axis(format="~s", tickCount=5, tickSize=0, grid=True),
        ),
    )

    area = base.mark_area(
        interpolate="monotone",
        color="#3564e8",
        opacity=0.08,
    )
    line = base.mark_line(
        interpolate="monotone",
        color="#3564e8",
        strokeWidth=2.5,
    )
    points = (
        base.mark_point(
            filled=True,
            color="#3564e8",
            size=48,
            stroke="#ffffff",
            strokeWidth=1.5,
        )
        .encode(
            tooltip=[
                alt.Tooltip("time_range:N", title="Time"),
                alt.Tooltip("redemptions:Q", title="Redemptions", format=","),
            ],
        )
        .add_params(selected_hour)
    )
    selected_point = (
        base.transform_filter(selected_hour)
        .mark_point(
            filled=True,
            color="#3564e8",
            size=115,
            stroke="#ffffff",
            strokeWidth=2,
        )
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
        alt.layer(area, line, points, selected_point, selected_label)
        .properties(height=285)
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
    """Create the new-versus-returning customer donut chart."""
    chart_data = data.copy()
    chart_data["percentage"] = (
        chart_data["customers"] / chart_data["customers"].sum() * 100
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
                    range=["#3564e8", "#765acb"],
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


trend_data, channel_data = load_dashboard_data(
    dashboard_start_date,
    dashboard_end_date,
)
trend_chart = build_trend_chart(trend_data)
channel_chart = build_channel_chart(channel_data)
category_data, sampled_products, redeemed_products = load_product_performance_data(
    dashboard_start_date,
    dashboard_end_date,
)
category_chart = build_category_performance_chart(category_data)
category_overview, hourly_redemptions = load_product_detail_data(
    dashboard_start_date,
    dashboard_end_date,
)
time_of_day_chart = build_time_of_day_chart(hourly_redemptions)
outlets, campaigns, locations = load_merchant_performance_data(
    dashboard_start_date,
    dashboard_end_date,
)
customer_segments, loyalty, gender, payment_methods = load_customer_insights_data(
    dashboard_start_date,
    dashboard_end_date,
)
customer_mix_chart = build_customer_mix_chart(customer_segments)

total_vouchers = int(trend_data["vouchers_redeemed"].sum())
total_redemption = float(trend_data["redemption_value"].sum())
average_transaction = total_redemption / total_vouchers

st.html('<div class="section-spacer" aria-hidden="true"></div>')

trend_column, channel_column = st.columns([3, 1], gap="medium")

with trend_column:
    with st.container(border=True, height=500):
        st.html(
            '<div class="analytics-title native-chart-title">'
            "Redemption &amp; Sales Trend</div>"
        )
        chart_column, summary_column = st.columns([4, 1], gap="medium")
        with chart_column:
            st.html('<div class="trend-chart-spacer" aria-hidden="true"></div>')
            st.altair_chart(trend_chart, width="stretch")
        with summary_column:
            st.html(
                f"""
                <div class="native-summary">
                    <div class="summary-item">
                        <div class="summary-value">{total_vouchers:,}</div>
                        <div class="summary-label">Total Voucher Redeemed</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-value">Rp {total_redemption / 1_000_000:.1f}M</div>
                        <div class="summary-label">Total Redemption Value</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-value">Rp {average_transaction:,.0f}</div>
                        <div class="summary-label">Average Transaction Value</div>
                    </div>
                </div>
                """
            )

with channel_column:
    with st.container(border=True, height=500):
        st.html(
            '<div class="analytics-title native-chart-title">'
            "Redemption by Channel</div>"
        )
        st.altair_chart(channel_chart, width="stretch")
        channel_colors = {
            "In-store": "#365bc8",
            "Klikko-Hub": "#765acb",
            "QR Payment": "#fb9844",
            "Other": "#3aaed1",
        }
        channel_rows = "".join(
            f"""
            <div class="channel-row">
                <span class="channel-dot" style="background:{channel_colors[row.channel]}"></span>
                <span>{row.channel}</span>
                <span class="channel-value">{row.redemptions:,}</span>
            </div>
            """
            for row in channel_data.itertuples(index=False)
        )
        st.html(f'<div class="channel-list">{channel_rows}</div>')


st.html('<div class="section-spacer" aria-hidden="true"></div>')
st.html(
    """
    <div class="product-section-heading">
        <div class="product-section-title">Product Performance</div>
        <div class="product-section-description">
            Top products by redemption, sampling, and category
        </div>
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
overview_column, time_column = st.columns([1.5, 1], gap="medium")

with overview_column:
    with st.container(border=True, height=400):
        st.html(
            '<div class="analytics-title native-chart-title product-card-title">'
            "Category Performance Overview</div>"
        )
        maximum_vouchers = float(category_overview["vouchers_redeemed"].max())
        maximum_value = float(category_overview["redemption_value"].max())
        overview_rows = "".join(
            f"""
            <div class="category-overview-row">
                <div class="category-overview-cell category-overview-category">
                    {escape(str(row.category))}
                </div>
                <div class="category-overview-cell category-metric">
                    <span class="category-metric-value">
                        {row.vouchers_redeemed:,} ({row.redeemed_share:.1f}%)
                    </span>
                    <span class="category-inline-track">
                        <span
                            class="category-inline-fill blue"
                            style="display:block;width:{row.vouchers_redeemed / maximum_vouchers * 100:.1f}%"
                        ></span>
                    </span>
                </div>
                <div class="category-overview-cell category-metric">
                    <span class="category-metric-value">
                        Rp {row.redemption_value:,.0f}
                    </span>
                    <span class="category-inline-track">
                        <span
                            class="category-inline-fill purple"
                            style="display:block;width:{row.redemption_value / maximum_value * 100:.1f}%"
                        ></span>
                    </span>
                </div>
                <div class="category-overview-cell">
                    {row.unique_customers:,}
                </div>
                <div class="category-overview-cell category-overview-rate">
                    {row.conversion_rate:.1f}%
                </div>
            </div>
            """
            for row in category_overview.itertuples(index=False)
        )
        st.html(
            f"""
            <div class="category-overview-wrap">
                <div class="category-overview-table">
                    <div class="category-overview-row category-overview-header">
                        <div>Category</div>
                        <div>Voucher Redeemed</div>
                        <div>Redemption Value (Rp)</div>
                        <div>Unique Customers</div>
                        <div class="category-overview-rate">Conversion Rate</div>
                    </div>
                    {overview_rows}
                </div>
            </div>
            """
        )

with time_column:
    with st.container(border=True, height=400):
        st.html(
            '<div class="analytics-title native-chart-title product-card-title">'
            "Redemption by Time of Day</div>"
        )
        st.altair_chart(time_of_day_chart, width="stretch")


st.html('<div class="section-spacer" aria-hidden="true"></div>')
st.html(
    """
    <div class="product-section-heading">
        <div class="product-section-title">Merchant Performance</div>
        <div class="product-section-description">
            Best performing outlets, campaigns, and locations
        </div>
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


st.html('<div class="section-spacer" aria-hidden="true"></div>')
st.html(
    """
    <div class="product-section-heading">
        <div class="product-section-title">Customer Insights</div>
    </div>
    """
)

customer_mix_column, loyalty_column, gender_column, payment_column = st.columns(
    [1.35, 1, 1.15, 1],
    gap="medium",
    vertical_alignment="top",
)

with customer_mix_column:
    with st.container(border=True, height=CUSTOMER_INSIGHTS_CARD_HEIGHT):
        st.html(
            '<div class="analytics-title native-chart-title product-card-title '
            'customer-card-title">'
            "New vs Returning Customers</div>"
        )
        donut_column, customer_legend_column = st.columns(
            [0.78, 1.22],
            gap="small",
            vertical_alignment="top",
        )
        with donut_column:
            st.altair_chart(customer_mix_chart, width="stretch")
        with customer_legend_column:
            segment_total = float(customer_segments["customers"].sum())
            customer_colors = {
                "New Customers": "#3564e8",
                "Returning Customers": "#765acb",
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
                            ({row.customers / segment_total * 100:.1f}%)
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
        st.html(
            f"""
            <div class="loyalty-metrics">
                <div class="loyalty-metric">
                    <div class="customer-insight-value">
                        {float(loyalty["average_transactions"]):.1f}
                    </div>
                    <div class="customer-insight-description">
                        Avg. Transactions / Customer
                    </div>
                </div>
                <div class="loyalty-metric">
                    <div class="customer-insight-value">
                        {float(loyalty["repeat_customer_percentage"]):.0f}%
                    </div>
                    <div class="customer-insight-description">
                        Customers redeemed more than 2x this month
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
        gender_rows = "".join(
            f"""
            <div>
                <div class="insight-progress-label">
                    <span>{escape(str(row.gender))}</span>
                    <span class="insight-progress-value">
                        {row.percentage:.0f}%
                    </span>
                </div>
                <div class="insight-progress-track">
                    <div
                        class="insight-progress-fill"
                        style="width:{row.percentage:.1f}%"
                    ></div>
                </div>
            </div>
            """
            for row in gender.itertuples(index=False)
        )
        st.html(
            f"""
            <div class="gender-breakdown">
                {gender_rows}
                <div class="top-age-group">
                    <div class="top-age-label">Top Age Group</div>
                    <div class="top-age-value">
                        {escape(str(loyalty["top_age_group"]))}
                        ({float(loyalty["top_age_group_percentage"]):.0f}%)
                    </div>
                </div>
            </div>
            """
        )

with payment_column:
    with st.container(border=True, height=CUSTOMER_INSIGHTS_CARD_HEIGHT):
        st.html(
            '<div class="analytics-title native-chart-title product-card-title '
            'customer-card-title">'
            "Payment Method</div>"
        )
        payment_rows = "".join(
            f"""
            <div class="payment-row">
                <span class="payment-method">{escape(str(row.method))}</span>
                <div class="insight-progress-track">
                    <div
                        class="insight-progress-fill"
                        style="width:{row.percentage:.1f}%"
                    ></div>
                </div>
                <span class="payment-percentage">{row.percentage:.0f}%</span>
            </div>
            """
            for row in payment_methods.itertuples(index=False)
        )
        st.html(f'<div class="payment-breakdown">{payment_rows}</div>')
