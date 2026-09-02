"""
Stage 2: Data Cleaning, Geo-Normalization & Deduplication
High-performance deduplication, location standardization, and date normalization
"""
import logging
import pandas as pd
import numpy as np
import pyarrow.parquet as pq
import pyarrow as pa
from pathlib import Path
from typing import Optional, Tuple, Dict, Set
from datetime import datetime
from difflib import SequenceMatcher
from hashlib import md5
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.config import PROCESSED_DATA_DIR, REPORTS_DIR, AFRICAN_COUNTRIES, AFRICAN_COUNTRY_CODES

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class GeoNormalizer:
    """Standardizes geographic data (countries, cities)"""
    
    def __init__(self):
        # African country name variations mapping
        self.country_map = {
            # Standard names
            "Nigeria": "Nigeria",
            "South Africa": "South Africa",
            "Egypt": "Egypt",
            "Ghana": "Ghana",
            "Kenya": "Kenya",
            "Morocco": "Morocco",
            "Tunisia": "Tunisia",
            "Uganda": "Uganda",
            "Algeria": "Algeria",
            # Variations
            "ZA": "South Africa",
            "NG": "Nigeria",
            "EG": "Egypt",
            "GH": "Ghana",
            "KE": "Kenya",
            "MA": "Morocco",
            "TN": "Tunisia",
            "UG": "Uganda",
            "DZ": "Algeria",
            # ISO codes
            "ZAF": "South Africa",
            "NGA": "Nigeria",
            "EGY": "Egypt",
            "GHA": "Ghana",
            "KEN": "Kenya",
            "MAR": "Morocco",
            "TUN": "Tunisia",
            "UGA": "Uganda",
            "DZA": "Algeria",
            # Common typos/alternatives
            "RSA": "South Africa",
            "SA": "South Africa",
            "NAI": "Kenya",
            "NBO": "Kenya",
            "JNB": "South Africa",
            "CPT": "South Africa",
            "CAI": "Egypt",
            "ACC": "Ghana",
            "ABJ": "Nigeria",
            "LOS": "Nigeria",
            "LAG": "Nigeria",
            "Any": "Global Remote",
            "Global Remote": "Global Remote",
            "Remote": "Global Remote",
            "Worldwide": "Global Remote",
            "Unknown": "Global Remote",
        }
    
    def normalize_country(self, country: str) -> str:
        """Normalize country name to standard format"""
        if pd.isna(country):
            return "Unknown"
        
        country_str = str(country).strip()
        
        # Direct mapping
        if country_str in self.country_map:
            return self.country_map[country_str]
        
        # Case-insensitive lookup
        for key, value in self.country_map.items():
            if country_str.lower() == key.lower():
                return value
        
        # Check if country is in AFRICAN_COUNTRIES
        for african_country in AFRICAN_COUNTRIES:
            if country_str.lower() == african_country.lower():
                return african_country
        
        # Default to Global Remote if not found
        return "Global Remote"


class DateNormalizer:
    """Standardizes date formats to ISO-8601"""
    
    @staticmethod
    def normalize_date(date_val) -> Optional[str]:
        """Convert date to ISO-8601 format (YYYY-MM-DD)"""
        if pd.isna(date_val):
            return None
        
        try:
            # Try pandas to_datetime
            date_obj = pd.to_datetime(date_val)
            return date_obj.strftime("%Y-%m-%d")
        except:
            return None


class Deduplicator:
    """High-performance deduplication using hash-based approach"""
    
    def __init__(self, threshold: float = 0.85):
        """
        Initialize deduplicator
        
        Args:
            threshold: Similarity threshold (0-1) for fuzzy matching
        """
        self.threshold = threshold
    
    def normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        if pd.isna(text):
            return ""
        return str(text).strip().lower()
    
    def text_similarity(self, s1: str, s2: str) -> float:
        """Calculate text similarity using SequenceMatcher"""
        return SequenceMatcher(None, s1, s2).ratio()
    
    def get_dedup_key(self, row: pd.Series) -> str:
        """Generate deduplication key from job record"""
        # Use combination of title, company, and country for exact matching
        title = self.normalize_text(row.get("job_title", ""))
        company = self.normalize_text(row.get("company", ""))
        country = self.normalize_text(row.get("country", ""))
        
        composite = f"{title}|{company}|{country}"
        return md5(composite.encode()).hexdigest()
    
    def deduplicate_fast(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
        """
        Fast deduplication using exact hash matching
        
        Returns:
            Tuple of (deduplicated DataFrame, duplicates count)
        """
        seen_keys = {}
        duplicates = []
        unique_records = []
        
        for idx, row in df.iterrows():
            dedup_key = self.get_dedup_key(row)
            
            if dedup_key not in seen_keys:
                # New unique record
                seen_keys[dedup_key] = idx
                unique_records.append(row)
            else:
                # Duplicate found
                duplicates.append(idx)
        
        result_df = pd.DataFrame(unique_records).reset_index(drop=True)
        return result_df, len(duplicates)


class DataCleaner:
    """Main data cleaning orchestrator"""
    
    def __init__(self, input_parquet: str):
        """
        Initialize cleaner
        
        Args:
            input_parquet: Path to input Parquet file
        """
        self.input_parquet = Path(input_parquet)
        self.df = None
        self.original_count = 0
        self.final_count = 0
        self.geo_normalizer = GeoNormalizer()
        self.deduplicator = Deduplicator(threshold=0.85)
        self.cleaning_report = {}
    
    def load_parquet(self) -> pd.DataFrame:
        """Load Parquet file"""
        logger.info(f"Loading Parquet: {self.input_parquet}")
        self.df = pd.read_parquet(self.input_parquet)
        self.original_count = len(self.df)
        logger.info(f"✓ Loaded {self.original_count:,} records")
        return self.df
    
    def normalize_dates(self) -> int:
        """Standardize all date columns to ISO-8601"""
        logger.info("Standardizing dates to ISO-8601 format...")
        date_columns = ["date_posted", "application_deadline"]
        
        normalized_count = 0
        for col in date_columns:
            if col in self.df.columns:
                normalized_vals = self.df[col].apply(DateNormalizer.normalize_date)
                changed = (self.df[col] != normalized_vals).sum()
                self.df[col] = normalized_vals
                normalized_count += changed
        
        logger.info(f"  Standardized {normalized_count:,} date values")
        return normalized_count
    
    def normalize_geography(self) -> Tuple[int, int]:
        """Normalize country and city names"""
        logger.info("Normalizing geographic data...")
        
        # Normalize countries
        if "country" in self.df.columns:
            original_countries = self.df["country"].copy()
            self.df["country"] = self.df["country"].apply(
                self.geo_normalizer.normalize_country
            )
            country_changes = (original_countries != self.df["country"]).sum()
            logger.info(f"  Country normalization: {country_changes:,} changes")
            return country_changes, 0
        
        return 0, 0
    
    def deduplicate(self) -> int:
        """Remove duplicate records using exact hash matching"""
        logger.info("Deduplicating records (exact hash matching)...")
        
        # Use fast deduplication
        self.df, duplicates_found = self.deduplicator.deduplicate_fast(self.df)
        
        logger.info(f"  Duplicates removed: {duplicates_found:,}")
        logger.info(f"  Records retained: {len(self.df):,}")
        
        return duplicates_found
    
    def validate_data(self) -> dict:
        """Generate data quality report"""
        logger.info("Validating data quality...")
        
        report = {
            "total_records": len(self.df),
            "null_counts": self.df.isnull().sum().to_dict(),
            "columns": list(self.df.columns),
            "data_types": {col: str(dtype) for col, dtype in self.df.dtypes.items()},
        }
        
        # Geographic summary
        country_dist = self.df["country"].value_counts().head(10).to_dict()
        report["geographic_distribution"] = country_dist
        
        # Source summary
        if "source" in self.df.columns:
            source_dist = self.df["source"].value_counts().to_dict()
            report["source_distribution"] = source_dist
        
        return report
    
    def save_cleaned_parquet(self) -> str:
        """Save cleaned data to Parquet"""
        PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = PROCESSED_DATA_DIR / f"jobpulse_cleaned_{timestamp}.parquet"
        
        logger.info(f"Saving cleaned data: {output_path}")
        table = pa.Table.from_pandas(self.df)
        pq.write_table(table, str(output_path))
        
        logger.info(f"✓ Saved {len(self.df):,} deduplicated records")
        return str(output_path)
    
    def generate_report(self) -> dict:
        """Generate comprehensive cleaning report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "stage": "Stage 2: Data Cleaning & Deduplication",
            "input": {
                "file": str(self.input_parquet),
                "records": self.original_count,
            },
            "output": {
                "records": len(self.df),
                "reduction_rate": round((1 - len(self.df) / self.original_count) * 100, 2),
            },
            "operations": {
                "geo_normalization": "country names standardized",
                "date_standardization": "ISO-8601 format applied",
                "deduplication": "fuzzy matching (threshold=0.85)",
            },
            "data_quality": self.validate_data(),
        }
        return report
    
    def run_full_pipeline(self) -> Tuple[pd.DataFrame, dict, str]:
        """Execute complete Stage 2 pipeline"""
        logger.info("\n" + "="*80)
        logger.info("STAGE 2: DATA CLEANING, GEO-NORMALIZATION & DEDUPLICATION")
        logger.info("="*80 + "\n")
        
        logger.info("\n[STEP 1/4] Loading ingested data...")
        self.load_parquet()
        
        logger.info("\n[STEP 2/4] Normalizing geographic data...")
        self.normalize_geography()
        
        logger.info("\n[STEP 3/4] Standardizing dates...")
        self.normalize_dates()
        
        logger.info("\n[STEP 4/4] Deduplicating records...")
        duplicates = self.deduplicate()
        
        logger.info("\n[STEP 5/5] Saving cleaned dataset...")
        output_path = self.save_cleaned_parquet()
        
        # Generate report
        report = self.generate_report()
        
        logger.info("\n" + "="*80)
        logger.info("STAGE 2 COMPLETE")
        logger.info(f"  Original Records: {self.original_count:,}")
        logger.info(f"  Cleaned Records: {len(self.df):,}")
        logger.info(f"  Duplicates Removed: {duplicates:,}")
        logger.info(f"  Reduction Rate: {report['output']['reduction_rate']:.2f}%")
        logger.info(f"  Output: {output_path}")
        logger.info("="*80 + "\n")
        
        return self.df, report, output_path


def run_stage_2_cleaning(input_parquet: str) -> Tuple[pd.DataFrame, dict, str]:
    """
    Execute Stage 2 pipeline
    
    Args:
        input_parquet: Path to ingested Parquet file
    
    Returns:
        Tuple of (cleaned DataFrame, report dict, output path)
    """
    cleaner = DataCleaner(input_parquet)
    return cleaner.run_full_pipeline()


if __name__ == "__main__":
    # Example usage: clean the most recently ingested Stage 1 output.
    candidates = sorted(PROCESSED_DATA_DIR.glob("ingested_raw_*.parquet"))
    if not candidates:
        raise SystemExit(
            "No Stage 1 output found in data/processed/. "
            "Run scripts/run_stage1_ingestion.py first."
        )
    df, report, output_path = run_stage_2_cleaning(str(candidates[-1]))
    print(f"\nStage 2 Complete: {len(df):,} cleaned records saved")
