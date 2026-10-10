"""
Dataset Generator for Reverse Logistics Platform.
Generates comprehensive enterprise-grade datasets for products, suppliers, returns,
inventory, and refurbishment engineering parameters.
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_all_datasets(output_dir: str = "data"):
    os.makedirs(output_dir, exist_ok=True)
    np.random.seed(42)

    # 1. Vendor Terms & Master Service Agreements (MSAs)
    vendors = [
        {
            "supplier": "HyperBattery Inc",
            "rtv_allowed": True,
            "window_days": 30,
            "restock_credit_pct": 0.80,
            "contact_email": "rma-ops@hyperbattery.com",
            "sla_business_days": 5,
            "msa_contract_id": "MSA-HYPER-2025-V2"
        },
        {
            "supplier": "ApexTech Electronics",
            "rtv_allowed": True,
            "window_days": 45,
            "restock_credit_pct": 0.85,
            "contact_email": "reverse-logistics@apextech.io",
            "sla_business_days": 7,
            "msa_contract_id": "MSA-APEX-2024-V4"
        },
        {
            "supplier": "NanoGlow Displays",
            "rtv_allowed": False,
            "window_days": 14,
            "restock_credit_pct": 0.0,
            "contact_email": "claims@nanoglow.com",
            "sla_business_days": 10,
            "msa_contract_id": "MSA-NANO-2024-V1"
        },
        {
            "supplier": "VoltEdge Power Systems",
            "rtv_allowed": True,
            "window_days": 30,
            "restock_credit_pct": 0.75,
            "contact_email": "warranty@voltedge.net",
            "sla_business_days": 6,
            "msa_contract_id": "MSA-VOLT-2025-V1"
        }
    ]
    vendor_df = pd.DataFrame(vendors)
    vendor_df.to_csv(os.path.join(output_dir, "vendor_terms.csv"), index=False)

    # 2. Product Catalog
    products = [
        {
            "sku": "SKU-HB-BAT5000",
            "product_name": "HyperCell Li-Ion Battery Pack 5000mAh",
            "supplier": "HyperBattery Inc",
            "cost_price": 145.00,
            "retail_price": 249.99,
            "category": "Battery & Power"
        },
        {
            "sku": "SKU-HB-CHRG65W",
            "product_name": "HyperGaN 65W Fast Wall Charger",
            "supplier": "HyperBattery Inc",
            "cost_price": 42.00,
            "retail_price": 79.99,
            "category": "Accessories"
        },
        {
            "sku": "SKU-APX-TAB11",
            "product_name": "ApexTab Ultra 11-inch Tablet 256GB",
            "supplier": "ApexTech Electronics",
            "cost_price": 310.00,
            "retail_price": 499.99,
            "category": "Tablets"
        },
        {
            "sku": "SKU-NG-DISP15",
            "product_name": "NanoGlow 15.6 OLED Panel Assembly",
            "supplier": "NanoGlow Displays",
            "cost_price": 115.00,
            "retail_price": 189.99,
            "category": "Displays"
        },
        {
            "sku": "SKU-VE-INV1000",
            "product_name": "VoltEdge Pure Sine Wave Inverter 1000W",
            "supplier": "VoltEdge Power Systems",
            "cost_price": 220.00,
            "retail_price": 369.99,
            "category": "Power Systems"
        }
    ]
    products_df = pd.DataFrame(products)
    products_df.to_csv(os.path.join(output_dir, "products.csv"), index=False)

    # 3. Refurbishment Engineering Specifications
    refurb_specs = [
        {
            "sku": "SKU-HB-BAT5000",
            "refurb_cost": 32.50,
            "refurb_time_hours": 1.2,
            "resale_estimate": 179.00,
            "parts_availability": "LIMITED"
        },
        {
            "sku": "SKU-HB-CHRG65W",
            "refurb_cost": 8.00,
            "refurb_time_hours": 0.4,
            "resale_estimate": 55.00,
            "parts_availability": "HIGH"
        },
        {
            "sku": "SKU-APX-TAB11",
            "refurb_cost": 55.00,
            "refurb_time_hours": 2.5,
            "resale_estimate": 360.00,
            "parts_availability": "HIGH"
        },
        {
            "sku": "SKU-NG-DISP15",
            "refurb_cost": 25.00,
            "refurb_time_hours": 1.0,
            "resale_estimate": 135.00,
            "parts_availability": "MEDIUM"
        },
        {
            "sku": "SKU-VE-INV1000",
            "refurb_cost": 48.00,
            "refurb_time_hours": 2.0,
            "resale_estimate": 275.00,
            "parts_availability": "HIGH"
        }
    ]
    refurb_df = pd.DataFrame(refurb_specs)
    refurb_df.to_csv(os.path.join(output_dir, "refurb_specs.csv"), index=False)

    # 4. Inventory Cover & Warehouse Shelving
    inventory = [
        {"sku": "SKU-HB-BAT5000", "stock_on_hand": 184, "safety_threshold": 50, "warehouse_zone": "Zone D-Hazardous"},
        {"sku": "SKU-HB-CHRG65W", "stock_on_hand": 340, "safety_threshold": 100, "warehouse_zone": "Zone A-Shelving"},
        {"sku": "SKU-APX-TAB11", "stock_on_hand": 92, "safety_threshold": 25, "warehouse_zone": "Zone B-Secure"},
        {"sku": "SKU-NG-DISP15", "stock_on_hand": 65, "safety_threshold": 20, "warehouse_zone": "Zone C-Fragile"},
        {"sku": "SKU-VE-INV1000", "stock_on_hand": 48, "safety_threshold": 15, "warehouse_zone": "Zone A-Heavy"}
    ]
    inventory_df = pd.DataFrame(inventory)
    inventory_df.to_csv(os.path.join(output_dir, "inventory.csv"), index=False)

    # 5. Returns Dataset
    # Batch HB-09: Benchmark anomaly batch with high lithium swelling defect concentration
    returns = []
    
    # 25 units for HB-09
    hb09_faults = [
        "BATTERY_SWELLING", "BATTERY_SWELLING", "BATTERY_SWELLING", "BATTERY_SWELLING",
        "BATTERY_SWELLING", "BATTERY_SWELLING", "BATTERY_SWELLING", "BATTERY_SWELLING",
        "BATTERY_SWELLING", "BATTERY_SWELLING", "BATTERY_SWELLING", "BATTERY_SWELLING", # 12 swelling (48%)
        "NO_POWER", "NO_POWER", "OVERHEATING", "OVERHEATING", "THERMAL_SHUTDOWN",
        "COSMETIC_BLEMISH", "COSMETIC_BLEMISH", "PACKAGING_DAMAGED", "MINOR_SCRATCH",
        "CONNECTOR_LOOSE", "CONNECTOR_LOOSE", "FIRMWARE_LOCK", "SLOW_DISCHARGE"
    ]
    hb09_grades = [
        "D", "D", "C", "D", "D", "D", "C", "D", "D", "D", "C", "D",
        "C", "C", "D", "D", "D",
        "A", "A", "A", "B",
        "B", "B", "B", "B"
    ]
    hb09_days = [
        12, 14, 18, 21, 22, 24, 25, 27, 28, 29, 29, 30, # In-window (<= 30 days)
        32, 35, 38, 41, 45,                             # Expired window (> 30 days)
        11, 15, 19, 22,
        26, 33, 37, 40
    ]

    for i in range(25):
        returns.append({
            "return_id": f"RET-HB09-{101 + i}",
            "sku": "SKU-HB-BAT5000",
            "supplier_batch": "HB-09",
            "grade": hb09_grades[i],
            "fault_code": hb09_faults[i],
            "days_since_dispatch": hb09_days[i],
            "customer_comment": "Device casing bulging significantly" if "SWELLING" in hb09_faults[i] else "General return"
        })

    # Additional standard batches: HB-08 (chargers), AP-12 (tablets), NG-03 (displays), VE-01 (inverters)
    additional_batches = [
        ("HB-08", "SKU-HB-CHRG65W", 20, ["PACKAGING_DAMAGED", "COSMETIC_BLEMISH", "NO_POWER"], ["A", "A", "B", "C"], 25),
        ("AP-12", "SKU-APX-TAB11", 18, ["SCREEN_CRACK", "TOUCH_UNRESPONSIVE", "AUDIO_DISTORTION"], ["B", "B", "C", "D"], 35),
        ("NG-03", "SKU-NG-DISP15", 15, ["DEAD_PIXELS", "BACKLIGHT_BLEED", "CRACKED_GLASS"], ["C", "C", "D"], 20),
        ("VE-01", "SKU-VE-INV1000", 12, ["NO_POWER", "OVERHEATING", "CONNECTOR_LOOSE"], ["B", "C", "C", "D"], 28)
    ]

    unit_counter = 200
    for b_id, sku, count, f_pool, g_pool, max_days in additional_batches:
        for _ in range(count):
            unit_counter += 1
            returns.append({
                "return_id": f"RET-{b_id}-{unit_counter}",
                "sku": sku,
                "supplier_batch": b_id,
                "grade": str(np.random.choice(g_pool)),
                "fault_code": str(np.random.choice(f_pool)),
                "days_since_dispatch": int(np.random.randint(4, max_days + 1)),
                "customer_comment": "Standard customer return request"
            })

    returns_df = pd.DataFrame(returns)
    returns_df.to_csv(os.path.join(output_dir, "returns.csv"), index=False)
    print(f"Datasets generated successfully in {output_dir}/")

if __name__ == "__main__":
    generate_all_datasets()
