# src/config.py
"""Configuration settings"""

from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
CLEANED_DATA_DIR = DATA_DIR / "cleaned"
ENRICHED_DATA_DIR = DATA_DIR / "enriched"
BALANCED_DATA_DIR = DATA_DIR / "balanced"
MODELS_DIR = PROJECT_ROOT / "models"
CHARTS_DIR = PROJECT_ROOT / "charts"

for d in [RAW_DATA_DIR, PROCESSED_DATA_DIR, CLEANED_DATA_DIR, ENRICHED_DATA_DIR, BALANCED_DATA_DIR, MODELS_DIR, CHARTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# File paths
RAW_CV_PATH = RAW_DATA_DIR / "test_topcv.csv"
RAW_DEV_PATH = RAW_DATA_DIR / "test_topdev.csv"
ENRICHED_PATH = ENRICHED_DATA_DIR / "enriched_dataset.csv"
BALANCED_PATH = BALANCED_DATA_DIR / "balanced_dataset.csv"
MODEL_PATH = MODELS_DIR / "salary_model.pkl"
SCALER_PATH = MODELS_DIR / "scaler.pkl"
FEATURES_PATH = MODELS_DIR / "feature_columns.pkl"

# Random seed
RANDOM_SEED = 42
TEST_SIZE = 0.2

# Salary bounds
MIN_SALARY = 5
MAX_SALARY = 100

# IT Keywords for filtering
IT_KEYWORDS = [
    'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'php', 'ruby', 'go',
    'react', 'angular', 'vue', 'nodejs', 'django', 'flask', 'spring', 'laravel',
    'backend', 'frontend', 'fullstack', 'devops', 'sre', 'platform',
    'data scientist', 'data engineer', 'data analyst', 'machine learning', 'ai',
    'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'gitlab',
    'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
    'tensorflow', 'pytorch', 'pandas', 'numpy', 'scikit-learn',
    'mobile', 'ios', 'android', 'swift', 'kotlin', 'flutter',
    'qa', 'tester', 'automation', 'selenium', 'cypress',
    'security', 'cybersecurity', 'penetration testing'
]


SKILLS_LIST = [
    # Programming Languages
    'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'php', 'ruby', 'go', 'rust', 'scala', 'kotlin', 'swift',
    
    # Frontend
    'react', 'angular', 'vue', 'nextjs', 'nuxt', 'svelte', 'html', 'css', 'sass', 'tailwind', 'bootstrap',
    
    # Backend
    'nodejs', 'express', 'django', 'flask', 'fastapi', 'spring', 'springboot', 'laravel', 'asp.net', 'rails',
    
    # Cloud & DevOps
    'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'k8s', 'jenkins', 'gitlab', 'github actions', 'terraform', 
    'ansible', 'prometheus', 'grafana', 'elk', 'splunk', 'cloudformation', 'pulumi',
    
    # Databases
    'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'cassandra', 'dynamodb', 'firebase',
    
    # Data & AI
    'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'keras', 'spark', 'hadoop', 'airflow', 
    'dbt', 'tableau', 'powerbi', 'looker', 'databricks', 'snowflake',
    
    # Mobile
    'android', 'ios', 'react native', 'flutter', 'swiftui', 'jetpack compose', 'xamarin',
    
    # Testing & QA
    'selenium', 'cypress', 'jest', 'pytest', 'junit', 'testng', 'postman', 'soapui',
    
    # Security
    'security', 'cybersecurity', 'penetration testing', 'ethical hacking', 'owasp', 'burpsuite', 'nmap',
    
    # Tools & Others
    'git', 'linux', 'bash', 'vim', 'intellij', 'vscode', 'jira', 'confluence', 'agile', 'scrum', 'kanban',
    'microservices', 'rest api', 'graphql', 'grpc', 'kafka', 'rabbitmq', 'redis', 'memcached'
]

# High value skills (increase salary)
HIGH_VALUE_SKILLS = ['python', 'aws', 'docker', 'kubernetes', 'devops', 'tensorflow', 'pytorch', 'react']

# Cities in Vietnam
VIETNAM_CITIES = ['Hanoi', 'Ho Chi Minh City', 'Da Nang', 'Hai Phong', 'Can Tho', 'Binh Duong', 'Dong Nai']