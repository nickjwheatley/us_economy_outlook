import unittest
from dataclasses import replace

from market_outlook.io import load_indicator_snapshot, load_source_registry
from market_outlook.history import generate_dashboard_history, load_historical_indicator_points
from market_outlook.scoring import compute_outlook, indicator_score


class ScoringTests(unittest.TestCase):
    def _result(self):
        registry = load_source_registry("data/source_registry.csv")
        snapshots = load_indicator_snapshot("data/fixtures/latest_indicators.csv")
        return compute_outlook(registry, snapshots)

    def test_fixture_score_is_deterministic(self):
        result = self._result()

        self.assertEqual(result.rules_score, 4.04)
        self.assertEqual(result.headline_score, 4.33)
        self.assertEqual(result.regime, "stall-speed slowdown")
        self.assertEqual(result.recession_risk, "elevated")

    def test_saas_and_vti_implications_are_present(self):
        result = self._result()

        self.assertIn("SaaS", result.saas_implication)
        self.assertIn("VTI", result.vti_implication)

    def test_worsening_unemployment_scores_worse_than_improving_unemployment(self):
        registry = load_source_registry("data/source_registry.csv")
        snapshots = load_indicator_snapshot("data/fixtures/latest_indicators.csv")
        series = registry["UNRATE"]
        base = snapshots["UNRATE"]

        worsening = replace(base, qoq_signal=0.50, yoy_signal=0.70)
        improving = replace(base, qoq_signal=-0.50, yoy_signal=-0.70)

        self.assertLess(indicator_score(series, worsening), indicator_score(series, improving))

    def test_debt_indicators_are_included(self):
        result = self._result()
        series_ids = {item.series_id for item in result.indicator_scores}

        self.assertIn("DRCCLACBS", series_ids)
        self.assertIn("DRALACBS", series_ids)
        self.assertIn("TDSP", series_ids)

    def test_market_valuation_indicators_are_included(self):
        result = self._result()
        series_ids = {item.series_id for item in result.indicator_scores}
        block_scores = {item.block: item.score for item in result.block_scores}

        self.assertIn("CAPE", series_ids)
        self.assertIn("SP500FPE", series_ids)
        self.assertIn("BUFFETT", series_ids)
        self.assertIn("CAPE_YIELD_SPREAD", series_ids)
        self.assertLess(block_scores["Market Valuation"], 4.0)
        self.assertIn("Valuation is stretched", result.vti_implication)

    def test_dashboard_history_contains_score_and_indicators(self):
        registry = load_source_registry("data/source_registry.csv")
        snapshots = load_indicator_snapshot("data/fixtures/latest_indicators.csv")
        result = compute_outlook(registry, snapshots)
        historical_points = load_historical_indicator_points("data/fixtures/historical_indicators.csv")

        history = generate_dashboard_history(registry, snapshots, result, historical_points)

        self.assertGreaterEqual(len(history["score"]), 320)
        self.assertIn("UNRATE", history["indicators"])
        self.assertGreaterEqual(len(history["indicators"]["UNRATE"]["points"]), 200)
        self.assertEqual(history["indicators"]["UNRATE"]["historySource"], "FRED monthly history")
        self.assertEqual(history["indicators"]["T10Y2Y"]["historySource"], "FRED monthly history")
        self.assertEqual(len(history["indicators"]["T10Y2Y"]["points"]), 360)
        self.assertIn("CAPE", history["indicators"])
        self.assertIn("BUFFETT", history["indicators"])
        self.assertIn("CAPE_YIELD_SPREAD", history["indicators"])
        self.assertEqual(history["indicators"]["CAPE"]["historySource"], "Robert Shiller/Yale monthly data")
        self.assertEqual(history["indicators"]["BUFFETT"]["historySource"], "World Bank annual data")
        self.assertNotIn("SP500FPE", history["indicators"])
        self.assertNotIn("BAMLH0A0HYM2", history["indicators"])
        self.assertGreaterEqual(len(history["recessions"]), 2)


if __name__ == "__main__":
    unittest.main()
