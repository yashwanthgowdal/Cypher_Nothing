"""
Configuration & Operational Constants for Reverse Logistics Optimization Platform.
Defines cost structures, defect categories, SLA thresholds, and recovery constants.
"""

from dataclasses import dataclass

@dataclass(frozen=True)
class OperationalCosts:
    HANDLING_COST_PER_UNIT: float = 5.00        # Inbound inspection and barcode handling
    SHIPPING_FREIGHT_PER_UNIT: float = 10.00     # Outbound pallet/courier freight
    SCRAP_DISPOSAL_FEE: float = 2.00            # E-waste eco-disposal processing fee
    TECHNICIAN_HOURLY_RATE: float = 35.00       # Internal technician labor rate per hour
    DAILY_DEPRECIATION_RATE: float = 0.002      # 0.20% value loss per day post-dispatch
    DEFAULT_RTV_CREDIT_RATE: float = 0.80       # Standard 80% vendor credit under Master Agreement
    DEFAULT_LIQUIDATION_RATE: float = 0.18      # Bulk secondary auction wholesale recovery rate
    DEFAULT_SCRAP_MATERIAL_RATE: float = 0.03   # Raw metal/parts recycling recovery rate

# Defect and Safety Classifications
CRITICAL_SAFETY_DEFECTS = {
    "BATTERY_SWELLING",
    "OVERHEATING",
    "THERMAL_SHUTDOWN",
    "SMOKE_BURNT_COMPONENT",
    "FIRE_HAZARD"
}

FUNCTIONAL_DEFECTS = {
    "NO_POWER",
    "SLOW_DISCHARGE",
    "CONNECTOR_LOOSE",
    "FIRMWARE_LOCK",
    "AUDIO_DISTORTION",
    "TOUCH_UNRESPONSIVE",
    "DEAD_PIXELS",
    "BACKLIGHT_BLEED"
}

COSMETIC_DEFECTS = {
    "COSMETIC_BLEMISH",
    "MINOR_SCRATCH",
    "PACKAGING_DAMAGED",
    "SCREEN_CRACK",
    "CRACKED_GLASS"
}

# Quality & Warranty Anomaly Thresholds
MAX_PERMISSIBLE_SAFETY_DEFECT_RATE = 0.05       # > 5.0% triggers mandatory Zone D quarantine
MAX_PERMISSIBLE_CLUSTER_DEFECT_RATE = 0.35      # > 35% of any defect triggers upstream supplier audit
