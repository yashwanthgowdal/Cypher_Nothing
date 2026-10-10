"""
Unit Tests for Data Pipeline, Machine Learning Model, and Anomaly Sentinel.
"""

import unittest
import pandas as pd
from core.data_pipeline import DataPipeline
from core.ml_disposition import DispositionModelPipeline, extract_features
from core.anomaly_sentinel import AnomalySentinel


class TestPipelineAndModules(unittest.TestCase):

    def setUp(self):
        self.pipeline = DataPipeline()

    def test_data_pipeline_tables_loaded(self):
        """Verifies all 5 core tables exist and merge properly."""
        unified = self.pipeline.get_unified_returns()
        self.assertFalse(unified.empty)
        required_cols = ['return_id', 'sku', 'cost_price', 'retail_price', 'window_days', 'supplier']
        for col in required_cols:
            self.assertIn(col, unified.columns)

    def test_ml_feature_extraction_and_inference(self):
        """Tests that feature extraction produces 12 standard columns and returns probability distributions."""
        sample_row = {
            'cost_price': 145.0,
            'retail_price': 249.99,
            'days_since_dispatch': 12,
            'window_days': 30,
            'rtv_allowed': True,
            'restock_credit_pct': 0.80,
            'grade': 'D',
            'refurb_cost': 32.50,
            'resale_estimate': 179.0,
            'fault_code': 'BATTERY_SWELLING'
        }
        feat_df = extract_features(sample_row)
        self.assertEqual(len(feat_df.columns), 12)

        ml = DispositionModelPipeline()
        preds = ml.predict(sample_row)
        self.assertEqual(len(preds), 1)
        pred = preds[0]
        self.assertIn(pred['disposition'], ['RESTOCK', 'RTV', 'REFURBISH', 'LIQUIDATE', 'QUARANTINE_SCRAP'])
        self.assertGreaterEqual(pred['confidence'], 0.0)
        self.assertLessEqual(pred['confidence'], 1.0)
        prob_sum = sum(pred['probabilities'].values())
        self.assertAlmostEqual(prob_sum, 1.0, places=2)

    def test_anomaly_sentinel_swelling_spike(self):
        """Verifies Level 1 hazard lockdown triggers when defect rate > 5%."""
        batch_df = self.pipeline.get_unified_returns(batch_id='HB-09')
        sentinel = AnomalySentinel()
        analysis = sentinel.analyze_batch(batch_df)

        self.assertTrue(analysis['anomalies_detected'])
        self.assertTrue(analysis['is_quarantine_required'])
        self.assertIsNotNone(analysis['safety_alert'])
        self.assertEqual(analysis['safety_alert']['severity'], 'CRITICAL - LEVEL 1')


if __name__ == '__main__':
    unittest.main()
