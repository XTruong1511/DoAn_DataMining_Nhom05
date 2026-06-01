# src/skill_recommendation.py
"""Skill recommendation based on market trends"""

import pandas as pd
import numpy as np
from collections import Counter
from mlxtend.frequent_patterns import apriori, association_rules
from src.config import SKILLS_LIST, HIGH_VALUE_SKILLS
from src.utils import create_logger

logger = create_logger("recommendation")


class SkillRecommender:
    """Recommend skills based on market data"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.skill_matrix = None
        self.rules = None
        
    def build_skill_matrix(self):
        """Build skill co-occurrence matrix with boolean values"""
        skill_cols = [f'skill_{s}' for s in SKILLS_LIST if f'skill_{s}' in self.df.columns]
        
        # Convert to boolean and fill NaN with False
        self.skill_matrix = self.df[skill_cols].fillna(0).astype(bool)
        
        return self.skill_matrix
    
    def mine_association_rules(self, min_support=0.03, min_lift=1.2):
        """Mine association rules between skills"""
        print("\n" + "="*70)
        print("MINING SKILL ASSOCIATION RULES")
        print("="*70)
        
        try:
            matrix = self.build_skill_matrix()
            
            if len(matrix) == 0 or len(matrix.columns) == 0:
                print("⚠️ No skill data available for association rules")
                self.rules = pd.DataFrame()
                return self.rules
            
            # Find frequent itemsets
            frequent_itemsets = apriori(matrix, min_support=min_support, use_colnames=True, low_memory=True)
            
            if len(frequent_itemsets) == 0:
                print("⚠️ No frequent itemsets found")
                self.rules = pd.DataFrame()
                return self.rules
            
            # Generate rules
            self.rules = association_rules(frequent_itemsets, metric='lift', min_threshold=min_lift)
            self.rules = self.rules.sort_values('lift', ascending=False)
            
            print(f"✅ Found {len(self.rules)} association rules")
            
        except Exception as e:
            print(f"⚠️ Could not mine association rules: {e}")
            self.rules = pd.DataFrame()
        
        return self.rules
    
    def get_hot_skills(self, top_n: int = 20) -> list:
        """Get most in-demand skills"""
        skill_cols = [f'skill_{s}' for s in SKILLS_LIST if f'skill_{s}' in self.df.columns]
        
        if not skill_cols:
            return []
        
        skill_counts = self.df[skill_cols].sum().sort_values(ascending=False)
        
        hot_skills = []
        for col, count in skill_counts.head(top_n).items():
            skill_name = col.replace('skill_', '')
            percentage = count / len(self.df) * 100 if len(self.df) > 0 else 0
            avg_salary = self.df[self.df[col] == 1]['salary'].mean() if count > 0 else 0
            
            hot_skills.append({
                'skill': skill_name,
                'demand_count': int(count),
                'demand_percentage': round(percentage, 1),
                'avg_salary': round(avg_salary, 1),
                'is_high_value': skill_name in HIGH_VALUE_SKILLS
            })
        
        return hot_skills
    
    def get_skill_combinations(self, current_skills: list, top_n: int = 10) -> list:
        """Recommend skills based on current skills"""
        recommendations = []
        
        if self.rules is None or len(self.rules) == 0:
            # Fallback: recommend top hot skills not already in current skills
            hot_skills = self.get_hot_skills(top_n * 2)
            return [h for h in hot_skills if h['skill'] not in current_skills][:top_n]
        
        try:
            for _, rule in self.rules.iterrows():
                antecedents = [s.replace('skill_', '') for s in rule['antecedents']]
                consequents = [s.replace('skill_', '') for s in rule['consequents']]
                
                # Check if user has antecedents
                if all(s in current_skills for s in antecedents):
                    for skill in consequents:
                        if skill not in current_skills:
                            # Get skill stats
                            col = f'skill_{skill}'
                            if col in self.df.columns:
                                count = self.df[col].sum()
                                avg_salary = self.df[self.df[col] == 1]['salary'].mean() if count > 0 else 0
                                
                                recommendations.append({
                                    'skill': skill,
                                    'from_skills': antecedents,
                                    'lift': round(rule['lift'], 2),
                                    'confidence': round(rule['confidence'], 2),
                                    'demand_count': int(count),
                                    'avg_salary': round(avg_salary, 1),
                                    'salary_increase': round(avg_salary - self.df['salary'].mean(), 1)
                                })
            
            # Remove duplicates and sort by lift
            seen = set()
            unique_recs = []
            for rec in sorted(recommendations, key=lambda x: x['lift'], reverse=True):
                if rec['skill'] not in seen:
                    seen.add(rec['skill'])
                    unique_recs.append(rec)
            
            return unique_recs[:top_n]
            
        except Exception as e:
            print(f"⚠️ Error getting recommendations: {e}")
            return []
    
    def get_salary_impact(self, skill: str) -> dict:
        """Get salary impact of a skill"""
        col = f'skill_{skill}'
        if col not in self.df.columns:
            return {'skill': skill, 'has_skill': False}
        
        with_skill = self.df[self.df[col] == 1]['salary'].mean()
        without_skill = self.df[self.df[col] == 0]['salary'].mean()
        
        return {
            'skill': skill,
            'has_skill': True,
            'avg_salary_with': round(with_skill, 1),
            'avg_salary_without': round(without_skill, 1),
            'increase': round(with_skill - without_skill, 1),
            'increase_percentage': round((with_skill - without_skill) / without_skill * 100, 1) if without_skill > 0 else 0
        }