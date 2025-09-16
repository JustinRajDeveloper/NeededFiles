#!/usr/bin/env python3
"""
Configuration template for Release Report Generator
Copy this file to config.py and fill in your actual values
"""

import os
from typing import Dict

def get_config() -> Dict[str, str]:
    """
    Configuration for the Release Report Generator
    
    You can either:
    1. Set environment variables
    2. Modify the values directly in this function
    3. Use a combination of both (env vars take precedence)
    """
    
    config = {
        # Git Repository Settings
        'git_repo_path': os.getenv('GIT_REPO_PATH', '/path/to/your/repository'),
        
        # Jira Settings
        'jira_url': os.getenv('JIRA_URL', 'https://your-company.atlassian.net'),
        'jira_pat_token': os.getenv('JIRA_PAT_TOKEN', 'your_jira_personal_access_token'),
        'jira_username': os.getenv('JIRA_USERNAME', 'your_email@company.com'),  # Optional for some Jira configs
        
        # OpenAI Settings
        'openai_api_key': os.getenv('OPENAI_API_KEY', 'sk-your_openai_api_key'),
        'openai_model': os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo'),  # or 'gpt-4'
        
        # SonarQube Settings
        'sonarqube_url': os.getenv('SONARQUBE_URL', 'https://your-sonarqube-instance.com'),
        'sonarqube_token': os.getenv('SONARQUBE_TOKEN', 'your_sonarqube_token'),
        'sonarqube_project_key': os.getenv('SONARQUBE_PROJECT_KEY', 'your_project_key'),
        
        # Veracode Settings
        'veracode_api_id': os.getenv('VERACODE_API_ID', 'your_veracode_api_id'),
        'veracode_api_key': os.getenv('VERACODE_API_KEY', 'your_veracode_api_key'),
        'veracode_app_id': os.getenv('VERACODE_APP_ID', 'your_app_id'),  # Application ID in Veracode
        
        # Report Settings
        'report_title': os.getenv('REPORT_TITLE', 'Release Summary Report'),
        'company_name': os.getenv('COMPANY_NAME', 'Your Company Name'),
        'company_logo': os.getenv('COMPANY_LOGO', ''),  # URL to company logo
        
        # Story Pattern Settings (customize based on your branch naming conventions)
        'story_patterns': {
            'feature': [
                r'^feature/([a-zA-Z]+-\d+)',
                r'^feat/([a-zA-Z]+-\d+)',
            ],
            'bugfix': [
                r'^bugfix/([a-zA-Z]+-\d+)',
                r'^bug/([a-zA-Z]+-\d+)',
                r'^fix/([a-zA-Z]+-\d+)',
            ],
            'hotfix': [
                r'^hotfix/([a-zA-Z]+-\d+)',
                r'^patch/([a-zA-Z]+-\d+)',
            ]
        }
    }
    
    # Validate required configurations
    required_fields = [
        'git_repo_path', 'jira_url', 'jira_pat_token', 'openai_api_key'
    ]
    
    missing_fields = []
    for field in required_fields:
        if not config.get(field) or config[field].startswith('your_') or config[field].startswith('/path/to/'):
            missing_fields.append(field)
    
    if missing_fields:
        raise ValueError(f"Missing required configuration fields: {', '.join(missing_fields)}")
    
    return config

# Environment variable setup script
def setup_env_vars():
    """
    Helper function to set up environment variables
    Run this once to set up your environment
    """
    env_vars = {
        'GIT_REPO_PATH': '/path/to/your/repository',
        'JIRA_URL': 'https://your-company.atlassian.net',
        'JIRA_PAT_TOKEN': 'your_jira_personal_access_token',
        'OPENAI_API_KEY': 'sk-your_openai_api_key',
        'SONARQUBE_URL': 'https://your-sonarqube-instance.com',
        'SONARQUBE_TOKEN': 'your_sonarqube_token',
        'SONARQUBE_PROJECT_KEY': 'your_project_key',
        'VERACODE_API_ID': 'your_veracode_api_id',
        'VERACODE_API_KEY': 'your_veracode_api_key',
    }
    
    print("Add these environment variables to your ~/.bashrc or ~/.zshrc:")
    print()
    for key, value in env_vars.items():
        print(f'export {key}="{value}"')
    print()
    print("Or create a .env file in your project directory with:")
    print()
    for key, value in env_vars.items():
        print(f'{key}={value}')

if __name__ == "__main__":
    setup_env_vars()
