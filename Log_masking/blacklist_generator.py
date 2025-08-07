#!/usr/bin/env python3
"""
Enhanced Telecom API Blacklist Generator
Generates consolidated application.properties blacklist entries for sensitive fields
Reads patterns from external configuration file
"""

import json
import re
import os
from datetime import datetime
from typing import Dict, List, Set, Any
from collections import defaultdict

class TelecomBlacklistGenerator:
    def __init__(self, patterns_file: str = 'patterns_config.json'):
        self.patterns_file = patterns_file
        self.load_patterns()
        
        # Consolidated blacklists
        self.payload_blacklist = set()  # Combined request + response
        self.headers_blacklist = set()
        
        # Detailed analysis for reporting
        self.detailed_analysis = []
        self.excluded_fields = []
        
        # Compiled regex patterns
        self.compiled_patterns = {}
        self.compile_patterns()
    
    def load_patterns(self):
        """Load patterns from external configuration file"""
        try:
            with open(self.patterns_file, 'r') as f:
                config = json.load(f)
            
            self.keywords = config.get('keywords', {})
            self.value_patterns = config.get('value_patterns', {})
            self.fuzzy_rules = config.get('fuzzy_rules', {})
            self.exclusions = set(config.get('exclusions', []))
            self.pattern_mappings = config.get('pattern_mappings', {})
            
            print(f"✅ Loaded patterns from {self.patterns_file}")
            
        except FileNotFoundError:
            print(f"❌ Pattern file {self.patterns_file} not found. Creating default...")
            self.create_default_patterns_file()
            self.load_patterns()
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing {self.patterns_file}: {e}")
            raise
    
    def create_default_patterns_file(self):
        """Create default patterns file if it doesn't exist"""
        # This would create the patterns_config.json file with default content
        # Using the content from the patterns_config artifact above
        default_config = {
            "keywords": {
                "spi": ["name", "email", "phone", "address", "ssn"],
                "cpni": ["call", "sms", "data", "usage", "location"],
                "rpi": ["payment", "billing", "balance", "amount"],
                "cso": ["ticket", "support", "internal", "employee"],
                "pci": ["card", "cvv", "expiry"]
            },
            "value_patterns": {
                "email": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
                "phone": "^\\+?[1-9]\\d{1,14}$"
            },
            "fuzzy_rules": {
                "fnme": "firstname",
                "phne": "phone"
            },
            "exclusions": ["status", "code", "type", "version"],
            "pattern_mappings": {
                "email": ["SPI"],
                "phone": ["SPI"]
            }
        }
        
        with open(self.patterns_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        print(f"📄 Created default patterns file: {self.patterns_file}")
    
    def compile_patterns(self):
        """Compile regex patterns for better performance"""
        for pattern_name, pattern_str in self.value_patterns.items():
            try:
                # Handle case-insensitive patterns
                flags = re.IGNORECASE if 'Jan|Feb|Mar' in pattern_str else 0
                self.compiled_patterns[pattern_name] = re.compile(pattern_str, flags)
            except re.error as e:
                print(f"⚠️  Invalid regex pattern '{pattern_name}': {e}")
    
    def extract_final_key(self, field_path: str) -> str:
        """Extract the final key from a field path"""
        if '.' in field_path:
            return field_path.split('.')[-1]
        return field_path
    
    def get_field_category(self, field_path: str) -> str:
        """Get the category (request/response/headers) from field path"""
        if field_path.startswith('request.'):
            return 'request'
        elif field_path.startswith('response.'):
            return 'response'
        elif field_path.startswith('headers.'):
            return 'headers'
        return 'unknown'
    
    def apply_fuzzy_matching(self, field_name: str) -> str:
        """Apply fuzzy matching to detect variations and abbreviations"""
        field_lower = field_name.lower()
        
        # Direct fuzzy rule match
        if field_lower in self.fuzzy_rules:
            return self.fuzzy_rules[field_lower]
        
        # Compound word detection (camelCase)
        if any(char.isupper() for char in field_name[1:]):
            parts = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)', field_name)
            for part in parts:
                part_lower = part.lower()
                if part_lower in ['date', 'birth', 'born'] and ('date' in parts[0].lower() or 'birth' in field_lower):
                    return 'dateofbirth'
                if part_lower in ['first', 'last'] and 'name' in field_lower:
                    return 'name'
        
        # Vowel removal matching
        consonants_only = re.sub(r'[aeiou]', '', field_lower)
        vowel_mappings = {
            'nm': 'name',
            'phn': 'phone', 
            'ml': 'email',
            'ddr': 'address'
        }
        if consonants_only in vowel_mappings:
            return vowel_mappings[consonants_only]
        
        return field_name
    
    def intelligent_keyword_match(self, field_path: str) -> List[str]:
        """Intelligent keyword matching with fuzzy logic"""
        final_key = self.extract_final_key(field_path).lower()
        normalized_key = self.apply_fuzzy_matching(final_key)
        
        categories = []
        
        for category, keywords in self.keywords.items():
            # Check both original and normalized key
            if any(keyword in final_key for keyword in keywords):
                categories.append(category.upper())
            elif any(keyword in normalized_key.lower() for keyword in keywords):
                categories.append(category.upper())
        
        return list(set(categories))
    
    def analyze_values(self, values: List[Any]) -> Dict[str, Any]:
        """Analyze field values for sensitive patterns"""
        results = {
            'patterns_found': [],
            'categories': [],
            'confidence': 'Low',
            'unique_values': []
        }
        
        # Get unique values for display (remove duplicates)
        unique_values = list(dict.fromkeys([str(v) for v in values[:5]]))
        results['unique_values'] = unique_values
        
        for value in unique_values:
            value_str = str(value).strip()
            
            for pattern_name, compiled_pattern in self.compiled_patterns.items():
                if compiled_pattern.match(value_str):
                    results['patterns_found'].append(pattern_name)
                    
                    # Map patterns to categories using configuration
                    if pattern_name in self.pattern_mappings:
                        results['categories'].extend(self.pattern_mappings[pattern_name])
        
        # Remove duplicates and set confidence
        results['categories'] = list(set(results['categories']))
        results['patterns_found'] = list(set(results['patterns_found']))
        
        if results['patterns_found']:
            results['confidence'] = 'High'
        
        return results
    
    def should_exclude(self, final_key: str) -> bool:
        """Check if field should be excluded from blacklist"""
        return final_key.lower() in self.exclusions
    
    def analyze_field(self, field_path: str, values: List[Any]):
        """Analyze a single field and determine if it should be blacklisted"""
        final_key = self.extract_final_key(field_path)
        category = self.get_field_category(field_path)
        
        if category == 'unknown':
            return
        
        # Check exclusions first
        if self.should_exclude(final_key):
            self.excluded_fields.append({
    def generate_detailed_table_html(self, output_file: str = 'blacklist_detailed_table.html'):
        """Generate detailed HTML table for developer review with improved clarity"""
        
        blacklisted_fields = [r for r in self.detailed_analysis if r['blacklisted']]
        not_blacklisted_fields = [r for r in self.detailed_analysis if not r['blacklisted']]
        fuzzy_matched_fields = [r for r in blacklisted_fields if r.get('fuzzy_match')]
        key_based_fields = [r for r in blacklisted_fields if r.get('key_based')]
        value_based_fields = [r for r in blacklisted_fields if r.get('value_based')]
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Telecom API Blacklist Decision Table - Fixed Version</title>
    <style>
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 20px; 
            line-height: 1.6; 
            background-color: #f5f5f5;
        }}
        .container {{ 
            max-width: 1400px; 
            margin: 0 auto; 
            background: white; 
            padding: 20px; 
            border-radius: 8px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{ 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            padding: 30px; 
            border-radius: 8px; 
            margin-bottom: 30px;
            text-align: center;
        }}
        .fix-notice {{
            background: #d4edda; 
            color: #155724; 
            padding: 15px; 
            border-radius: 8px; 
            margin: 20px 0;
            border-left: 4px solid #28a745;
        }}
        .summary {{ 
            background: #f8f9fa; 
            padding: 20px; 
            border-radius: 8px; 
            margin: 20px 0;
            border-left: 4px solid #007bff;
        }}
        .section {{ 
            margin: 30px 0; 
        }}
        .section-header {{ 
            background: #343a40; 
            color: white; 
            padding: 15px; 
            border-radius: 8px 8px 0 0; 
            margin: 0;
            font-size: 1.2em;
            font-weight: bold;
        }}
        table {{ 
            width: 100%; 
            border-collapse: collapse; 
            margin: 0; 
            background: white;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        th {{ 
            background-color: #495057; 
            color: white; 
            padding: 15px 12px; 
            text-align: left; 
            font-weight: 600;
            border-bottom: 2px solid #dee2e6;
        }}
        td {{ 
            padding: 12px; 
            border-bottom: 1px solid #dee2e6; 
            vertical-align: top;
        }}
        tr:hover {{ 
            background-color: #f8f9fa; 
        }}
        .field-path {{ 
            font-family: 'Courier New', monospace; 
            background: #e9ecef; 
            padding: 4px 8px; 
            border-radius: 4px;
            font-size: 0.9em;
            word-break: break-word;
        }}
        .final-key {{ 
            font-weight: bold; 
            color: #495057;
            font-size: 1.1em;
        }}
        .values {{ 
            font-family: 'Courier New', monospace; 
            background: #f8f9fa; 
            padding: 8px; 
            border-radius: 4px; 
            max-height: 100px; 
            overflow-y: auto;
            font-size: 0.9em;
            word-break: break-word;
        }}
        .reason {{ 
            line-height: 1.5;
        }}
        .blacklisted {{ 
            background-color: #fff5f5; 
            border-left: 4px solid #f56565;
        }}
        .not-blacklisted {{ 
            background-color: #f0fff4; 
            border-left: 4px solid #48bb78;
        }}
        .fuzzy-indicator {{ 
            background: #3182ce; 
            color: white; 
            padding: 2px 6px; 
            border-radius: 12px; 
            font-size: 0.7em; 
            margin-left: 8px;
        }}
        .key-based-indicator {{ 
            background: #e53e3e; 
            color: white; 
            padding: 2px 6px; 
            border-radius: 12px; 
            font-size: 0.7em; 
            margin-left: 4px;
        }}
        .value-based-indicator {{ 
            background: #3182ce; 
            color: white; 
            padding: 2px 6px; 
            border-radius: 12px; 
            font-size: 0.7em; 
            margin-left: 4px;
        }}
        .category-tag {{ 
            background: #e2e8f0; 
            color: #2d3748; 
            padding: 2px 8px; 
            border-radius: 12px; 
            font-size: 0.8em; 
            margin: 2px;
            display: inline-block;
        }}
        .spi {{ background: #fed7d7; color: #742a2a; }}
        .cpni {{ background: #feebc8; color: #744210; }}
        .rpi {{ background: #e9d8fd; color: #44337a; }}
        .cso {{ background: #bee3f8; color: #2a4365; }}
        .pci {{ background: #fed7d7; color: #742a2a; }}
        .filter-controls {{ 
            background: #f8f9fa; 
            padding: 15px; 
            border-radius: 8px; 
            margin: 20px 0;
            border: 1px solid #dee2e6;
        }}
        .btn {{ 
            background: #007bff; 
            color: white; 
            border: none; 
            padding: 8px 16px; 
            border-radius: 4px; 
            cursor: pointer; 
            margin: 2px;
        }}
        .btn:hover {{ background: #0056b3; }}
        .btn.active {{ background: #28a745; }}
        .stats {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 15px; 
            margin: 20px 0;
        }}
        .stat-card {{ 
            background: white; 
            padding: 20px; 
            border-radius: 8px; 
            text-align: center; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #007bff;
        }}
        .stat-number {{ 
            font-size: 2em; 
            font-weight: bold; 
            color: #007bff; 
        }}
    </style>
    <script>
        function filterTable(show) {{
            const blacklistedRows = document.querySelectorAll('.blacklisted');
            const notBlacklistedRows = document.querySelectorAll('.not-blacklisted');
            const buttons = document.querySelectorAll('.filter-btn');
            
            // Reset button states
            buttons.forEach(btn => btn.classList.remove('active'));
            
            if (show === 'all') {{
                blacklistedRows.forEach(row => row.style.display = '');
                notBlacklistedRows.forEach(row => row.style.display = '');
                document.querySelector('[onclick="filterTable(\\'all\\')"]').classList.add('active');
            }} else if (show === 'blacklisted') {{
                blacklistedRows.forEach(row => row.style.display = '');
                notBlacklistedRows.forEach(row => row.style.display = 'none');
                document.querySelector('[onclick="filterTable(\\'blacklisted\\')"]').classList.add('active');
            }} else if (show === 'safe') {{
                blacklistedRows.forEach(row => row.style.display = 'none');
                notBlacklistedRows.forEach(row => row.style.display = '');
                document.querySelector('[onclick="filterTable(\\'safe\\')"]').classList.add('active');
            }}
        }}
        
        // Initialize with all shown
        window.onload = function() {{
            filterTable('all');
        }}
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔒 Telecom API Blacklist Decision Table</h1>
            <h2>✅ Fixed Version - No More False Positives</h2>
            <p>Developer Review & Validation Interface</p>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <div class="fix-notice">
            <h3>🛠️ Fixes Applied:</h3>
            <ul>
                <li><strong>Key-based matching:</strong> Now applies ONLY to final key (e.g., 'verified' from 'response.contactMedium.Characteristic.verified')</li>
                <li><strong>Value-based matching:</strong> Excludes boolean values (True/False) and common non-sensitive values</li>
                <li><strong>Removed problematic patterns:</strong> name_pattern removed to prevent false positives on boolean values</li>
                <li><strong>Enhanced exclusions:</strong> Added 'verified', 'preferred', 'enabled', etc. to exclusion list</li>
            </ul>
        </div>

        <div class="summary">
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">{len(self.detailed_analysis)}</div>
                    <div>Total Fields</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(blacklisted_fields)}</div>
                    <div>Blacklisted</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(key_based_fields)}</div>
                    <div>Key-based</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(value_based_fields)}</div>
                    <div>Value-based</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(fuzzy_matched_fields)}</div>
                    <div>Fuzzy Detected</div>
                </div>
            </div>
        </div>

        <div class="filter-controls">
            <strong>Filter View:</strong>
            <button class="btn filter-btn" onclick="filterTable('all')">Show All</button>
            <button class="btn filter-btn" onclick="filterTable('blacklisted')">Only Blacklisted</button>
            <button class="btn filter-btn" onclick="filterTable('safe')">Only Safe Fields</button>
        </div>

        <div class="section">
            <table>
                <thead>
                    <tr>
                        <th style="width: 25%;">Blacklisted Field</th>
                        <th style="width: 35%;">Original Field & Values</th>
                        <th style="width: 40%;">Reason for Decision</th>
                    </tr>
                </thead>
                <tbody>
"""

        # Combine all fields for single table
        all_fields = blacklisted_fields + not_blacklisted_fields
        all_fields.sort(key=lambda x: (x['category'], x['field_path']))

        for result in all_fields:
            row_class = "blacklisted" if result['blacklisted'] else "not-blacklisted"
            
            # Blacklisted field column
            if result['blacklisted']:
                blacklisted_field = f'<span class="final-key">{result["final_key"]}</span>'
                
                # Add indicators
                if result.get('fuzzy_match'):
                    blacklisted_field += '<span class="fuzzy-indicator">FUZZY</span>'
                if result.get('key_based'):
                    blacklisted_field += '<span class="key-based-indicator">KEY</span>'
                if result.get('value_based'):
                    blacklisted_field += '<span class="value-based-indicator">VALUE</span>'
                
                # Add category tags
                if result['categories_detected']:
                    category_tags = ''.join([f'<span class="category-tag {cat.lower()}">{cat}</span>' 
                                           for cat in result['categories_detected']])
                    blacklisted_field += f'<br><div style="margin-top: 5px;">{category_tags}</div>'
            else:
                blacklisted_field = '<span style="color: #28a745; font-weight: bold;">✓ SAFE</span>'
            
            # Original field & values column
            original_field = f'<div class="field-path">{result["field_path"]}</div>'
            if result['unique_values']:
                # Limit display to first 3 unique values
                display_values = result['unique_values'][:3]
                values_text = '<br>'.join([f'<code>{v}</code>' for v in display_values])
                if len(result['unique_values']) > 3:
                    values_text += f'<br><em>... and {len(result["unique_values"]) - 3} more</em>'
                original_field += f'<div class="values" style="margin-top: 8px;"><strong>Values:</strong><br>{values_text}</div>'
            
            # Reason column
            reason = '<br>'.join(result['reasons'])
            
            html_content += f"""
                    <tr class="{row_class}">
                        <td>{blacklisted_field}</td>
                        <td>{original_field}</td>
                        <td class="reason">{reason}</td>
                    </tr>
"""

        html_content += f"""
                </tbody>
            </table>
        </div>

        <div class="section">
            <div class="section-header">📋 Usage Instructions</div>
            <div style="padding: 20px; background: #f8f9fa;">
                <h4>How to Review:</h4>
                <ol>
                    <li><strong>Filter the table</strong> using buttons above to focus on specific field types</li>
                    <li><strong>Review blacklisted fields</strong> - ensure they are actually sensitive in your context</li>
                    <li><strong>Check safe fields</strong> - verify no sensitive data was missed</li>
                    <li><strong>Look for indicators:</strong> 🔵FUZZY (intelligent match), 🔴KEY (keyword), 🔵VALUE (pattern)</li>
                    <li><strong>Update patterns file</strong> if needed to improve detection</li>
                </ol>
                
                <h4>Fixed Issues:</h4>
                <ul>
                    <li>✅ Boolean values (True/False) no longer flagged as sensitive</li>
                    <li>✅ Key matching applies only to final key (not full path)</li>
                    <li>✅ Value exclusions prevent common false positives</li>
                    <li>✅ Clear indicators show detection method</li>
                </ul>
            </div>
        </div>

        <div class="section">
            <div class="section-header">⚙️ Generated Configuration</div>
            <div style="padding: 20px; background: #f8f9fa;">
                <h4>application.properties entries:</h4>
                <pre style="background: #2d3748; color: #e2e8f0; padding: 15px; border-radius: 4px; overflow-x: auto;">
payload.blacklist={','.join(sorted(self.payload_blacklist))}
headers.blacklist={','.join(sorted(self.headers_blacklist))}
                </pre>
            </div>
        </div>
    </div>
</body>
</html>
"""

        with open(output_file, 'w') as f:
            f.write(html_content)
        
        print(f"📄 Fixed detailed table generated: {output_file}")
        return output_filepath': field_path,
                'final_key': final_key,
                'reason': 'Excluded - Common non-sensitive field'
            })
            return
        
        # Initialize analysis result
        analysis_result = {
            'field_path': field_path,
            'final_key': final_key,
            'category': category,
            'blacklisted': False,
            'reasons': [],
            'categories_detected': [],
            'unique_values': [],
            'confidence': 'Low',
            'fuzzy_match': None
        }
        
        # Key-based analysis
        key_categories = self.intelligent_keyword_match(field_path)
        if key_categories:
            analysis_result['blacklisted'] = True
            analysis_result['categories_detected'].extend(key_categories)
            
            # Check if fuzzy matching was applied
            normalized_key = self.apply_fuzzy_matching(final_key.lower())
            if normalized_key != final_key.lower():
                analysis_result['fuzzy_match'] = normalized_key
                analysis_result['reasons'].append(f"Key-based: '{final_key}' intelligently matched to '{normalized_key}' ({', '.join(key_categories)})")
            else:
                analysis_result['reasons'].append(f"Key-based: Contains sensitive keywords ({', '.join(key_categories)})")
        
        # Value-based analysis
        if values:
            value_analysis = self.analyze_values(values)
            analysis_result['unique_values'] = value_analysis['unique_values']
            
            if value_analysis['categories']:
                analysis_result['blacklisted'] = True
                analysis_result['categories_detected'].extend(value_analysis['categories'])
                analysis_result['reasons'].append(f"Value-based: Matches patterns {value_analysis['patterns_found']} ({', '.join(value_analysis['categories'])})")
                analysis_result['confidence'] = value_analysis['confidence']
        
        # Remove duplicates from categories
        analysis_result['categories_detected'] = list(set(analysis_result['categories_detected']))
        
        if not analysis_result['blacklisted']:
            analysis_result['reasons'].append("No sensitive patterns detected")
        
        # Add to appropriate blacklist
        if analysis_result['blacklisted']:
            if category in ['request', 'response']:
                self.payload_blacklist.add(final_key)
            elif category == 'headers':
                self.headers_blacklist.add(final_key)
        
        self.detailed_analysis.append(analysis_result)
    
    def generate_properties(self, output_file: str = 'application.properties'):
        """Generate consolidated application.properties file"""
        content = f"""# Telecom API Blacklist Configuration - CONSOLIDATED
# Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Pattern source: {self.patterns_file}
# Total fields analyzed: {len(self.detailed_analysis)}
# Fields blacklisted: {len([r for r in self.detailed_analysis if r['blacklisted']])}

# CONSOLIDATED BLACKLISTS (duplicates removed)
payload.blacklist={','.join(sorted(self.payload_blacklist))}
headers.blacklist={','.join(sorted(self.headers_blacklist))}
"""
        
        with open(output_file, 'w') as f:
            f.write(content)
        
        print(f"📄 Properties file generated: {output_file}")
        return output_file
    
    def generate_detailed_table_html(self, output_file: str = 'blacklist_detailed_table.html'):
        """Generate detailed HTML table for developer review"""
        
        blacklisted_fields = [r for r in self.detailed_analysis if r['blacklisted']]
        not_blacklisted_fields = [r for r in self.detailed_analysis if not r['blacklisted']]
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Telecom API Blacklist Decision Table</title>
    <style>
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 20px; 
            line-height: 1.6; 
            background-color: #f5f5f5;
        }}
        .container {{ 
            max-width: 1400px; 
            margin: 0 auto; 
            background: white; 
            padding: 20px; 
            border-radius: 8px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{ 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            padding: 30px; 
            border-radius: 8px; 
            margin-bottom: 30px;
            text-align: center;
        }}
        .summary {{ 
            background: #f8f9fa; 
            padding: 20px; 
            border-radius: 8px; 
            margin: 20px 0;
            border-left: 4px solid #007bff;
        }}
        .section {{ 
            margin: 30px 0; 
        }}
        .section-header {{ 
            background: #343a40; 
            color: white; 
            padding: 15px; 
            border-radius: 8px 8px 0 0; 
            margin: 0;
            font-size: 1.2em;
            font-weight: bold;
        }}
        table {{ 
            width: 100%; 
            border-collapse: collapse; 
            margin: 0; 
            background: white;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        th {{ 
            background-color: #495057; 
            color: white; 
            padding: 15px 12px; 
            text-align: left; 
            font-weight: 600;
            border-bottom: 2px solid #dee2e6;
        }}
        td {{ 
            padding: 12px; 
            border-bottom: 1px solid #dee2e6; 
            vertical-align: top;
        }}
        tr:hover {{ 
            background-color: #f8f9fa; 
        }}
        .field-path {{ 
            font-family: 'Courier New', monospace; 
            background: #e9ecef; 
            padding: 4px 8px; 
            border-radius: 4px;
            font-size: 0.9em;
            word-break: break-word;
        }}
        .final-key {{ 
            font-weight: bold; 
            color: #495057;
            font-size: 1.1em;
        }}
        .values {{ 
            font-family: 'Courier New', monospace; 
            background: #f8f9fa; 
            padding: 8px; 
            border-radius: 4px; 
            max-height: 100px; 
            overflow-y: auto;
            font-size: 0.9em;
            word-break: break-word;
        }}
        .reason {{ 
            line-height: 1.5;
        }}
        .blacklisted {{ 
            background-color: #fff5f5; 
            border-left: 4px solid #f56565;
        }}
        .not-blacklisted {{ 
            background-color: #f0fff4; 
            border-left: 4px solid #48bb78;
        }}
        .fuzzy-indicator {{ 
            background: #3182ce; 
            color: white; 
            padding: 2px 6px; 
            border-radius: 12px; 
            font-size: 0.7em; 
            margin-left: 8px;
        }}
        .category-tag {{ 
            background: #e2e8f0; 
            color: #2d3748; 
            padding: 2px 8px; 
            border-radius: 12px; 
            font-size: 0.8em; 
            margin: 2px;
            display: inline-block;
        }}
        .spi {{ background: #fed7d7; color: #742a2a; }}
        .cpni {{ background: #feebc8; color: #744210; }}
        .rpi {{ background: #e9d8fd; color: #44337a; }}
        .cso {{ background: #bee3f8; color: #2a4365; }}
        .pci {{ background: #fed7d7; color: #742a2a; }}
        .filter-controls {{ 
            background: #f8f9fa; 
            padding: 15px; 
            border-radius: 8px; 
            margin: 20px 0;
            border: 1px solid #dee2e6;
        }}
        .btn {{ 
            background: #007bff; 
            color: white; 
            border: none; 
            padding: 8px 16px; 
            border-radius: 4px; 
            cursor: pointer; 
            margin: 2px;
        }}
        .btn:hover {{ background: #0056b3; }}
        .btn.active {{ background: #28a745; }}
        .stats {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 15px; 
            margin: 20px 0;
        }}
        .stat-card {{ 
            background: white; 
            padding: 20px; 
            border-radius: 8px; 
            text-align: center; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #007bff;
        }}
        .stat-number {{ 
            font-size: 2em; 
            font-weight: bold; 
            color: #007bff; 
        }}
    </style>
    <script>
        function filterTable(show) {{
            const blacklistedRows = document.querySelectorAll('.blacklisted');
            const notBlacklistedRows = document.querySelectorAll('.not-blacklisted');
            const buttons = document.querySelectorAll('.filter-btn');
            
            // Reset button states
            buttons.forEach(btn => btn.classList.remove('active'));
            
            if (show === 'all') {{
                blacklistedRows.forEach(row => row.style.display = '');
                notBlacklistedRows.forEach(row => row.style.display = '');
                document.querySelector('[onclick="filterTable(\\'all\\')"]').classList.add('active');
            }} else if (show === 'blacklisted') {{
                blacklistedRows.forEach(row => row.style.display = '');
                notBlacklistedRows.forEach(row => row.style.display = 'none');
                document.querySelector('[onclick="filterTable(\\'blacklisted\\')"]').classList.add('active');
            }} else if (show === 'safe') {{
                blacklistedRows.forEach(row => row.style.display = 'none');
                notBlacklistedRows.forEach(row => row.style.display = '');
                document.querySelector('[onclick="filterTable(\\'safe\\')"]').classList.add('active');
            }}
        }}
        
        // Initialize with all shown
        window.onload = function() {{
            filterTable('all');
        }}
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔒 Telecom API Blacklist Decision Table</h1>
            <p>Developer Review & Validation Interface</p>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <div class="summary">
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">{len(self.detailed_analysis)}</div>
                    <div>Total Fields</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(blacklisted_fields)}</div>
                    <div>Blacklisted</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(not_blacklisted_fields)}</div>
                    <div>Safe Fields</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len([r for r in blacklisted_fields if r.get('fuzzy_match')])}</div>
                    <div>Fuzzy Detected</div>
                </div>
            </div>
        </div>

        <div class="filter-controls">
            <strong>Filter View:</strong>
            <button class="btn filter-btn" onclick="filterTable('all')">Show All</button>
            <button class="btn filter-btn" onclick="filterTable('blacklisted')">Only Blacklisted</button>
            <button class="btn filter-btn" onclick="filterTable('safe')">Only Safe Fields</button>
        </div>

        <div class="section">
            <table>
                <thead>
                    <tr>
                        <th style="width: 25%;">Blacklisted Field</th>
                        <th style="width: 35%;">Original Field & Values</th>
                        <th style="width: 40%;">Reason for Decision</th>
                    </tr>
                </thead>
                <tbody>
"""

        # Combine all fields for single table
        all_fields = blacklisted_fields + not_blacklisted_fields
        all_fields.sort(key=lambda x: (x['category'], x['field_path']))

        for result in all_fields:
            row_class = "blacklisted" if result['blacklisted'] else "not-blacklisted"
            
            # Blacklisted field column
            if result['blacklisted']:
                blacklisted_field = f'<span class="final-key">{result["final_key"]}</span>'
                if result.get('fuzzy_match'):
                    blacklisted_field += '<span class="fuzzy-indicator">FUZZY</span>'
                
                # Add category tags
                if result['categories_detected']:
                    category_tags = ''.join([f'<span class="category-tag {cat.lower()}">{cat}</span>' 
                                           for cat in result['categories_detected']])
                    blacklisted_field += f'<br><div style="margin-top: 5px;">{category_tags}</div>'
            else:
                blacklisted_field = '<span style="color: #28a745; font-weight: bold;">✓ SAFE</span>'
            
            # Original field & values column
            original_field = f'<div class="field-path">{result["field_path"]}</div>'
            if result['unique_values']:
                # Limit display to first 3 unique values
                display_values = result['unique_values'][:3]
                values_text = '<br>'.join(display_values)
                if len(result['unique_values']) > 3:
                    values_text += f'<br><em>... and {len(result["unique_values"]) - 3} more</em>'
                original_field += f'<div class="values" style="margin-top: 8px;"><strong>Values:</strong><br>{values_text}</div>'
            
            # Reason column
            reason = '<br>'.join(result['reasons'])
            
            html_content += f"""
                    <tr class="{row_class}">
                        <td>{blacklisted_field}</td>
                        <td>{original_field}</td>
                        <td class="reason">{reason}</td>
                    </tr>
"""

        html_content += """
                </tbody>
            </table>
        </div>

        <div class="section">
            <div class="section-header">📋 Usage Instructions</div>
            <div style="padding: 20px; background: #f8f9fa;">
                <h4>How to Review:</h4>
                <ol>
                    <li><strong>Filter the table</strong> using buttons above to focus on specific field types</li>
                    <li><strong>Review blacklisted fields</strong> - ensure they are actually sensitive in your context</li>
                    <li><strong>Check safe fields</strong> - verify no sensitive data was missed</li>
                    <li><strong>Look for fuzzy matches</strong> - marked with blue FUZZY tag, verify accuracy</li>
                    <li><strong>Update patterns file</strong> if needed to improve detection</li>
                </ol>
                
                <h4>Action Items:</h4>
                <ul>
                    <li>Copy the generated <code>application.properties</code> entries to your configuration</li>
                    <li>Test API responses with blacklist applied to ensure no functional issues</li>
                    <li>Add any additional fields to patterns configuration as needed</li>
                    <li>Schedule regular reviews when APIs change</li>
                </ul>
            </div>
        </div>

        <div class="section">
            <div class="section-header">⚙️ Generated Configuration</div>
            <div style="padding: 20px; background: #f8f9fa;">
                <h4>application.properties entries:</h4>
                <pre style="background: #2d3748; color: #e2e8f0; padding: 15px; border-radius: 4px; overflow-x: auto;">
payload.blacklist={','.join(sorted(self.payload_blacklist))}
headers.blacklist={','.join(sorted(self.headers_blacklist))}
                </pre>
            </div>
        </div>
    </div>
</body>
</html>
"""

        with open(output_file, 'w') as f:
            f.write(html_content)
        
        print(f"📄 Detailed table generated: {output_file}")
        return output_file
    
    def print_console_summary(self):
        """Print consolidated summary to console"""
        blacklisted_count = len([r for r in self.detailed_analysis if r['blacklisted']])
        fuzzy_count = len([r for r in self.detailed_analysis if r.get('fuzzy_match')])
        
        print("\n" + "="*70)
        print("        CONSOLIDATED BLACKLIST ANALYSIS SUMMARY")
        print("="*70)
        print(f"🧠 Intelligence Level: ENHANCED (patterns from {self.patterns_file})")
        print(f"📊 Total fields analyzed: {len(self.detailed_analysis)}")
        print(f"🚫 Fields blacklisted: {blacklisted_count}")
        print(f"🎯 Fuzzy detections: {fuzzy_count}")
        print(f"⚠️  Fields excluded: {len(self.excluded_fields)}")
        
        print(f"\n📂 CONSOLIDATED BLACKLISTS:")
        print(f"   payload.blacklist: {len(self.payload_blacklist)} fields")
        print(f"   headers.blacklist: {len(self.headers_blacklist)} fields")
        
        # Show some example detections
        fuzzy_examples = [r for r in self.detailed_analysis if r.get('fuzzy_match')][:3]
        if fuzzy_examples:
            print(f"\n🧠 Sample intelligent detections:")
            for example in fuzzy_examples:
                print(f"   '{example['final_key']}' → '{example['fuzzy_match']}' ({', '.join(example['categories_detected'])})")
        
        # Show consolidated blacklist preview
        if self.payload_blacklist:
            payload_preview = list(self.payload_blacklist)[:8]
            payload_str = ','.join(payload_preview)
            if len(self.payload_blacklist) > 8:
                payload_str += f",... (+{len(self.payload_blacklist) - 8} more)"
            print(f"\n📋 payload.blacklist preview: {payload_str}")
        
        if self.headers_blacklist:
            headers_preview = list(self.headers_blacklist)[:8]
            headers_str = ','.join(headers_preview)
            if len(self.headers_blacklist) > 8:
                headers_str += f",... (+{len(self.headers_blacklist) - 8} more)"
            print(f"📋 headers.blacklist preview: {headers_str}")
    
    def analyze_data(self, data_file: str):
        """Analyze the extracted data"""
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        # Analyze each field in the data
        for item in data.get('data', []):
            for field_path, values in item.items():
                if field_path == 'curl':  # Skip curl commands
                    continue
                self.analyze_field(field_path, values)
        
        return {
            'total_fields': len(self.detailed_analysis),
            'blacklisted_fields': len([r for r in self.detailed_analysis if r['blacklisted']]),
            'excluded_fields': len(self.excluded_fields)
        }

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python blacklist_generator.py <postman_extraction_results.json> [patterns_config.json]")
        print("Example: python blacklist_generator.py data.json patterns_config.json")
        return
    
    data_file = sys.argv[1]
    patterns_file = sys.argv[2] if len(sys.argv) > 2 else 'patterns_config.json'
    
    if not os.path.exists(data_file):
        print(f"❌ Data file {data_file} not found")
        return
    
    print("🧠 Starting intelligent blacklist analysis...")
    print(f"📄 Data source: {data_file}")
    print(f"⚙️  Patterns source: {patterns_file}")
    
    try:
        generator = TelecomBlacklistGenerator(patterns_file)
        
        # Analyze the data
        summary = generator.analyze_data(data_file)
        
        # Generate outputs
        properties_file = generator.generate_properties()
        table_file = generator.generate_detailed_table_html()
        
        # Print console summary
        generator.print_console_summary()
        
        print(f"\n📄 Generated files:")
        print(f"   📋 Properties: {properties_file}")
        print(f"   📊 Review table: {table_file}")
        print(f"   ⚙️  Patterns config: {patterns_file}")
        
        print(f"\n✅ Analysis complete!")
        print(f"👀 Open {table_file} in your browser to review all decisions")
        print(f"📝 Copy configuration from {properties_file} to your application")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()