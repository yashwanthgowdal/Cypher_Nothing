"""
Data Pipeline Module.
Handles ingestion, strict schema validation, referential integrity merging,
and dynamic filtering across Returns, Products, Suppliers, and Inventory.
"""

import os
import pandas as pd
import numpy as np
from typing import Tuple, Optional, Dict, Any


REQUIRED_COLUMNS = {
    'products': ['sku', 'product_name', 'supplier', 'cost_price', 'retail_price', 'category'],
    'returns': ['return_id', 'sku', 'supplier_batch', 'grade', 'fault_code', 'days_since_dispatch'],
    'vendor_terms': ['supplier', 'rtv_allowed', 'window_days', 'restock_credit_pct'],
    'refurb_specs': ['sku', 'refurb_cost', 'refurb_time_hours', 'resale_estimate', 'parts_availability'],
    'inventory': ['sku', 'stock_on_hand', 'safety_threshold', 'warehouse_zone']
}


class DataPipeline:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir

    def load_raw_tables(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Loads and validates all 5 core tables from disk."""
        products_path = os.path.join(self.data_dir, "products.csv")
        returns_path = os.path.join(self.data_dir, "returns.csv")
        vendor_path = os.path.join(self.data_dir, "vendor_terms.csv")
        refurb_path = os.path.join(self.data_dir, "refurb_specs.csv")
        inventory_path = os.path.join(self.data_dir, "inventory.csv")

        # Auto-generate if missing
        if not all(os.path.exists(p) for p in [products_path, returns_path, vendor_path, refurb_path, inventory_path]):
            from data.generate_datasets import generate_all_datasets
            generate_all_datasets(self.data_dir)

        products_df = pd.read_csv(products_path)
        returns_df = pd.read_csv(returns_path)
        vendor_df = pd.read_csv(vendor_path)
        refurb_df = pd.read_csv(refurb_path)
        inventory_df = pd.read_csv(inventory_path)

        self._validate_schemas(products_df, returns_df, vendor_df, refurb_df, inventory_df)
        return products_df, returns_df, vendor_df, refurb_df, inventory_df

    def _validate_schemas(self, products_df, returns_df, vendor_df, refurb_df, inventory_df):
        """Ensures all tables conform to strict enterprise data contracts."""
        tables = {
            'products': products_df,
            'returns': returns_df,
            'vendor_terms': vendor_df,
            'refurb_specs': refurb_df,
            'inventory': inventory_df
        }
        for name, df in tables.items():
            missing = [col for col in REQUIRED_COLUMNS[name] if col not in df.columns]
            if missing:
                raise ValueError(f"Table '{name}' missing required columns: {missing}")

    def get_unified_returns(self, batch_id: Optional[str] = None) -> pd.DataFrame:
        """
        Creates an enriched return dataframe joining catalog pricing,
        supplier warranty terms, refurb feasibility, and warehouse inventory.
        """
        products_df, returns_df, vendor_df, refurb_df, inventory_df = self.load_raw_tables()

        # Merge relationships
        merged = returns_df.merge(products_df, on='sku', how='left')
        merged = merged.merge(vendor_df, on='supplier', how='left')
        merged = merged.merge(refurb_df, on='sku', how='left')
        merged = merged.merge(inventory_df, on='sku', how='left')

        # Clean numerical types and fill defaults
        merged['cost_price'] = pd.to_numeric(merged['cost_price'], errors='coerce').fillna(100.0)
        merged['retail_price'] = pd.to_numeric(merged['retail_price'], errors='coerce').fillna(180.0)
        merged['refurb_cost'] = pd.to_numeric(merged['refurb_cost'], errors='coerce').fillna(25.0)
        merged['refurb_time_hours'] = pd.to_numeric(merged['refurb_time_hours'], errors='coerce').fillna(1.0)
        merged['resale_estimate'] = pd.to_numeric(merged['resale_estimate'], errors='coerce').fillna(merged['retail_price'] * 0.70)
        merged['window_days'] = pd.to_numeric(merged['window_days'], errors='coerce').fillna(30).astype(int)
        merged['days_since_dispatch'] = pd.to_numeric(merged['days_since_dispatch'], errors='coerce').fillna(0).astype(int)
        merged['rtv_allowed'] = merged['rtv_allowed'].astype(bool)
        merged['restock_credit_pct'] = pd.to_numeric(merged['restock_credit_pct'], errors='coerce').fillna(0.80)

        if batch_id:
            merged = merged[merged['supplier_batch'] == batch_id].copy()

        return merged

    def list_available_batches(self) -> Dict[str, Dict[str, Any]]:
        """Returns summary metadata of all batches present in the return logs."""
        unified = self.get_unified_returns()
        batches = {}
        for b_id, grp in unified.groupby('supplier_batch'):
            batches[b_id] = {
                'batch_id': b_id,
                'supplier': grp['supplier'].iloc[0],
                'sku': grp['sku'].iloc[0],
                'product_name': grp['product_name'].iloc[0],
                'total_units': len(grp),
                'safety_flags': int(grp['fault_code'].str.contains('SWELLING|OVERHEATING|THERMAL', case=False, na=False).sum()),
                'avg_days_since_dispatch': round(float(grp['days_since_dispatch'].mean()), 1)
            }
        return batches
