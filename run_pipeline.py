# run_pipeline.py
"""Complete data pipeline with augmentation"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import ENRICHED_PATH, BALANCED_PATH, DATA_DIR
from src.data_preprocessing import load_raw_data, merge_datasets, filter_it_jobs, clean_data
from src.data_enrichment import adjust_outlier_salaries, enhance_missing_skills, enrich_dataset
from src.data_balancing import balance_dataset
from src.data_augmentation import augment_dataset
from src.utils import create_logger

logger = create_logger("pipeline")

# Tạo thư mục augmented
AUGMENTED_PATH = DATA_DIR / "augmented" / "augmented_dataset.csv"
AUGMENTED_PATH.parent.mkdir(parents=True, exist_ok=True)


def run_pipeline():
    """Run complete data pipeline"""
    print("="*70)
    print("COMPLETE DATA PIPELINE - IT JOB MARKET ANALYSIS")
    print("="*70)
    
    # ============================================================
    # STEP 1-4: LOAD, MERGE, FILTER, CLEAN
    # ============================================================
    df_cv, df_dev = load_raw_data()
    df_merged = merge_datasets(df_cv, df_dev)
    df_it = filter_it_jobs(df_merged)
    df_cleaned = clean_data(df_it)
    
    print(f"\n✅ After cleaning: {len(df_cleaned)} rows, {len(df_cleaned.columns)} columns")
    
    # ============================================================
    # STEP 5-8: ENRICH DATA
    # ============================================================
    df_enriched = enrich_dataset(df_cleaned)
    df_enriched.to_csv(ENRICHED_PATH, index=False)
    print(f"\n✅ Enriched data saved to {ENRICHED_PATH}")
    
    # ============================================================
    # STEP 9-11: BALANCE DATA
    # ============================================================
    df_balanced = balance_dataset(df_enriched)
    
    # ============================================================
    # STEP 12: ENHANCE MISSING SKILLS
    # ============================================================
    df_balanced = enhance_missing_skills(df_balanced)
    
    # ============================================================
    # STEP 13: ADJUST OUTLIER SALARIES
    # ============================================================
    df_balanced = adjust_outlier_salaries(df_balanced)
    
    # ============================================================
    # SAVE FINAL DATASET
    # ============================================================
    df_balanced.to_csv(BALANCED_PATH, index=False)
    print(f"\n✅ Final balanced data saved to {BALANCED_PATH}")
    
    # ============================================================
    # FINAL STATISTICS
    # ============================================================
    print("\n" + "="*70)
    print("FINAL DATASET STATISTICS")
    print("="*70)
    
    print(f"\n📊 Total samples: {len(df_balanced):,}")
    print(f"📊 Features: {len(df_balanced.columns)}")
    print(f"💰 Salary range: {df_balanced['salary'].min():.1f} - {df_balanced['salary'].max():.1f}M")
    print(f"💰 Average salary: {df_balanced['salary'].mean():.1f}M")
    print(f"📅 Average experience: {df_balanced['exp_years'].mean():.1f} years")
    print(f"🔧 Average skills: {df_balanced['num_skills'].mean():.2f}")
    
    print(f"\n📊 Class distribution:")
    for level in df_balanced['level'].value_counts().items():
        print(f"   {level[0]}: {level[1]} samples")
    
    print(f"\n📊 City distribution:")
    for city, count in df_balanced['city'].value_counts().head(10).items():
        print(f"   {city}: {count} samples")
    
    print(f"\n📊 Top 10 skills:")
    skill_cols = [c for c in df_balanced.columns if c.startswith('skill_')]
    skill_counts = df_balanced[skill_cols].sum().sort_values(ascending=False)
    for i, (skill, count) in enumerate(skill_counts.head(10).items()):
        skill_name = skill.replace('skill_', '')
        print(f"   {i+1}. {skill_name}: {int(count)} jobs ({count/len(df_balanced)*100:.1f}%)")
    
    return df_balanced


if __name__ == "__main__":
    df = run_pipeline()