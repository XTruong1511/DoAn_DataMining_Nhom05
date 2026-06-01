# src/market_clustering.py
"""Market clustering using K-Means"""

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from src.utils import create_logger

logger = create_logger("clustering")


class MarketClusterer:
    """Cluster job market into segments"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.scaler = StandardScaler()
        self.kmeans = None
        self.cluster_labels = None
        self.cluster_profiles = None
        
    def perform_clustering(self, n_clusters: int = 4):
        """Perform K-Means clustering"""
        print("\n" + "="*70)
        print(f"MARKET CLUSTERING (K-MEANS with K={n_clusters})")
        print("="*70)
        
        # Select features for clustering
        features = ['exp_years', 'num_skills', 'salary', 'is_big_city']
        available_features = [f for f in features if f in self.df.columns]
        
        if not available_features:
            print("⚠️ Not enough features for clustering")
            return None
            
        print(f"📊 Features used for clustering: {', '.join(available_features)}")
        
        # Prepare data (fill NA, remove outliers could be done here, but we assume clean data)
        X = self.df[available_features].fillna(0).copy()
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train K-Means
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        self.cluster_labels = self.kmeans.fit_predict(X_scaled)
        
        # Add labels to dataframe
        self.df['cluster'] = self.cluster_labels
        
        # Profile clusters
        self._profile_clusters(available_features)
        
        return self.df
        
    def _profile_clusters(self, features):
        """Analyze and print cluster characteristics"""
        print("\n📊 Cluster Profiles:")
        
        self.cluster_profiles = self.df.groupby('cluster')[features].mean()
        self.cluster_profiles['count'] = self.df.groupby('cluster').size()
        self.cluster_profiles['percentage'] = (self.cluster_profiles['count'] / len(self.df)) * 100
        
        for cluster_id, row in self.cluster_profiles.iterrows():
            print(f"\n🔹 Cluster {cluster_id} - '{self._name_cluster(row)}' ({int(row['count'])} jobs, {row['percentage']:.1f}%):")
            print(f"   - Average Salary: {row.get('salary', 0):.1f}M")
            print(f"   - Average Experience: {row.get('exp_years', 0):.1f} years")
            print(f"   - Average Skills: {row.get('num_skills', 0):.1f}")
            if 'is_big_city' in row:
                print(f"   - Big City Ratio: {row['is_big_city']*100:.1f}%")
                
    def _name_cluster(self, profile) -> str:
        """Heuristic to give a readable name to the cluster based on stats"""
        exp = profile.get('exp_years', 0)
        salary = profile.get('salary', 0)
        
        if exp < 2 and salary < 15:
            return "Entry/Junior Level"
        elif exp >= 4 and salary >= 30:
            return "Senior/Expert & High Paid"
        elif exp >= 2 and exp < 4:
            return "Mid-level Professional"
        else:
            return "Specialized/Other"
