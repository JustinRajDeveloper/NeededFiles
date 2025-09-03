import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Sample Report Generator for Solr Monitor
class SampleReportGenerator:
    
    @staticmethod
    def generate_sample_comparison_report() -> Dict[str, Any]:
        """Generate a sample comparison report showing different scenarios"""
        
        base_time = datetime.now()
        
        return {
            "report_generated": base_time.isoformat(),
            "report_period": "Last 24 hours",
            "total_checks": 24,
            "changes_detected": 3,
            "consistency_rate": "87.5%",
            
            "summary": {
                "stable_periods": 21,
                "periods_with_changes": 3,
                "max_account_count_change": -15,
                "most_recent_change": (base_time - timedelta(hours=2)).isoformat()
            },
            
            "detailed_comparisons": [
                {
                    "timestamp": (base_time - timedelta(hours=1)).isoformat(),
                    "query_hash": "abc123def456",
                    "status": "STABLE",
                    "account_count_diff": 0,
                    "previous_count": 1245,
                    "current_count": 1245,
                    "is_different": False,
                    "differences": None,
                    "message": "No changes detected - results consistent"
                },
                {
                    "timestamp": (base_time - timedelta(hours=2)).isoformat(),
                    "query_hash": "abc123def456", 
                    "status": "CHANGED",
                    "account_count_diff": -15,
                    "previous_count": 1260,
                    "current_count": 1245,
                    "is_different": True,
                    "differences": {
                        "accounts_removed": [
                            {"account_number": "ACC789012", "status": "CLOSED"},
                            {"account_number": "ACC345678", "status": "SUSPENDED"}
                        ],
                        "field_changes": {
                            "ACC123456": {
                                "balance": {"old": 1500.00, "new": 1750.00},
                                "last_updated": {"old": "2025-09-01T10:00:00Z", "new": "2025-09-02T14:30:00Z"}
                            }
                        }
                    },
                    "message": "15 accounts removed, balance updates detected"
                },
                {
                    "timestamp": (base_time - timedelta(hours=3)).isoformat(),
                    "query_hash": "abc123def456",
                    "status": "STABLE", 
                    "account_count_diff": 0,
                    "previous_count": 1260,
                    "current_count": 1260,
                    "is_different": False,
                    "differences": None,
                    "message": "No changes detected"
                },
                {
                    "timestamp": (base_time - timedelta(hours=6)).isoformat(),
                    "query_hash": "abc123def456",
                    "status": "CHANGED",
                    "account_count_diff": 3,
                    "previous_count": 1257,
                    "current_count": 1260,
                    "is_different": True,
                    "differences": {
                        "accounts_added": [
                            {"account_number": "ACC987654", "status": "ACTIVE", "balance": 2500.00},
                            {"account_number": "ACC456789", "status": "ACTIVE", "balance": 1200.00},
                            {"account_number": "ACC321098", "status": "PENDING", "balance": 0.00}
                        ]
                    },
                    "message": "3 new accounts added"
                },
                {
                    "timestamp": (base_time - timedelta(hours=12)).isoformat(),
                    "query_hash": "abc123def456",
                    "status": "FIELD_CHANGE",
                    "account_count_diff": 0,
                    "previous_count": 1257,
                    "current_count": 1257,
                    "is_different": True,
                    "differences": {
                        "field_changes": {
                            "ACC111222": {
                                "status": {"old": "PENDING", "new": "ACTIVE"}
                            },
                            "ACC333444": {
                                "balance": {"old": 500.00, "new": 750.00},
                                "last_transaction": {"old": "2025-08-30T09:15:00Z", "new": "2025-09-01T16:45:00Z"}
                            }
                        }
                    },
                    "message": "Account status and balance updates detected"
                }
            ],
            
            "alerts_sent": [
                {
                    "timestamp": (base_time - timedelta(hours=2)).isoformat(),
                    "alert_type": "ACCOUNT_COUNT_DECREASE",
                    "severity": "HIGH",
                    "message": "15 accounts removed from yesterday's results - investigate potential data issue"
                },
                {
                    "timestamp": (base_time - timedelta(hours=6)).isoformat(),
                    "alert_type": "NEW_ACCOUNTS_ADDED",
                    "severity": "MEDIUM", 
                    "message": "3 new accounts appeared in historical data - verify data consistency"
                }
            ],
            
            "trends": {
                "account_count_over_time": [
                    {"hour": -24, "count": 1254},
                    {"hour": -18, "count": 1254},
                    {"hour": -12, "count": 1257},
                    {"hour": -6, "count": 1260},
                    {"hour": -3, "count": 1260},
                    {"hour": -2, "count": 1245},
                    {"hour": -1, "count": 1245}
                ],
                "change_frequency": {
                    "no_change": 21,
                    "account_count_change": 2,
                    "field_only_change": 1
                }
            }
        }
    
    @staticmethod
    def generate_email_alert_sample() -> str:
        """Generate sample email alert content"""
        return """
        Subject: 🚨 Solr Query Results Changed - Alert
        
        Alert: Solr Query Results Have Changed
        
        Query executed at: 2025-09-02T14:00:00.123456
        Previous result from: 2025-09-02T13:00:00.654321
        
        Account Count Changes:
        - Previous: 1260 accounts
        - Current: 1245 accounts  
        - Difference: -15 accounts (DECREASE)
        
        Detected Differences:
        
        REMOVED ITEMS:
        - response['docs'][789]: Account ACC789012 (status: CLOSED)
        - response['docs'][345]: Account ACC345678 (status: SUSPENDED)
        - ... (13 more accounts)
        
        MODIFIED ITEMS:
        - response['docs'][123]['balance']: 1500.0 → 1750.0
        - response['docs'][123]['last_updated']: 2025-09-01T10:00:00Z → 2025-09-02T14:30:00Z
        
        IMPACT ANALYSIS:
        - 15 accounts (1.2%) missing from yesterday's data
        - This indicates potential data consistency issues
        - Historical query results should not change
        
        RECOMMENDED ACTIONS:
        1. Check Solr indexing process for yesterday's date
        2. Verify data pipeline integrity  
        3. Review account closure/suspension processes
        4. Validate source system data for 2025-09-01
        
        Please investigate the cause of these changes immediately.
        
        ---
        Solr Monitor System
        Generated: 2025-09-02T14:05:00Z
        """
    
    @staticmethod
    def generate_console_output_sample() -> str:
        """Generate sample console/log output"""
        return """
        2025-09-02 14:00:15,123 - INFO - Starting Solr query monitoring...
        2025-09-02 14:00:15,456 - INFO - Executing Solr query: http://solr-server:8983/solr/accounts/select
        2025-09-02 14:00:16,789 - INFO - Query completed successfully. Response size: 245KB
        2025-09-02 14:00:16,890 - INFO - Extracted account count: 1245
        2025-09-02 14:00:16,920 - INFO - Previous result found from 2025-09-02T13:00:00Z
        2025-09-02 14:00:17,145 - WARNING - Differences detected in query results!
        2025-09-02 14:00:17,146 - WARNING - Account count changed by: -15
        2025-09-02 14:00:17,147 - WARNING - Differences: {'iterable_item_removed': {"root['response']['docs'][789]": {'account_number': 'ACC789012', 'status': 'ACTIVE', 'balance': 1200.0}}}
        2025-09-02 14:00:17,890 - INFO - Comparison stored in database with ID: 1247
        2025-09-02 14:00:18,123 - INFO - Email alert sent to alerts@company.com
        2025-09-02 14:00:18,124 - INFO - Monitoring cycle completed
        
        2025-09-02 13:00:15,333 - INFO - Starting Solr query monitoring...
        2025-09-02 13:00:15,567 - INFO - Executing Solr query: http://solr-server:8983/solr/accounts/select  
        2025-09-02 13:00:16,234 - INFO - Query completed successfully. Response size: 248KB
        2025-09-02 13:00:16,334 - INFO - Extracted account count: 1260
        2025-09-02 13:00:16,364 - INFO - Previous result found from 2025-09-02T12:00:00Z
        2025-09-02 13:00:16,589 - INFO - No differences detected - results are consistent
        2025-09-02 13:00:16,634 - INFO - Comparison stored in database with ID: 1246
        2025-09-02 13:00:16,635 - INFO - Monitoring cycle completed
        """
        
    @staticmethod
    def generate_database_queries_sample() -> Dict[str, str]:
        """Generate sample SQL queries you can run for analysis"""
        return {
            "recent_changes": """
                SELECT 
                    datetime(c.timestamp) as change_time,
                    c.account_count_diff,
                    c.is_different,
                    r2.account_count as current_count,
                    r1.account_count as previous_count
                FROM comparisons c
                JOIN query_results r1 ON c.previous_result_id = r1.id  
                JOIN query_results r2 ON c.current_result_id = r2.id
                WHERE c.timestamp >= datetime('now', '-24 hours')
                AND c.is_different = 1
                ORDER BY c.timestamp DESC;
            """,
            
            "account_count_trend": """
                SELECT 
                    datetime(timestamp) as check_time,
                    account_count,
                    LAG(account_count) OVER (ORDER BY timestamp) as previous_count,
                    account_count - LAG(account_count) OVER (ORDER BY timestamp) as change
                FROM query_results 
                WHERE timestamp >= datetime('now', '-7 days')
                ORDER BY timestamp DESC;
            """,
            
            "stability_report": """
                SELECT 
                    DATE(timestamp) as date,
                    COUNT(*) as total_checks,
                    SUM(CASE WHEN is_different = 1 THEN 1 ELSE 0 END) as changes_detected,
                    ROUND(100.0 * SUM(CASE WHEN is_different = 0 THEN 1 ELSE 0 END) / COUNT(*), 2) as stability_percentage
                FROM comparisons 
                WHERE timestamp >= datetime('now', '-7 days')
                GROUP BY DATE(timestamp)
                ORDER BY date DESC;
            """,
            
            "largest_changes": """
                SELECT 
                    datetime(timestamp) as when_changed,
                    ABS(account_count_diff) as magnitude,
                    account_count_diff as actual_change,
                    CASE 
                        WHEN account_count_diff > 0 THEN 'INCREASE'
                        WHEN account_count_diff < 0 THEN 'DECREASE' 
                        ELSE 'NO_CHANGE'
                    END as change_type
                FROM comparisons 
                WHERE account_count_diff != 0
                ORDER BY ABS(account_count_diff) DESC
                LIMIT 10;
            """
        }

# Generate and display sample reports
def display_sample_reports():
    generator = SampleReportGenerator()
    
    print("=" * 80)
    print("SAMPLE SOLR MONITOR REPORT")
    print("=" * 80)
    
    # Main comparison report
    report = generator.generate_sample_comparison_report()
    
    print(f"Report Generated: {report['report_generated']}")
    print(f"Monitoring Period: {report['report_period']}")
    print(f"Total Checks: {report['total_checks']}")
    print(f"Changes Detected: {report['changes_detected']}")
    print(f"Data Consistency Rate: {report['consistency_rate']}")
    print()
    
    print("📊 SUMMARY")
    print("-" * 40)
    for key, value in report['summary'].items():
        print(f"{key.replace('_', ' ').title()}: {value}")
    print()
    
    print("📋 RECENT MONITORING RESULTS")
    print("-" * 40)
    for comparison in report['detailed_comparisons'][:3]:  # Show last 3
        status_emoji = "✅" if comparison['status'] == 'STABLE' else "⚠️"
        print(f"{status_emoji} {comparison['timestamp']}")
        print(f"   Status: {comparison['status']}")
        print(f"   Account Count: {comparison['current_count']} (Δ{comparison['account_count_diff']:+d})")
        print(f"   Message: {comparison['message']}")
        print()
    
    print("🚨 RECENT ALERTS")
    print("-" * 40)
    for alert in report['alerts_sent']:
        severity_emoji = "🔴" if alert['severity'] == 'HIGH' else "🟡"
        print(f"{severity_emoji} {alert['timestamp']} - {alert['alert_type']}")
        print(f"   {alert['message']}")
        print()
    
    print("📈 ACCOUNT COUNT TREND (Last 24 hours)")
    print("-" * 40)
    for trend in report['trends']['account_count_over_time']:
        print(f"   {trend['hour']:3d}h ago: {trend['count']} accounts")
    print()
    
    print("=" * 80)
    print("SAMPLE EMAIL ALERT")
    print("=" * 80)
    print(generator.generate_email_alert_sample())
    
    print("=" * 80)
    print("SAMPLE CONSOLE OUTPUT")  
    print("=" * 80)
    print(generator.generate_console_output_sample())
    
    print("=" * 80)
    print("USEFUL DATABASE QUERIES")
    print("=" * 80)
    queries = generator.generate_database_queries_sample()
    for name, query in queries.items():
        print(f"-- {name.replace('_', ' ').title()}")
        print(query)
        print()

if __name__ == "__main__":
    display_sample_reports()
