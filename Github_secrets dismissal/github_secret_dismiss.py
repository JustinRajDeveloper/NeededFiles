#!/usr/bin/env python3
"""
GitHub Secret Scanning Alert Bulk Dismiss Script

This script allows you to bulk dismiss GitHub secret scanning alerts
by providing a list of alert URLs or alert numbers.

Requirements:
- requests library: pip install requests
- GitHub personal access token with repo and security_events scopes
"""

import requests
import re
import sys
from urllib.parse import urlparse
import json
import time

class GitHubSecretDismisser:
    def __init__(self, token):
        """Initialize with GitHub personal access token"""
        self.token = token
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'GitHub-Secret-Dismisser'
        })
        
    def parse_alert_url(self, url):
        """
        Parse GitHub secret scanning alert URL to extract owner, repo, and alert_number
        Expected format: https://github.com/{owner}/{repo}/security/secret-scanning/{alert_number}
        """
        pattern = r'github\.com/([^/]+)/([^/]+)/security/secret-scanning/(\d+)'
        match = re.search(pattern, url)
        
        if match:
            return {
                'owner': match.group(1),
                'repo': match.group(2),
                'alert_number': int(match.group(3))
            }
        return None
    
    def dismiss_alert(self, owner, repo, alert_number, reason="false_positive", comment="Bulk dismissed"):
        """
        Dismiss a single secret scanning alert
        
        Args:
            owner: Repository owner
            repo: Repository name  
            alert_number: Alert number
            reason: Dismissal reason ('false_positive', 'wont_fix', 'revoked', 'pattern_edited', 'pattern_deleted')
            comment: Optional dismissal comment
        """
        url = f'https://api.github.com/repos/{owner}/{repo}/secret-scanning/alerts/{alert_number}'
        
        payload = {
            'state': 'dismissed',
            'dismissed_reason': reason,
            'dismissed_comment': comment
        }
        
        try:
            response = self.session.patch(url, json=payload)
            
            if response.status_code == 200:
                print(f"✅ Successfully dismissed alert {alert_number} in {owner}/{repo}")
                return True
            elif response.status_code == 404:
                print(f"❌ Alert {alert_number} not found in {owner}/{repo}")
                return False
            elif response.status_code == 422:
                print(f"❌ Alert {alert_number} in {owner}/{repo} is already dismissed or invalid state")
                return False
            else:
                print(f"❌ Failed to dismiss alert {alert_number} in {owner}/{repo}: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error dismissing alert {alert_number} in {owner}/{repo}: {e}")
            return False
    
    def dismiss_alerts_from_urls(self, urls, reason="false_positive", comment="Bulk dismissed", delay=0.5):
        """
        Dismiss multiple alerts from a list of URLs
        
        Args:
            urls: List of GitHub secret scanning alert URLs
            reason: Dismissal reason
            comment: Dismissal comment
            delay: Delay between requests to avoid rate limiting
        """
        successful = 0
        failed = 0
        
        print(f"Starting bulk dismissal of {len(urls)} alerts...")
        print(f"Reason: {reason}")
        print(f"Comment: {comment}")
        print("-" * 50)
        
        for i, url in enumerate(urls, 1):
            url = url.strip()
            if not url:
                continue
                
            print(f"[{i}/{len(urls)}] Processing: {url}")
            
            # Parse the URL
            alert_info = self.parse_alert_url(url)
            if not alert_info:
                print(f"❌ Invalid URL format: {url}")
                failed += 1
                continue
            
            # Dismiss the alert
            if self.dismiss_alert(
                alert_info['owner'], 
                alert_info['repo'], 
                alert_info['alert_number'],
                reason,
                comment
            ):
                successful += 1
            else:
                failed += 1
            
            # Add delay to avoid rate limiting
            if delay > 0 and i < len(urls):
                time.sleep(delay)
        
        print("-" * 50)
        print(f"Bulk dismissal completed!")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"📊 Total processed: {len(urls)}")

def load_urls_from_file(filename):
    """Load URLs from a text file (one URL per line)"""
    try:
        with open(filename, 'r') as f:
            urls = [line.strip() for line in f.readlines() if line.strip()]
        return urls
    except FileNotFoundError:
        print(f"❌ File {filename} not found")
        return []

def main():
    # Configuration
    GITHUB_TOKEN = "your_github_token_here"  # Replace with your GitHub token
    
    # Dismissal settings
    DISMISSAL_REASON = "false_positive"  # Options: false_positive, wont_fix, revoked, pattern_edited, pattern_deleted
    DISMISSAL_COMMENT = "Bulk dismissed via script"
    REQUEST_DELAY = 0.5  # Seconds between requests
    
    # Example usage - choose one of these methods:
    
    # Method 1: URLs directly in the script
    alert_urls = [
        "https://github.com/owner/repo/security/secret-scanning/1",
        "https://github.com/owner/repo/security/secret-scanning/2",
        "https://github.com/owner/repo/security/secret-scanning/3",
        # Add more URLs here
    ]
    
    # Method 2: Load URLs from a file
    # alert_urls = load_urls_from_file('alert_urls.txt')
    
    # Validate token
    if GITHUB_TOKEN == "your_github_token_here":
        print("❌ Please set your GitHub token in the GITHUB_TOKEN variable")
        sys.exit(1)
    
    if not alert_urls:
        print("❌ No alert URLs provided")
        sys.exit(1)
    
    # Create dismisser and process alerts
    dismisser = GitHubSecretDismisser(GITHUB_TOKEN)
    dismisser.dismiss_alerts_from_urls(
        alert_urls, 
        reason=DISMISSAL_REASON,
        comment=DISMISSAL_COMMENT,
        delay=REQUEST_DELAY
    )

if __name__ == "__main__":
    main()
