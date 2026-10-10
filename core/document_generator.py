"""
Document Automation & PDF Report Generation Module.
Compiles executive RMA Debit Notes, Refurbishment Job Tickets,
Quarantine Containment Certificates, and financial manifests into high-resolution PDFs.
"""

import io
import os
from datetime import datetime
from typing import Dict, Any, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether
)


def generate_batch_dossier_pdf(
    batch_id: str,
    vendor: str,
    optimization_results: Dict[str, Any],
    uplift_data: Dict[str, Any],
    anomalies: Dict[str, Any],
    agent_decision: Dict[str, str],
    output_filepath: Optional[str] = None
) -> bytes:
    """
    Builds a multi-section executive reverse logistics PDF dossier.
    Returns bytes and optionally saves to disk.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#2563EB'),
        spaceAfter=12
    )
    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=10,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#334155')
    )
    alert_style = ParagraphStyle(
        'AlertText',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#DC2626')
    )
    note_style = ParagraphStyle(
        'NoteText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor('#64748B')
    )

    elements = []

    # 1. Header Banner
    elements.append(Paragraph("GADGETBAY REVERSE LOGISTICS · CYPHER CHALLENGE 10", title_style))
    elements.append(Paragraph(f"EXECUTIVE DISPOSITION DOSSIER & RMA AUDIT MANIFEST | BATCH: {batch_id}", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0284C7'), spaceAfter=10))

    # 2. Metadata Table
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    meta_table_data = [
        [
            Paragraph(f"<b>Batch Identifier:</b> {batch_id} (Wireless Headphones HP-220)", body_style),
            Paragraph(f"<b>Designated Supplier:</b> {vendor}", body_style)
        ],
        [
            Paragraph(f"<b>Assessment Snapshot Date:</b> 2026-11-16 (Audit Time: {now_str})", body_style),
            Paragraph(f"<b>Net Projected Salvage:</b> ₹{optimization_results.get('total_nsv', 0.0):,.2f}", body_style)
        ],
        [
            Paragraph(f"<b>Financial Uplift vs Baseline:</b> +₹{uplift_data.get('dollar_uplift', 0.0):,.2f} (+{uplift_data.get('pct_uplift', 0.0)}%)", body_style),
            Paragraph(f"<b>Quality Anomaly:</b> {'⚠️ RECURRING DEFECT CLUSTER DETECTED' if anomalies.get('anomalies_detected') else '✅ STANDARD CLEARANCE'}",
                      alert_style if anomalies.get('anomalies_detected') else body_style)
        ]
    ]
    t_meta = Table(meta_table_data, colWidths=[270, 270])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(t_meta)
    elements.append(Spacer(1, 8))

    # 3. Auditable Unit-Level Economics Table (Problem 3 Compliance)
    elements.append(Paragraph("1. Auditable Recovery Route Economics (Unit-Level Calculation)", h2_style))
    audit_table_data = [
        ["Recovery Route", "Accounting Formula", "Gross Proceeds", "Direct Costs/Deductions", "Net Recovery", "Baseline Uplift"]
    ]
    audit_table_data.append([
        "REFURBISH",
        "Selling Price (₹2,500) × Resale (75%) − Refurb (₹250)",
        "₹1,875.00",
        "-₹250.00 (Parts/Labor)",
        "₹1,625.00 / unit",
        "+₹1,135.00 / unit"
    ])
    audit_table_data.append([
        "VENDOR CREDIT (RTV)",
        "Cost Price (₹1,400) × Credit (60%) [≤30-Day Window]",
        "₹840.00",
        "₹0.00 (Vendor Terms)",
        "₹840.00 / unit",
        "+₹350.00 / unit"
    ])
    audit_table_data.append([
        "LIQUIDATION (BASELINE)",
        "Cost Price (₹1,400) × Recovery (35% Grade B)",
        "₹490.00",
        "₹0.00 (As-Is Wholesale)",
        "₹490.00 / unit",
        "₹0.00 (Baseline)"
    ])
    t_audit = Table(audit_table_data, colWidths=[95, 175, 75, 95, 80, 60])
    t_audit.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7.5),
        ('FONTSIZE', (0, 1), (-1, -1), 7.5),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (2, 1), (5, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(t_audit)
    elements.append(Paragraph("<i>*Note: Net salvage recovery is defined as realized cash proceeds less direct variable recovery costs. Sunk original historical cost (₹1,400) is excluded to prevent double-deduction. Bulk liquidation baseline: 40 units × ₹490 = ₹19,600.00.</i>", note_style))
    elements.append(Spacer(1, 8))

    # 4. Time-to-Cash Stage Analysis (Problem 4 Compliance)
    elements.append(Paragraph("2. Time-to-Cash Multi-Stage Analysis", h2_style))
    ttc_table_data = [
        ["Channel", "Processing Time", "Time to Sale", "Payment Settlement Window", "Total Time-to-Cash"]
    ]
    ttc_table_data.append(["REFURBISH", "5 days (Bench Repair)", "7 days (Demand Runway)", "7 days (Marketplace Payout)", "19 Days Total"])
    ttc_table_data.append(["VENDOR CREDIT (RTV)", "2 days (RMA Inspection)", "0 days (Direct Credit)", "30 days (Vendor Net-30 AP)", "32 Days Total"])
    ttc_table_data.append(["LIQUIDATION", "1 day (Pallet Staging)", "2 days (Auction Bidding)", "3 days (Wire on Invoice)", "6 Days Total (Fastest Cash)"])
    t_ttc = Table(ttc_table_data, colWidths=[100, 100, 100, 140, 100])
    t_ttc.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7.5),
        ('FONTSIZE', (0, 1), (-1, -1), 7.5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(t_ttc)
    elements.append(Spacer(1, 8))

    # 5. Route Allocation Breakdown Table
    elements.append(Paragraph("3. Optimized Batch Allocation Summary", h2_style))
    routes = optimization_results.get('route_counts', {})
    route_table_data = [
        ["Recovery Channel", "Allocated Units", "Operational Route Description", "Projected NSV Contribution"]
    ]
    channel_descriptions = {
        'RESTOCK': "Immediate inventory reintegration (Open-Box Pristine)",
        'RTV': "Return to Vendor warranty claim / invoice debit credit",
        'REFURBISH': "Internal technical restoration for graded secondary resale",
        'LIQUIDATE': "Wholesale B2B secondary auction liquidation lot",
        'SCRAP': "Safe electronic recycling / raw material extraction"
    }

    decisions = optimization_results.get('unit_decisions', [])
    channel_nsv_totals = {}
    for d in decisions:
        ch = d['assigned_channel']
        channel_nsv_totals[ch] = channel_nsv_totals.get(ch, 0.0) + d['net_salvage_value']

    for ch, count in routes.items():
        desc = channel_descriptions.get(ch, "Custom disposition channel")
        c_tot = channel_nsv_totals.get(ch, 0.0)
        route_table_data.append([ch, str(count), desc, f"₹{c_tot:,.2f}"])

    t_routes = Table(route_table_data, colWidths=[90, 70, 270, 110])
    t_routes.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8.0),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),
        ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(t_routes)
    elements.append(Spacer(1, 8))

    # 4. Anomaly Sentinel & Quarantine Action
    if anomalies.get('is_quarantine_required'):
        elements.append(Paragraph("2. Mandatory Safety Quarantine Order (Level 1)", h2_style))
        safety = anomalies.get('safety_alert', {})
        quar_data = [
            ["DEFECT PATTERN", safety.get('defect_category', 'Lithium-Ion Swelling')],
            ["AFFECTED UNITS", f"{safety.get('affected_units')} of {safety.get('batch_total')} ({safety.get('defect_rate_pct')}%)"],
            ["CONTAINMENT ZONE", safety.get('quarantine_zone', 'Zone D-Hazardous Vault')],
            ["LEGAL DIRECTIVE", safety.get('msa_clause_reference', 'Section 4.2 Indemnification')]
        ]
        t_quar = Table(quar_data, colWidths=[140, 400])
        t_quar.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#FEE2E2')),
            ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#FFF1F2')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#991B1B')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#FCA5A5')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(t_quar)
        elements.append(Spacer(1, 10))

    # 6. Three-Level Supplier Quality Analysis (Problem 5 Compliance)
    three_lvl = anomalies.get('three_level_quality_analysis', {})
    if three_lvl:
        elements.append(Paragraph("4. Three-Level Supplier Quality Investigation", h2_style))
        lvl1 = three_lvl.get('level_1_observed_pattern', {})
        lvl2 = three_lvl.get('level_2_quality_investigation', {})
        lvl3 = three_lvl.get('level_3_contractual_action', {})
        
        q_data = [
            [Paragraph("<b>Level 1: Observed Pattern</b>", body_style), Paragraph(lvl1.get('summary', ''), body_style)],
            [Paragraph("<b>Level 2: Cross-Batch Investigation</b>", body_style), Paragraph(lvl2.get('summary', ''), body_style)],
            [Paragraph("<b>Level 3: Contractual RMA Action</b>", body_style), Paragraph(lvl3.get('summary', ''), body_style)]
        ]
        t_q = Table(q_data, colWidths=[150, 390])
        t_q.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F1F5F9')),
            ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#F8FAFC')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(t_q)
        elements.append(Spacer(1, 8))

    # 7. Agentic Reasoning & Strategic Executive Notes
    elements.append(Paragraph("5. Executive AI Counsel Recommendation & Trade-Offs", h2_style))
    exec_text = agent_decision.get('executive_summary', 'Triage completed.')
    elements.append(Paragraph(f"<b>Operational Directive:</b> {exec_text}", body_style))
    elements.append(Spacer(1, 4))

    trade_text = agent_decision.get('financial_tradeoff_analysis', '')
    elements.append(Paragraph(f"<b>Financial Risk Synthesis:</b><br/>{trade_text.replace(chr(10), '<br/>')}", body_style))
    elements.append(Spacer(1, 10))

    # 6. Formal Sign-Off Section
    sig_data = [
        [
            Paragraph("<b>QA Engineering Inspector:</b>", body_style),
            Paragraph("<b>Reverse Logistics Operations Lead:</b>", body_style)
        ],
        [
            Paragraph("Sign: ___________________________ Date: _________", body_style),
            Paragraph("Sign: ___________________________ Date: _________", body_style)
        ]
    ]
    t_sig = Table(sig_data, colWidths=[270, 270])
    t_sig.setStyle(TableStyle([
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(KeepTogether(t_sig))

    # Compile document
    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    if output_filepath:
        os.makedirs(os.path.dirname(os.path.abspath(output_filepath)), exist_ok=True)
        with open(output_filepath, "wb") as f:
            f.write(pdf_bytes)

    return pdf_bytes
