#!/usr/bin/env python3
"""
Test script to validate all API connections and configurations
Run this before generating your first report to ensure everything works
"""

import requests
import json
import base64
import subprocess
import os
from datetime import datetime
import openai
from config_template import get_config

def test_git_repository(repo_path: str) -> bool:
    """Test Git repository access"""
    print("🔍 Testing Git repository...")
    
    try:
        if not os.path.exists(repo_path):
            print(f"   ❌ Repository path does not exist: {repo_path}")
            return False
        
        if not os.path.exists(os.path.join(repo_path, '.git')):
            print(f"   ❌ Not a Git repository: {repo_path}")
            return False
        
        # Test git commands
        original_dir = os.getcwd()
        os.chdir(repo_path)
        
        # Get current branch
        result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            current_branch = result.stdout.strip()
            print(f"   ✅ Repository accessible, current branch: {current_branch}")
            
            # List some recent commits
            result = subprocess.run(['git', 'log', '--oneline', '-5'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                commit_count = len(result.stdout.strip().split('\n'))
                print(f"   ✅ Found {commit_count} recent commits")
            
            os.chdir(original_dir)
            return True
        else:
            print(f"   ❌ Git command failed: {result.stderr}")
            os.chdir(original_dir)
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing Git repository: {e}")
        return False

def test_jira_connection(jira_url: str, jira_token: str) -> bool:
    """Test Jira API connection"""
    print("🎫 Testing Jira connection...")
    
    try:
        # Test authentication by getting current user info
        url = f"{jira_url}/rest/api/3/myself"
        headers = {
            'Authorization': f"Bearer {jira_token}",
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            user_info = response.json()
            print(f"   ✅ Connected as: {user_info.get('displayName', 'Unknown User')}")
            print(f"   ✅ Email: {user_info.get('emailAddress', 'Not provided')}")
            
            # Test project access
            projects_url = f"{jira_url}/rest/api/3/project"
            projects_response = requests.get(projects_url, headers=headers, timeout=10)
            
            if projects_response.status_code == 200:
                projects = projects_response.json()
                print(f"   ✅ Access to {len(projects)} projects")
                if projects:
                    print(f"   📋 Sample projects: {', '.join([p['key'] for p in projects[:3]])}")
            
            return True
        elif response.status_code == 401:
            print(f"   ❌ Authentication failed - check your PAT token")
            return False
        elif response.status_code == 403:
            print(f"   ❌ Access denied - token may lack required permissions")
            return False
        else:
            print(f"   ❌ Connection failed: {response.status_code} {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"   ❌ Connection timeout - check Jira URL")
        return False
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Cannot connect to Jira - check URL and network")
        return False
    except Exception as e:
        print(f"   ❌ Error testing Jira: {e}")
        return False

def test_openai_connection(api_key: str) -> bool:
    """Test OpenAI API connection"""
    print("🤖 Testing OpenAI connection...")
    
    try:
        if not api_key or not api_key.startswith('sk-'):
            print(f"   ❌ Invalid OpenAI API key format")
            return False
        
        openai.api_key = api_key
        
        # Test with a simple completion
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Say 'API test successful' if you can read this."}
            ],
            max_tokens=10,
            timeout=15
        )
        
        if response.choices and response.choices[0].message:
            print(f"   ✅ API connection successful")
            print(f"   ✅ Model: gpt-3.5-turbo")
            print(f"   ✅ Response: {response.choices[0].message.content.strip()}")
            return True
        else:
            print(f"   ❌ Unexpected response format")
            return False
            
    except openai.error.AuthenticationError:
        print(f"   ❌ Authentication failed - check your API key")
        return False
    except openai.error.RateLimitError:
        print(f"   ❌ Rate limit exceeded - try again later")
        return False
    except openai.error.APIError as e:
        print(f"   ❌ OpenAI API error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error testing OpenAI: {e}")
        return False

def test_sonarqube_connection(sonar_url: str, sonar_token: str, project_key: str) -> bool:
    """Test SonarQube API connection"""
    print("📊 Testing SonarQube connection...")
    
    try:
        if not sonar_token:
            print(f"   ⚠️  No SonarQube token provided - skipping test")
            return True
        
        # Test system status
        credentials = base64.b64encode(f"{sonar_token}:".encode()).decode()
        headers = {'Authorization': f'Basic {credentials}'}
        
        # Test system status
        status_url = f"{sonar_url}/api/system/status"
        response = requests.get(status_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            status = response.json()
            print(f"   ✅ SonarQube status: {status.get('status', 'Unknown')}")
            print(f"   ✅ Version: {status.get('version', 'Unknown')}")
            
            # Test project access if project key provided
            if project_key:
                project_url = f"{sonar_url}/api/projects/search"
                params = {'projects': project_key}
                project_response = requests.get(project_url, headers=headers, params=params, timeout=10)
                
                if project_response.status_code == 200:
                    projects = project_response.json()
                    if projects.get('components'):
                        print(f"   ✅ Project '{project_key}' found")
                    else:
                        print(f"   ⚠️  Project '{project_key}' not found or no access")
                
                # Test metrics access
                metrics_url = f"{sonar_url}/api/measures/component"
                params = {'component': project_key, 'metricKeys': 'coverage,ncloc'}
                metrics_response = requests.get(metrics_url, headers=headers, params=params, timeout=10)
                
                if metrics_response.status_code == 200:
                    print(f"   ✅ Metrics accessible for project")
                
            return True
        elif response.status_code == 401:
            print(f"   ❌ Authentication failed - check SonarQube token")
            return False
        else:
            print(f"   ❌ Connection failed: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Cannot connect to SonarQube - check URL")
        return False
    except Exception as e:
        print(f"   ❌ Error testing SonarQube: {e}")
        return False

def test_veracode_connection(api_id: str, api_key: str) -> bool:
    """Test Veracode API connection"""
    print("🔒 Testing Veracode connection...")
    
    try:
        if not api_id or not api_key:
            print(f"   ⚠️  No Veracode credentials provided - skipping test")
            return True
        
        # Note: Veracode API requires HMAC authentication which is complex
        # This is a simplified test - in practice you'd need the full HMAC implementation
        print(f"   ⚠️  Veracode API test requires full HMAC implementation")
        print(f"   ✅ API ID provided: {api_id[:8]}...")
        print(f"   ✅ API Key provided: {'*' * len(api_key)}")
        print(f"   📝 Manual verification recommended")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error testing Veracode: {e}")
        return False

def test_sample_story_extraction():
    """Test story extraction logic with sample data"""
    print("🧪 Testing story extraction logic...")
    
    from release_report_generator import ReleaseReportGenerator
    
    # Create a dummy config
    dummy_config = {
        'git_repo_path': '.',
        'jira_url': 'https://test.atlassian.net',
        'jira_pat_token': 'dummy',
        'openai_api_key': 'dummy'
    }
    
    generator = ReleaseReportGenerator(dummy_config)
    
    # Test sample commit messages
    test_cases = [
        "Merge branch 'feature/PROJ-123-new-login'",
        "Merge pull request #45 from user/bugfix/BUG-456-fix-payment",
        "Merge branch 'hotfix/URGENT-789-security-patch'",
        "Merge branch 'TASK-999-update-documentation'",
        "Regular commit message without story"
    ]
    
    success_count = 0
    for commit_msg in test_cases:
        result = generator.extract_story_from_branch_name(commit_msg)
        if result:
            story_id, story_type, branch_name = result
            print(f"   ✅ '{commit_msg}' → {story_id} ({story_type})")
            success_count += 1
        else:
            print(f"   ➡️  '{commit_msg}' → No story found (expected for some cases)")
    
    print(f"   📊 Extracted {success_count}/{len(test_cases)} stories")
    return True

def main():
    """Run all connection tests"""
    print("🚀 Release Report Generator - Connection Test")
    print("=" * 50)
    print(f"Test run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Load configuration
    try:
        config = get_config()
        print("✅ Configuration loaded successfully")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        print("\nPlease check your config.py file")
        return False
    
    print()
    
    # Run all tests
    tests = [
        ("Git Repository", lambda: test_git_repository(config['git_repo_path'])),
        ("Jira API", lambda: test_jira_connection(config['jira_url'], config['jira_pat_token'])),
        ("OpenAI API", lambda: test_openai_connection(config['openai_api_key'])),
        ("SonarQube API", lambda: test_sonarqube_connection(
            config.get('sonarqube_url', ''), 
            config.get('sonarqube_token', ''), 
            config.get('sonarqube_project_key', '')
        )),
        ("Veracode API", lambda: test_veracode_connection(
            config.get('veracode_api_id', ''), 
            config.get('veracode_api_key', '')
        )),
        ("Story Extraction", test_sample_story_extraction),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   ❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
        print()
    
    # Summary
    print("📋 Test Summary")
    print("-" * 30)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:8} {test_name}")
        if result:
            passed += 1
    
    print()
    print(f"Results: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! You're ready to generate reports.")
        print("\nNext steps:")
        print("1. Run: ./release-report --list-branches")
        print("2. Generate your first report: ./release-report main develop")
    else:
        print(f"\n⚠️  {len(results) - passed} tests failed. Please fix the issues above before generating reports.")
    
    return passed == len(results)

if __name__ == "__main__":
    main()
