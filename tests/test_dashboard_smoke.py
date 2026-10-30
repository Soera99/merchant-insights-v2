"""Render the actual entry point in mock mode and verify route/rerun behavior."""
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / 'app.py'


class DashboardSmokeTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {
            'DASHBOARD_DATA_MODE': 'mock',
            'DASHBOARD_REPOSITORY_FACTORY': '',
        })
        self.env.start()
        self.addCleanup(self.env.stop)

    def app(self, dashboard=None):
        app = AppTest.from_file(str(APP), default_timeout=60)
        if dashboard is not None:
            app.query_params['dashboard'] = dashboard
        app.query_params['embed'] = 'true'
        return app.run()

    def assert_rendered(self, app):
        self.assertEqual(list(app.exception), [], [e.message for e in app.exception])
        self.assertGreater(len(app.markdown), 0)

    def test_legacy_iframe_renders_free(self):
        app = self.app()
        self.assert_rendered(app)
        self.assertGreater(len(app.selectbox), 0)

    def test_explicit_free_route_and_rerun(self):
        app = self.app('free')
        self.assert_rendered(app)
        self.assertEqual(app.query_params.get('dashboard'), 'free')
        app.run()
        self.assert_rendered(app)

    def test_advanced_route_and_rerun(self):
        app = self.app('advanced')
        self.assert_rendered(app)
        self.assertEqual(app.query_params.get('dashboard'), 'advanced')
        self.assertEqual(app.query_params.get('embed'), 'true')
        self.assertTrue(any('Executive' in tab.label for tab in app.tabs))
        app.run()
        self.assert_rendered(app)

    def test_switch_route_in_same_session(self):
        app = self.app('free')
        self.assert_rendered(app)
        app.query_params['dashboard'] = 'advanced'
        app.run()
        self.assert_rendered(app)
        self.assertTrue(any('Executive' in tab.label for tab in app.tabs))
        app.query_params['dashboard'] = 'free'
        app.run()
        self.assert_rendered(app)

    def test_free_province_filter_rerun(self):
        app = self.app('free')
        province = app.selectbox[0]
        province.select('DKI Jakarta').run()
        self.assert_rendered(app)
        self.assertEqual(app.selectbox[0].value, 'DKI Jakarta')
        self.assertIn('Jakarta Selatan', app.selectbox[1].options)

    def test_advanced_filter_editor_apply_and_clear(self):
        app = self.app('advanced')
        app.button(key='fb_add_exec').click().run()
        self.assert_rendered(app)
        self.assertGreater(len(app.selectbox), 0)
        app.selectbox[0].select(app.selectbox[0].options[1]).run()
        app.button(key='fb_apply_exec').click().run()
        self.assert_rendered(app)
        self.assertTrue(app.session_state['applied_filters'])
        app.button(key='fb_clear_exec').click().run()
        self.assert_rendered(app)
        self.assertEqual(app.session_state['applied_filters'], {})

    def test_invalid_route_shows_error(self):
        app = self.app('../services/free_data.py')
        self.assertEqual(list(app.exception), [])
        self.assertEqual(len(app.error), 1)
        self.assertEqual(len(app.tabs), 0)
