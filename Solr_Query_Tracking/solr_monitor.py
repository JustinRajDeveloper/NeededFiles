import json
import sqlite3
import requests
import schedule
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import hashlib
from dataclasses import dataclass
from deepdiff import DeepDiff
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template, jsonify, request, redirect, url_for
import threading
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('solr_monitor.log'),
        logging.StreamHandler()
    ]
)

@dataclass
class QueryResult:
    timestamp: datetime
    query_hash: str
    result_hash: str
    account_count: int
    raw_response: str
    query_params: Dict[str, Any]

class SolrMonitor:
    def __init__(self, solr_url: str, db_path: str = "solr_monitor.db"):
        self.solr_url = solr_url
        self.db_path = db_path
        self.setup_database()
        
    def setup_database(self):
        """Initialize SQLite database to store query results"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS query_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            query_hash TEXT NOT NULL,
            result_hash TEXT NOT NULL,
            account_count INTEGER NOT NULL,
            raw_response TEXT NOT NULL,
            query_params TEXT NOT NULL
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS comparisons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            query_hash TEXT NOT NULL,
            previous_result_id INTEGER,
            current_result_id INTEGER,
            differences TEXT,
            account_count_diff INTEGER,
            is_different BOOLEAN NOT NULL,
            FOREIGN KEY (previous_result_id) REFERENCES query_results (id),
            FOREIGN KEY (current_result_id) REFERENCES query_results (id)
        )
        ''')
        
        conn.commit()
        conn.close()
        
    def execute_solr_query(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Solr query and return JSON response"""
        try:
            response = requests.get(self.solr_url, params=query_params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Error executing Solr query: {e}")
            raise
            
    def calculate_hash(self, data: Any) -> str:
        """Calculate hash of the data for comparison"""
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
        
    def store_result(self, result: QueryResult) -> int:
        """Store query result in database and return the record ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO query_results 
        (timestamp, query_hash, result_hash, account_count, raw_response, query_params)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            result.timestamp.isoformat(),
            result.query_hash,
            result.result_hash,
            result.account_count,
            result.raw_response,
            json.dumps(result.query_params)
        ))
        
        result_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return result_id
        
    def get_previous_result(self, query_hash: str) -> Optional[QueryResult]:
        """Get the most recent previous result for the same query"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT timestamp, query_hash, result_hash, account_count, raw_response, query_params, id
        FROM query_results 
        WHERE query_hash = ?
        ORDER BY timestamp DESC 
        LIMIT 1
        ''', (query_hash,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return QueryResult(
                timestamp=datetime.fromisoformat(row[0]),
                query_hash=row[1],
                result_hash=row[2],
                account_count=row[3],
                raw_response=row[4],
                query_params=json.loads(row[5])
            ), row[6]  # Also return the ID
        return None, None
        
    def compare_results(self, current_result: Dict[str, Any], 
                       previous_result_str: str) -> Dict[str, Any]:
        """Compare current result with previous result"""
        try:
            previous_result = json.loads(previous_result_str)
            diff = DeepDiff(previous_result, current_result, 
                          ignore_order=True, report_type='text')
            return {
                'has_differences': bool(diff),
                'differences': str(diff) if diff else None,
                'detailed_diff': diff.to_dict() if hasattr(diff, 'to_dict') else {}
            }
        except Exception as e:
            logging.error(f"Error comparing results: {e}")
            return {'has_differences': False, 'differences': None, 'detailed_diff': {}}
            
    def store_comparison(self, query_hash: str, previous_result_id: Optional[int], 
                        current_result_id: int, comparison: Dict[str, Any], 
                        account_count_diff: int):
        """Store comparison result in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO comparisons 
        (timestamp, query_hash, previous_result_id, current_result_id, 
         differences, account_count_diff, is_different)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            query_hash,
            previous_result_id,
            current_result_id,
            comparison['differences'],
            account_count_diff,
            comparison['has_differences']
        ))
        
        conn.commit()
        conn.close()
        
    def monitor_query(self, query_params: Dict[str, Any], 
                     notification_callback: Optional[callable] = None):
        """Execute query, compare with previous result, and store results"""
        try:
            # Execute current query
            current_response = self.execute_solr_query(query_params)
            
            # Create result object
            query_hash = self.calculate_hash(query_params)
            result_hash = self.calculate_hash(current_response)
            
            # Extract account count (adjust path based on your Solr response structure)
            account_count = self.extract_account_count(current_response)
            
            current_result = QueryResult(
                timestamp=datetime.now(),
                query_hash=query_hash,
                result_hash=result_hash,
                account_count=account_count,
                raw_response=json.dumps(current_response),
                query_params=query_params
            )
            
            # Store current result
            current_result_id = self.store_result(current_result)
            
            # Get previous result
            previous_result, previous_result_id = self.get_previous_result(query_hash)
            
            if previous_result:
                # Compare results
                comparison = self.compare_results(current_response, previous_result.raw_response)
                account_count_diff = current_result.account_count - previous_result.account_count
                
                # Store comparison
                self.store_comparison(query_hash, previous_result_id, current_result_id, 
                                    comparison, account_count_diff)
                
                # Log and notify if differences found
                if comparison['has_differences']:
                    logging.warning(f"Differences detected in query results!")
                    logging.warning(f"Account count changed by: {account_count_diff}")
                    logging.warning(f"Differences: {comparison['differences']}")
                    
                    if notification_callback:
                        notification_callback(current_result, previous_result, comparison)
                else:
                    logging.info("No differences detected - results are consistent")
            else:
                logging.info("No previous result found - this is the first execution")
                
        except Exception as e:
            logging.error(f"Error in monitor_query: {e}")
            
    def extract_account_count(self, response: Dict[str, Any]) -> int:
        """Extract account count from Solr response - adjust based on your response structure"""
        # Common Solr response patterns - adjust as needed
        if 'response' in response and 'numFound' in response['response']:
            return response['response']['numFound']
        elif 'response' in response and 'docs' in response['response']:
            return len(response['response']['docs'])
        else:
            # Fallback - try to find any list that might contain accounts
            for key, value in response.items():
                if isinstance(value, list):
                    return len(value)
            return 0
            
    def get_comparison_report(self, hours_back: int = 24) -> List[Dict[str, Any]]:
        """Get comparison report for the last N hours"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since_time = datetime.now() - timedelta(hours=hours_back)
        
        cursor.execute('''
        SELECT c.timestamp, c.query_hash, c.account_count_diff, 
               c.is_different, c.differences,
               r1.account_count as previous_count,
               r2.account_count as current_count,
               c.id
        FROM comparisons c
        JOIN query_results r1 ON c.previous_result_id = r1.id
        JOIN query_results r2 ON c.current_result_id = r2.id
        WHERE c.timestamp >= ?
        ORDER BY c.timestamp DESC
        ''', (since_time.isoformat(),))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[7],
                'timestamp': row[0],
                'query_hash': row[1],
                'account_count_diff': row[2],
                'is_different': bool(row[3]),
                'differences': row[4],
                'previous_count': row[5],
                'current_count': row[6]
            })
            
        conn.close()
        return results
        
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get summary statistics for dashboard"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get basic stats
        cursor.execute('''
        SELECT 
            COUNT(*) as total_checks,
            SUM(CASE WHEN is_different = 1 THEN 1 ELSE 0 END) as changes_detected,
            MAX(datetime(timestamp)) as last_check,
            MIN(datetime(timestamp)) as first_check
        FROM comparisons 
        WHERE timestamp >= datetime('now', '-24 hours')
        ''')
        
        stats = cursor.fetchone()
        
        # Get trend data for the last 24 hours
        cursor.execute('''
        SELECT 
            strftime('%H', timestamp) as hour,
            r2.account_count,
            c.is_different,
            c.timestamp
        FROM comparisons c
        JOIN query_results r2 ON c.current_result_id = r2.id
        WHERE c.timestamp >= datetime('now', '-24 hours')
        ORDER BY c.timestamp ASC
        ''')
        
        trend_data = cursor.fetchall()
        
        # Get recent alerts (changes)
        cursor.execute('''
        SELECT c.timestamp, c.account_count_diff, c.differences,
               r2.account_count as current_count
        FROM comparisons c
        JOIN query_results r2 ON c.current_result_id = r2.id
        WHERE c.is_different = 1 
        AND c.timestamp >= datetime('now', '-24 hours')
        ORDER BY c.timestamp DESC
        LIMIT 5
        ''')
        
        recent_alerts = cursor.fetchall()
        
        conn.close()
        
        total_checks = stats[0] if stats[0] else 0
        changes_detected = stats[1] if stats[1] else 0
        stability_rate = ((total_checks - changes_detected) / total_checks * 100) if total_checks > 0 else 100
        
        return {
            'total_checks': total_checks,
            'changes_detected': changes_detected,
            'stability_rate': round(stability_rate, 2),
            'last_check': stats[2],
            'first_check': stats[3],
            'trend_data': [{'hour': row[0], 'account_count': row[1], 'is_different': row[2], 'timestamp': row[3]} for row in trend_data],
            'recent_alerts': [{'timestamp': row[0], 'account_count_diff': row[1], 'differences': row[2], 'current_count': row[3]} for row in recent_alerts]
        }
        
    def get_account_count_trend(self, hours_back: int = 168) -> List[Dict[str, Any]]:
        """Get account count trend data for charts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since_time = datetime.now() - timedelta(hours=hours_back)
        
        cursor.execute('''
        SELECT 
            datetime(r.timestamp) as timestamp,
            r.account_count,
            COALESCE(c.is_different, 0) as is_different
        FROM query_results r
        LEFT JOIN comparisons c ON r.id = c.current_result_id
        WHERE r.timestamp >= ?
        ORDER BY r.timestamp ASC
        ''', (since_time.isoformat(),))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'timestamp': row[0],
                'account_count': row[1],
                'is_different': bool(row[2])
            })
            
        conn.close()
        return results
        
    def send_email_notification(self, current_result: QueryResult, 
                               previous_result: QueryResult, 
                               comparison: Dict[str, Any],
                               email_config: Dict[str, str]):
        """Send email notification when differences are detected"""
        try:
            msg = MIMEMultipart()
            msg['From'] = email_config['from_email']
            msg['To'] = email_config['to_email']
            msg['Subject'] = "Solr Query Results Changed - Alert"
            
            body = f"""
            Alert: Solr Query Results Have Changed
            
            Query executed at: {current_result.timestamp}
            Previous result from: {previous_result.timestamp}
            
            Account Count Changes:
            - Previous: {previous_result.account_count}
            - Current: {current_result.account_count}
            - Difference: {current_result.account_count - previous_result.account_count}
            
            Detected Differences:
            {comparison['differences']}
            
            Please investigate the cause of these changes.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            if email_config.get('use_tls'):
                server.starttls()
            if email_config.get('username'):
                server.login(email_config['username'], email_config['password'])
                
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            logging.error(f"Failed to send email notification: {e}")

# Flask Web Dashboard
class SolrMonitorDashboard:
    def __init__(self, monitor: SolrMonitor):
        self.monitor = monitor
        self.app = Flask(__name__)
        self.app.secret_key = os.urandom(24)
        self.create_templates()  # Create templates immediately
        self.setup_routes()
        
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def dashboard():
            """Main dashboard page"""
            summary = self.monitor.get_dashboard_summary()
            return render_template('dashboard.html', summary=summary)
            
        @self.app.route('/comparisons')
        def comparisons():
            """Detailed comparisons page"""
            hours_back = request.args.get('hours', 24, type=int)
            comparisons_data = self.monitor.get_comparison_report(hours_back)
            return render_template('comparisons.html', 
                                 comparisons=comparisons_data, 
                                 hours_back=hours_back)
            
        @self.app.route('/trends')
        def trends():
            """Trends and analytics page"""
            hours_back = request.args.get('hours', 168, type=int)  # Default 7 days
            trend_data = self.monitor.get_account_count_trend(hours_back)
            return render_template('trends.html', 
                                 trend_data=trend_data, 
                                 hours_back=hours_back)
            
        @self.app.route('/api/summary')
        def api_summary():
            """API endpoint for dashboard summary"""
            return jsonify(self.monitor.get_dashboard_summary())
            
        @self.app.route('/api/comparisons')
        def api_comparisons():
            """API endpoint for comparisons data"""
            hours_back = request.args.get('hours', 24, type=int)
            return jsonify(self.monitor.get_comparison_report(hours_back))
            
        @self.app.route('/api/trends')
        def api_trends():
            """API endpoint for trend data"""
            hours_back = request.args.get('hours', 168, type=int)
            return jsonify(self.monitor.get_account_count_trend(hours_back))
            
        @self.app.route('/api/run-check', methods=['POST'])
        def api_run_check():
            """API endpoint to trigger manual check"""
            try:
                # This would need the query params - simplified for demo
                return jsonify({'status': 'success', 'message': 'Check triggered'})
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500
                
    def create_templates(self):
        """Create HTML templates for the dashboard"""
        os.makedirs('templates', exist_ok=True)
        
        # Base template
        with open('templates/base.html', 'w') as f:
            f.write('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Solr Monitor Dashboard{% endblock %}</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/tailwindcss/2.2.19/tailwind.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-gray-100">
    <nav class="bg-blue-600 text-white p-4">
        <div class="container mx-auto flex justify-between items-center">
            <h1 class="text-xl font-bold">
                <i class="fas fa-search mr-2"></i>Solr Monitor Dashboard
            </h1>
            <div class="space-x-4">
                <a href="/" class="hover:text-blue-200">Dashboard</a>
                <a href="/comparisons" class="hover:text-blue-200">Comparisons</a>
                <a href="/trends" class="hover:text-blue-200">Trends</a>
            </div>
        </div>
    </nav>
    
    <div class="container mx-auto mt-8 px-4">
        {% block content %}{% endblock %}
    </div>
    
    <script>
        // Auto-refresh every 5 minutes
        setTimeout(function(){ location.reload(); }, 300000);
    </script>
</body>
</html>''')

        # Dashboard template
        with open('templates/dashboard.html', 'w') as f:
            f.write('''{% extends "base.html" %}

{% block content %}
<div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
    <!-- Stats Cards -->
    <div class="bg-white p-6 rounded-lg shadow">
        <div class="flex items-center">
            <i class="fas fa-check-circle text-green-500 text-2xl mr-4"></i>
            <div>
                <p class="text-sm text-gray-600">Total Checks (24h)</p>
                <p class="text-2xl font-bold">{{ summary.total_checks }}</p>
            </div>
        </div>
    </div>
    
    <div class="bg-white p-6 rounded-lg shadow">
        <div class="flex items-center">
            <i class="fas fa-exclamation-triangle text-yellow-500 text-2xl mr-4"></i>
            <div>
                <p class="text-sm text-gray-600">Changes Detected</p>
                <p class="text-2xl font-bold">{{ summary.changes_detected }}</p>
            </div>
        </div>
    </div>
    
    <div class="bg-white p-6 rounded-lg shadow">
        <div class="flex items-center">
            <i class="fas fa-chart-line text-blue-500 text-2xl mr-4"></i>
            <div>
                <p class="text-sm text-gray-600">Stability Rate</p>
                <p class="text-2xl font-bold">{{ summary.stability_rate }}%</p>
            </div>
        </div>
    </div>
    
    <div class="bg-white p-6 rounded-lg shadow">
        <div class="flex items-center">
            <i class="fas fa-clock text-purple-500 text-2xl mr-4"></i>
            <div>
                <p class="text-sm text-gray-600">Last Check</p>
                <p class="text-sm font-bold">{{ summary.last_check or 'Never' }}</p>
            </div>
        </div>
    </div>
</div>

<!-- Account Count Trend Chart -->
<div class="bg-white p-6 rounded-lg shadow mb-8">
    <h2 class="text-xl font-bold mb-4">
        <i class="fas fa-chart-area mr-2"></i>Account Count Trend (24h)
    </h2>
    <canvas id="trendChart" width="400" height="100"></canvas>
</div>

<!-- Recent Alerts -->
<div class="bg-white p-6 rounded-lg shadow">
    <h2 class="text-xl font-bold mb-4">
        <i class="fas fa-bell mr-2"></i>Recent Changes
    </h2>
    {% if summary.recent_alerts %}
        <div class="space-y-3">
            {% for alert in summary.recent_alerts %}
            <div class="border-l-4 {% if alert.account_count_diff < 0 %}border-red-500{% elif alert.account_count_diff > 0 %}border-green-500{% else %}border-yellow-500{% endif %} pl-4 py-2">
                <div class="flex justify-between items-start">
                    <div>
                        <p class="font-semibold">
                            {% if alert.account_count_diff < 0 %}
                                <i class="fas fa-arrow-down text-red-500 mr-1"></i>
                                {{ alert.account_count_diff }} accounts removed
                            {% elif alert.account_count_diff > 0 %}
                                <i class="fas fa-arrow-up text-green-500 mr-1"></i>
                                +{{ alert.account_count_diff }} accounts added
                            {% else %}
                                <i class="fas fa-edit text-yellow-500 mr-1"></i>
                                Field changes detected
                            {% endif %}
                        </p>
                        <p class="text-sm text-gray-600">Current count: {{ alert.current_count }}</p>
                    </div>
                    <span class="text-xs text-gray-500">{{ alert.timestamp }}</span>
                </div>
            </div>
            {% endfor %}
        </div>
    {% else %}
        <p class="text-gray-500">No changes detected in the last 24 hours.</p>
    {% endif %}
</div>

<script>
// Trend Chart
const ctx = document.getElementById('trendChart').getContext('2d');
const trendData = {{ summary.trend_data | tojson }};
if (trendData && trendData.length > 0) {
    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: trendData.map(d => d.timestamp.split('T')[1].substring(0,5)),
            datasets: [{
                label: 'Account Count',
                data: trendData.map(d => d.account_count),
                borderColor: 'rgb(59, 130, 246)',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                tension: 0.1,
                pointBackgroundColor: trendData.map(d => d.is_different ? 'red' : 'rgb(59, 130, 246)'),
                pointRadius: trendData.map(d => d.is_different ? 6 : 3)
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: false
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const point = trendData[context.dataIndex];
                            return `Count: ${context.parsed.y}${point.is_different ? ' (Changed!)' : ''}`;
                        }
                    }
                }
            }
        }
    });
} else {
    document.getElementById('trendChart').getContext('2d').fillText('No data available yet', 10, 50);
}
</script>
{% endblock %}''')

        # Trends template
        with open('templates/trends.html', 'w') as f:
            f.write('''{% extends "base.html" %}

{% block title %}Trends - Solr Monitor{% endblock %}

{% block content %}
<div class="flex justify-between items-center mb-6">
    <h1 class="text-2xl font-bold">
        <i class="fas fa-chart-line mr-2"></i>Account Count Trends
    </h1>
    <div class="space-x-2">
        <a href="/trends?hours=24" class="px-3 py-1 bg-blue-500 text-white rounded {% if hours_back == 24 %}bg-blue-700{% endif %}">24h</a>
        <a href="/trends?hours=168" class="px-3 py-1 bg-blue-500 text-white rounded {% if hours_back == 168 %}bg-blue-700{% endif %}">7d</a>
        <a href="/trends?hours=720" class="px-3 py-1 bg-blue-500 text-white rounded {% if hours_back == 720 %}bg-blue-700{% endif %}">30d</a>
    </div>
</div>

<div class="bg-white p-6 rounded-lg shadow">
    <canvas id="mainTrendChart" width="400" height="100"></canvas>
</div>

<script>
const trendCtx = document.getElementById('mainTrendChart').getContext('2d');
const trendData = {{ trend_data | tojson }};

const mainChart = new Chart(trendCtx, {
    type: 'line',
    data: {
        labels: trendData.map(d => new Date(d.timestamp).toLocaleString()),
        datasets: [{
            label: 'Account Count',
            data: trendData.map(d => d.account_count),
            borderColor: 'rgb(59, 130, 246)',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            tension: 0.1,
            pointBackgroundColor: trendData.map(d => d.is_different ? 'red' : 'rgb(59, 130, 246)'),
            pointRadius: trendData.map(d => d.is_different ? 6 : 3),
            fill: true
        }]
    },
    options: {
        responsive: true,
        scales: {
            x: {
                display: true,
                title: {
                    display: true,
                    text: 'Time'
                }
            },
            y: {
                display: true,
                title: {
                    display: true,
                    text: 'Account Count'
                },
                beginAtZero: false
            }
        },
        plugins: {
            tooltip: {
                callbacks: {
                    label: function(context) {
                        const point = trendData[context.dataIndex];
                        return `Count: ${context.parsed.y}${point.is_different ? ' (Changed!)' : ''}`;
                    }
                }
            },
            legend: {
                display: true
            }
        }
    }
});
</script>
{% endblock %}''')

    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Run the Flask dashboard"""
        print(f"Templates folder created at: {os.path.abspath('templates')}")
        print(f"Starting dashboard at http://{host}:{port}")
        self.app.run(host=host, port=port, debug=debug)

# Enhanced main function with web dashboard
def main_with_dashboard():
    # Configuration
    SOLR_URL = "http://your-solr-server:8983/solr/your-collection/select"
    
    # Your Solr query parameters - adjust based on your needs
    QUERY_PARAMS = {
        'q': '*:*',  # Your query
        'fq': f'date:[{(datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")}T00:00:00Z TO {(datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")}T23:59:59Z]',  # Yesterday's date filter
        'fl': 'account_number,field1,field2',  # Fields to return
        'rows': 10000,  # Max rows
        'wt': 'json'
    }
    
    # Email configuration (optional)
    EMAIL_CONFIG = {
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'use_tls': True,
        'from_email': 'your-email@company.com',
        'to_email': 'alerts@company.com',
        'username': 'your-email@company.com',
        'password': 'your-app-password'
    }
    
    # Initialize monitor
    monitor = SolrMonitor(SOLR_URL)
    dashboard = SolrMonitorDashboard(monitor)
    
    # Define notification callback
    def notification_callback(current, previous, comparison):
        monitor.send_email_notification(current, previous, comparison, EMAIL_CONFIG)
    
    # Define the monitoring job
    def run_monitor():
        logging.info("Starting Solr query monitoring...")
        monitor.monitor_query(QUERY_PARAMS, notification_callback)
        
    # Schedule the job to run every hour
    schedule.every().hour.do(run_monitor)
    
    # Run once immediately
    run_monitor()
    
    # Start scheduler in background thread
    def scheduler_thread():
        logging.info("Scheduler started. Monitoring every hour...")
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    scheduler = threading.Thread(target=scheduler_thread, daemon=True)
    scheduler.start()
    
    # Start web dashboard
    logging.info("Starting web dashboard on http://localhost:5000")
    dashboard.run(host='0.0.0.0', port=5000, debug=False)

# Original main function (command-line only)
def main():
    # Configuration
    SOLR_URL = "http://your-solr-server:8983/solr/your-collection/select"
    
    # Your Solr query parameters - adjust based on your needs
    QUERY_PARAMS = {
        'q': '*:*',  # Your query
        'fq': f'date:[{(datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")}T00:00:00Z TO {(datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")}T23:59:59Z]',  # Yesterday's date filter
        'fl': 'account_number,field1,field2',  # Fields to return
        'rows': 10000,  # Max rows
        'wt': 'json'
    }
    
    # Email configuration (optional)
    EMAIL_CONFIG = {
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'use_tls': True,
        'from_email': 'your-email@company.com',
        'to_email': 'alerts@company.com',
        'username': 'your-email@company.com',
        'password': 'your-app-password'
    }
    
    # Initialize monitor
    monitor = SolrMonitor(SOLR_URL)
    
    # Define notification callback
    def notification_callback(current, previous, comparison):
        monitor.send_email_notification(current, previous, comparison, EMAIL_CONFIG)
    
    # Define the monitoring job
    def run_monitor():
        logging.info("Starting Solr query monitoring...")
        monitor.monitor_query(QUERY_PARAMS, notification_callback)
        
    # Schedule the job to run every hour
    schedule.every().hour.do(run_monitor)
    
    # Run once immediately
    run_monitor()
    
    # Keep the scheduler running
    logging.info("Scheduler started. Monitoring every hour...")
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--no-dashboard':
        # Run command-line only version
        main()
    else:
        # Default to dashboard version
        main_with_dashboard()

        # Comparisons template
        with open('templates/comparisons.html', 'w') as f:
            f.write('''{% extends "base.html" %}

{% block title %}Comparisons - Solr Monitor{% endblock %}

{% block content %}
<div class="flex justify-between items-center mb-6">
    <h1 class="text-2xl font-bold">
        <i class="fas fa-balance-scale mr-2"></i>Detailed Comparisons
    </h1>
    <div class="space-x-2">
        <a href="/comparisons?hours=6" class="px-3 py-1 bg-blue-500 text-white rounded {% if hours_back == 6 %}bg-blue-700{% endif %}">6h</a>
        <a href="/comparisons?hours=24" class="px-3 py-1 bg-blue-500 text-white rounded {% if hours_back == 24 %}bg-blue-700{% endif %}">24h</a>
        <a href="/comparisons?hours=168" class="px-3 py-1 bg-blue-500 text-white rounded {% if hours_back == 168 %}bg-blue-700{% endif %}">7d</a>
    </div>
</div>

<div class="space-y-4">
    {% for comparison in comparisons %}
    <div class="bg-white p-6 rounded-lg shadow">
        <div class="flex justify-between items-start mb-4">
            <div>
                <h3 class="font-semibold text-lg">
                    {% if comparison.is_different %}
                        <i class="fas fa-exclamation-triangle text-yellow-500 mr-2"></i>
                        Changes Detected
                    {% else %}
                        <i class="fas fa-check-circle text-green-500 mr-2"></i>
                        No Changes
                    {% endif %}
                </h3>
                <p class="text-sm text-gray-600">{{ comparison.timestamp }}</p>
            </div>
            <div class="text-right">
                <p class="text-sm text-gray-600">Account Count</p>
                <p class="font-bold">
                    {{ comparison.current_count }}
                    {% if comparison.account_count_diff != 0 %}
                        <span class="{% if comparison.account_count_diff > 0 %}text-green-600{% else %}text-red-600{% endif %}">
                            ({{ comparison.account_count_diff | abs }}{% if comparison.account_count_diff > 0 %}+{% else %}-{% endif %})
                        </span>
                    {% endif %}
                </p>
            </div>
        </div>
        
        {% if comparison.is_different and comparison.differences %}
        <div class="bg-gray-50 p-4 rounded border-l-4 border-yellow-500">
            <h4 class="font-semibold mb-2">Differences:</h4>
            <pre class="text-xs bg-white p-2 rounded overflow-x-auto">{{ comparison.differences }}</pre>
        </div>
        {% endif %}
    </div>
    {% endfor %}
    
    {% if not comparisons %}
    <div class="bg-white p-8 rounded-lg shadow text-center">
        <i class="fas fa-search text-gray-400 text-4xl mb-4"></i>
        <p class="text-gray-600">No comparisons found for the selected time period.</p>
    </div>
    {% endif %}
</div>
{% endblock %}''')