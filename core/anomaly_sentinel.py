"""
Quality Control & Anomaly Sentinel Module.
Performs Statistical Process Control (SPC) on defect clusters,
detects critical safety hazards (lithium-ion thermal runaway / swelling),
and identifies contractual warranty expiration risks.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
from core.config import (
    CRITICAL_SAFETY_DEFECTS,
    MAX_PERMISSIBLE_SAFETY_DEFECT_RATE,
    MAX_PERMISSIBLE_CLUSTER_DEFECT_RATE
)


class AnomalySentinel:
    def __init__(
        self,
        safety_threshold: float = MAX_PERMISSIBLE_SAFETY_DEFECT_RATE,
        cluster_threshold: float = MAX_PERMISSIBLE_CLUSTER_DEFECT_RATE
    ):
        self.safety_threshold = safety_threshold
        self.cluster_threshold = cluster_threshold

    def analyze_batch(self, batch_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Inspects batch returns for safety violations, defect spikes, and warranty expirations.
        """
        if batch_df.empty:
            return {"anomalies_detected": False, "alerts": []}

        total_units = len(batch_df)
        alerts: List[Dict[str, Any]] = []
        is_quarantine_required = False

        # 1. Critical Safety Hazard Inspection (Lithium Pouch Expansion / Thermal)
        safety_pattern = "|".join(CRITICAL_SAFETY_DEFECTS)
        safety_mask = batch_df['fault_code'].str.contains(safety_pattern, case=False, na=False)
        safety_units = batch_df[safety_mask]
        safety_count = len(safety_units)
        safety_rate = safety_count / total_units if total_units > 0 else 0.0

        safety_alert = None
        if safety_rate >= self.safety_threshold and safety_count > 0:
            is_quarantine_required = True
            safety_alert = {
                "alert_id": "ALT-SEC-001",
                "type": "CRITICAL_SAFETY_DEFECT_SPIKE",
                "severity": "CRITICAL - LEVEL 1",
                "defect_category": "Lithium-Ion Thermal Expansion & Swelling",
                "affected_units": int(safety_count),
                "batch_total": int(total_units),
                "defect_rate_pct": round(safety_rate * 100, 2),
                "allowable_threshold_pct": round(self.safety_threshold * 100, 2),
                "quarantine_zone": "Zone D-Hazardous (Isolated Fire-Safe Storage)",
                "recommended_action": "MANDATORY_BATCH_QUARANTINE_AND_SUPPLIER_CHARGEBACK",
                "msa_clause_reference": "Section 4.2 - Defective Manufacturing Indemnification"
            }
            alerts.append(safety_alert)

        # 2. Pareto Defect Cluster Analysis (Non-Safety Surges)
        fault_counts = batch_df['fault_code'].value_counts()
        for fault_name, count in fault_counts.items():
            if fault_name in CRITICAL_SAFETY_DEFECTS:
                continue
            rate = count / total_units
            if rate >= self.cluster_threshold:
                alerts.append({
                    "alert_id": f"ALT-CLUS-{len(alerts) + 1}",
                    "type": "DEFECT_CLUSTER_SURGE",
                    "severity": "HIGH",
                    "defect_category": str(fault_name),
                    "affected_units": int(count),
                    "batch_total": int(total_units),
                    "defect_rate_pct": round(rate * 100, 2),
                    "allowable_threshold_pct": round(self.cluster_threshold * 100, 2),
                    "recommended_action": "ISSUE_SUPPLIER_QUALITY_AUDIT_WARNING"
                })

        # 3. Contractual Warranty Expiration Risk
        expired_mask = batch_df['days_since_dispatch'] > batch_df['window_days']
        expired_units = batch_df[expired_mask]
        expired_count = len(expired_units)

        if expired_count > 0:
            potential_credit_loss = float(expired_units['cost_price'].sum() * 0.80)
            alerts.append({
                "alert_id": f"ALT-WARR-{len(alerts) + 1}",
                "type": "RTV_WINDOW_EXPIRED",
                "severity": "MEDIUM",
                "affected_units": int(expired_count),
                "total_units": int(total_units),
                "potential_credit_lost": round(potential_credit_loss, 2),
                "recommended_action": "DIVERT_TO_INTERNAL_REFURBISH_OR_LIQUIDATION"
            })

        return {
            "anomalies_detected": len(alerts) > 0,
            "is_quarantine_required": is_quarantine_required,
            "safety_alert": safety_alert,
            "alerts": alerts,
            "total_alerts": len(alerts)
        }
