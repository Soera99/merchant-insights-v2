import unittest

from shared.routing import resolve_dashboard


class RoutingTests(unittest.TestCase):
    def test_legacy_url_defaults_to_free(self):
        self.assertEqual(resolve_dashboard(None), 'free')
        self.assertEqual(resolve_dashboard(''), 'free')

    def test_free_and_advanced(self):
        self.assertEqual(resolve_dashboard('free'), 'free')
        self.assertEqual(resolve_dashboard('advanced'), 'advanced')

    def test_unknown_routes_do_not_resolve_to_files(self):
        for value in ['../services/free_data.py', 'premium', '/advanced']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                resolve_dashboard(value)
