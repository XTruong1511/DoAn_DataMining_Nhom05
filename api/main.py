# api/main.py
"""FastAPI backend"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import MODEL_PATH, SCALER_PATH, FEATURES_PATH, BALANCED_PATH
from src.skill_recommendation import SkillRecommender

app = FastAPI(title="IT Job Market API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load model and recommender
model = joblib.load(MODEL_PATH) if MODEL_PATH.exists() else None
scaler = joblib.load(SCALER_PATH) if SCALER_PATH.exists() else None
features = joblib.load(FEATURES_PATH) if FEATURES_PATH.exists() else None
df = pd.read_csv(BALANCED_PATH) if BALANCED_PATH.exists() else None
recommender = SkillRecommender(df) if df is not None else None
if recommender:
    recommender.mine_association_rules()


class PredictRequest(BaseModel):
    experience_years: float
    skills: List[str]
    remote: bool = False
    english: bool = False
    city: str = "Ho Chi Minh City"


class PredictResponse(BaseModel):
    predicted_salary: float
    confidence_lower: float
    confidence_upper: float
    recommendations: List[Dict]


@app.get("/")
async def root():
    return {"message": "IT Job Market Analytics API", "status": "running"}


@app.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    if model is None or scaler is None or features is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Create feature vector
        feature_dict = {
            'exp_years': request.experience_years,
            'num_skills': len(request.skills),
            'remote': 1 if request.remote else 0,
            'english': 1 if request.english else 0,
            'is_big_city': 1 if request.city in ['Ho Chi Minh City', 'Hanoi'] else 0,
            'city_multiplier': 1.1 if request.city in ['Ho Chi Minh City', 'Hanoi'] else 1.0,
            'is_big_company': 0,
            'exp_squared': request.experience_years ** 2,
            'exp_skill_interaction': request.experience_years * len(request.skills),
            'exp_high_value': request.experience_years * len([s for s in request.skills if s in ['python', 'aws', 'docker', 'kubernetes', 'devops']]),
            'remote_english': 1 if request.remote and request.english else 0,
            'remote_big_city': 1 if request.remote and request.city in ['Ho Chi Minh City', 'Hanoi'] else 0,
            'salary_per_skill': 0,
            'num_high_value_skills': len([s for s in request.skills if s in ['python', 'aws', 'docker', 'kubernetes', 'devops']])
        }
        
        # Add skill flags
        all_skills = [c.replace('skill_', '') for c in df.columns if c.startswith('skill_')]
        for skill in all_skills:
            feature_dict[f'skill_{skill}'] = 1 if skill in request.skills else 0
        
        input_df = pd.DataFrame([feature_dict])
        
        for feat in features:
            if feat not in input_df.columns:
                input_df[feat] = 0
        
        input_df = input_df[features]
        input_scaled = scaler.transform(input_df)
        prediction = np.expm1(model.predict(input_scaled)[0])
        
        # Get recommendations
        recommendations = []
        if recommender and len(request.skills) > 0:
            recs = recommender.get_skill_combinations(request.skills, 5)
            recommendations = [{'skill': r['skill'], 'increase': r['salary_increase']} for r in recs]
        
        return PredictResponse(
            predicted_salary=round(prediction, 1),
            confidence_lower=round(prediction * 0.85, 1),
            confidence_upper=round(prediction * 1.15, 1),
            recommendations=recommendations
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/hot-skills")
async def get_hot_skills():
    if recommender is None:
        raise HTTPException(status_code=503, detail="Recommender not loaded")
    
    return {"hot_skills": recommender.get_hot_skills(20)}


@app.get("/health")
async def health():
    return {"status": "healthy", "model_loaded": model is not None}