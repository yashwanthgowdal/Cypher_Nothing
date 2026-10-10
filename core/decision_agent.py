"""
Strategic Decision Agent & LLM Orchestrator.
Generates executive triage strategies, financial trade-off evaluations,
formal Master Supply Agreement (MSA) legal dispute chargebacks, and quarantine directives.
Uses Groq API when available with robust deterministic enterprise fallback.
"""

import os
import json
from typing import Dict, Any, Optional

try:
    from groq import Groq
except ImportError:
    Groq = None


class StrategicDecisionAgent:
    def __init__(self, model_name: str = "llama-3.3-70b-versatile"):
        self.model_name = model_name
        self.api_key = os.environ.get("GROQ_API_KEY")
        self.client = None
        if self.api_key and Groq is not None:
            try:
                self.client = Groq(api_key=self.api_key)
            except Exception:
                self.client = None

    def reason(self, context: Dict[str, Any]) -> Dict[str, str]:
        """
        Executes ReAct reasoning loop.
        Context expected:
        {
            'batch_id': str,
            'supplier': str,
            'total_units': int,
            'route_counts': dict,
            'total_nsv': float,
            'uplift_data': dict,
            'anomalies': dict
        }
        """
        batch_id = context.get('batch_id', 'UNKNOWN')
        supplier = context.get('supplier', 'Supplier Inc')
        routes = context.get('route_counts', {})
        nsv = context.get('total_nsv', 0.0)
        uplift = context.get('uplift_data', {})
        anomalies = context.get('anomalies', {})

        # If Groq client is configured, call LLM
        if self.client:
            try:
                prompt = f"""
                You are the Lead Reverse Logistics & Quality Counsel for Gadgetbay Electronics.
                Analyze the following batch triage telemetry:
                - Batch ID: {batch_id}
                - Primary Supplier: {supplier}
                - Total Units: {context.get('total_units')}
                - Optimized Route Allocations: {json.dumps(routes)}
                - Total Net Salvage Value (NSV): ${nsv:,.2f}
                - Net Financial Uplift vs Naive Baseline: ${uplift.get('dollar_uplift', 0.0):,.2f} ({uplift.get('pct_uplift', 0.0)}%)
                - Anomaly Sentinel Telemetry: {json.dumps(anomalies)}

                Generate a comprehensive executive disposition plan. Return strictly valid JSON with four keys:
                1. "executive_summary": High-level strategic recommendation for the VP of Operations.
                2. "financial_tradeoff_analysis": Rigorous breakdown of cash guarantees vs. labor/holding risks.
                3. "legal_chargeback_draft": Formal contractual debit notice to the supplier citing MSA Section 4.2 warranty indemnification.
                4. "warehouse_quarantine_directive": Floor execution instructions for safety containment.
                """
                completion = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
                res = json.loads(completion.choices[0].message.content)
                if all(k in res for k in ["executive_summary", "financial_tradeoff_analysis", "legal_chargeback_draft", "warehouse_quarantine_directive"]):
                    return res
            except Exception as e:
                pass  # Fall through to deterministic enterprise synthesis

        # Deterministic Enterprise Strategy Synthesis
        is_quarantine = anomalies.get('is_quarantine_required', False)
        safety_alert = anomalies.get('safety_alert', {})
        rtv_count = routes.get('RTV', 0)
        refurb_count = routes.get('REFURBISH', 0)
        scrap_count = routes.get('SCRAP', 0)
        restock_count = routes.get('RESTOCK', 0)
        liquidate_count = routes.get('LIQUIDATE', 0)

        dollar_uplift = uplift.get('dollar_uplift', 0.0)
        pct_uplift = uplift.get('pct_uplift', 0.0)

        # 1. Executive Summary
        if is_quarantine:
            defect_rate = safety_alert.get('defect_rate_pct', 48.0)
            exec_summary = (
                f"CRITICAL DISPOSITION DIRECTIVE FOR BATCH {batch_id}: Immediate containment executed due to a "
                f"{defect_rate}% failure rate from thermal/battery swelling defects. Optimized disposition channels "
                f"{rtv_count} units to Return-to-Vendor (RTV) to recover 100% manufacturer warranty credit under MSA Section 4.2, "
                f"allocates {refurb_count} non-hazardous units to internal technical refurbishment, and quarantines {scrap_count} "
                f"severely damaged units. Total projected net salvage value stands at ${nsv:,.2f}, delivering a ${dollar_uplift:,.2f} "
                f"(+{pct_uplift}%) uplift over traditional FIFO liquidation."
            )
        else:
            exec_summary = (
                f"OPTIMAL TRIAGE CLEARANCE FOR BATCH {batch_id}: Quality telemetry indicates standard return parameters. "
                f"Disposition algorithm directs {restock_count} pristine units to active inventory (Restock), {refurb_count} "
                f"units to technician refurbishment, {rtv_count} units to vendor warranty credit, and {liquidate_count} units to "
                f"secondary wholesale channels. Projected net salvage value is ${nsv:,.2f} (+{pct_uplift}% financial uplift)."
            )

        # 2. Financial Tradeoff Analysis
        tradeoffs = (
            f"• Contractual RTV Recovery ({rtv_count} units): Secures guaranteed vendor cash credit with zero internal labor "
            f"overhead ($0 risk) and circumvents secondary market holding depreciation (0.2%/day).\n"
            f"• Graded Refurbishment ({refurb_count} units): Generates maximum secondary resale margin, utilizing available shift labor "
            f"while remaining within strict parts inventory limits.\n"
            f"• Uplift Realization: By dynamically routing units based on individual unit economics rather than bulk liquidation, "
            f"the operation captures ${nsv:,.2f} in net recovery—an incremental +${dollar_uplift:,.2f} gain over traditional warehouse baselines."
        )

        # 3. Legal Chargeback Draft
        if is_quarantine:
            affected = safety_alert.get('affected_units', 12)
            total = safety_alert.get('batch_total', 25)
            legal_draft = (
                f"FORMAL NOTICE OF DEFECTIVE LOT & FULL CHARGEBACK INDEMNIFICATION\n"
                f"DATE: Ref #{batch_id}-LEGAL-RMA\n"
                f"TO: Legal & Quality Assurance, {supplier}\n"
                f"FROM: Reverse Logistics & Compliance Division, Gadgetbay Operations\n\n"
                f"Pursuant to Section 4.2 ('Manufacturer Defect Indemnification & Product Safety Warranty') of the Master Supply Agreement:\n"
                f"Notice is hereby served that Batch #{batch_id} exhibited an unacceptably high critical defect concentration of "
                f"{safety_alert.get('defect_rate_pct', 48.0)}% ({affected} of {total} inspected units), exhibiting lithium-ion cell swelling "
                f"and thermal instability exceeding the contractual 5.0% Acceptable Quality Limit (AQL).\n\n"
                f"Demand is hereby executed for:\n"
                f"1. Immediate 100% credit invoice debit covering all affected serials.\n"
                f"2. Vendor-subsidized courier pickup and hazardous material hazmat freight expenses.\n"
                f"3. Written Root-Cause Corrective Action (RCCA) report within ten (10) business days."
            )
        else:
            legal_draft = (
                f"STANDARD WARRANTY RECOVERY CLAIM — BATCH #{batch_id}\n"
                f"TO: Returns Department, {supplier}\n"
                f"STATUS: Standard RTV Claims Processing\n"
                f"Submitting {rtv_count} units under contractual return window for standard restock credit processing."
            )

        # 4. Quarantine Directive
        if is_quarantine:
            quarantine_dir = (
                f"MANDATORY FLOOR ISOLATION ORDER — BATCH #{batch_id}\n"
                f"LOCATION: Zone D-Hazardous (Isolated Fire-Safe Container Vault)\n"
                f"PROTOCOL: High thermal / swelling hazard confirmed. Immediately freeze serial numbers in ERP. "
                f"Do not attempt internal charging, disassembly, or repackaging. Transport under ambient air-cooled "
                f"fire-containment tubs to Zone D pending Hazmat return dispatch."
            )
        else:
            quarantine_dir = (
                f"STANDARD INVENTORY CLEARANCE — BATCH #{batch_id}\n"
                f"LOCATION: Main Receiving Bay #4\n"
                f"PROTOCOL: Normal handling clearance. Route units to respective shelving and refurbishment stations."
            )

        return {
            "executive_summary": exec_summary,
            "financial_tradeoff_analysis": tradeoffs,
            "legal_chargeback_draft": legal_draft,
            "warehouse_quarantine_directive": quarantine_dir
        }
