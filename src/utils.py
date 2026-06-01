# src/utils.py
"""Utility functions"""

import re
import pandas as pd
import numpy as np
from typing import List, Optional
from pathlib import Path
import logging


def create_logger(name: str):
    """Create a logger instance"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = logs_dir / f"{name}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def parse_salary_from_min_max(min_val, max_val) -> Optional[float]:
    """Parse salary from min and max values (VND) to million VND"""
    try:
        # Convert to float
        if pd.isna(min_val) or min_val == 'nan' or min_val == '':
            min_sal = None
        else:
            min_sal = float(min_val)
        
        if pd.isna(max_val) or max_val == 'nan' or max_val == '':
            max_sal = None
        else:
            max_sal = float(max_val)
        
        # Both present
        if min_sal is not None and max_sal is not None and min_sal > 0 and max_sal > 0:
            return round((min_sal + max_sal) / 2 / 1_000_000, 1)
        
        # Only min
        if min_sal is not None and min_sal > 0:
            return round(min_sal / 1_000_000, 1)
        
        # Only max
        if max_sal is not None and max_sal > 0:
            return round(max_sal / 1_000_000, 1)
        
        return None
    except:
        return None


def parse_experience(exp_str: str) -> float:
    """Parse experience string to years"""
    if pd.isna(exp_str) or exp_str == '':
        return 2.0
    
    s = str(exp_str).lower().strip()
    
    level_map = {
        'fresher': 0, 'intern': 0, 'entry': 0.5,
        'junior': 1, 'middle': 3, 'senior': 5,
        'lead': 6, 'manager': 7, 'director': 8
    }
    
    for key, val in level_map.items():
        if key in s:
            return val
    
    numbers = re.findall(r'(\d+(?:\.\d+)?)', s)
    if len(numbers) >= 2:
        return (float(numbers[0]) + float(numbers[1])) / 2
    elif len(numbers) == 1:
        return float(numbers[0])
    
    return 2.0


def clean_city(city: str) -> str:
    """Clean and standardize city name"""
    if pd.isna(city) or city == '':
        return 'Other'
    
    s = str(city).lower().strip()
    
    city_map = {
        'hà nội': 'Hanoi', 'ha noi': 'Hanoi', 'hanoi': 'Hanoi',
        'hồ chí minh': 'Ho Chi Minh City', 'ho chi minh': 'Ho Chi Minh City',
        'hcm': 'Ho Chi Minh City', 'hcmc': 'Ho Chi Minh City', 'saigon': 'Ho Chi Minh City',
        'đà nẵng': 'Da Nang', 'da nang': 'Da Nang', 'danang': 'Da Nang',
        'hải phòng': 'Hai Phong', 'hai phong': 'Hai Phong',
        'cần thơ': 'Can Tho', 'can tho': 'Can Tho',
        'bình dương': 'Binh Duong', 'binh duong': 'Binh Duong',
        'đồng nai': 'Dong Nai', 'dong nai': 'Dong Nai'
    }
    
    for key, val in city_map.items():
        if key in s:
            return val
    
    return s.title() if s else 'Other'


def extract_skills(text: str, skill_list: List[str]) -> List[str]:
    """Extract skills from text"""
    if pd.isna(text) or text == '':
        return []
    
    text = str(text).lower()
    found = []
    for skill in skill_list:
        if re.search(r'\b' + re.escape(skill) + r'\b', text):
            found.append(skill)
    return list(set(found))


def detect_remote(text: str) -> bool:
    """Detect remote work from text"""
    if pd.isna(text):
        return False
    return bool(re.search(r'remote|work from home|wfh|hybrid', str(text).lower()))


def detect_english(text: str) -> bool:
    """Detect English requirement from text"""
    if pd.isna(text):
        return False
    return bool(re.search(r'english|ielts|toeic|toefl', str(text).lower()))


def fill_missing_salary(df: pd.DataFrame) -> pd.DataFrame:
    """Fill missing salary with median"""
    df_filled = df.copy()
    median_sal = df_filled['salary'].median()
    if pd.isna(median_sal):
        median_sal = 20
    df_filled['salary'] = df_filled['salary'].fillna(median_sal)
    return df_filled

def clean_city_advanced(city: str) -> str:
    """Clean and standardize city name - ADVANCED version"""
    if pd.isna(city) or city == '':
        return 'Other'
    
    s = str(city).lower().strip()
    
    # Remove salary ranges and other noise
    if 'vnd' in s or 'triệu' in s or 'million' in s:
        return 'Other'
    if re.match(r'^\d', s):  # starts with number
        return 'Other'
    
    # City mapping
    city_map = {
        'hà nội': 'Hanoi', 'ha noi': 'Hanoi', 'hanoi': 'Hanoi',
        'hồ chí minh': 'Ho Chi Minh City', 'ho chi minh': 'Ho Chi Minh City',
        'hcm': 'Ho Chi Minh City', 'hcmc': 'Ho Chi Minh City', 'saigon': 'Ho Chi Minh City',
        'đà nẵng': 'Da Nang', 'da nang': 'Da Nang', 'danang': 'Da Nang',
        'hải phòng': 'Hai Phong', 'hai phong': 'Hai Phong', 'haiphong': 'Hai Phong',
        'cần thơ': 'Can Tho', 'can tho': 'Can Tho',
        'bình dương': 'Binh Duong', 'binh duong': 'Binh Duong',
        'đồng nai': 'Dong Nai', 'dong nai': 'Dong Nai',
        'bắc ninh': 'Bac Ninh', 'bac ninh': 'Bac Ninh',
        'quảng ninh': 'Quang Ninh', 'quang ninh': 'Quang Ninh',
        'hưng yên': 'Hung Yen', 'hung yen': 'Hung Yen',
        'hải dương': 'Hai Duong', 'hai duong': 'Hai Duong',
        'vĩnh phúc': 'Vinh Phuc', 'vinh phuc': 'Vinh Phuc',
        'thái nguyên': 'Thai Nguyen', 'thai nguyen': 'Thai Nguyen',
        'nam định': 'Nam Dinh', 'nam dinh': 'Nam Dinh',
        'nghệ an': 'Nghe An', 'nghe an': 'Nghe An',
        'thanh hóa': 'Thanh Hoa', 'thanh hoa': 'Thanh Hoa',
        'quảng nam': 'Quang Nam', 'quang nam': 'Quang Nam',
        'bình định': 'Binh Dinh', 'binh dinh': 'Binh Dinh',
        'khánh hòa': 'Khanh Hoa', 'khanh hoa': 'Khanh Hoa',
        'lâm đồng': 'Lam Dong', 'lam dong': 'Lam Dong',
        'đắk lắk': 'Dak Lak', 'dak lak': 'Dak Lak',
        'gia lai': 'Gia Lai', 'gia lai': 'Gia Lai',
        'kon tum': 'Kon Tum', 'kon tum': 'Kon Tum',
        'bình thuận': 'Binh Thuan', 'binh thuan': 'Binh Thuan',
        'bà rịa - vũng tàu': 'Ba Ria Vung Tau', 'vung tau': 'Ba Ria Vung Tau',
        'long an': 'Long An', 'long an': 'Long An',
        'tiền giang': 'Tien Giang', 'tien giang': 'Tien Giang',
        'bến tre': 'Ben Tre', 'ben tre': 'Ben Tre',
        'trà vinh': 'Tra Vinh', 'tra vinh': 'Tra Vinh',
        'vĩnh long': 'Vinh Long', 'vinh long': 'Vinh Long',
        'đồng tháp': 'Dong Thap', 'dong thap': 'Dong Thap',
        'an giang': 'An Giang', 'an giang': 'An Giang',
        'kiên giang': 'Kien Giang', 'kien giang': 'Kien Giang',
        'cà mau': 'Ca Mau', 'ca mau': 'Ca Mau',
        'bạc liêu': 'Bac Lieu', 'bac lieu': 'Bac Lieu',
        'sóc trăng': 'Soc Trang', 'soc trang': 'Soc Trang',
        'hậu giang': 'Hau Giang', 'hau giang': 'Hau Giang'
    }
    
    for key, val in city_map.items():
        if key in s:
            return val
    
    # If not found in mapping, check if it's a valid Vietnamese province
    if len(s.split()) <= 3 and not any(c.isdigit() for c in s):
        return s.title()
    
    return 'Other'

def create_synthetic_fresher_data(n_samples: int = 500) -> pd.DataFrame:
    """Create synthetic fresher data for balancing"""
    np.random.seed(42)
    
    data = []
    for _ in range(n_samples):
        exp = np.random.uniform(0, 1)
        num_skills = np.random.randint(1, 5)
        base_salary = 6 + num_skills * 0.8
        salary = base_salary + np.random.normal(0, 1)
        
        data.append({
            'exp_years': exp,
            'salary': max(5, min(12, salary)),
            'num_skills': num_skills,
            'remote': np.random.choice([0, 1], p=[0.7, 0.3]),
            'english': np.random.choice([0, 1], p=[0.8, 0.2]),
            'city': np.random.choice(['Hanoi', 'Ho Chi Minh City', 'Da Nang']),
            'level': 'Fresher'
        })
    
    return pd.DataFrame(data)
