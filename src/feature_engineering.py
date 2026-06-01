# src/feature_engineering.py
"""Feature engineering for optimal model performance"""

import pandas as pd
import numpy as np
from sklearn.feature_selection import SelectKBest, f_regression, mutual_info_regression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from src.config import HIGH_VALUE_SKILLS
from src.utils import create_logger

logger = create_logger("features")


def select_best_features(X: pd.DataFrame, y: pd.Series, k: int = 30) -> list:
    """Select best features using mutual information and f-regression"""
    print("\n" + "="*70)
    print("STEP 12: FEATURE SELECTION")
    print("="*70)
    
    # Mutual information
    mi_selector = SelectKBest(score_func=mutual_info_regression, k=min(k, len(X.columns)))
    mi_selector.fit(X.fillna(0), y)
    
    # F-regression
    f_selector = SelectKBest(score_func=f_regression, k=min(k, len(X.columns)))
    f_selector.fit(X.fillna(0), y)
    
    # Combine scores
    mi_scores = pd.Series(mi_selector.scores_, index=X.columns)
    f_scores = pd.Series(f_selector.scores_, index=X.columns)
    
    # Normalize scores
    mi_norm = (mi_scores - mi_scores.min()) / (mi_scores.max() - mi_scores.min())
    f_norm = (f_scores - f_scores.min()) / (f_scores.max() - f_scores.min())
    
    # Combined score
    combined_score = mi_norm * 0.6 + f_norm * 0.4
    best_features = combined_score.nlargest(k).index.tolist()
    
    print(f"✅ Selected {len(best_features)} best features")
    print("\nTop 15 features:")
    for i, (feature, score) in enumerate(combined_score.nlargest(15).items()):
        print(f"   {i+1:2d}. {feature}: {score:.4f}")
    
    return best_features


def get_feature_columns() -> list:
    """Get all potential feature columns"""
    return [
        # Experience features
        'exp_years', 'exp_squared', 'exp_skill_interaction', 'exp_high_value',
        
        # Skill features
        'num_skills', 'num_high_value_skills', 'salary_per_skill',
        
        # Work condition features
        'remote', 'english', 'remote_english', 'remote_big_city',
        
        # Location features
        'is_big_city', 'city_multiplier', 'is_big_company',
        
        # Skill flags (top skills)
        'skill_python', 'skill_java', 'skill_javascript', 'skill_react',
        'skill_aws', 'skill_docker', 'skill_kubernetes', 'skill_sql',
        'skill_devops', 'skill_tensorflow', 'skill_pytorch', 'skill_git',
        
        # Skill combinations
        'combo_fullstack_data', 'combo_devops_stack', 'combo_fullstack_js',
        'combo_java_enterprise', 'combo_cloud_native', 'combo_ai_stack', 'combo_data_stack'
    ]


def prepare_features(df: pd.DataFrame) -> tuple:
    """Prepare features for model training"""
    print("\n" + "="*70)
    print("STEP 13: PREPARING FEATURES")
    print("="*70)
    
    # Get feature columns
    feature_cols = get_feature_columns()
    available_cols = [col for col in feature_cols if col in df.columns]
    
    print(f"✅ Available features: {len(available_cols)}")
    
    X = df[available_cols].fillna(0)
    y = df['salary']
    
    # Remove outliers
    lower = y.quantile(0.01)
    upper = y.quantile(0.98)
    mask = (y >= lower) & (y <= upper)
    X = X[mask]
    y = y[mask]
    
    print(f"✅ After outlier removal: {len(X)} samples")
    
    # Select best features
    # best_features = select_best_features(X, y, k=25)
    best_features = available_cols  # Use all for now
    
    X_selected = X[best_features]
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_selected)
    
    print(f"✅ Final feature set: {len(best_features)} features")
    
    return X_scaled, y, scaler, best_features