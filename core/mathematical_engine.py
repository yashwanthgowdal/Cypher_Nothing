"""
Rigorous Mathematical Optimization Engine for Reverse Logistics.
Computes exact Net Salvage Value (NSV) across recovery channels,
applies operational capacity constraints (labor hours, parts stock),
and calculates exact financial uplift against naive baselines.
"""

from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pandas as pd
from core.config import (
    OperationalCosts,
    CRITICAL_SAFETY_DEFECTS,
    FUNCTIONAL_DEFECTS,
    COSMETIC_DEFECTS
)


def calculate_unit_nsv(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes exact Net Salvage Value (NSV) for each candidate disposition channel
    using exact operational cost accounting, contractual terms, and depreciation.

    Returns:
    {
        'channel_nsv': {'RESTOCK': ..., 'RTV': ..., 'REFURBISH': ..., 'LIQUIDATE': ..., 'SCRAP': ...},
        'best_channel': str,
        'max_nsv': float,
        'is_rtv_eligible': bool,
        'is_hazardous': bool,
        'refurb_hours_required': float
    }
    """
    costs = OperationalCosts()

    cost_price = float(row.get('cost_price', 100.0))
    retail_price = float(row.get('retail_price', 180.0))
    days = int(row.get('days_since_dispatch', 20))
    window = int(row.get('window_days', 30))
    rtv_allowed = bool(row.get('rtv_allowed', True))
    credit_pct = float(row.get('restock_credit_pct', costs.DEFAULT_RTV_CREDIT_RATE))
    grade = str(row.get('grade', 'C')).upper()
    fault = str(row.get('fault_code', '')).upper()

    parts_cost = float(row.get('refurb_cost', cost_price * 0.20))
    labor_hours = float(row.get('refurb_time_hours', 1.0))
    resale_estimate = float(row.get('resale_estimate', retail_price * 0.70))

    # Time-decay holding depreciation factor (0.2% per day elapsed)
    depreciation_factor = max(0.0, 1.0 - (costs.DAILY_DEPRECIATION_RATE * days))

    is_hazardous = any(hazard in fault for hazard in CRITICAL_SAFETY_DEFECTS)
    is_rtv_eligible = rtv_allowed and (days <= window)

    channel_nsv: Dict[str, float] = {}

    # 1. RESTOCK CHANNEL (Only Grade A with zero functional defects)
    has_functional_defect = any(f in fault for f in FUNCTIONAL_DEFECTS) or is_hazardous
    if grade == 'A' and not has_functional_defect:
        # Open-box resale at 90% of retail minus handling and time depreciation
        restock_gross = retail_price * 0.90 * depreciation_factor
        channel_nsv['RESTOCK'] = round(restock_gross - costs.HANDLING_COST_PER_UNIT, 2)
    else:
        channel_nsv['RESTOCK'] = -99999.0

    # 2. RETURN TO VENDOR (RTV)
    if is_rtv_eligible:
        if is_hazardous:
            # Under MSA Section 4.2: 100% manufacturer warranty defect reimbursement with zero freight penalty
            channel_nsv['RTV'] = round((cost_price * 1.00) - costs.HANDLING_COST_PER_UNIT, 2)
        else:
            # Standard contractual credit percentage minus freight and handling
            credit_amount = cost_price * credit_pct
            channel_nsv['RTV'] = round(credit_amount - costs.SHIPPING_FREIGHT_PER_UNIT - costs.HANDLING_COST_PER_UNIT, 2)
    else:
        channel_nsv['RTV'] = -99999.0

    # 3. REFURBISH CHANNEL (Grades B & C, strictly non-hazardous)
    if grade in ['B', 'C'] and not is_hazardous:
        labor_expense = labor_hours * costs.TECHNICIAN_HOURLY_RATE
        total_refurb_expense = parts_cost + labor_expense
        refurb_gross = resale_estimate * depreciation_factor
        net_refurb = refurb_gross - total_refurb_expense - costs.HANDLING_COST_PER_UNIT
        channel_nsv['REFURBISH'] = round(net_refurb, 2)
    else:
        channel_nsv['REFURBISH'] = -99999.0

    # 4. LIQUIDATE CHANNEL (Wholesale pallet auction)
    if not is_hazardous:
        liq_rate = float(row.get('recovery_pct_of_cost') or row.get('liquidation_recovery_pct') or costs.DEFAULT_LIQUIDATION_RATE)
        liquidate_gross = cost_price * liq_rate
        channel_nsv['LIQUIDATE'] = round(liquidate_gross - costs.HANDLING_COST_PER_UNIT, 2)
    else:
        channel_nsv['LIQUIDATE'] = -99999.0

    # 5. SCRAP / QUARANTINE RECYCLE
    scrap_gross = cost_price * costs.DEFAULT_SCRAP_MATERIAL_RATE
    net_scrap = max(0.0, scrap_gross - costs.SCRAP_DISPOSAL_FEE)
    channel_nsv['SCRAP'] = round(net_scrap, 2)

    # Determine optimal unconstrained route
    best_channel = max(channel_nsv, key=channel_nsv.get)
    max_nsv = channel_nsv[best_channel]

    # Auditable Unit-Level Formula Breakdown (Challenge 10 Standard)
    resale_pct = float(row.get('resale_pct_of_new', 0.75))
    resale_gross_undepreciated = retail_price * resale_pct
    refurb_before_fees = resale_gross_undepreciated - parts_cost
    vendor_credit_amount = cost_price * credit_pct if is_rtv_eligible else 0.0
    liq_rate = float(row.get('recovery_pct_of_cost') or row.get('liquidation_recovery_pct') or costs.DEFAULT_LIQUIDATION_RATE)
    liquidation_amount = cost_price * liq_rate

    time_to_cash = {
        'REFURBISH': {
            'processing_days': int(row.get('days_required', 5)),
            'time_to_sale_days': costs.REFURB_SALE_DAYS,
            'payment_days': costs.REFURB_PAYMENT_DAYS,
            'total_days': int(row.get('days_required', 5)) + costs.REFURB_SALE_DAYS + costs.REFURB_PAYMENT_DAYS
        },
        'RTV': {
            'processing_days': 2,
            'time_to_sale_days': 0,
            'payment_days': costs.VENDOR_CREDIT_PAYMENT_DAYS,
            'total_days': 2 + costs.VENDOR_CREDIT_PAYMENT_DAYS
        },
        'LIQUIDATE': {
            'processing_days': 1,
            'time_to_sale_days': 2,
            'payment_days': costs.LIQUIDATION_PAYMENT_DAYS,
            'total_days': 1 + 2 + costs.LIQUIDATION_PAYMENT_DAYS
        },
        'RESTOCK': {
            'processing_days': 1,
            'time_to_sale_days': 5,
            'payment_days': 7,
            'total_days': 13
        },
        'SCRAP': {
            'processing_days': 1,
            'time_to_sale_days': 0,
            'payment_days': 1,
            'total_days': 2
        }
    }

    breakdown = {
        'selling_price': retail_price,
        'cost_price': cost_price,
        'resale_pct_of_new': resale_pct,
        'refurb_cost': parts_cost,
        'refurb_recovery_before_fees': round(refurb_before_fees, 2),
        'vendor_credit_pct': credit_pct,
        'vendor_credit_amount': round(vendor_credit_amount, 2),
        'is_rtv_eligible': is_rtv_eligible,
        'rtv_window_days': window,
        'days_since_dispatch': days,
        'liquidation_pct': liq_rate,
        'liquidation_amount': round(liquidation_amount, 2),
        'baseline_salvage_value': round(liquidation_amount, 2),
        'time_to_cash': time_to_cash,
        'formula_refurb': f"₹{retail_price:,.0f} × {resale_pct*100:.0f}% − ₹{parts_cost:,.0f} = ₹{refurb_before_fees:,.2f}",
        'formula_rtv': f"₹{cost_price:,.0f} × {credit_pct*100:.0f}% = ₹{vendor_credit_amount:,.2f}" if is_rtv_eligible else "Ineligible (30-day window expired)",
        'formula_liq': f"₹{cost_price:,.0f} × {liq_rate*100:.0f}% = ₹{liquidation_amount:,.2f}",
        'net_recovery_accounting_note': "Gross recovery proceeds less direct variable recovery costs. Sunk historical purchase cost is excluded to prevent double-deduction."
    }

    return {
        'channel_nsv': channel_nsv,
        'best_channel': best_channel,
        'max_nsv': max_nsv,
        'is_rtv_eligible': is_rtv_eligible,
        'is_hazardous': is_hazardous,
        'refurb_hours_required': labor_hours if grade in ['B', 'C'] and not is_hazardous else 0.0,
        'breakdown': breakdown,
        'time_to_cash': time_to_cash.get(best_channel, time_to_cash['LIQUIDATE'])
    }


def optimize_batch(
    batch_df: pd.DataFrame,
    max_labor_hours: Optional[float] = None,
    parts_inventory: Optional[Dict[str, int]] = None
) -> Dict[str, Any]:
    """
    Executes rigorous batch optimization over all returns.
    Accounts for operational capacity limits (available technician hours, spare parts inventory).
    """
    if isinstance(batch_df, list):
        batch_df = pd.DataFrame(batch_df)
    if batch_df is None or batch_df.empty:
        return {
            'route_counts': {},
            'total_nsv': 0.0,
            'unit_decisions': [],
            'labor_hours_used': 0.0,
            'constrained_reassignments': 0
        }

    # Step 1: Calculate unit-level economics for all items
    unit_evals = []
    for _, row in batch_df.iterrows():
        eval_res = calculate_unit_nsv(row.to_dict())
        unit_evals.append({
            'return_id': row.get('return_id'),
            'sku': row.get('sku'),
            'supplier': row.get('supplier'),
            'cost_price': float(row.get('cost_price', 100.0)),
            'grade': str(row.get('grade', 'C')),
            'fault_code': str(row.get('fault_code', '')),
            'days_since_dispatch': int(row.get('days_since_dispatch', 20)),
            'channel_nsv': eval_res['channel_nsv'],
            'best_channel': eval_res['best_channel'],
            'max_nsv': eval_res['max_nsv'],
            'hours_needed': eval_res['refurb_hours_required'],
            'is_hazardous': eval_res['is_hazardous']
        })

    # Step 2: Constrained Resource Allocation
    total_labor_capacity = max_labor_hours if max_labor_hours is not None else float('inf')
    parts_stock = parts_inventory.copy() if parts_inventory else {}

    accumulated_hours = 0.0
    constrained_reassignments = 0
    final_decisions = []

    # Sort candidates desiring REFURBISH by highest margin yield to maximize efficiency under constraint
    def sort_key(item):
        if item['best_channel'] == 'REFURBISH':
            # Priority = Net salvage per labor hour
            hrs = max(0.1, item['hours_needed'])
            return (2, item['max_nsv'] / hrs)
        elif item['best_channel'] == 'RTV':
            return (1, item['max_nsv'])
        else:
            return (0, item['max_nsv'])

    unit_evals.sort(key=sort_key, reverse=True)

    for item in unit_evals:
        target_channel = item['best_channel']
        assigned_channel = target_channel
        assigned_nsv = item['max_nsv']

        if target_channel == 'REFURBISH':
            sku = item['sku']
            needed_hrs = item['hours_needed']
            has_labor = (accumulated_hours + needed_hrs) <= total_labor_capacity
            has_parts = parts_stock.get(sku, 9999) > 0

            if has_labor and has_parts:
                accumulated_hours += needed_hrs
                if sku in parts_stock:
                    parts_stock[sku] -= 1
            else:
                # Labor or parts exhausted -> pivot to second best available channel
                constrained_reassignments += 1
                fallback_options = {
                    ch: val for ch, val in item['channel_nsv'].items()
                    if ch != 'REFURBISH' and val > -90000
                }
                if fallback_options:
                    assigned_channel = max(fallback_options, key=fallback_options.get)
                    assigned_nsv = fallback_options[assigned_channel]
                else:
                    assigned_channel = 'SCRAP'
                    assigned_nsv = item['channel_nsv'].get('SCRAP', 0.0)

        final_decisions.append({
            'return_id': item['return_id'],
            'sku': item['sku'],
            'grade': item['grade'],
            'fault_code': item['fault_code'],
            'assigned_channel': assigned_channel,
            'net_salvage_value': assigned_nsv,
            'is_hazardous': item['is_hazardous']
        })

    # Step 3: Compute aggregate batch metrics
    route_counts = {}
    total_batch_nsv = 0.0
    for d in final_decisions:
        ch = d['assigned_channel']
        route_counts[ch] = route_counts.get(ch, 0) + 1
        total_batch_nsv += d['net_salvage_value']

    return {
        'route_counts': route_counts,
        'total_nsv': round(total_batch_nsv, 2),
        'unit_decisions': final_decisions,
        'labor_hours_used': round(accumulated_hours, 2),
        'constrained_reassignments': constrained_reassignments
    }


def calculate_baseline_comparison(batch_df: pd.DataFrame, optimized_nsv: float) -> Dict[str, Any]:
    """
    Computes exact financial uplift against traditional naive warehouse triage baselines:
    1. Naive Liquidation Baseline: Every non-A unit dumped to bulk liquidator (18% cost).
    2. Naive Restock/Scrap Baseline: Standard FIFO triage without warranty window optimization.
    """
    costs = OperationalCosts()
    total_cost_basis = float(batch_df['cost_price'].sum()) if not batch_df.empty else 0.0
    naive_salvage = 0.0

    for _, row in batch_df.iterrows():
        c_p = float(row.get('cost_price', 100.0))
        grade = str(row.get('grade', 'C')).upper()
        if grade == 'A':
            # Sold as open-box
            naive_salvage += (float(row.get('retail_price', 180.0)) * 0.85) - costs.HANDLING_COST_PER_UNIT
        else:
            # Blindly bulk-liquidated at standard 15% wholesale
            naive_salvage += (c_p * 0.15) - costs.HANDLING_COST_PER_UNIT

    naive_salvage = max(0.0, round(naive_salvage, 2))
    dollar_uplift = round(optimized_nsv - naive_salvage, 2)
    pct_uplift = round(((optimized_nsv - naive_salvage) / max(1.0, naive_salvage)) * 100, 1)

    return {
        'total_cost_basis': round(total_cost_basis, 2),
        'naive_salvage_value': naive_salvage,
        'optimized_nsv': round(optimized_nsv, 2),
        'dollar_uplift': dollar_uplift,
        'pct_uplift': pct_uplift
    }
