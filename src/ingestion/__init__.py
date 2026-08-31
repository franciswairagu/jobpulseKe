"""Data ingestion module for JobPulse"""
from .loader import DataLoader, run_stage_1_ingestion

__all__ = ["DataLoader", "run_stage_1_ingestion"]
