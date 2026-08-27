import json
import os
import unittest
from datetime import date
from unittest.mock import patch

from data_access import (
    ApiDashboardRepository,
    DashboardFilters,
    create_dashboard_repository,
)


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class ApiDashboardRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.filters = DashboardFilters(
            province="All Provinces",
            city="All Cities",
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 18),
        )

    @patch("data_access.urlopen")
    def test_filter_options_request_and_mapping(self, mock_urlopen):
        mock_urlopen.return_value = FakeResponse(
            {
                "status": 200,
                "content": {
                    "vars": {
                        "filter_options": {
                            "DKI Jakarta": ["Jakarta Selatan", "All Cities"],
                            "All Provinces": ["All Cities"],
                        }
                    }
                },
            }
        )
        repository = ApiDashboardRepository(
            "https://backend.example/", "019f0000-0000-7000-8000-000000000001"
        )

        options = repository.load_filter_options()

        requests = [call.args[0] for call in mock_urlopen.call_args_list]
        request = requests[0]
        self.assertEqual(
            request.full_url,
            "https://backend.example/api/v1/partners/dashboard/filter-options",
        )
        self.assertEqual(request.method, "POST")
        self.assertEqual(
            json.loads(request.data),
            {"values": ["019f0000-0000-7000-8000-000000000001"]},
        )
        self.assertEqual(
            options,
            {
                "All Provinces": ["All Cities"],
                "DKI Jakarta": ["All Cities", "Jakarta Selatan"],
            },
        )

    @patch("data_access.urlopen")
    def test_kpi_request_value_order_and_mapping(self, mock_urlopen):
        query_out = [
            {
                "metric_key": "active_campaigns",
                "value": 0,
                "change_pct": 0,
                "comparison_label": "comparison not implemented",
            }
        ]
        mock_urlopen.return_value = FakeResponse(
            {"status": 200, "content": {"vars": {"query_out": query_out}}}
        )
        repository = ApiDashboardRepository(
            "https://backend.example", "019f0000-0000-7000-8000-000000000001"
        )
        filters = DashboardFilters(
            province=self.filters.province,
            city=self.filters.city,
            start_date=self.filters.start_date,
            end_date=date(2026, 8, 13),
        )

        frame = repository.load_kpi_data(filters)

        request = mock_urlopen.call_args.args[0]
        self.assertEqual(
            request.full_url,
            "https://backend.example/api/v1/partners/dashboard/kpis",
        )
        self.assertEqual(
            json.loads(request.data),
            {
                "values": [
                    "019f0000-0000-7000-8000-000000000001",
                    "All Provinces",
                    "All Cities",
                    "2026-08-01",
                    "2026-08-13",
                ]
            },
        )
        self.assertEqual(frame.to_dict("records"), query_out)

    @patch("data_access.urlopen")
    def test_campaign_kpis_and_funnel_mapping(self, mock_urlopen):
        campaign_kpis = {
            "campaign_views": 0,
            "campaign_clicks": 0,
            "click_through_rate": 0,
            "claim_rate": 0,
            "total_vouchers_redeemed": 3,
            "total_redemption_value": 60_000,
            "average_transaction_value": 20_000,
        }
        funnel = [
            {"stage_order": 1, "stage": "View", "value": 0},
            {"stage_order": 2, "stage": "Click", "value": 0},
            {"stage_order": 3, "stage": "Claim", "value": 5},
            {"stage_order": 4, "stage": "Redeem", "value": 3},
        ]
        mock_urlopen.side_effect = [
            FakeResponse(
                {"status": 200, "content": {"vars": {"query_out": [campaign_kpis]}}}
            ),
            FakeResponse(
                {"status": 200, "content": {"vars": {"query_out": funnel}}}
            ),
        ]
        repository = ApiDashboardRepository(
            "https://backend.example", "019f0000-0000-7000-8000-000000000002"
        )

        metrics, funnel_frame = repository.load_campaign_performance_data(
            self.filters
        )

        requests = [call.args[0] for call in mock_urlopen.call_args_list]
        self.assertEqual(
            [request.full_url for request in requests],
            [
                "https://backend.example/api/v1/partners/dashboard/"
                "campaign-performance/kpis",
                "https://backend.example/api/v1/partners/dashboard/"
                "campaign-performance/funnel",
            ],
        )
        expected_values = [
            "019f0000-0000-7000-8000-000000000002",
            "All Provinces",
            "All Cities",
            "2026-08-01",
            "2026-08-18",
        ]
        self.assertEqual(json.loads(requests[0].data), {"values": expected_values})
        self.assertEqual(json.loads(requests[1].data), {"values": expected_values})
        metric_records = metrics.set_index("metric_key").to_dict("index")
        self.assertEqual(metric_records["total_vouchers_redeemed"]["value"], 3)
        self.assertEqual(metric_records["total_redemption_value"]["value"], 60_000)
        self.assertEqual(
            funnel_frame["percentage"].tolist(),
            [0.0, 0.0, 100.0, 60.0],
        )

    @patch("data_access.urlopen")
    def test_campaign_redemption_trend_mapping(self, mock_urlopen):
        trend = [
            {
                "period": "2026-08-03T00:00:00Z",
                "vouchers_redeemed": 1,
                "redemption_value": 15_000,
            },
            {
                "period": "2026-08-06T00:00:00Z",
                "vouchers_redeemed": 2,
                "redemption_value": 20_000,
            },
        ]
        mock_urlopen.side_effect = [
            FakeResponse(
                {"status": 200, "content": {"vars": {"query_out": trend}}}
            ),
            FakeResponse(
                {
                    "status": 200,
                    "content": {
                        "vars": {
                            "query_out": [
                                {
                                    "channel": "In-store",
                                    "redemption_count": 3,
                                    "channel_order": 1,
                                }
                            ]
                        }
                    },
                }
            ),
        ]
        repository = ApiDashboardRepository(
            "https://backend.example", "019f0000-0000-7000-8000-000000000002"
        )

        trend_frame, channel_frame = repository.load_dashboard_data(self.filters)

        requests = [call.args[0] for call in mock_urlopen.call_args_list]
        request = requests[0]
        self.assertEqual(
            request.full_url,
            "https://backend.example/api/v1/partners/dashboard/"
            "campaign-performance/redemption-trend",
        )
        self.assertEqual(
            requests[1].full_url,
            "https://backend.example/api/v1/partners/dashboard/"
            "product-performance/redemption-channel",
        )
        self.assertEqual(trend_frame["period"].tolist(), ["03 Aug", "06 Aug"])
        self.assertEqual(
            trend_frame["average_transaction_value"].tolist(),
            [15_000.0, 10_000.0],
        )
        self.assertEqual(
            channel_frame.to_dict("records"),
            [{"channel": "In-store", "redemptions": 3}],
        )

    @patch("data_access.urlopen")
    def test_empty_trend_keeps_required_columns(self, mock_urlopen):
        empty = FakeResponse(
            {"status": 200, "content": {"vars": {"query_out": []}}}
        )
        channels = FakeResponse(
            {
                "status": 200,
                "content": {
                    "vars": {
                        "query_out": [
                            {"channel": "In-store", "redemption_count": 0}
                        ]
                    }
                },
            }
        )
        mock_urlopen.side_effect = [empty, channels]
        repository = ApiDashboardRepository(
            "https://backend.example", "019f0000-0000-7000-8000-000000000001"
        )

        trend_frame, _ = repository.load_dashboard_data(self.filters)

        self.assertTrue(trend_frame.empty)
        self.assertEqual(
            trend_frame.columns.tolist(),
            [
                "period",
                "vouchers_redeemed",
                "redemption_value",
                "average_transaction_value",
            ],
        )

    @patch("data_access.urlopen")
    def test_product_merchant_and_customer_api_mapping(self, mock_urlopen):
        payloads = [
            [{"category_name": "Beverages", "redemption_count": 3, "sample_count": 2}],
            [{"product_name": "Latte", "sample_count": 2}],
            [{"product_name": "Latte", "redemption_count": 3}],
            [
                {
                    "category_name": "Beverages",
                    "redemption_count": 3,
                    "redemption_percentage": 100,
                }
            ],
            [{"hour": 12, "redemption_count": 3}],
            [{"store_name": "Outlet A", "redemption_count": 3}],
            [{"campaign_name": "Campaign A", "redemption_count": 3}],
            [{"city": "Jakarta Selatan", "redemption_count": 3}],
            [{"consumer_type": "New Customers", "customer_count": 2}],
            [
                {"loyalty_type": "Repeat", "customer_count": 2, "percentage": 66.67},
                {"loyalty_type": "One-time", "customer_count": 1, "percentage": 33.33},
            ],
            [
                {"gender": "MALE", "redemption_count": 4, "percentage": 57.14},
                {"gender": "FEMALE", "redemption_count": 3, "percentage": 42.86},
            ],
            [
                {
                    "age_group": "25-34",
                    "redemption_count": 6,
                    "percentage": 85.71,
                }
            ],
        ]
        mock_urlopen.side_effect = [
            FakeResponse(
                {"status": 200, "content": {"vars": {"query_out": rows}}}
            )
            for rows in payloads
        ]
        repository = ApiDashboardRepository(
            "https://backend.example", "019f0000-0000-7000-8000-000000000001"
        )

        categories, sampled, products = repository.load_product_performance_data(
            self.filters
        )
        overview, hourly = repository.load_product_detail_data(self.filters)
        outlets, campaigns, locations = repository.load_merchant_performance_data(
            self.filters
        )
        segments, loyalty, gender, ages = repository.load_customer_insights_data(
            self.filters
        )

        self.assertEqual(categories.iloc[0].to_dict(), {"category": "Beverages", "redeemed": 3, "sampling": 2})
        self.assertEqual(sampled.iloc[0].to_dict(), {"product": "Latte", "count": 2})
        self.assertEqual(products.iloc[0].to_dict(), {"product": "Latte", "count": 3})
        self.assertEqual(overview.iloc[0]["vouchers_redeemed"], 3)
        self.assertEqual(overview.iloc[0]["redeemed_share"], 100)
        self.assertEqual(overview.iloc[0]["redemption_value"], 0)
        self.assertEqual(overview.iloc[0]["unique_customers"], 0)
        self.assertEqual(overview.iloc[0]["conversion_rate"], 0.0)
        self.assertEqual(hourly.iloc[0]["time_range"], "12:00 – 13:00")
        self.assertEqual(outlets.iloc[0].to_dict(), {"name": "Outlet A", "redemptions": 3})
        self.assertEqual(campaigns.iloc[0].to_dict(), {"name": "Campaign A", "redemptions": 3})
        self.assertEqual(locations.iloc[0].to_dict(), {"name": "Jakarta Selatan", "redemptions": 3})
        self.assertEqual(segments.iloc[0].to_dict(), {"segment": "New Customers", "customers": 2})
        self.assertEqual(
            loyalty,
            {
                "average_transactions": 0.0,
                "repeat_customer_count": 2,
                "repeat_customer_percentage": 66.67,
            },
        )
        self.assertEqual(gender["gender"].tolist(), ["Male", "Female"])
        self.assertEqual(gender["percentage"].tolist(), [57.14, 42.86])
        self.assertEqual(ages.iloc[0]["age_group"], "25-34")
        self.assertEqual(ages.iloc[0]["age_range"], "")

    def test_factory_selects_api_repository_when_api_config_is_present(self):
        env = {
            "DASHBOARD_API_BASE_URL": "https://backend.example",
            "DASHBOARD_USER_ID": "user-1",
        }
        with patch.dict(os.environ, env, clear=True):
            repository = create_dashboard_repository()

        self.assertIsInstance(repository, ApiDashboardRepository)
        self.assertEqual(repository.user_id, "user-1")

    def test_factory_supports_legacy_partner_id_config(self):
        env = {
            "DASHBOARD_API_BASE_URL": "https://backend.example",
            "DASHBOARD_PARTNER_ID": "legacy-user-1",
        }
        with patch.dict(os.environ, env, clear=True):
            repository = create_dashboard_repository()

        self.assertIsInstance(repository, ApiDashboardRepository)
        self.assertEqual(repository.user_id, "legacy-user-1")


if __name__ == "__main__":
    unittest.main()
