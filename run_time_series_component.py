"""
run_time_series_component.py

Entry point for the "time series" analytics component. Given that
date_posted coverage/reliability doesn't support trend or forecasting
work on this dataset snapshot (see reports/reliability_audit_*.md for
the full evidence), this component was rescoped to:

  1. A field & date reliability audit — quantifies what can and can't
     be trusted, and why, so other stages don't build on broken fields.
  2. A market composition analysis — real market-intelligence findings
     using the fields that ARE well-populated at full dataset scale.

Usage:
    python run_time_series_component.py [path_to_cleaned_parquet]
"""

import sys
from src.analytics import reliability_audit, market_composition


def main():
    input_path = sys.argv[1] if len(sys.argv) > 1 else "data/processed/jobpulse_cleaned.parquet"

    audit_results = reliability_audit.run(input_path, output_dir="reports")
    print()
    market_results = market_composition.run(input_path, output_dir="data/analytics")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Reliability report: {audit_results['report_path']}")
    print(f"Trustworthy dated rows: {len(audit_results['trustworthy_rows'])}")
    print(f"Countries in market composition: {len(market_results['country_market_share'])}")


if __name__ == "__main__":
    main()
