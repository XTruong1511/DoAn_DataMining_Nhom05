# src/model_training.py
"""Model training module"""

import pandas as pd
import numpy as np
import joblib
import json
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor

from src.config import MODEL_PATH, SCALER_PATH, FEATURES_PATH, RANDOM_SEED, TEST_SIZE, MODELS_DIR
from src.utils import create_logger

logger = create_logger("model_training")


def get_feature_columns(df: pd.DataFrame) -> list:
    """Get feature columns for training"""
    
    # Base features
    base_features = ['exp_years', 'num_skills', 'remote', 'english', 'is_big_city', 'city_multiplier', 'is_big_company']
    
    # Skill features
    skill_cols = [col for col in df.columns if col.startswith('skill_')]
    
    # Combination features
    combo_cols = [col for col in df.columns if col.startswith('combo_')]
    
    # Interaction features
    interaction_cols = ['exp_skill_interaction', 'exp_high_value', 'remote_english', 'remote_big_city', 'exp_squared']
    existing_interaction = [col for col in interaction_cols if col in df.columns]
    
    # All features
    feature_cols = base_features + skill_cols + combo_cols + existing_interaction
    feature_cols = [col for col in feature_cols if col in df.columns]
    
    return feature_cols


def prepare_data(df: pd.DataFrame):
    """Prepare data for training"""
    print("\n" + "="*70)
    print("PREPARING DATA FOR TRAINING")
    print("="*70)
    
    # Get feature columns
    feature_cols = get_feature_columns(df)
    print(f"✅ Features: {len(feature_cols)}")
    
    # Prepare X and y
    X = df[feature_cols].fillna(0)
    y = df['salary']
    
    # Remove outliers
    upper_bound = y.quantile(0.98)
    lower_bound = y.quantile(0.02)
    mask = (y >= lower_bound) & (y <= upper_bound)
    X = X[mask]
    y = y[mask]
    print(f"✅ After outlier removal: {len(X)} samples")
    
    # Log transform target
    y_log = np.log1p(y)
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_log, test_size=TEST_SIZE, random_state=RANDOM_SEED
    )
    
    # Scale
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    print(f"✅ Train: {len(X_train)}, Test: {len(X_test)}")
    
    return X_train_scaled, X_test_scaled, y_train, y_test, scaler, feature_cols, y


def train_linear_regression(X_train, y_train):
    """Train Linear Regression"""
    print("\n📊 Training Linear Regression (Baseline)...")
    
    model = LinearRegression()
    model.fit(X_train, y_train)
    return model


def train_random_forest(X_train, y_train):
    """Train Random Forest"""
    print("\n📊 Training Random Forest...")
    
    param_grid = {
        'n_estimators': [100, 200],
        'max_depth': [10, 15],
        'min_samples_split': [5, 10],
        'min_samples_leaf': [2, 4]
    }
    
    rf = RandomForestRegressor(random_state=RANDOM_SEED, n_jobs=-1)
    grid_search = GridSearchCV(rf, param_grid, cv=5, scoring='r2', n_jobs=-1, verbose=0)
    grid_search.fit(X_train, y_train)
    
    print(f"   Best params: {grid_search.best_params_}")
    return grid_search.best_estimator_


def train_xgboost(X_train, y_train):
    """Train XGBoost"""
    print("\n📊 Training XGBoost...")
    
    model = XGBRegressor(
        n_estimators=200, max_depth=7, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8,
        random_state=RANDOM_SEED, n_jobs=-1, verbosity=0
    )
    model.fit(X_train, y_train)
    return model


def train_lightgbm(X_train, y_train):
    """Train LightGBM"""
    print("\n📊 Training LightGBM...")
    
    model = LGBMRegressor(
        n_estimators=200, max_depth=10, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8,
        random_state=RANDOM_SEED, n_jobs=-1, verbose=-1
    )
    model.fit(X_train, y_train)
    return model


def train_gradient_boosting(X_train, y_train):
    """Train Gradient Boosting"""
    print("\n📊 Training Gradient Boosting...")
    
    model = GradientBoostingRegressor(
        n_estimators=200, max_depth=5, learning_rate=0.05,
        subsample=0.8, random_state=RANDOM_SEED
    )
    model.fit(X_train, y_train)
    return model


def evaluate_model(model, X_test, y_test, y_original):
    """Evaluate model"""
    y_pred_log = model.predict(X_test)
    y_pred = np.expm1(y_pred_log)
    y_true = np.expm1(y_test)
    
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    mape = np.mean(np.abs((y_true - y_pred) / (y_true + 0.01))) * 100
    
    return {'mae': round(mae, 2), 'rmse': round(rmse, 2), 'r2': round(r2, 4), 'mape': round(mape, 1)}


def train_and_save(df: pd.DataFrame):
    """Main training function"""
    print("\n" + "="*70)
    print("MODEL TRAINING PIPELINE")
    print("="*70)
    
    # Prepare data
    X_train, X_test, y_train, y_test, scaler, feature_cols, y_original = prepare_data(df)
    
    # Train models
    models = {
        'Linear Regression': train_linear_regression(X_train, y_train),
        'Random Forest': train_random_forest(X_train, y_train),
        'XGBoost': train_xgboost(X_train, y_train),
        'LightGBM': train_lightgbm(X_train, y_train),
        'Gradient Boosting': train_gradient_boosting(X_train, y_train)
    }
    
    # Evaluate
    print("\n" + "="*70)
    print("MODEL EVALUATION RESULTS")
    print("="*70)
    print(f"{'Model':<20} {'MAE':<10} {'RMSE':<10} {'R²':<10} {'MAPE':<10}")
    print("-"*60)
    
    results = {}
    best_model = None
    best_r2 = -np.inf
    
    for name, model in models.items():
        metrics = evaluate_model(model, X_test, y_test, y_original)
        results[name] = metrics
        print(f"{name:<20} {metrics['mae']:<10} {metrics['rmse']:<10} {metrics['r2']:<10} {metrics['mape']:<10}%")
        
        if metrics['r2'] > best_r2:
            best_r2 = metrics['r2']
            best_model = model
            best_name = name
    
    print("-"*60)
    print(f"✅ Best Model: {best_name} (R²: {best_r2:.4f}, MAE: {results[best_name]['mae']}M)")
    
    # Feature importance
    if hasattr(best_model, 'feature_importances_'):
        importance = pd.DataFrame({
            'feature': feature_cols,
            'importance': best_model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\n" + "="*70)
        print("TOP 15 FEATURE IMPORTANCE")
        print("="*70)
        for i, row in importance.head(15).iterrows():
            print(f"   {i+1:2d}. {row['feature']}: {row['importance']:.4f}")
    
    # Save model and artifacts
    joblib.dump(best_model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    joblib.dump(feature_cols, FEATURES_PATH)
    
    # Save metrics
    with open(MODELS_DIR / 'metrics.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Model saved to {MODEL_PATH}")
    print(f"✅ Scaler saved to {SCALER_PATH}")
    print(f"✅ Features saved to {FEATURES_PATH}")
    
    return best_model, results