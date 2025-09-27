        
        # Generate table for each category
        for category in ['feature', 'bugfix', 'devdeploy', 'other']:
            tickets = categorized_tickets.get(category, {})
            if tickets:
                category_title = category.replace('_', ' ').title()
                category_icon = {'feature': '✨', 'bugfix': '🐛', 'devdeploy': '🚀', 'other': '📋'}.get(category, '📋')
                html += f"""
                <div class="category">
                    <h3>{category_icon} {category_title} ({len(tickets)} tickets)</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Ticket Key</th>
                                <th>Summary</th>
                                <th>Description</th>
                                <th>Status</th>
                                <th>Type</th>
                                <th>PR Author</th>
                                <th>Reviewers</th>
                                <th>PR Link</th>
                            </tr>
                        </thead>
                        <tbody>
                """
                
                for ticket, pr_info in sorted(tickets.items()):
                    details = ticket_details.get(ticket, {})
                    status = details.get('status', 'N/A')
                    status_class = 'status-todo'
                    if 'done' in status.lower() or 'closed' in status.lower():
                        status_class = 'status-done'
                    elif 'progress' in status.lower():
                        status_class = 'status-in-progress'
                    
                    description = details.get('description', 'N/A')
                    if len(description) > 200:
                        description = description[:200] + '...'
                    
                    reviewers_html = ''
                    for reviewer in pr_info.get('reviewers', []):
                        badge_class = 'reviewer-badge'
                        if reviewer['state'] == 'APPROVED':
                            badge_class += ' reviewer-approved'
                        reviewers_html += f'<span class="{badge_class}">{reviewer["name"]}</span>'
                    
                    if not reviewers_html:
                        reviewers_html = '<span style="color: #999;">No reviewers</span>'
                    
                    pr_link = 'N/A'
                    if pr_info.get('pr_number'):
                        pr_link = f'<a href="{pr_info["pr_url"]}" class="pr-link" target="_blank">#{pr_info["pr_number"]}</a>'
                    
                    html += f"""
                        <tr>
                            <td class="ticket-key">{ticket}</td>
                            <td class="summary">{details.get('summary', 'N/A')}</td>
                            <td class="description">{description}</td>
                            <td><span class="status {status_class}">{status}</span></td>
                            <td>{details.get('type', 'N/A')}</td>
                            <td>{pr_info.get('author', 'N/A')}</td>
                            <td>{reviewers_html}</td>
                            <td>{pr_link}</td>
                        </tr>
                    """
                
                html += """
                        </tbody>
                    </table>
                </div>
                """
        
        html += """
            </div>
        """
    
    html += """
            <div class="footer">
                <div class="footer-logo">AT&T</div>
                <p>CG Release Report Summary • Confidential</p>
                <p style="margin-top: 10px; font-size: 12px;">© 2025 AT&T Inc. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html#!/usr/bin/env python3
"""
Git Branch Merge Commit Jira Report Generator
Extracts Jira tickets from merge commits between two branches and generates HTML report
Supports multiple repositories with consolidated reporting and AI-powered summaries
"""

import re
import sys
import subprocess
from collections import defaultdict
from datetime import datetime
from typing import List, Dict, Set, Optional
import requests
from requests.auth import HTTPBasicAuth
import json
import argparse

# Jira Configuration
JIRA_URL = "https://your-domain.atlassian.net"
JIRA_EMAIL = "your-email@example.com"
JIRA_API_TOKEN = "your-api-token"

# GitHub Configuration
GITHUB_TOKEN = "your-github-token"
GITHUB_ORG = "your-org"

# Platform: 'github' or 'gitlab'
PLATFORM = "github"


def get_merge_commits_github(repo: str, branch1: str, branch2: str) -> List[Dict]:
    """Get all merge commits between two branches using GitHub API"""
    url = f"https://api.github.com/repos/{repo}/compare/{branch1}...{branch2}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        merge_commits = []
        for commit in data.get('commits', []):
            if len(commit['parents']) > 1:
                merge_commits.append({
                    'hash': commit['sha'],
                    'author': commit['commit']['author']['name'],
                    'author_email': commit['commit']['author']['email'],
                    'committer': commit['commit']['committer']['name'],
                    'subject': commit['commit']['message'].split('\n')[0],
                    'body': '\n'.join(commit['commit']['message'].split('\n')[1:]),
                    'html_url': commit['html_url'],
                    'repo': repo
                })
        
        return merge_commits
    except requests.exceptions.RequestException as e:
        print(f"Error fetching commits from GitHub repo {repo}: {e}")
        return []


def extract_pr_number(commit_message: str) -> Optional[int]:
    """Extract PR/MR number from commit message"""
    patterns = [
        r'#(\d+)',
        r'!\((\d+)\)',
        r'pull request #(\d+)',
        r'PR #(\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, commit_message, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def get_github_pr_details(repo: str, pr_number: int) -> Dict:
    """Get PR details from GitHub"""
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        pr_data = response.json()
        
        reviews_url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/reviews"
        reviews_response = requests.get(reviews_url, headers=headers)
        reviews_data = reviews_response.json() if reviews_response.status_code == 200 else []
        
        reviewers = []
        reviewer_dict = {}
        for review in reviews_data:
            username = review['user']['login']
            state = review['state']
            if username not in reviewer_dict or state == 'APPROVED':
                reviewer_dict[username] = state
        
        for username, state in reviewer_dict.items():
            reviewers.append({
                'name': username,
                'state': state
            })
        
        return {
            'pr_number': pr_number,
            'author': pr_data['user']['login'],
            'reviewers': reviewers,
            'title': pr_data['title'],
            'url': pr_data['html_url'],
            'created_at': pr_data['created_at'],
            'merged_at': pr_data.get('merged_at', 'N/A')
        }
    except Exception as e:
        print(f"Error fetching GitHub PR #{pr_number} from {repo}: {e}")
        return {
            'pr_number': pr_number,
            'author': 'Unknown',
            'reviewers': [],
            'title': 'N/A',
            'url': '#'
        }


def extract_ticket_from_branch(commit_message: str) -> tuple:
    """Extract Jira ticket number from commit message"""
    patterns = {
        'feature': r'feature/([A-Z]+-\d+)',
        'devdeploy': r'devdeploy/([A-Z]+-\d+)',
        'bugfix': r'bugfix/([A-Z]+-\d+)',
    }
    
    for category, pattern in patterns.items():
        match = re.search(pattern, commit_message, re.IGNORECASE)
        if match:
            return match.group(1).upper(), category
    
    generic_pattern = r'([A-Z]+-\d+)'
    match = re.search(generic_pattern, commit_message, re.IGNORECASE)
    if match:
        return match.group(1).upper(), 'other'
    
    return None, None


def categorize_tickets(commits: List[Dict]) -> Dict[str, Dict]:
    """Categorize unique tickets from merge commits with PR details"""
    categories = defaultdict(dict)
    
    for commit in commits:
        full_message = f"{commit['subject']} {commit['body']}"
        ticket, category = extract_ticket_from_branch(full_message)
        
        if ticket and category:
            pr_number = extract_pr_number(full_message)
            pr_details = None
            
            if pr_number:
                if PLATFORM == 'github':
                    pr_details = get_github_pr_details(commit['repo'], pr_number)
            
            if ticket not in categories[category]:
                categories[category][ticket] = {
                    'author': pr_details['author'] if pr_details else commit['author'],
                    'reviewers': pr_details['reviewers'] if pr_details else [],
                    'pr_number': pr_number,
                    'pr_url': pr_details['url'] if pr_details else commit.get('html_url', '#'),
                    'pr_title': pr_details['title'] if pr_details else commit['subject'],
                    'commit_hash': commit['hash'][:8],
                    'repo': commit['repo']
                }
    
    return categories


def get_jira_ticket_details(tickets: List[str]) -> List[Dict]:
    """Fetch ticket details from Jira including description and acceptance criteria"""
    if not tickets:
        return []
    
    ticket_list = ','.join(tickets)
    jql = f"key in ({ticket_list})"
    
    url = f"{JIRA_URL}/rest/api/3/search"
    
    auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    params = {
        "jql": jql,
        "fields": "summary,status,assignee,priority,issuetype,created,updated,reporter,description",
        "maxResults": 100
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, auth=auth)
        response.raise_for_status()
        data = response.json()
        
        ticket_details = []
        for issue in data.get('issues', []):
            fields = issue['fields']
            
            # Extract description
            description = ""
            if fields.get('description'):
                description = extract_text_from_adf(fields['description'])
            
            # Extract acceptance criteria (usually in description or custom field)
            acceptance_criteria = extract_acceptance_criteria(fields.get('description', {}))
            
            ticket_details.append({
                'key': issue['key'],
                'summary': fields.get('summary', 'N/A'),
                'status': fields.get('status', {}).get('name', 'N/A'),
                'assignee': fields.get('assignee', {}).get('displayName', 'Unassigned') if fields.get('assignee') else 'Unassigned',
                'priority': fields.get('priority', {}).get('name', 'N/A'),
                'type': fields.get('issuetype', {}).get('name', 'N/A'),
                'created': fields.get('created', 'N/A'),
                'updated': fields.get('updated', 'N/A'),
                'reporter': fields.get('reporter', {}).get('displayName', 'N/A') if fields.get('reporter') else 'N/A',
                'description': description,
                'acceptance_criteria': acceptance_criteria
            })
        
        return ticket_details
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Jira details: {e}")
        return []


def extract_text_from_adf(adf_content: dict) -> str:
    """Extract plain text from Atlassian Document Format (ADF)"""
    if not adf_content:
        return ""
    
    text_parts = []
    
    def traverse(node):
        if isinstance(node, dict):
            if node.get('type') == 'text':
                text_parts.append(node.get('text', ''))
            if 'content' in node:
                for child in node['content']:
                    traverse(child)
        elif isinstance(node, list):
            for item in node:
                traverse(item)
    
    traverse(adf_content)
    return ' '.join(text_parts).strip()


def extract_acceptance_criteria(description: dict) -> str:
    """Extract acceptance criteria from Jira description"""
    text = extract_text_from_adf(description)
    
    # Look for common acceptance criteria patterns
    patterns = [
        r'Acceptance Criteria[:\s]*(.*?)(?=\n\n|\Z)',
        r'AC[:\s]*(.*?)(?=\n\n|\Z)',
        r'Criteria[:\s]*(.*?)(?=\n\n|\Z)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
    
    return ""


def generate_copilot_prompt_for_repo(repo: str, tickets_data: List[Dict]) -> str:
    """Generate GitHub Copilot CLI prompt for repository summary"""
    prompt = f"""Analyze the following Jira tickets for repository '{repo}' and provide a high-level technical summary:

Repository: {repo}

Tickets:
"""
    
    for ticket in tickets_data:
        prompt += f"""
Ticket: {ticket['key']}
Summary: {ticket['summary']}
Type: {ticket['type']}
Description: {ticket['description'][:500]}...
Acceptance Criteria: {ticket['acceptance_criteria'][:300]}...

"""
    
    prompt += """
Please provide:
1. A concise high-level summary (2-3 sentences) of what changed in this microservice
2. Key technical impacts and areas affected
3. Any notable integrations or dependencies mentioned

Format as a brief technical summary suitable for a release report.
"""
    
    return prompt


def generate_copilot_prompt_consolidated(all_repo_data: List[Dict]) -> str:
    """Generate GitHub Copilot CLI prompt for consolidated summary"""
    prompt = """Analyze the following changes across multiple microservices and provide a consolidated executive summary:

"""
    
    for repo_data in all_repo_data:
        repo = repo_data['repo']
        tickets = [repo_data['ticket_details'][key] for key in repo_data['all_tickets'] 
                  if key in repo_data['ticket_details']]
        
        prompt += f"\n--- Repository: {repo} ---\n"
        for ticket in tickets[:5]:  # Limit to first 5 per repo
            prompt += f"""
{ticket['key']}: {ticket['summary']}
Type: {ticket['type']} | Priority: {ticket['priority']}
Description: {ticket['description'][:300]}...

"""
    
    prompt += """
Please provide:
1. Executive Summary (3-4 sentences): What was delivered across all services?
2. Impact Overview: Which microservices/areas were affected and how?
3. Key Features/Fixes: Highlight the most important changes
4. Technical Dependencies: Any cross-service impacts or integrations

Format as a professional release summary suitable for stakeholders.
"""
    
    return prompt


def call_copilot_cli(prompt: str) -> str:
    """Call GitHub Copilot CLI to generate summary"""
    try:
        # Using gh copilot suggest for text generation
        result = subprocess.run(
            ['gh', 'copilot', 'suggest', '-t', 'shell'],
            input=f"echo '{prompt}'",
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return "⚠️ Could not generate AI summary. Please ensure GitHub Copilot CLI is installed and configured."
    
    except FileNotFoundError:
        return "⚠️ GitHub Copilot CLI not found. Install with: gh extension install github/gh-copilot"
    except subprocess.TimeoutExpired:
        return "⚠️ Copilot CLI timed out"
    except Exception as e:
        return f"⚠️ Error calling Copilot CLI: {str(e)}"


def generate_consolidated_html_report(all_repo_data: List[Dict], branch1: str, branch2: str, 
                                      enable_ai_summary: bool = False,
                                      consolidated_summary: str = "",
                                      repo_summaries: Dict[str, str] = {}) -> str:
    """Generate consolidated HTML report for multiple repositories"""
    
    current_time = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    
    total_tickets = sum(len(data['categorized_tickets'].get(cat, {})) 
                       for data in all_repo_data 
                       for cat in ['feature', 'bugfix', 'devdeploy', 'other'])
    
    total_features = sum(len(data['categorized_tickets'].get('feature', {})) for data in all_repo_data)
    total_bugfixes = sum(len(data['categorized_tickets'].get('bugfix', {})) for data in all_repo_data)
    total_devdeploys = sum(len(data['categorized_tickets'].get('devdeploy', {})) for data in all_repo_data)
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CG Release Report Summary - AT&T</title>
        <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
                padding: 20px;
                color: #333;
            }}
            
            .container {{
                max-width: 1400px;
                margin: 0 auto;
            }}
            
            .header {{
                background: linear-gradient(135deg, #00A8E1 0%, #0057B8 100%);
                color: white;
                padding: 40px;
                border-radius: 12px;
                margin-bottom: 30px;
                box-shadow: 0 8px 24px rgba(0, 87, 184, 0.3);
                position: relative;
                overflow: hidden;
            }}
            
            .header::before {{
                content: '';
                position: absolute;
                top: -50%;
                right: -10%;
                width: 500px;
                height: 500px;
                background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
                border-radius: 50%;
            }}
            
            .header-content {{
                position: relative;
                z-index: 1;
            }}
            
            .logo-section {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 20px;
            }}
            
            .att-logo {{
                width: 120px;
                height: 60px;
                background: white;
                border-radius: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 700;
                font-size: 32px;
                color: #0057B8;
                letter-spacing: -1px;
            }}
            
            .report-title {{
                text-align: center;
                flex: 1;
                margin: 0 20px;
            }}
            
            .report-title h1 {{
                font-size: 36px;
                font-weight: 300;
                margin-bottom: 8px;
                letter-spacing: -0.5px;
            }}
            
            .report-title .subtitle {{
                font-size: 16px;
                opacity: 0.9;
                font-weight: 300;
            }}
            
            .header-meta {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 20px;
                margin-top: 25px;
                padding-top: 25px;
                border-top: 1px solid rgba(255, 255, 255, 0.2);
            }}
            
            .meta-item {{
                text-align: center;
            }}
            
            .meta-label {{
                font-size: 12px;
                opacity: 0.8;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 5px;
            }}
            
            .meta-value {{
                font-size: 18px;
                font-weight: 500;
            }}
            
            .ai-summary {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 35px;
                border-radius: 12px;
                margin-bottom: 30px;
                box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3);
            }}
            
            .ai-summary h2 {{
                font-size: 24px;
                font-weight: 400;
                margin-bottom: 20px;
                display: flex;
                align-items: center;
                gap: 12px;
            }}
            
            .ai-icon {{
                width: 32px;
                height: 32px;
                background: rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 18px;
            }}
            
            .ai-summary-content {{
                line-height: 1.8;
                font-size: 15px;
                opacity: 0.95;
            }}
            
            .stats {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            
            .stat-box {{
                background: white;
                padding: 30px;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
                border-left: 4px solid #00A8E1;
                transition: transform 0.2s, box-shadow 0.2s;
            }}
            
            .stat-box:hover {{
                transform: translateY(-4px);
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
            }}
            
            .stat-number {{
                font-size: 42px;
                font-weight: 700;
                background: linear-gradient(135deg, #00A8E1 0%, #0057B8 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                margin-bottom: 8px;
            }}
            
            .stat-label {{
                color: #666;
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                font-weight: 500;
            }}
            
            .repo-section {{
                background: white;
                padding: 35px;
                border-radius: 12px;
                margin-bottom: 30px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
            }}
            
            .repo-header {{
                background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
                color: white;
                padding: 25px;
                border-radius: 10px;
                margin-bottom: 25px;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }}
            
            .repo-header h2 {{
                font-size: 24px;
                font-weight: 400;
                display: flex;
                align-items: center;
                gap: 12px;
            }}
            
            .repo-badge {{
                background: rgba(255, 255, 255, 0.2);
                padding: 6px 16px;
                border-radius: 20px;
                font-size: 14px;
            }}
            
            .repo-ai-summary {{
                background: #f8f9fa;
                padding: 25px;
                border-radius: 10px;
                margin-bottom: 25px;
                border-left: 4px solid #667eea;
            }}
            
            .repo-ai-summary h4 {{
                color: #2c3e50;
                font-size: 18px;
                font-weight: 500;
                margin-bottom: 15px;
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            
            .repo-ai-summary p {{
                line-height: 1.7;
                color: #555;
                margin-bottom: 12px;
            }}
            
            .category {{
                margin-bottom: 35px;
            }}
            
            .category h3 {{
                color: #0057B8;
                font-size: 20px;
                font-weight: 500;
                padding-bottom: 12px;
                margin-bottom: 20px;
                border-bottom: 3px solid #00A8E1;
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            
            table {{
                width: 100%;
                border-collapse: separate;
                border-spacing: 0;
                font-size: 14px;
                margin-top: 15px;
            }}
            
            th {{
                background: linear-gradient(135deg, #0057B8 0%, #003d82 100%);
                color: white;
                padding: 16px 12px;
                text-align: left;
                font-weight: 500;
                text-transform: uppercase;
                font-size: 12px;
                letter-spacing: 0.5px;
            }}
            
            th:first-child {{
                border-radius: 8px 0 0 0;
            }}
            
            th:last-child {{
                border-radius: 0 8px 0 0;
            }}
            
            td {{
                padding: 16px 12px;
                border-bottom: 1px solid #e8ecf1;
                vertical-align: top;
            }}
            
            tr:last-child td {{
                border-bottom: none;
            }}
            
            tr:hover {{
                background-color: #f8f9fa;
            }}
            
            .ticket-key {{
                font-weight: 600;
                color: #0057B8;
                font-size: 15px;
            }}
            
            .status {{
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 11px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                white-space: nowrap;
            }}
            
            .status-done {{
                background-color: #d4edda;
                color: #155724;
            }}
            
            .status-in-progress {{
                background-color: #cce5ff;
                color: #004085;
            }}
            
            .status-todo {{
                background-color: #f8d7da;
                color: #721c24;
            }}
            
            .summary {{
                max-width: 280px;
                word-wrap: break-word;
                font-weight: 500;
                color: #2c3e50;
            }}
            
            .description {{
                max-width: 350px;
                word-wrap: break-word;
                font-size: 13px;
                color: #666;
                line-height: 1.5;
            }}
            
            .pr-link {{
                color: #00A8E1;
                text-decoration: none;
                font-weight: 500;
                transition: color 0.2s;
            }}
            
            .pr-link:hover {{
                color: #0057B8;
                text-decoration: underline;
            }}
            
            .reviewer-badge {{
                display: inline-block;
                background-color: #e3f2fd;
                color: #1565c0;
                padding: 4px 10px;
                border-radius: 12px;
                margin: 2px;
                font-size: 11px;
                font-weight: 500;
            }}
            
            .reviewer-approved {{
                background-color: #e8f5e9;
                color: #2e7d32;
            }}
            
            .footer {{
                text-align: center;
                padding: 30px;
                color: #666;
                font-size: 13px;
                margin-top: 40px;
                border-top: 1px solid #e0e0e0;
            }}
            
            .footer-logo {{
                width: 80px;
                height: 40px;
                background: #0057B8;
                color: white;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                border-radius: 6px;
                font-weight: 700;
                font-size: 20px;
                margin-bottom: 10px;
            }}
            
            @media print {{
                body {{
                    background: white;
                }}
                .stat-box, .repo-section {{
                    box-shadow: none;
                    border: 1px solid #e0e0e0;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="header-content">
                    <div class="logo-section">
                        <div class="att-logo">AT&T</div>
                        <div class="report-title">
                            <h1>CG Release Report Summary</h1>
                            <div class="subtitle">Comprehensive Release Analysis & Impact Assessment</div>
                        </div>
                        <div style="width: 120px;"></div>
                    </div>
                    <div class="header-meta">
                        <div class="meta-item">
                            <div class="meta-label">Branch Comparison</div>
                            <div class="meta-value">{branch1} → {branch2}</div>
                        </div>
                        <div class="meta-item">
                            <div class="meta-label">Repositories</div>
                            <div class="meta-value">{len(all_repo_data)} Services</div>
                        </div>
                        <div class="meta-item">
                            <div class="meta-label">Generated</div>
                            <div class="meta-value">{current_time}</div>
                        </div>
                    </div>
                </div>
            </div>
    """
    
    if enable_ai_summary and consolidated_summary:
        html += f"""
            <div class="ai-summary">
                <h2><span class="ai-icon">🤖</span>AI-Generated Executive Summary</h2>
                <div class="ai-summary-content">
                    {consolidated_summary.replace(chr(10), '<br>')}
                </div>
            </div>
        """
    
    html += f"""
            <div class="stats">
                <div class="stat-box">
                    <div class="stat-number">{total_tickets}</div>
                    <div class="stat-label">Total Tickets</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">{total_features}</div>
                    <div class="stat-label">Features</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">{total_bugfixes}</div>
                    <div class="stat-label">Bug Fixes</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">{total_devdeploys}</div>
                    <div class="stat-label">Dev Deploy</div>
                </div>
            </div>
    """
    
    # Generate sections for each repository
    for repo_data in all_repo_data:
        repo = repo_data['repo']
        categorized_tickets = repo_data['categorized_tickets']
        ticket_details = repo_data['ticket_details']
        
        repo_total = sum(len(tickets) for tickets in categorized_tickets.values())
        
        html += f"""
            <div class="repo-section">
                <div class="repo-header">
                    <h2>📦 {repo}</h2>
                    <span class="repo-badge">{repo_total} tickets</span>
                </div>
        """
        
        if enable_ai_summary and repo in repo_summaries:
            html += f"""
                <div class="repo-ai-summary">
                    <h4>🤖 AI Summary for {repo}</h4>
                    <p>{repo_summaries[repo].replace(chr(10), '<br>')}</p>
                </div>
            """
        
        # Generate table for each category
        for category in ['feature', 'bugfix', 'devdeploy', 'other']:
            tickets = categorized_tickets.get(category, {})
            if tickets:
                category_title = category.replace('_', ' ').title()
                html += f"""
            <div class="category">
                <h3>🏷️ {category_title} ({len(tickets)} tickets)</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Ticket Key</th>
                            <th>Summary</th>
                            <th>Description</th>
                            <th>Status</th>
                            <th>Type</th>
                            <th>PR Author</th>
                            <th>Reviewers</th>
                            <th>PR Link</th>
                        </tr>
                    </thead>
                    <tbody>
                """
                
                for ticket, pr_info in sorted(tickets.items()):
                    details = ticket_details.get(ticket, {})
                    status = details.get('status', 'N/A')
                    status_class = 'status-todo'
                    if 'done' in status.lower() or 'closed' in status.lower():
                        status_class = 'status-done'
                    elif 'progress' in status.lower():
                        status_class = 'status-in-progress'
                    
                    description = details.get('description', 'N/A')
                    if len(description) > 200:
                        description = description[:200] + '...'
                    
                    reviewers_html = ''
                    for reviewer in pr_info.get('reviewers', []):
                        badge_class = 'reviewer-badge'
                        if reviewer['state'] == 'APPROVED':
                            badge_class += ' reviewer-approved'
                        reviewers_html += f'<span class="{badge_class}">{reviewer["name"]}</span>'
                    
                    if not reviewers_html:
                        reviewers_html = '<span style="color: #999;">No reviewers</span>'
                    
                    pr_link = 'N/A'
                    if pr_info.get('pr_number'):
                        pr_link = f'<a href="{pr_info["pr_url"]}" class="pr-link" target="_blank">#{pr_info["pr_number"]}</a>'
                    
                    html += f"""
                        <tr>
                            <td class="ticket-key">{ticket}</td>
                            <td class="summary">{details.get('summary', 'N/A')}</td>
                            <td class="description">{description}</td>
                            <td><span class="status {status_class}">{status}</span></td>
                            <td>{details.get('type', 'N/A')}</td>
                            <td>{pr_info.get('author', 'N/A')}</td>
                            <td class="reviewers">{reviewers_html}</td>
                            <td>{pr_link}</td>
                        </tr>
                    """
                
                html += """
                    </tbody>
                </table>
            </div>
                """
        
        html += """
        </div>
        """
    
    html += """
    </body>
    </html>
    """
    
    return html


def process_repository(repo: str, branch1: str, branch2: str) -> Dict:
    """Process a single repository and return its data"""
    print(f"\n📦 Processing repository: {repo}")
    print(f"   Comparing {branch1} → {branch2}")
    
    merge_commits = get_merge_commits_github(repo, branch1, branch2)
    print(f"   ✅ Found {len(merge_commits)} merge commits")
    
    categorized_tickets = categorize_tickets(merge_commits)
    total_tickets = sum(len(tickets) for tickets in categorized_tickets.values())
    print(f"   📋 Extracted {total_tickets} unique tickets")
    
    all_tickets = []
    for tickets in categorized_tickets.values():
        all_tickets.extend(tickets.keys())
    
    return {
        'repo': repo,
        'categorized_tickets': categorized_tickets,
        'all_tickets': all_tickets
    }


def main():
    parser = argparse.ArgumentParser(
        description='Generate consolidated Jira report from Git merge commits',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Single repo:
    python script.py main develop owner/repo1
  
  Multiple repos:
    python script.py main develop owner/repo1 owner/repo2 owner/repo3
  
  With AI summaries:
    python script.py main develop owner/repo1 owner/repo2 --enable-ai-summary
        """
    )
    
    parser.add_argument('branch1', help='Base branch (e.g., main)')
    parser.add_argument('branch2', help='Compare branch (e.g., develop)')
    parser.add_argument('repos', nargs='+', help='Repository names (e.g., owner/repo)')
    parser.add_argument('--enable-ai-summary', action='store_true', 
                       help='Enable AI-powered summaries using GitHub Copilot CLI')
    
    args = parser.parse_args()
    
    branch1 = args.branch1
    branch2 = args.branch2
    repos = args.repos
    enable_ai = args.enable_ai_summary
    
    print(f"🔍 Analyzing {len(repos)} repository(ies) between {branch1} and {branch2}")
    print(f"   Platform: {PLATFORM.upper()}")
    if enable_ai:
        print(f"   AI Summary: ENABLED (using GitHub Copilot CLI)")
    
    # Process all repositories
    all_repo_data = []
    all_unique_tickets = set()
    
    for repo in repos:
        repo_data = process_repository(repo, branch1, branch2)
        all_repo_data.append(repo_data)
        all_unique_tickets.update(repo_data['all_tickets'])
    
    # Fetch Jira details
    print(f"\n🔗 Fetching Jira details for {len(all_unique_tickets)} unique tickets...")
    ticket_details_list = get_jira_ticket_details(list(all_unique_tickets))
    ticket_details = {ticket['key']: ticket for ticket in ticket_details_list}
    print(f"✅ Retrieved details for {len(ticket_details)} tickets")
    
    for repo_data in all_repo_data:
        repo_data['ticket_details'] = ticket_details
    
    # Generate AI summaries if enabled
    consolidated_summary = ""
    repo_summaries = {}
    
    if enable_ai:
        print(f"\n🤖 Generating AI summaries using GitHub Copilot CLI...")
        
        # Generate consolidated summary
        print(f"   Generating consolidated summary...")
        consolidated_prompt = generate_copilot_prompt_consolidated(all_repo_data)
        consolidated_summary = call_copilot_cli(consolidated_prompt)
        
        # Generate per-repo summaries
        for repo_data in all_repo_data:
            repo = repo_data['repo']
            print(f"   Generating summary for {repo}...")
            tickets = [ticket_details[key] for key in repo_data['all_tickets'] if key in ticket_details]
            repo_prompt = generate_copilot_prompt_for_repo(repo, tickets)
            repo_summaries[repo] = call_copilot_cli(repo_prompt)
        
        print(f"✅ AI summaries generated")
    
    # Generate HTML report
    print(f"\n📄 Generating consolidated HTML report...")
    html_report = generate_consolidated_html_report(
        all_repo_data, 
        branch1, 
        branch2, 
        enable_ai,
        consolidated_summary,
        repo_summaries
    )
    
    # Save report
    output_file = f"consolidated_jira_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_report)
    
    print(f"✨ Consolidated report generated successfully: {output_file}")
    print(f"\n📊 Summary:")
    print(f"   Total repositories: {len(repos)}")
    print(f"   Total unique tickets: {len(all_unique_tickets)}")
    for repo_data in all_repo_data:
        repo_total = sum(len(tickets) for tickets in repo_data['categorized_tickets'].values())
        print(f"   - {repo_data['repo']}: {repo_total} tickets")
    
    if enable_ai:
        print(f"\n🤖 AI summaries included in report")


if __name__ == "__main__":
    main()