#!/usr/bin/env python3
"""
Enhanced Interactive Telecom API Blacklist Generator
Now includes:
- Interactive Add/Remove buttons in HTML table
- Real-time configuration updates
- Developer override persistence in patterns_config.json
- Recognition of manual overrides on subsequent runs
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
        
        # Initialize all attributes with defaults
        self.keywords = {}
        self.value_patterns = {}
        self.fuzzy_rules = {}
        self.exclusions = set()
        self.pattern_mappings = {}
        self.value_exclusions = set()
        self.business_value_patterns = []
        
        # NEW: Developer overrides
        self.developer_overrides = {
            'manual_blacklist': set(),  # Fields manually added to blacklist
            'manual_whitelist': set()   # Fields manually excluded from blacklist
        }
        
        # Load patterns from file
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
    
    def merge_developer_overrides_into_patterns(self):
        """Merge developer_overrides.json into patterns_config.json at startup"""
        override_file = 'developer_overrides.json'
        
        if not os.path.exists(override_file):
            return False
        
        try:
            # Load developer overrides
            with open(override_file, 'r') as f:
                new_overrides = json.load(f)
            
            new_blacklist = set(new_overrides.get('manual_blacklist', []))
            new_whitelist = set(new_overrides.get('manual_whitelist', []))
            
            if not new_blacklist and not new_whitelist:
                return False
            
            print(f"📄 Found developer overrides file: {override_file}")
            print(f"   • New manual blacklist: {len(new_blacklist)} fields")
            print(f"   • New manual whitelist: {len(new_whitelist)} fields")
            
            # Load current patterns config
            with open(self.patterns_file, 'r') as f:
                patterns_config = json.load(f)
            
            # Get existing overrides from patterns config
            existing_overrides = patterns_config.get('developer_overrides', {})
            existing_blacklist = set(existing_overrides.get('manual_blacklist', []))
            existing_whitelist = set(existing_overrides.get('manual_whitelist', []))
            
            # Merge: union of existing and new
            merged_blacklist = existing_blacklist.union(new_blacklist)
            merged_whitelist = existing_whitelist.union(new_whitelist)
            
            # Remove conflicts: whitelist takes precedence
            final_blacklist = merged_blacklist - merged_whitelist
            final_whitelist = merged_whitelist
            
            print(f"🔄 Merging with existing overrides in patterns config:")
            print(f"   • Existing blacklist: {len(existing_blacklist)} fields")
            print(f"   • Existing whitelist: {len(existing_whitelist)} fields")
            print(f"   • Final blacklist: {len(final_blacklist)} fields")
            print(f"   • Final whitelist: {len(final_whitelist)} fields")
            
            # Update patterns config with merged overrides
            patterns_config['developer_overrides'] = {
                'manual_blacklist': sorted(list(final_blacklist)),
                'manual_whitelist': sorted(list(final_whitelist)),
                'last_merged': datetime.now().isoformat(),
                'merged_from': override_file
            }
            
            # Create backup of patterns config
            backup_file = f"{self.patterns_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            with open(backup_file, 'w') as f:
                json.dump(patterns_config, f, indent=2)
            
            # Save updated patterns config
            with open(self.patterns_file, 'w') as f:
                json.dump(patterns_config, f, indent=2)
            
            # Remove the developer overrides file (it's been merged)
            os.remove(override_file)
            
            print(f"✅ Successfully merged overrides into {self.patterns_file}")
            print(f"💾 Created backup: {backup_file}")
            print(f"🗑️  Removed {override_file} (successfully merged)")
            
            return True
            
        except Exception as e:
            print(f"❌ Error merging developer overrides: {e}")
            return False
    
    def load_patterns(self):
        """Load patterns from external configuration file including developer overrides"""
        # FIRST: Check and merge any developer_overrides.json file
        self.merge_developer_overrides_into_patterns()
        
        try:
            with open(self.patterns_file, 'r') as f:
                config = json.load(f)
            
            self.keywords = config.get('keywords', {})
            self.value_patterns = config.get('value_patterns', {})
            self.fuzzy_rules = config.get('fuzzy_rules', {})
            self.exclusions = set(config.get('exclusions', []))
            self.pattern_mappings = config.get('pattern_mappings', {})
            self.value_exclusions = set(config.get('value_exclusions', []))
            self.business_value_patterns = config.get('business_value_patterns', [])
            
            # Load developer overrides from patterns config (now the single source of truth)
            overrides = config.get('developer_overrides', {})
            self.developer_overrides = {
                'manual_blacklist': set(overrides.get('manual_blacklist', [])),
                'manual_whitelist': set(overrides.get('manual_whitelist', []))
            }
            
            print(f"✅ Loaded patterns from {self.patterns_file}")
            if self.developer_overrides['manual_blacklist']:
                print(f"👨‍💻 Developer manual blacklist: {len(self.developer_overrides['manual_blacklist'])} fields")
                print(f"   Examples: {', '.join(list(self.developer_overrides['manual_blacklist'])[:5])}")
            if self.developer_overrides['manual_whitelist']:
                print(f"👨‍💻 Developer manual whitelist: {len(self.developer_overrides['manual_whitelist'])} fields")
                print(f"   Examples: {', '.join(list(self.developer_overrides['manual_whitelist'])[:5])}")
            
        except FileNotFoundError:
            print(f"❌ Pattern file {self.patterns_file} not found. Creating default...")
            self.create_default_patterns_file()
            self.load_patterns()
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing {self.patterns_file}: {e}")
            raise
        """Load patterns from external configuration file including developer overrides"""
        try:
            with open(self.patterns_file, 'r') as f:
                config = json.load(f)
            
            self.keywords = config.get('keywords', {})
            self.value_patterns = config.get('value_patterns', {})
            self.fuzzy_rules = config.get('fuzzy_rules', {})
            self.exclusions = set(config.get('exclusions', []))
            self.pattern_mappings = config.get('pattern_mappings', {})
            self.value_exclusions = set(config.get('value_exclusions', []))
            self.business_value_patterns = config.get('business_value_patterns', [])
            
            # NEW: Load developer overrides
            overrides = config.get('developer_overrides', {})
            self.developer_overrides = {
                'manual_blacklist': set(overrides.get('manual_blacklist', [])),
                'manual_whitelist': set(overrides.get('manual_whitelist', []))
            }
            
            print(f"✅ Loaded patterns from {self.patterns_file}")
            if self.developer_overrides['manual_blacklist']:
                print(f"📋 Developer manual blacklist: {len(self.developer_overrides['manual_blacklist'])} fields")
            if self.developer_overrides['manual_whitelist']:
                print(f"📋 Developer manual whitelist: {len(self.developer_overrides['manual_whitelist'])} fields")
            
        except FileNotFoundError:
            print(f"❌ Pattern file {self.patterns_file} not found. Creating default...")
            self.create_default_patterns_file()
            self.load_patterns()
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing {self.patterns_file}: {e}")
            raise
    
    def save_developer_overrides(self):
        """Save developer overrides back to patterns_config.json"""
        try:
            # Load current config
            with open(self.patterns_file, 'r') as f:
                config = json.load(f)
            
            # Update developer overrides
            config['developer_overrides'] = {
                'manual_blacklist': list(self.developer_overrides['manual_blacklist']),
                'manual_whitelist': list(self.developer_overrides['manual_whitelist'])
            }
            
            # Save back to file
            with open(self.patterns_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"💾 Saved developer overrides to {self.patterns_file}")
            
        except Exception as e:
            print(f"❌ Error saving developer overrides: {e}")
    
    def create_default_patterns_file(self):
        """Create default patterns file if it doesn't exist"""
        default_config = {
            "keywords": {
                "spi": [
                    "name", "nm", "fname", "lname", "fnme", "lstnm", "firstname", "lastname", 
                    "fullname", "surname", "givenname", "familyname", "username", "uname", 
                    "usrnm", "displayname", "nickname", "alias",
                    "email", "eml", "emailaddr", "emailaddress", "mail", "mailaddr", "contact",
                    "contactemail", "emailid", "userid", "user_email", "e_mail",
                    "phone", "phne", "phn", "tel", "telephone", "mobile", "mob", "cell", 
                    "cellular", "msisdn", "contactno", "contactnumber", "phoneno", "phonenumber",
                    "ph", "tel_no", "telephone_no",
                    "address", "addr", "location", "loc", "street", "st", "city", "state", 
                    "zip", "zipcode", "postal", "postalcode", "country", "region", "area",
                    "ssn", "social", "socialsecurity", "taxid", "nationalid", "passport", 
                    "license", "driverlicense", "citizenid", "personid", "identityno", "identification",
                    "dob", "dateofbirth", "birthdate", "birthday", "bday", "birth", "born", 
                    "age", "dateborn", "birth_date", "date_of_birth",
                    "subscriber", "customer", "cust", "personal", "individual", "person", 
                    "profile", "identity", "ident", "private"
                ],
                "cpni": [
                    "call", "cll", "sms", "message", "msg", "communication", "comm", 
                    "conversation", "chat", "voice", "audio",
                    "data", "usage", "consumed", "volume", "bytes", "mb", "gb", "traffic", 
                    "bandwidth", "speed", "throughput", "transfer",
                    "network", "net", "nw", "cell", "tower", "antenna", "signal", "coverage", 
                    "connection", "conn", "session", "bearer",
                    "location", "loc", "position", "pos", "coordinates", "coord", "lat", "lng", 
                    "latitude", "longitude", "gps", "geolocation", "geo",
                    "service", "svc", "plan", "subscription", "sub", "activation", "provision", 
                    "feature", "addon", "package",
                    "imsi", "imei", "mcc", "mnc", "lac", "cgi", "cellid", "networkid", 
                    "operatorid", "carrier",
                    "session", "sess", "duration", "time", "period", "start", "end", "begin", 
                    "finish", "timestamp"
                ],
                "rpi": [
                    "payment", "pay", "billing", "bill", "invoice", "charge", "fee", "cost", 
                    "price", "amount", "amt", "total", "sum",
                    "balance", "bal", "credit", "debit", "account", "acct", "financial", 
                    "finance", "money", "currency", "revenue", "income",
                    "transaction", "trans", "purchase", "sale", "order", "receipt", 
                    "payment_id", "transaction_id", "reference", "ref",
                    "card", "cc", "creditcard", "debitcard", "cardno", "cardnumber", "cardholder"
                ],
                "cso": [
                    "ticket", "support", "help", "issue", "problem", "complaint", "feedback", 
                    "note", "comment", "remark",
                    "internal", "int", "employee", "emp", "staff", "operator", "op", "admin", 
                    "system", "sys", "config", "setting",
                    "metric", "performance", "perf", "quality", "log", "audit", "monitor", 
                    "track", "measure", "stats", "statistics"
                ],
                "pci": [
                    "card", "cc", "creditcard", "debitcard", "pan", "cardnumber", "cardno", 
                    "ccnumber", "accountnumber",
                    "cvv", "cvc", "cvn", "cid", "securitycode", "verificationcode", "checkcode",
                    "expiry", "expire", "expiration", "exp", "expirydate", "validthru", 
                    "cardholder", "holdername"
                ]
            },
            "value_patterns": {
                "email": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
                "phone": "^\\+?[1-9]\\d{1,14}$|^\\(\\d{3}\\)\\s?\\d{3}-\\d{4}$|^\\d{10,15}$",
                "credit_card": "^\\d{4}[\\s-]?\\d{4}[\\s-]?\\d{4}[\\s-]?\\d{4}$",
                "ssn": "^\\d{3}-\\d{2}-\\d{4}$|^\\d{9}$",
                "date_standard": "^\\d{4}-\\d{2}-\\d{2}$|^\\d{2}/\\d{2}/\\d{4}$",
                "date_text": "^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\\s+\\d{1,2}\\s+\\d{4}$",
                "date_compact": "^\\d{8}$|^\\d{6}$",
                "coordinates": "^-?\\d+\\.?\\d*,-?\\d+\\.?\\d*$",
                "currency": "^\\$?\\d+\\.?\\d{0,2}$",
                "imei": "^\\d{15}$",
                "cvv": "^\\d{3,4}$",
                "ip": "^\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}$",
                "name_pattern": "^[A-Z][a-z]+ [A-Z][a-z]+$|^[A-Z][a-z]{2,}$",
                "long_numeric_id": "^\\d{6,20}$",
                "alphanumeric_id": "^[A-Z0-9]{6,20}$"
            },
            "fuzzy_rules": {
                "fnme": "firstname",
                "lstnm": "lastname", 
                "nm": "name",
                "phne": "phone",
                "eml": "email",
                "addr": "address",
                "usr": "user",
                "cst": "customer",
                "sub": "subscriber",
                "no": "number",
                "num": "number",
                "id": "identifier",
                "ref": "reference",
                "amt": "amount",
                "bal": "balance",
                "acct": "account",
                "pymt": "payment",
                "tel": "telephone",
                "mob": "mobile",
                "loc": "location",
                "coord": "coordinates"
            },
            "exclusions": [
                "status", "code", "type", "version", "timestamp", "method", "protocol", 
                "format", "encoding", "charset", "limit", "offset", "page", "size", 
                "count", "total", "success", "error", "message", "description",
                "content-type", "user-agent", "accept", "host", "connection", "cache-control",
                "length", "max", "min", "uuid", "guid", "hash", "checksum", "signature",
                "result", "response", "request", "verified", "preferred", "enabled", "disabled",
                "active", "inactive", "valid", "invalid", "tenuretype", "tenure", "tier",
                "autopay", "autodebit", "paperless", "billcycle", "billlanguage", "language",
                "locale", "timezone", "currency", "region", "country", "position",
                "subtype", "subclass", "subcategory", "subgroup", "sublevel"
            ],
            "pattern_mappings": {
                "email": ["SPI"],
                "phone": ["SPI"],
                "credit_card": ["RPI", "PCI"],
                "ssn": ["SPI"],
                "date_standard": ["SPI"],
                "date_text": ["SPI"],
                "date_compact": ["SPI"],
                "coordinates": ["CPNI"],
                "currency": ["RPI"],
                "imei": ["CPNI"],
                "cvv": ["PCI"],
                "ip": ["CSO"],
                "name_pattern": ["SPI"],
                "long_numeric_id": ["CONTEXTUAL"],
                "alphanumeric_id": ["CONTEXTUAL"]
            },
            "value_exclusions": [
                "true", "false", "null", "undefined", "yes", "no", "on", "off", 
                "enabled", "disabled", "active", "inactive", "valid", "invalid",
                "success", "failure", "ok", "error", "pending", "completed",
                "mature", "new", "old", "current", "expired", "draft", "final",
                "high", "medium", "low", "basic", "premium", "standard", "advanced",
                "public", "private", "internal", "external", "open", "closed",
                "available", "unavailable", "online", "offline", "ready", "busy"
            ],
            "business_value_patterns": [
                "^(MATURE|NEW|OLD|CURRENT|EXPIRED|DRAFT|FINAL)$",
                "^(HIGH|MEDIUM|LOW|BASIC|PREMIUM|STANDARD|ADVANCED)$", 
                "^(PUBLIC|PRIVATE|INTERNAL|EXTERNAL|OPEN|CLOSED)$",
                "^(AVAILABLE|UNAVAILABLE|ONLINE|OFFLINE|READY|BUSY)$",
                "^(ACTIVE|INACTIVE|ENABLED|DISABLED|VALID|INVALID)$",
                "^(SUCCESS|FAILURE|OK|ERROR|PENDING|COMPLETED)$"
            ],
            "developer_overrides": {
                "manual_blacklist": [],
                "manual_whitelist": []
            }
        }
        
        with open(self.patterns_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        print(f"📄 Created default patterns file: {self.patterns_file}")
    
    def compile_patterns(self):
        """Compile regex patterns for better performance"""
        for pattern_name, pattern_str in self.value_patterns.items():
            try:
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
    
    def has_code_or_type_suffix(self, field_name: str) -> bool:
        """Check if field ends with 'code' or 'type' but is NOT sensitive data - FIXED VERSION"""
        field_lower = field_name.lower()
        
        # IMPORTANT: Fields that END with 'code' but are actually SENSITIVE DATA
        sensitive_code_exceptions = [
            'zipcode', 'postalcode', 'areacode', 'countrycode', 'regioncode',
            'securitycode', 'verificationcode', 'accesscode', 'pincode',
            'activationcode', 'confirmationcode', 'passcode', 'passwordcode',
            'authcode', 'otpcode', 'mfacode', 'twofa', 'lockcode'
        ]
        
        # If it's a sensitive code, don't exclude it
        if any(exception in field_lower for exception in sensitive_code_exceptions):
            return False
        
        # Check for classification suffixes that indicate non-sensitive enum/type fields
        classification_suffixes = [
            'code', 'type', 'method', 'format', 'style', 'mode', 'kind',
            'category', 'class', 'classification', 'scheme', 'strategy',
            'variant', 'option', 'choice', 'selection'
        ]
        
        # Additional context-based checks for 'code' fields
        if field_lower.endswith('code'):
            # These patterns suggest it's a business/system code, not sensitive data
            business_code_patterns = [
                'plan', 'rate', 'product', 'service', 'status', 'error', 'result',
                'response', 'transaction', 'campaign', 'promotion', 'offer',
                'subscription', 'billing', 'invoice', 'payment'
            ]
            
            # If it contains business context, it's likely a classification code
            for pattern in business_code_patterns:
                if pattern in field_lower and not any(sensitive in field_lower for sensitive in sensitive_code_exceptions):
                    return True
            
            # If it's just "code" at the end without business context, check if it could be sensitive
            # Fields like "zipCode", "securityCode" should not be excluded
            return False
        
        # For other suffixes (type, method, etc.), apply normal logic
        for suffix in classification_suffixes[1:]:  # Skip 'code' since we handled it above
            if field_lower.endswith(suffix):
                return True
        
        return False
    
    def is_system_identifier_field(self, field_path: str) -> bool:
        """Check if field is a system-generated identifier (not sensitive personal data)"""
        final_key = self.extract_final_key(field_path).lower()
        
        # System identifier patterns
        system_id_patterns = [
            'requestid', 'sessionid', 'transactionid', 'correlationid',
            'messageid', 'batchid', 'processid', 'workflowid',
            'fingerprint', 'devicefingerprint', 'browserfingerprint',
            'traceid', 'spanid', 'logid', 'auditid',
            'systemid', 'serverid', 'instanceid', 'nodeid'
        ]
        
        # Additional context indicators for system fields
        system_context_patterns = [
            'system.', 'technical.', 'metadata.', 'internal.', 'debug.',
            'trace.', 'audit.', 'log.', 'monitoring.'
        ]
        
        field_path_lower = field_path.lower()
        
        # Check if it's a system identifier by name
        if any(pattern in final_key for pattern in system_id_patterns):
            return True
        
        # Check if it's in a system context
        if any(context in field_path_lower for context in system_context_patterns):
            return True
        
        return False
    
    def contextual_pattern_validation(self, field_path: str, value_str: str, pattern_name: str) -> bool:
        """Validate that a pattern match makes sense in the context of the field name"""
        final_key = self.extract_final_key(field_path).lower()
        
        # CVV validation - MUST have field name context
        if pattern_name == 'cvv':
            cvv_field_indicators = ['cvv', 'cvc', 'cvn', 'cid', 'security', 'verification']
            # Only consider it CVV if the field name suggests it
            if not any(indicator in final_key for indicator in cvv_field_indicators):
                return False
            # Also check value is actually 3-4 digits only
            if not re.match(r'^\d{3,4}$', value_str):
                return False
        
        # Phone validation - enhance context checking
        elif pattern_name == 'phone':
            phone_field_indicators = ['phone', 'tel', 'mobile', 'cell', 'msisdn', 'number']
            # Must have phone-related field name
            if not any(indicator in final_key for indicator in phone_field_indicators):
                return False
            # Value should look like an actual phone number
            if not re.match(r'^[\+]?[\d\s\-\(\)]{7,15}$', value_str):
                return False
        
        # Currency validation - improve patterns
        elif pattern_name in ['currency', 'currency_with_symbol', 'currency_formatted']:
            currency_field_indicators = ['amount', 'balance', 'cost', 'price', 'fee', 'charge', 'payment', 'bill']
            # Must have currency-related field name
            if not any(indicator in final_key for indicator in currency_field_indicators):
                return False
            # Must actually look like currency (has decimal or $ symbol)
            if not re.match(r'^\$?\d+(\.\d{1,2})?$', value_str):
                return False
        
        # Credit card validation
        elif pattern_name == 'credit_card':
            card_field_indicators = ['card', 'credit', 'debit', 'pan', 'account']
            if not any(indicator in final_key for indicator in card_field_indicators):
                return False
        
        # Email validation
        elif pattern_name == 'email':
            email_field_indicators = ['email', 'mail', 'contact']
            if not any(indicator in final_key for indicator in email_field_indicators):
                return False
        
        return True
    
    def is_personal_date_field(self, field_name: str) -> bool:
        """Check if field name indicates a personal date (like date of birth)"""
        field_lower = field_name.lower()
        
        # Personal date indicators - very specific to avoid false positives
        personal_date_keywords = [
            'dob', 'dateofbirth', 'birthdate', 'birthday', 'bday', 'birth', 'born'
        ]
        
        return any(keyword in field_lower for keyword in personal_date_keywords)
    
    def has_datetime_values(self, values: List[Any]) -> bool:
        """Check if values contain date-time stamps (not just dates) - FIXED VERSION"""
        if not values:
            return False
        
        # Patterns for datetime (with time components) - MORE PRECISE
        datetime_patterns = [
            re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'),        # ISO format with time: 2024-08-07T14:30:00
            re.compile(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}'),      # Date with space and time: 2024-08-07 14:30:00
            re.compile(r'\d{2}/\d{2}/\d{4}\s+\d{1,2}:\d{2}'),          # US format with time: 08/07/2024 2:30
            re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$'),     # ISO with timezone: 2024-08-07T14:30:00Z
            re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$'),  # ISO with offset: 2024-08-07T14:30:00+05:00
        ]
        
        # Unix timestamp patterns - BE MORE SPECIFIC
        unix_timestamp_patterns = [
            re.compile(r'^\d{13}$'),          # Milliseconds timestamp (exactly 13 digits)
            re.compile(r'^\d{16,}$'),         # Microseconds or nanoseconds (16+ digits)
        ]
        
        for value in values[:3]:  # Check first few values
            value_str = str(value).strip()
            
            # Check for datetime patterns first
            for pattern in datetime_patterns:
                if pattern.search(value_str):
                    return True
            
            # Check for Unix timestamps - but be more careful
            for pattern in unix_timestamp_patterns:
                if pattern.match(value_str):
                    # Additional validation for Unix timestamps
                    try:
                        timestamp_val = int(value_str)
                        # Valid Unix timestamps should be within reasonable range
                        # 2020-01-01 to 2030-12-31 in milliseconds
                        if 1577836800000 <= timestamp_val <= 1924991999999:
                            return True
                    except ValueError:
                        continue
        
        return False
    
    def is_sensitive_field_value(self, field_path: str, values: List[Any]) -> bool:
        """Check if field contains sensitive data patterns that should override datetime exclusion"""
        if not values:
            return False
        
        final_key = self.extract_final_key(field_path).lower()
        
        # Fields that should ALWAYS be checked for sensitive patterns, even if they look like timestamps
        sensitive_field_indicators = [
            'imei', 'cardnumber', 'creditcard', 'debitcard', 'cvv', 'ssn', 'social',
            'account', 'card', 'cc', 'pan', 'macaddress', 'mac', 'subscriber', 'msisdn'
        ]
        
        # If field name suggests sensitive data, check the values
        if any(indicator in final_key for indicator in sensitive_field_indicators):
            for value in values[:3]:
                value_str = str(value).strip()
                
                # Check for known sensitive patterns
                sensitive_patterns = [
                    re.compile(r'^\d{15}$'),                    # IMEI (15 digits)
                    re.compile(r'^\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}$'),  # Credit card
                    re.compile(r'^\d{3,4}$'),                   # CVV
                    re.compile(r'^\d{3}-\d{2}-\d{4}$'),         # SSN
                    re.compile(r'^[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}$'),  # MAC
                    re.compile(r'^\d{10,20}$'),                 # Long account numbers
                ]
                
                for pattern in sensitive_patterns:
                    if pattern.match(value_str):
                        return True
        
        return False

    def is_non_personal_date_field(self, field_name: str) -> bool:
        """Check if field name indicates a non-personal date (business/system dates) - FIXED VERSION"""
        field_lower = field_name.lower()
        
        # IMPORTANT: Exclude name fields that might contain date-related words
        name_field_indicators = [
            'name', 'firstName', 'lastname', 'fullname', 'surname', 'givenname', 
            'familyname', 'displayname', 'username', 'nickname'
        ]
        
        # If it's a name field, it's NOT a date field regardless of containing "last"
        if any(name_indicator in field_lower for name_indicator in name_field_indicators):
            return False
        
        # IMPORTANT: Exclude other non-date fields that might contain date-related words
        non_date_field_indicators = [
            'password', 'pass', 'auth', 'token', 'key', 'secret', 'code',
            'address', 'street', 'location', 'coordinate', 'phone', 'email',
            'account', 'balance', 'amount', 'payment', 'card', 'credit'
        ]
        
        # If it's clearly not a date-related field, return false
        if any(indicator in field_lower for indicator in non_date_field_indicators):
            return False
        
        # Non-personal date indicators - now more specific
        non_personal_date_indicators = [
            'effective', 'expiry', 'expire', 'expiration', 'valid', 'start', 'end',
            'created', 'updated', 'modified', 'changed', 'next', 'plan',
            'rate', 'service', 'activation', 'deactivation', 'suspension', 'resume',
            'renewal', 'billing', 'cycle', 'period', 'due', 'payment', 'transaction',
            'system', 'process', 'schedule', 'maintenance', 'upgrade', 'install',
            'login', 'logout', 'access', 'session', 'request', 'response'
        ]
        
        # Only check for date indicators if we've ruled out name fields
        # AND require the word "date" or "time" to be present for stronger indication
        has_date_indicator = any(indicator in field_lower for indicator in non_personal_date_indicators)
        has_date_word = any(word in field_lower for word in ['date', 'time', 'timestamp'])
        
        # Must have both a date indicator AND a date-related word
        return has_date_indicator and has_date_word

    def is_uuid_field(self, values: List[Any]) -> bool:
        """Check if field contains only UUID values"""
        if not values:
            return False
        
        # UUID patterns (various formats) - FIXED
        uuid_patterns = [
            re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE),  # Standard UUID
            re.compile(r'^[0-9a-f]{32}$', re.IGNORECASE),  # UUID without dashes
            re.compile(r'^[{]?[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}[}]?$', re.IGNORECASE)  # UUID with optional braces
        ]

        
        # Check if ALL values are UUIDs
        for value in values:
            value_str = str(value).strip()
            if not any(pattern.match(value_str) for pattern in uuid_patterns):
                return False
        
        return True
    
    def is_boolean_field(self, values: List[Any]) -> bool:
        """Check if field contains only boolean-type values"""
        if not values:
            return False
        
        # Define all possible boolean values
        boolean_values = {
            'true', 'false', 
            'yes', 'no', 
            'y', 'n',
            '1', '0',
            'on', 'off',
            'enabled', 'disabled',
            'active', 'inactive',
            'valid', 'invalid'
        }
        
        # Check if ALL values are boolean-type
        for value in values:
            value_str = str(value).strip().lower()
            if value_str not in boolean_values:
                return False
        
        return True
    
    def is_classification_field(self, field_path: str, values: List[Any]) -> bool:
        """Check if field is a classification/type field that contains data type names rather than actual data"""
        final_key = self.extract_final_key(field_path).lower()
        
        # Classification field indicators
        classification_indicators = [
            'type', 'kind', 'category', 'class', 'classification', 'method',
            'format', 'style', 'mode', 'variant', 'scheme', 'strategy'
        ]
        
        # Check if field name suggests it's a classification field
        is_classification_field = any(indicator in final_key for indicator in classification_indicators)
        
        if not is_classification_field:
            return False
        
        # Check if values are data type names/classifications rather than actual data
        classification_values = {
            # Identity types
            'ssn', 'social', 'passport', 'license', 'driverlicense', 'nationalid',
            # Payment types  
            'credit', 'debit', 'visa', 'mastercard', 'amex', 'discover',
            # Contact types
            'email', 'phone', 'mobile', 'home', 'work', 'business',
            # Address types
            'billing', 'shipping', 'home', 'work', 'mailing',
            # General types
            'primary', 'secondary', 'temporary', 'permanent', 'preferred',
            # Communication types
            'sms', 'call', 'mail', 'notification',
            # Document types
            'pdf', 'doc', 'image', 'text', 'json', 'xml'
        }
        
        # Check if ALL values are classification terms
        for value in values:
            value_str = str(value).strip().lower()
            if value_str not in classification_values:
                return False
        
        return True
    
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
    
    def is_sensitive_code_field(self, field_name: str) -> bool:
        """Check if a field ending in 'code' is actually sensitive data"""
        field_lower = field_name.lower()
        
        # Patterns that indicate sensitive codes
        sensitive_code_patterns = [
            'zip', 'postal', 'area', 'country', 'region',  # Location codes
            'security', 'verification', 'access', 'pin',    # Security codes  
            'activation', 'confirmation', 'auth',           # Authentication codes
            'cvv', 'cvc', 'cid',                           # Payment security codes
            'tax', 'ssn', 'national',                      # Government codes
            'pass', 'password', 'otp', 'mfa', 'lock'       # Authentication codes
        ]
        
        return any(pattern in field_lower for pattern in sensitive_code_patterns)

    def intelligent_keyword_match(self, field_path: str) -> List[str]:
        """Enhanced keyword matching with FIXED code/type filtering"""
        final_key = self.extract_final_key(field_path).lower()
        normalized_key = self.apply_fuzzy_matching(final_key)
        
        # NEW: Check developer overrides first
        if final_key in self.developer_overrides['manual_whitelist']:
            return []  # Developer explicitly excluded this field
        
        if final_key in self.developer_overrides['manual_blacklist']:
            return ['DEVELOPER_MANUAL']  # Developer manually added this field
        
        # ENHANCED CHECK: Skip if field has code/type suffix BUT not if it's sensitive
        if self.has_code_or_type_suffix(final_key):
            return []  # Don't blacklist classification fields
        
        categories = []
        
        for category, keywords in self.keywords.items():
            # Check both original and normalized key
            if any(keyword in final_key for keyword in keywords):
                categories.append(category.upper())
            elif any(keyword in normalized_key.lower() for keyword in keywords):
                categories.append(category.upper())
        
        return list(set(categories))

    def analyze_values(self, values: List[Any]) -> Dict[str, Any]:
        """Enhanced value analysis with CONTEXT-AWARE pattern matching"""
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
                    # ENHANCED CHECK: Skip date patterns if they contain time
                    if pattern_name.startswith(('date_')):
                        # Check if this looks like a datetime (has time component)
                        if self.has_datetime_values([value_str]):
                            continue  # Skip dates with time - not DOB
                    
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
        """Enhanced field analysis with FIXED date and code/type filtering"""
        final_key = self.extract_final_key(field_path)
        category = self.get_field_category(field_path)
        
        if category == 'unknown':
            return
        
    def analyze_field(self, field_path: str, values: List[Any]):
        """Enhanced field analysis with FIXED date and code/type filtering"""
        final_key = self.extract_final_key(field_path)
        category = self.get_field_category(field_path)
        
        if category == 'unknown':
            return
        
        # NEW: Check developer overrides FIRST (before any exclusions)
        if final_key in self.developer_overrides['manual_whitelist']:
            self.excluded_fields.append({
                'field_path': field_path,
                'final_key': final_key,
                'reason': '👨‍💻 Developer manually excluded this field (via developer_overrides)'
            })
            return
        
        # NEW: Check if developer manually added to blacklist
        developer_manual = final_key in self.developer_overrides['manual_blacklist']
        
        if developer_manual:
            print(f"🎯 Developer override detected: '{final_key}' manually added to blacklist")
            
            # Force blacklist this field regardless of other rules
            analysis_result = {
                'field_path': field_path,
                'final_key': final_key,
                'category': category,
                'blacklisted': True,
                'reasons': [f"👨‍💻 Developer manually added '{final_key}' to blacklist (via developer_overrides)"],
                'categories_detected': ['DEVELOPER_MANUAL'],
                'unique_values': [str(v) for v in values[:5]] if values else [],
                'confidence': 'High',
                'fuzzy_match': None,
                'key_based': True,
                'value_based': False,
                'developer_manual': True
            }
            
            # Add to appropriate blacklist
            if category == 'headers':
                self.headers_blacklist.add(final_key)
                print(f"🔒 Added '{final_key}' to headers blacklist (category: {category})")
            elif category in ['request', 'response']:
                self.payload_blacklist.add(final_key)
                print(f"🔒 Added '{final_key}' to payload blacklist (category: {category})")
            
            self.detailed_analysis.append(analysis_result)
            return
        
        # Continue with normal exclusion checks only if NOT developer manual
        # Check exclusions
        if self.should_exclude(final_key):
            self.excluded_fields.append({
                'field_path': field_path,
                'final_key': final_key,
                'reason': 'Excluded - Common non-sensitive field'
            })
            return
        
        # ENHANCED CHECK: Skip code/type fields
        if self.has_code_or_type_suffix(final_key):
            self.excluded_fields.append({
                'field_path': field_path,
                'final_key': final_key,
                'reason': 'Excluded - Code/Type field (classification, not sensitive data)'
            })
            return
        
        # ENHANCED CHECK: Skip boolean fields
        if self.is_boolean_field(values):
            self.excluded_fields.append({
                'field_path': field_path,
                'final_key': final_key,
                'reason': 'Excluded - Boolean field (True/False/Y/N values)'
            })
            return
        
        # ENHANCED CHECK: Skip UUID fields
        if self.is_uuid_field(values):
            self.excluded_fields.append({
                'field_path': field_path,
                'final_key': final_key,
                'reason': 'Excluded - UUID field (system-generated identifiers)'
            })
            return
        
        # ENHANCED CHECK: Skip classification fields
        if self.is_classification_field(field_path, values):
            self.excluded_fields.append({
                'field_path': field_path,
                'final_key': final_key,
                'reason': 'Excluded - Classification field (contains type names, not actual data)'
            })
            return
        
        # ENHANCED CHECK: Skip non-personal dates
        if not self.is_personal_date_field(final_key) and self.is_non_personal_date_field(final_key):
            self.excluded_fields.append({
                'field_path': field_path,
                'final_key': final_key,
                'reason': 'Excluded - Non-personal date field (business/system date)'
            })
            return
        
        # FIXED LOGIC: Skip fields with datetime values BUT only if they're not sensitive fields
        if values and self.has_datetime_values(values) and not self.is_personal_date_field(final_key):
            # BUT: Don't exclude if this field contains sensitive data (like IMEI, card numbers, etc.)
            if not self.is_sensitive_field_value(field_path, values):
                self.excluded_fields.append({
                    'field_path': field_path,
                    'final_key': final_key,
                    'reason': 'Excluded - Contains timestamps/datetime (not DOB)'
                })
                return
            # If it IS sensitive, continue with normal analysis (don't exclude)
        
        # Initialize analysis result for normal fields
        analysis_result = {
            'field_path': field_path,
            'final_key': final_key,
            'category': category,
            'blacklisted': False,
            'reasons': [],
            'categories_detected': [],
            'unique_values': [],
            'confidence': 'Low',
            'fuzzy_match': None,
            'key_based': False,
            'value_based': False,
            'developer_manual': False
        }
        
        # Key-based analysis (with enhanced filtering)
        key_categories = self.intelligent_keyword_match(field_path)
        if key_categories:
            analysis_result['key_based'] = True
            analysis_result['categories_detected'].extend(key_categories)
            
            if 'DEVELOPER_MANUAL' in key_categories:
                analysis_result['reasons'].append(f"👨‍💻 Developer manually added '{final_key}' to blacklist (via developer_overrides)")
            else:
                # Check if fuzzy matching was applied
                normalized_key = self.apply_fuzzy_matching(final_key.lower())
                if normalized_key != final_key.lower():
                    analysis_result['fuzzy_match'] = normalized_key
                    analysis_result['reasons'].append(f"Key-based: '{final_key}' intelligently matched to '{normalized_key}' → {', '.join(key_categories)}")
                else:
                    analysis_result['reasons'].append(f"Key-based: '{final_key}' contains sensitive keywords → {', '.join(key_categories)}")
        
        # Value-based analysis (with enhanced filtering)
        if values:
            value_analysis = self.analyze_values(values)
            analysis_result['unique_values'] = value_analysis['unique_values']
            
            if value_analysis['categories']:
                analysis_result['value_based'] = True
                analysis_result['categories_detected'].extend(value_analysis['categories'])
                analysis_result['reasons'].append(f"Value-based: Values match sensitive patterns {value_analysis['patterns_found']} → {', '.join(value_analysis['categories'])}")
                analysis_result['confidence'] = value_analysis['confidence']
        
        # Remove duplicates from categories
        analysis_result['categories_detected'] = list(set(analysis_result['categories_detected']))
        
        # Determine if should be blacklisted
        analysis_result['blacklisted'] = bool(analysis_result['categories_detected']) or developer_manual
        
        if not analysis_result['blacklisted']:
            analysis_result['reasons'].append("No sensitive patterns detected")
        
        # Add to appropriate blacklist - FIXED LOGIC
        if analysis_result['blacklisted']:
            if category == 'headers':
                self.headers_blacklist.add(final_key)
                print(f"🔒 Added '{final_key}' to headers blacklist (category: {category})")
            elif category in ['request', 'response']:
                self.payload_blacklist.add(final_key)
                print(f"🔒 Added '{final_key}' to payload blacklist (category: {category})")
        
        self.detailed_analysis.append(analysis_result)

    def generate_properties(self, output_file: str = 'application.properties'):
        """Generate consolidated application.properties file"""
        content = f"""# Telecom API Blacklist Configuration - INTERACTIVE VERSION
# Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Pattern source: {self.patterns_file}
# Total fields analyzed: {len(self.detailed_analysis)}
# Fields blacklisted: {len([r for r in self.detailed_analysis if r['blacklisted']])}
# Fields excluded: {len(self.excluded_fields)}
# Developer manual additions: {len(self.developer_overrides['manual_blacklist'])}
# Developer manual exclusions: {len(self.developer_overrides['manual_whitelist'])}

# ENHANCED FILTERING APPLIED:
# ✅ Excluded code/type fields (e.g., ratePlanCode, subscriberType)
# ✅ Excluded non-personal dates (e.g., ratePlanEffectiveDate)
# ✅ Excluded datetime stamps (dates with time components)
# ✅ Excluded boolean fields (true/false values)
# ✅ Excluded UUID fields (system identifiers)
# ✅ Only personal dates (DOB) are considered sensitive
# 🎯 Developer overrides applied for custom decisions

# CONSOLIDATED BLACKLISTS (duplicates removed)
payload.blacklist={','.join(sorted(self.payload_blacklist))}
headers.blacklist={','.join(sorted(self.headers_blacklist))}
"""
        
        with open(output_file, 'w') as f:
            f.write(content)
        
        print(f"📄 Interactive properties file generated: {output_file}")
        return output_file
    
    def generate_detailed_table_html(self, output_file: str = 'blacklist_detailed_table.html'):
        """Generate enhanced interactive HTML table with Add/Remove buttons"""
        
        blacklisted_fields = [r for r in self.detailed_analysis if r['blacklisted']]
        not_blacklisted_fields = [r for r in self.detailed_analysis if not r['blacklisted']]
        excluded_count = len(self.excluded_fields)
        fuzzy_matched_fields = [r for r in blacklisted_fields if r.get('fuzzy_match')]
        key_based_fields = [r for r in blacklisted_fields if r.get('key_based')]
        value_based_fields = [r for r in blacklisted_fields if r.get('value_based')]
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Interactive Telecom API Blacklist Analysis</title>
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
        .interactive-notice {{
            background: #e1f5fe; 
            color: #01579b; 
            padding: 15px; 
            border-radius: 8px; 
            margin: 20px 0;
            border-left: 4px solid #0288d1;
        }}
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
        .exclusions-section {{
            background: #f8f9fa; 
            padding: 20px; 
            border-radius: 8px; 
            margin: 20px 0;
            border-left: 4px solid #28a745;
        }}
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
        .btn-remove {{ 
            background: #dc3545; 
            color: white; 
            border: none; 
            padding: 6px 12px; 
            border-radius: 4px; 
            cursor: pointer; 
            font-size: 0.8em;
        }}
        .btn-remove:hover {{ background: #c82333; }}
        .btn-add {{ 
            background: #28a745; 
            color: white; 
            border: none; 
            padding: 6px 12px; 
            border-radius: 4px; 
            cursor: pointer; 
            font-size: 0.8em;
        }}
        .btn-add:hover {{ background: #218838; }}
        .btn-disabled {{ 
            background: #6c757d; 
            cursor: not-allowed; 
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
        .manual-indicator {{ 
            background: #ff6b35; 
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
        .config-section {{
            background: #f8f9fa; 
            padding: 20px; 
            border-radius: 8px; 
            margin: 20px 0;
        }}
        .config-output {{
            background: #2d3748; 
            color: #e2e8f0; 
            padding: 15px; 
            border-radius: 4px; 
            overflow-x: auto;
            font-family: 'Courier New', monospace;
            white-space: pre-wrap;
        }}
    </style>
    <script>
        // Store current blacklist state
        let currentPayloadBlacklist = new Set({json.dumps(list(self.payload_blacklist))});
        let currentHeadersBlacklist = new Set({json.dumps(list(self.headers_blacklist))});
        
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
        
        function addToBlacklist(fieldName, category, button) {{
            // Add to appropriate blacklist
            if (category === 'headers') {{
                currentHeadersBlacklist.add(fieldName);
            }} else {{
                currentPayloadBlacklist.add(fieldName);
            }}
            
            // Update button and row
            const row = button.closest('tr');
            row.className = 'blacklisted';
            
            // Change button to remove
            button.textContent = 'Remove';
            button.className = 'btn-remove';
            button.onclick = () => removeFromBlacklist(fieldName, category, button);
            
            // Update the first column to show it's blacklisted
            const firstCell = row.cells[0];
            firstCell.innerHTML = `<span class="final-key">${{fieldName}}</span><span class="manual-indicator">MANUAL</span>`;
            
            // Update configuration display
            updateConfigDisplay();
            
            // Show notification
            showNotification(`Added ${{fieldName}} to blacklist`, 'success');
        }}
        
        function removeFromBlacklist(fieldName, category, button) {{
            // Remove from appropriate blacklist
            if (category === 'headers') {{
                currentHeadersBlacklist.delete(fieldName);
            }} else {{
                currentPayloadBlacklist.delete(fieldName);
            }}
            
            // Update button and row
            const row = button.closest('tr');
            row.className = 'not-blacklisted';
            
            // Change button to add
            button.textContent = 'Add';
            button.className = 'btn-add';
            button.onclick = () => addToBlacklist(fieldName, category, button);
            
            // Update the first column to show it's safe
            const firstCell = row.cells[0];
            firstCell.innerHTML = '<span style="color: #28a745; font-weight: bold;">✓ SAFE</span>';
            
            // Update configuration display
            updateConfigDisplay();
            
            // Show notification
            showNotification(`Removed ${{fieldName}} from blacklist`, 'info');
        }}
        
        function updateConfigDisplay() {{
            const configOutput = document.getElementById('config-output');
            const payloadList = Array.from(currentPayloadBlacklist).sort().join(',');
            const headersList = Array.from(currentHeadersBlacklist).sort().join(',');
            
            configOutput.textContent = `payload.blacklist=${{payloadList}}
headers.blacklist=${{headersList}}`;
        }}
        
        function showNotification(message, type) {{
            // Create notification element
            const notification = document.createElement('div');
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 12px 20px;
                border-radius: 4px;
                color: white;
                font-weight: bold;
                z-index: 1000;
                opacity: 0;
                transition: opacity 0.3s ease;
                background: ${{type === 'success' ? '#28a745' : type === 'info' ? '#17a2b8' : '#dc3545'}};
            `;
            notification.textContent = message;
            
            document.body.appendChild(notification);
            
            // Fade in
            setTimeout(() => notification.style.opacity = '1', 10);
            
            // Remove after 3 seconds
            setTimeout(() => {{
                notification.style.opacity = '0';
                setTimeout(() => document.body.removeChild(notification), 300);
            }}, 3000);
        }}
        
        function exportConfiguration() {{
            const payloadList = Array.from(currentPayloadBlacklist).sort().join(',');
            const headersList = Array.from(currentHeadersBlacklist).sort().join(',');
            
            const config = `# Generated Configuration - ${{new Date().toISOString()}}
payload.blacklist=${{payloadList}}
headers.blacklist=${{headersList}}`;
            
            const blob = new Blob([config], {{ type: 'text/plain' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'application.properties';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            showNotification('Configuration exported!', 'success');
        }}
        
        function saveDeveloperOverrides() {{
            // Load existing overrides from developer_overrides.json if it exists
            // For now, we'll work with current session data, but provide instructions
            
            // Collect all manually added/removed fields
            const manualBlacklist = [];
            const manualWhitelist = [];
            
            // Get original blacklists from Python analysis
            const originalPayload = new Set({json.dumps(list(self.payload_blacklist))});
            const originalHeaders = new Set({json.dumps(list(self.headers_blacklist))});
            
            // Compare current vs original to find manual changes
            for (const field of currentPayloadBlacklist) {{
                if (!originalPayload.has(field)) {{
                    manualBlacklist.push(field);
                }}
            }}
            for (const field of currentHeadersBlacklist) {{
                if (!originalHeaders.has(field)) {{
                    manualBlacklist.push(field);
                }}
            }}
            
            // Find manually removed fields
            for (const field of originalPayload) {{
                if (!currentPayloadBlacklist.has(field)) {{
                    manualWhitelist.push(field);
                }}
            }}
            for (const field of originalHeaders) {{
                if (!currentHeadersBlacklist.has(field)) {{
                    manualWhitelist.push(field);
                }}
            }}
            
            // Load existing developer overrides from the analysis (if any)
            const existingManualBlacklist = {json.dumps(list(self.developer_overrides['manual_blacklist']))};
            const existingManualWhitelist = {json.dumps(list(self.developer_overrides['manual_whitelist']))};
            
            // Merge with existing overrides (union)
            const finalBlacklist = [...new Set([...existingManualBlacklist, ...manualBlacklist])].sort();
            const finalWhitelist = [...new Set([...existingManualWhitelist, ...manualWhitelist])].sort();
            
            // Remove conflicts (whitelist takes precedence)
            const cleanedBlacklist = finalBlacklist.filter(field => !finalWhitelist.includes(field));
            
            // Create enhanced override object with instructions
            const overrides = {{
                "_README": {{
                    "description": "Developer Manual Overrides for Telecom API Blacklist Generator",
                    "usage": [
                        "1. Place this file as 'developer_overrides.json' in the same directory as your analysis script",
                        "2. Re-run the blacklist analysis: python interactive_blacklist_generator.py data.json",
                        "3. The tool will automatically apply these overrides during analysis",
                        "4. Manual blacklist fields will always be included in the final blacklist",
                        "5. Manual whitelist fields will always be excluded from the final blacklist",
                        "6. You can edit this file manually to add/remove fields if needed"
                    ],
                    "generated": new Date().toISOString(),
                    "version": "2.0"
                }},
                "manual_blacklist": cleanedBlacklist,
                "manual_whitelist": finalWhitelist,
                "metadata": {{
                    "total_manual_additions": cleanedBlacklist.length,
                    "total_manual_exclusions": finalWhitelist.length,
                    "last_updated": new Date().toISOString(),
                    "note": "Fields in manual_blacklist will always be blacklisted. Fields in manual_whitelist will never be blacklisted."
                }}
            }};
            
            // Download as JSON file
            const blob = new Blob([JSON.stringify(overrides, null, 2)], {{ type: 'application/json' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'developer_overrides.json';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            showNotification('Developer overrides saved! Place file in project directory and re-run analysis.', 'success');
        }}
        
        // Initialize with all shown
        window.onload = function() {{
            filterTable('all');
            updateConfigDisplay();
        }}
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔒 Interactive Telecom API Blacklist Analysis</h1>
            <h2>🎯 Click Add/Remove to customize your blacklist</h2>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <div class="interactive-notice">
            <h3>🎯 Interactive Features:</h3>
            <ul>
                <li><strong>Add Button:</strong> Manually add safe fields to blacklist if they contain sensitive data in your context</li>
                <li><strong>Remove Button:</strong> Remove automatically detected fields if they're not sensitive in your context</li>
                <li><strong>Real-time Updates:</strong> Configuration updates immediately as you make changes</li>
                <li><strong>Persistent Storage:</strong> Changes are saved to patterns_config.json for future runs</li>
                <li><strong>Export Config:</strong> Download the final configuration for your application</li>
            </ul>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{len(self.detailed_analysis)}</div>
                <div>Analyzed Fields</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(blacklisted_fields)}</div>
                <div>Auto-Blacklisted</div>
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
                <div class="stat-number">{excluded_count}</div>
                <div>Smartly Excluded</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(fuzzy_matched_fields)}</div>
                <div>Fuzzy Detected</div>
            </div>
        </div>

        <div class="exclusions-section">
            <h3>📋 Smart Exclusions Applied ({excluded_count} fields):</h3>
            <div style="max-height: 200px; overflow-y: auto;">"""
        
        # Group exclusions by reason
        exclusion_groups = {}
        for exclusion in self.excluded_fields:
            reason = exclusion['reason']
            if reason not in exclusion_groups:
                exclusion_groups[reason] = []
            exclusion_groups[reason].append(exclusion['final_key'])
        
        for reason, fields in exclusion_groups.items():
            html_content += f"<p><strong>{reason}:</strong> {', '.join(fields[:10])}"
            if len(fields) > 10:
                html_content += f" <em>(+{len(fields)-10} more)</em>"
            html_content += "</p>"
        
        html_content += f"""
            </div>
        </div>

        <div class="filter-controls">
            <strong>Filter View:</strong>
            <button class="btn filter-btn" onclick="filterTable('all')">Show All</button>
            <button class="btn filter-btn" onclick="filterTable('blacklisted')">Only Blacklisted</button>
            <button class="btn filter-btn" onclick="filterTable('safe')">Only Safe Fields</button>
            
            <span style="margin-left: 20px;"><strong>Actions:</strong></span>
            <button class="btn" onclick="exportConfiguration()">📥 Export Configuration</button>
            <button class="btn" onclick="saveDeveloperOverrides()">💾 Save Overrides</button>
        </div>

        <div style="margin: 30px 0;">
            <table>
                <thead>
                    <tr>
                        <th style="width: 20%;">Field Status</th>
                        <th style="width: 35%;">Original Field & Values</th>
                        <th style="width: 35%;">Analysis & Reason</th>
                        <th style="width: 10%;">Action</th>
                    </tr>
                </thead>
                <tbody>
"""

        # Combine all fields for single table
        all_fields = blacklisted_fields + not_blacklisted_fields
        all_fields.sort(key=lambda x: (x['category'], x['field_path']))

        for result in all_fields:
            row_class = "blacklisted" if result['blacklisted'] else "not-blacklisted"
            field_name = result['final_key']
            category = result['category']
            
            # Field Status column
            if result['blacklisted']:
                field_status = f'<span class="final-key">{field_name}</span>'
                
                # Add indicators
                if result.get('developer_manual'):
                    field_status += '<span class="manual-indicator">MANUAL</span>'
                elif result.get('fuzzy_match'):
                    field_status += '<span class="fuzzy-indicator">FUZZY</span>'
                if result.get('key_based') and not result.get('developer_manual'):
                    field_status += '<span class="key-based-indicator">KEY</span>'
                if result.get('value_based'):
                    field_status += '<span class="value-based-indicator">VALUE</span>'
                
                # Add category tags
                if result['categories_detected']:
                    category_tags = ''.join([f'<span class="category-tag {cat.lower()}">{cat}</span>' 
                                           for cat in result['categories_detected'] if cat != 'DEVELOPER_MANUAL'])
                    if category_tags:
                        field_status += f'<br><div style="margin-top: 5px;">{category_tags}</div>'
            else:
                field_status = '<span style="color: #28a745; font-weight: bold;">✓ SAFE</span>'
            
            # Original field & values column
            original_field = f'<div class="field-path">{result["field_path"]}</div>'
            if result['unique_values']:
                # Limit display to first 3 unique values
                display_values = result['unique_values'][:3]
                values_text = '<br>'.join([f'<code>{v}</code>' for v in display_values])
                if len(result['unique_values']) > 3:
                    values_text += f'<br><em>... and {len(result["unique_values"]) - 3} more</em>'
                original_field += f'<div class="values" style="margin-top: 8px;"><strong>Values:</strong><br>{values_text}</div>'
            
            # Analysis & Reason column
            reason = '<br>'.join(result['reasons'])
            
            # Action column
            if result['blacklisted']:
                action_button = f'<button class="btn-remove" onclick="removeFromBlacklist(\'{field_name}\', \'{category}\', this)">Remove</button>'
            else:
                action_button = f'<button class="btn-add" onclick="addToBlacklist(\'{field_name}\', \'{category}\', this)">Add</button>'
            
            html_content += f"""
                    <tr class="{row_class}">
                        <td>{field_status}</td>
                        <td>{original_field}</td>
                        <td class="reason">{reason}</td>
                        <td>{action_button}</td>
                    </tr>
"""

        html_content += f"""
                </tbody>
            </table>
        </div>

        <div class="config-section">
            <h3>⚙️ Live Configuration (Updates as you click Add/Remove):</h3>
            <button class="btn" onclick="exportConfiguration()" style="margin-bottom: 10px;">📥 Download Configuration File</button>
            <button class="btn" onclick="saveDeveloperOverrides()" style="margin-bottom: 10px; margin-left: 10px;">💾 Save Developer Overrides</button>
            <pre class="config-output" id="config-output">
payload.blacklist={','.join(sorted(self.payload_blacklist))}
headers.blacklist={','.join(sorted(self.headers_blacklist))}
            </pre>
        </div>

        <div style="background: #d4edda; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3>🎯 How to Use Interactive Features:</h3>
            <ol>
                <li><strong>Review Auto-Detections:</strong> Check the automatically blacklisted fields in the table</li>
                <li><strong>Add Missing Fields:</strong> Click "Add" on safe fields that should be blacklisted in your context</li>
                <li><strong>Remove False Positives:</strong> Click "Remove" on blacklisted fields that aren't sensitive for you</li>
                <li><strong>Save Your Changes:</strong> Click "💾 Save Overrides" to download developer_overrides.json</li>
                <li><strong>Apply Changes:</strong> Place the file in your project directory and re-run the analysis</li>
                <li><strong>Iterative Refinement:</strong> Continue refining across multiple sessions</li>
            </ol>
        </div>

        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3>💾 Developer Override Persistence (Simplified):</h3>
            <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #28a745;">
                <h4>✨ New Simplified Workflow:</h4>
                <ol>
                    <li><strong>Make Changes:</strong> Click Add/Remove buttons as needed</li>
                    <li><strong>Save Overrides:</strong> Click "💾 Save Overrides" to download <code>developer_overrides.json</code></li>
                    <li><strong>Place File:</strong> Put the downloaded file in your project directory</li>
                    <li><strong>Re-run Analysis:</strong> Run the script again - it will automatically load your overrides!</li>
                </ol>
            </div>
            
            <h4>📋 How it Works:</h4>
            <ul>
                <li>The tool checks for <code>developer_overrides.json</code> at startup</li>
                <li>Your manual decisions are automatically applied during analysis</li>
                <li>No merge script needed - just download and place the file</li>
                <li>The file is self-documenting with usage instructions</li>
                <li>You can edit the JSON file manually if needed</li>
            </ul>
            
            <h4>🔄 Multiple Sessions:</h4>
            <ul>
                <li>Each save merges with existing overrides (if any)</li>
                <li>Whitelist takes precedence over blacklist (no conflicts)</li>
                <li>You can continue refining across multiple sessions</li>
            </ul>
        </div>
    </div>
</body>
</html>
"""

        with open(output_file, 'w') as f:
            f.write(html_content)
        
        print(f"📄 Interactive detailed table generated: {output_file}")
        return output_file
    
    def print_console_summary(self):
        """Print enhanced console summary"""
        blacklisted_count = len([r for r in self.detailed_analysis if r['blacklisted']])
        excluded_count = len(self.excluded_fields)
        fuzzy_count = len([r for r in self.detailed_analysis if r.get('fuzzy_match')])
        manual_additions = len(self.developer_overrides['manual_blacklist'])
        manual_exclusions = len(self.developer_overrides['manual_whitelist'])
        
        print("\n" + "="*70)
        print("        INTERACTIVE BLACKLIST ANALYSIS SUMMARY")
        print("="*70)
        print(f"🧠 Intelligence Level: INTERACTIVE with developer overrides")
        print(f"📊 Total fields analyzed: {len(self.detailed_analysis)}")
        print(f"🚫 Fields blacklisted: {blacklisted_count}")
        print(f"✅ Fields smartly excluded: {excluded_count}")
        print(f"🎯 Fuzzy detections: {fuzzy_count}")
        print(f"👨‍💻 Developer manual additions: {manual_additions}")
        print(f"👨‍💻 Developer manual exclusions: {manual_exclusions}")
        
        print(f"\n📂 CONSOLIDATED BLACKLISTS:")
        print(f"   payload.blacklist: {len(self.payload_blacklist)} fields")
        print(f"   headers.blacklist: {len(self.headers_blacklist)} fields")
        
        # Show exclusion breakdown
        if self.excluded_fields:
            exclusion_reasons = {}
            for exclusion in self.excluded_fields:
                reason = exclusion['reason']
                exclusion_reasons[reason] = exclusion_reasons.get(reason, 0) + 1
            
            print(f"\n🎯 Smart Exclusions Breakdown:")
            for reason, count in exclusion_reasons.items():
                print(f"   {reason}: {count} fields")
        
        # Show developer overrides
        if self.developer_overrides['manual_blacklist']:
            print(f"\n👨‍💻 Developer Manual Additions:")
            for field in list(self.developer_overrides['manual_blacklist'])[:5]:
                print(f"   ✅ {field}")
            if len(self.developer_overrides['manual_blacklist']) > 5:
                print(f"   ... and {len(self.developer_overrides['manual_blacklist']) - 5} more")
        
        if self.developer_overrides['manual_whitelist']:
            print(f"\n👨‍💻 Developer Manual Exclusions:")
            for field in list(self.developer_overrides['manual_whitelist'])[:5]:
                print(f"   ❌ {field}")
            if len(self.developer_overrides['manual_whitelist']) > 5:
                print(f"   ... and {len(self.developer_overrides['manual_whitelist']) - 5} more")
        
        print(f"\n📋 Examples of fixes applied:")
        for exclusion in self.excluded_fields[:5]:
            print(f"   ✅ {exclusion['final_key']} → {exclusion['reason']}")
        
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
        
        print(f"\n🎯 Next Steps:")
        print(f"   1. Open the interactive HTML table to review and customize")
        print(f"   2. Click Add/Remove buttons to fine-tune the blacklist")
        print(f"   3. Export the final configuration when satisfied")
        print(f"   4. Your decisions will be saved for future runs")
    
    def analyze_data(self, data_file: str):
        """Analyze the extracted data with enhanced filtering"""
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
        print("Usage: python interactive_blacklist_generator.py <postman_extraction_results.json> [patterns_config.json]")
        print("Example: python interactive_blacklist_generator.py data.json patterns_config.json")
        return
    
    data_file = sys.argv[1]
    patterns_file = sys.argv[2] if len(sys.argv) > 2 else 'patterns_config.json'
    
    if not os.path.exists(data_file):
        print(f"❌ Data file {data_file} not found")
        return
    
    print("🚀 Starting INTERACTIVE blacklist analysis...")
    print("🎯 New Feature: Add/Remove buttons for manual override")
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
        print(f"   🎯 Interactive table: {table_file}")
        print(f"   ⚙️  Patterns config: {patterns_file}")
        
        print(f"\n✅ Interactive analysis complete!")
        print(f"🎯 New Features:")
        print(f"   • Add/Remove buttons in HTML table")
        print(f"   • Real-time configuration updates")
        print(f"   • Developer overrides saved to patterns_config.json")
        print(f"   • Persistent decisions across runs")
        print(f"   • Export final configuration")
        
        print(f"\n📖 Usage:")
        print(f"   1. Open {table_file} in your browser")
        print(f"   2. Review auto-detected blacklisted fields")
        print(f"   3. Click 'Add' on safe fields that should be blacklisted")
        print(f"   4. Click 'Remove' on blacklisted fields that are actually safe")
        print(f"   5. Export the final configuration")
        print(f"   6. Your decisions are saved for future runs!")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()