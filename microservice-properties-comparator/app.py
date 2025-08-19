from flask import Flask, render_template, request, jsonify, send_file
import requests
import base64
import json
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from urllib.parse import quote
import os
import re
from datetime import datetime
import pandas as pd
from io import BytesIO

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Configuration
GITHUB_API_BASE = "https://api.github.com"
ENVIRONMENTS = ['dev', 'test', 'perf', 'prod']

class GitHubAPIPropertyComparator:
    def __init__(self, github_token=None):
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        
        if self.github_token:
            self.session.headers.update({
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            })
    
    def parse_repo_url(self, repo_url):
        """Extract owner and repo name from GitHub URL"""
        if 'github.com' in repo_url:
            parts = repo_url.replace('https://', '').replace('http://', '').split('/')
            if len(parts) >= 2:
                owner = parts[1]
                repo = parts[2].replace('.git', '')
                return owner, repo
        raise ValueError("Invalid GitHub repository URL")
    
    def get_file_content(self, owner, repo, file_path, branch='main'):
        """Get content of a specific file from GitHub API"""
        try:
            encoded_path = quote(file_path, safe='/')
            url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{encoded_path}"
            
            params = {'ref': branch}
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                file_data = response.json()
                if file_data.get('encoding') == 'base64':
                    content = base64.b64decode(file_data['content']).decode('utf-8')
                    return content
            elif response.status_code == 404:
                if branch == 'main':
                    return self.get_file_content(owner, repo, file_path, 'master')
                return None
            else:
                self.logger.error(f"Error fetching {file_path}: {response.status_code}")
                return None
        except Exception as e:
            self.logger.error(f"Exception fetching {file_path}: {e}")
            return None
    
    def get_directory_contents(self, owner, repo, dir_path, branch='main'):
        """Get list of files in a directory"""
        try:
            encoded_path = quote(dir_path, safe='/')
            url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{encoded_path}"
            
            params = {'ref': branch}
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                if branch == 'main':
                    return self.get_directory_contents(owner, repo, dir_path, 'master')
                return []
            else:
                return []
        except Exception as e:
            return []
    
    def parse_properties_content(self, content):
        """Parse properties file content"""
        properties = {}
        if not content:
            return properties
            
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                properties[key.strip()] = value.strip()
        return properties
    
    def analyze_security_issues(self, all_data):
        """Analyze properties for security issues"""
        security_issues = {
            'hardcoded_secrets': {},
            'insecure_protocols': {},
            'weak_configurations': {}
        }
        
        secret_patterns = {
            'password': r'(?i)password\s*=\s*(?!(\$\{|\%\{|env\.|System\.|<|null|""|\'\'|N/A))([^\s]+)',
            'secret': r'(?i)secret\s*=\s*(?!(\$\{|\%\{|env\.|System\.|<|null|""|\'\'|N/A))([^\s]+)',
            'key': r'(?i)(api[-_]?key|private[-_]?key|access[-_]?key)\s*=\s*(?!(\$\{|\%\{|env\.|System\.|<|null|""|\'\'|N/A))([^\s]+)',
            'token': r'(?i)token\s*=\s*(?!(\$\{|\%\{|env\.|System\.|<|null|""|\'\'|N/A))([^\s]+)',
        }
        
        insecure_patterns = {
            'http_urls': r'(?i)(url|endpoint|host)\s*=\s*(http://[^\s]+)',
            'unencrypted_db': r'(?i)(database\.url|db\.url|datasource\.url)\s*=\s*(jdbc:[^:]+://[^/]+/[^?]*(?!\?.*ssl))',
        }
        
        weak_patterns = {
            'ssl_disabled': r'(?i)(ssl\.enabled|tls\.enabled|secure)\s*=\s*(false|no|0)',
            'debug_enabled': r'(?i)(debug|dev\.mode)\s*=\s*(true|yes|1)',
        }
        
        for ms_name, ms_data in all_data.items():
            for env_type, configs in ms_data.items():
                for config_name, properties in configs.items():
                    env_config = f"{env_type}_{config_name}"
                    
                    for prop_key, prop_value in properties.items():
                        prop_line = f"{prop_key}={prop_value}"
                        
                        # Check patterns
                        for pattern_name, pattern in secret_patterns.items():
                            if re.search(pattern, prop_line):
                                if env_config not in security_issues['hardcoded_secrets']:
                                    security_issues['hardcoded_secrets'][env_config] = []
                                security_issues['hardcoded_secrets'][env_config].append({
                                    'microservice': ms_name,
                                    'property': prop_key,
                                    'value': prop_value,
                                    'issue_type': pattern_name,
                                    'severity': 'HIGH'
                                })
                        
                        for pattern_name, pattern in insecure_patterns.items():
                            if re.search(pattern, prop_line):
                                if env_config not in security_issues['insecure_protocols']:
                                    security_issues['insecure_protocols'][env_config] = []
                                security_issues['insecure_protocols'][env_config].append({
                                    'microservice': ms_name,
                                    'property': prop_key,
                                    'value': prop_value,
                                    'issue_type': pattern_name,
                                    'severity': 'MEDIUM'
                                })
                        
                        for pattern_name, pattern in weak_patterns.items():
                            if re.search(pattern, prop_line):
                                if env_config not in security_issues['weak_configurations']:
                                    security_issues['weak_configurations'][env_config] = []
                                severity = 'LOW' if pattern_name == 'debug_enabled' and 'dev' in env_type else 'MEDIUM'
                                security_issues['weak_configurations'][env_config].append({
                                    'microservice': ms_name,
                                    'property': prop_key,
                                    'value': prop_value,
                                    'issue_type': pattern_name,
                                    'severity': severity
                                })
        
        return security_issues
    
    def scan_microservice_templates(self, owner, repo, microservice_name, branch='main'):
        """Scan templates folder for a specific microservice"""
        microservice_data = {}
        templates_path = f"{microservice_name}/templates"
        
        env_folders = self.get_directory_contents(owner, repo, templates_path, branch)
        
        if not env_folders:
            return microservice_data
        
        for env_folder in env_folders:
            if env_folder['type'] == 'dir':
                env_name = env_folder['name'].lower()
                env_path = f"{templates_path}/{env_folder['name']}"
                
                env_files = self.get_directory_contents(owner, repo, env_path, branch)
                microservice_data[env_name] = {}
                
                for file_info in env_files:
                    if file_info['type'] == 'file' and file_info['name'].endswith('.properties'):
                        file_path = f"{env_path}/{file_info['name']}"
                        content = self.get_file_content(owner, repo, file_path, branch)
                        
                        if content:
                            env_id = file_info['name'].replace('.properties', '')
                            properties = self.parse_properties_content(content)
                            microservice_data[env_name][env_id] = properties
        
        return microservice_data
    
    def scan_selected_microservices(self, repo_url, microservice_list, branch='main'):
        """Scan only the specified microservices"""
        try:
            owner, repo = self.parse_repo_url(repo_url)
            all_data = {}
            
            def scan_single_microservice(ms_name):
                return ms_name, self.scan_microservice_templates(owner, repo, ms_name, branch)
            
            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_microservice = {
                    executor.submit(scan_single_microservice, ms_name): ms_name 
                    for ms_name in microservice_list
                }
                
                for future in as_completed(future_to_microservice):
                    ms_name, ms_data = future.result()
                    if ms_data:
                        all_data[ms_name] = ms_data
            
            return all_data
        except Exception as e:
            raise e
    
    def compare_environments(self, all_data):
        """Compare properties across microservices for each environment"""
        comparison_results = {}
        
        all_env_configs = set()
        for microservice_data in all_data.values():
            for env_type, configs in microservice_data.items():
                for config_name in configs.keys():
                    all_env_configs.add(f"{env_type}_{config_name}")
        
        for env_config in all_env_configs:
            env_type, config_name = env_config.split('_', 1)
            
            env_properties = defaultdict(dict)
            microservices_in_env = []
            
            for ms_name, ms_data in all_data.items():
                if env_type in ms_data and config_name in ms_data[env_type]:
                    microservices_in_env.append(ms_name)
                    properties = ms_data[env_type][config_name]
                    
                    for key, value in properties.items():
                        env_properties[key][ms_name] = value
            
            if len(microservices_in_env) < 2:
                continue
            
            matching_properties = {}
            mismatched_properties = {}
            
            for prop_key, ms_values in env_properties.items():
                unique_values = set(ms_values.values())
                if len(unique_values) == 1:
                    matching_properties[prop_key] = ms_values
                else:
                    mismatched_properties[prop_key] = ms_values
            
            comparison_results[env_config] = {
                'microservices': microservices_in_env,
                'matching': matching_properties,
                'mismatched': mismatched_properties,
                'total_properties': len(env_properties),
                'matched_count': len(matching_properties),
                'mismatched_count': len(mismatched_properties)
            }
        
        return comparison_results

# Initialize the comparator
comparator = GitHubAPIPropertyComparator()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/scan', methods=['POST'])
def scan_properties():
    """Scan specific microservices and return comparison results"""
    try:
        data = request.get_json()
        repo_url = data.get('repo_url')
        microservice_list = data.get('microservices', [])
        github_token = data.get('github_token')
        branch = data.get('branch', 'main')
        
        if not repo_url:
            return jsonify({'error': 'Repository URL is required'}), 400
        
        if not microservice_list:
            return jsonify({'error': 'Microservice list is required'}), 400
        
        if github_token:
            global comparator
            comparator = GitHubAPIPropertyComparator(github_token)
        
        all_data = comparator.scan_selected_microservices(repo_url, microservice_list, branch)
        
        if not all_data:
            return jsonify({'error': 'No data found for the specified microservices'}), 404
        
        comparison_results = comparator.compare_environments(all_data)
        security_issues = comparator.analyze_security_issues(all_data)
        
        return jsonify({
            'success': True,
            'scanned_microservices': list(all_data.keys()),
            'requested_microservices': microservice_list,
            'microservices_count': len(all_data),
            'environments': list(comparison_results.keys()),
            'comparison_results': comparison_results,
            'security_analysis': security_issues,
            'summary': {
                'total_environments': len(comparison_results),
                'total_mismatches': sum(env['mismatched_count'] for env in comparison_results.values()),
                'total_matches': sum(env['matched_count'] for env in comparison_results.values()),
                'security_issues_count': {
                    'hardcoded_secrets': sum(len(issues) for issues in security_issues['hardcoded_secrets'].values()),
                    'insecure_protocols': sum(len(issues) for issues in security_issues['insecure_protocols'].values()),
                    'weak_configurations': sum(len(issues) for issues in security_issues['weak_configurations'].values())
                }
            }
        })
        
    except Exception as e:
        app.logger.error(f"Error in scan_properties: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/discover-microservices', methods=['POST'])
def discover_microservices():
    """Discover available microservices in the repository"""
    try:
        data = request.get_json()
        repo_url = data.get('repo_url')
        github_token = data.get('github_token')
        branch = data.get('branch', 'main')
        
        if not repo_url:
            return jsonify({'error': 'Repository URL is required'}), 400
        
        if github_token:
            temp_comparator = GitHubAPIPropertyComparator(github_token)
        else:
            temp_comparator = comparator
        
        owner, repo = temp_comparator.parse_repo_url(repo_url)
        root_contents = temp_comparator.get_directory_contents(owner, repo, '', branch)
        
        microservices = []
        for item in root_contents:
            if item['type'] == 'dir':
                templates_exists = temp_comparator.get_directory_contents(
                    owner, repo, f"{item['name']}/templates", branch
                )
                if templates_exists:
                    microservices.append(item['name'])
        
        return jsonify({
            'success': True,
            'microservices': sorted(microservices),
            'count': len(microservices)
        })
        
    except Exception as e:
        app.logger.error(f"Error in discover_microservices: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/preview-microservice', methods=['POST'])
def preview_microservice():
    """Preview the structure of a specific microservice"""
    try:
        data = request.get_json()
        repo_url = data.get('repo_url')
        microservice_name = data.get('microservice_name')
        github_token = data.get('github_token')
        branch = data.get('branch', 'main')
        
        if not repo_url or not microservice_name:
            return jsonify({'error': 'Repository URL and microservice name are required'}), 400
        
        if github_token:
            temp_comparator = GitHubAPIPropertyComparator(github_token)
        else:
            temp_comparator = comparator
        
        owner, repo = temp_comparator.parse_repo_url(repo_url)
        templates_path = f"{microservice_name}/templates"
        structure = {}
        
        env_folders = temp_comparator.get_directory_contents(owner, repo, templates_path, branch)
        
        for env_folder in env_folders:
            if env_folder['type'] == 'dir':
                env_name = env_folder['name']
                env_path = f"{templates_path}/{env_name}"
                
                env_files = temp_comparator.get_directory_contents(owner, repo, env_path, branch)
                properties_files = [
                    f['name'] for f in env_files 
                    if f['type'] == 'file' and f['name'].endswith('.properties')
                ]
                structure[env_name] = properties_files
        
        return jsonify({
            'success': True,
            'microservice': microservice_name,
            'structure': structure
        })
        
    except Exception as e:
        app.logger.error(f"Error in preview_microservice: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/excel', methods=['POST'])
def export_excel():
    """Export comparison results to Excel"""
    try:
        data = request.get_json()
        if not data or 'comparison_results' not in data:
            return jsonify({'error': 'No comparison data provided'}), 400
        
        comparison_results = data['comparison_results']
        security_issues = data.get('security_analysis', {})
        
        output = BytesIO()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Security summary
            if security_issues:
                create_security_sheet(writer, security_issues)
            
            # Summary sheet
            summary_data = []
            for env_config, env_data in comparison_results.items():
                env_security_count = 0
                for issue_type in security_issues.values():
                    if env_config in issue_type:
                        env_security_count += len(issue_type[env_config])
                
                summary_data.append({
                    'Environment': env_config,
                    'Microservices': len(env_data['microservices']),
                    'Total Properties': env_data['total_properties'],
                    'Matched': env_data['matched_count'],
                    'Mismatched': env_data['mismatched_count'],
                    'Security Issues': env_security_count,
                    'Match %': f"{(env_data['matched_count'] / max(env_data['total_properties'], 1)) * 100:.1f}%"
                })
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Environment details
            for env_config, env_data in comparison_results.items():
                sheet_data = []
                microservices = env_data['microservices']
                
                all_properties = {**env_data['matching'], **env_data['mismatched']}
                for prop_key, ms_values in all_properties.items():
                    status = 'MATCH' if prop_key in env_data['matching'] else 'MISMATCH'
                    row = {'Property': prop_key, 'Status': status}
                    
                    for ms in microservices:
                        row[ms] = ms_values.get(ms, 'N/A')
                    sheet_data.append(row)
                
                if sheet_data:
                    df = pd.DataFrame(sheet_data)
                    sheet_name = env_config.replace('/', '_')[:31]
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'properties_comparison_{timestamp}.xlsx'
        )
        
    except Exception as e:
        app.logger.error(f"Error in export_excel: {e}")
        return jsonify({'error': str(e)}), 500

def create_security_sheet(writer, security_issues):
    """Create security analysis sheet"""
    security_data = []
    
    for issue_category, category_data in security_issues.items():
        if not category_data:
            continue
        category_name = issue_category.replace('_', ' ').title()
        for env, issues in category_data.items():
            for issue in issues:
                security_data.append({
                    'Environment': env,
                    'Microservice': issue['microservice'],
                    'Property': issue['property'],
                    'Issue_Category': category_name,
                    'Issue_Type': issue['issue_type'],
                    'Severity': issue['severity'],
                    'Value': mask_sensitive_value(issue['value'])
                })
    
    if security_data:
        security_df = pd.DataFrame(security_data)
        security_df.to_excel(writer, sheet_name='Security_Issues', index=False)

def mask_sensitive_value(value):
    """Mask sensitive values for export"""
    if len(value) > 8:
        return value[:4] + '*' * (len(value) - 8) + value[-4:]
    elif len(value) > 4:
        return value[:2] + '*' * (len(value) - 4) + value[-2:]
    else:
        return '*' * len(value)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    app.run(debug=debug, host='0.0.0.0', port=port)