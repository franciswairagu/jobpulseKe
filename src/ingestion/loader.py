"""
Stage 1: Data Loading & Ingestion Schema Setup
Loads local CSV datasets and validates against standard schema
"""
import logging
import pandas as pd
import pyarrow.parquet as pq
import pyarrow as pa
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    RAW_DATA_DIR, PROCESSED_DATA_DIR, EXPECTED_COLUMNS,
    AFRICAN_COUNTRIES, MIN_JOB_DESCRIPTION_LENGTH, LOG_FORMAT, LOG_LEVEL
)

logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)
logger = logging.getLogger(__name__)


class DataLoader:
    """
    Loads and ingests local job data files
    """
    
    def __init__(self, raw_data_path: Optional[str] = None):
        """
        Initialize data loader
        
        Args:
            raw_data_path: Path to raw data CSV (defaults to master_africa_tech_jobs.csv)
        """
        if raw_data_path is None:
            raw_data_path = RAW_DATA_DIR / "master_africa_tech_jobs.csv"
        else:
            raw_data_path = Path(raw_data_path)
        
        self.raw_data_path = raw_data_path
        self.df = None
        self.schema_validation_report = {}
        
    def load_csv(self) -> pd.DataFrame:
        """Load CSV file into DataFrame"""
        logger.info(f"Loading data from {self.raw_data_path}")
        try:
            self.df = pd.read_csv(self.raw_data_path)
            logger.info(f"✓ Loaded {len(self.df)} rows, {len(self.df.columns)} columns")
            return self.df
        except Exception as e:
            logger.error(f"✗ Failed to load CSV: {e}")
            raise
    
    def validate_schema(self) -> dict:
        """
        Validate data against expected schema
        
        Returns:
            Dictionary with validation results
        """
        if self.df is None:
            raise ValueError("No data loaded. Call load_csv() first.")
        
        report = {
            "total_rows": len(self.df),
            "total_columns": len(self.df.columns),
            "expected_columns": list(EXPECTED_COLUMNS.keys()),
            "actual_columns": list(self.df.columns),
            "missing_columns": [],
            "extra_columns": [],
            "column_nulls": {},
        }
        
        # Check for missing columns
        for col in EXPECTED_COLUMNS.keys():
            if col not in self.df.columns:
                report["missing_columns"].append(col)
        
        # Check for extra columns
        for col in self.df.columns:
            if col not in EXPECTED_COLUMNS:
                report["extra_columns"].append(col)
        
        # Null value distribution
        for col in self.df.columns:
            null_count = self.df[col].isnull().sum()
            null_pct = (null_count / len(self.df)) * 100
            report["column_nulls"][col] = {
                "null_count": int(null_count),
                "null_percentage": round(null_pct, 2)
            }
        
        self.schema_validation_report = report
        logger.info(f"✓ Schema validation complete")
        return report
    
    def filter_rich_descriptions(self) -> pd.DataFrame:
        """
        Filter ingested records to keep:
        1. All records regardless of description length
        2. Fill missing descriptions with "No description"
        3. Relevant to African locations or remote-eligible roles
        
        Returns:
            Filtered DataFrame
        """
        if self.df is None:
            raise ValueError("No data loaded. Call load_csv() first.")
        
        initial_count = len(self.df)
        logger.info(f"Applying geographic and description fill filters...")
        
        # Step 1: Fill empty descriptions with "No description"
        self.df["job_description"] = self.df["job_description"].fillna("No description")
        self.df.loc[self.df["job_description"].astype(str).str.strip() == "", "job_description"] = "No description"
        desc_filled = (self.df["job_description"] == "No description").sum()
        logger.info(f"  Filled empty descriptions: {desc_filled} records")
        
        # Step 2: African country OR work_mode indicates remote/eligible
        def is_african_or_remote(row):
            country = str(row.get("country", "")).strip()
            work_mode = str(row.get("work_mode", "")).strip().lower()
            remote_scope = str(row.get("remote_scope", "")).strip().lower()
            
            # Check if African
            is_african = any(
                country.lower() == ac.lower() for ac in AFRICAN_COUNTRIES
            )
            
            # Check if remote/eligible
            is_remote_eligible = any(
                keyword in work_mode or keyword in remote_scope
                for keyword in ["remote", "hybrid", "work from home", "unknown"]
            )
            
            return is_african or is_remote_eligible
        
        self.df = self.df[self.df.apply(is_african_or_remote, axis=1)]
        after_geo_filter = len(self.df)
        logger.info(f"  After geographic filter (African/Remote): "
                   f"{after_geo_filter} rows ({initial_count - after_geo_filter} dropped)")
        
        logger.info(f"✓ Filtering complete: {initial_count} → {after_geo_filter} rows retained")
        return self.df
    
    def save_to_parquet(self, partition_by: Optional[str] = None) -> str:
        """
        Save ingested data to partitioned Parquet files
        
        Args:
            partition_by: Column name to partition by (e.g., 'country', 'source')
        
        Returns:
            Path to saved parquet file/directory
        """
        if self.df is None or len(self.df) == 0:
            raise ValueError("No data to save. Load and filter data first.")
        
        # Ensure processed directory exists
        PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        # Generate output path with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = PROCESSED_DATA_DIR / f"ingested_raw_{timestamp}.parquet"
        
        logger.info(f"Saving to parquet: {output_path}")
        
        # Convert to PyArrow table and write
        try:
            table = pa.Table.from_pandas(self.df)
            pq.write_table(table, str(output_path))
            logger.info(f"✓ Saved {len(self.df)} rows to {output_path}")
            return str(output_path)
        except Exception as e:
            logger.error(f"✗ Failed to save parquet: {e}")
            raise
    
    def get_ingestion_summary(self) -> dict:
        """Get comprehensive ingestion summary"""
        if self.df is None:
            return {"status": "No data loaded"}
        
        summary = {
            "total_records_ingested": len(self.df),
            "columns": len(self.df.columns),
            "column_list": list(self.df.columns),
            "null_counts": self.df.isnull().sum().to_dict(),
            "data_types": {col: str(dtype) for col, dtype in self.df.dtypes.items()},
            "schema_report": self.schema_validation_report,
            "sample_records": self.df.head(5).to_dict('records'),
        }
        return summary


def run_stage_1_ingestion(raw_data_path: Optional[str] = None) -> Tuple[pd.DataFrame, dict]:
    """
    Execute full Stage 1 pipeline:
    1. Load raw data
    2. Validate schema
    3. Fill empty descriptions with "No description"
    4. Filter to African/remote-eligible jobs (no description length requirement)
    5. Save to parquet
    
    Returns:
        Tuple of (processed DataFrame, ingestion summary)
    """
    logger.info("\n" + "="*80)
    logger.info("STAGE 1: DATA LOADING & INGESTION SCHEMA SETUP (REVISED)")
    logger.info("="*80 + "\n")
    
    loader = DataLoader(raw_data_path)
    
    # Step 1: Load
    logger.info("\n[STEP 1/4] Loading raw data...")
    loader.load_csv()
    
    # Step 2: Validate schema
    logger.info("\n[STEP 2/4] Validating schema...")
    schema_report = loader.validate_schema()
    logger.info(f"  Missing columns: {schema_report['missing_columns'] or 'None'}")
    logger.info(f"  Extra columns: {schema_report['extra_columns'][:3]}..." if len(schema_report['extra_columns']) > 3
                else f"  Extra columns: {schema_report['extra_columns']}")
    
    # Step 3: Filter (no description length requirement, fill empties)
    logger.info("\n[STEP 3/4] Filling empty descriptions & filtering geographic relevance...")
    filtered_df = loader.filter_rich_descriptions()
    
    # Step 4: Save
    logger.info("\n[STEP 4/4] Saving to Parquet...")
    parquet_path = loader.save_to_parquet()
    
    # Generate summary
    summary = loader.get_ingestion_summary()
    
    logger.info("\n" + "="*80)
    logger.info(f"STAGE 1 COMPLETE (REVISED)")
    logger.info(f"  Records ingested: {summary['total_records_ingested']:,}")
    logger.info(f"  Parquet saved: {parquet_path}")
    logger.info("="*80 + "\n")
    
    return filtered_df, summary


if __name__ == "__main__":
    df, summary = run_stage_1_ingestion()
    print("\nIngestion Summary:")
    print(f"  Total records: {summary['total_records_ingested']:,}")
    print(f"  Columns: {summary['columns']}")
