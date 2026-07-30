"""Replaceable data-access layer for the Merchant Insights dashboard.

The app uses ``MockDashboardRepository`` by default. A backend team can provide
its own repository factory and set:

    DASHBOARD_REPOSITORY_FACTORY=package.module:create_repository

The returned object must implement the methods in ``DashboardRepository``.
All methods receive the selected dashboard date range.
"""

from __future__ import annotations

from datetime import date
from importlib import import_module
import os
from typing import Protocol, runtime_checkable

import pandas as pd


@runtime_checkable
class DashboardRepository(Protocol):
    """Contract implemented by mock, SQL, warehouse, or API repositories."""

    def load_kpi_data(
        self,
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame: ...

    def load_dashboard_data(
        self,
        start_date: date,
        end_date: date,
    ) -> tuple[pd.DataFrame, pd.DataFrame]: ...

    def load_product_performance_data(
        self,
        start_date: date,
        end_date: date,
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]: ...

    def load_product_detail_data(
        self,
        start_date: date,
        end_date: date,
    ) -> tuple[pd.DataFrame, pd.DataFrame]: ...

    def load_merchant_performance_data(
        self,
        start_date: date,
        end_date: date,
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]: ...

    def load_customer_insights_data(
        self,
        start_date: date,
        end_date: date,
    ) -> tuple[
        pd.DataFrame,
        dict[str, float | str],
        pd.DataFrame,
        pd.DataFrame,
    ]: ...


class MockDashboardRepository:
    """Current demo dataset; replace with a backend repository in production."""

    def load_kpi_data(
        self,
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        del start_date, end_date
        return pd.DataFrame(
            {
                "metric_key": [
                    "vouchers_redeemed",
                    "redemption_value",
                    "campaigns",
                    "customers",
                    "new_customers",
                ],
                "value": [18_746, 156_800_000, 24, 12_894, 2_349],
                "change_pct": [14.6, 18.3, 9.1, 12.8, 15.7],
                "comparison_label": ["vs Apr 2025"] * 5,
            }
        )

    def load_dashboard_data(
        self,
        start_date: date,
        end_date: date,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        del start_date, end_date
        trend_data = pd.DataFrame(
            {
                "period": [
                    "1 – 4 Mei",
                    "5 – 11 Mei",
                    "12 – 18 Mei",
                    "19 – 25 Mei",
                    "26 – 31 Mei",
                ],
                "vouchers_redeemed": [3000, 3600, 3300, 4400, 4446],
                "redemption_value": [
                    22_000_000,
                    28_000_000,
                    25_000_000,
                    40_000_000,
                    41_800_000,
                ],
                "average_transaction_value": [7950, 8510, 7820, 8580, 8550],
            }
        )
        channel_data = pd.DataFrame(
            {
                "channel": ["In-store", "Klikko-Hub", "QR Payment", "Other"],
                "redemptions": [9028, 5245, 3075, 1398],
            }
        )
        return trend_data, channel_data

    def load_product_performance_data(
        self,
        start_date: date,
        end_date: date,
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        del start_date, end_date
        category_data = pd.DataFrame(
            {
                "category": [
                    "Beverages",
                    "Food",
                    "Snacks",
                    "Merchandise",
                    "Other",
                ],
                "redeemed": [5_000, 4_900, 2_800, 1_500, 900],
                "sampling": [2_842, 773, 628, 303, 345],
            }
        )
        sampled_products = pd.DataFrame(
            {
                "product": [
                    "Iced Latte",
                    "Americano",
                    "Caramel Macchiato",
                    "Chocolate Croissant",
                    "Mineral Water",
                ],
                "count": [3_246, 2_814, 2_368, 1_987, 1_745],
            }
        )
        redeemed_products = pd.DataFrame(
            {
                "product": [
                    "Iced Latte",
                    "Americano",
                    "Caramel Macchiato",
                    "Chicken Sandwich",
                    "Signature Burger",
                ],
                "count": [4_820, 4_215, 3_184, 2_789, 2_576],
            }
        )
        return category_data, sampled_products, redeemed_products

    def load_product_detail_data(
        self,
        start_date: date,
        end_date: date,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        del start_date, end_date
        category_overview = pd.DataFrame(
            {
                "category": [
                    "Beverages",
                    "Food",
                    "Snacks",
                    "Merchandise",
                    "Other",
                ],
                "vouchers_redeemed": [7_842, 5_673, 3_428, 1_803, 1_245],
                "redeemed_share": [41.8, 30.3, 18.3, 9.6, 6.6],
                "redemption_value": [
                    62_450_000,
                    48_230_000,
                    24_180_000,
                    14_560_000,
                    7_420_000,
                ],
                "unique_customers": [5_126, 3_842, 2_614, 1_425, 892],
                "conversion_rate": [18.6, 16.9, 14.2, 13.1, 11.8],
            }
        )
        hourly_redemptions = pd.DataFrame(
            {
                "hour": list(range(25)),
                "redemptions": [
                    560,
                    260,
                    70,
                    45,
                    60,
                    250,
                    820,
                    1_300,
                    1_520,
                    1_450,
                    1_850,
                    2_650,
                    3_246,
                    2_320,
                    1_850,
                    1_520,
                    1_620,
                    1_920,
                    2_680,
                    2_580,
                    2_300,
                    680,
                    280,
                    110,
                    55,
                ],
            }
        )
        hourly_redemptions["time_range"] = hourly_redemptions["hour"].map(
            lambda hour: (
                f"{hour:02d}:00 – {(hour + 1):02d}:00"
                if hour < 24
                else "24:00"
            )
        )
        hourly_redemptions["selected_label"] = hourly_redemptions.apply(
            lambda row: f"{row['time_range']}  •  {row['redemptions']:,.0f}",
            axis=1,
        )
        return category_overview, hourly_redemptions

    def load_merchant_performance_data(
        self,
        start_date: date,
        end_date: date,
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        del start_date, end_date
        outlets = pd.DataFrame(
            {
                "name": [
                    "Pujangga Coffee BSD Central",
                    "Pujangga Coffee AEON Mall BSD",
                    "Pujangga Coffee The Breeze",
                    "Pujangga Coffee ITC BSD",
                    "Pujangga Coffee QBig BSD",
                ],
                "redemptions": [2_890, 2_456, 1_987, 1_643, 1_298],
            }
        )
        campaigns = pd.DataFrame(
            {
                "name": [
                    "Weekend Flash Sale",
                    "Buy 1 Get 1 Iced Latte",
                    "Payday Treats",
                    "Coffee Lovers Promo",
                    "New Member Special",
                ],
                "redemptions": [6_842, 4_928, 3_764, 2_985, 2_227],
            }
        )
        locations = pd.DataFrame(
            {
                "name": [
                    "BSD City",
                    "Gading Serpong",
                    "Tangerang Selatan",
                    "Alam Sutera",
                    "Jakarta Selatan",
                ],
                "redemptions": [5_842, 4_125, 3_246, 2_734, 2_213],
            }
        )
        return outlets, campaigns, locations

    def load_customer_insights_data(
        self,
        start_date: date,
        end_date: date,
    ) -> tuple[
        pd.DataFrame,
        dict[str, float | str],
        pd.DataFrame,
        pd.DataFrame,
    ]:
        del start_date, end_date
        customer_segments = pd.DataFrame(
            {
                "segment": ["New Customers", "Returning Customers"],
                "customers": [2_349, 10_545],
            }
        )
        loyalty = {
            "average_transactions": 3.7,
            "repeat_customer_percentage": 28.0,
            "top_age_group": "25 – 34 years",
            "top_age_group_percentage": 42.0,
        }
        gender = pd.DataFrame(
            {
                "gender": ["Male", "Female"],
                "percentage": [54.0, 46.0],
            }
        )
        payment_methods = pd.DataFrame(
            {
                "method": ["E-Wallet", "QR Payment", "Cash", "Card"],
                "percentage": [56.0, 28.0, 11.0, 5.0],
            }
        )
        return customer_segments, loyalty, gender, payment_methods


REQUIRED_COLUMNS: dict[str, set[str]] = {
    "kpi": {"metric_key", "value", "change_pct", "comparison_label"},
    "trend": {
        "period",
        "vouchers_redeemed",
        "redemption_value",
        "average_transaction_value",
    },
    "channel": {"channel", "redemptions"},
    "category_performance": {"category", "redeemed", "sampling"},
    "sampled_products": {"product", "count"},
    "redeemed_products": {"product", "count"},
    "category_overview": {
        "category",
        "vouchers_redeemed",
        "redeemed_share",
        "redemption_value",
        "unique_customers",
        "conversion_rate",
    },
    "hourly_redemptions": {
        "hour",
        "redemptions",
        "time_range",
        "selected_label",
    },
    "leaderboard": {"name", "redemptions"},
    "customer_segments": {"segment", "customers"},
    "gender": {"gender", "percentage"},
    "payment_methods": {"method", "percentage"},
}


def validate_frame(frame: pd.DataFrame, schema_name: str) -> pd.DataFrame:
    """Fail early with a useful message when backend output changes shape."""
    if not isinstance(frame, pd.DataFrame):
        raise TypeError(f"{schema_name} must be a pandas DataFrame")
    missing = REQUIRED_COLUMNS[schema_name].difference(frame.columns)
    if missing:
        columns = ", ".join(sorted(missing))
        raise ValueError(f"{schema_name} is missing required columns: {columns}")
    return frame.copy()


def create_dashboard_repository() -> DashboardRepository:
    """Create the configured repository, defaulting to local demo data."""
    factory_path = os.getenv("DASHBOARD_REPOSITORY_FACTORY", "").strip()
    if not factory_path:
        return MockDashboardRepository()

    try:
        module_name, factory_name = factory_path.split(":", maxsplit=1)
    except ValueError as exc:
        raise ValueError(
            "DASHBOARD_REPOSITORY_FACTORY must use 'module:function' format"
        ) from exc

    module = import_module(module_name)
    factory = getattr(module, factory_name)
    repository = factory()
    if not isinstance(repository, DashboardRepository):
        raise TypeError(
            f"{factory_path} did not return a DashboardRepository-compatible object"
        )
    return repository
