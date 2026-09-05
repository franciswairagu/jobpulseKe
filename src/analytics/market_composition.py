"""
market_composition.py — Pan-African Market Composition Analysis

Builds market-intelligence aggregations using only the fields that are
actually well-populated across the full dataset (country, work_mode,
tech_category — all <25% missing, most 0%), rather than the sparse fields
(salary, experience_required, date_posted) that can't support whole-dataset
analysis. Feeds Stage 6's "Pan-African market overview" and "Regional
skills intelligence matrix" deliverables.

Outputs:
  - data/analytics/tech_category_by_country_<ts>.csv
  - data/analytics/work_mode_by_category_<ts>.csv
  - data/analytics/country_market_share_<ts>.csv
"""

import pandas as pd
from datetime import datetime
from pathlib import Path


def load_data(path: str) -> pd.DataFrame:
    return pd.read_parquet(path)


def tech_category_by_country(df: pd.DataFrame) -> pd.DataFrame:
    """Which tech categories are in demand in which countries."""
    sub = df.dropna(subset=["tech_category", "country"])
    pivot = pd.crosstab(sub["country"], sub["tech_category"])
    pivot["total"] = pivot.sum(axis=1)
    return pivot.sort_values("total", ascending=False)


def work_mode_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """Remote vs onsite split within each tech category."""
    sub = df.dropna(subset=["tech_category", "work_mode"])
    pivot = pd.crosstab(sub["tech_category"], sub["work_mode"], normalize="index") * 100
    pivot = pivot.round(1)
    pivot["n"] = sub.groupby("tech_category").size()
    return pivot.sort_values("n", ascending=False)


def country_market_share(df: pd.DataFrame) -> pd.DataFrame:
    """Overall posting share by country — the top-line market overview number."""
    counts = df["country"].value_counts()
    share = (counts / counts.sum() * 100).round(1)
    return pd.DataFrame({"postings": counts, "market_share_pct": share})


def run(input_path: str, output_dir: str = "data/analytics"):
    print("=" * 80)
    print("MARKET COMPOSITION ANALYSIS")
    print("=" * 80)

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("\n[STEP 1/4] Loading data...")
    df = load_data(input_path)
    print(f"✓ Loaded {len(df)} rows")

    print("\n[STEP 2/4] Building tech_category × country matrix...")
    tc_country = tech_category_by_country(df)
    p1 = out_dir / f"tech_category_by_country_{ts}.csv"
    tc_country.to_csv(p1)
    print(f"✓ Saved {p1} ({len(tc_country)} countries)")

    print("\n[STEP 3/4] Building work_mode × tech_category matrix...")
    wm_category = work_mode_by_category(df)
    p2 = out_dir / f"work_mode_by_category_{ts}.csv"
    wm_category.to_csv(p2)
    print(f"✓ Saved {p2} ({len(wm_category)} categories)")

    print("\n[STEP 4/4] Building country market share...")
    share = country_market_share(df)
    p3 = out_dir / f"country_market_share_{ts}.csv"
    share.to_csv(p3)
    print(f"✓ Saved {p3}")

    print("\n" + "=" * 80)
    print("MARKET COMPOSITION ANALYSIS COMPLETE")
    print("=" * 80)

    return {
        "tech_category_by_country": tc_country,
        "work_mode_by_category": wm_category,
        "country_market_share": share,
    }


if __name__ == "__main__":
    import sys
    input_path = sys.argv[1] if len(sys.argv) > 1 else "data/processed/jobpulse_cleaned.parquet"
    run(input_path)
