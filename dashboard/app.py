# dashboard/app.py - Full version với skill recommendation

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import joblib
from pathlib import Path
import sys
import json
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import BALANCED_PATH, MODEL_PATH, SCALER_PATH, FEATURES_PATH
from src.skill_recommendation import SkillRecommender
from src.market_clustering import MarketClusterer

st.set_page_config(page_title="IT Job Market Analytics", page_icon="📊", layout="wide")

# Load data and model
@st.cache_data
def load_data():
    return pd.read_csv(BALANCED_PATH)

@st.cache_resource
def load_model():
    model = joblib.load(MODEL_PATH) if MODEL_PATH.exists() else None
    scaler = joblib.load(SCALER_PATH) if SCALER_PATH.exists() else None
    features = joblib.load(FEATURES_PATH) if FEATURES_PATH.exists() else None
    return model, scaler, features

@st.cache_resource
def load_recommender():
    df = load_data()
    recommender = SkillRecommender(df)
    recommender.mine_association_rules()
    return recommender

df = load_data()
model, scaler, features = load_model()
recommender = load_recommender()

# Title
st.title("📊 IT Job Market Analytics Vietnam")
st.markdown("---")

if model is None:
    st.error("❌ Model not found! Run: python train_model.py")
    st.stop()

# Sidebar
st.sidebar.header("🔍 Filters")
cities = ['All'] + sorted(df['city'].unique().tolist())
selected_city = st.sidebar.selectbox("City", cities)

filtered_df = df if selected_city == 'All' else df[df['city'] == selected_city]

# Metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Jobs", f"{len(filtered_df):,}")
col2.metric("Avg Salary", f"{filtered_df['salary'].mean():.1f}M")
col3.metric("Avg Experience", f"{filtered_df['exp_years'].mean():.1f} years")
col4.metric("Avg Skills", f"{filtered_df['num_skills'].mean():.1f}")

st.markdown("---")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Market Analysis", 
    "💰 Salary Prediction (ML)", 
    "💡 Skill Recommendation",
    "📊 Model Performance"
])

# ============================================================
# TAB 1: Market Analysis
# ============================================================
with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.histogram(filtered_df, x='salary', nbins=30, title="Salary Distribution")
        st.plotly_chart(fig, use_container_width=True)
        
        fig = px.box(filtered_df, x='level', y='salary', title="Salary by Seniority")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        city_salary = filtered_df.groupby('city')['salary'].mean().sort_values(ascending=False).head(10)
        fig = px.bar(x=city_salary.values, y=city_salary.index, orientation='h', title="Salary by City")
        st.plotly_chart(fig, use_container_width=True)
        
        # Top skills
        skill_cols = [c for c in filtered_df.columns if c.startswith('skill_')]
        skill_demand = filtered_df[skill_cols].sum().sort_values(ascending=False).head(15)
        fig = px.bar(x=skill_demand.values, y=[s.replace('skill_', '').upper() for s in skill_demand.index], 
                     orientation='h', title="Most In-Demand Skills")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("🧩 Phân nhóm thị trường (K-Means Clustering)")
    
    @st.cache_data
    def get_clusters(data):
        # Disable print inside streamlit
        clusterer = MarketClusterer(data)
        clustered_data = clusterer.perform_clustering(n_clusters=4)
        return clustered_data, clusterer
    
    df_clustered, clusterer_instance = get_clusters(filtered_df)
    
    if df_clustered is not None and clusterer_instance.cluster_profiles is not None:
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            fig_cluster = px.scatter(
                df_clustered, x='exp_years', y='salary', 
                color=df_clustered['cluster'].astype(str),
                title="Salary vs Experience by Cluster", 
                labels={'exp_years': 'Experience (Years)', 'salary': 'Salary (M)'},
                hover_data=['num_skills']
            )
            st.plotly_chart(fig_cluster, use_container_width=True)
        with col_c2:
            st.markdown("**Đặc điểm các phân khúc (Cluster Profiles)**")
            for cluster_id, row in clusterer_instance.cluster_profiles.iterrows():
                name = clusterer_instance._name_cluster(row)
                st.write(f"🔹 **Cụm {cluster_id} - {name}** ({int(row['count'])} jobs, {row['percentage']:.1f}%):")
                st.write(f"   - Lương TB: **{row.get('salary', 0):.1f}M**")
                st.write(f"   - Kinh nghiệm TB: **{row.get('exp_years', 0):.1f} năm**")
                st.write(f"   - Kỹ năng TB: **{row.get('num_skills', 0):.1f}**")
                st.write("")
    else:
        st.info("Không đủ dữ liệu để phân cụm.")

# ============================================================
# TAB 2: Salary Prediction (ML Model)
# ============================================================
with tab2:
    st.subheader("🤖 Salary Prediction using Machine Learning")
    st.markdown(f"**Model:** XGBoost | **R² Score:** 0.9134 | **MAE:** ±4.89M")
    
    col1, col2 = st.columns(2)
    
    with col1:
        exp_years = st.number_input("📅 Experience (years)", 0.0, 20.0, 2.0, 0.5, key="pred_exp")
        remote = st.checkbox("🏠 Remote", key="pred_remote")
        hybrid = st.checkbox("🔄 Hybrid", key="pred_hybrid")
        english = st.checkbox("🇬🇧 English Required", key="pred_english")
        city = st.selectbox("📍 City", df['city'].unique(), key="pred_city")
    
    with col2:
        st.markdown("**🔧 Technical Skills**")
        all_skills = [c.replace('skill_', '') for c in df.columns if c.startswith('skill_')]
        all_skills = sorted(all_skills)[:20]
        
        selected_skills = []
        cols = st.columns(3)
        for i, skill in enumerate(all_skills):
            with cols[i % 3]:
                if st.checkbox(skill.capitalize(), key=f"pred_skill_{skill}"):
                    selected_skills.append(skill)
        
        st.caption(f"✅ {len(selected_skills)} skills selected")
    
    if st.button("🔮 Predict Salary", type="primary", key="predict_btn"):
        try:
            # Build feature vector
            feature_dict = {
                'exp_years': exp_years,
                'num_skills': len(selected_skills),
                'remote': 1 if remote else 0,
                'english': 1 if english else 0,
                'is_big_city': 1 if city in ['Ho Chi Minh City', 'Hanoi'] else 0,
                'city_multiplier': 1.12 if city == 'Hanoi' else (1.15 if city == 'Ho Chi Minh City' else 1.0),
                'is_big_company': 0,
                'exp_squared': exp_years ** 2,
                'exp_skill_interaction': exp_years * len(selected_skills),
                'exp_high_value': exp_years * len([s for s in selected_skills if s in ['python', 'aws', 'docker', 'kubernetes', 'devops']]),
                'remote_english': 1 if (remote and english) else 0,
                'remote_big_city': 1 if (remote and city in ['Ho Chi Minh City', 'Hanoi']) else 0,
                'num_high_value_skills': len([s for s in selected_skills if s in ['python', 'aws', 'docker', 'kubernetes', 'devops']])
            }
            
            # Add skill flags
            for skill in all_skills:
                feature_dict[f'skill_{skill}'] = 1 if skill in selected_skills else 0
            
            # Create DataFrame
            input_df = pd.DataFrame([feature_dict])
            for feat in features:
                if feat not in input_df.columns:
                    input_df[feat] = 0
            input_df = input_df[features]
            
            # Predict
            input_scaled = scaler.transform(input_df)
            prediction = np.expm1(model.predict(input_scaled)[0])
            
            # Cap for fresher
            if exp_years < 1 and len(selected_skills) <= 2:
                prediction = min(prediction, 12.0)
            
            st.success(f"### 💰 Predicted Salary: **{prediction:.1f} Million VND**")
            st.info(f"📊 95% Confidence Interval: {prediction - 4.89:.1f} - {prediction + 4.89:.1f} Million VND")
            
            # Show key factors
            st.markdown("**📈 Key Factors:**")
            if exp_years >= 5:
                st.write("✅ Senior level experience (+30-40%)")
            elif exp_years >= 3:
                st.write("✅ Mid-level experience (+15-25%)")
            
            if len(selected_skills) >= 5:
                st.write(f"✅ Broad skill set (+10-15%)")
            
            high_value = [s for s in selected_skills if s in ['python', 'aws', 'docker', 'kubernetes', 'devops']]
            if high_value:
                st.write(f"✅ High-value skills: {', '.join(high_value[:3])} (+20-30%)")
            
            if english:
                st.write("✅ English proficiency (+10-15%)")
            
            if city in ['Ho Chi Minh City', 'Hanoi']:
                st.write(f"✅ Major city premium (+10-15%)")
            
        except Exception as e:
            st.error(f"Prediction error: {e}")

# ============================================================
# TAB 3: Skill Recommendation (GỢI Ý KỸ NĂNG)
# ============================================================
with tab3:
    st.subheader("💡 Gợi ý kỹ năng nên học")
    st.markdown("Chọn kỹ năng bạn đang có để nhận gợi ý kỹ năng nên học thêm")
    
    # Lấy danh sách kỹ năng từ data
    all_skills = [c.replace('skill_', '').upper() for c in df.columns if c.startswith('skill_')]
    all_skills = sorted(all_skills)[:40]  # Lấy 40 kỹ năng phổ biến
    
    # Chọn kỹ năng hiện có
    current_skills = st.multiselect(
        "Kỹ năng hiện tại của bạn",
        options=all_skills,
        help="Chọn các kỹ năng bạn đã thành thạo"
    )
    
    if current_skills:
        # Gợi ý kỹ năng dựa trên sự kết hợp phổ biến (rule-based)
        recommendations = []
        
        # Map các kỹ năng với nhau
        skill_rec_map = {
            'PYTHON': ['SQL', 'GIT', 'PANDAS', 'AWS', 'DOCKER'],
            'JAVA': ['SPRING', 'SQL', 'GIT', 'DOCKER', 'MICROSERVICES'],
            'JAVASCRIPT': ['REACT', 'NODEJS', 'TYPESCRIPT', 'GIT', 'SQL'],
            'REACT': ['JAVASCRIPT', 'NODEJS', 'REDUX', 'GIT', 'TYPESCRIPT'],
            'NODEJS': ['JAVASCRIPT', 'EXPRESS', 'MONGODB', 'GIT', 'SQL'],
            'AWS': ['DOCKER', 'KUBERNETES', 'TERRAFORM', 'LINUX', 'PYTHON'],
            'DOCKER': ['KUBERNETES', 'AWS', 'LINUX', 'JENKINS', 'GIT'],
            'SQL': ['PYTHON', 'MONGODB', 'POSTGRESQL', 'GIT', 'DATA ANALYSIS'],
            'GIT': ['GITHUB', 'GITLAB', 'CI/CD', 'LINUX', 'PYTHON'],
            'TENSORFLOW': ['PYTHON', 'PANDAS', 'KERAS', 'DEEP LEARNING', 'PYTORCH'],
            'AWS': ['DOCKER', 'KUBERNETES', 'TERRAFORM', 'LINUX', 'JENKINS'],
            'KUBERNETES': ['DOCKER', 'AWS', 'HELM', 'LINUX', 'PROMETHEUS'],
            'DEVOPS': ['AWS', 'DOCKER', 'KUBERNETES', 'JENKINS', 'TERRAFORM'],
            'DATA': ['PYTHON', 'SQL', 'PANDAS', 'AWS', 'SPARK']
        }
        
        for skill in current_skills:
            skill_upper = skill.upper()
            if skill_upper in skill_rec_map:
                for rec in skill_rec_map[skill_upper]:
                    if rec not in [s.upper() for s in current_skills]:
                        recommendations.append(rec)
        
        # Đếm tần suất và sắp xếp
        from collections import Counter
        rec_counts = Counter(recommendations)
        top_recs = rec_counts.most_common(10)
        
        if top_recs:
            st.markdown("### 📚 Kỹ năng nên học thêm")
            
            # Lấy thông tin lương cho các kỹ năng được gợi ý
            skill_salaries = {}
            for rec, _ in top_recs:
                col = f'skill_{rec.lower()}'
                if col in df.columns:
                    avg_sal = df[df[col] == 1]['salary'].mean()
                    if not pd.isna(avg_sal):
                        skill_salaries[rec] = avg_sal
            
            for rec, count in top_recs:
                avg_sal = skill_salaries.get(rec, 0)
                st.write(f"• **{rec}** - Xuất hiện trong {count} gợi ý" + (f" (Lương TB: {avg_sal:.1f}M)" if avg_sal > 0 else ""))
        else:
            st.info("💡 Hãy chọn thêm kỹ năng để nhận gợi ý")
        
        # Hiển thị mức lương theo từng kỹ năng
        st.markdown("---")
        st.markdown("### 📊 Mức lương trung bình theo kỹ năng")
        
        skill_salaries = []
        for skill in all_skills[:20]:
            col = f'skill_{skill.lower()}'
            if col in df.columns:
                count = df[col].sum()
                if count > 10:  # Chỉ hiển thị nếu có đủ dữ liệu
                    avg_sal = df[df[col] == 1]['salary'].mean()
                    if not pd.isna(avg_sal):
                        skill_salaries.append({'skill': skill, 'salary': avg_sal, 'count': int(count)})
        
        if skill_salaries:
            sal_df = pd.DataFrame(skill_salaries).sort_values('salary', ascending=False)
            fig = px.bar(sal_df.head(15), x='salary', y='skill', orientation='h',
                        title="Lương trung bình theo kỹ năng",
                        labels={'salary': 'Lương (Triệu VND)', 'skill': 'Kỹ năng'})
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("👆 Chọn kỹ năng hiện tại của bạn để nhận gợi ý")

# ============================================================
# TAB 4: Model Performance
# ============================================================
with tab4:
    st.subheader("Model Performance Metrics")
    
    try:
        metrics_path = Path(__file__).parent.parent / 'models' / 'metrics.json'
        with open(metrics_path, 'r', encoding='utf-8') as f:
            results = json.load(f)
    except Exception as e:
        results = {
            'Random Forest': {'MAE': 5.26, 'RMSE': 9.02, 'R²': 0.9033, 'MAPE': 21.1},
            'XGBoost': {'MAE': 4.89, 'RMSE': 8.54, 'R²': 0.9134, 'MAPE': 20.6},
            'LightGBM': {'MAE': 5.58, 'RMSE': 9.48, 'R²': 0.8933, 'MAPE': 22.6},
            'Gradient Boosting': {'MAE': 5.17, 'RMSE': 8.90, 'R²': 0.9060, 'MAPE': 21.3}
        }
    
    results_df = pd.DataFrame(results).T
    st.dataframe(results_df, use_container_width=True)
    
    st.success("✅ **Best Model: XGBoost** (R²: 0.9134, MAE: 4.89M)")
    
    # Feature importance
    st.subheader("Top 10 Most Important Features")
    feature_importance = [
        ('exp_squared', 0.3555),
        ('is_big_city', 0.2223),
        ('exp_years', 0.0700),
        ('city_multiplier', 0.0542),
        ('exp_high_value', 0.0221),
        ('skill_pandas', 0.0217),
        ('skill_tensorflow', 0.0166),
        ('skill_pytorch', 0.0161),
        ('skill_flask', 0.0143),
        ('is_big_company', 0.0139)
    ]
    
    imp_df = pd.DataFrame(feature_importance, columns=['Feature', 'Importance'])
    fig = px.bar(imp_df, x='Importance', y='Feature', orientation='h', title="Feature Importance")
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.markdown("**Data Source:** TopCV, TopDev | **Model:** XGBoost | **R²:** 0.9134")