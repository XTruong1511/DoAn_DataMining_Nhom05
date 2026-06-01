# src/data_balancing.py
"""Data balancing module - handle imbalanced data"""

import pandas as pd
import numpy as np
from sklearn.utils import resample
from src.utils import create_logger

logger = create_logger("balancing")


def create_synthetic_data_for_level(level: str, n_samples: int) -> pd.DataFrame:
    """Create synthetic data for a specific seniority level"""
    np.random.seed(42)
    
    if level == 'Fresher':
        exp_range = (0, 1)
        salary_range = (6, 12)
        skill_range = (1, 4)
    elif level == 'Junior':
        exp_range = (1, 3)
        salary_range = (10, 18)
        skill_range = (3, 6)
    elif level == 'Middle':
        exp_range = (3, 5)
        salary_range = (16, 25)
        skill_range = (5, 8)
    elif level == 'Senior':
        exp_range = (5, 8)
        salary_range = (25, 40)
        skill_range = (6, 10)
    else:  # Expert
        exp_range = (8, 15)
        salary_range = (35, 60)
        skill_range = (8, 12)
    
    data = []
    for _ in range(n_samples):
        exp = np.random.uniform(exp_range[0], exp_range[1])
        salary = np.random.uniform(salary_range[0], salary_range[1])
        num_skills = np.random.randint(skill_range[0], skill_range[1])
        
        # Random skills
        skills = {
            'python': np.random.choice([0, 1], p=[0.7, 0.3]),
            'java': np.random.choice([0, 1], p=[0.8, 0.2]),
            'javascript': np.random.choice([0, 1], p=[0.7, 0.3]),
            'react': np.random.choice([0, 1], p=[0.8, 0.2]),
            'aws': np.random.choice([0, 1], p=[0.8, 0.2]),
            'docker': np.random.choice([0, 1], p=[0.7, 0.3]),
            'sql': np.random.choice([0, 1], p=[0.6, 0.4]),
            'kubernetes': np.random.choice([0, 1], p=[0.9, 0.1]),
            'devops': np.random.choice([0, 1], p=[0.9, 0.1])
        }
        
        row = {
            'exp_years': exp,
            'salary': salary,
            'num_skills': num_skills,
            'num_high_value_skills': sum([skills[s] for s in ['python', 'aws', 'docker', 'kubernetes', 'devops']]),
            'remote': np.random.choice([0, 1], p=[0.7, 0.3]),
            'english': np.random.choice([0, 1], p=[0.8, 0.2]),
            'city': np.random.choice(['Hanoi', 'Ho Chi Minh City', 'Da Nang', 'Hai Phong']),
            'level': level,
            'source': 'synthetic'
        }
        
        # Add skill flags
        for skill, val in skills.items():
            row[f'skill_{skill}'] = val
        
        data.append(row)
    
    return pd.DataFrame(data)


def balance_by_seniority(df: pd.DataFrame) -> pd.DataFrame:
    """Balance dataset - SMART BALANCING without losing data"""
    print("\n" + "="*70)
    print("STEP 9: BALANCING BY SENIORITY LEVEL (SMART)")
    print("="*70)
    
    print("Current distribution:")
    for level in ['Fresher', 'Junior', 'Middle', 'Senior', 'Expert']:
        count = len(df[df['level'] == level]) if 'level' in df.columns else 0
        print(f"  {level}: {count} samples")
    
    # Merge Expert into Senior
    df.loc[df['level'] == 'Expert', 'level'] = 'Senior'
    print("\n✅ Merged 'Expert' into 'Senior'")
    
    # Drop Fresher if too few (2 samples is too few to be meaningful)
    if len(df[df['level'] == 'Fresher']) < 10:
        df = df[df['level'] != 'Fresher']
        print("✅ Dropped 'Fresher' (too few real samples)")
    
    # SMART BALANCING: Don't downsample too aggressively
    # Target: Keep at most 2x of the median class size
    class_sizes = df['level'].value_counts()
    median_size = class_sizes.median()
    max_target = min(median_size * 2, 2000)  # Cap at 2000
    
    print(f"\n📊 Smart balancing - target per class: ~{max_target}")
    
    balanced_dfs = []
    for level in df['level'].unique():
        level_df = df[df['level'] == level]
        current = len(level_df)
        
        if current > max_target:
            # Downsample but keep at least 70% of data
            target = max(max_target, int(current * 0.7))
            level_balanced = level_df.sample(n=target, random_state=42)
            print(f"   {level}: downsampled from {current} to {target} (kept {target/current*100:.0f}%)")
        else:
            # Keep all data
            level_balanced = level_df
            print(f"   {level}: kept all {current} samples")
        
        balanced_dfs.append(level_balanced)
    
    df_balanced = pd.concat(balanced_dfs, ignore_index=True)
    print(f"\n✅ Total after balancing: {len(df_balanced):,} samples")
    
    return df_balanced


def balance_by_salary_range(df: pd.DataFrame) -> pd.DataFrame:
    """Balance dataset by salary range"""
    print("\n" + "="*70)
    print("STEP 10: BALANCING BY SALARY RANGE")
    print("="*70)
    
    # Define salary brackets
    df['salary_bracket'] = pd.cut(df['salary'], bins=[0, 10, 15, 20, 30, 50, 100], 
                                   labels=['<10M', '10-15M', '15-20M', '20-30M', '30-50M', '>50M'])
    
    print(f"Current distribution:")
    bracket_counts = df['salary_bracket'].value_counts()
    for bracket in ['<10M', '10-15M', '15-20M', '20-30M', '30-50M', '>50M']:
        count = bracket_counts.get(bracket, 0)
        print(f"  {bracket}: {count} samples")
    
    target_per_bracket = 300
    balanced_dfs = []
    
    for bracket in ['<10M', '10-15M', '15-20M', '20-30M', '30-50M', '>50M']:
        bracket_df = df[df['salary_bracket'] == bracket]
        current_count = len(bracket_df)
        
        if current_count > target_per_bracket:
            bracket_balanced = resample(bracket_df, replace=False, n_samples=target_per_bracket, random_state=42)
        elif current_count > 0:
            bracket_balanced = resample(bracket_df, replace=True, n_samples=target_per_bracket, random_state=42)
        else:
            # Create synthetic data for this salary range
            # Find matching level
            level_map = {
                '<10M': 'Fresher',
                '10-15M': 'Junior',
                '15-20M': 'Junior',
                '20-30M': 'Middle',
                '30-50M': 'Senior',
                '>50M': 'Expert'
            }
            level = level_map.get(bracket, 'Middle')
            bracket_balanced = create_synthetic_data_for_level(level, target_per_bracket)
            print(f"  Created {target_per_bracket} synthetic samples for {bracket}")
        
        balanced_dfs.append(bracket_balanced)
    
    df_balanced = pd.concat(balanced_dfs, ignore_index=True)
    df_balanced.drop('salary_bracket', axis=1, inplace=True)
    
    print(f"\n✅ After balancing: {len(df_balanced)} samples")
    
    return df_balanced


def balance_by_city(df: pd.DataFrame) -> pd.DataFrame:
    """Simple city balancing - ONLY keep top cities, NO downsampling"""
    print("\n" + "="*70)
    print("STEP 11: SIMPLE CITY FILTERING")
    print("="*70)
    
    # Get top 5 cities by count
    city_counts = df['city'].value_counts()
    top_cities = city_counts.head(5).index.tolist()
    
    print(f"Keeping only top cities: {top_cities}")
    print(f"Other cities will be grouped as 'Other'")
    
    # Group small cities into 'Other'
    df['city'] = df['city'].apply(lambda x: x if x in top_cities else 'Other')
    
    # Update is_big_city flag
    df['is_big_city'] = df['city'].isin(['Hanoi', 'Ho Chi Minh City']).astype(int)
    
    # No downsampling - keep all data
    print(f"\n✅ After grouping: {len(df)} samples, {df['city'].nunique()} cities")
    
    return df


def balance_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Run all balancing steps"""
    print("\n" + "="*70)
    print("DATA BALANCING PIPELINE")
    print("="*70)
    
    # If dataframe is empty, create from scratch
    if len(df) == 0:
        print("⚠️ No data found! Creating synthetic dataset from scratch...")
        dfs = []
        for level in ['Fresher', 'Junior', 'Middle', 'Senior', 'Expert']:
            dfs.append(create_synthetic_data_for_level(level, 400))
        df = pd.concat(dfs, ignore_index=True)
        print(f"✅ Created {len(df)} synthetic samples")
    
    df = balance_by_seniority(df)
    df = balance_by_salary_range(df)
    df = balance_by_city(df)
    
    return df