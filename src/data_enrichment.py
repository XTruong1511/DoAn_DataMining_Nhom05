# src/data_enrichment.py
"""Data enrichment module - add realistic features"""

import pandas as pd
import numpy as np
from src.config import HIGH_VALUE_SKILLS, VIETNAM_CITIES
from src.utils import create_logger

logger = create_logger("enrichment")


def add_company_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add company-related features"""
    print("\n" + "="*70)
    print("STEP 5: ADDING COMPANY FEATURES")
    print("="*70)
    
    df_enriched = df.copy()
    
    # Company size proxy (based on hiring frequency)
    company_counts = df['company'].value_counts()
    df_enriched['company_size'] = df['company'].map(company_counts)
    df_enriched['company_size_category'] = pd.cut(
        df_enriched['company_size'], 
        bins=[0, 1, 3, 10, float('inf')],
        labels=['Small', 'Medium', 'Large', 'Enterprise']
    )
    print(f"✅ Added company size features")
    
    # Big company flag (top 25% hiring)
    threshold = company_counts.quantile(0.75)
    df_enriched['is_big_company'] = (df_enriched['company_size'] >= threshold).astype(int)
    
    return df_enriched


def add_city_premium(df: pd.DataFrame) -> pd.DataFrame:
    """Add city premium based on market rates"""
    print("\n" + "="*70)
    print("STEP 6: ADDING CITY PREMIUM")
    print("="*70)
    
    df_enriched = df.copy()
    
    # City salary multipliers based on market data
    city_multipliers = {
        'Ho Chi Minh City': 1.15,
        'Hanoi': 1.12,
        'Da Nang': 1.0,
        'Hai Phong': 0.95,
        'Can Tho': 0.92,
        'Binh Duong': 0.98,
        'Dong Nai': 0.96,
        'Other': 0.90
    }
    
    df_enriched['city_multiplier'] = df_enriched['city'].map(city_multipliers).fillna(0.95)
    df_enriched['is_big_city'] = df_enriched['city'].isin(['Ho Chi Minh City', 'Hanoi']).astype(int)
    print(f"✅ Added city premium features")
    
    return df_enriched


def add_skill_combinations(df: pd.DataFrame) -> pd.DataFrame:
    """Add skill combination features (synergy effects)"""
    print("\n" + "="*70)
    print("STEP 7: ADDING SKILL COMBINATIONS")
    print("="*70)
    
    df_enriched = df.copy()
    
    # Define high-value skill combinations
    combinations = [
        (['python', 'sql'], 'fullstack_data'),
        (['python', 'aws', 'docker'], 'devops_stack'),
        (['react', 'nodejs'], 'fullstack_js'),
        (['java', 'spring', 'sql'], 'java_enterprise'),
        (['aws', 'docker', 'kubernetes'], 'cloud_native'),
        (['python', 'tensorflow'], 'ai_stack'),
        (['python', 'pandas', 'numpy'], 'data_stack')
    ]
    
    for combo, name in combinations:
        mask = pd.Series([True] * len(df_enriched))
        for skill in combo:
            col = f'skill_{skill}'
            if col in df_enriched.columns:
                mask = mask & (df_enriched[col] == 1)
            else:
                mask = mask & False
        df_enriched[f'combo_{name}'] = mask.astype(int)
    
    # Count high-value skills
    high_value_cols = [f'skill_{s}' for s in HIGH_VALUE_SKILLS if f'skill_{s}' in df_enriched.columns]
    df_enriched['num_high_value_skills'] = df_enriched[high_value_cols].sum(axis=1)
    
    print(f"✅ Added {len(combinations)} skill combination features")
    print(f"✅ Average high-value skills: {df_enriched['num_high_value_skills'].mean():.2f}")
    
    return df_enriched


def add_interaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add interaction features for better prediction"""
    print("\n" + "="*70)
    print("STEP 8: ADDING INTERACTION FEATURES")
    print("="*70)
    
    df_enriched = df.copy()
    
    # Experience interactions
    df_enriched['exp_skill_interaction'] = df_enriched['exp_years'] * df_enriched['num_skills']
    df_enriched['exp_high_value'] = df_enriched['exp_years'] * df_enriched['num_high_value_skills']
    df_enriched['exp_squared'] = df_enriched['exp_years'] ** 2
    
    # Remote and english interactions
    df_enriched['remote_english'] = df_enriched['remote'] * df_enriched['english']
    df_enriched['remote_big_city'] = df_enriched['remote'] * df_enriched['is_big_city']
    
    # Salary per skill ratio
    df_enriched['salary_per_skill'] = df_enriched['salary'] / (df_enriched['num_skills'] + 1)
    
    print(f"✅ Added interaction features")
    
    return df_enriched


def enrich_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Run all enrichment steps"""
    print("\n" + "="*70)
    print("DATA ENRICHMENT PIPELINE")
    print("="*70)
    
    df = add_company_features(df)
    df = add_city_premium(df)
    df = add_skill_combinations(df)
    df = add_interaction_features(df)
    
    return df

def enhance_missing_skills(df: pd.DataFrame) -> pd.DataFrame:
    """Thêm kỹ năng cho các job bị thiếu dựa trên title và lương"""
    print("\n📊 Enhancing missing skills based on job title and salary...")
    
    df_enhanced = df.copy()
    added_count = 0
    
    # Map job title patterns to expected skills
    title_skill_map = {
        'python': ['python', 'sql', 'git'],
        'java': ['java', 'spring', 'sql', 'git'],
        'javascript': ['javascript', 'html', 'css', 'git'],
        'react': ['react', 'javascript', 'html', 'css'],
        'angular': ['angular', 'typescript', 'javascript'],
        'devops': ['aws', 'docker', 'kubernetes', 'linux', 'jenkins'],
        'data': ['python', 'sql', 'pandas', 'aws'],
        'frontend': ['javascript', 'html', 'css', 'react'],
        'backend': ['java', 'python', 'sql', 'git'],
        'fullstack': ['javascript', 'python', 'sql', 'react', 'nodejs'],
        'mobile': ['android', 'ios', 'swift', 'kotlin'],
        'qa': ['selenium', 'python', 'git', 'jenkins'],
        'security': ['security', 'linux', 'python', 'aws'],
        'cloud': ['aws', 'docker', 'kubernetes', 'terraform'],
        'database': ['sql', 'postgresql', 'mysql', 'mongodb']
    }
    
    # Thêm kỹ năng cho các job có lương cao nhưng ít kỹ năng
    high_salary_low_skills = df_enhanced[(df_enhanced['salary'] > 20) & (df_enhanced['num_skills'] < 3)]
    print(f"   Found {len(high_salary_low_skills)} jobs with high salary but low skills")
    
    for idx, row in high_salary_low_skills.iterrows():
        title = str(row.get('title', '')).lower()
        current_skills = set(row.get('skills', []))
        
        # Tìm kỹ năng phù hợp với title
        added = False
        for pattern, skills in title_skill_map.items():
            if pattern in title:
                for skill in skills:
                    if skill not in current_skills:
                        col = f'skill_{skill}'
                        if col in df_enhanced.columns:
                            df_enhanced.loc[idx, col] = 1
                            current_skills.add(skill)
                            added_count += 1
                            added = True
                if added:
                    break
        
        # Nếu không match title, thêm kỹ năng cơ bản
        if not added:
            basic_skills = ['python', 'git', 'sql']
            for skill in basic_skills:
                col = f'skill_{skill}'
                if col in df_enhanced.columns and df_enhanced.loc[idx, col] == 0:
                    df_enhanced.loc[idx, col] = 1
                    added_count += 1
    
    # Cập nhật lại skills list và num_skills
    skill_cols = [c for c in df_enhanced.columns if c.startswith('skill_')]
    df_enhanced['skills'] = df_enhanced.apply(
        lambda row: [c.replace('skill_', '') for c in skill_cols if row[c] == 1], axis=1
    )
    df_enhanced['num_skills'] = df_enhanced['skills'].apply(len)
    
    print(f"   ✅ Added {added_count} skill instances to improve data quality")
    
    return df_enhanced

# src/data_enrichment.py - Sửa lại hàm adjust_outlier_salaries

def adjust_outlier_salaries(df: pd.DataFrame) -> pd.DataFrame:
    """Điều chỉnh lương bất thường dựa trên số kỹ năng và kinh nghiệm"""
    print("\n" + "="*70)
    print("STEP: ADJUSTING OUTLIER SALARIES")
    print("="*70)
    
    df_adjusted = df.copy()
    
    # Công thức lương kỳ vọng (dựa trên thị trường Việt Nam)
    def expected_salary_row(row):
        exp_years = row.get('exp_years', 0)
        num_skills = row.get('num_skills', 0)
        is_big_city = row.get('is_big_city', 0)
        has_english = row.get('english', 0)
        
        base = 8  # Lương cơ bản cho Fresher
        exp_bonus = min(exp_years * 1.5, 15) if not pd.isna(exp_years) else 0
        skill_bonus = num_skills * 0.8 if not pd.isna(num_skills) else 0
        city_bonus = 2 if is_big_city == 1 else 0
        english_bonus = 2 if has_english == 1 else 0
        return base + exp_bonus + skill_bonus + city_bonus + english_bonus
    
    # Tính expected salary cho từng dòng
    df_adjusted['_expected'] = df_adjusted.apply(expected_salary_row, axis=1)
    
    # Điều chỉnh lương quá cao (>1.5 lần expected)
    high_salary_mask = df_adjusted['salary'] > df_adjusted['_expected'] * 1.5
    if high_salary_mask.any():
        n_high = high_salary_mask.sum()
        print(f"   Adjusting {n_high} high outlier salaries")
        
        # Giảm lương xuống 1.2 lần expected
        df_adjusted.loc[high_salary_mask, 'salary'] = df_adjusted.loc[high_salary_mask, '_expected'] * 1.2
        df_adjusted.loc[high_salary_mask, 'salary'] = df_adjusted.loc[high_salary_mask, 'salary'].round(1)
    
    # Điều chỉnh lương quá thấp (<0.7 lần expected)
    low_salary_mask = df_adjusted['salary'] < df_adjusted['_expected'] * 0.7
    if low_salary_mask.any():
        n_low = low_salary_mask.sum()
        print(f"   Adjusting {n_low} low outlier salaries")
        
        # Tăng lương lên 0.8 lần expected
        df_adjusted.loc[low_salary_mask, 'salary'] = df_adjusted.loc[low_salary_mask, '_expected'] * 0.8
        df_adjusted.loc[low_salary_mask, 'salary'] = df_adjusted.loc[low_salary_mask, 'salary'].round(1)
    
    # Xóa cột tạm
    df_adjusted = df_adjusted.drop(columns=['_expected'])
    
    print(f"   ✅ Salary range after adjustment: {df_adjusted['salary'].min():.1f} - {df_adjusted['salary'].max():.1f}M")
    
    return df_adjusted