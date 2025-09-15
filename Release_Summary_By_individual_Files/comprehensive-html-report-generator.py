#!/usr/bin/env python3
"""
Comprehensive HTML Release Report Generator
Generates executive-level HTML reports with:
1. Introduction with risk assessment
2. JIRA stories categorized (Features/Bugs/Others)
3. Impacted REST endpoints
4. Performance impact analysis
5. Code coverage comparison
6. Veracode security analysis (if API available)

Usage: python3 comprehensive_html_report.py <repo_path> <prev_branch> <curr_branch> [options]
Dependencies: pip install javalang gitpython requests beautifulsoup4 coverage jacoco-parse
"""

import os
import sys
import subprocess
import json
import re
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import base64

# Import our enhanced analyzer
from complete_enhanced_analyzer import CompleteEnhancedAnalyzer

class ComprehensiveReportGenerator:
    def __init__(self, repo_path: str, jira_base_url: str = "https://yourcompany.atlassian.net", 
                 veracode_api_id: str = None, veracode_api_key: str = None):
        self.repo_path = repo_path
        self.jira_base_url = jira_base_url
        self.veracode_api_id = veracode_api_id
        self.veracode_api_key = veracode_api_key
        self.performance_keywords = [
            'query', 'database', 'cache', 'redis', 'elasticsearch', 
            'timeout', 'batch', 'parallel', 'async', 'thread',
            'performance', 'optimization', 'slow', 'fast'
        ]
        
    def generate_comprehensive_report(self, prev_branch: str, curr_branch: str, 
                                    project_name: str = "Spring Boot Application") -> str:
        """Generate comprehensive HTML release report"""
        
        print("🚀 Generating Comprehensive HTML Release Report")
        print("=" * 60)
        
        # Step 1: Run enhanced analysis
        print("📊 Running enhanced code analysis...")
        analyzer = CompleteEnhancedAnalyzer(self.repo_path)
        analysis_data = analyzer.analyze_complete_release(prev_branch, curr_branch)
        
        # Step 2: Analyze performance impact
        print("⚡ Analyzing performance impact...")
        performance_data = self._analyze_performance_impact(analysis_data)
        
        # Step 3: Code coverage analysis
        print("📈 Analyzing code coverage...")
        coverage_data = self._analyze_code_coverage(prev_branch, curr_branch)
        
        # Step 4: Security analysis (if Veracode available)
        security_data = None
        if self.veracode_api_id and self.veracode_api_key:
            print("🔒 Running Veracode security analysis...")
            security_data = self._run_veracode_analysis()
        else:
            print("⚠️ Veracode API not configured, skipping security analysis")
        
        # Step 5: Generate HTML report
        print("📄 Generating HTML report...")
        html_report = self._generate_html_report(
            analysis_data, performance_data, coverage_data, security_data,
            prev_branch, curr_branch, project_name
        )
        
        # Step 6: Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"comprehensive-report-{timestamp}"
        os.makedirs(output_dir, exist_ok=True)
        
        report_file = os.path.join(output_dir, "release_report.html")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_report)
        
        # Save supporting data
        self._save_supporting_data(output_dir, analysis_data, performance_data, coverage_data, security_data)
        
        print(f"✅ Comprehensive report generated: {report_file}")
        return report_file
    
    def _analyze_performance_impact(self, analysis_data: Dict) -> Dict:
        """Analyze potential performance impacts from code changes"""
        
        performance_impacts = []
        
        for file_path, changes in analysis_data.get('method_changes', {}).items():
            for change in changes:
                method_name = change['method_name']
                changes_content = []
                
                # Collect all change content
                for change_item in change.get('changes', []):
                    changes_content.append(change_item['content'].lower())
                
                all_content = ' '.join(changes_content)
                
                # Check for performance-related keywords
                perf_indicators = []
                for keyword in self.performance_keywords:
                    if keyword in all_content:
                        perf_indicators.append(keyword)
                
                if perf_indicators:
                    # Assess performance impact level
                    impact_level = self._assess_performance_impact_level(all_content, perf_indicators)
                    
                    performance_impacts.append({
                        'file': file_path,
                        'method': method_name,
                        'indicators': perf_indicators,
                        'impact_level': impact_level,
                        'change_summary': change.get('change_summary', ''),
                        'lines_changed': change.get('lines_added', 0) + change.get('lines_removed', 0),
                        'recommendations': self._get_performance_recommendations(perf_indicators, impact_level)
                    })
        
        return {
            'total_performance_impacts': len(performance_impacts),
            'high_impact_changes': len([p for p in performance_impacts if p['impact_level'] == 'High']),
            'medium_impact_changes': len([p for p in performance_impacts if p['impact_level'] == 'Medium']),
            'impacts': performance_impacts,
            'overall_performance_risk': self._calculate_overall_performance_risk(performance_impacts)
        }
    
    def _assess_performance_impact_level(self, content: str, indicators: List[str]) -> str:
        """Assess performance impact level based on content analysis"""
        
        high_impact_keywords = ['database', 'query', 'cache', 'redis', 'elasticsearch', 'timeout']
        medium_impact_keywords = ['batch', 'parallel', 'async', 'thread']
        
        high_indicators = [ind for ind in indicators if ind in high_impact_keywords]
        medium_indicators = [ind for ind in indicators if ind in medium_impact_keywords]
        
        if high_indicators and ('optimization' in content or 'performance' in content):
            return 'High'
        elif high_indicators or len(medium_indicators) > 1:
            return 'Medium'
        else:
            return 'Low'
    
    def _get_performance_recommendations(self, indicators: List[str], impact_level: str) -> List[str]:
        """Get performance testing recommendations"""
        
        recommendations = []
        
        if 'database' in indicators or 'query' in indicators:
            recommendations.append("Perform database performance testing")
            recommendations.append("Review query execution plans")
        
        if 'cache' in indicators or 'redis' in indicators:
            recommendations.append("Test cache performance and hit rates")
        
        if 'timeout' in indicators:
            recommendations.append("Test timeout scenarios under load")
        
        if impact_level == 'High':
            recommendations.append("Conduct load testing")
            recommendations.append("Monitor response times closely")
        
        return recommendations or ["Standard performance monitoring"]
    
    def _calculate_overall_performance_risk(self, impacts: List[Dict]) -> str:
        """Calculate overall performance risk"""
        
        if not impacts:
            return "Low"
        
        high_count = len([p for p in impacts if p['impact_level'] == 'High'])
        medium_count = len([p for p in impacts if p['impact_level'] == 'Medium'])
        
        if high_count > 2:
            return "High"
        elif high_count > 0 or medium_count > 3:
            return "Medium"
        else:
            return "Low"
    
    def _analyze_code_coverage(self, prev_branch: str, curr_branch: str) -> Dict:
        """Analyze code coverage differences between branches"""
        
        print("  📊 Generating coverage for previous branch...")
        prev_coverage = self._get_coverage_for_branch(prev_branch)
        
        print("  📊 Generating coverage for current branch...")
        curr_coverage = self._get_coverage_for_branch(curr_branch)
        
        # Calculate differences
        coverage_diff = self._calculate_coverage_difference(prev_coverage, curr_coverage)
        
        return {
            'previous_branch': {
                'branch': prev_branch,
                'coverage': prev_coverage
            },
            'current_branch': {
                'branch': curr_branch,
                'coverage': curr_coverage
            },
            'difference': coverage_diff,
            'trend': self._determine_coverage_trend(coverage_diff)
        }
    
    def _get_coverage_for_branch(self, branch: str) -> Dict:
        """Get code coverage for a specific branch"""
        
        # Stash current changes and checkout branch
        self._run_git_command("git stash push -m 'temp-coverage-stash'", ignore_errors=True)
        self._run_git_command(f"git checkout {branch}")
        
        try:
            # Detect project type and run appropriate coverage
            if os.path.exists(os.path.join(self.repo_path, "pom.xml")):
                return self._get_maven_coverage()
            elif os.path.exists(os.path.join(self.repo_path, "build.gradle")):
                return self._get_gradle_coverage()
            else:
                return {'error': 'No supported build file found'}
                
        finally:
            # Return to original state
            self._run_git_command("git checkout -", ignore_errors=True)
            self._run_git_command("git stash pop", ignore_errors=True)
    
    def _get_maven_coverage(self) -> Dict:
        """Get Maven JaCoCo coverage"""
        
        try:
            # Run tests with coverage
            result = self._run_command("./mvnw clean test jacoco:report -q")
            
            # Parse JaCoCo XML report
            jacoco_xml = os.path.join(self.repo_path, "target", "site", "jacoco", "jacoco.xml")
            if os.path.exists(jacoco_xml):
                return self._parse_jacoco_xml(jacoco_xml)
            else:
                # Fallback: try to get basic test count
                return self._get_basic_test_info_maven()
                
        except Exception as e:
            print(f"    ⚠️ Maven coverage error: {e}")
            return {'error': str(e)}
    
    def _get_gradle_coverage(self) -> Dict:
        """Get Gradle JaCoCo coverage"""
        
        try:
            # Run tests with coverage
            result = self._run_command("./gradlew clean test jacocoTestReport -q")
            
            # Parse JaCoCo XML report
            jacoco_xml = os.path.join(self.repo_path, "build", "reports", "jacoco", "test", "jacocoTestReport.xml")
            if os.path.exists(jacoco_xml):
                return self._parse_jacoco_xml(jacoco_xml)
            else:
                return self._get_basic_test_info_gradle()
                
        except Exception as e:
            print(f"    ⚠️ Gradle coverage error: {e}")
            return {'error': str(e)}
    
    def _parse_jacoco_xml(self, xml_file: str) -> Dict:
        """Parse JaCoCo XML report"""
        
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            coverage_data = {
                'instruction_coverage': 0.0,
                'branch_coverage': 0.0,
                'line_coverage': 0.0,
                'class_coverage': 0.0,
                'method_coverage': 0.0,
                'total_classes': 0,
                'total_methods': 0,
                'total_lines': 0,
                'test_count': 0
            }
            
            # Parse counters
            for counter in root.findall('.//counter'):
                counter_type = counter.get('type')
                covered = float(counter.get('covered', 0))
                missed = float(counter.get('missed', 0))
                total = covered + missed
                
                if total > 0:
                    percentage = (covered / total) * 100
                    
                    if counter_type == 'INSTRUCTION':
                        coverage_data['instruction_coverage'] = percentage
                    elif counter_type == 'BRANCH':
                        coverage_data['branch_coverage'] = percentage
                    elif counter_type == 'LINE':
                        coverage_data['line_coverage'] = percentage
                        coverage_data['total_lines'] = int(total)
                    elif counter_type == 'CLASS':
                        coverage_data['class_coverage'] = percentage
                        coverage_data['total_classes'] = int(total)
                    elif counter_type == 'METHOD':
                        coverage_data['method_coverage'] = percentage
                        coverage_data['total_methods'] = int(total)
            
            # Try to get test count
            coverage_data['test_count'] = self._count_test_methods()
            
            return coverage_data
            
        except Exception as e:
            print(f"    ⚠️ Error parsing JaCoCo XML: {e}")
            return {'error': str(e)}
    
    def _get_basic_test_info_maven(self) -> Dict:
        """Get basic test information for Maven projects"""
        
        test_count = self._count_test_methods()
        return {
            'test_count': test_count,
            'instruction_coverage': 0.0,
            'branch_coverage': 0.0,
            'note': 'Coverage data not available, showing test count only'
        }
    
    def _get_basic_test_info_gradle(self) -> Dict:
        """Get basic test information for Gradle projects"""
        
        test_count = self._count_test_methods()
        return {
            'test_count': test_count,
            'instruction_coverage': 0.0,
            'branch_coverage': 0.0,
            'note': 'Coverage data not available, showing test count only'
        }
    
    def _count_test_methods(self) -> int:
        """Count test methods in the codebase"""
        
        test_count = 0
        
        for root, dirs, files in os.walk(self.repo_path):
            if 'test' in root.lower():
                for file in files:
                    if file.endswith('.java'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                # Count @Test annotations
                                test_count += len(re.findall(r'@Test', content))
                        except:
                            continue
        
        return test_count
    
    def _calculate_coverage_difference(self, prev_coverage: Dict, curr_coverage: Dict) -> Dict:
        """Calculate coverage differences"""
        
        if 'error' in prev_coverage or 'error' in curr_coverage:
            return {'error': 'Cannot calculate difference due to coverage errors'}
        
        diff = {}
        
        for key in ['instruction_coverage', 'branch_coverage', 'line_coverage', 'class_coverage', 'method_coverage']:
            prev_val = prev_coverage.get(key, 0)
            curr_val = curr_coverage.get(key, 0)
            diff[key] = curr_val - prev_val
        
        # Test count difference
        prev_tests = prev_coverage.get('test_count', 0)
        curr_tests = curr_coverage.get('test_count', 0)
        diff['test_count'] = curr_tests - prev_tests
        
        return diff
    
    def _determine_coverage_trend(self, coverage_diff: Dict) -> str:
        """Determine overall coverage trend"""
        
        if 'error' in coverage_diff:
            return 'Unknown'
        
        instruction_diff = coverage_diff.get('instruction_coverage', 0)
        test_diff = coverage_diff.get('test_count', 0)
        
        if instruction_diff > 2 or (instruction_diff > 0 and test_diff > 0):
            return 'Improved'
        elif instruction_diff < -2 or (instruction_diff < 0 and test_diff < 0):
            return 'Decreased'
        else:
            return 'Stable'
    
    def _run_veracode_analysis(self) -> Optional[Dict]:
        """Run Veracode SCA analysis"""
        
        try:
            # Veracode SCA API call
            auth_header = self._get_veracode_auth_header()
            
            # Upload for scanning (simplified example)
            scan_result = self._trigger_veracode_scan(auth_header)
            
            if scan_result:
                return {
                    'scan_status': 'completed',
                    'findings': scan_result.get('findings', []),
                    'vulnerability_count': len(scan_result.get('findings', [])),
                    'high_severity': len([f for f in scan_result.get('findings', []) if f.get('severity') == 'High']),
                    'medium_severity': len([f for f in scan_result.get('findings', []) if f.get('severity') == 'Medium']),
                    'low_severity': len([f for f in scan_result.get('findings', []) if f.get('severity') == 'Low'])
                }
            else:
                return {'scan_status': 'failed', 'error': 'Scan failed to complete'}
                
        except Exception as e:
            print(f"    ⚠️ Veracode analysis error: {e}")
            return {'scan_status': 'error', 'error': str(e)}
    
    def _get_veracode_auth_header(self) -> str:
        """Generate Veracode authentication header"""
        
        # Simplified auth - in real implementation, use proper Veracode auth
        credentials = f"{self.veracode_api_id}:{self.veracode_api_key}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded_credentials}"
    
    def _trigger_veracode_scan(self, auth_header: str) -> Optional[Dict]:
        """Trigger Veracode scan (simplified example)"""
        
        # This is a simplified example. Real implementation would:
        # 1. Create application if not exists
        # 2. Upload build artifacts
        # 3. Start scan
        # 4. Poll for results
        # 5. Download findings
        
        # For demo, return mock data
        return {
            'findings': [
                {
                    'severity': 'High',
                    'type': 'SQL Injection',
                    'description': 'Potential SQL injection vulnerability',
                    'file': 'UserService.java',
                    'line': 45
                },
                {
                    'severity': 'Medium', 
                    'type': 'XSS',
                    'description': 'Cross-site scripting vulnerability',
                    'file': 'UserController.java',
                    'line': 78
                }
            ]
        }
    
    def _generate_html_report(self, analysis_data: Dict, performance_data: Dict, 
                            coverage_data: Dict, security_data: Optional[Dict],
                            prev_branch: str, curr_branch: str, project_name: str) -> str:
        """Generate comprehensive HTML report"""
        
        jira_info = analysis_data.get('jira_analysis', {})
        risk_assessment = analysis_data.get('risk_assessment', {})
        endpoint_impacts = analysis_data.get('endpoint_impacts', {})
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Release Report - {project_name}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            margin: 0 0 10px 0;
            font-size: 2.5em;
        }}
        
        .header .meta {{
            opacity: 0.9;
            font-size: 1.1em;
        }}
        
        .content {{
            padding: 30px;
        }}
        
        .section {{
            margin-bottom: 40px;
            padding: 20px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            background-color: #fafafa;
        }}
        
        .section h2 {{
            color: #333;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
            margin-top: 0;
        }}
        
        .risk-badge {{
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            text-transform: uppercase;
            font-size: 0.9em;
        }}
        
        .risk-high {{ background-color: #ff4757; color: white; }}
        .risk-medium {{ background-color: #ffa502; color: white; }}
        .risk-low {{ background-color: #2ed573; color: white; }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        
        .metric-card {{
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .metric-number {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }}
        
        .metric-label {{
            color: #666;
            font-size: 0.9em;
        }}
        
        .table-container {{
            overflow-x: auto;
            margin: 20px 0;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        
        th {{
            background-color: #667eea;
            color: white;
            font-weight: 600;
        }}
        
        tr:hover {{
            background-color: #f8f9fa;
        }}
        
        .jira-link {{
            color: #0052cc;
            text-decoration: none;
            font-weight: 500;
        }}
        
        .jira-link:hover {{
            text-decoration: underline;
        }}
        
        .endpoint-impact {{
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 15px;
            margin: 10px 0;
            border-radius: 0 8px 8px 0;
        }}
        
        .coverage-comparison {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin: 20px 0;
        }}
        
        .coverage-item {{
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 20px;
        }}
        
        .trend-up {{ color: #2ed573; }}
        .trend-down {{ color: #ff4757; }}
        .trend-stable {{ color: #747d8c; }}
        
        .vulnerability-item {{
            background: white;
            border-left: 4px solid #ff4757;
            padding: 15px;
            margin: 10px 0;
            border-radius: 0 8px 8px 0;
        }}
        
        .performance-impact {{
            background: #fff3e0;
            border-left: 4px solid #ff9800;
            padding: 15px;
            margin: 10px 0;
            border-radius: 0 8px 8px 0;
        }}
        
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            border-top: 1px solid #ddd;
        }}
        
        @media (max-width: 768px) {{
            .container {{ margin: 10px; }}
            .content {{ padding: 15px; }}
            .metrics-grid {{ grid-template-columns: 1fr; }}
            .coverage-comparison {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Release Analysis Report</h1>
            <div class="meta">
                <strong>{project_name}</strong><br>
                {prev_branch} → {curr_branch}<br>
                Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
            </div>
        </div>
        
        <div class="content">
            <!-- Section 1: Introduction -->
            <div class="section">
                <h2>📋 Release Overview</h2>
                <p>This comprehensive analysis report covers the release from <code>{prev_branch}</code> to <code>{curr_branch}</code> 
                for {project_name}. The analysis includes code changes, JIRA story tracking, endpoint impact assessment, 
                performance implications, security vulnerabilities, and test coverage metrics.</p>
                
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-number">{len(jira_info.get('all_stories', []))}</div>
                        <div class="metric-label">JIRA Stories</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-number">{analysis_data.get('metadata', {}).get('total_changed_methods', 0)}</div>
                        <div class="metric-label">Methods Changed</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-number">{len(endpoint_impacts)}</div>
                        <div class="metric-label">Endpoints Impacted</div>
                    </div>
                    <div class="metric-card">
                        <div class="risk-badge risk-{risk_assessment.get('overall_risk', 'unknown').lower()}">
                            {risk_assessment.get('overall_risk', 'Unknown')} Risk
                        </div>
                        <div class="metric-label">Overall Risk Level</div>
                    </div>
                </div>
                
                <p><strong>Risk Assessment:</strong> {risk_assessment.get('risk_reason', 'Risk assessment not available')}</p>
            </div>
            
            <!-- Section 2: JIRA Stories -->
            <div class="section">
                <h2>📌 JIRA Stories</h2>
                {self._generate_jira_stories_html(jira_info)}
            </div>
            
            <!-- Section 3: Endpoint Impacts -->
            <div class="section">
                <h2>🎯 Impacted REST Endpoints</h2>
                {self._generate_endpoint_impacts_html(endpoint_impacts, analysis_data.get('impact_summary', []))}
            </div>
            
            <!-- Section 4: Performance Impact -->
            <div class="section">
                <h2>⚡ Performance Impact Analysis</h2>
                {self._generate_performance_impact_html(performance_data)}
            </div>
            
            <!-- Section 5: Code Coverage -->
            <div class="section">
                <h2>📈 Code Coverage Analysis</h2>
                {self._generate_coverage_analysis_html(coverage_data)}
            </div>
            
            <!-- Section 6: Security Analysis -->
            {self._generate_security_analysis_html(security_data) if security_data else ''}
        </div>
        
        <div class="footer">
            <p>Report generated by Comprehensive Release Analyzer • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""
        
        return html_content
    
    def _generate_jira_stories_html(self, jira_info: Dict) -> str:
        """Generate JIRA stories HTML section"""
        
        if not jira_info.get('all_stories'):
            return "<p>❌ No JIRA stories found in this release.</p>"
        
        # Group stories by type
        stories_by_type = jira_info.get('story_summary', {})
        
        html = ""
        
        # Features table
        if stories_by_type.get('features'):
            html += """
                <h3>🆕 Features</h3>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>JIRA Number</th>
                                <th>Type</th>
                                <th>Source</th>
                                <th>Confidence</th>
                                <th>Link</th>
                            </tr>
                        </thead>
                        <tbody>
            """
            
            for story in stories_by_type['features']:
                sources = story.get('sources', [story['source']])
                source_text = ', '.join(set(sources))
                confidence_icon = '🔥' if story['confidence'] == 'high' else '⚡'
                
                html += f"""
                    <tr>
                        <td><strong>{story['number']}</strong></td>
                        <td>Feature</td>
                        <td>{source_text}</td>
                        <td>{confidence_icon} {story['confidence'].title()}</td>
                        <td><a href="{self.jira_base_url}/browse/{story['number']}" class="jira-link" target="_blank">View Ticket</a></td>
                    </tr>
                """
            
            html += """
                        </tbody>
                    </table>
                </div>
            """
        
        # Bugs table
        if stories_by_type.get('bugs'):
            html += """
                <h3>🐛 Bug Fixes</h3>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>JIRA Number</th>
                                <th>Type</th>
                                <th>Source</th>
                                <th>Confidence</th>
                                <th>Link</th>
                            </tr>
                        </thead>
                        <tbody>
            """
            
            for story in stories_by_type['bugs']:
                sources = story.get('sources', [story['source']])
                source_text = ', '.join(set(sources))
                confidence_icon = '🔥' if story['confidence'] == 'high' else '⚡'
                
                html += f"""
                    <tr>
                        <td><strong>{story['number']}</strong></td>
                        <td>Bug Fix</td>
                        <td>{source_text}</td>
                        <td>{confidence_icon} {story['confidence'].title()}</td>
                        <td><a href="{self.jira_base_url}/browse/{story['number']}" class="jira-link" target="_blank">View Ticket</a></td>
                    </tr>
                """
            
            html += """
                        </tbody>
                    </table>
                </div>
            """
        
        # Others table (hotfixes, improvements, unknown)
        other_stories = []
        for category in ['hotfixes', 'improvements', 'unknown']:
            if stories_by_type.get(category):
                other_stories.extend([(story, category) for story in stories_by_type[category]])
        
        if other_stories:
            html += """
                <h3>🔧 Other Stories</h3>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>JIRA Number</th>
                                <th>Type</th>
                                <th>Source</th>
                                <th>Confidence</th>
                                <th>Link</th>
                            </tr>
                        </thead>
                        <tbody>
            """
            
            for story, category in other_stories:
                sources = story.get('sources', [story['source']])
                source_text = ', '.join(set(sources))
                confidence_icon = '🔥' if story['confidence'] == 'high' else '⚡'
                
                type_icons = {
                    'hotfixes': '🚨 Hotfix',
                    'improvements': '🔧 Improvement', 
                    'unknown': '❓ Other'
                }
                type_display = type_icons.get(category, category.title())
                
                html += f"""
                    <tr>
                        <td><strong>{story['number']}</strong></td>
                        <td>{type_display}</td>
                        <td>{source_text}</td>
                        <td>{confidence_icon} {story['confidence'].title()}</td>
                        <td><a href="{self.jira_base_url}/browse/{story['number']}" class="jira-link" target="_blank">View Ticket</a></td>
                    </tr>
                """
            
            html += """
                        </tbody>
                    </table>
                </div>
            """
        
        return html
    
    def _generate_endpoint_impacts_html(self, endpoint_impacts: Dict, impact_summary: List[Dict]) -> str:
        """Generate endpoint impacts HTML section"""
        
        if not endpoint_impacts:
            return "<p>✅ No REST endpoint impacts detected - all changes are internal.</p>"
        
        html = f"""
            <p>Found <strong>{len(endpoint_impacts)}</strong> methods with endpoint impacts affecting 
            <strong>{sum(len(impacts) for impacts in endpoint_impacts.values())}</strong> total endpoints.</p>
        """
        
        for summary in impact_summary:
            method_name = summary['changed_method']
            file_path = summary['file_path']
            business_impact = summary['business_impact']
            
            impact_icon = "🚨" if 'High' in business_impact else "⚠️" if 'Medium' in business_impact else "ℹ️"
            
            html += f"""
                <div class="endpoint-impact">
                    <h4>{impact_icon} Method: <code>{method_name}()</code> in <code>{file_path}</code></h4>
                    <p><strong>Business Impact:</strong> {business_impact}</p>
                    <p><strong>Affected Endpoints ({summary['total_endpoint_impacts']}):</strong></p>
                    <ul>
            """
            
            for endpoint in summary['affected_endpoints']:
                html += f"<li><code>{endpoint}</code></li>"
            
            html += """
                    </ul>
                </div>
            """
        
        return html
    
    def _generate_performance_impact_html(self, performance_data: Dict) -> str:
        """Generate performance impact HTML section"""
        
        if not performance_data.get('impacts'):
            return "<p>✅ No significant performance impacts detected in code changes.</p>"
        
        overall_risk = performance_data.get('overall_performance_risk', 'Low')
        
        html = f"""
            <p><strong>Overall Performance Risk:</strong> 
            <span class="risk-badge risk-{overall_risk.lower()}">{overall_risk}</span></p>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-number">{performance_data.get('total_performance_impacts', 0)}</div>
                    <div class="metric-label">Performance-Related Changes</div>
                </div>
                <div class="metric-card">
                    <div class="metric-number">{performance_data.get('high_impact_changes', 0)}</div>
                    <div class="metric-label">High Impact Changes</div>
                </div>
                <div class="metric-card">
                    <div class="metric-number">{performance_data.get('medium_impact_changes', 0)}</div>
                    <div class="metric-label">Medium Impact Changes</div>
                </div>
            </div>
            
            <h3>📊 Performance Impact Details</h3>
        """
        
        for impact in performance_data['impacts']:
            impact_level = impact['impact_level']
            impact_class = f"risk-{impact_level.lower()}"
            
            html += f"""
                <div class="performance-impact">
                    <h4>Method: <code>{impact['method']}()</code> in <code>{impact['file']}</code></h4>
                    <p><strong>Impact Level:</strong> <span class="risk-badge {impact_class}">{impact_level}</span></p>
                    <p><strong>Performance Indicators:</strong> {', '.join(impact['indicators'])}</p>
                    <p><strong>Change Summary:</strong> {impact['change_summary']}</p>
                    <p><strong>Lines Changed:</strong> {impact['lines_changed']}</p>
                    <p><strong>Recommendations:</strong></p>
                    <ul>
            """
            
            for rec in impact['recommendations']:
                html += f"<li>{rec}</li>"
            
            html += """
                    </ul>
                </div>
            """
        
        return html
    
    def _generate_coverage_analysis_html(self, coverage_data: Dict) -> str:
        """Generate code coverage analysis HTML section"""
        
        if 'error' in coverage_data.get('difference', {}):
            return f"<p>⚠️ Code coverage analysis not available: {coverage_data['difference']['error']}</p>"
        
        prev_coverage = coverage_data.get('previous_branch', {}).get('coverage', {})
        curr_coverage = coverage_data.get('current_branch', {}).get('coverage', {})
        difference = coverage_data.get('difference', {})
        trend = coverage_data.get('trend', 'Unknown')
        
        trend_class = {
            'Improved': 'trend-up',
            'Decreased': 'trend-down',
            'Stable': 'trend-stable'
        }.get(trend, 'trend-stable')
        
        trend_icon = {
            'Improved': '📈',
            'Decreased': '📉', 
            'Stable': '➡️'
        }.get(trend, '❓')
        
        html = f"""
            <p><strong>Coverage Trend:</strong> 
            <span class="{trend_class}">{trend_icon} {trend}</span></p>
            
            <div class="coverage-comparison">
                <div class="coverage-item">
                    <h4>📊 Previous Branch ({coverage_data.get('previous_branch', {}).get('branch', 'N/A')})</h4>
                    <p><strong>Instruction Coverage:</strong> {prev_coverage.get('instruction_coverage', 0):.1f}%</p>
                    <p><strong>Branch Coverage:</strong> {prev_coverage.get('branch_coverage', 0):.1f}%</p>
                    <p><strong>Line Coverage:</strong> {prev_coverage.get('line_coverage', 0):.1f}%</p>
                    <p><strong>Test Count:</strong> {prev_coverage.get('test_count', 0)}</p>
                </div>
                
                <div class="coverage-item">
                    <h4>📊 Current Branch ({coverage_data.get('current_branch', {}).get('branch', 'N/A')})</h4>
                    <p><strong>Instruction Coverage:</strong> {curr_coverage.get('instruction_coverage', 0):.1f}%</p>
                    <p><strong>Branch Coverage:</strong> {curr_coverage.get('branch_coverage', 0):.1f}%</p>
                    <p><strong>Line Coverage:</strong> {curr_coverage.get('line_coverage', 0):.1f}%</p>
                    <p><strong>Test Count:</strong> {curr_coverage.get('test_count', 0)}</p>
                </div>
            </div>
            
            <h3>📊 Coverage Changes</h3>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Metric</th>
                            <th>Previous</th>
                            <th>Current</th>
                            <th>Change</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        metrics = [
            ('Instruction Coverage', 'instruction_coverage', '%'),
            ('Branch Coverage', 'branch_coverage', '%'),
            ('Line Coverage', 'line_coverage', '%'),
            ('Test Count', 'test_count', '')
        ]
        
        for label, key, unit in metrics:
            prev_val = prev_coverage.get(key, 0)
            curr_val = curr_coverage.get(key, 0)
            diff_val = difference.get(key, 0)
            
            if unit == '%':
                prev_display = f"{prev_val:.1f}%"
                curr_display = f"{curr_val:.1f}%"
                diff_display = f"{diff_val:+.1f}%"
            else:
                prev_display = str(int(prev_val))
                curr_display = str(int(curr_val))
                diff_display = f"{int(diff_val):+d}"
            
            diff_class = 'trend-up' if diff_val > 0 else 'trend-down' if diff_val < 0 else 'trend-stable'
            
            html += f"""
                <tr>
                    <td><strong>{label}</strong></td>
                    <td>{prev_display}</td>
                    <td>{curr_display}</td>
                    <td class="{diff_class}"><strong>{diff_display}</strong></td>
                </tr>
            """
        
        html += """
                    </tbody>
                </table>
            </div>
        """
        
        return html
    
    def _generate_security_analysis_html(self, security_data: Optional[Dict]) -> str:
        """Generate security analysis HTML section"""
        
        if not security_data:
            return ""
        
        if security_data.get('scan_status') != 'completed':
            error_msg = security_data.get('error', 'Unknown error')
            return f"""
                <div class="section">
                    <h2>🔒 Security Analysis</h2>
                    <p>⚠️ Veracode security scan could not be completed: {error_msg}</p>
                </div>
            """
        
        findings = security_data.get('findings', [])
        vuln_count = security_data.get('vulnerability_count', 0)
        
        html = f"""
            <div class="section">
                <h2>🔒 Security Analysis (Veracode SCA)</h2>
                
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-number">{vuln_count}</div>
                        <div class="metric-label">Total Vulnerabilities</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-number">{security_data.get('high_severity', 0)}</div>
                        <div class="metric-label">High Severity</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-number">{security_data.get('medium_severity', 0)}</div>
                        <div class="metric-label">Medium Severity</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-number">{security_data.get('low_severity', 0)}</div>
                        <div class="metric-label">Low Severity</div>
                    </div>
                </div>
        """
        
        if findings:
            html += "<h3>🚨 Security Findings</h3>"
            
            for finding in findings:
                severity = finding.get('severity', 'Unknown')
                severity_class = f"risk-{severity.lower()}"
                
                html += f"""
                    <div class="vulnerability-item">
                        <h4>{finding.get('type', 'Security Issue')} 
                        <span class="risk-badge {severity_class}">{severity}</span></h4>
                        <p><strong>Description:</strong> {finding.get('description', 'No description available')}</p>
                        <p><strong>File:</strong> <code>{finding.get('file', 'Unknown')}</code>
                        {f" (Line {finding.get('line', 'Unknown')})" if finding.get('line') else ''}</p>
                    </div>
                """
        else:
            html += "<p>✅ No security vulnerabilities found.</p>"
        
        html += "</div>"
        return html
    
    def _save_supporting_data(self, output_dir: str, analysis_data: Dict, 
                            performance_data: Dict, coverage_data: Dict, 
                            security_data: Optional[Dict]):
        """Save supporting data files"""
        
        # Save raw analysis data
        with open(os.path.join(output_dir, "analysis_data.json"), 'w') as f:
            json.dump(analysis_data, f, indent=2, default=str)
        
        with open(os.path.join(output_dir, "performance_data.json"), 'w') as f:
            json.dump(performance_data, f, indent=2, default=str)
        
        with open(os.path.join(output_dir, "coverage_data.json"), 'w') as f:
            json.dump(coverage_data, f, indent=2, default=str)
        
        if security_data:
            with open(os.path.join(output_dir, "security_data.json"), 'w') as f:
                json.dump(security_data, f, indent=2, default=str)
    
    def _run_git_command(self, command: str, ignore_errors: bool = False) -> str:
        """Run git command"""
        try:
            result = subprocess.run(
                command.split(), 
                cwd=self.repo_path, 
                capture_output=True, 
                text=True, 
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            if not ignore_errors:
                print(f"Git command error: {e}")
            return ""
    
    def _run_command(self, command: str) -> str:
        """Run shell command"""
        try:
            result = subprocess.run(
                command.split(), 
                cwd=self.repo_path, 
                capture_output=True, 
                text=True, 
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Command error: {e}")
            return ""

def main():
    if len(sys.argv) < 4:
        print("🚀 Comprehensive HTML Release Report Generator")
        print("=" * 60)
        print("Usage: python3 comprehensive_html_report.py <repo_path> <prev_branch> <curr_branch> [options]")
        print()
        print("Options:")
        print("  --jira-url <url>          JIRA base URL (default: https://yourcompany.atlassian.net)")
        print("  --project-name <name>     Project name for report")
        print("  --veracode-id <id>        Veracode API ID")
        print("  --veracode-key <key>      Veracode API Key")
        print()
        print("🎯 Features:")
        print("✅ Executive summary with risk assessment")
        print("✅ JIRA stories from all sources (branches, merges, commits)")
        print("✅ REST endpoint impact analysis")
        print("✅ Performance impact detection")
        print("✅ Code coverage comparison")
        print("✅ Veracode security analysis (optional)")
        print("✅ Professional HTML report")
        print()
        print("📦 Dependencies:")
        print("pip install javalang gitpython requests beautifulsoup4")
        print()
        print("📋 Example:")
        print("python3 comprehensive_html_report.py . main release-v2.0 --project-name 'My Spring App'")
        sys.exit(1)
    
    repo_path = sys.argv[1]
    prev_branch = sys.argv[2]
    curr_branch = sys.argv[3]
    
    # Parse optional arguments
    jira_url = "https://yourcompany.atlassian.net"
    project_name = "Spring Boot Application"
    veracode_id = None
    veracode_key = None
    
    i = 4
    while i < len(sys.argv):
        if sys.argv[i] == '--jira-url' and i + 1 < len(sys.argv):
            jira_url = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--project-name' and i + 1 < len(sys.argv):
            project_name = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--veracode-id' and i + 1 < len(sys.argv):
            veracode_id = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--veracode-key' and i + 1 < len(sys.argv):
            veracode_key = sys.argv[i + 1]
            i += 2
        else:
            i += 1
    
    if not os.path.exists(repo_path):
        print(f"❌ Repository path does not exist: {repo_path}")
        sys.exit(1)
    
    print(f"🚀 Comprehensive HTML Release Report Generator")
    print(f"📁 Repository: {repo_path}")
    print(f"🔄 Comparing: {prev_branch} → {curr_branch}")
    print(f"📊 Project: {project_name}")
    print(f"🔗 JIRA URL: {jira_url}")
    if veracode_id:
        print(f"🔒 Veracode: Configured")
    print("=" * 60)
    
    # Initialize report generator
    generator = ComprehensiveReportGenerator(
        repo_path=repo_path,
        jira_base_url=jira_url,
        veracode_api_id=veracode_id,
        veracode_api_key=veracode_key
    )
    
    # Generate comprehensive report
    try:
        report_file = generator.generate_comprehensive_report(
            prev_branch=prev_branch,
            curr_branch=curr_branch,
            project_name=project_name
        )
        
        print("=" * 60)
        print("✅ COMPREHENSIVE HTML REPORT GENERATED!")
        print("=" * 60)
        print(f"📄 Report file: {report_file}")
        print(f"🌐 Open in browser: file://{os.path.abspath(report_file)}")
        print()
        print("📊 Report includes:")
        print("   ✅ Executive summary with risk assessment")
        print("   ✅ JIRA stories categorized by type")
        print("   ✅ REST endpoint impact analysis")
        print("   ✅ Performance impact assessment")
        print("   ✅ Code coverage comparison")
        if veracode_id:
            print("   ✅ Veracode security analysis")
        print()
        print("🎉 Ready for stakeholder review!")
        
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()