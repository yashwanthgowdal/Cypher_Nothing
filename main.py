"""
Reverse Logistics Autonomous Optimization Platform.
Unified production entry point for batch triage, ML inference, mathematical optimization,
anomaly sentinel monitoring, agentic legal reasoning, and executive PDF reporting.
"""

import sys
import os

# Ensure UTF-8 stdout encoding on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import argparse
from typing import Optional, Dict, Any

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from core.data_pipeline import DataPipeline
from core.ml_disposition import DispositionModelPipeline
from core.mathematical_engine import optimize_batch, calculate_baseline_comparison, calculate_unit_nsv
from core.anomaly_sentinel import AnomalySentinel
from core.decision_agent import StrategicDecisionAgent
from core.document_generator import generate_batch_dossier_pdf

console = Console(highlight=False, legacy_windows=False)


def display_header():
    title = Text("GADGETBAY REVERSE LOGISTICS", style="bold white on blue", justify="center")
    subtitle = Text("Autonomous Returns Disposition & Anomaly Sentinel Platform\nEnterprise Production Engine v2.0", style="italic cyan", justify="center")
    console.print(Panel(Text.assemble(title, "\n", subtitle), border_style="blue", box=box.ROUNDED))


def run_batch_triage(
    batch_id: str,
    max_labor_hours: Optional[float] = None,
    generate_pdf: bool = True,
    pdf_output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Executes 100% end-to-end reverse logistics triage on a specific supplier batch.
    """
    console.print(f"\n[bold cyan]▶ Loading Enriched Returns Pipeline for Batch: [yellow]{batch_id}[/]...[/]")

    pipeline = DataPipeline()
    batch_df = pipeline.get_unified_returns(batch_id=batch_id)

    if batch_df.empty:
        console.print(f"[bold red]❌ Batch '{batch_id}' not found in returns database.[/]")
        return {}

    supplier_name = batch_df['supplier'].iloc[0]
    total_units = len(batch_df)
    sku_name = batch_df['sku'].iloc[0]
    product_name = batch_df['product_name'].iloc[0]

    console.print(f"  • Supplier: [bold]{supplier_name}[/] | SKU: [bold]{sku_name}[/] ({product_name})")
    console.print(f"  • Volume: [bold green]{total_units} units[/] under inspection\n")

    # 1. Machine Learning Probabilistic Predictions
    console.print("[bold blue]1. Executing ML Disposition Inference...[/]")
    ml_engine = DispositionModelPipeline()
    ml_predictions = ml_engine.predict(batch_df)

    # 2. Mathematical Optimization with Operational Constraints
    console.print("[bold blue]2. Running Constrained Mathematical NSV Optimizer...[/]")
    opt_results = optimize_batch(batch_df, max_labor_hours=max_labor_hours)
    total_nsv = opt_results['total_nsv']

    # 3. Financial Uplift Benchmark Calculation
    uplift = calculate_baseline_comparison(batch_df, optimized_nsv=total_nsv)

    # 4. Anomaly Sentinel Quality Inspection
    console.print("[bold blue]3. Inspecting Defect Clusters & Safety Compliance...[/]")
    sentinel = AnomalySentinel()
    anomalies = sentinel.analyze_batch(batch_df)

    # 5. Strategic Agent Reasoning
    console.print("[bold blue]4. Synthesizing Strategic Directives & MSA Reasoner...[/]")
    agent = StrategicDecisionAgent()
    agent_context = {
        'batch_id': batch_id,
        'supplier': supplier_name,
        'total_units': total_units,
        'route_counts': opt_results['route_counts'],
        'total_nsv': total_nsv,
        'uplift_data': uplift,
        'anomalies': anomalies
    }
    decision = agent.reason(agent_context)

    # --- RICH VISUAL OUTPUTS ---
    # Metric Summary Table
    metric_table = Table(title="Batch Financial & Operational Scorecard", box=box.ROUNDED, header_style="bold magenta")
    metric_table.add_column("Metric", style="bold")
    metric_table.add_column("Value", justify="right")
    metric_table.add_column("Benchmark Context", style="dim")

    metric_table.add_row("Total Batch Units", f"{total_units:,}", "100% Inbound Inspected")
    metric_table.add_row("Projected Net Salvage Value", f"${total_nsv:,.2f}", "Exact Mathematical Realization")
    metric_table.add_row("Traditional Naive Salvage", f"${uplift['naive_salvage_value']:,.2f}", "FIFO Bulk Liquidation Baseline")
    metric_table.add_row("Net Dollar Uplift", f"[bold green]+${uplift['dollar_uplift']:,.2f}[/]", f"+{uplift['pct_uplift']}% Value Lift")
    metric_table.add_row("Refurb Labor Utilized", f"{opt_results['labor_hours_used']} hrs", "Technician Work Shift Load")

    console.print(metric_table)
    console.print("")

    # Route Breakdown Table
    route_table = Table(title="Optimized Channel Allocation", box=box.SIMPLE_HEAVY, header_style="bold cyan")
    route_table.add_column("Channel", style="bold")
    route_table.add_column("Allocated Units", justify="center")
    route_table.add_column("Share %", justify="center")
    route_table.add_column("Operational Channel Action")

    for ch, count in opt_results['route_counts'].items():
        pct = (count / total_units) * 100
        color = "green" if ch == "RESTOCK" else "blue" if ch == "RTV" else "yellow" if ch == "REFURBISH" else "red"
        route_table.add_row(
            f"[{color}]{ch}[/]",
            str(count),
            f"{pct:.1f}%",
            f"Transfer {count} units to {ch} pipeline"
        )
    console.print(route_table)
    console.print("")

    # Anomaly / Quarantine Alert Panel
    if anomalies.get('is_quarantine_required'):
        safety = anomalies['safety_alert']
        alert_body = (
            f"[bold red]CRITICAL SAFETY DEFECT SPIKE DETECTED[/]\n"
            f"• Defect Pattern: [bold]{safety['defect_category']}[/]\n"
            f"• Defect Rate: [bold]{safety['defect_rate_pct']}%[/] (Max permissible: {safety['allowable_threshold_pct']}%)\n"
            f"• Mandatory Action: [bold yellow]{safety['recommended_action']}[/]\n"
            f"• Quarantine Facility: [bold underline]{safety['quarantine_zone']}[/]\n"
            f"• Legal Basis: [bold]{safety['msa_clause_reference']}[/]"
        )
        console.print(Panel(alert_body, title="🚨 ANOMALY SENTINEL: LEVEL 1 HAZARD LOCKOUT", border_style="red", box=box.HEAVY))
        console.print("")

    # Executive AI Strategy
    exec_panel = Panel(
        f"[bold]Operational Strategy Directive:[/]\n{decision['executive_summary']}\n\n"
        f"[bold]Financial Trade-off Analysis:[/]\n{decision['financial_tradeoff_analysis']}",
        title="🧠 EXECUTIVE AI COUNSEL STRATEGY",
        border_style="green",
        box=box.ROUNDED
    )
    console.print(exec_panel)
    console.print("")

    # 6. Executive PDF Manifest Generation
    if generate_pdf:
        default_pdf_path = pdf_output_path or os.path.join("output", f"Gadgetbay_Manifest_{batch_id}.pdf")
        generate_batch_dossier_pdf(
            batch_id=batch_id,
            vendor=supplier_name,
            optimization_results=opt_results,
            uplift_data=uplift,
            anomalies=anomalies,
            agent_decision=decision,
            output_filepath=default_pdf_path
        )
        console.print(f"[bold green]📄 Official Audit Dossier & RMA PDF generated:[/] [underline]{default_pdf_path}[/]\n")

    return {
        'batch_id': batch_id,
        'optimization_results': opt_results,
        'uplift': uplift,
        'anomalies': anomalies,
        'decision': decision
    }


def scan_single_unit(return_id: str):
    """Real-time unit scanner simulation."""
    console.print(f"\n[bold cyan]🔍 Scanning Inbound Unit Serial: [yellow]{return_id}[/]...[/]")
    pipeline = DataPipeline()
    returns_df = pipeline.get_unified_returns()

    unit = returns_df[returns_df['return_id'] == return_id]
    if unit.empty:
        console.print(f"[bold red]❌ Serial '{return_id}' not found in database.[/]")
        return

    row = unit.iloc[0].to_dict()
    eval_res = calculate_unit_nsv(row)
    ml_engine = DispositionModelPipeline()
    ml_pred = ml_engine.predict(row)[0]

    scan_table = Table(title=f"Inbound Scanner Readout: {return_id}", box=box.ROUNDED)
    scan_table.add_column("Property", style="bold")
    scan_table.add_column("Value")

    scan_table.add_row("SKU", str(row['sku']))
    scan_table.add_row("Product", str(row['product_name']))
    scan_table.add_row("Supplier", str(row['supplier']))
    scan_table.add_row("Condition Grade", str(row['grade']))
    scan_table.add_row("Detected Fault", str(row['fault_code']))
    scan_table.add_row("Days Since Dispatch", f"{row['days_since_dispatch']} days (Window: {row['window_days']} days)")
    scan_table.add_row("ML Prediction", f"{ml_pred['disposition']} (Confidence: {ml_pred['confidence'] * 100:.1f}%)")
    scan_table.add_row("Exact Net Salvage Value", f"${eval_res['max_nsv']:.2f}")
    scan_table.add_row("Assigned Route Channel", f"[bold green]{eval_res['best_channel']}[/]")

    console.print(scan_table)


def run_fleet_overview():
    """Runtimes triage across all active batches in the warehouse."""
    pipeline = DataPipeline()
    batches = pipeline.list_available_batches()

    fleet_table = Table(title="Warehouse Active Fleet Overview", box=box.ROUNDED, header_style="bold cyan")
    fleet_table.add_column("Batch ID", style="bold yellow")
    fleet_table.add_column("Supplier", style="bold")
    fleet_table.add_column("SKU & Product Name")
    fleet_table.add_column("Units", justify="right")
    fleet_table.add_column("Safety Flags", justify="center")
    fleet_table.add_column("Action Directive")

    for b_id, b_meta in batches.items():
        flag_text = f"[bold red]{b_meta['safety_flags']}[/]" if b_meta['safety_flags'] > 0 else "[green]0[/]"
        action = "[bold red]QUARANTINE[/]" if b_meta['safety_flags'] > 0 else "[green]AUTO-TRIAGE[/]"
        fleet_table.add_row(
            b_id,
            b_meta['supplier'],
            f"{b_meta['sku']} ({b_meta['product_name']})",
            str(b_meta['total_units']),
            flag_text,
            action
        )

    console.print(fleet_table)


def main():
    parser = argparse.ArgumentParser(description="Gadgetbay Reverse Logistics Platform")
    parser.add_argument("--batch", type=str, default="HB-09", help="Supplier batch ID to triage (default: HB-09)")
    parser.add_argument("--all-batches", action="store_true", help="Triage all warehouse batches sequentially")
    parser.add_argument("--overview", action="store_true", help="Display warehouse fleet overview")
    parser.add_argument("--scan", type=str, help="Scan individual unit by return_id (e.g. RET-HB09-101)")
    parser.add_argument("--train", action="store_true", help="Train and validate the ML model")
    parser.add_argument("--labor-cap", type=float, help="Optional technician labor hour capacity limit")
    parser.add_argument("--pdf", type=str, help="Custom output path for generated PDF")

    args = parser.parse_args()

    display_header()

    if args.train:
        console.print("[bold cyan]▶ Initiating Machine Learning Model Training...[/]")
        ml = DispositionModelPipeline()
        meta = ml.train_and_evaluate()
        console.print(f"[bold green]✅ Model training complete![/] Validation Accuracy: [bold]{meta['accuracy'] * 100:.2f}%[/]")
        return

    if args.scan:
        scan_single_unit(args.scan)
        return

    if args.overview:
        run_fleet_overview()
        return

    if args.all_batches:
        pipeline = DataPipeline()
        batches = pipeline.list_available_batches()
        console.print(f"[bold cyan]Running sequential triage across {len(batches)} batches...[/]\n")
        for b_id in batches.keys():
            run_batch_triage(batch_id=b_id, max_labor_hours=args.labor_cap)
        return

    # Default: triage specified batch (HB-09)
    run_batch_triage(batch_id=args.batch, max_labor_hours=args.labor_cap, pdf_output_path=args.pdf)


if __name__ == "__main__":
    main()
