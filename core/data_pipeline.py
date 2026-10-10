"""
Data Pipeline Module for Gadgetbay AI Reverse Logistics.
Ingests, validates, merges, and enriches data from official evaluation files:
- products.csv (sku, product, category, cost_price, selling_price, supplier)
- returns.csv (return_id, date_received, sku, supplier_batch, reason_code, condition_grade, status)
- vendor_terms.csv (supplier, sku, rtv_allowed, credit_pct, window_days)
- liquidation.csv (category, condition_grade, recovery_pct_of_cost)
- refurbishment.csv (category, refurb_cost, days_required, resale_pct_of_new)
- inventory.csv (sku, new_stock, avg_daily_demand)
- sales.csv (date, sku, qty_sold, selling_price)
"""

import os
from datetime import datetime
import pandas as pd
import numpy as np
from typing import Tuple, Optional, Dict, Any

EVALUATION_SNAPSHOT_DATE = "2026-11-16"


class DataPipeline:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir

    def load_raw_tables(self) -> Dict[str, pd.DataFrame]:
        """Loads all evaluation tables from disk with flexible fallbacks."""
        tables = {}
        file_map = {
            'products': 'products.csv',
            'returns': 'returns.csv',
            'vendor_terms': 'vendor_terms.csv',
            'liquidation': 'liquidation.csv',
            'refurbishment': 'refurbishment.csv',
            'inventory': 'inventory.csv',
            'sales': 'sales.csv'
        }

        # Check for fallback filenames (e.g. refurb_specs.csv)
        if not os.path.exists(os.path.join(self.data_dir, 'refurbishment.csv')) and os.path.exists(os.path.join(self.data_dir, 'refurb_specs.csv')):
            file_map['refurbishment'] = 'refurb_specs.csv'

        for key, fname in file_map.items():
            fpath = os.path.join(self.data_dir, fname)
            if os.path.exists(fpath):
                tables[key] = pd.read_csv(fpath)
            else:
                tables[key] = pd.DataFrame()

        return tables

    def get_unified_returns(self, batch_id: Optional[str] = None) -> pd.DataFrame:
        """
        Creates an enriched return dataframe joining catalog pricing,
        supplier warranty terms, refurb feasibility, liquidation rates, and warehouse inventory.
        """
        tables = self.load_raw_tables()
        returns_df = tables['returns'].copy()
        products_df = tables['products'].copy()
        vendor_df = tables['vendor_terms'].copy()
        refurb_df = tables['refurbishment'].copy()
        liquidation_df = tables['liquidation'].copy()
        inventory_df = tables['inventory'].copy()

        # Standardize products_df
        if 'product' in products_df.columns and 'product_name' not in products_df.columns:
            products_df['product_name'] = products_df['product']
        if 'selling_price' in products_df.columns and 'retail_price' not in products_df.columns:
            products_df['retail_price'] = products_df['selling_price']

        # Standardize returns_df
        if 'condition_grade' in returns_df.columns and 'grade' not in returns_df.columns:
            returns_df['grade'] = returns_df['condition_grade']
        if 'reason_code' in returns_df.columns and 'fault_code' not in returns_df.columns:
            returns_df['fault_code'] = returns_df['reason_code'].astype(str).str.replace('\u2013', '-').str.replace('–', '-')
        
        # Calculate days_since_dispatch / days_since_received relative to 2026-11-16
        if 'date_received' in returns_df.columns:
            snapshot_dt = pd.to_datetime(EVALUATION_SNAPSHOT_DATE)
            received_dt = pd.to_datetime(returns_df['date_received'], errors='coerce')
            returns_df['days_since_dispatch'] = (snapshot_dt - received_dt).dt.days.fillna(10).astype(int)
        elif 'days_since_dispatch' not in returns_df.columns:
            returns_df['days_since_dispatch'] = 10

        # Standardize vendor_df
        if 'credit_pct' in vendor_df.columns and 'restock_credit_pct' not in vendor_df.columns:
            vendor_df['restock_credit_pct'] = vendor_df['credit_pct']
        if 'rtv_allowed' in vendor_df.columns:
            vendor_df['rtv_allowed'] = vendor_df['rtv_allowed'].astype(str).str.strip().str.lower().isin(['yes', 'true', '1'])

        # Merge products
        merged = returns_df.merge(products_df, on='sku', how='left')

        # Merge vendor terms: prioritize match on ['supplier', 'sku'] if possible, else ['sku'], else ['supplier']
        if not vendor_df.empty:
            if 'sku' in vendor_df.columns:
                vendor_cols = [c for c in ['sku', 'rtv_allowed', 'restock_credit_pct', 'window_days'] if c in vendor_df.columns]
                merged = merged.merge(vendor_df[vendor_cols], on='sku', how='left')
            elif 'supplier' in vendor_df.columns:
                vendor_cols = [c for c in ['supplier', 'rtv_allowed', 'restock_credit_pct', 'window_days'] if c in vendor_df.columns]
                merged = merged.merge(vendor_df[vendor_cols], on='supplier', how='left')

        # Merge refurbishment: merge on category if category is present in refurb_df, else on sku
        if not refurb_df.empty:
            if 'category' in refurb_df.columns and 'category' in merged.columns:
                refurb_cols = [c for c in ['category', 'refurb_cost', 'days_required', 'resale_pct_of_new'] if c in refurb_df.columns]
                merged = merged.merge(refurb_df[refurb_cols], on='category', how='left')
            elif 'sku' in refurb_df.columns:
                merged = merged.merge(refurb_df, on='sku', how='left')

        # Merge liquidation: merge on ['category', 'grade']
        if not liquidation_df.empty:
            liq_grade_col = 'condition_grade' if 'condition_grade' in liquidation_df.columns else 'grade'
            if 'category' in liquidation_df.columns and liq_grade_col in liquidation_df.columns:
                liquidation_renamed = liquidation_df.rename(columns={liq_grade_col: 'grade'})
                merged = merged.merge(liquidation_renamed[['category', 'grade', 'recovery_pct_of_cost']], on=['category', 'grade'], how='left')

        # Merge inventory: merge on sku
        if not inventory_df.empty and 'sku' in inventory_df.columns:
            inv_cols = [c for c in ['sku', 'new_stock', 'avg_daily_demand', 'stock_on_hand', 'safety_threshold'] if c in inventory_df.columns]
            merged = merged.merge(inventory_df[inv_cols], on='sku', how='left')

        # Clean numerical types and fill defaults
        merged['cost_price'] = pd.to_numeric(merged['cost_price'], errors='coerce').fillna(100.0)
        merged['retail_price'] = pd.to_numeric(merged['retail_price'], errors='coerce').fillna(merged['cost_price'] * 1.6)
        merged['refurb_cost'] = pd.to_numeric(merged.get('refurb_cost', 0), errors='coerce').fillna(250.0)
        merged['days_required'] = pd.to_numeric(merged.get('days_required', 0), errors='coerce').fillna(5.0)
        merged['refurb_time_hours'] = merged['days_required'] * 1.5
        merged['resale_pct_of_new'] = pd.to_numeric(merged.get('resale_pct_of_new', 0), errors='coerce').fillna(0.70)
        merged['resale_estimate'] = merged['resale_pct_of_new'] * merged['retail_price']
        merged['recovery_pct_of_cost'] = pd.to_numeric(merged.get('recovery_pct_of_cost', 0), errors='coerce').fillna(0.20)
        merged['liquidation_recovery_pct'] = merged['recovery_pct_of_cost']
        merged['window_days'] = pd.to_numeric(merged.get('window_days', 30), errors='coerce').fillna(30).astype(int)
        merged['days_since_dispatch'] = pd.to_numeric(merged['days_since_dispatch'], errors='coerce').fillna(10).astype(int)
        merged['rtv_allowed'] = merged.get('rtv_allowed', True).fillna(True).astype(bool)
        merged['restock_credit_pct'] = pd.to_numeric(merged.get('restock_credit_pct', 0.60), errors='coerce').fillna(0.60)
        merged['new_stock'] = pd.to_numeric(merged.get('new_stock', 50), errors='coerce').fillna(50)
        merged['avg_daily_demand'] = pd.to_numeric(merged.get('avg_daily_demand', 2.0), errors='coerce').fillna(2.0)
        merged['stock_runway_days'] = merged['new_stock'] / merged['avg_daily_demand'].replace(0, 0.001)

        # Ensure product_name is present
        if 'product_name' not in merged.columns or merged['product_name'].isnull().all():
            merged['product_name'] = merged['sku']

        if 'supplier_batch' in merged.columns and 'batch_id' not in merged.columns:
            merged['batch_id'] = merged['supplier_batch']
        elif 'batch_id' in merged.columns and 'supplier_batch' not in merged.columns:
            merged['supplier_batch'] = merged['batch_id']

        if batch_id:
            batch_col = 'supplier_batch' if 'supplier_batch' in merged.columns else 'batch_id'
            merged = merged[merged[batch_col] == batch_id].copy()

        return merged

    def list_available_batches(self) -> Dict[str, Dict[str, Any]]:
        """Returns summary metadata of all batches present in the return logs, sorted by size."""
        unified = self.get_unified_returns()
        batches = {}
        for b_id, grp in unified.groupby('supplier_batch'):
            batches[b_id] = {
                'batch_id': b_id,
                'supplier': str(grp['supplier'].iloc[0]) if 'supplier' in grp.columns else "Gadgetbay Supplier",
                'sku': str(grp['sku'].iloc[0]),
                'product_name': str(grp['product_name'].iloc[0]),
                'total_units': len(grp),
                'safety_flags': int(grp['fault_code'].astype(str).str.contains('SWELLING|OVERHEATING|THERMAL|NOT POWERING ON|FIRE|DEFECTIVE', case=False, na=False).sum()),
                'avg_days_since_dispatch': round(float(grp['days_since_dispatch'].mean()), 1)
            }
        
        # Sort so largest/critical batches appear first
        sorted_batches = dict(sorted(batches.items(), key=lambda item: item[1]['total_units'], reverse=True))
        return sorted_batches
