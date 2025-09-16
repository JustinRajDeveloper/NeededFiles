#!/usr/bin/env python3
"""
Release Summary Report Generator
Compares two Git branches and generates a comprehensive executive report
"""

import os
import re
import json
import requests
import subprocess
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
import base64
from urllib.parse import quote
import openai
from jinja2 import Template

@dataclass
class StoryInfo:
    story_id: str
    story_type: str
    branch_name: str
    commit_hash: str
    jira_summary: str = ""
    jira_description: str = ""
    fix_version: str = ""
    fix_version_matches: bool = True
    impacted_resources: List[str] = None
    risk_level: str = "Unknown"
    
    def __post_init__(self):
        if self.impacted_resources is None:
            self.impacted_resources = []

@dataclass
class CoverageInfo:
    branch: str
    current_coverage: float = 0.0
    previous_coverage: float = 0.0
    coverage_delta: float = 0.0

@dataclass
class VulnerabilityInfo:
    severity: str
    count: int
    description: str = ""

class ReleaseReportGenerator:
    def __init__(self, config: Dict):
        """
        Initialize with configuration
        
        config should contain:
        - git_repo_path: Path to Git repository
        - jira_url: Jira instance URL
        - jira_pat_token: Jira Personal Access Token
        - openai_api_key: OpenAI API key
        - sonarqube_url: SonarQube instance URL
        - sonarqube_token: SonarQube token
        - veracode_api_id: Veracode API ID
        - veracode_api_key: Veracode API key
        - project_key: Project key for SonarQube
        """
        self.config = config
        self.stories: List[StoryInfo] = []
        
        # Initialize OpenAI
        openai.api_key = config.get('openai_api_key')
        
    def get_merge_commits_between_branches(self, base_branch: str, target_branch: str) -> List[Tuple[str, str]]:
        """Get all merge commits between two branches"""
        try:
            os.chdir(self.config['git_repo_path'])
            
            # Get merge commits
            cmd = f"git log --merges --pretty=format:'%H|%s' {base_branch}..{target_branch}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"Git command failed: {result.stderr}")
            
            merge_commits = []
            for line in result.stdout.strip().split('\n'):
                if line and '|' in line:
                    commit_hash, commit_message = line.split('|', 1)
                    merge_commits.append((commit_hash.strip(), commit_message.strip()))
            
            return merge_commits
            
        except Exception as e:
            print(f"Error getting merge commits: {e}")
            return []
    
    def extract_story_from_branch_name(self, commit_message: str) -> Optional[Tuple[str, str, str]]:
        """Extract story ID and type from commit message containing branch name"""
        
        # Common patterns for merge commit messages
        patterns = [
            r"Merge branch '([^']+)'",
            r"Merge pull request #\d+ from [^/]+/([^\s]+)",
            r"from ([^\s]+)",
        ]
        
        branch_name = None
        for pattern in patterns:
            match = re.search(pattern, commit_message)
            if match:
                branch_name = match.group(1)
                break
        
        if not branch_name:
            return None
        
        # Extract story information from branch name
        story_patterns = [
            (r'^feature/([a-zA-Z]+-\d+)', 'feature'),
            (r'^bugfix/([a-zA-Z]+-\d+)', 'bugfix'),
            (r'^hotfix/([a-zA-Z]+-\d+)', 'hotfix'),
            (r'^([a-zA-Z]+-\d+)', 'other'),  # Generic pattern
        ]
        
        for pattern, story_type in story_patterns:
            match = re.search(pattern, branch_name, re.IGNORECASE)
            if match:
                story_id = match.group(1).upper()
                return story_id, story_type, branch_name
        
        return None
    
    def get_jira_ticket_info(self, story_id: str) -> Dict:
        """Fetch ticket information from Jira"""
        try:
            url = f"{self.config['jira_url']}/rest/api/3/issue/{story_id}"
            headers = {
                'Authorization': f"Bearer {self.config['jira_pat_token']}",
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to fetch Jira ticket {story_id}: {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"Error fetching Jira ticket {story_id}: {e}")
            return {}
    
    def parse_jira_description(self, description: str) -> Tuple[List[str], str]:
        """Parse Jira description to extract impacted resources and risk level"""
        if not description:
            return [], "Unknown"
        
        impacted_resources = []
        risk_level = "Unknown"
        
        # Extract impacted resources (URLs/endpoints)
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        resources = re.findall(url_pattern, description)
        impacted_resources.extend(resources)
        
        # Extract API endpoints
        api_pattern = r'/(api|v\d+)/[^\s]+'
        apis = re.findall(api_pattern, description)
        impacted_resources.extend(apis)
        
        # Extract risk level
        risk_patterns = [
            r'Risk\s+level\s*[:\-]\s*(High|Medium|Low)',
            r'Risk\s*[:\-]\s*(High|Medium|Low)',
        ]
        
        for pattern in risk_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                risk_level = match.group(1).title()
                break
        
        return impacted_resources, risk_level
    
    def analyze_stories(self, base_branch: str, target_branch: str, target_version: str):
        """Analyze all stories between branches"""
        merge_commits = self.get_merge_commits_between_branches(base_branch, target_branch)
        
        for commit_hash, commit_message in merge_commits:
            story_info = self.extract_story_from_branch_name(commit_message)
            
            if story_info:
                story_id, story_type, branch_name = story_info
                
                # Create story object
                story = StoryInfo(
                    story_id=story_id,
                    story_type=story_type,
                    branch_name=branch_name,
                    commit_hash=commit_hash
                )
                
                # Fetch Jira information
                jira_data = self.get_jira_ticket_info(story_id)
                if jira_data:
                    fields = jira_data.get('fields', {})
                    
                    story.jira_summary = fields.get('summary', '')
                    story.jira_description = fields.get('description', {}).get('content', [{}])[0].get('content', [{}])[0].get('text', '') if fields.get('description') else ''
                    
                    # Get fix version
                    fix_versions = fields.get('fixVersions', [])
                    if fix_versions:
                        story.fix_version = fix_versions[0].get('name', '')
                        story.fix_version_matches = story.fix_version == target_version
                    
                    # Parse description for impacted resources and risk level
                    story.impacted_resources, story.risk_level = self.parse_jira_description(story.jira_description)
                
                self.stories.append(story)
    
    def get_openai_consolidation(self) -> str:
        """Use OpenAI to create a consolidated summary"""
        if not self.stories:
            return "No stories found for consolidation."
        
        # Prepare stories data for OpenAI
        stories_text = []
        for story in self.stories:
            story_text = f"""
Story: {story.story_id} ({story.story_type})
Summary: {story.jira_summary}
Description: {story.jira_description}
Impacted Resources: {', '.join(story.impacted_resources) if story.impacted_resources else 'None specified'}
Risk Level: {story.risk_level}
---
"""
            stories_text.append(story_text)
        
        prompt = f"""
Please analyze the following software release stories and provide a consolidated summary that includes:

1. Overall impacted resource endpoints (consolidate and deduplicate)
2. Overall risk level assessment (High/Medium/Low based on individual risks)
3. Key implementation highlights
4. Potential integration concerns

Stories:
{''.join(stories_text)}

Please provide a professional executive summary focusing on business impact and technical risks.
"""
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a technical lead preparing an executive summary for a software release."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error getting OpenAI consolidation: {e}")
            return "Failed to generate AI consolidation summary."
    
    def get_sonarqube_coverage(self, branch: str) -> CoverageInfo:
        """Get code coverage from SonarQube"""
        coverage_info = CoverageInfo(branch=branch)
        
        try:
            project_key = self.config['project_key']
            base_url = self.config['sonarqube_url']
            token = self.config['sonarqube_token']
            
            # Encode credentials
            credentials = base64.b64encode(f"{token}:".encode()).decode()
            headers = {'Authorization': f'Basic {credentials}'}
            
            # Get current coverage
            url = f"{base_url}/api/measures/component"
            params = {
                'component': project_key,
                'metricKeys': 'coverage',
                'branch': branch
            }
            
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                measures = data.get('component', {}).get('measures', [])
                if measures:
                    coverage_info.current_coverage = float(measures[0].get('value', 0))
            
            # Get historical coverage (approximation - you might need to adjust this based on your SonarQube setup)
            # This is a simplified approach - you might want to use the history API
            coverage_info.previous_coverage = coverage_info.current_coverage  # Placeholder
            coverage_info.coverage_delta = 0.0  # Placeholder
            
        except Exception as e:
            print(f"Error getting SonarQube coverage: {e}")
        
        return coverage_info
    
    def get_veracode_vulnerabilities(self) -> List[VulnerabilityInfo]:
        """Get vulnerability information from Veracode"""
        vulnerabilities = []
        
        try:
            # This is a simplified example - Veracode API is complex
            # You'll need to adapt this based on your specific Veracode setup
            api_id = self.config['veracode_api_id']
            api_key = self.config['veracode_api_key']
            
            # Placeholder implementation
            # In reality, you'd make calls to Veracode REST API
            vulnerabilities = [
                VulnerabilityInfo(severity="High", count=2, description="SQL Injection vulnerabilities"),
                VulnerabilityInfo(severity="Medium", count=5, description="Cross-site scripting issues"),
                VulnerabilityInfo(severity="Low", count=10, description="Information disclosure")
            ]
            
        except Exception as e:
            print(f"Error getting Veracode vulnerabilities: {e}")
        
        return vulnerabilities
    
    def generate_html_report(self, base_branch: str, target_branch: str, target_version: str) -> str:
        """Generate comprehensive HTML report"""
        
        # Get AI consolidation
        ai_summary = self.get_openai_consolidation()
        
        # Get coverage information
        coverage_info = self.get_sonarqube_coverage(target_branch)
        
        # Get vulnerability information
        vulnerabilities = self.get_veracode_vulnerabilities()
        
        # Calculate summary statistics
        total_stories = len(self.stories)
        fix_version_mismatches = sum(1 for s in self.stories if not s.fix_version_matches)
        risk_levels = {'High': 0, 'Medium': 0, 'Low': 0, 'Unknown': 0}
        for story in self.stories:
            risk_levels[story.risk_level] += 1
        
        story_types = {'feature': 0, 'bugfix': 0, 'hotfix': 0, 'other': 0}
        for story in self.stories:
            story_types[story.story_type] += 1
        
        # HTML template
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Release Summary Report</title>
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background-color: #f5f5f5; 
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            background-color: white; 
            padding: 30px; 
            border-radius: 10px; 
            box-shadow: 0 0 20px rgba(0,0,0,0.1); 
        }
        .header { 
            text-align: center; 
            margin-bottom: 40px; 
            padding-bottom: 20px; 
            border-bottom: 3px solid #2c3e50; 
        }
        .header h1 { 
            color: #2c3e50; 
            margin-bottom: 10px; 
        }
        .summary-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
            gap: 20px; 
            margin-bottom: 40px; 
        }
        .summary-card { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            padding: 20px; 
            border-radius: 10px; 
            text-align: center; 
        }
        .summary-card h3 { margin-top: 0; }
        .summary-card .number { font-size: 2em; font-weight: bold; }
        
        .section { 
            margin-bottom: 40px; 
            padding: 20px; 
            background-color: #fafafa; 
            border-radius: 8px; 
        }
        .section h2 { 
            color: #2c3e50; 
            border-bottom: 2px solid #3498db; 
            padding-bottom: 10px; 
        }
        
        .ai-summary { 
            background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%); 
            color: white; 
            padding: 25px; 
            border-radius: 10px; 
            margin-bottom: 30px; 
        }
        .ai-summary h2 { 
            margin-top: 0; 
            color: white; 
            border-bottom: 2px solid rgba(255,255,255,0.3); 
        }
        
        .story-table { 
            width: 100%; 
            border-collapse: collapse; 
            margin-top: 20px; 
        }
        .story-table th, .story-table td { 
            border: 1px solid #ddd; 
            padding: 12px; 
            text-align: left; 
        }
        .story-table th { 
            background-color: #34495e; 
            color: white; 
        }
        .story-table tr:nth-child(even) { background-color: #f2f2f2; }
        
        .risk-high { background-color: #e74c3c; color: white; }
        .risk-medium { background-color: #f39c12; color: white; }
        .risk-low { background-color: #27ae60; color: white; }
        .risk-unknown { background-color: #95a5a6; color: white; }
        
        .version-mismatch { background-color: #e74c3c; color: white; }
        .version-match { background-color: #27ae60; color: white; }
        
        .coverage-bar { 
            height: 25px; 
            background-color: #ecf0f1; 
            border-radius: 12px; 
            overflow: hidden; 
        }
        .coverage-fill { 
            height: 100%; 
            background: linear-gradient(90deg, #e74c3c, #f39c12, #27ae60); 
            transition: width 0.3s ease; 
        }
        
        .vulnerability-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 15px; 
        }
        .vulnerability-card { 
            padding: 15px; 
            border-radius: 8px; 
            text-align: center; 
            color: white; 
        }
        .vuln-high { background-color: #e74c3c; }
        .vuln-medium { background-color: #f39c12; }
        .vuln-low { background-color: #27ae60; }
        
        @media print {
            body { background-color: white; }
            .container { box-shadow: none; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Release Summary Report</h1>
            <p><strong>Release:</strong> {{ base_branch }} → {{ target_branch }} ({{ target_version }})</p>
            <p><strong>Generated:</strong> {{ generation_date }}</p>
        </div>
        
        <div class="summary-grid">
            <div class="summary-card">
                <h3>📊 Total Stories</h3>
                <div class="number">{{ total_stories }}</div>
            </div>
            <div class="summary-card">
                <h3>⚠️ Version Mismatches</h3>
                <div class="number">{{ fix_version_mismatches }}</div>
            </div>
            <div class="summary-card">
                <h3>🔥 High Risk Items</h3>
                <div class="number">{{ risk_levels.High }}</div>
            </div>
            <div class="summary-card">
                <h3>📈 Code Coverage</h3>
                <div class="number">{{ "%.1f"|format(coverage_info.current_coverage) }}%</div>
            </div>
        </div>
        
        <div class="ai-summary">
            <h2>🤖 AI-Generated Executive Summary</h2>
            <div style="white-space: pre-line; line-height: 1.6;">{{ ai_summary }}</div>
        </div>
        
        <div class="section">
            <h2>📋 Story Breakdown</h2>
            <div class="summary-grid">
                <div class="summary-card" style="background: linear-gradient(135deg, #55a3ff 0%, #003d82 100%);">
                    <h3>Features</h3>
                    <div class="number">{{ story_types.feature }}</div>
                </div>
                <div class="summary-card" style="background: linear-gradient(135deg, #ff6b6b 0%, #cc5500 100%);">
                    <h3>Bug Fixes</h3>
                    <div class="number">{{ story_types.bugfix }}</div>
                </div>
                <div class="summary-card" style="background: linear-gradient(135deg, #feca57 0%, #ff9ff3 100%);">
                    <h3>Hotfixes</h3>
                    <div class="number">{{ story_types.hotfix }}</div>
                </div>
                <div class="summary-card" style="background: linear-gradient(135deg, #48dbfb 0%, #0abde3 100%);">
                    <h3>Others</h3>
                    <div class="number">{{ story_types.other }}</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>🔍 Detailed Story Analysis</h2>
            <table class="story-table">
                <thead>
                    <tr>
                        <th>Story ID</th>
                        <th>Type</th>
                        <th>Summary</th>
                        <th>Risk Level</th>
                        <th>Fix Version</th>
                        <th>Version Match</th>
                        <th>Impacted Resources</th>
                    </tr>
                </thead>
                <tbody>
                    {% for story in stories %}
                    <tr>
                        <td><strong>{{ story.story_id }}</strong></td>
                        <td><span style="text-transform: capitalize;">{{ story.story_type }}</span></td>
                        <td>{{ story.jira_summary }}</td>
                        <td><span class="risk-{{ story.risk_level.lower() }}">{{ story.risk_level }}</span></td>
                        <td>{{ story.fix_version or 'Not Set' }}</td>
                        <td><span class="{{ 'version-match' if story.fix_version_matches else 'version-mismatch' }}">
                            {{ '✓' if story.fix_version_matches else '✗' }}
                        </span></td>
                        <td>{{ ', '.join(story.impacted_resources[:3]) }}{{ '...' if story.impacted_resources|length > 3 else '' }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2>📊 Code Coverage Analysis</h2>
            <p><strong>Branch:</strong> {{ coverage_info.branch }}</p>
            <div style="margin: 20px 0;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span>Current Coverage:</span>
                    <span><strong>{{ "%.1f"|format(coverage_info.current_coverage) }}%</strong></span>
                </div>
                <div class="coverage-bar">
                    <div class="coverage-fill" style="width: {{ coverage_info.current_coverage }}%;"></div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>🔒 Security Vulnerabilities</h2>
            <div class="vulnerability-grid">
                {% for vuln in vulnerabilities %}
                <div class="vulnerability-card vuln-{{ vuln.severity.lower() }}">
                    <h3>{{ vuln.severity }} Risk</h3>
                    <div class="number">{{ vuln.count }}</div>
                    <p>{{ vuln.description }}</p>
                </div>
                {% endfor %}
            </div>
        </div>
        
        <div class="section">
            <h2>⚠️ Recommendations</h2>
            <ul style="line-height: 1.8;">
                {% if fix_version_mismatches > 0 %}
                <li><strong>Fix Version Alignment:</strong> {{ fix_version_mismatches }} stories have mismatched fix versions that need attention.</li>
                {% endif %}
                {% if risk_levels.High > 0 %}
                <li><strong>High Risk Review:</strong> {{ risk_levels.High }} high-risk items require thorough testing and monitoring.</li>
                {% endif %}
                {% if coverage_info.current_coverage < 80 %}
                <li><strong>Coverage Improvement:</strong> Consider increasing test coverage above 80% for better reliability.</li>
                {% endif %}
                <li><strong>Security Review:</strong> Address all high and medium severity vulnerabilities before release.</li>
                <li><strong>Documentation:</strong> Ensure all impacted resources are properly documented for stakeholders.</li>
            </ul>
        </div>
        
        <div style="text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; color: #7f8c8d;">
            <p>Generated by Release Summary Report Tool | {{ generation_date }}</p>
        </div>
    </div>
</body>
</html>
"""
        
        # Render template
        template = Template(html_template)
        html_content = template.render(
            base_branch=base_branch,
            target_branch=target_branch,
            target_version=target_version,
            generation_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_stories=total_stories,
            fix_version_mismatches=fix_version_mismatches,
            risk_levels=risk_levels,
            story_types=story_types,
            ai_summary=ai_summary,
            coverage_info=coverage_info,
            vulnerabilities=vulnerabilities,
            stories=self.stories
        )
        
        return html_content
    
    def generate_report(self, base_branch: str, target_branch: str, target_version: str, output_file: str = "release_report.html"):
        """Main method to generate the complete report"""
        print("🔍 Analyzing stories between branches...")
        self.analyze_stories(base_branch, target_branch, target_version)
        
        print(f"📊 Found {len(self.stories)} stories")
        
        print("📝 Generating HTML report...")
        html_content = self.generate_html_report(base_branch, target_branch, target_version)
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Report generated: {output_file}")
        return output_file


# Example usage and configuration
def main():
    """Example usage of the Release Report Generator"""
    
    # Configuration
    config = {
        'git_repo_path': '/path/to/your/repo',
        'jira_url': 'https://your-company.atlassian.net',
        'jira_pat_token': 'your_jira_pat_token',
        'openai_api_key': 'your_openai_api_key',
        'sonarqube_url': 'https://your-sonarqube-instance.com',
        'sonarqube_token': 'your_sonarqube_token',
        'project_key': 'your_project_key',
        'veracode_api_id': 'your_veracode_api_id',
        'veracode_api_key': 'your_veracode_api_key'
    }
    
    # Initialize generator
    generator = ReleaseReportGenerator(config)
    
    # Generate report
    base_branch = "main"
    target_branch = "release/v2.1.0"
    target_version = "v2.1.0"
    
    generator.generate_report(base_branch, target_branch, target_version, "release_summary_v2.1.0.html")


if __name__ == "__main__":
    main()
