# train_model.py
"""Train salary prediction model"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import BALANCED_PATH
from src.model_training import train_and_save
from src.skill_recommendation import SkillRecommender
from src.market_clustering import MarketClusterer
import pandas as pd


def main():
    print("="*70)
    print("MODEL TRAINING")
    print("="*70)
    
    # Load balanced data
    df = pd.read_csv(BALANCED_PATH)
    print(f"✅ Loaded {len(df):,} records")
    
    # Train model
    predictor, results = train_and_save(df)
    
    # Run market clustering
    clusterer = MarketClusterer(df)
    df_clustered = clusterer.perform_clustering(n_clusters=4)
    
    # Build skill recommender
    recommender = SkillRecommender(df)
    recommender.mine_association_rules()
    
    # Show hot skills
    print("\n" + "="*70)
    print("HOT SKILLS IN MARKET")
    print("="*70)
    hot_skills = recommender.get_hot_skills(15)
    for i, skill in enumerate(hot_skills):
        marker = "🔥" if skill['is_high_value'] else "  "
        print(f"{marker} {i+1:2d}. {skill['skill']:15s}: {skill['demand_percentage']:.1f}% jobs, {skill['avg_salary']:.1f}M")
    
    print("\n✅ Training complete!")


if __name__ == "__main__":
    main()