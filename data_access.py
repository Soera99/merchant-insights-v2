"""Replaceable data-access layer for the Merchant Insights dashboard.

The app uses ``MockDashboardRepository`` by default. A backend team can provide
its own repository factory and set:

    DASHBOARD_REPOSITORY_FACTORY=package.module:create_repository

The returned object must implement the methods in ``DashboardRepository``.
All business-data methods receive one ``DashboardFilters`` object so a future
backend can apply province, city, and date conditions consistently.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from importlib import import_module
import json
import os
from typing import Protocol, runtime_checkable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd


# -----------------------------------------------------------------------------
# Filter model
# This immutable object is the single filter contract shared by UI and backend.
# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class DashboardFilters:
    province: str
    city: str
    start_date: date
    end_date: date


# -----------------------------------------------------------------------------
# Repository interface
# Backend teams implement this protocol using SQL, an API, or a data warehouse.
# -----------------------------------------------------------------------------
@runtime_checkable
class DashboardRepository(Protocol):
    """Contract implemented by mock, SQL, warehouse, or API repositories."""

    def load_filter_options(self) -> dict[str, list[str]]: ...

    def load_kpi_data(self, filters: DashboardFilters) -> pd.DataFrame: ...

    def load_dashboard_data(
        self,
        filters: DashboardFilters,
    ) -> tuple[pd.DataFrame, pd.DataFrame]: ...

    def load_campaign_performance_data(
        self,
        filters: DashboardFilters,
    ) -> tuple[pd.DataFrame, pd.DataFrame]: ...

    def load_product_performance_data(
        self,
        filters: DashboardFilters,
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]: ...

    def load_product_detail_data(
        self,
        filters: DashboardFilters,
    ) -> tuple[pd.DataFrame, pd.DataFrame]: ...

    def load_merchant_performance_data(
        self,
        filters: DashboardFilters,
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]: ...

    def load_customer_insights_data(
        self,
        filters: DashboardFilters,
    ) -> tuple[
        pd.DataFrame,
        dict[str, float | str],
        pd.DataFrame,
        pd.DataFrame,
    ]: ...


# -----------------------------------------------------------------------------
# Demo repository
# This keeps the dashboard usable before the internal database is connected.
# -----------------------------------------------------------------------------
class MockDashboardRepository:
    """Current demo dataset; replace with a backend repository in production."""

    def load_filter_options(self) -> dict[str, list[str]]:
        return {
            "All Provinces": ["All Cities"],
            "Banten": [
                "All Cities",
                "Tangerang Selatan",
                "Tangerang",
                "Serang",
            ],
            "DKI Jakarta": [
                "All Cities",
                "Jakarta Selatan",
                "Jakarta Pusat",
                "Jakarta Barat",
            ],
            "West Java": ["All Cities", "Bandung", "Bekasi", "Depok"],
        }

    def load_kpi_data(self, filters: DashboardFilters) -> pd.DataFrame:
        del filters
        return pd.DataFrame(
            {
                "metric_key": [
                    "active_campaigns",
                    "completed_campaigns",
                    "vouchers_claimed",
                    "vouchers_redeemed",
                    "total_consumers",
                    "new_consumers",
                    "stores_participated",
                    "redemption_rate",
                    "redemption_value",
                ],
                "value": [
                    25,
                    18,
                    84_320,
                    39_140,
                    152_400,
                    28_770,
                    120,
                    46.4,
                    156_800_000,
                ],
                "change_pct": [15.5, 8.2, 12.4, 15.5, 9.8, 18.1, 6.4, -2.3, 15.5],
                "comparison_label": ["vs. Apr 2026"] * 9,
            }
        )

    def load_dashboard_data(
        self,
        filters: DashboardFilters,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        del filters
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

    def load_campaign_performance_data(
        self,
        filters: DashboardFilters,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Return campaign KPIs and ordered conversion-funnel stages."""
        del filters
        campaign_metrics = pd.DataFrame(
            {
                "metric_key": [
                    "campaign_views",
                    "campaign_clicks",
                    "click_through_rate",
                    "claim_rate",
                    "total_vouchers_redeemed",
                    "total_redemption_value",
                    "average_transaction_value",
                ],
                "value": [
                    128_400,
                    54_200,
                    6.8,
                    24.5,
                    128_400,
                    156_800_000,
                    12_800,
                ],
                "change_pct": [15.5, 15.5, 2.5, 2.5, 15.5, 15.5, 2.5],
                "comparison_label": ["vs. Apr 2026"] * 7,
            }
        )
        funnel_data = pd.DataFrame(
            {
                "stage": ["View", "Click", "Claim", "Redeem"],
                "count": [128_400, 54_200, 21_800, 9_300],
                "percentage": [100.0, 42.0, 17.0, 7.0],
                "stage_order": [1, 2, 3, 4],
            }
        )
        return campaign_metrics, funnel_data

    def load_product_performance_data(
        self,
        filters: DashboardFilters,
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        del filters
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
        filters: DashboardFilters,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        del filters
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
        filters: DashboardFilters,
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        del filters
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
        filters: DashboardFilters,
    ) -> tuple[
        pd.DataFrame,
        dict[str, float | str],
        pd.DataFrame,
        pd.DataFrame,
    ]:
        del filters
        customer_segments = pd.DataFrame(
            {
                "segment": ["New Customers", "Returning Customers"],
                "customers": [2_349, 10_545],
            }
        )
        loyalty = {
            "average_transactions": 3.7,
            "repeat_customer_percentage": 28.0,
        }
        gender = pd.DataFrame(
            {
                "gender": ["Male", "Female"],
                "percentage": [54.0, 46.0],
            }
        )
        age_groups = pd.DataFrame(
            {
                "age_group": [
                    "Generation Z",
                    "Millennials",
                    "Generation X",
                    "Baby Boomers",
                ],
                "age_range": [
                    "18 – 29 years",
                    "30 – 45 years",
                    "46 – 61 years",
                    "62+ years",
                ],
                "percentage": [26.0, 42.0, 21.0, 11.0],
            }
        )
        return customer_segments, loyalty, gender, age_groups


# -----------------------------------------------------------------------------
# Backend API repository
# Every live dashboard endpoint uses the authenticated dashboard user's ID as
# the first request value and shares the same province, city, and date filters.
# -----------------------------------------------------------------------------
class ApiDashboardRepository(MockDashboardRepository):
    """Use the live backend APIs for every dashboard business-data section."""

    FILTER_OPTIONS_PATH = "/api/v1/partners/dashboard/filter-options"
    KPI_PATH = "/api/v1/partners/dashboard/kpis"
    CAMPAIGN_KPI_PATH = "/api/v1/partners/dashboard/campaign-performance/kpis"
    CAMPAIGN_FUNNEL_PATH = (
        "/api/v1/partners/dashboard/campaign-performance/funnel"
    )
    CAMPAIGN_TREND_PATH = (
        "/api/v1/partners/dashboard/campaign-performance/redemption-trend"
    )
    PRODUCT_TOP_CATEGORIES_PATH = (
        "/api/v1/partners/dashboard/product-performance/top-categories"
    )
    PRODUCT_TOP_SAMPLED_PATH = (
        "/api/v1/partners/dashboard/product-performance/top-sampled-products"
    )
    PRODUCT_TOP_PRODUCTS_PATH = (
        "/api/v1/partners/dashboard/product-performance/top-products"
    )
    PRODUCT_CATEGORY_OVERVIEW_PATH = (
        "/api/v1/partners/dashboard/product-performance/category-overview"
    )
    PRODUCT_REDEMPTION_TIME_PATH = (
        "/api/v1/partners/dashboard/product-performance/redemption-time"
    )
    PRODUCT_REDEMPTION_CHANNEL_PATH = (
        "/api/v1/partners/dashboard/product-performance/redemption-channel"
    )
    MERCHANT_BEST_OUTLETS_PATH = (
        "/api/v1/partners/dashboard/merchant-performance/best-outlets"
    )
    MERCHANT_BEST_CAMPAIGNS_PATH = (
        "/api/v1/partners/dashboard/merchant-performance/best-campaigns"
    )
    MERCHANT_TOP_LOCATIONS_PATH = (
        "/api/v1/partners/dashboard/merchant-performance/top-locations"
    )
    CUSTOMER_CONSUMER_TYPE_PATH = (
        "/api/v1/partners/dashboard/customer-insights/consumer-type"
    )
    CUSTOMER_LOYALTY_PATH = (
        "/api/v1/partners/dashboard/customer-insights/customer-loyalty"
    )
    CUSTOMER_GENDER_PATH = (
        "/api/v1/partners/dashboard/customer-insights/redemption-gender"
    )
    CUSTOMER_AGE_GROUP_PATH = (
        "/api/v1/partners/dashboard/customer-insights/age-group"
    )
    CAMPAIGN_METRIC_KEYS = (
        "campaign_views",
        "campaign_clicks",
        "click_through_rate",
        "claim_rate",
        "total_vouchers_redeemed",
        "total_redemption_value",
        "average_transaction_value",
    )

    def __init__(
        self,
        base_url: str,
        user_id: str,
        timeout_seconds: float = 10.0,
        bearer_token: str = "",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.user_id = user_id
        self.timeout_seconds = timeout_seconds
        self.bearer_token = bearer_token

    def _post(self, path: str, values: list[str]) -> dict[str, object]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.bearer_token:
            headers["Authorization"] = f"Bearer {self.bearer_token}"

        request = Request(
            f"{self.base_url}{path}",
            data=json.dumps({"values": values}).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.load(response)
        except HTTPError as exc:
            raise RuntimeError(
                f"Dashboard API returned HTTP {exc.code} for {path}"
            ) from exc
        except URLError as exc:
            raise RuntimeError(
                f"Dashboard API request failed for {path}: {exc.reason}"
            ) from exc
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ValueError(f"Dashboard API returned invalid JSON for {path}") from exc

        if not isinstance(payload, dict):
            raise ValueError(f"Dashboard API response for {path} must be an object")
        return payload

    def _filter_values(self, filters: DashboardFilters) -> list[str]:
        return [
            self.user_id,
            filters.province,
            filters.city,
            filters.start_date.isoformat(),
            filters.end_date.isoformat(),
        ]

    def _load_query_out(
        self,
        path: str,
        filters: DashboardFilters,
        dataset_name: str,
    ) -> list[dict[str, object]]:
        payload = self._post(path, self._filter_values(filters))
        response_content = payload.get("content", payload)
        try:
            query_out = response_content["vars"]["query_out"]
        except (KeyError, TypeError) as exc:
            raise ValueError(
                f"{dataset_name} response must contain vars.query_out or "
                "content.vars.query_out"
            ) from exc

        if not isinstance(query_out, list) or any(
            not isinstance(row, dict) for row in query_out
        ):
            raise ValueError(f"{dataset_name} query_out must be a list of objects")
        return query_out

    @staticmethod
    def _normalized_frame(
        rows: list[dict[str, object]],
        columns: list[str],
        aliases: dict[str, tuple[str, ...]],
        dataset_name: str,
        defaults: dict[str, object] | None = None,
    ) -> pd.DataFrame:
        """Map backend field aliases and preserve schemas for empty results."""
        if not rows:
            return pd.DataFrame(columns=columns)

        frame = pd.DataFrame(rows)
        rename_map: dict[str, str] = {}
        for target, candidates in aliases.items():
            if target in frame.columns:
                continue
            source = next(
                (candidate for candidate in candidates if candidate in frame.columns),
                None,
            )
            if source is not None:
                rename_map[source] = target
        frame = frame.rename(columns=rename_map)

        for column, default_value in (defaults or {}).items():
            if column not in frame.columns:
                frame[column] = default_value

        missing = set(columns).difference(frame.columns)
        if missing:
            names = ", ".join(sorted(missing))
            raise ValueError(f"{dataset_name} is missing: {names}")
        return frame.loc[:, columns].copy()

    def load_filter_options(self) -> dict[str, list[str]]:
        payload = self._post(self.FILTER_OPTIONS_PATH, [self.user_id])
        response_content = payload.get("content", payload)
        try:
            filter_options = response_content["vars"]["filter_options"]
        except (KeyError, TypeError) as exc:
            raise ValueError(
                "Filter-options response must contain vars.filter_options "
                "or content.vars.filter_options"
            ) from exc

        if not isinstance(filter_options, dict) or not filter_options:
            raise ValueError("vars.filter_options must be a non-empty object")

        normalized: dict[str, list[str]] = {}
        for province, cities in filter_options.items():
            if not isinstance(province, str) or not province:
                raise ValueError(
                    "Every filter-options province must be a non-empty string"
                )
            if (
                not isinstance(cities, list)
                or not cities
                or any(not isinstance(city, str) or not city for city in cities)
            ):
                raise ValueError(
                    f"Filter-options cities for {province!r} must be a "
                    "non-empty string list"
                )

            ordered_cities = list(dict.fromkeys(cities))
            if "All Cities" in ordered_cities:
                ordered_cities.remove("All Cities")
                ordered_cities.insert(0, "All Cities")
            normalized[province] = ordered_cities

        if "All Provinces" in normalized:
            all_provinces = normalized.pop("All Provinces")
            normalized = {"All Provinces": all_provinces, **normalized}
        return normalized

    def load_kpi_data(self, filters: DashboardFilters) -> pd.DataFrame:
        query_out = self._load_query_out(self.KPI_PATH, filters, "KPI")
        return pd.DataFrame(query_out)

    def load_dashboard_data(
        self,
        filters: DashboardFilters,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        query_out = self._load_query_out(
            self.CAMPAIGN_TREND_PATH,
            filters,
            "Campaign redemption trend",
        )
        trend_data = self._normalized_frame(
            query_out,
            ["period", "vouchers_redeemed", "redemption_value"],
            {
                "period": ("date", "redemption_date"),
                "vouchers_redeemed": ("redemption_count", "redeemed_count"),
                "redemption_value": ("total_redemption_value",),
            },
            "Campaign redemption trend",
        )
        required = {"period", "vouchers_redeemed", "redemption_value"}
        missing = required.difference(trend_data.columns)
        if missing:
            columns = ", ".join(sorted(missing))
            raise ValueError(f"Campaign redemption trend is missing: {columns}")

        if trend_data.empty:
            trend_data["average_transaction_value"] = pd.Series(dtype="float64")
        else:
            parsed_periods = pd.to_datetime(trend_data["period"], errors="coerce")
            if parsed_periods.isna().any():
                raise ValueError(
                    "Campaign redemption trend contains an invalid period"
                )
            trend_data["period"] = parsed_periods.dt.strftime("%d %b")
            voucher_counts = pd.to_numeric(
                trend_data["vouchers_redeemed"], errors="coerce"
            )
            redemption_values = pd.to_numeric(
                trend_data["redemption_value"], errors="coerce"
            )
            if voucher_counts.isna().any() or redemption_values.isna().any():
                raise ValueError("Campaign redemption trend values must be numeric")
            trend_data["average_transaction_value"] = redemption_values.div(
                voucher_counts.where(voucher_counts != 0),
            ).fillna(0.0)

        channel_rows = self._load_query_out(
            self.PRODUCT_REDEMPTION_CHANNEL_PATH,
            filters,
            "Product redemption channel",
        )
        channel_data = self._normalized_frame(
            channel_rows,
            ["channel", "redemptions"],
            {"redemptions": ("redemption_count", "redeemed_count", "count")},
            "Product redemption channel",
        )
        return trend_data, channel_data

    def load_campaign_performance_data(
        self,
        filters: DashboardFilters,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        metric_rows = self._load_query_out(
            self.CAMPAIGN_KPI_PATH,
            filters,
            "Campaign KPI",
        )
        if not metric_rows:
            metric_values = {
                metric_key: 0 for metric_key in self.CAMPAIGN_METRIC_KEYS
            }
        elif len(metric_rows) != 1:
            raise ValueError("Campaign KPI query_out must contain exactly one object")
        else:
            metric_values = metric_rows[0]
        missing_metrics = set(self.CAMPAIGN_METRIC_KEYS).difference(metric_values)
        if missing_metrics:
            keys = ", ".join(sorted(missing_metrics))
            raise ValueError(f"Campaign KPI response is missing metrics: {keys}")
        campaign_metrics = pd.DataFrame(
            [
                {
                    "metric_key": metric_key,
                    "value": metric_values[metric_key],
                    "change_pct": 0.0,
                    "comparison_label": "comparison not implemented",
                }
                for metric_key in self.CAMPAIGN_METRIC_KEYS
            ]
        )

        funnel_rows = self._load_query_out(
            self.CAMPAIGN_FUNNEL_PATH,
            filters,
            "Campaign funnel",
        )
        funnel_data = self._normalized_frame(
            funnel_rows,
            ["stage", "count", "stage_order"],
            {"count": ("value", "consumer_count")},
            "Campaign funnel",
        )
        required_funnel = {"stage", "count", "stage_order"}
        missing_funnel = required_funnel.difference(funnel_data.columns)
        if missing_funnel:
            columns = ", ".join(sorted(missing_funnel))
            raise ValueError(f"Campaign funnel is missing: {columns}")
        funnel_data["count"] = pd.to_numeric(funnel_data["count"], errors="coerce")
        if funnel_data["count"].isna().any():
            raise ValueError("Campaign funnel values must be numeric")
        denominator = funnel_data["count"].max()
        funnel_data["percentage"] = (
            funnel_data["count"].div(denominator).mul(100.0)
            if denominator > 0
            else 0.0
        )
        return campaign_metrics, funnel_data

    def load_product_performance_data(
        self,
        filters: DashboardFilters,
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        category_rows = self._load_query_out(
            self.PRODUCT_TOP_CATEGORIES_PATH, filters, "Top categories"
        )
        category_data = self._normalized_frame(
            category_rows,
            ["category", "redeemed", "sampling"],
            {
                "category": ("category_name", "name"),
                "redeemed": (
                    "redemption_count",
                    "redeemed_count",
                    "vouchers_redeemed",
                ),
                "sampling": (
                    "sampling_count",
                    "sampled_count",
                    "sample_count",
                    "samples",
                ),
            },
            "Top categories",
        )

        sampled_rows = self._load_query_out(
            self.PRODUCT_TOP_SAMPLED_PATH, filters, "Top sampled products"
        )
        sampled_products = self._normalized_frame(
            sampled_rows,
            ["product", "count"],
            {
                "product": ("product_name", "name", "title"),
                "count": (
                    "sampling_count",
                    "sampled_count",
                    "sample_count",
                    "samples",
                ),
            },
            "Top sampled products",
        )

        product_rows = self._load_query_out(
            self.PRODUCT_TOP_PRODUCTS_PATH, filters, "Top products"
        )
        redeemed_products = self._normalized_frame(
            product_rows,
            ["product", "count"],
            {
                "product": ("product_name", "name", "title"),
                "count": (
                    "redemption_count",
                    "redeemed_count",
                    "vouchers_redeemed",
                ),
            },
            "Top products",
        )
        return category_data, sampled_products, redeemed_products

    def load_product_detail_data(
        self,
        filters: DashboardFilters,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        overview_rows = self._load_query_out(
            self.PRODUCT_CATEGORY_OVERVIEW_PATH,
            filters,
            "Category overview",
        )
        category_overview = self._normalized_frame(
            overview_rows,
            [
                "category",
                "vouchers_redeemed",
                "redeemed_share",
                "redemption_value",
                "unique_customers",
                "conversion_rate",
            ],
            {
                "category": ("category_name", "name"),
                "vouchers_redeemed": ("redemption_count", "redeemed_count"),
                "redeemed_share": (
                    "redemption_share",
                    "redemption_percentage",
                    "share_pct",
                    "percentage",
                ),
                "redemption_value": ("total_redemption_value",),
                "unique_customers": ("customer_count", "consumer_count"),
                "conversion_rate": ("conversion_pct",),
            },
            "Category overview",
            defaults={
                "redemption_value": 0,
                "unique_customers": 0,
                "conversion_rate": 0.0,
            },
        )

        time_rows = self._load_query_out(
            self.PRODUCT_REDEMPTION_TIME_PATH,
            filters,
            "Redemption time",
        )
        hourly_redemptions = self._normalized_frame(
            time_rows,
            ["hour", "redemptions"],
            {"redemptions": ("redemption_count", "redeemed_count", "count")},
            "Redemption time",
        )
        hourly_redemptions["time_range"] = hourly_redemptions["hour"].map(
            lambda hour: f"{int(hour):02d}:00 – {(int(hour) + 1):02d}:00"
        )
        hourly_redemptions["selected_label"] = hourly_redemptions.apply(
            lambda row: f"{row['time_range']}  •  {row['redemptions']:,.0f}",
            axis=1,
        )
        return category_overview, hourly_redemptions

    def _load_leaderboard(
        self,
        path: str,
        filters: DashboardFilters,
        dataset_name: str,
        name_aliases: tuple[str, ...],
    ) -> pd.DataFrame:
        rows = self._load_query_out(path, filters, dataset_name)
        return self._normalized_frame(
            rows,
            ["name", "redemptions"],
            {
                "name": name_aliases,
                "redemptions": (
                    "redemption_count",
                    "redeemed_count",
                    "vouchers_redeemed",
                    "count",
                ),
            },
            dataset_name,
        )

    def load_merchant_performance_data(
        self,
        filters: DashboardFilters,
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        outlets = self._load_leaderboard(
            self.MERCHANT_BEST_OUTLETS_PATH,
            filters,
            "Best outlets",
            ("store_name", "outlet_name", "merchant_name"),
        )
        campaigns = self._load_leaderboard(
            self.MERCHANT_BEST_CAMPAIGNS_PATH,
            filters,
            "Best campaigns",
            ("campaign_name", "voucher_program_name"),
        )
        locations = self._load_leaderboard(
            self.MERCHANT_TOP_LOCATIONS_PATH,
            filters,
            "Top locations",
            ("location", "city", "city_name", "province"),
        )
        return outlets, campaigns, locations

    def load_customer_insights_data(
        self,
        filters: DashboardFilters,
    ) -> tuple[
        pd.DataFrame,
        dict[str, float | str],
        pd.DataFrame,
        pd.DataFrame,
    ]:
        segment_rows = self._load_query_out(
            self.CUSTOMER_CONSUMER_TYPE_PATH, filters, "Consumer type"
        )
        customer_segments = self._normalized_frame(
            segment_rows,
            ["segment", "customers"],
            {
                "segment": ("consumer_type", "customer_type", "type", "name"),
                "customers": (
                    "customer_count",
                    "consumer_count",
                    "total_consumers",
                    "count",
                ),
            },
            "Consumer type",
        )

        loyalty_rows = self._load_query_out(
            self.CUSTOMER_LOYALTY_PATH, filters, "Customer loyalty"
        )
        if loyalty_rows and "loyalty_type" in loyalty_rows[0]:
            loyalty_frame = pd.DataFrame(loyalty_rows)
            repeat_rows = loyalty_frame.loc[
                loyalty_frame["loyalty_type"]
                .astype(str)
                .str.lower()
                .str.contains("repeat")
            ]
            if not repeat_rows.empty and "percentage" in repeat_rows.columns:
                repeat_percentage = float(repeat_rows.iloc[0]["percentage"])
            elif "customer_count" in loyalty_frame.columns:
                counts = pd.to_numeric(
                    loyalty_frame["customer_count"], errors="coerce"
                ).fillna(0)
                repeat_count = counts.loc[repeat_rows.index].sum()
                repeat_percentage = (
                    float(repeat_count / counts.sum() * 100)
                    if counts.sum()
                    else 0.0
                )
            else:
                repeat_percentage = 0.0
            average_source = next(
                (
                    column
                    for column in (
                        "average_transactions",
                        "avg_transactions",
                        "average_transactions_per_customer",
                        "avg_transactions_per_customer",
                    )
                    if column in loyalty_frame.columns
                ),
                None,
            )
            loyalty = {
                "average_transactions": (
                    float(loyalty_frame.iloc[0][average_source])
                    if average_source
                    else 0.0
                ),
                "repeat_customer_count": (
                    int(
                        pd.to_numeric(
                            repeat_rows.iloc[0].get("customer_count", 0),
                            errors="coerce",
                        )
                    )
                    if not repeat_rows.empty
                    else 0
                ),
                "repeat_customer_percentage": repeat_percentage,
            }
        else:
            loyalty_frame = self._normalized_frame(
                loyalty_rows,
                ["average_transactions", "repeat_customer_percentage"],
                {
                    "average_transactions": (
                        "avg_transactions",
                        "average_transactions_per_customer",
                        "avg_transactions_per_customer",
                    ),
                    "repeat_customer_percentage": (
                        "repeat_customer_pct",
                        "repeat_percentage",
                        "repeat_rate",
                    ),
                },
                "Customer loyalty",
            )
            loyalty = (
                {
                    "average_transactions": loyalty_frame.iloc[0][
                        "average_transactions"
                    ],
                    "repeat_customer_percentage": loyalty_frame.iloc[0][
                        "repeat_customer_percentage"
                    ],
                }
                if not loyalty_frame.empty
                else {
                    "average_transactions": 0.0,
                    "repeat_customer_percentage": 0.0,
                }
            )

        gender_rows = self._load_query_out(
            self.CUSTOMER_GENDER_PATH, filters, "Redemption gender"
        )
        gender = self._percentage_frame(
            gender_rows,
            label="gender",
            label_aliases=("gender_name", "name"),
            dataset_name="Redemption gender",
        )

        age_rows = self._load_query_out(
            self.CUSTOMER_AGE_GROUP_PATH, filters, "Age group"
        )
        age_groups = self._normalized_frame(
            age_rows,
            ["age_group", "age_range", "percentage"],
            {
                "age_group": ("generation", "group", "name"),
                "age_range": ("range", "age_range_label"),
                "percentage": (
                    "redemption_percentage",
                    "share_pct",
                    "share",
                ),
            },
            "Age group",
            defaults={"age_range": ""},
        )
        return customer_segments, loyalty, gender, age_groups

    def _percentage_frame(
        self,
        rows: list[dict[str, object]],
        label: str,
        label_aliases: tuple[str, ...],
        dataset_name: str,
    ) -> pd.DataFrame:
        if not rows:
            return pd.DataFrame(columns=[label, "percentage"])
        frame = pd.DataFrame(rows)
        if label not in frame.columns:
            source = next(
                (name for name in label_aliases if name in frame.columns), None
            )
            if source is not None:
                frame = frame.rename(columns={source: label})
        if "percentage" not in frame.columns:
            percentage_source = next(
                (
                    name
                    for name in (
                        "redemption_percentage",
                        "share_pct",
                        "share",
                    )
                    if name in frame.columns
                ),
                None,
            )
            if percentage_source is not None:
                frame = frame.rename(columns={percentage_source: "percentage"})
            else:
                count_source = next(
                    (
                        name
                        for name in (
                            "redemption_count",
                            "redeemed_count",
                            "count",
                        )
                        if name in frame.columns
                    ),
                    None,
                )
                if count_source is not None:
                    counts = pd.to_numeric(frame[count_source], errors="coerce")
                    total = counts.sum()
                    frame["percentage"] = (
                        counts.div(total).mul(100) if total else 0.0
                    )
        missing = {label, "percentage"}.difference(frame.columns)
        if missing:
            names = ", ".join(sorted(missing))
            raise ValueError(f"{dataset_name} is missing: {names}")
        if label == "gender":
            frame[label] = frame[label].astype(str).str.replace("_", " ").str.title()
        return frame[[label, "percentage"]].copy()


# -----------------------------------------------------------------------------
# Data schemas
# These checks fail early when a backend query returns missing columns.
# -----------------------------------------------------------------------------
REQUIRED_COLUMNS: dict[str, set[str]] = {
    "kpi": {"metric_key", "value", "change_pct", "comparison_label"},
    "campaign_metrics": {
        "metric_key",
        "value",
        "change_pct",
        "comparison_label",
    },
    "campaign_funnel": {"stage", "count", "percentage", "stage_order"},
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
    "age_groups": {"age_group", "age_range", "percentage"},
}


# -----------------------------------------------------------------------------
# Schema validation
# Every DataFrame crosses this boundary before it reaches a chart or card.
# -----------------------------------------------------------------------------
def validate_frame(frame: pd.DataFrame, schema_name: str) -> pd.DataFrame:
    """Fail early with a useful message when backend output changes shape."""
    if not isinstance(frame, pd.DataFrame):
        raise TypeError(f"{schema_name} must be a pandas DataFrame")
    missing = REQUIRED_COLUMNS[schema_name].difference(frame.columns)
    if missing:
        columns = ", ".join(sorted(missing))
        raise ValueError(f"{schema_name} is missing required columns: {columns}")
    return frame.copy()


# -----------------------------------------------------------------------------
# Repository factory
# An environment variable swaps mock data for the internal backend adapter.
# -----------------------------------------------------------------------------
def create_dashboard_repository() -> DashboardRepository:
    """Create the configured repository, defaulting to local demo data."""
    factory_path = os.getenv("DASHBOARD_REPOSITORY_FACTORY", "").strip()
    if not factory_path:
        base_url = os.getenv("DASHBOARD_API_BASE_URL", "").strip()
        user_id = os.getenv("DASHBOARD_USER_ID", "").strip()
        legacy_partner_id = os.getenv("DASHBOARD_PARTNER_ID", "").strip()
        dashboard_user_id = user_id or legacy_partner_id
        if not base_url and not dashboard_user_id:
            return MockDashboardRepository()
        if not base_url or not dashboard_user_id:
            raise ValueError(
                "DASHBOARD_API_BASE_URL and DASHBOARD_USER_ID must be set together"
            )
        try:
            timeout_seconds = float(
                os.getenv("DASHBOARD_API_TIMEOUT_SECONDS", "10").strip()
            )
        except ValueError as exc:
            raise ValueError("DASHBOARD_API_TIMEOUT_SECONDS must be a number") from exc
        if timeout_seconds <= 0:
            raise ValueError("DASHBOARD_API_TIMEOUT_SECONDS must be greater than zero")
        return ApiDashboardRepository(
            base_url=base_url,
            user_id=dashboard_user_id,
            timeout_seconds=timeout_seconds,
            bearer_token=os.getenv("DASHBOARD_API_BEARER_TOKEN", "").strip(),
        )

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
