# src/data_augmentation.py
"""Data augmentation for better model training - LIMITED AUGMENTATION"""

import pandas as pd
import numpy as np
from src.config import SKILLS_LIST, HIGH_VALUE_SKILLS
from src.utils import create_logger

logger = create_logger("augmentation")


class DataAugmentor:
    """Data augmentation for salary prediction - with limits"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.original_size = len(df)
    
    def balance_existing_levels(self, target_per_level: int = None) -> pd.DataFrame:
        """Balance ONLY existing levels - NO aggressive downsampling"""
        print(f"\n📊 Balancing existing levels...")
        
        # Calculate target based on data distribution
        class_sizes = self.df['level'].value_counts()
        median_size = class_sizes.median()
        
        # Target: keep at least 70% of data for large classes, don't oversample small ones
        if target_per_level is None:
            target_per_level = max(median_size, 300)  # At least 300, at most median
        
        balanced_dfs = []
        
        for level in self.df['level'].unique():
            level_df = self.df[self.df['level'] == level]
            current = len(level_df)
            
            if current > target_per_level * 2:
                # For very large classes, downsample to target_per_level * 1.5
                target = min(target_per_level * 2, int(current * 0.7))
                level_balanced = level_df.sample(n=target, random_state=42)
                print(f"   {level}: downsampled from {current} to {target} (kept {target/current*100:.0f}%)")
            else:
                # Keep all data
                level_balanced = level_df
                print(f"   {level}: kept all {current} samples")
            
            balanced_dfs.append(level_balanced)
        
        df_balanced = pd.concat(balanced_dfs, ignore_index=True)
        print(f"\n   Total after balancing: {len(df_balanced)} samples")
        
        return df_balanced
    
    def add_noise_to_salary(self, noise_level: float = 0.03, n_samples: int = 200) -> pd.DataFrame:
        """Add noise to salary values to create variations"""
        print(f"\n📊 Adding noise to salary (±{noise_level*100:.0f}%)...")
        
        if len(self.df) == 0:
            print("   No data to augment!")
            return pd.DataFrame()
        
        sample_size = min(n_samples, len(self.df))
        sample_df = self.df.sample(n=sample_size, random_state=42)
        
        augmented = []
        for _, row in sample_df.iterrows():
            new_row = row.to_dict()
            noise = np.random.normal(1, noise_level)
            new_salary = row['salary'] * noise
            new_row['salary'] = max(5, min(100, new_salary))
            augmented.append(new_row)
        
        df_augmented = pd.DataFrame(augmented)
        print(f"   Created {len(df_augmented)} augmented samples")
        
        return df_augmented
    
    def interpolate_between_samples(self, n_samples: int = 200) -> pd.DataFrame:
        """Create interpolated samples between existing ones"""
        print(f"\n📊 Creating interpolated samples...")
        
        if len(self.df) < 2:
            print("   Not enough data for interpolation!")
            return pd.DataFrame()
        
        # Fill NaN values before interpolation
        df_clean = self.df.copy()
        numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            df_clean[col] = df_clean[col].fillna(0)
        
        augmented = []
        skill_cols = [c for c in df_clean.columns if c.startswith('skill_')]
        
        for _ in range(min(n_samples, 500)):
            # Pick two random samples
            sample1 = df_clean.sample(1).iloc[0]
            sample2 = df_clean.sample(1).iloc[0]
            
            # Interpolation factor
            alpha = np.random.uniform(0.3, 0.7)
            
            new_row = {}
            
            # Numeric features
            for col in ['exp_years', 'salary', 'num_skills', 'num_high_value_skills']:
                val1 = float(sample1[col]) if pd.notna(sample1[col]) else 0
                val2 = float(sample2[col]) if pd.notna(sample2[col]) else 0
                new_row[col] = val1 * alpha + val2 * (1 - alpha)
            
            # Ensure integer for count features
            new_row['num_skills'] = max(1, int(round(new_row['num_skills'])))
            new_row['num_high_value_skills'] = max(0, int(round(new_row['num_high_value_skills'])))
            
            # Categorical features
            def safe_choice(v1, v2):
                if pd.isna(v1) and pd.isna(v2):
                    return 0
                if pd.isna(v1):
                    return int(v2) if v2 is not None else 0
                if pd.isna(v2):
                    return int(v1) if v1 is not None else 0
                return int(np.random.choice([v1, v2]))
            
            new_row['remote'] = safe_choice(sample1.get('remote', 0), sample2.get('remote', 0))
            new_row['english'] = safe_choice(sample1.get('english', 0), sample2.get('english', 0))
            new_row['is_big_city'] = safe_choice(sample1.get('is_big_city', 0), sample2.get('is_big_city', 0))
            new_row['is_big_company'] = safe_choice(sample1.get('is_big_company', 0), sample2.get('is_big_company', 0))
            
            # City and level (string)
            city1 = sample1.get('city', 'Other')
            city2 = sample2.get('city', 'Other')
            new_row['city'] = city1 if pd.notna(city1) else city2
            new_row['level'] = np.random.choice([sample1.get('level', 'Middle'), sample2.get('level', 'Middle')])
            
            # City multiplier
            cm1 = float(sample1.get('city_multiplier', 1.0)) if pd.notna(sample1.get('city_multiplier', 1.0)) else 1.0
            cm2 = float(sample2.get('city_multiplier', 1.0)) if pd.notna(sample2.get('city_multiplier', 1.0)) else 1.0
            new_row['city_multiplier'] = (cm1 + cm2) / 2
            
            # Derived features
            new_row['exp_squared'] = new_row['exp_years'] ** 2
            new_row['exp_skill_interaction'] = new_row['exp_years'] * new_row['num_skills']
            new_row['exp_high_value'] = new_row['exp_years'] * new_row['num_high_value_skills']
            new_row['remote_english'] = 1 if (new_row['remote'] == 1 and new_row['english'] == 1) else 0
            new_row['remote_big_city'] = 1 if (new_row['remote'] == 1 and new_row['is_big_city'] == 1) else 0
            new_row['salary_per_skill'] = new_row['salary'] / max(new_row['num_skills'], 1)
            
            # Skill flags (OR operation)
            for col in skill_cols:
                val1 = float(sample1[col]) if pd.notna(sample1[col]) else 0
                val2 = float(sample2[col]) if pd.notna(sample2[col]) else 0
                new_row[col] = 1 if (val1 == 1 or val2 == 1) else 0
            
            new_row['source'] = 'interpolated'
            
            augmented.append(new_row)
        
        df_augmented = pd.DataFrame(augmented)
        print(f"   Created {len(df_augmented)} interpolated samples")
        
        return df_augmented
    
    def augment_full_dataset(self, max_augmentation_ratio: float = 0.3) -> pd.DataFrame:
        """Run full data augmentation pipeline with limit"""
        print("\n" + "="*70)
        print("DATA AUGMENTATION PIPELINE (LIMITED)")
        print("="*70)
        print(f"Original size: {len(self.df)}")
        print(f"Max augmentation ratio: {max_augmentation_ratio*100:.0f}%")
        
        df_augmented = self.df.copy()
        original_size = len(df_augmented)
        
        # Maximum allowed augmented samples
        max_augmented = int(original_size * max_augmentation_ratio)
        print(f"Max augmented samples allowed: {max_augmented}")
        
        # 1. Balance existing levels (NO synthetic creation)
        df_augmented = self.balance_existing_levels(target_per_level=500)
        
        # 2. Add limited noise to salary
        noise_limit = min(150, max_augmented // 3)
        noise_samples = self.add_noise_to_salary(noise_level=0.03, n_samples=noise_limit)
        if len(noise_samples) > 0:
            df_augmented = pd.concat([df_augmented, noise_samples], ignore_index=True)
            print(f"   Added {len(noise_samples)} noise samples")
        
        # 3. Create limited interpolated samples
        interp_limit = min(150, max_augmented // 3)
        interp_samples = self.interpolate_between_samples(n_samples=interp_limit)
        if len(interp_samples) > 0:
            df_augmented = pd.concat([df_augmented, interp_samples], ignore_index=True)
            print(f"   Added {len(interp_samples)} interpolated samples")
        
        # 4. Ensure we don't exceed limit
        total_augmented = len(df_augmented) - original_size
        if total_augmented > max_augmented:
            print(f"   Warning: Exceeded limit! Removing excess...")
            excess = total_augmented - max_augmented
            # Remove from the end (most recently added)
            df_augmented = df_augmented.iloc[:-excess] if excess > 0 else df_augmented
        
        # 5. Remove duplicates
        before_dedup = len(df_augmented)
        df_augmented = df_augmented.drop_duplicates(subset=['exp_years', 'num_skills', 'city', 'level'], keep='first')
        print(f"   Removed {before_dedup - len(df_augmented)} duplicates")
        
        final_size = len(df_augmented)
        augmentation_ratio = (final_size - original_size) / original_size
        
        print(f"\n✅ Final size: {final_size}")
        print(f"   Augmentation ratio: {augmentation_ratio*100:.1f}% (target: ≤{max_augmentation_ratio*100:.0f}%)")
        
        return df_augmented


def augment_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Main function to augment dataset"""
    augmentor = DataAugmentor(df)
    return augmentor.augment_full_dataset()