"""
Production Web Application Server for Gadgetbay Reverse Logistics.
Serves the modern cyber-industrial web cockpit and high-performance REST APIs.
"""

import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import io
from flask import Flask, render_template, jsonify, request, send_file
from core.data_pipeline import DataPipeline
from core.ml_disposition import DispositionModelPipeline
from core.mathematical_engine import optimize_batch, calculate_baseline_comparison, calculate_unit_nsv
from core.anomaly_sentinel import AnomalySentinel
from core.decision_agent import StrategicDecisionAgent
from core.document_generator import generate_batch_dossier_pdf

from core.database import verify_user, get_user_by_id, record_scan_event, get_recent_scans, get_scan_statistics

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = "gadgetbay_enterprise_secure_token_key_2026"
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
pipeline = DataPipeline()
ml_pipeline = DispositionModelPipeline()
sentinel = AnomalySentinel()
agent = StrategicDecisionAgent()

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    """Authenticates worker, supervisor, or executive credentials."""
    data = request.get_json() or {}
    login_id = str(data.get("login_id") or data.get("id") or "").strip()
    password = str(data.get("password") or "").strip()

    user = verify_user(login_id, password)
    if not user:
        return jsonify({"success": False, "error": "Invalid Worker ID or Password."}), 401

    return jsonify({
        "success": True,
        "user": {
            "id": user["login_id"],
            "login_id": user["login_id"],
            "name": user["name"],
            "role": user["role"],
            "title": user["title"],
            "station": user["station"],
            "avatar": user["avatar"]
        }
    })


@app.route("/api/scans/record", methods=["POST"])
def record_scan_api():
    """Records a completed physical bin placement into the database."""
    data = request.get_json() or {}
    scan_id = record_scan_event(data)
    stats = get_scan_statistics()
    return jsonify({"success": True, "scan_id": scan_id, "stats": stats})


@app.route("/api/scans/history", methods=["GET"])
def get_scans_history_api():
    """Returns real-time confirmed physical scans from database."""
    scans = get_recent_scans(limit=30)
    stats = get_scan_statistics()
    return jsonify({"scans": scans, "stats": stats})


@app.route("/")
def index():
    """Serves the main web cockpit."""
    return render_template("index.html")


@app.route("/api/batches", methods=["GET"])
def get_batches():
    """Returns summary metadata of all batches present in the warehouse."""
    batches = pipeline.list_available_batches()
    return jsonify({"batches": batches})


@app.route("/api/triage/<batch_id>", methods=["GET"])
def triage_batch_api(batch_id):
    """
    Executes real-time mathematical optimization and triage on a specific batch.
    Supports dynamic shift labor hour capping via ?labor_cap=<float>.
    """
    labor_cap = request.args.get("labor_cap", default=None, type=float)

    batch_df = pipeline.get_unified_returns(batch_id=batch_id)
    if batch_df.empty:
        return jsonify({"error": f"Batch '{batch_id}' not found."}), 404

    supplier_name = str(batch_df['supplier'].iloc[0])
    sku_name = str(batch_df['sku'].iloc[0])
    product_name = str(batch_df['product_name'].iloc[0])
    total_units = len(batch_df)

    # 1. Constrained Mathematical Optimization
    opt_results = optimize_batch(batch_df, max_labor_hours=labor_cap)

    # 2. Financial Uplift Benchmark
    uplift = calculate_baseline_comparison(batch_df, optimized_nsv=opt_results['total_nsv'])

    # 3. Anomaly Sentinel Scan
    anomalies = sentinel.analyze_batch(batch_df)

    # 4. Strategic ReAct Agent Synthesis
    agent_context = {
        'batch_id': batch_id,
        'supplier': supplier_name,
        'total_units': total_units,
        'route_counts': opt_results['route_counts'],
        'total_nsv': opt_results['total_nsv'],
        'uplift_data': uplift,
        'anomalies': anomalies
    }
    decision = agent.reason(agent_context)

    return jsonify({
        "batch_id": batch_id,
        "supplier": supplier_name,
        "sku": sku_name,
        "product_name": product_name,
        "total_units": total_units,
        "optimization_results": opt_results,
        "uplift": uplift,
        "anomalies": anomalies,
        "decision": decision
    })


@app.route("/api/scan/<path:return_id>", methods=["GET"])
def scan_serial_api(return_id):
    """
    Executes sub-5ms diagnosis for a scanned return serial number or SKU.
    Returns 200 with unit details if found, or 404 with structured unregistered notice.
    """
    clean_id = return_id.strip()
    returns_df = pipeline.get_unified_returns()

    # 1. Exact or case-insensitive match on return_id
    unit = returns_df[returns_df['return_id'].str.upper() == clean_id.upper()]

    # 2. Match on sku if not matched on return_id
    if unit.empty:
        unit = returns_df[returns_df['sku'].str.upper() == clean_id.upper()]

    if unit.empty:
        return jsonify({
            "found": False,
            "scanned_code": clean_id,
            "error": "NOT_FOUND_IN_DATABASE",
            "message": f"Scanned barcode '{clean_id}' was read successfully by the optical sensor, but does not match any registered item in the active Gadgetbay RMA manifest database.",
            "status": "UNREGISTERED_INBOUND"
        }), 404

    row = unit.iloc[0].to_dict()
    eval_res = calculate_unit_nsv(row)
    ml_pred = ml_pipeline.predict(row)[0]

    return jsonify({
        "found": True,
        "scanned_code": clean_id,
        "unit": {
            "return_id": row['return_id'],
            "sku": row['sku'],
            "product_name": row['product_name'],
            "supplier": row['supplier'],
            "grade": row['grade'],
            "fault_code": row['fault_code'],
            "days_since_dispatch": int(row['days_since_dispatch']),
            "window_days": int(row['window_days']),
            "cost_price": float(row['cost_price']),
            "retail_price": float(row['retail_price'])
        },
        "ml_prediction": ml_pred,
        "evaluation": eval_res
    })


def _get_batch_pdf_bytes(filename):
    clean_batch_id = filename.replace(".pdf", "")
    batch_df = pipeline.get_unified_returns(batch_id=clean_batch_id)
    if batch_df.empty:
        return None, clean_batch_id

    supplier_name = str(batch_df['supplier'].iloc[0])
    opt_results = optimize_batch(batch_df)
    uplift = calculate_baseline_comparison(batch_df, optimized_nsv=opt_results['total_nsv'])
    anomalies = sentinel.analyze_batch(batch_df)
    decision = agent.reason({
        'batch_id': clean_batch_id,
        'supplier': supplier_name,
        'total_units': len(batch_df),
        'route_counts': opt_results['route_counts'],
        'total_nsv': opt_results['total_nsv'],
        'uplift_data': uplift,
        'anomalies': anomalies
    })

    disk_path = os.path.join(os.path.abspath("output"), f"Gadgetbay_RMA_{clean_batch_id}.pdf")
    pdf_bytes = generate_batch_dossier_pdf(
        batch_id=clean_batch_id,
        vendor=supplier_name,
        optimization_results=opt_results,
        uplift_data=uplift,
        anomalies=anomalies,
        agent_decision=decision,
        output_filepath=disk_path
    )
    return pdf_bytes, clean_batch_id


@app.route("/api/download-pdf/<filename>", methods=["GET"])
@app.route("/api/download/<filename>", methods=["GET"])
def download_pdf_api(filename):
    """
    Generates and downloads the executive ReportLab PDF dossier as a real attachment.
    """
    pdf_bytes, batch_id = _get_batch_pdf_bytes(filename)
    if not pdf_bytes:
        return jsonify({"error": f"Batch '{batch_id}' not found."}), 404

    response = send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"Gadgetbay_RMA_{batch_id}.pdf"
    )
    response.headers["Content-Disposition"] = f'attachment; filename="Gadgetbay_RMA_{batch_id}.pdf"'
    response.headers["Content-Type"] = "application/pdf"
    return response


@app.route("/api/view-pdf/<filename>", methods=["GET"])
def view_pdf_inline(filename):
    """
    Opens the PDF directly inside the browser's native PDF reader.
    """
    pdf_bytes, batch_id = _get_batch_pdf_bytes(filename)
    if not pdf_bytes:
        return jsonify({"error": f"Batch '{batch_id}' not found."}), 404

    response = send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=False
    )
    response.headers["Content-Disposition"] = f'inline; filename="Gadgetbay_RMA_{batch_id}.pdf"'
    response.headers["Content-Type"] = "application/pdf"
    return response


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n==================================================================")
    print(f"🚀 Gadgetbay Reverse Logistics Web Cockpit is LIVE!")
    print(f"🔗 Open in your browser: http://127.0.0.1:{port}")
    print(f"==================================================================\n")
    app.run(host="0.0.0.0", port=port, debug=False)
