# src/data_preprocessing.py
"""Data preprocessing module - ENHANCED SKILL EXTRACTION"""

import pandas as pd
import numpy as np
import re
from difflib import get_close_matches
from src.config import IT_KEYWORDS, SKILLS_LIST
from src.skill_extractor import get_extractor
from src.utils import (
    parse_salary_from_min_max, parse_experience, clean_city, 
    detect_remote, detect_english, fill_missing_salary, create_logger
)

logger = create_logger("preprocessing")


def extract_skills_advanced(text: str, skill_list: list) -> list:
    """
    Extract skills from text using multiple strategies:
    1. Exact word matching
    2. Fuzzy matching for typos
    3. Bi-gram matching
    4. Common variations
    """
    if pd.isna(text) or text == '':
        return []
    
    text = str(text).lower()
    
    # Normalize text
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    
    found_skills = set()
    
    # Strategy 1: Exact word matching
    for skill in skill_list:
        skill_lower = skill.lower()
        if re.search(r'\b' + re.escape(skill_lower) + r'\b', text):
            found_skills.add(skill_lower)
    
    # Strategy 2: Common variations
    variations = {
        'pyspark': 'spark', 'scikit': 'scikit-learn', 'sklearn': 'scikit-learn',
        'tf': 'tensorflow', 'k8s': 'kubernetes', 'reactjs': 'react',
        'vuejs': 'vue', 'node': 'nodejs', 'postgres': 'postgresql',
        'mongo': 'mongodb', 'docker': 'docker', 'aws': 'aws',
        'azure': 'azure', 'gcp': 'gcp', 'jenkins': 'jenkins'
    }
    
    for variation, standard in variations.items():
        if re.search(r'\b' + re.escape(variation) + r'\b', text):
            found_skills.add(standard)
    
    # Strategy 3: Multi-word skills (bi-gram)
    words = text.split()
    bigrams = [' '.join(words[i:i+2]) for i in range(len(words)-1)]
    
    for skill in skill_list:
        if ' ' in skill:
            if skill.lower() in text or skill.lower() in bigrams:
                found_skills.add(skill.lower())
    
    # Strategy 4: Fuzzy matching for important skills
    important_skills = ['python', 'java', 'javascript', 'react', 'angular', 'docker', 'kubernetes', 'aws']
    for skill in important_skills:
        if skill in found_skills:
            continue
        # Check for close matches
        matches = get_close_matches(skill, text.split(), n=1, cutoff=0.8)
        if matches:
            found_skills.add(skill)
    
    return list(found_skills)


def enhance_skills_by_title(df: pd.DataFrame) -> pd.DataFrame:
    """Add missing skills based on job title"""
    print("\n📊 Enhancing skills based on job titles...")
    
    df_enhanced = df.copy()
    
    title_skill_map = {
        'python': ['python', 'sql', 'git'],
        'java': ['java', 'sql', 'spring', 'git'],
        'javascript': ['javascript', 'html', 'css', 'git'],
        'react': ['react', 'javascript', 'html', 'css', 'redux'],
        'angular': ['angular', 'typescript', 'javascript', 'html', 'css'],
        'devops': ['aws', 'docker', 'kubernetes', 'linux', 'jenkins', 'git'],
        'data scientist': ['python', 'pandas', 'numpy', 'sql', 'scikit-learn'],
        'data engineer': ['python', 'sql', 'spark', 'airflow', 'aws'],
        'frontend': ['javascript', 'html', 'css', 'react', 'git'],
        'backend': ['python', 'java', 'sql', 'git', 'docker'],
        'fullstack': ['javascript', 'python', 'sql', 'react', 'nodejs', 'git'],
        'mobile': ['swift', 'kotlin', 'android', 'ios', 'git'],
        'qa': ['selenium', 'pytest', 'junit', 'git'],
        'security': ['security', 'aws', 'linux', 'python']
    }
    
    added_count = 0
    for title_pattern, expected_skills in title_skill_map.items():
        mask = df_enhanced['title'].str.contains(title_pattern, case=False, na=False)
        
        for skill in expected_skills:
            col = f'skill_{skill}'
            if col in df_enhanced.columns:
                new_mask = mask & (df_enhanced[col] == 0)
                df_enhanced.loc[new_mask, col] = 1
                added_count += new_mask.sum()
    
    # Update num_skills
    skill_cols = [c for c in df_enhanced.columns if c.startswith('skill_')]
    df_enhanced['num_skills'] = df_enhanced[skill_cols].sum(axis=1)
    
    print(f"   Added {added_count} skill instances based on job titles")
    print(f"   New average skills: {df_enhanced['num_skills'].mean():.2f}")
    
    return df_enhanced


def load_raw_data() -> tuple:
    """Load raw data files"""
    print("\n" + "="*70)
    print("STEP 1: LOADING RAW DATA")
    print("="*70)
    
    from src.config import RAW_CV_PATH, RAW_DEV_PATH
    
    df_cv = pd.read_csv(RAW_CV_PATH)
    df_dev = pd.read_csv(RAW_DEV_PATH)
    
    print(f"✅ TopCV: {len(df_cv):,} rows, {len(df_cv.columns)} columns")
    print(f"✅ TopDev: {len(df_dev):,} rows, {len(df_dev.columns)} columns")
    
    return df_cv, df_dev


def merge_datasets(df_cv: pd.DataFrame, df_dev: pd.DataFrame) -> pd.DataFrame:
    """Merge TopCV and TopDev datasets"""
    print("\n" + "="*70)
    print("STEP 2: MERGING DATASETS")
    print("="*70)
    
    # Process TopCV
    df1 = pd.DataFrame()
    
    if 'job_title' in df_cv.columns:
        df1['title'] = df_cv['job_title'].fillna('').astype(str)
    elif 'title' in df_cv.columns:
        df1['title'] = df_cv['title'].fillna('').astype(str)
    else:
        df1['title'] = ''
    
    if 'company' in df_cv.columns:
        df1['company'] = df_cv['company'].fillna('').astype(str)
    else:
        df1['company'] = ''
    
    if 'location' in df_cv.columns:
        df1['city_raw'] = df_cv['location'].fillna('').astype(str)
    elif 'city' in df_cv.columns:
        df1['city_raw'] = df_cv['city'].fillna('').astype(str)
    else:
        df1['city_raw'] = ''
    
    if 'salary_min' in df_cv.columns:
        df1['salary_min'] = pd.to_numeric(df_cv['salary_min'], errors='coerce')
    else:
        df1['salary_min'] = np.nan
    
    if 'salarry_max' in df_cv.columns:
        df1['salary_max'] = pd.to_numeric(df_cv['salarry_max'], errors='coerce')
    else:
        df1['salary_max'] = np.nan
    
    if 'experience' in df_cv.columns:
        df1['exp_raw'] = df_cv['experience'].fillna('').astype(str)
    elif 'exp' in df_cv.columns:
        df1['exp_raw'] = df_cv['exp'].fillna('').astype(str)
    else:
        df1['exp_raw'] = ''
    
    desc = pd.Series([''] * len(df_cv))
    for col in ['job_description', 'description', 'qualifications', 'requirements']:
        if col in df_cv.columns:
            desc = desc + ' ' + df_cv[col].fillna('').astype(str)
    df1['description'] = desc.str.strip()
    
    if 'working form' in df_cv.columns:
        df1['working_form'] = df_cv['working form'].fillna('').astype(str)
    elif 'working_form' in df_cv.columns:
        df1['working_form'] = df_cv['working_form'].fillna('').astype(str)
    else:
        df1['working_form'] = ''
    
    df1['source'] = 'TopCV'
    
    # Process TopDev (similar)
    df2 = pd.DataFrame()
    
    if 'job_title' in df_dev.columns:
        df2['title'] = df_dev['job_title'].fillna('').astype(str)
    elif 'title' in df_dev.columns:
        df2['title'] = df_dev['title'].fillna('').astype(str)
    else:
        df2['title'] = ''
    
    if 'company' in df_dev.columns:
        df2['company'] = df_dev['company'].fillna('').astype(str)
    else:
        df2['company'] = ''
    
    if 'location' in df_dev.columns:
        df2['city_raw'] = df_dev['location'].fillna('').astype(str)
    elif 'city' in df_dev.columns:
        df2['city_raw'] = df_dev['city'].fillna('').astype(str)
    else:
        df2['city_raw'] = ''
    
    if 'salary_min' in df_dev.columns:
        df2['salary_min'] = pd.to_numeric(df_dev['salary_min'], errors='coerce')
    else:
        df2['salary_min'] = np.nan
    
    if 'salarry_max' in df_dev.columns:
        df2['salary_max'] = pd.to_numeric(df_dev['salarry_max'], errors='coerce')
    else:
        df2['salary_max'] = np.nan
    
    if 'experience' in df_dev.columns:
        df2['exp_raw'] = df_dev['experience'].fillna('').astype(str)
    elif 'exp' in df_dev.columns:
        df2['exp_raw'] = df_dev['exp'].fillna('').astype(str)
    else:
        df2['exp_raw'] = ''
    
    desc2 = pd.Series([''] * len(df_dev))
    for col in ['job_description', 'description', 'qualifications', 'requirements']:
        if col in df_dev.columns:
            desc2 = desc2 + ' ' + df_dev[col].fillna('').astype(str)
    df2['description'] = desc2.str.strip()
    
    if 'working form' in df_dev.columns:
        df2['working_form'] = df_dev['working form'].fillna('').astype(str)
    elif 'working_form' in df_dev.columns:
        df2['working_form'] = df_dev['working_form'].fillna('').astype(str)
    else:
        df2['working_form'] = ''
    
    df2['source'] = 'TopDev'
    
    df_merged = pd.concat([df1, df2], ignore_index=True)
    print(f"✅ Merged: {len(df_merged):,} rows")
    
    df_merged = df_merged.drop_duplicates(subset=['title', 'company'], keep='first')
    print(f"✅ After dedup: {len(df_merged):,} rows")
    
    return df_merged


def filter_it_jobs(df: pd.DataFrame) -> pd.DataFrame:
    """Filter only IT jobs"""
    print("\n" + "="*70)
    print("STEP 3: FILTERING IT JOBS")
    print("="*70)
    
    def is_it(row):
        text = f"{row['title']} {row['description']}".lower()
        return any(kw.lower() in text for kw in IT_KEYWORDS)
    
    df['is_it'] = df.apply(is_it, axis=1)
    df_it = df[df['is_it']].copy()
    df_it.drop('is_it', axis=1, inplace=True)
    
    print(f"✅ IT jobs: {len(df_it):,} ({len(df_it)/len(df)*100:.1f}%)")
    
    return df_it


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and preprocess data with strong deduplication"""
    print("\n" + "="*70)
    print("STEP 4: CLEANING DATA (WITH DEDUPLICATION)")
    print("="*70)
    
    df_clean = df.copy()
    
    # ============================================================
    # 1. CHECK AVAILABLE COLUMNS
    # ============================================================
    print(f"Available columns: {list(df_clean.columns)[:10]}...")
    
    # ============================================================
    # 2. REMOVE DUPLICATES
    # ============================================================
    before_dedup = len(df_clean)
    
    # Xóa trùng theo title + company (nếu có)
    dedup_cols = ['title', 'company']
    existing_cols = [c for c in dedup_cols if c in df_clean.columns]
    if existing_cols:
        df_clean = df_clean.drop_duplicates(subset=existing_cols, keep='first')
        print(f"✅ Removed {before_dedup - len(df_clean)} duplicates by {existing_cols}")
    
    # ============================================================
    # 3. PARSE SALARY
    # ============================================================
    if 'salary_min' in df_clean.columns and 'salary_max' in df_clean.columns:
        df_clean['salary'] = df_clean.apply(
            lambda row: parse_salary_from_min_max(row.get('salary_min'), row.get('salary_max')), 
            axis=1
        )
    elif 'salary_min' in df_clean.columns and 'salarry_max' in df_clean.columns:
        df_clean['salary'] = df_clean.apply(
            lambda row: parse_salary_from_min_max(row.get('salary_min'), row.get('salarry_max')), 
            axis=1
        )
    else:
        print("⚠️ No salary columns found!")
        df_clean['salary'] = np.nan
    
    valid_salary = df_clean['salary'].notna().sum()
    print(f"✅ Valid salary entries: {valid_salary:,} ({valid_salary/len(df_clean)*100:.1f}%)")
    
    # Fill missing salaries
    median_sal = df_clean['salary'].median()
    if pd.isna(median_sal):
        median_sal = 20
    df_clean['salary'] = df_clean['salary'].fillna(median_sal)
    
    # ============================================================
    # 4. PARSE EXPERIENCE
    # ============================================================
    if 'exp_raw' in df_clean.columns:
        df_clean['exp_years'] = df_clean['exp_raw'].apply(parse_experience)
    elif 'experience' in df_clean.columns:
        df_clean['exp_years'] = df_clean['experience'].apply(parse_experience)
    else:
        df_clean['exp_years'] = 2.0
    
    print(f"✅ Experience parsed")
    
    # ============================================================
    # 5. CLEAN CITY
    # ============================================================
    if 'city_raw' in df_clean.columns:
        df_clean['city'] = df_clean['city_raw'].apply(clean_city)
    elif 'city' in df_clean.columns:
        df_clean['city'] = df_clean['city'].apply(clean_city)
    else:
        df_clean['city'] = 'Other'
    
    print(f"✅ Cities cleaned: {df_clean['city'].nunique()} unique")
    
    # ============================================================
    # 6. SKILL EXTRACTION - CHỈ LẤY KỸ NĂNG IT ĐÚNG
    # ============================================================
    from src.skill_extractor import get_extractor
    extractor = get_extractor()
    
    # Định nghĩa valid IT skills
    VALID_IT_SKILLS = set([
        'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'php', 'ruby', 'go',
        'react', 'angular', 'vue', 'nextjs', 'nodejs', 'express', 'django', 'flask', 'spring',
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'gitlab', 'terraform',
        'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
        'pandas', 'numpy', 'tensorflow', 'pytorch', 'scikit-learn', 'spark',
        'android', 'ios', 'swift', 'kotlin', 'flutter', 'react native',
        'selenium', 'cypress', 'pytest', 'jest', 'postman',
        'git', 'linux', 'bash', 'jira', 'confluence'
    ])
    
    # Lấy description column
    desc_col = None
    for col in ['description', 'job_description']:
        if col in df_clean.columns:
            desc_col = col
            break
    
    if desc_col:
        def extract_valid_skills(text):
            if pd.isna(text):
                return []
            skills = extractor.extract(str(text))
            return [s for s in skills if s in VALID_IT_SKILLS]
        
        df_clean['skills'] = df_clean[desc_col].apply(extract_valid_skills)
        df_clean['num_skills'] = df_clean['skills'].apply(len)
        
        # Tạo skill flags
        for skill in VALID_IT_SKILLS:
            df_clean[f'skill_{skill}'] = df_clean['skills'].apply(lambda x: 1 if skill in x else 0)
        
        print(f"   ✅ Average skills per job: {df_clean['num_skills'].mean():.2f}")
        print(f"   ✅ Jobs with 5+ skills: {(df_clean['num_skills'] >= 5).sum()}")
    else:
        print("   ⚠️ No description column found!")
        df_clean['skills'] = [[] for _ in range(len(df_clean))]
        df_clean['num_skills'] = 0
    
    # ============================================================
    # 7. LOẠI BỎ JOBS CÓ SKILL RÁC
    # ============================================================
    def has_garbage_skills(skills):
        for s in skills:
            if len(s) <= 2 and s not in VALID_IT_SKILLS:
                return True
            if s in ['r', 'illustrator', 'photoshop', 'design']:
                return True
        return False
    
    before_clean = len(df_clean)
    df_clean = df_clean[~df_clean['skills'].apply(has_garbage_skills)]
    print(f"✅ Removed {before_clean - len(df_clean)} jobs with garbage skills")
    
    # ============================================================
    # 8. DETECT REMOTE AND ENGLISH
    # ============================================================
    if desc_col:
        df_clean['remote'] = df_clean[desc_col].apply(detect_remote).astype(int)
        df_clean['english'] = df_clean[desc_col].apply(detect_english).astype(int)
    else:
        df_clean['remote'] = 0
        df_clean['english'] = 0
    
    print(f"✅ Remote: {df_clean['remote'].mean()*100:.1f}%, English: {df_clean['english'].mean()*100:.1f}%")
    
    # ============================================================
    # 9. SENIORITY LEVEL
    # ============================================================
    df_clean['level'] = df_clean['exp_years'].apply(lambda x: 
        'Fresher' if x < 1 else 'Junior' if x < 3 else 'Middle' if x < 5 else 'Senior' if x < 8 else 'Expert')
    
    # ============================================================
    # 10. FILTER VALID SALARY
    # ============================================================
    df_clean = df_clean[(df_clean['salary'] >= 5) & (df_clean['salary'] <= 100)]
    print(f"✅ After salary filter: {len(df_clean):,} rows")
    
    return df_clean