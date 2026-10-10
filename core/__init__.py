"""
Core Reverse Logistics & Returns Triage Package.
"""

from core.config import OperationalCosts
from core.data_pipeline import DataPipeline
from core.ml_disposition import DispositionModelPipeline
from core.mathematical_engine import calculate_unit_nsv, optimize_batch, calculate_baseline_comparison
from core.anomaly_sentinel import AnomalySentinel
from core.decision_agent import StrategicDecisionAgent
from core.document_generator import generate_batch_dossier_pdf

__all__ = [
    "OperationalCosts",
    "DataPipeline",
    "DispositionModelPipeline",
    "calculate_unit_nsv",
    "optimize_batch",
    "calculate_baseline_comparison",
    "AnomalySentinel",
    "StrategicDecisionAgent",
    "generate_batch_dossier_pdf"
]
