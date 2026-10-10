# 📦 Gadgetbay Autonomous Reverse Logistics & Triage Platform

An enterprise-grade, autonomous decision-support and optimization engine for e-commerce electronics returns. Solves multi-channel returns routing using **mathematically rigorous Net Salvage Value (NSV) optimization**, **pure-NumPy ensemble machine learning**, **statistical anomaly detection (Level 1 hazard quarantine)**, and **automated executive legal/RMA documentation**.

---

## 🏛️ System Architecture

```
cyper/
├── core/                           # Production Engine Core Package
│   ├── __init__.py                 # Core package exports
│   ├── config.py                   # Operational parameters & defect classifications
│   ├── data_pipeline.py            # Strict schema validation & referential joins
│   ├── ml_disposition.py           # Calibrated Decision Forest classifier (Zero DLL bloat)
│   ├── mathematical_engine.py      # Penny-accurate NSV calculation & constrained batch optimizer
│   ├── anomaly_sentinel.py         # Statistical process control, safety spike & warranty tracking
│   ├── decision_agent.py           # Strategic ReAct Reasoner & MSA legal dispute drafter
│   └── document_generator.py       # Executive ReportLab PDF dossier & RMA debit generator
├── data/                           # Validated Datasets
│   ├── generate_datasets.py        # Enterprise return volume & anomaly generator
│   ├── products.csv                # Product catalog & wholesale/retail pricing
│   ├── returns.csv                 # Inbound returns with condition grades & fault telemetry
│   ├── inventory.csv               # Warehouse stock-on-hand & zone locations
│   ├── refurb_specs.csv            # Refurb labor hours, parts costs & secondary estimates
│   └── vendor_terms.csv            # Master Service Agreement return windows & credit %
├── models/                         # Serialized Model Artifacts
│   ├── disposition_model.pkl       # Trained Decision Forest ensemble (98.25% validation accuracy)
│   └── model_metadata.json         # Performance metrics, class recalls & training telemetry
├── output/                         # Generated Executive Dossiers & PDFs
│   └── Gadgetbay_Manifest_HB-09.pdf# Production RMA debit note & quarantine certificate
├── tests/                          # Automated Unit & Integration Test Suite
│   ├── test_mathematical_engine.py # Exact economic formulas & capacity constraint tests
│   └── test_integration.py         # Data pipeline, ML inference & anomaly sentinel tests
├── main.py                         # Unified Production CLI Runner with Rich Dashboards
├── requirements.txt                # Production Python dependencies
└── README.md                       # Platform documentation & mathematical specifications
```

---

## 📐 Mathematical Formulation of Net Salvage Value (NSV)

In enterprise reverse logistics, routing decisions are governed by exact financial recovery economics:

Let:
- $C_p$: Wholesale acquisition cost
- $P_s$: Retail selling price
- $C_h$: Unit handling & triage fee ($\$5.00$)
- $C_f$: Outbound freight/pallet shipping fee ($\$10.00$)
- $C_{parts}$: Refurbishment spare parts expense
- $T_{labor}$: Technician labor hours ($W_{labor} = \$35.00/\text{hr}$)
- $t$: Elapsed days since dispatch
- $\delta(t)$: Holding time depreciation factor: $\delta(t) = \max(0.0, 1.0 - 0.002 \cdot t)$
- $\gamma_{rtv}$: Contractual vendor credit recovery percentage (e.g. $80\%$)

### Recovery Channels:

1. **Restock ($\text{Grade} = A$, Pristine)**:
   $$NSV_{\text{RESTOCK}} = (P_s \times 0.90 \times \delta(t)) - C_h$$

2. **Return to Vendor (RTV, Contractual Warranty Claim)**:
   $$\text{Eligible if } RTV_{allowed} = \text{True} \text{ and } t \le W_{rtv}$$
   - *Standard Defect*: $NSV_{\text{RTV}} = (C_p \times \gamma_{rtv}) - C_f - C_h$
   - *Critical Hazardous Defect (MSA Section 4.2)*: $NSV_{\text{RTV}} = (C_p \times 1.00) - C_h$ (100% manufacturer warranty indemnification, freight waived)
   - *Expired Window*: $NSV_{\text{RTV}} = -\infty$

3. **Refurbishment ($\text{Grade} \in \{B, C\}$)**:
   $$C_{refurb} = C_{parts} + (T_{labor} \times W_{labor})$$
   $$NSV_{\text{REFURB}} = (P_{resale\_est} \times \delta(t)) - C_{refurb} - C_h$$

4. **Wholesale Liquidation (Secondary Bulk Lot)**:
   $$NSV_{\text{LIQUIDATE}} = (C_p \times 0.18) - C_h$$

5. **Scrap / Eco-Recycle**:
   $$NSV_{\text{SCRAP}} = \max\left(0.0, (C_p \times 0.03) - C_{scrap}\right)$$

### Constrained Batch Optimization:
$$\max \sum_{i=1}^N NSV(i, \text{channel}_i)$$
$$\text{subject to } \sum_{i \in \text{REFURB}} T_{labor}(i) \le H_{\max} \quad \text{(Shift Labor Hour Limit)}$$

---

## 🚀 Quickstart & Usage

### 1. Installation
```bash
pip install -r requirements.txt
```

### 2. Run Default Triage (Benchmark Batch HB-09)
Executes end-to-end ML inference, mathematical optimization, anomaly sentinel scan, and generates executive PDF:
```bash
python main.py
```

### 3. Warehouse Fleet Overview
Displays all active warehouse batches, unit volumes, and real-time safety flags:
```bash
python main.py --overview
```

### 4. Inbound Scanner Simulation (Sub-5ms Real-Time Triage)
Simulates barcode scanning a specific unit serial:
```bash
python main.py --scan RET-HB09-101
```

### 5. Multi-Batch Sequential Fleet Triage
Runs automated triage across all batches in the warehouse:
```bash
python main.py --all-batches
```

### 6. Operational Labor Constraints
Simulate a shift with limited technician availability (e.g., maximum 5.0 labor hours):
```bash
python main.py --batch HB-09 --labor-cap 5.0
```

### 7. Retrain Machine Learning Model
Retrains the Decision Forest ensemble on fresh data and validates accuracy:
```bash
python main.py --train
```

---

## 🧪 Automated Testing
Run the complete unit and integration test suite:
```bash
python -m unittest discover tests
```
All 8 test suites validate schema referential integrity, penny-accurate financial math, resource constraints, and Level 1 hazard triggers.
