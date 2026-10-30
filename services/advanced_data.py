"""Original advanced demo models and data adapters, separated from rendering.

Replace these loaders with authenticated API adapters when advanced data is ready.
"""
from __future__ import annotations

import calendar
from dataclasses import dataclass

import pandas as pd
import streamlit as st

from shared.theme import BAR_COLOR as BAR

_UP = [(38, 45, 43, 52, 58, 57, 66, 74), (42, 47, 50, 48, 56, 61, 64, 70), (45, 49, 47, 55, 59, 63, 66, 71), (36, 42, 40, 51, 58, 55, 68, 76), (44, 47, 49, 52, 51, 58, 62, 67)]
_DOWN = (70, 67, 68, 63, 61, 58, 56, 52)


@dataclass(frozen=True)
class KPI:
    label: str
    value: str
    delta: str
    comparison: str
    target: int
    trend: tuple[int, ...]
    icon: str = ""



@st.cache_resource
def load_dashboard_data(user_id: str = "demo-merchant") -> dict:
    """Demo adapter. Replace this body with an authenticated API call later."""
    months = [calendar.month_abbr[i] for i in range(1, 13)]
    kpis = [
        KPI("Total Revenue", "Rp 4.82B", "+12.8%", "vs last period", 86, (42, 48, 45, 57, 63, 61, 70, 78)),
        KPI("Revenue Growth", "12.8%", "+2.4pp", "period over period", 78, (35, 44, 40, 52, 56, 63, 61, 71)),
        KPI("Total Consumers", "286,430", "+8.4%", "all time", 82, (45, 49, 52, 57, 62, 66, 71, 77)),
        KPI("Active Consumers", "48,291", "+6.7%", "last 30 days", 74, (54, 58, 55, 62, 60, 69, 72, 76)),
        KPI("Total Campaigns", "62", "+5", "active and completed", 79, (31, 38, 43, 47, 53, 60, 66, 72)),
        KPI("Voucher Redeemed", "428,800", "+22.4%", "total redeemed", 91, (39, 44, 41, 53, 59, 57, 67, 75)),
        KPI("Redemption Rate", "62.4%", "+3.1pp", "claimed to redeemed", 89, (48, 51, 55, 58, 61, 64, 68, 71)),
        KPI("Campaign ROI", "3.8x", "+0.6x", "revenue divided by cost", 84, (40, 46, 43, 55, 62, 58, 68, 74)),
        KPI("Avg Basket Value", "Rp 48K", "+4.9%", "per transaction", 76, (51, 54, 52, 58, 61, 66, 64, 70)),
        KPI("Forecast Revenue", "Rp 1.4B", "+9.2%", "next 30 days", 88, (38, 45, 49, 55, 61, 66, 73, 80)),
    ]
    geography = pd.DataFrame(
        [
            ("DKI Jakarta", -6.2088, 106.8456, 1200, 14200, 48300),
            ("West Java", -6.9175, 107.6191, 820, 12100, 41200),
            ("East Java", -7.2575, 112.7521, 690, 9600, 35800),
            ("Central Java", -7.0051, 110.4381, 610, 8800, 31900),
            ("Bali", -8.4095, 115.1889, 520, 7200, 26400),
            ("North Sumatra", 3.5952, 98.6722, 470, 6800, 24100),
            ("South Sulawesi", -5.1477, 119.4327, 390, 5900, 19800),
            ("East Kalimantan", -0.5022, 117.1536, 350, 4700, 17200),
            ("Riau", 0.5071, 101.4478, 310, 4200, 15800),
            ("West Sumatra", -0.9471, 100.4172, 280, 3900, 14300),
            ("South Kalimantan", -3.3186, 114.5944, 260, 3500, 12800),
            ("Papua", -2.5916, 140.6690, 220, 2800, 9400),
        ],
        columns=["province", "lat", "lon", "revenue", "consumers", "vouchers"],
    )
    return {
        "user_id": user_id, "kpis": kpis, "months": months,
        "revenue": [280, 325, 305, 370, 405, 390, 455, 510, 445, 535, 505, 585],
        "consumer": [18, 21, 23, 22, 28, 30, 32, 35, 38, 41, 44, 48],
        "campaign": [12, 17, 20, 23, 27, 29, 32, 35, 34, 37, 36, 39],
        "redemption": [42, 48, 46, 55, 61, 59, 70, 76, 72, 88, 94, 105],
        "geography": geography,
    }



@st.cache_resource
def load_marketing_data(user_id: str = "demo-merchant") -> dict:
    """Demo adapter for the Marketing & Campaign Intelligence tab. Replace with an authenticated API call later."""
    kpis = [
        KPI("Active Campaign", "48", "+12%", "currently running", 72, (30, 35, 33, 41, 44, 48, 52, 56), "activity"),
        KPI("Completed Campaign", "124", "+18%", "all time", 78, (40, 44, 47, 52, 58, 61, 67, 72), "check-circle"),
        KPI("Campaign Reach", "2.4M", "+8.4%", "unique consumers", 74, (45, 49, 47, 55, 59, 63, 66, 71), "users"),
        KPI("Impression", "8.2M", "+14.2%", "ad views", 81, (38, 46, 44, 53, 60, 58, 68, 75), "eye"),
        KPI("CTR", "3.4%", "+0.8pp", "click-through rate", 72, (41, 44, 50, 48, 56, 61, 64, 70), "target"),
        KPI("Voucher Claimed", "820K", "+22.4%", "total claimed", 86, (36, 42, 40, 51, 58, 57, 68, 77), "gift"),
        KPI("Voucher Redeemed", "428.8K", "+18.8%", "claimed to redeemed", 83, (39, 44, 43, 50, 57, 60, 66, 73), "check-square"),
        KPI("Conversion Rate", "2.8%", "+0.5pp", "view to purchase", 69, (44, 47, 49, 52, 51, 58, 62, 66), "trending-up"),
        KPI("Campaign ROI", "4.2×", "+0.8×", "revenue per spend", 88, (40, 46, 43, 55, 62, 58, 68, 76), "zap"),
        KPI("Cost per Redemption", "Rp 3,200", "-8.2%", "lower is better", 75, (70, 68, 66, 67, 62, 60, 57, 54), "credit-card"),
    ]
    return {
        "user_id": user_id,
        "kpis": kpis,
        "funnel": [("Impression", 8_200_000), ("View", 4_100_000), ("Click", 820_000), ("Voucher Claim", 410_000), ("Voucher Saved", 280_000), ("Voucher Redeemed", 188_000), ("Purchase", 142_000), ("Repeat Purchase", 66_000)],
        "ads": [
            ("Video Ads", "1,200K", "42%", "4.2%", "76%", "3.4%"),
            ("Digital Ads", "800K", "36%", "3.1%", "68%", "2.8%"),
            ("Banner Ads", "240K", "18%", "1.8%", "52%", "1.2%"),
            ("Nearby Promotion", "160K", "12%", "2.4%", "44%", "1.6%"),
        ],
        "lifecycle": [120, 135, 130, 150, 165, 160, 178, 190, 185, 205, 215, 230],
        "status": [("Issued", 2_100_000, "#d9deea"), ("Claimed", 820_000, "#a9c8f5"), ("Saved", 280_000, "#5b9bf0"), ("Redeemed", 188_000, "#3b57c0"), ("Expired", 812_000, "#f5a3a3")],
        "top": ("Campaign Merdeka", "Rp 840M", 88),
        "bottom": ("Bakery Weekday Deal", "Rp 12M", 8),
        "timeline": [("Merdeka Launch", "Jun 4–7", "#a5b4e8"), ("Flash Sale Ramp", "Jun 8–16", "#a5b4e8"), ("Ramadan Peak", "Jun 18–21", "#3b57c0"), ("Momentum Hold", "Jun 22–30", "#c5cad3")],
        "roi": [2.4, 2.6, 2.5, 2.9, 3.1, 3.0, 3.4, 3.6, 3.5, 3.9, 4.0, 4.2],
        "forecast": [("Campaign Reach Forecast", "2.8M", "+16.8%", "trending-up"), ("Campaign ROI Forecast", "4.8×", "+14.3%", "zap"), ("Voucher Redemption Forecast", "520K", "+21.4%", "credit-card"), ("Campaign Completion Forecast", "91%", "+7.0pp", "check-circle")],
    }



def make_kpis(rows: list[tuple[str, str, str, str, str]]) -> list[KPI]:
    return [KPI(label, value, delta, note, 72, _DOWN if delta.startswith("-") else _UP[i % len(_UP)], icon) for i, (label, value, delta, note, icon) in enumerate(rows)]



@st.cache_resource
def load_consumer_data(user_id: str = "demo-merchant") -> dict:
    """Demo adapter for the Consumer & Merchant tab. Replace with an authenticated API call later."""
    return {
        "kpis": make_kpis([
            ("Total Consumers", "284.4K", "+8.8%", "all time", "users"),
            ("New Consumers", "24.2K", "+12.4%", "this month", "user-plus"),
            ("Returning Consumers", "88.4K", "+11.0%", "2+ purchases", "repeat"),
            ("Active Consumers", "152.8K", "+5.2%", "last 30 days", "activity"),
            ("Repeat Purchase", "31.1%", "+2.8pp", "repeat rate", "cart"),
            ("Average Spend", "Rp 158K", "+4.2%", "per consumer", "dollar"),
            ("Lifetime Value", "Rp 2.8M", "+6.5%", "avg lifetime", "trending-up"),
        ]),
        "gender": [("Male", 52, "52%", "#5b9bf0"), ("Female", 48, "48%", "#ec4899")],
        "age": [("13–17", 8), ("18–24", 28), ("25–34", 34), ("35–50", 22), ("50+", 8)],
        "generation": [("Gen Z", 18), ("Millennial", 48), ("Gen X", 24), ("Boomer", 10)],
        "occupation": [("Student", 22), ("Professional", 48), ("Self-Employed", 18), ("Other", 12)],
        "income": [("Low (<Rp 3M)", 24), ("Mid (Rp 3–7M)", 42), ("High (>Rp 7M)", 34)],
        "loyalty": [("Bronze", 45), ("Silver", 32), ("Gold", 18), ("Platinum", 5)],
        "fav_product": [("Iced Latte 250ml", "8.2K", 100), ("Teh Botol 500ml", "7.1K", 87), ("Oreo Original", "6.2K", 76)],
        "fav_merchant": [("Guardian BSD Central", "28.4K", 100), ("Indomaret Serpong", "24.2K", 85), ("Alfamart Gading", "18.8K", 66)],
        "frequency": [2.1, 2.3, 2.2, 2.6, 2.8, 2.7, 3.0, 3.2, 3.1, 3.4, 3.5, 3.7],
        "fav_category": [("Beverages", "48%", 100), ("Snacks", "32%", 67), ("Health & Beauty", "14%", 29)],
        "purchase_time": [("Morning (7–12)", 18), ("Afternoon (12–17)", 35), ("Evening (17–22)", 38), ("Night (22–7)", 9)],
        "merchants": [("Guardian BSD Central", "Rp 420M", "+12.4%"), ("Indomaret Serpong", "Rp 360M", "+9.2%"), ("Alfamart Gading", "Rp 280M", "+5.1%")],
        "merchant_trend": [210, 240, 255, 270, 262, 290, 310, 305, 330, 345, 340, 372],
        "journey": [("Advertisement", 480_000), ("Claim", 210_000), ("Redeem", 88_000), ("Purchase", 42_000), ("Repeat Purchase", 13_000)],
        "forecast": [("Consumer Growth Forecast", "+32.8K", "+12.5%", "trending-up"), ("Repeat Purchase Probability", "42.1%", "+8.2pp", "repeat"), ("Churn Probability", "8.4%", "-2.1pp", "alert-circle"), ("Merchant Growth Forecast", "+18%", "+5.4pp", "percent")],
    }



@st.cache_resource
def load_product_data(user_id: str = "demo-merchant") -> dict:
    """Demo adapter for the Product & Sales tab. Replace with an authenticated API call later."""
    return {
        "sales_kpis": make_kpis([
            ("Revenue", "Rp 4.2B", "+12.4%", "total sales", "trending-up"),
            ("Net Revenue", "Rp 3.4B", "+11.2%", "after costs", "dollar"),
            ("Gross Revenue", "Rp 5.1B", "+13.8%", "before costs", "bar-chart"),
            ("Average Basket", "Rp 48K", "-2.1%", "per transaction", "cart"),
            ("Voucher Cost", "Rp 280M", "+8.2%", "redemption cost", "gift"),
            ("Promotion Cost", "Rp 420M", "+6.5%", "marketing spend", "megaphone"),
            ("Revenue Growth", "+14.2%", "+2.1pp", "YoY growth", "arrow-up-right"),
        ]),
        "product_kpis": make_kpis([
            ("Product Revenue", "Rp 4.2B", "+12.4%", "total from products", "package"),
            ("Product Sales", "1.24M", "+18.0%", "units sold", "cart"),
            ("Redemption", "428.8K", "+18.8%", "voucher redeemed", "tag"),
            ("Sampling", "184K", "+24.2%", "samples distributed", "flask"),
            ("Conversion", "2.8%", "+0.5pp", "sample to buy", "trending-up"),
            ("Repeat Purchase", "31.1%", "+2.8pp", "repeat rate", "repeat"),
        ]),
        "analysis": [
            ("Category", [("Beverages", 2400, "Rp 2.4B"), ("Snacks", 1200, "Rp 1.2B"), ("Health & Beauty", 600, "Rp 0.6B")]),
            ("Brand", [("Brand A", 420, "420K"), ("Brand B", 360, "360K"), ("Brand C", 285, "285K")]),
            ("Flavor", [("Original", 580, "580K"), ("Strawberry", 380, "380K"), ("Vanilla", 280, "280K")]),
            ("Size Variant", [("250ml", 680, "680K"), ("500ml", 380, "380K"), ("1L", 180, "180K")]),
            ("Package Type", [("Can", 520, "520K"), ("Bottle", 480, "480K"), ("Pouch", 240, "240K")]),
        ],
        "lifecycle": [("New", 12, 8, "#22b07d"), ("Growing", 45, 30, "#5b9bf0"), ("Mature", 72, 48, "#3b57c0"), ("Declining", 21, 14, "#ef4444")],
        "ranking": [
            ("TOP SELLING", [("Iced Latte 250ml", "280K", 100), ("Teh Botol 500ml", "240K", 86), ("Oreo Original", "210K", 75)], BAR),
            ("TOP REDEEMED", [("Voucher Beverage Pack", "184K", 100), ("Snack Combo Pack", "142K", 77), ("Loyalty Reward Item", "102K", 55)], BAR),
            ("TOP SAMPLED", [("New Juice Flavor", "82K", 100), ("Energy Drink Beta", "68K", 83), ("Probiotic Yogurt", "54K", 66)], BAR),
            ("FAST MOVING", [("Iced Latte 250ml", "+45%", 100), ("Teh Botol 500ml", "+38%", 84), ("Oreo Original", "+32%", 71)], BAR),
            ("SLOW MOVING", [("Expired Bakery Item", "-28%", 100), ("Regional Limited Edition", "-18%", 64), ("Vintage Formula Drink", "-12%", 43)], "#9aa3b2"),
        ],
        "revenue_trend": [280, 310, 295, 340, 352, 348, 385, 410, 398, 440, 452, 480],
        "sales_trend": [62, 70, 66, 78, 84, 80, 92, 101, 96, 108, 104, 118],
        "forecast": [("Demand Forecast", "1.42M", "+14.5%", "trending-up"), ("Revenue Forecast", "Rp 4.8B", "+14.3%", "dollar"), ("Sampling Forecast", "224K", "+21.7%", "flask"), ("Sales Forecast", "+16.2%", "+4.8pp", "bar-chart")],
    }



@st.cache_resource
def load_operations_data(user_id: str = "demo-merchant") -> dict:
    """Demo adapter for the Klikko-Hub & Operational tab. Replace with an authenticated API call later."""
    return {
        "kpis": make_kpis([
            ("Total Machine", "284", "+8.2%", "all machines", "cpu"),
            ("Active Machine", "268", "+5.4%", "currently operational", "activity"),
            ("Machine Revenue", "Rp 2.1B", "+14.2%", "total from machines", "trending-up"),
            ("Machine Utilization", "82.4%", "+6.8pp", "capacity usage", "gauge"),
            ("Availability", "96.2%", "+1.2pp", "uptime", "check-circle"),
            ("Downtime", "8.2h", "-12.4%", "avg per week", "alert-triangle"),
        ]),
        "ranking": [("Vending BSD Central 01", "Rp 180M", 95), ("Vending Alam Sutera 02", "Rp 156M", 82), ("Vending Gading 03", "Rp 142M", 75)],
        "sales_trend": [120, 135, 128, 150, 162, 158, 176, 190, 184, 205, 214, 232],
        "snapshot": [("Total Revenue", 84, "Rp 2.1B", BAR), ("Units Sold", 76, "842K", BAR), ("Avg Basket", 65, "Rp 2.5K", BAR)],
        "sampling": [("Sample Distributed", "184K", "+24.2%", "flask"), ("Unique Consumer", "124K", "+18.8%", "users"), ("Survey Completion", "82%", "+8.2pp", "clipboard"), ("Purchase Conversion", "28.4%", "+4.2pp", "cart"), ("Voucher Earned", "52.4K", "+14.8%", "gift")],
        "media": [
            ("Video & Banner", [("Video Impression", "4.2M", "+18.4%"), ("Banner Impression", "2.8M", "+12.2%")]),
            ("Digital & Engagement", [("Digital Ads", "1.8M", "+14.6%"), ("QR Scan", "284K", "+22.4%")]),
            ("Media Performance", [("Ads Engagement", "18.2%", "+3.4pp"), ("Playlist Pref.", "92%", "+2.1pp")]),
        ],
        "machine_revenue": [("Vending BSD Central 01", "Rp 180M", 95), ("Vending Alam Sutera 02", "Rp 156M", 82), ("Vending Gading 03", "Rp 142M", 75)],
        "status": [("Operational", 268, 94, "#22b07d"), ("Maintenance", 12, 4, "#f59e0b"), ("Offline", 4, 2, "#ef4444")],
        "regions": [("Jakarta", 68), ("Central Java", 62), ("Banten", 52), ("West Java", 48), ("East Java", 31), ("Other", 23)],
        "forecast": [("Machine Traffic Forecast", "2.4M", "+18.2%", "activity"), ("Revenue Forecast", "Rp 2.5B", "+19.0%", "trending-up"), ("Sampling Demand Forecast", "224K", "+21.7%", "flask"), ("Retail Media Forecast", "+24.6%", "+6.8pp", "monitor"), ("Selling Demand Forecast", "+22.4%", "+5.2pp", "cart")],
    }

