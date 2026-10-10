"""
Database Manager for Gadgetbay Reverse Logistics Platform.
Implements SQLite persistent storage for:
1. Operator authentication & role assignment (Worker, Supervisor, Executive)
2. Scanned barcode inventory & real-time chain-of-custody tracking
3. Historical audit log of all triage directives and bin confirmations
"""

import sqlite3
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from core.data_pipeline import DataPipeline

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "warehouse_inventory.db")

def get_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes tables, seeds registered users and inventory baseline."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        login_id TEXT PRIMARY KEY,
        password TEXT NOT NULL,
        name TEXT NOT NULL,
        role TEXT NOT NULL,
        title TEXT NOT NULL,
        station TEXT NOT NULL,
        avatar TEXT NOT NULL
    )
    """)

    # Seed Default Verified Enterprise Roles
    default_users = [
        ("TECH-402", "worker123", "Marcus Vance", "worker", "Inbound Receiving Technician", "Receiving Bay #4", "MV"),
        ("SUP-108", "super123", "Elena Rostova", "supervisor", "Triage & Operations Lead", "Shift Control Center", "ER"),
        ("EXEC-001", "exec123", "David Chen", "executive", "VP of Supply Chain & CFO", "Executive Dashboard", "DC"),
    ]
    for u in default_users:
        cursor.execute("""
        INSERT OR IGNORE INTO users (login_id, password, name, role, title, station, avatar)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, u)

    # 2. Scanned Items & Triage Audit Log Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scanned_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        barcode TEXT NOT NULL,
        return_id TEXT,
        sku TEXT,
        product_name TEXT,
        grade TEXT,
        fault_code TEXT,
        is_hazardous INTEGER DEFAULT 0,
        best_channel TEXT,
        bin_assigned TEXT,
        nsv_amount REAL DEFAULT 0.0,
        operator_id TEXT NOT NULL,
        scan_timestamp TEXT NOT NULL,
        status TEXT NOT NULL,
        is_external_unregistered INTEGER DEFAULT 0
    )
    """)

    # 3. Inventory Master Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory_manifest (
        return_id TEXT PRIMARY KEY,
        sku TEXT,
        supplier_batch TEXT,
        grade TEXT,
        fault_code TEXT,
        product_name TEXT,
        supplier TEXT,
        cost_price REAL,
        retail_price REAL,
        status TEXT DEFAULT 'PENDING_SCAN'
    )
    """)

    # Populate inventory manifest from DataPipeline if table is empty
    cursor.execute("SELECT COUNT(*) FROM inventory_manifest")
    count = cursor.fetchone()[0]
    if count == 0:
        pipeline = DataPipeline()
        df = pipeline.get_unified_returns()
        for _, row in df.iterrows():
            cursor.execute("""
            INSERT OR IGNORE INTO inventory_manifest 
            (return_id, sku, supplier_batch, grade, fault_code, product_name, supplier, cost_price, retail_price, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING_SCAN')
            """, (
                str(row['return_id']),
                str(row['sku']),
                str(row['supplier_batch']),
                str(row['grade']),
                str(row['fault_code']),
                str(row['product_name']),
                str(row['supplier']),
                float(row['cost_price']),
                float(row['retail_price'])
            ))

    conn.commit()
    conn.close()

def verify_user(login_id: str, password: str) -> Optional[Dict[str, Any]]:
    """Verifies user credentials against database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE UPPER(login_id) = UPPER(?) AND password = ?", (login_id.strip(), password.strip()))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def get_user_by_id(login_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves user profile by login ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE UPPER(login_id) = UPPER(?)", (login_id.strip(),))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def record_scan_event(scan_data: Dict[str, Any]) -> int:
    """Inserts a completed physical scan and bin placement into the database."""
    conn = get_connection()
    cursor = conn.cursor()

    now_iso = datetime.now().isoformat()
    barcode = str(scan_data.get('barcode', '')).strip()
    return_id = scan_data.get('return_id')
    sku = scan_data.get('sku')
    product_name = scan_data.get('product_name')
    grade = scan_data.get('grade')
    fault_code = scan_data.get('fault_code')
    is_hazardous = 1 if scan_data.get('is_hazardous') else 0
    best_channel = scan_data.get('best_channel', 'PENDING')
    bin_assigned = scan_data.get('bin_assigned', 'Receiving Staging')
    nsv_amount = float(scan_data.get('nsv_amount', 0.0))
    operator_id = scan_data.get('operator_id', 'TECH-402')
    status = scan_data.get('status', 'CONFIRMED_BINNED')
    is_external = 1 if scan_data.get('is_external_unregistered') else 0

    cursor.execute("""
    INSERT INTO scanned_history 
    (barcode, return_id, sku, product_name, grade, fault_code, is_hazardous, best_channel, bin_assigned, nsv_amount, operator_id, scan_timestamp, status, is_external_unregistered)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        barcode, return_id, sku, product_name, grade, fault_code,
        is_hazardous, best_channel, bin_assigned, nsv_amount,
        operator_id, now_iso, status, is_external
    ))
    scan_id = cursor.lastrowid

    # If this matches an inventory unit, update its status
    if return_id:
        cursor.execute("UPDATE inventory_manifest SET status = 'TRIAGED_BINNED' WHERE return_id = ?", (return_id,))

    conn.commit()
    conn.close()
    return scan_id

def get_recent_scans(limit: int = 50) -> List[Dict[str, Any]]:
    """Returns the most recent confirmed physical scans."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM scanned_history ORDER BY id DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_scan_statistics() -> Dict[str, Any]:
    """Computes real-time warehouse statistics based on database records."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM scanned_history WHERE status = 'CONFIRMED_BINNED'")
    total_triaged = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(nsv_amount) FROM scanned_history WHERE status = 'CONFIRMED_BINNED'")
    total_nsv = cursor.fetchone()[0] or 0.0

    cursor.execute("SELECT COUNT(*) FROM scanned_history WHERE is_hazardous = 1")
    hazards_isolated = cursor.fetchone()[0]

    cursor.execute("SELECT best_channel, COUNT(*) as cnt FROM scanned_history GROUP BY best_channel")
    channel_counts = {r['best_channel']: r['cnt'] for r in cursor.fetchall() if r['best_channel']}

    conn.close()
    return {
        "total_triaged": total_triaged,
        "total_nsv": round(total_nsv, 2),
        "hazards_isolated": hazards_isolated,
        "channel_counts": channel_counts
    }

# Run migration on module import
init_db()
