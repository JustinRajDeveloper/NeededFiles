from flask import Flask, render_template, request, jsonify, session
import sqlite3
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import json
import re
from base64 import b64encode

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def init_db():
    conn = sqlite3.connect('admin_tool.db')
    cursor = conn.cursor()

    # State changes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS state_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id TEXT,
            account_number TEXT,
            target_sor TEXT,
            from_state TEXT,
            to_state TEXT,
            status TEXT,
            response TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # RTB First Bill runs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rtb_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT UNIQUE,
            run_date DATE,
            presto_count INTEGER,
            cosmos_count INTEGER,
            matching_count INTEGER,
            mismatch_count INTEGER,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )
    ''')

    # RTB accounts details table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rtb_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT,
            account_number TEXT,
            source TEXT,
            match_status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (run_id) REFERENCES rtb_runs(run_id)
        )
    ''')

    # Index for faster queries
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_rtb_run_date ON rtb_runs(run_date)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_rtb_accounts_run_id ON rtb_accounts(run_id)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_rtb_accounts_match_status ON rtb_accounts(run_id, match_status)
    ''')

    # Release management cache table (temporary storage during session)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS release_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            release_version TEXT,
            scrum_team TEXT,
            component TEXT,
            jira_data TEXT,
            github_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Release branch audit trail
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS release_branches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            release_version TEXT,
            branch_name TEXT,
            created_from TEXT,
            scrum_team TEXT,
            component TEXT,
            created_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/team/<team_name>')
def team(team_name):
    return render_template('team.html', team=team_name)

@app.route('/category/<team_name>/<category>')
def category(team_name, category):
    return render_template('category.html', team=team_name, category=category)

@app.route('/tool/<team_name>/<category>/<tool>')
def tool(team_name, category, tool):
    return render_template('tool.html', team=team_name, category=category, tool=tool)

@app.route('/process_state_change', methods=['POST'])
def process_state_change():
    try:
        target_sor = request.form.get('target_sor')
        from_state = request.form.get('from_state')
        to_state = request.form.get('to_state')
        file = request.files.get('excel_file')
        
        if not file:
            return jsonify({'error': 'No file uploaded'}), 400
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        df = pd.read_excel(filepath)
        accounts = df['account_number'].tolist()
        
        batch_id = datetime.now().strftime('%Y%m%d%H%M%S')
        
        results = process_accounts_batch(accounts, target_sor, from_state, to_state, batch_id)
        
        os.remove(filepath)
        
        return jsonify({
            'success': True,
            'batch_id': batch_id,
            'total_accounts': len(accounts),
            'results': results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def process_accounts_batch(accounts, target_sor, from_state, to_state, batch_id):
    batch_size = 100
    max_workers = 5
    results = {'success': 0, 'failed': 0}
    
    for i in range(0, len(accounts), batch_size):
        batch = accounts[i:i + batch_size]
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for account in batch:
                future = executor.submit(
                    process_single_account,
                    account, target_sor, from_state, to_state, batch_id
                )
                futures.append(future)
            
            for future in futures:
                result = future.result()
                if result['status'] == 'success':
                    results['success'] += 1
                else:
                    results['failed'] += 1
    
    return results

def process_single_account(account, target_sor, from_state, to_state, batch_id):
    try:
        # Replace with your actual API endpoint
        # api_url = 'https://your-api-endpoint.com/state-change'
        # payload = {
        #     'account_number': account,
        #     'target_sor': target_sor,
        #     'from_state': from_state,
        #     'to_state': to_state
        # }
        # response = requests.post(api_url, json=payload, timeout=30)
        # api_response = response.json()
        # status = 'success' if response.status_code == 200 else 'failed'
        
        # Mock response for testing
        api_response = {'message': 'State change completed', 'account': account}
        status = 'success'
        
        save_to_db(batch_id, account, target_sor, from_state, to_state, status, json.dumps(api_response))
        
        return {'account': account, 'status': status}
        
    except Exception as e:
        save_to_db(batch_id, account, target_sor, from_state, to_state, 'failed', str(e))
        return {'account': account, 'status': 'failed', 'error': str(e)}

def save_to_db(batch_id, account, target_sor, from_state, to_state, status, response):
    conn = sqlite3.connect('admin_tool.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO state_changes 
        (batch_id, account_number, target_sor, from_state, to_state, status, response)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (batch_id, account, target_sor, from_state, to_state, status, response))
    conn.commit()
    conn.close()

@app.route('/get_results/<batch_id>')
def get_results(batch_id):
    conn = sqlite3.connect('admin_tool.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM state_changes WHERE batch_id = ?', (batch_id,))
    results = cursor.fetchall()
    conn.close()

    return jsonify({
        'batch_id': batch_id,
        'results': [
            {
                'id': r[0],
                'account': r[2],
                'target_sor': r[3],
                'from_state': r[4],
                'to_state': r[5],
                'status': r[6],
                'response': r[7],
                'timestamp': r[8]
            } for r in results
        ]
    })

@app.route('/api/get_all_runs')
def get_all_runs():
    """Get all batch runs with summary statistics"""
    conn = sqlite3.connect('admin_tool.db')
    cursor = conn.cursor()

    # Get all unique batch IDs with their statistics
    cursor.execute('''
        SELECT
            batch_id,
            target_sor,
            from_state,
            to_state,
            COUNT(*) as total_accounts,
            SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
            SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count,
            MIN(created_at) as created_at,
            MAX(created_at) as last_updated
        FROM state_changes
        GROUP BY batch_id
        ORDER BY created_at DESC
    ''')

    runs = cursor.fetchall()
    conn.close()

    return jsonify({
        'runs': [
            {
                'batch_id': r[0],
                'target_sor': r[1],
                'from_state': r[2],
                'to_state': r[3],
                'total_accounts': r[4],
                'success_count': r[5],
                'failed_count': r[6],
                'created_at': r[7],
                'last_updated': r[8],
                'status': 'completed' if r[4] == (r[5] + r[6]) else 'processing'
            } for r in runs
        ]
    })

@app.route('/api/get_run_details/<batch_id>')
def get_run_details(batch_id):
    """Get detailed success and failed accounts for a specific batch"""
    conn = sqlite3.connect('admin_tool.db')
    cursor = conn.cursor()

    # Get successful accounts
    cursor.execute('''
        SELECT account_number, target_sor, from_state, to_state, response, created_at
        FROM state_changes
        WHERE batch_id = ? AND status = 'success'
        ORDER BY created_at
    ''', (batch_id,))
    success_records = cursor.fetchall()

    # Get failed accounts
    cursor.execute('''
        SELECT account_number, target_sor, from_state, to_state, response, created_at
        FROM state_changes
        WHERE batch_id = ? AND status = 'failed'
        ORDER BY created_at
    ''', (batch_id,))
    failed_records = cursor.fetchall()

    conn.close()

    return jsonify({
        'batch_id': batch_id,
        'success': [
            {
                'account_number': r[0],
                'target_sor': r[1],
                'from_state': r[2],
                'to_state': r[3],
                'response': r[4],
                'timestamp': r[5]
            } for r in success_records
        ],
        'failed': [
            {
                'account_number': r[0],
                'target_sor': r[1],
                'from_state': r[2],
                'to_state': r[3],
                'response': r[4],
                'timestamp': r[5]
            } for r in failed_records
        ]
    })

@app.route('/api/get_run_progress/<batch_id>')
def get_run_progress(batch_id):
    """Get real-time progress of a batch run"""
    conn = sqlite3.connect('admin_tool.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            COUNT(*) as processed,
            SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
            SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count
        FROM state_changes
        WHERE batch_id = ?
    ''', (batch_id,))

    result = cursor.fetchone()
    conn.close()

    return jsonify({
        'batch_id': batch_id,
        'processed': result[0] if result else 0,
        'success_count': result[1] if result and result[1] else 0,
        'failed_count': result[2] if result and result[2] else 0
    })

# ============================================
# Configuration Loader
# ============================================

def load_config():
    """Load configuration from config.json"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}

# ============================================
# Jira Integration
# ============================================

def fetch_jira_tickets(fix_version):
    """Fetch Jira tickets for a specific fix version"""
    config = load_config()
    jira_config = config.get('jira', {})

    base_url = jira_config.get('base_url')
    email = jira_config.get('email')
    api_token = jira_config.get('api_token')
    jql_template = jira_config.get('jql_template', '')

    # Replace fix_version in JQL template
    jql_query = jql_template.replace('{fix_version}', fix_version)

    url = f"{base_url}/rest/api/3/search"
    auth = (email, api_token)

    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    params = {
        'jql': jql_query,
        'maxResults': 1000,
        'fields': 'key,summary,assignee,components,customfield_scrumTeam,status'
    }

    try:
        response = requests.get(url, headers=headers, auth=auth, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        tickets = []
        for issue in data.get('issues', []):
            ticket = {
                'key': issue['key'],
                'summary': issue['fields'].get('summary', ''),
                'assignee': issue['fields'].get('assignee', {}).get('displayName', 'Unassigned'),
                'assignee_email': issue['fields'].get('assignee', {}).get('emailAddress', ''),
                'components': [c['name'] for c in issue['fields'].get('components', [])],
                'scrum_team': issue['fields'].get('customfield_scrumTeam', 'Unknown'),
                'status': issue['fields'].get('status', {}).get('name', 'Unknown')
            }
            tickets.append(ticket)

        return {'success': True, 'tickets': tickets, 'total': len(tickets)}

    except Exception as e:
        return {'success': False, 'error': str(e), 'tickets': []}

# ============================================
# GitHub Integration
# ============================================

def get_github_branches(repo_name):
    """Get all branches for a GitHub repository"""
    config = load_config()
    github_config = config.get('github', {})

    token = github_config.get('token')
    org = github_config.get('organization')

    url = f"https://api.github.com/repos/{org}/{repo_name}/branches"
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        branches = response.json()
        return [branch['name'] for branch in branches]
    except Exception as e:
        print(f"Error fetching branches for {repo_name}: {e}")
        return []

def compare_github_branches(repo_name, base_branch, head_branch):
    """Compare two branches and get commits"""
    config = load_config()
    github_config = config.get('github', {})

    token = github_config.get('token')
    org = github_config.get('organization')

    url = f"https://api.github.com/repos/{org}/{repo_name}/compare/{base_branch}...{head_branch}"
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        commits = []
        commit_pattern = re.compile(r'Merge pull request #(\d+) from feature/([A-Z]+-\d+)')

        for commit in data.get('commits', []):
            message = commit['commit']['message']
            match = commit_pattern.search(message)

            if match:
                pr_number = match.group(1)
                jira_key = match.group(2)

                commits.append({
                    'sha': commit['sha'],
                    'message': message,
                    'pr_number': pr_number,
                    'jira_key': jira_key,
                    'author': commit['commit']['author']['name'],
                    'date': commit['commit']['author']['date'],
                    'url': commit['html_url']
                })

        return {
            'success': True,
            'commits': commits,
            'total_commits': data.get('total_commits', 0),
            'ahead_by': data.get('ahead_by', 0),
            'behind_by': data.get('behind_by', 0)
        }

    except Exception as e:
        return {'success': False, 'error': str(e), 'commits': []}

def create_github_branch(repo_name, new_branch_name, from_branch='master'):
    """Create a new branch on GitHub"""
    config = load_config()
    github_config = config.get('github', {})

    token = github_config.get('token')
    org = github_config.get('organization')

    # Get the SHA of the source branch
    ref_url = f"https://api.github.com/repos/{org}/{repo_name}/git/ref/heads/{from_branch}"
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }

    try:
        # Get source branch SHA
        response = requests.get(ref_url, headers=headers, timeout=30)
        response.raise_for_status()
        sha = response.json()['object']['sha']

        # Create new branch
        create_url = f"https://api.github.com/repos/{org}/{repo_name}/git/refs"
        data = {
            'ref': f'refs/heads/{new_branch_name}',
            'sha': sha
        }

        response = requests.post(create_url, headers=headers, json=data, timeout=30)
        response.raise_for_status()

        return {
            'success': True,
            'branch_name': new_branch_name,
            'sha': sha,
            'url': f"https://github.com/{org}/{repo_name}/tree/{new_branch_name}"
        }

    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_pull_request_details(repo_name, pr_number):
    """Get pull request details"""
    config = load_config()
    github_config = config.get('github', {})

    token = github_config.get('token')
    org = github_config.get('organization')

    url = f"https://api.github.com/repos/{org}/{repo_name}/pulls/{pr_number}"
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        pr = response.json()

        return {
            'number': pr['number'],
            'title': pr['title'],
            'url': pr['html_url'],
            'state': pr['state'],
            'merged': pr.get('merged', False),
            'author': pr['user']['login']
        }
    except Exception as e:
        print(f"Error fetching PR {pr_number}: {e}")
        return None

# ============================================
# Teams Integration
# ============================================

def send_teams_message(webhook_url, title, message, color='0078D4'):
    """Send message to Teams channel via webhook"""
    if not webhook_url:
        return {'success': False, 'error': 'No webhook URL provided'}

    payload = {
        "@type": "MessageCard",
        "@context": "https://schema.org/extensions",
        "themeColor": color,
        "title": title,
        "text": message
    }

    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def send_teams_to_scrum_team(scrum_team, title, message, color='0078D4'):
    """Send message to scrum team channel"""
    config = load_config()
    teams_config = config.get('teams', {})

    if not teams_config.get('enabled', False):
        return {'success': False, 'error': 'Teams integration disabled'}

    webhooks = teams_config.get('scrum_team_webhooks', {})
    webhook_url = webhooks.get(scrum_team)

    if not webhook_url:
        return {'success': False, 'error': f'No webhook configured for {scrum_team}'}

    return send_teams_message(webhook_url, title, message, color)

# ============================================
# RTB First Bill Tool Endpoints
# ============================================

def fetch_presto_accounts():
    """Fetch accounts from Presto API"""
    try:
        # Replace with your actual Presto API endpoint
        # api_url = 'https://your-presto-api.com/accounts'
        # response = requests.get(api_url, timeout=30)
        # return response.json().get('accounts', [])

        # Mock data for testing
        import random
        base_accounts = [f"PRESTO_{i:06d}" for i in range(1, 101)]
        # Randomly remove some accounts to create mismatches
        if random.random() > 0.8:
            return base_accounts[:-5]
        return base_accounts
    except Exception as e:
        print(f"Error fetching Presto accounts: {e}")
        return []

def fetch_cosmos_accounts():
    """Fetch accounts from Cosmos API"""
    try:
        # Replace with your actual Cosmos API endpoint
        # api_url = 'https://your-cosmos-api.com/accounts'
        # response = requests.get(api_url, timeout=30)
        # return response.json().get('accounts', [])

        # Mock data for testing
        import random
        base_accounts = [f"PRESTO_{i:06d}" for i in range(1, 101)]
        # Randomly add some extra accounts to create mismatches
        if random.random() > 0.8:
            base_accounts.extend([f"COSMOS_EXTRA_{i:03d}" for i in range(1, 6)])
        return base_accounts
    except Exception as e:
        print(f"Error fetching Cosmos accounts: {e}")
        return []

def process_rtb_comparison(run_id, run_date):
    """Process RTB First Bill comparison between Presto and Cosmos"""
    from concurrent.futures import ThreadPoolExecutor

    # Fetch accounts from both sources in parallel
    with ThreadPoolExecutor(max_workers=2) as executor:
        presto_future = executor.submit(fetch_presto_accounts)
        cosmos_future = executor.submit(fetch_cosmos_accounts)

        presto_accounts = presto_future.result()
        cosmos_accounts = cosmos_future.result()

    presto_set = set(presto_accounts)
    cosmos_set = set(cosmos_accounts)

    # Find matching and mismatched accounts
    matching = presto_set.intersection(cosmos_set)
    only_in_presto = presto_set - cosmos_set
    only_in_cosmos = cosmos_set - presto_set

    # Save to database
    conn = sqlite3.connect('admin_tool.db')
    cursor = conn.cursor()

    # Update run statistics
    cursor.execute('''
        UPDATE rtb_runs
        SET presto_count = ?,
            cosmos_count = ?,
            matching_count = ?,
            mismatch_count = ?,
            status = 'completed',
            completed_at = CURRENT_TIMESTAMP
        WHERE run_id = ?
    ''', (len(presto_set), len(cosmos_set), len(matching),
          len(only_in_presto) + len(only_in_cosmos), run_id))

    # Insert matching accounts
    for account in matching:
        cursor.execute('''
            INSERT INTO rtb_accounts (run_id, account_number, source, match_status)
            VALUES (?, ?, 'both', 'matched')
        ''', (run_id, account))

    # Insert Presto-only accounts
    for account in only_in_presto:
        cursor.execute('''
            INSERT INTO rtb_accounts (run_id, account_number, source, match_status)
            VALUES (?, ?, 'presto_only', 'mismatched')
        ''', (run_id, account))

    # Insert Cosmos-only accounts
    for account in only_in_cosmos:
        cursor.execute('''
            INSERT INTO rtb_accounts (run_id, account_number, source, match_status)
            VALUES (?, ?, 'cosmos_only', 'mismatched')
        ''', (run_id, account))

    conn.commit()
    conn.close()

    return {
        'presto_count': len(presto_set),
        'cosmos_count': len(cosmos_set),
        'matching_count': len(matching),
        'mismatch_count': len(only_in_presto) + len(only_in_cosmos)
    }

@app.route('/api/rtb/check_and_run')
def rtb_check_and_run():
    """Check if RTB run exists for today, if not create one"""
    today = datetime.now().date()

    conn = sqlite3.connect('admin_tool.db')
    cursor = conn.cursor()

    # Check if run exists for today
    cursor.execute('''
        SELECT run_id, status FROM rtb_runs WHERE run_date = ?
    ''', (today,))

    existing_run = cursor.fetchone()

    if existing_run:
        run_id = existing_run[0]
        status = existing_run[1]
        conn.close()
        return jsonify({
            'run_exists': True,
            'run_id': run_id,
            'status': status,
            'message': 'Run already exists for today'
        })

    # Create new run
    run_id = f"RTB_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    cursor.execute('''
        INSERT INTO rtb_runs (run_id, run_date, status)
        VALUES (?, ?, 'processing')
    ''', (run_id, today))

    conn.commit()
    conn.close()

    # Process comparison in background
    from threading import Thread
    thread = Thread(target=process_rtb_comparison, args=(run_id, today))
    thread.start()

    return jsonify({
        'run_exists': False,
        'run_id': run_id,
        'status': 'processing',
        'message': 'New run created and processing'
    })

@app.route('/api/rtb/trigger_run')
def rtb_trigger_run():
    """Manually trigger a new RTB run"""
    today = datetime.now().date()
    run_id = f"RTB_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    conn = sqlite3.connect('admin_tool.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO rtb_runs (run_id, run_date, status)
        VALUES (?, ?, 'processing')
    ''', (run_id, today))

    conn.commit()
    conn.close()

    # Process comparison in background
    from threading import Thread
    thread = Thread(target=process_rtb_comparison, args=(run_id, today))
    thread.start()

    return jsonify({
        'success': True,
        'run_id': run_id,
        'message': 'Run triggered successfully'
    })

@app.route('/api/rtb/get_all_runs')
def rtb_get_all_runs():
    """Get all RTB runs"""
    conn = sqlite3.connect('admin_tool.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT run_id, run_date, presto_count, cosmos_count,
               matching_count, mismatch_count, status, created_at, completed_at
        FROM rtb_runs
        ORDER BY run_date DESC, created_at DESC
    ''')

    runs = cursor.fetchall()
    conn.close()

    return jsonify({
        'runs': [
            {
                'run_id': r[0],
                'run_date': r[1],
                'presto_count': r[2] if r[2] else 0,
                'cosmos_count': r[3] if r[3] else 0,
                'matching_count': r[4] if r[4] else 0,
                'mismatch_count': r[5] if r[5] else 0,
                'status': r[6],
                'match_status': 'matched' if r[5] == 0 else 'mismatched',
                'created_at': r[7],
                'completed_at': r[8]
            } for r in runs
        ]
    })

@app.route('/api/rtb/get_mismatch_details/<run_id>')
def rtb_get_mismatch_details(run_id):
    """Get mismatch details for a specific run"""
    conn = sqlite3.connect('admin_tool.db')
    cursor = conn.cursor()

    # Get run summary
    cursor.execute('''
        SELECT run_id, run_date, presto_count, cosmos_count,
               matching_count, mismatch_count, status
        FROM rtb_runs
        WHERE run_id = ?
    ''', (run_id,))

    run_info = cursor.fetchone()

    if not run_info:
        conn.close()
        return jsonify({'error': 'Run not found'}), 404

    # Get mismatched accounts (Presto only)
    cursor.execute('''
        SELECT account_number, source, created_at
        FROM rtb_accounts
        WHERE run_id = ? AND source = 'presto_only'
        ORDER BY account_number
    ''', (run_id,))
    presto_only = cursor.fetchall()

    # Get mismatched accounts (Cosmos only)
    cursor.execute('''
        SELECT account_number, source, created_at
        FROM rtb_accounts
        WHERE run_id = ? AND source = 'cosmos_only'
        ORDER BY account_number
    ''', (run_id,))
    cosmos_only = cursor.fetchall()

    conn.close()

    return jsonify({
        'run_info': {
            'run_id': run_info[0],
            'run_date': run_info[1],
            'presto_count': run_info[2],
            'cosmos_count': run_info[3],
            'matching_count': run_info[4],
            'mismatch_count': run_info[5],
            'status': run_info[6]
        },
        'presto_only': [
            {
                'account_number': r[0],
                'source': r[1],
                'timestamp': r[2]
            } for r in presto_only
        ],
        'cosmos_only': [
            {
                'account_number': r[0],
                'source': r[1],
                'timestamp': r[2]
            } for r in cosmos_only
        ]
    })

@app.route('/api/rtb/get_run_status/<run_id>')
def rtb_get_run_status(run_id):
    """Get real-time status of a run"""
    conn = sqlite3.connect('admin_tool.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT status, presto_count, cosmos_count, matching_count, mismatch_count
        FROM rtb_runs
        WHERE run_id = ?
    ''', (run_id,))

    result = cursor.fetchone()
    conn.close()

    if not result:
        return jsonify({'error': 'Run not found'}), 404

    return jsonify({
        'run_id': run_id,
        'status': result[0],
        'presto_count': result[1] if result[1] else 0,
        'cosmos_count': result[2] if result[2] else 0,
        'matching_count': result[3] if result[3] else 0,
        'mismatch_count': result[4] if result[4] else 0
    })

# ============================================
# Release Branch Creation Tool Endpoints
# ============================================

@app.route('/api/release/fetch_jira_tickets', methods=['POST'])
def api_fetch_jira_tickets():
    """Fetch Jira tickets for a release version"""
    data = request.json
    fix_version = data.get('fix_version')

    if not fix_version:
        return jsonify({'error': 'fix_version is required'}), 400

    result = fetch_jira_tickets(fix_version)

    if not result['success']:
        return jsonify(result), 500

    # Group by scrum team
    scrum_teams = {}
    for ticket in result['tickets']:
        team = ticket['scrum_team']
        if team not in scrum_teams:
            scrum_teams[team] = []
        scrum_teams[team].append(ticket)

    # Store in session cache
    session_id = datetime.now().strftime('%Y%m%d%H%M%S')
    conn = sqlite3.connect('admin_tool.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO release_cache (session_id, release_version, jira_data)
        VALUES (?, ?, ?)
    ''', (session_id, fix_version, json.dumps(result['tickets'])))

    conn.commit()
    conn.close()

    return jsonify({
        'success': True,
        'session_id': session_id,
        'fix_version': fix_version,
        'total_tickets': result['total'],
        'scrum_teams': list(scrum_teams.keys()),
        'scrum_team_data': {team: len(tickets) for team, tickets in scrum_teams.items()}
    })

@app.route('/api/release/get_components/<session_id>/<scrum_team>')
def api_get_components(session_id, scrum_team):
    """Get unique components for a scrum team"""
    conn = sqlite3.connect('admin_tool.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT jira_data FROM release_cache
        WHERE session_id = ?
        LIMIT 1
    ''', (session_id,))

    result = cursor.fetchone()
    conn.close()

    if not result:
        return jsonify({'error': 'Session not found'}), 404

    tickets = json.loads(result[0])

    # Filter by scrum team and get unique components
    components = set()
    team_tickets = []

    for ticket in tickets:
        if ticket['scrum_team'] == scrum_team:
            team_tickets.append(ticket)
            for component in ticket['components']:
                components.add(component)

    config = load_config()
    component_repos = config.get('github', {}).get('component_repos', {})

    return jsonify({
        'success': True,
        'scrum_team': scrum_team,
        'components': sorted(list(components)),
        'component_repos': component_repos,
        'ticket_count': len(team_tickets)
    })

@app.route('/api/release/get_branches/<component>')
def api_get_branches(component):
    """Get branches for a component"""
    config = load_config()
    component_repos = config.get('github', {}).get('component_repos', {})

    repo_name = component_repos.get(component)

    if not repo_name:
        return jsonify({'error': f'No repository mapped for component {component}'}), 404

    branches = get_github_branches(repo_name)

    return jsonify({
        'success': True,
        'component': component,
        'repo_name': repo_name,
        'branches': branches
    })

@app.route('/api/release/compare_and_analyze', methods=['POST'])
def api_compare_and_analyze():
    """Compare branches and analyze Jira tickets vs commits"""
    data = request.json
    session_id = data.get('session_id')
    scrum_team = data.get('scrum_team')
    component = data.get('component')
    from_branch = data.get('from_branch')
    to_branch = data.get('to_branch')

    if not all([session_id, scrum_team, component, from_branch, to_branch]):
        return jsonify({'error': 'Missing required parameters'}), 400

    # Get Jira tickets from cache
    conn = sqlite3.connect('admin_tool.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT jira_data FROM release_cache
        WHERE session_id = ?
        LIMIT 1
    ''', (session_id,))

    result = cursor.fetchone()
    conn.close()

    if not result:
        return jsonify({'error': 'Session not found'}), 404

    all_tickets = json.loads(result[0])

    # Filter tickets for this scrum team and component
    jira_tickets = []
    for ticket in all_tickets:
        if ticket['scrum_team'] == scrum_team and component in ticket['components']:
            jira_tickets.append(ticket)

    # Get repository name
    config = load_config()
    component_repos = config.get('github', {}).get('component_repos', {})
    repo_name = component_repos.get(component)

    if not repo_name:
        return jsonify({'error': f'No repository mapped for component {component}'}), 404

    # Compare branches
    comparison = compare_github_branches(repo_name, to_branch, from_branch)

    if not comparison['success']:
        return jsonify(comparison), 500

    # Extract Jira keys from tickets
    jira_keys = set([ticket['key'] for ticket in jira_tickets])
    commit_jira_keys = set([commit['jira_key'] for commit in comparison['commits']])

    # Analysis
    missing_in_branch = jira_keys - commit_jira_keys  # In Jira but no commit
    extra_in_branch = commit_jira_keys - jira_keys    # In commits but not in Jira
    matched = jira_keys & commit_jira_keys            # Both in Jira and commits

    # Build detailed results
    missing_tickets = [t for t in jira_tickets if t['key'] in missing_in_branch]
    extra_commits = [c for c in comparison['commits'] if c['jira_key'] in extra_in_branch]
    matched_data = []

    for key in matched:
        ticket = next((t for t in jira_tickets if t['key'] == key), None)
        commit = next((c for c in comparison['commits'] if c['jira_key'] == key), None)

        if ticket and commit:
            # Get PR details
            pr_details = get_pull_request_details(repo_name, commit['pr_number'])

            matched_data.append({
                'jira_key': key,
                'jira_summary': ticket['summary'],
                'jira_url': f"https://your-jira-instance.atlassian.net/browse/{key}",
                'commit_sha': commit['sha'],
                'commit_url': commit['url'],
                'pr_number': commit['pr_number'],
                'pr_url': pr_details['url'] if pr_details else '#',
                'author': commit['author'],
                'date': commit['date']
            })

    return jsonify({
        'success': True,
        'scrum_team': scrum_team,
        'component': component,
        'repo_name': repo_name,
        'from_branch': from_branch,
        'to_branch': to_branch,
        'total_jira_tickets': len(jira_tickets),
        'total_commits': len(comparison['commits']),
        'ahead_by': comparison['ahead_by'],
        'behind_by': comparison['behind_by'],
        'analysis': {
            'missing_in_branch': [
                {
                    'key': t['key'],
                    'summary': t['summary'],
                    'assignee': t['assignee'],
                    'assignee_email': t['assignee_email'],
                    'status': t['status'],
                    'jira_url': f"https://your-jira-instance.atlassian.net/browse/{t['key']}"
                } for t in missing_tickets
            ],
            'extra_in_branch': extra_commits,
            'matched': matched_data
        }
    })

@app.route('/api/release/send_missing_notification', methods=['POST'])
def api_send_missing_notification():
    """Send Teams notification for missing commits"""
    data = request.json
    scrum_team = data.get('scrum_team')
    component = data.get('component')
    missing_tickets = data.get('missing_tickets', [])
    release_version = data.get('release_version')

    if not missing_tickets:
        return jsonify({'error': 'No tickets to notify'}), 400

    # Build message
    ticket_list = '\n'.join([f"• {t['key']}: {t['summary']} (Assignee: {t['assignee']})" for t in missing_tickets])

    title = f"⚠️ Release {release_version} - Missing Commits in Master"
    message = f"""
**Scrum Team:** {scrum_team}
**Component:** {component}

The following stories are tagged for release **{release_version}** but are NOT found in master branch:

{ticket_list}

**Action Required:** Please ensure these features are merged to master before creating the release branch.
    """

    # Send to Teams
    result = send_teams_to_scrum_team(scrum_team, title, message, color='FF6C00')

    return jsonify(result)

@app.route('/api/release/send_extra_notification', methods=['POST'])
def api_send_extra_notification():
    """Send Teams notification for extra commits"""
    data = request.json
    scrum_team = data.get('scrum_team')
    component = data.get('component')
    extra_commits = data.get('extra_commits', [])
    release_version = data.get('release_version')

    if not extra_commits:
        return jsonify({'error': 'No commits to notify'}), 400

    # Build message
    commit_list = '\n'.join([f"• {c['jira_key']}: {c['message'][:100]}..." for c in extra_commits])

    title = f"🚨 CRITICAL: Release {release_version} - Untagged Commits in Master"
    message = f"""
**Scrum Team:** {scrum_team}
**Component:** {component}

The following commits are in master but NOT tagged for release **{release_version}**:

{commit_list}

**CRITICAL:** These changes will go to production if we create the release branch now.

**Questions:**
1. Should these be included in this release?
2. Have these been validated and tested?
3. Should we tag them to this release version?

**Please review immediately.**
    """

    # Send to Teams
    result = send_teams_to_scrum_team(scrum_team, title, message, color='D13438')

    return jsonify(result)

@app.route('/api/release/create_branch', methods=['POST'])
def api_create_release_branch():
    """Create release branch on GitHub"""
    data = request.json
    component = data.get('component')
    branch_name = data.get('branch_name')
    from_branch = data.get('from_branch', 'master')
    release_version = data.get('release_version')
    scrum_team = data.get('scrum_team')

    if not all([component, branch_name, release_version]):
        return jsonify({'error': 'Missing required parameters'}), 400

    # Get repository name
    config = load_config()
    component_repos = config.get('github', {}).get('component_repos', {})
    repo_name = component_repos.get(component)

    if not repo_name:
        return jsonify({'error': f'No repository mapped for component {component}'}), 404

    # Create branch
    result = create_github_branch(repo_name, branch_name, from_branch)

    if result['success']:
        # Save to audit trail
        conn = sqlite3.connect('admin_tool.db')
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO release_branches
            (release_version, branch_name, created_from, scrum_team, component, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (release_version, branch_name, from_branch, scrum_team, component, 'admin_user'))

        conn.commit()
        conn.close()

    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
