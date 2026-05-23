"""
Vital Signs Monitoring Module

This module implements:
- Remote photoplethysmography (rPPG) for camera-based vital signs
- Heart rate detection from facial video
- Blood pressure estimation
- Real-time monitoring dashboard
"""

from .rppg import VitalSigns, rPPGMonitor

__all__ = ["VitalSigns", "rPPGMonitor"]
