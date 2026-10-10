"""
Unit Tests for Mathematical Optimization Engine.
Validates exact penny-accurate Net Salvage Value calculations and resource constraints.
"""

import unittest
from core.mathematical_engine import calculate_unit_nsv, optimize_batch
from core.config import OperationalCosts
import pandas as pd


class TestMathematicalEngine(unittest.TestCase):

    def setUp(self):
        self.costs = OperationalCosts()

    def test_grade_a_restock_calculation(self):
        """Pristine Grade A should route to RESTOCK at 90% retail minus handling and time decay."""
        row = {
            'cost_price': 50.0,
            'retail_price': 100.0,
            'grade': 'A',
            'fault_code': 'COSMETIC_BLEMISH',
            'days_since_dispatch': 0,
            'rtv_allowed': False,
            'window_days': 30
        }
        res = calculate_unit_nsv(row)
        self.assertEqual(res['best_channel'], 'RESTOCK')
        expected_nsv = (100.0 * 0.90) - self.costs.HANDLING_COST_PER_UNIT
        self.assertAlmostEqual(res['max_nsv'], expected_nsv, places=2)

    def test_rtv_contractual_calculation(self):
        """Eligible non-hazardous unit within window should claim credit minus freight and handling."""
        row = {
            'cost_price': 100.0,
            'retail_price': 200.0,
            'grade': 'D',
            'fault_code': 'NO_POWER',
            'days_since_dispatch': 15,
            'rtv_allowed': True,
            'window_days': 30,
            'restock_credit_pct': 0.80
        }
        res = calculate_unit_nsv(row)
        self.assertEqual(res['best_channel'], 'RTV')
        expected_nsv = (100.0 * 0.80) - self.costs.SHIPPING_FREIGHT_PER_UNIT - self.costs.HANDLING_COST_PER_UNIT
        self.assertAlmostEqual(res['max_nsv'], expected_nsv, places=2)

    def test_hazardous_defect_msa_full_reimbursement(self):
        """Swelling defect within warranty window receives 100% credit without freight penalty under MSA 4.2."""
        row = {
            'cost_price': 145.0,
            'retail_price': 249.99,
            'grade': 'D',
            'fault_code': 'BATTERY_SWELLING',
            'days_since_dispatch': 12,
            'rtv_allowed': True,
            'window_days': 30
        }
        res = calculate_unit_nsv(row)
        self.assertEqual(res['best_channel'], 'RTV')
        self.assertTrue(res['is_hazardous'])
        # 100% cost recovery ($145.00) minus handling ($5.00) = $140.00
        self.assertEqual(res['max_nsv'], 140.00)

    def test_refurbish_expired_rtv(self):
        """Grade B unit past RTV window should refurbish if net secondary resale is profitable."""
        row = {
            'cost_price': 100.0,
            'retail_price': 250.0,
            'grade': 'B',
            'fault_code': 'MINOR_SCRATCH',
            'days_since_dispatch': 45,
            'rtv_allowed': True,
            'window_days': 30,
            'refurb_cost': 20.0,
            'refurb_time_hours': 1.0,
            'resale_estimate': 180.0
        }
        res = calculate_unit_nsv(row)
        self.assertEqual(res['best_channel'], 'REFURBISH')
        # Resale ($180 * (1 - 45*0.002)) - parts ($20) - labor ($35) - handling ($5)
        decay = 1.0 - (45 * 0.002)
        expected = (180.0 * decay) - 20.0 - (1.0 * self.costs.TECHNICIAN_HOURLY_RATE) - self.costs.HANDLING_COST_PER_UNIT
        self.assertAlmostEqual(res['max_nsv'], round(expected, 2), places=2)

    def test_labor_capacity_constraint(self):
        """When technician hours are capped to 0, candidate units must pivot to second-best channel."""
        batch_data = [
            {
                'return_id': 'RET-01',
                'sku': 'SKU-01',
                'supplier': 'TestVendor',
                'cost_price': 100.0,
                'retail_price': 250.0,
                'grade': 'B',
                'fault_code': 'MINOR_SCRATCH',
                'days_since_dispatch': 45,
                'window_days': 30,
                'rtv_allowed': False,
                'refurb_cost': 20.0,
                'refurb_time_hours': 2.0,
                'resale_estimate': 180.0
            }
        ]
        df = pd.DataFrame(batch_data)
        # With 0 labor hours
        opt = optimize_batch(df, max_labor_hours=0.0)
        self.assertEqual(opt['route_counts'].get('REFURBISH', 0), 0)
        self.assertEqual(opt['constrained_reassignments'], 1)
        self.assertIn('LIQUIDATE', opt['route_counts'])


if __name__ == '__main__':
    unittest.main()
