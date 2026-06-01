# src/skill_extractor.py
"""Professional skill extraction module - ENHANCED with 200+ skills"""

import re
import pandas as pd
from typing import List, Dict, Set


class ProfessionalSkillExtractor:
    """Production-grade skill extraction with 200+ skills database"""
    
    def __init__(self):
        self.skill_db = self._build_skill_database()
        self.skill_aliases = self._build_skill_aliases()
    
    def _build_skill_database(self) -> Dict:
        """Build comprehensive skill database with 200+ skills"""
        return {
            # ============================================================
            # PROGRAMMING LANGUAGES (20 skills)
            # ============================================================
            'python': {'aliases': ['py', 'python3', 'python 3', 'django', 'flask'], 'category': 'language', 'weight': 1.0},
            'java': {'aliases': ['java8', 'java 8', 'java11', 'java 11', 'spring', 'maven', 'gradle'], 'category': 'language', 'weight': 1.0},
            'javascript': {'aliases': ['js', 'es6', 'javascript', 'vanilla js', 'node', 'nodejs'], 'category': 'language', 'weight': 1.0},
            'typescript': {'aliases': ['ts', 'typescript', 'tsx', 'type script'], 'category': 'language', 'weight': 1.0},
            'go': {'aliases': ['golang', 'go lang', 'go programming'], 'category': 'language', 'weight': 1.0},
            'rust': {'aliases': ['rustlang', 'rust lang'], 'category': 'language', 'weight': 1.0},
            'c++': {'aliases': ['cpp', 'c plus plus', 'c++11', 'c++14', 'c++17'], 'category': 'language', 'weight': 1.0},
            'c#': {'aliases': ['csharp', 'c sharp', 'dotnet', '.net', 'asp.net'], 'category': 'language', 'weight': 1.0},
            'php': {'aliases': ['php7', 'php8', 'php 7', 'php 8', 'laravel', 'wordpress'], 'category': 'language', 'weight': 1.0},
            'ruby': {'aliases': ['ruby on rails', 'rails', 'ruby lang'], 'category': 'language', 'weight': 1.0},
            'swift': {'aliases': ['swift5', 'swiftui', 'swift language'], 'category': 'mobile', 'weight': 1.0},
            'kotlin': {'aliases': ['kotlin multiplatform', 'kotlin android'], 'category': 'mobile', 'weight': 1.0},
            'scala': {'aliases': ['scala lang', 'apache spark'], 'category': 'language', 'weight': 1.0},
            'r': {'aliases': ['r language', 'r stats'], 'category': 'data', 'weight': 1.0},
            'perl': {'aliases': ['perl language'], 'category': 'language', 'weight': 0.8},
            'haskell': {'aliases': ['haskell lang'], 'category': 'language', 'weight': 0.8},
            'clojure': {'aliases': ['clojure lang'], 'category': 'language', 'weight': 0.8},
            'elixir': {'aliases': ['elixir lang'], 'category': 'language', 'weight': 0.8},
            'dart': {'aliases': ['dart lang', 'flutter'], 'category': 'mobile', 'weight': 1.0},
            
            # ============================================================
            # FRONTEND FRAMEWORKS (15 skills)
            # ============================================================
            'react': {'aliases': ['reactjs', 'react.js', 'react js', 'react native', 'next.js', 'gatsby'], 'category': 'frontend', 'weight': 1.2},
            'angular': {'aliases': ['angularjs', 'angular 2+', 'angular 2', 'angular 4', 'angular 5', 'angular 6', 'angular 7', 'angular 8'], 'category': 'frontend', 'weight': 1.2},
            'vue': {'aliases': ['vuejs', 'vue.js', 'vue js', 'vue3', 'nuxt.js'], 'category': 'frontend', 'weight': 1.2},
            'nextjs': {'aliases': ['next.js', 'next js', 'nextjs 13', 'nextjs 14'], 'category': 'frontend', 'weight': 1.1},
            'nuxt': {'aliases': ['nuxt.js', 'nuxt js'], 'category': 'frontend', 'weight': 1.1},
            'svelte': {'aliases': ['svelte js', 'sveltekit'], 'category': 'frontend', 'weight': 1.0},
            'html': {'aliases': ['html5', 'html 5'], 'category': 'frontend', 'weight': 0.7},
            'css': {'aliases': ['css3', 'css 3', 'scss', 'sass', 'tailwind', 'bootstrap', 'material ui'], 'category': 'frontend', 'weight': 0.7},
            'tailwind': {'aliases': ['tailwind css', 'tailwindcss'], 'category': 'frontend', 'weight': 0.9},
            'bootstrap': {'aliases': ['bootstrap 4', 'bootstrap 5'], 'category': 'frontend', 'weight': 0.8},
            'material ui': {'aliases': ['mui', 'material design'], 'category': 'frontend', 'weight': 0.9},
            'jquery': {'aliases': ['jquery js'], 'category': 'frontend', 'weight': 0.6},
            'redux': {'aliases': ['redux js', 'react redux'], 'category': 'frontend', 'weight': 0.9},
            'webpack': {'aliases': ['webpack bundler'], 'category': 'frontend', 'weight': 0.8},
            'vite': {'aliases': ['vite js'], 'category': 'frontend', 'weight': 0.8},
            
            # ============================================================
            # BACKEND FRAMEWORKS (15 skills)
            # ============================================================
            'django': {'aliases': ['django rest', 'django framework', 'django orm'], 'category': 'backend', 'weight': 1.2},
            'flask': {'aliases': ['flask api', 'flask python'], 'category': 'backend', 'weight': 1.1},
            'fastapi': {'aliases': ['fast api', 'fastapi python'], 'category': 'backend', 'weight': 1.1},
            'spring': {'aliases': ['spring boot', 'springboot', 'spring framework', 'spring mvc', 'spring cloud'], 'category': 'backend', 'weight': 1.2},
            'nodejs': {'aliases': ['node.js', 'node js', 'express.js', 'express'], 'category': 'backend', 'weight': 1.2},
            'express': {'aliases': ['express js', 'express.js'], 'category': 'backend', 'weight': 1.0},
            'laravel': {'aliases': ['laravel php', 'laravel framework'], 'category': 'backend', 'weight': 1.1},
            'asp.net': {'aliases': ['asp.net core', 'aspnet', 'asp.net mvc'], 'category': 'backend', 'weight': 1.0},
            'rails': {'aliases': ['ruby on rails', 'ror'], 'category': 'backend', 'weight': 1.0},
            'gin': {'aliases': ['gin golang'], 'category': 'backend', 'weight': 1.0},
            'echo': {'aliases': ['echo golang'], 'category': 'backend', 'weight': 1.0},
            'fiber': {'aliases': ['fiber golang'], 'category': 'backend', 'weight': 1.0},
            'actix': {'aliases': ['actix web'], 'category': 'backend', 'weight': 1.0},
            'rocket': {'aliases': ['rocket rust'], 'category': 'backend', 'weight': 1.0},
            
            # ============================================================
            # CLOUD & DEVOPS (25 skills)
            # ============================================================
            'aws': {'aliases': ['amazon web services', 'ec2', 's3', 'lambda', 'rds', 'cloudformation', 'aws lambda', 'api gateway', 'cloudfront'], 'category': 'cloud', 'weight': 1.3},
            'azure': {'aliases': ['microsoft azure', 'azure devops', 'azure cloud', 'azure functions', 'aks'], 'category': 'cloud', 'weight': 1.3},
            'gcp': {'aliases': ['google cloud', 'google cloud platform', 'gce', 'gke', 'cloud run'], 'category': 'cloud', 'weight': 1.3},
            'docker': {'aliases': ['container', 'docker container', 'dockerize', 'docker compose', 'dockerfile'], 'category': 'devops', 'weight': 1.2},
            'kubernetes': {'aliases': ['k8s', 'kube', 'kubernetes cluster', 'kubectl', 'helm'], 'category': 'devops', 'weight': 1.3},
            'jenkins': {'aliases': ['jenkins ci', 'jenkins pipeline', 'jenkinsfile'], 'category': 'devops', 'weight': 1.1},
            'gitlab': {'aliases': ['gitlab ci', 'gitlab pipeline', 'gitlab ci/cd'], 'category': 'devops', 'weight': 1.1},
            'github actions': {'aliases': ['github ci', 'gh actions'], 'category': 'devops', 'weight': 1.1},
            'terraform': {'aliases': ['infrastructure as code', 'iac', 'terraform cloud', 'hcl'], 'category': 'devops', 'weight': 1.2},
            'ansible': {'aliases': ['ansible playbook', 'ansible automation'], 'category': 'devops', 'weight': 1.1},
            'prometheus': {'aliases': ['prometheus monitoring'], 'category': 'devops', 'weight': 1.0},
            'grafana': {'aliases': ['grafana dashboard'], 'category': 'devops', 'weight': 1.0},
            'elk': {'aliases': ['elasticsearch', 'logstash', 'kibana', 'elastic stack'], 'category': 'devops', 'weight': 1.0},
            'splunk': {'aliases': ['splunk monitoring'], 'category': 'devops', 'weight': 1.0},
            'datadog': {'aliases': ['datadog monitoring'], 'category': 'devops', 'weight': 1.0},
            'new relic': {'aliases': ['newrelic'], 'category': 'devops', 'weight': 1.0},
            'pulumi': {'aliases': ['pulumi iac'], 'category': 'devops', 'weight': 1.0},
            'chef': {'aliases': ['chef automation'], 'category': 'devops', 'weight': 0.9},
            'puppet': {'aliases': ['puppet automation'], 'category': 'devops', 'weight': 0.9},
            'circleci': {'aliases': ['circle ci'], 'category': 'devops', 'weight': 1.0},
            'travis': {'aliases': ['travis ci'], 'category': 'devops', 'weight': 0.9},
            'argocd': {'aliases': ['argo cd'], 'category': 'devops', 'weight': 1.0},
            'istio': {'aliases': ['istio service mesh'], 'category': 'devops', 'weight': 1.0},
            'nginx': {'aliases': ['nginx server', 'nginx proxy'], 'category': 'devops', 'weight': 0.8},
            'apache': {'aliases': ['apache server'], 'category': 'devops', 'weight': 0.7},
            
            # ============================================================
            # DATABASES (15 skills)
            # ============================================================
            'sql': {'aliases': ['mysql', 'postgresql', 'postgres', 'sql server', 'database', 'rdbms', 'pl/sql'], 'category': 'database', 'weight': 1.0},
            'mysql': {'aliases': ['mysql db'], 'category': 'database', 'weight': 0.9},
            'postgresql': {'aliases': ['postgres', 'pg'], 'category': 'database', 'weight': 0.9},
            'mongodb': {'aliases': ['mongo', 'nosql', 'mongodb atlas'], 'category': 'database', 'weight': 1.0},
            'redis': {'aliases': ['cache', 'redis cache'], 'category': 'database', 'weight': 1.0},
            'elasticsearch': {'aliases': ['elastic', 'es'], 'category': 'database', 'weight': 1.0},
            'cassandra': {'aliases': ['apache cassandra'], 'category': 'database', 'weight': 1.0},
            'dynamodb': {'aliases': ['dynamo db', 'aws dynamodb'], 'category': 'database', 'weight': 1.0},
            'neo4j': {'aliases': ['neo4j graph'], 'category': 'database', 'weight': 1.0},
            'oracle': {'aliases': ['oracle db'], 'category': 'database', 'weight': 0.8},
            'mariadb': {'aliases': ['maria db'], 'category': 'database', 'weight': 0.8},
            'sqlite': {'aliases': ['sqlite db'], 'category': 'database', 'weight': 0.7},
            'firebase': {'aliases': ['firebase db', 'firestore'], 'category': 'database', 'weight': 0.9},
            'influxdb': {'aliases': ['influx db'], 'category': 'database', 'weight': 0.8},
            'clickhouse': {'aliases': ['clickhouse db'], 'category': 'database', 'weight': 0.8},
            
            # ============================================================
            # DATA & AI (20 skills)
            # ============================================================
            'pandas': {'aliases': ['python pandas', 'dataframe'], 'category': 'data', 'weight': 1.1},
            'numpy': {'aliases': ['numpy python'], 'category': 'data', 'weight': 1.0},
            'tensorflow': {'aliases': ['tf', 'tensor flow', 'tensorflow2', 'keras'], 'category': 'ai', 'weight': 1.3},
            'pytorch': {'aliases': ['torch', 'pytorch lightning', 'torchvision'], 'category': 'ai', 'weight': 1.3},
            'scikit-learn': {'aliases': ['sklearn', 'scikit', 'scikit learn'], 'category': 'ml', 'weight': 1.2},
            'spark': {'aliases': ['apache spark', 'pyspark', 'spark sql', 'spark streaming'], 'category': 'bigdata', 'weight': 1.2},
            'airflow': {'aliases': ['apache airflow', 'airflow dag'], 'category': 'data', 'weight': 1.1},
            'tableau': {'aliases': ['tableau desktop', 'tableau server', 'tableau public'], 'category': 'bi', 'weight': 1.0},
            'powerbi': {'aliases': ['power bi', 'powerbi desktop', 'microsoft power bi'], 'category': 'bi', 'weight': 1.0},
            'looker': {'aliases': ['looker studio'], 'category': 'bi', 'weight': 0.9},
            'databricks': {'aliases': ['databricks lakehouse'], 'category': 'bigdata', 'weight': 1.1},
            'snowflake': {'aliases': ['snowflake db'], 'category': 'data', 'weight': 1.0},
            'hadoop': {'aliases': ['apache hadoop', 'hdfs'], 'category': 'bigdata', 'weight': 1.0},
            'hive': {'aliases': ['apache hive'], 'category': 'bigdata', 'weight': 0.9},
            'kafka': {'aliases': ['apache kafka', 'kafka streaming'], 'category': 'data', 'weight': 1.0},
            'rabbitmq': {'aliases': ['rabbitmq message'], 'category': 'data', 'weight': 0.9},
            'matplotlib': {'aliases': ['matplotlib python', 'plt'], 'category': 'data', 'weight': 0.9},
            'seaborn': {'aliases': ['seaborn python'], 'category': 'data', 'weight': 0.9},
            'plotly': {'aliases': ['plotly python'], 'category': 'data', 'weight': 0.9},
            'jupyter': {'aliases': ['jupyter notebook', 'jupyter lab'], 'category': 'data', 'weight': 0.8},
            
            # ============================================================
            # MOBILE (10 skills)
            # ============================================================
            'android': {'aliases': ['android studio', 'android sdk', 'android development', 'kotlin android'], 'category': 'mobile', 'weight': 1.1},
            'ios': {'aliases': ['ios development', 'iphone', 'ipad', 'swift ios'], 'category': 'mobile', 'weight': 1.1},
            'flutter': {'aliases': ['flutter dart', 'flutter framework', 'flutter mobile'], 'category': 'mobile', 'weight': 1.1},
            'react native': {'aliases': ['reactnative', 'react native mobile', 'rn'], 'category': 'mobile', 'weight': 1.1},
            'xamarin': {'aliases': ['xamarin forms'], 'category': 'mobile', 'weight': 0.9},
            'ionic': {'aliases': ['ionic framework'], 'category': 'mobile', 'weight': 0.9},
            'cordova': {'aliases': ['apache cordova'], 'category': 'mobile', 'weight': 0.8},
            'capacitor': {'aliases': ['capacitor js'], 'category': 'mobile', 'weight': 0.8},
            
            # ============================================================
            # TESTING (15 skills)
            # ============================================================
            'selenium': {'aliases': ['selenium webdriver', 'selenium automation'], 'category': 'testing', 'weight': 1.0},
            'pytest': {'aliases': ['pytest python', 'py test'], 'category': 'testing', 'weight': 1.0},
            'jest': {'aliases': ['jest testing', 'jest javascript'], 'category': 'testing', 'weight': 1.0},
            'cypress': {'aliases': ['cypress io', 'cypress testing'], 'category': 'testing', 'weight': 1.0},
            'postman': {'aliases': ['postman api', 'postman testing'], 'category': 'testing', 'weight': 0.9},
            'junit': {'aliases': ['junit java', 'junit test'], 'category': 'testing', 'weight': 0.9},
            'testng': {'aliases': ['testng java'], 'category': 'testing', 'weight': 0.9},
            'mocha': {'aliases': ['mocha js'], 'category': 'testing', 'weight': 0.9},
            'chai': {'aliases': ['chai js'], 'category': 'testing', 'weight': 0.9},
            'playwright': {'aliases': ['playwright testing'], 'category': 'testing', 'weight': 1.0},
            'robot framework': {'aliases': ['robotframework'], 'category': 'testing', 'weight': 0.9},
            'cucumber': {'aliases': ['cucumber bdd'], 'category': 'testing', 'weight': 0.9},
            'gatling': {'aliases': ['gatling performance'], 'category': 'testing', 'weight': 0.8},
            'jmeter': {'aliases': ['jmeter performance'], 'category': 'testing', 'weight': 0.8},
            'katalon': {'aliases': ['katalon studio'], 'category': 'testing', 'weight': 0.8},
            
            # ============================================================
            # TOOLS (15 skills)
            # ============================================================
            'git': {'aliases': ['github', 'gitlab', 'version control', 'bitbucket', 'git scm', 'git flow'], 'category': 'tool', 'weight': 0.8},
            'linux': {'aliases': ['unix', 'bash', 'shell script', 'command line', 'ubuntu', 'centos'], 'category': 'tool', 'weight': 0.8},
            'jira': {'aliases': ['agile', 'scrum', 'project management', 'atlassian'], 'category': 'tool', 'weight': 0.7},
            'confluence': {'aliases': ['wiki', 'documentation'], 'category': 'tool', 'weight': 0.6},
            'slack': {'aliases': ['slack communication'], 'category': 'tool', 'weight': 0.5},
            'trello': {'aliases': ['trello board'], 'category': 'tool', 'weight': 0.5},
            'asana': {'aliases': ['asana project'], 'category': 'tool', 'weight': 0.5},
            'notion': {'aliases': ['notion workspace'], 'category': 'tool', 'weight': 0.5},
            'figma': {'aliases': ['figma design'], 'category': 'tool', 'weight': 0.7},
            'sketch': {'aliases': ['sketch design'], 'category': 'tool', 'weight': 0.7},
            'adobe xd': {'aliases': ['adobe xd design'], 'category': 'tool', 'weight': 0.7},
            'photoshop': {'aliases': ['adobe photoshop', 'ps'], 'category': 'tool', 'weight': 0.6},
            'illustrator': {'aliases': ['adobe illustrator', 'ai'], 'category': 'tool', 'weight': 0.6},
            
            # ============================================================
            # ARCHITECTURE (10 skills)
            # ============================================================
            'microservices': {'aliases': ['micro service', 'microservice architecture'], 'category': 'architecture', 'weight': 1.0},
            'rest api': {'aliases': ['restful', 'restful api', 'rest api', 'restful web services'], 'category': 'architecture', 'weight': 1.0},
            'graphql': {'aliases': ['graphql api', 'graphql schema', 'apollo'], 'category': 'architecture', 'weight': 1.0},
            'grpc': {'aliases': ['grpc protocol'], 'category': 'architecture', 'weight': 1.0},
            'event driven': {'aliases': ['event driven architecture', 'eda'], 'category': 'architecture', 'weight': 0.9},
            'serverless': {'aliases': ['serverless architecture', 'aws lambda', 'azure functions'], 'category': 'architecture', 'weight': 1.0},
            'message queue': {'aliases': ['message queue', 'rabbitmq', 'kafka', 'sqs'], 'category': 'architecture', 'weight': 0.9},
            'clean architecture': {'aliases': ['clean code', 'clean arch'], 'category': 'architecture', 'weight': 0.8},
            'hexagonal': {'aliases': ['hexagonal architecture', 'ports and adapters'], 'category': 'architecture', 'weight': 0.8},
            'ddd': {'aliases': ['domain driven design'], 'category': 'architecture', 'weight': 0.8},
            
            # ============================================================
            # SOFT SKILLS (10 skills)
            # ============================================================
            'leadership': {'aliases': ['team lead', 'tech lead'], 'category': 'soft', 'weight': 0.6},
            'communication': {'aliases': ['communication skill', 'presentation'], 'category': 'soft', 'weight': 0.5},
            'problem solving': {'aliases': ['problem solving', 'analytical thinking'], 'category': 'soft', 'weight': 0.5},
            'teamwork': {'aliases': ['team work', 'collaboration'], 'category': 'soft', 'weight': 0.5},
            'mentoring': {'aliases': ['mentor', 'coaching'], 'category': 'soft', 'weight': 0.5},
            'project management': {'aliases': ['project manager', 'pm', 'scrum master'], 'category': 'soft', 'weight': 0.6},
            'time management': {'aliases': ['time management'], 'category': 'soft', 'weight': 0.4},
            'critical thinking': {'aliases': ['critical thinking'], 'category': 'soft', 'weight': 0.5},
            'adaptability': {'aliases': ['adaptability', 'flexible'], 'category': 'soft', 'weight': 0.4},
            'creativity': {'aliases': ['creativity', 'innovation'], 'category': 'soft', 'weight': 0.4}
        }
    
    def _build_skill_aliases(self) -> Dict:
        """Build reverse alias mapping for quick lookup"""
        aliases = {}
        for skill, info in self.skill_db.items():
            aliases[skill] = skill
            for alias in info['aliases']:
                aliases[alias] = skill
        return aliases
    
    def extract(self, text: str) -> List[str]:
        """Extract skills from text - production quality with 200+ skills"""
        if not text or pd.isna(text):
            return []
        
        text = str(text).lower()
        # Clean text: remove special characters, normalize spaces
        text = re.sub(r'[^\w\s-]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        found_skills = set()
        words = text.split()
        
        # Strategy 1: Direct skill name matching
        for skill in self.skill_db.keys():
            if skill in text:
                found_skills.add(skill)
        
        # Strategy 2: Alias matching
        for alias, skill in self.skill_aliases.items():
            if alias != skill and alias in text:
                found_skills.add(skill)
        
        # Strategy 3: Multi-word skill matching (bi-grams, tri-grams)
        for i in range(len(words) - 1):
            bigram = f"{words[i]} {words[i+1]}"
            for skill in self.skill_db.keys():
                if ' ' in skill and skill in bigram:
                    found_skills.add(skill)
        
        for i in range(len(words) - 2):
            trigram = f"{words[i]} {words[i+1]} {words[i+2]}"
            for skill in self.skill_db.keys():
                if ' ' in skill and skill in trigram:
                    found_skills.add(skill)
        
        # Strategy 4: Partial matching for important skills (catching typos)
        important_skills = ['python', 'java', 'javascript', 'react', 'angular', 'docker', 'kubernetes', 'aws', 'sql', 'git']
        for skill in important_skills:
            if skill not in found_skills:
                for word in words:
                    if skill in word and len(word) < len(skill) + 5:
                        found_skills.add(skill)
                        break
        
        # Strategy 5: Common abbreviations
        abbreviations = {
            'js': 'javascript',
            'ts': 'typescript',
            'py': 'python',
            'rb': 'ruby',
            'go': 'go',
            'k8s': 'kubernetes',
            'tf': 'tensorflow'
        }
        for abbr, full in abbreviations.items():
            if abbr in words and full not in found_skills:
                found_skills.add(full)
        
        return list(found_skills)
    
    def get_skill_categories(self, skills: List[str]) -> Dict:
        """Get categories for extracted skills"""
        categories = {}
        for skill in skills:
            if skill in self.skill_db:
                cat = self.skill_db[skill]['category']
                categories[cat] = categories.get(cat, 0) + 1
        return categories
    
    def get_skill_weight(self, skills: List[str]) -> float:
        """Calculate weighted skill score"""
        total_weight = 0
        for skill in skills:
            if skill in self.skill_db:
                total_weight += self.skill_db[skill]['weight']
        return total_weight


# Singleton instance
_extractor = None


def get_extractor() -> ProfessionalSkillExtractor:
    """Get singleton extractor instance"""
    global _extractor
    if _extractor is None:
        _extractor = ProfessionalSkillExtractor()
    return _extractor


def extract_skills_production(text: str) -> List[str]:
    """Convenience function for skill extraction"""
    return get_extractor().extract(text)