"""
Stage 4: Feature Engineering & Analytics Aggregations

Orchestrates:
1. Feature engineering (salary conversion, remote flags, experience buckets)
2. Aggregation generation (Skill×Region, salary distributions, career pathways)
3. Export for BI consumption (JSON, CSV, Parquet formats)
"""

import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

import pandas as pd

from src.analytics import engineer_features, run_aggregations

logger = logging.getLogger(__name__)


class Stage4Orchestrator:
    """Orchestrates feature engineering and analytics aggregations"""
    
    def __init__(self):
        pass
    
    def run_pipeline(self, input_parquet: Path, output_features_parquet: Path,
                    output_analytics_dir: Path, report_path: Path) -> Dict[str, Any]:
        """
        Execute full Stage 4 pipeline.
        
        Args:
            input_parquet: NLP-enriched dataset from Stage 3
            output_features_parquet: Output path for feature-engineered dataset
            output_analytics_dir: Directory for aggregation exports
            report_path: Path to save comprehensive report
        
        Returns:
            Execution report
        """
        logger.info("\n" + "="*80)
        logger.info("STAGE 4: FEATURE ENGINEERING & ANALYTICS AGGREGATIONS")
        logger.info("="*80)
        
        logger.info("\n[STEP 1/5] Loading NLP-enriched dataset...")
        df = pd.read_parquet(input_parquet)
        input_count = len(df)
        logger.info(f"✓ Loaded {input_count:,} records")
        
        logger.info("\n[STEP 2/5] Engineering analytical features...")
        df = engineer_features(df)
        logger.info(f"✓ Engineered features (now {len(df.columns)} columns)")
        
        logger.info("\n[STEP 3/5] Generating aggregation tables...")
        aggregations = run_aggregations(df)
        logger.info(f"✓ Generated aggregations")
        
        logger.info("\n[STEP 4/5] Saving outputs...")
        
        # Save feature-engineered dataset
        df.to_parquet(output_features_parquet)
        logger.info(f"✓ Saved feature-engineered dataset: {output_features_parquet}")
        
        # Create analytics directory
        output_analytics_dir.mkdir(parents=True, exist_ok=True)
        
        # Save aggregations as JSON
        aggregation_outputs = {
            'skill_region_matrix.json': aggregations['skill_region_matrix'],
            'salary_distribution.json': aggregations['salary_distribution'],
            'remote_trends.json': aggregations['remote_trends'],
            'career_pathways.json': aggregations['career_pathways'],
            'skills_by_seniority.json': aggregations['skills_by_seniority'],
        }
        
        for filename, data in aggregation_outputs.items():
            filepath = output_analytics_dir / filename
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"✓ Saved: {filename}")
        
        # Export aggregations as CSV for BI tools
        self._export_skill_region_csv(
            aggregations['skill_region_matrix'],
            output_analytics_dir / 'skill_region_matrix.csv'
        )
        
        self._export_salary_csv(
            df, aggregations['salary_distribution'],
            output_analytics_dir / 'salary_by_segment.csv'
        )
        
        logger.info("\n[STEP 5/5] Generating comprehensive report...")
        
        # Generate report
        report = self._generate_report(
            input_count,
            len(df),
            df,
            aggregations
        )
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        logger.info(f"✓ Saved report: {report_path}")
        
        logger.info("\n" + "="*80)
        logger.info("STAGE 4 COMPLETE")
        logger.info(f"  Input Records: {input_count:,}")
        logger.info(f"  Output Records: {len(df):,}")
        logger.info(f"  New Features: 10")
        logger.info(f"  Aggregation Tables: {len(aggregation_outputs)}")
        logger.info("="*80 + "\n")
        
        return report
    
    def _export_skill_region_csv(self, matrix: Dict, output_path: Path):
        """Export skill×region matrix as CSV"""
        rows = []
        for skill, regions in matrix.items():
            for region, count in regions.items():
                rows.append({'skill': skill, 'region': region, 'count': count})
        
        df = pd.DataFrame(rows)
        df.to_csv(output_path, index=False)
        logger.info(f"✓ Exported: skill_region_matrix.csv ({len(df):,} rows)")
    
    def _export_salary_csv(self, df: pd.DataFrame, distributions: Dict, 
                          output_path: Path):
        """Export salary distributions as CSV"""
        rows = []
        
        # By country
        for country, stats in distributions['by_country'].items():
            salary_stats = stats.get('stats', {})
            rows.append({
                'segment_type': 'country',
                'segment': country,
                'total_jobs': stats.get('records_total', 0),
                'jobs_with_salary': stats.get('records_with_salary', 0),
                'salary_min_usd': salary_stats.get('min'),
                'salary_max_usd': salary_stats.get('max'),
                'salary_mean_usd': salary_stats.get('mean'),
                'salary_median_usd': salary_stats.get('median'),
            })
        
        # By seniority
        for seniority, stats in distributions['by_seniority'].items():
            salary_stats = stats.get('stats', {})
            rows.append({
                'segment_type': 'seniority',
                'segment': seniority,
                'total_jobs': stats.get('records_total', 0),
                'jobs_with_salary': stats.get('records_with_salary', 0),
                'salary_min_usd': salary_stats.get('min'),
                'salary_max_usd': salary_stats.get('max'),
                'salary_mean_usd': salary_stats.get('mean'),
                'salary_median_usd': salary_stats.get('median'),
            })
        
        df_export = pd.DataFrame(rows)
        df_export.to_csv(output_path, index=False)
        logger.info(f"✓ Exported: salary_by_segment.csv ({len(df_export):,} rows)")
    
    def _generate_report(self, input_count: int, output_count: int,
                        df: pd.DataFrame, aggregations: Dict) -> Dict[str, Any]:
        """Generate comprehensive Stage 4 report"""
        
        # Feature statistics
        feature_stats = {
            'remote_jobs': int(df['is_remote'].sum()),
            'remote_pct': round(100.0 * df['is_remote'].sum() / len(df), 2),
            'pan_african_jobs': int(df['is_pan_african'].sum()),
            'pan_african_pct': round(100.0 * df['is_pan_african'].sum() / len(df), 2),
            'jobs_with_salary': int(df['has_salary_data'].sum()),
            'jobs_with_salary_pct': round(100.0 * df['has_salary_data'].sum() / len(df), 2),
            'avg_skill_richness': float(df['skill_richness'].mean()),
            'jobs_requiring_cert': int(df['requires_certification'].sum()),
            'jobs_requiring_cert_pct': round(100.0 * df['requires_certification'].sum() / len(df), 2),
        }
        
        # Salary statistics
        salary_stats = {
            'overall_min_usd': float(df['salary_min_usd'].min()) if df['has_salary_data'].any() else None,
            'overall_max_usd': float(df['salary_max_usd'].max()) if df['has_salary_data'].any() else None,
            'overall_mean_usd': float(df[df['has_salary_data']]['salary_mid_usd'].mean()) if df['has_salary_data'].any() else None,
            'overall_median_usd': float(df[df['has_salary_data']]['salary_mid_usd'].median()) if df['has_salary_data'].any() else None,
        }
        
        # Seniority distribution
        seniority_dist = df['seniority_level'].value_counts().to_dict()
        
        # Experience bucket distribution
        exp_bucket_dist = df['experience_bucket'].value_counts().to_dict()
        
        report = {
            'stage': 'Stage 4: Feature Engineering & Analytics Aggregations',
            'timestamp': datetime.now().isoformat(),
            'input': {
                'records': input_count,
                'columns': 31,
            },
            'output': {
                'records': output_count,
                'columns': len(df.columns),
            },
            'features_engineered': {
                'new_columns': [
                    'salary_min_usd',
                    'salary_max_usd',
                    'salary_mid_usd',
                    'is_remote',
                    'is_pan_african',
                    'experience_bucket',
                    'seniority_order',
                    'is_high_salary',
                    'has_salary_data',
                    'skill_richness',
                    'requires_certification',
                ],
                'feature_statistics': feature_stats,
            },
            'salary_analysis': salary_stats,
            'seniority_distribution': seniority_dist,
            'experience_distribution': exp_bucket_dist,
            'aggregations_generated': {
                'skill_region_matrix': f"{len(aggregations['skill_region_matrix'])} skills",
                'salary_distribution': f"{len(aggregations['salary_distribution']['by_country'])} countries",
                'remote_trends': f"{len(aggregations['remote_trends']['by_country'])} countries",
                'career_pathways': f"{len(aggregations['career_pathways']['seniority_progression'])} levels",
                'skills_by_seniority': f"{len(aggregations['skills_by_seniority'])} levels",
            },
        }
        
        return report


def run_stage_4_analytics(
    input_parquet: Path,
    output_features_parquet: Path,
    output_analytics_dir: Path,
    report_path: Path
) -> Dict[str, Any]:
    """
    Execute Stage 4 pipeline.
    
    Entry point for stage execution.
    """
    orchestrator = Stage4Orchestrator()
    return orchestrator.run_pipeline(
        input_parquet,
        output_features_parquet,
        output_analytics_dir,
        report_path
    )
