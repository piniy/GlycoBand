"""Leakage-safe splitting, controls, metrics, calibration, and OOD evaluation."""

from glycoband.evaluation.trend_split import assign_trend_splits, validate_trend_splits

__all__ = ["assign_trend_splits", "validate_trend_splits"]
