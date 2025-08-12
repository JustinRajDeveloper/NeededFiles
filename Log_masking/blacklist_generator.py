#!/usr/bin/env python3
"""
Enhanced Interactive Telecom API Blacklist Generator with Developer UI
NEW FEATURES:
- Developer-friendly tabbed interface
- Remove/Add buttons for dynamic field management
- Downloadable developer overrides JSON
- Automatic override loading and merging
- Separate tables for exact match, value-based, exclusions, and safe fields
- Complete field listings without truncation
"""

import json
import re
import os
from datetime import datetime
from typing import Dict, List, Set, Any
from collections import defaultdict

class EnhancedTelecomBlacklistGenerator:
    def __init__(self, patterns_file: str = 'enhanced_patterns_config.json'):
        self.patterns_file = patterns_file
        self.developer_overrides_file = 'developer_overrides.json'
        
        # Initialize all attributes with defaults
        self.exact_keywords = {}
        self.entity_prefixes = []
        self.value_patterns = {}
        self.fuzzy_rules = {}
        self.exclusions = set()
        self.pattern_mappings = {}
        self.value_exclusions = set()
        self.business_value_patterns = []
        
        # Developer overrides
        self.developer_overrides = {
            'manual_blacklist': set(),
            'manual_whitelist': set()
        }
        
        # Consolidated blacklists
        self.payload_blacklist = set()
        self.headers_blacklist = set()
        
        # Detailed analysis for reporting - categorized
        self.exact_match_blacklisted = []
        self.value_based_blacklisted = []
        self.safe_fields = []
        self.excluded_fields = []
        
        # Compiled regex patterns
        self.compiled_patterns = {}
        self.compiled_exact_patterns = {}
        
        # Load developer overrides first, then patterns
        self.load_developer_overrides()
        self.load_patterns()
        self.compile_patterns()
    
    def load_developer_overrides(self):
        """Load and merge developer overrides if file exists"""
        if os.path.exists(self.developer_overrides_file):
            try:
                with open(self.developer_overrides_file, 'r') as f:
                    overrides = json.load(f)
                
                self.developer_overrides = {
                    'manual_blacklist': set(overrides.get('manual_blacklist', [])),
                    'manual_whitelist': set(overrides.get('manual_whitelist', []))
                }
                
                print(f"✅ Loaded developer overrides from {self.developer_overrides_file}")
                print(f"   Manual blacklist: {len(self.developer_overrides['manual_blacklist'])} fields")
                print(f"   Manual whitelist: {len(self.developer_overrides['manual_whitelist'])} fields")
                
                # Merge into patterns config if it exists
                self.merge_overrides_to_patterns()
                
            except Exception as e:
                print(f"⚠️  Error loading developer overrides: {e}")
                self.developer_overrides = {'manual_blacklist': set(), 'manual_whitelist': set()}
        else:
            print(f"📝 No existing developer overrides file found")
    
    def merge_overrides_to_patterns(self):
        """Merge developer overrides into patterns config file"""
        if os.path.exists(self.patterns_file):
            try:
                with open(self.patterns_file, 'r') as f:
                    config = json.load(f)
                
                # Update developer overrides in patterns config
                config['developer_overrides'] = {
                    'manual_blacklist': list(self.developer_overrides['manual_blacklist']),
                    'manual_whitelist': list(self.developer_overrides['manual_whitelist'])
                }
                
                # Write back to patterns file
                with open(self.patterns_file, 'w') as f:
                    json.dump(config, f, indent=2)
                
                print(f"🔄 Merged developer overrides into {self.patterns_file}")
                
            except Exception as e:
                print(f"⚠️  Error merging overrides to patterns: {e}")
    
    def create_enhanced_patterns_file(self):
        """Create enhanced patterns file with extensive abbreviations and exact matching"""
        enhanced_config = {
            "entity_prefixes": [
                # Customer variations
                "customer", "cust", "c", "client", "cli", "subscriber", "sub", "s",
                "user", "usr", "u", "person", "pers", "p", "individual", "ind",
                "account", "acc", "acct", "a", "member", "mem", "m", "profile", "prof",
                
                # Business entities
                "employee", "emp", "e", "staff", "operator", "op", "admin", "administrator",
                "contact", "cont", "owner", "holder", "cardholder", "ch",
                
                # System entities
                "primary", "prim", "secondary", "sec", "billing", "bill", "payment", "pay",
                "emergency", "emerg", "backup", "temp", "temporary", "alt", "alternate"
            ],
            
            "exact_keywords": {
                "spi": {
                    # Name variations - EXTENSIVE LIST
                    "name_fields": [
                        # Full name variations
                        "name", "nm", "nme", "fullname", "full_name", "completename", "complete_name",
                        "wholename", "whole_name", "entirename", "entire_name",
                        
                        # First name variations
                        "firstname", "first_name", "fname", "fnme", "fn", "f_name", "givenname", 
                        "given_name", "forename", "fore_name", "prename", "pre_name",
                        
                        # Last name variations
                        "lastname", "last_name", "lname", "lnme", "ln", "l_name", "surname", 
                        "sur_name", "familyname", "family_name", "patronymic",
                        
                        # Middle name variations
                        "middlename", "middle_name", "mname", "mnme", "mn", "m_name",
                        "middleinitial", "middle_initial", "mi",
                        
                        # Other name variations
                        "displayname", "display_name", "nickname", "nick_name", "alias", 
                        "username", "user_name", "uname", "usrnm", "screenname", "screen_name",
                        "handle", "moniker", "title", "suffix", "prefix", "maiden", "maidenname"
                    ],
                    
                    # Email variations - EXTENSIVE LIST
                    "email_fields": [
                        "email", "eml", "em", "e_mail", "emailaddr", "email_addr", "emailaddress", 
                        "email_address", "mail", "mailaddr", "mail_addr", "mailaddress", "mail_address",
                        "contact", "contactemail", "contact_email", "emailid", "email_id", 
                        "mailid", "mail_id", "emailaccount", "email_account", "mailaccount", "mail_account",
                        "workmail", "work_mail", "workemail", "work_email", "businessemail", "business_email",
                        "personalemail", "personal_email", "homemail", "home_mail", "homeemail", "home_email",
                        "primaryemail", "primary_email", "secondaryemail", "secondary_email",
                        "alternateemail", "alternate_email", "backupemail", "backup_email"
                    ],
                    
                    # Phone variations - EXTENSIVE LIST
                    "phone_fields": [
                        "phone", "phn", "phne", "ph", "fone", "tel", "telephone", "tele", "mobile", 
                        "mob", "cell", "cellular", "cellphone", "cell_phone", "mobilephone", "mobile_phone",
                        "msisdn", "number", "num", "no", "phoneno", "phone_no", "phonenumber", "phone_number",
                        "contactno", "contact_no", "contactnumber", "contact_number", "tel_no", "telephone_no",
                        "homephone", "home_phone", "workphone", "work_phone", "businessphone", "business_phone",
                        "officephone", "office_phone", "personalphone", "personal_phone", "mobilenum", "mobile_num",
                        "cellnum", "cell_num", "phoneline", "phone_line", "line", "extension", "ext",
                        "primaryphone", "primary_phone", "secondaryphone", "secondary_phone", "fax", "faxno", "fax_no"
                    ],
                    
                    # Address variations - EXTENSIVE LIST
                    "address_fields": [
                        "address", "addr", "add", "location", "loc", "place", "residence", "dwelling",
                        "street", "st", "str", "streetaddress", "street_address", "streetaddr", "street_addr",
                        "homeaddress", "home_address", "workaddress", "work_address", "businessaddress", "business_address",
                        "mailingaddress", "mailing_address", "billingaddress", "billing_address", "shippingaddress", "shipping_address",
                        "physicaladdress", "physical_address", "residentialaddress", "residential_address",
                        "primaryaddress", "primary_address", "secondaryaddress", "secondary_address",
                        
                        # Address components
                        "city", "town", "municipality", "locality", "county", "state", "province", "region", 
                        "country", "nation", "zip", "zipcode", "zip_code", "postal", "postalcode", "postal_code",
                        "postcode", "post_code", "area", "areacode", "area_code", "district", "zone",
                        "apartment", "apt", "unit", "suite", "ste", "floor", "building", "bldg"
                    ],
                    
                    # Date of Birth variations - EXTENSIVE LIST
                    "dob_fields": [
                        "dob", "dateofbirth", "date_of_birth", "birthdate", "birth_date", "birthday", "bday", "b_day",
                        "birth", "born", "birthtime", "birth_time", "dateborn", "date_born", "db", "bd",
                        "birthyear", "birth_year", "birthmonth", "birth_month", "birthday", "birth_day",
                        "dobirth", "do_birth", "nativity", "natal", "age", "yob", "year_of_birth"
                    ],
                    
                    # SSN and ID variations - EXTENSIVE LIST
                    "ssn_fields": [
                        "ssn", "socialsecurity", "social_security", "socialsecuritynumber", "social_security_number",
                        "social", "taxid", "tax_id", "taxpayerid", "taxpayer_id", "tin", "ein",
                        "nationalid", "national_id", "nationalnumber", "national_number", "citizenid", "citizen_id",
                        "identityno", "identity_no", "identitynumber", "identity_number", "identification", "ident",
                        "personalid", "personal_id", "personid", "person_id", "individualid", "individual_id",
                        "govid", "gov_id", "governmentid", "government_id", "federalid", "federal_id"
                    ],
                    
                    # License variations - EXTENSIVE LIST
                    "license_fields": [
                        "license", "licence", "driverlicense", "driver_license", "driverlicence", "driver_licence",
                        "dl", "dln", "driverlicensenumber", "driver_license_number", "licensenum", "license_num",
                        "drivinglicense", "driving_license", "drivingpermit", "driving_permit", "permit",
                        "passport", "passportno", "passport_no", "passportnumber", "passport_number",
                        "passportid", "passport_id", "visa", "visano", "visa_no", "visanumber", "visa_number"
                    ],
                    
                    # General personal identifiers
                    "personal_fields": [
                        "subscriber", "customer", "cust", "personal", "individual", "person", "profile",
                        "identity", "ident", "private", "confidential", "sensitive", "pii", "personalinfo", "personal_info"
                    ]
                },
                
                "cpni": {
                    # Communication variations
                    "communication_fields": [
                        "call", "cll", "calling", "voice", "voicecall", "voice_call", "conversation", "conv",
                        "sms", "message", "msg", "text", "textmessage", "text_message", "mms", "chat",
                        "communication", "comm", "talk", "audio", "recording", "rec"
                    ],
                    
                    # Data usage variations
                    "usage_fields": [
                        "data", "usage", "consumed", "consumption", "volume", "bytes", "mb", "gb", "tb",
                        "megabytes", "gigabytes", "terabytes", "kilobytes", "kb", "traffic", "bandwidth", "bw",
                        "speed", "throughput", "transfer", "download", "upload", "stream", "streaming"
                    ],
                    
                    # Network variations
                    "network_fields": [
                        "network", "net", "nw", "cell", "cellular", "tower", "antenna", "signal", "coverage",
                        "connection", "conn", "session", "sess", "bearer", "carrier", "operator", "provider",
                        "imsi", "imei", "mcc", "mnc", "lac", "cgi", "cellid", "cell_id", "networkid", "network_id",
                        "operatorid", "operator_id", "carrierid", "carrier_id", "providerid", "provider_id"
                    ],
                    
                    # Location variations
                    "location_fields": [
                        "location", "loc", "position", "pos", "coordinates", "coord", "coords", "gps",
                        "latitude", "lat", "longitude", "lng", "lon", "geolocation", "geo", "geocode",
                        "place", "whereabouts", "locale", "spot", "site", "point", "area", "zone", "region"
                    ],
                    
                    # Service variations
                    "service_fields": [
                        "service", "svc", "plan", "package", "subscription", "sub", "activation", "provision",
                        "feature", "addon", "add_on", "option", "roaming", "international", "domestic"
                    ],
                    
                    # Session and timing variations
                    "session_fields": [
                        "session", "sess", "duration", "time", "period", "start", "end", "begin", "finish",
                        "timestamp", "starttime", "start_time", "endtime", "end_time", "calltime", "call_time"
                    ]
                },
                
                "rpi": {
                    # Payment variations
                    "payment_fields": [
                        "payment", "pay", "billing", "bill", "invoice", "charge", "fee", "cost", "price",
                        "amount", "amt", "total", "sum", "subtotal", "grandtotal", "grand_total",
                        "balance", "bal", "credit", "debit", "debt", "owed", "due", "outstanding"
                    ],
                    
                    # Financial variations
                    "financial_fields": [
                        "account", "acct", "financial", "finance", "money", "currency", "revenue", "income",
                        "expense", "expenditure", "transaction", "trans", "purchase", "sale", "order",
                        "receipt", "paymentid", "payment_id", "transactionid", "transaction_id", "reference", "ref",
                        "confirmation", "conf", "approval", "auth", "authorization"
                    ],
                    
                    # Card variations
                    "card_fields": [
                        "card", "cc", "creditcard", "credit_card", "debitcard", "debit_card", "cardno", "card_no",
                        "cardnumber", "card_number", "cardholder", "card_holder", "cardname", "card_name",
                        "cardtype", "card_type", "cardissuer", "card_issuer", "paymentcard", "payment_card",
                        "bankcard", "bank_card", "plasticcard", "plastic_card"
                    ]
                },
                
                "cso": {
                    # Support variations
                    "support_fields": [
                        "ticket", "support", "help", "issue", "problem", "complaint", "feedback", "note",
                        "comment", "remark", "observation", "report", "incident", "case", "request", "req"
                    ],
                    
                    # Internal variations
                    "internal_fields": [
                        "internal", "int", "employee", "emp", "staff", "operator", "op", "admin", "administrator",
                        "system", "sys", "config", "configuration", "setting", "settings", "parameter", "param"
                    ],
                    
                    # Metrics variations
                    "metrics_fields": [
                        "metric", "performance", "perf", "quality", "log", "audit", "monitor", "monitoring",
                        "track", "tracking", "measure", "measurement", "stats", "statistics", "analytics",
                        "kpi", "indicator", "score", "rating", "benchmark"
                    ]
                },
                
                "pci": {
                    # Card number variations
                    "card_number_fields": [
                        "card", "cc", "creditcard", "credit_card", "debitcard", "debit_card", "pan",
                        "cardnumber", "card_number", "cardno", "card_no", "ccnumber", "cc_number",
                        "accountnumber", "account_number", "number", "num", "no"
                    ],
                    
                    # Security code variations
                    "security_code_fields": [
                        "cvv", "cvc", "cvn", "cid", "securitycode", "security_code", "verificationcode",
                        "verification_code", "checkcode", "check_code", "csc", "cardcode", "card_code",
                        "securitynumber", "security_number", "pin", "pincode", "pin_code"
                    ],
                    
                    # Expiry variations
                    "expiry_fields": [
                        "expiry", "expire", "expiration", "exp", "expirydate", "expiry_date", "expirationdate",
                        "expiration_date", "validthru", "valid_thru", "validuntil", "valid_until", "goodthru", "good_thru"
                    ],
                    
                    # Cardholder variations
                    "cardholder_fields": [
                        "cardholder", "card_holder", "holdername", "holder_name", "cardname", "card_name",
                        "nameoncard", "name_on_card", "cardownername", "card_owner_name", "ownername", "owner_name"
                    ]
                }
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
                "manual_blacklist": list(self.developer_overrides.get('manual_blacklist', [])),
                "manual_whitelist": list(self.developer_overrides.get('manual_whitelist', []))
            }
        }
        
        with open(self.patterns_file, 'w') as f:
            json.dump(enhanced_config, f, indent=2)
        print(f"📄 Created enhanced patterns file: {self.patterns_file}")
    
    def load_patterns(self):
        """Load enhanced patterns from configuration file"""
        try:
            with open(self.patterns_file, 'r') as f:
                config = json.load(f)
            
            self.exact_keywords = config.get('exact_keywords', {})
            self.entity_prefixes = config.get('entity_prefixes', [])
            self.value_patterns = config.get('value_patterns', {})
            self.exclusions = set(config.get('exclusions', []))
            self.pattern_mappings = config.get('pattern_mappings', {})
            self.value_exclusions = set(config.get('value_exclusions', []))
            self.business_value_patterns = config.get('business_value_patterns', [])
            
            # Merge any existing developer overrides from patterns file
            pattern_overrides = config.get('developer_overrides', {})
            if pattern_overrides:
                existing_blacklist = set(pattern_overrides.get('manual_blacklist', []))
                existing_whitelist = set(pattern_overrides.get('manual_whitelist', []))
                
                # Merge with loaded overrides
                self.developer_overrides['manual_blacklist'].update(existing_blacklist)
                self.developer_overrides['manual_whitelist'].update(existing_whitelist)
            
            print(f"✅ Loaded enhanced patterns from {self.patterns_file}")
            print(f"🎯 Entity prefixes: {len(self.entity_prefixes)}")
            print(f"🎯 Exact keyword categories: {len(self.exact_keywords)}")
            
            # Print stats for each category
            for category, subcategories in self.exact_keywords.items():
                total_keywords = sum(len(keywords) for keywords in subcategories.values())
                print(f"   {category.upper()}: {total_keywords} exact keywords across {len(subcategories)} subcategories")
            
        except FileNotFoundError:
            print(f"❌ Pattern file {self.patterns_file} not found. Creating enhanced default...")
            self.create_enhanced_patterns_file()
            self.load_patterns()
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing {self.patterns_file}: {e}")
            raise
    
    def compile_patterns(self):
        """Compile regex patterns for exact word matching"""
        # Compile value patterns
        for pattern_name, pattern_str in self.value_patterns.items():
            try:
                flags = re.IGNORECASE if 'Jan|Feb|Mar' in pattern_str else 0
                self.compiled_patterns[pattern_name] = re.compile(pattern_str, flags)
            except re.error as e:
                print(f"⚠️  Invalid regex pattern '{pattern_name}': {e}")
        
        # Compile exact word matching patterns for each category
        for category, subcategories in self.exact_keywords.items():
            self.compiled_exact_patterns[category] = {}
            for subcategory, keywords in subcategories.items():
                # Create word boundary regex for exact matching
                escaped_keywords = [re.escape(keyword) for keyword in keywords]
                pattern = r'\b(?:' + '|'.join(escaped_keywords) + r')\b'
                try:
                    self.compiled_exact_patterns[category][subcategory] = re.compile(pattern, re.IGNORECASE)
                except re.error as e:
                    print(f"⚠️  Invalid exact pattern for {category}.{subcategory}: {e}")
    
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
    
    def extract_entity_and_field(self, field_name: str) -> tuple:
        """
        Extract entity prefix and field name from compound fields
        Returns: (entity_prefix, field_name, is_compound)
        """
        field_lower = field_name.lower()
        
        # Check if field starts with any entity prefix
        for prefix in self.entity_prefixes:
            prefix_lower = prefix.lower()
            if field_lower.startswith(prefix_lower) and len(field_lower) > len(prefix_lower):
                # Extract the remaining part after prefix
                remaining = field_lower[len(prefix_lower):]
                # Check if remaining part starts with a capital (camelCase) or underscore
                original_remaining = field_name[len(prefix):]
                if (original_remaining and original_remaining[0].isupper()) or field_name[len(prefix):].startswith('_'):
                    clean_remaining = original_remaining.lstrip('_').lower()
                    return (prefix, clean_remaining, True)
        
        return (None, field_lower, False)
    
    def exact_keyword_match(self, field_path: str) -> List[str]:
        """Enhanced exact keyword matching with entity prefix support"""
        final_key = self.extract_final_key(field_path).lower()
        
        # Check developer overrides first
        if final_key in self.developer_overrides['manual_whitelist']:
            return []
        
        if final_key in self.developer_overrides['manual_blacklist']:
            return ['DEVELOPER_MANUAL']
        
        # Extract entity and field components
        entity_prefix, field_name, is_compound = self.extract_entity_and_field(final_key)
        
        matched_categories = []
        
        # Check exact matches for each category
        for category, subcategories in self.compiled_exact_patterns.items():
            category_matched = False
            
            for subcategory, compiled_pattern in subcategories.items():
                # Check direct field name match
                if compiled_pattern.search(field_name):
                    matched_categories.append(category.upper())
                    category_matched = True
                    print(f"🎯 EXACT MATCH: '{final_key}' -> {category.upper()} ({subcategory})")
                    if is_compound:
                        print(f"   └── Compound field: entity='{entity_prefix}' + field='{field_name}'")
                    break
            
            # If compound field and no direct match, check if entity suggests sensitivity
            if is_compound and not category_matched and entity_prefix:
                # Check if entity prefix itself indicates personal/sensitive data
                sensitive_entities = ['customer', 'person', 'user', 'subscriber', 'individual', 'profile']
                if entity_prefix.lower() in sensitive_entities:
                    # Check if the field part matches any pattern in this category
                    for subcategory, compiled_pattern in subcategories.items():
                        if compiled_pattern.search(field_name):
                            matched_categories.append(category.upper())
                            print(f"🎯 ENTITY + FIELD MATCH: '{final_key}' -> {category.upper()} (entity: {entity_prefix})")
                            break
        
        return list(set(matched_categories))
    
    def should_exclude(self, final_key: str) -> bool:
        """Check if field should be excluded from blacklist"""
        return final_key.lower() in self.exclusions
    
    def has_code_or_type_suffix(self, field_name: str) -> bool:
        """Check if field ends with 'code' or 'type' but is NOT sensitive data"""
        field_lower = field_name.lower()
        
        # Sensitive code exceptions that should NOT be excluded
        sensitive_code_exceptions = [
            'zipcode', 'postalcode', 'areacode', 'countrycode', 'regioncode',
            'securitycode', 'verificationcode', 'accesscode', 'pincode',
            'activationcode', 'confirmationcode', 'passcode', 'passwordcode',
            'authcode', 'otpcode', 'mfacode', 'twofa', 'lockcode'
        ]
        
        # If it's a sensitive code, don't exclude it
        if any(exception in field_lower for exception in sensitive_code_exceptions):
            return False
        
        # Classification suffixes that indicate non-sensitive enum/type fields
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
            
            return False
        
        # For other suffixes, apply normal logic
        for suffix in classification_suffixes[1:]:  # Skip 'code' since we handled it above
            if field_lower.endswith(suffix):
                return True
        
        return False
    
    def is_boolean_field(self, values: List[Any]) -> bool:
        """Check if field contains only boolean-type values"""
        if not values:
            return False
        
        boolean_values = {
            'true', 'false', 'yes', 'no', 'y', 'n', '1', '0',
            'on', 'off', 'enabled', 'disabled', 'active', 'inactive',
            'valid', 'invalid'
        }
        
        for value in values:
            value_str = str(value).strip().lower()
            if value_str not in boolean_values:
                return False
        
        return True
    
    def is_uuid_field(self, values: List[Any]) -> bool:
        """Check if field contains only UUID values"""
        if not values:
            return False
        
        uuid_patterns = [
            re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE),  # Standard UUID
            re.compile(r'^[0-9a-f]{32}$', re.IGNORECASE),  # UUID without dashes
            re.compile(r'^[{]?[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}[}]?$', re.IGNORECASE)  # UUID with optional braces
        ]
        
        for value in values:
            value_str = str(value).strip()
            if not any(pattern.match(value_str) for pattern in uuid_patterns):
                return False
        
        return True
    
    def has_datetime_values(self, values: List[Any]) -> bool:
        """Check if values contain date-time stamps (not just dates)"""
        if not values:
            return False
        
        datetime_patterns = [
            re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'),
            re.compile(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}'),
            re.compile(r'\d{2}/\d{2}/\d{4}\s+\d{1,2}:\d{2}'),
            re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z'),
            re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}'),
        ]
        
        unix_timestamp_patterns = [
            re.compile(r'^\d{13}$'),  # Milliseconds
            re.compile(r'^\d{16,}$'),  # Microseconds or nanoseconds
        ]
        
        for value in values[:3]:
            value_str = str(value).strip()
            
            for pattern in datetime_patterns:
                if pattern.search(value_str):
                    return True
            
            for pattern in unix_timestamp_patterns:
                if pattern.match(value_str):
                    try:
                        timestamp_val = int(value_str)
                        if 1577836800000 <= timestamp_val <= 1924991999999:
                            return True
                    except ValueError:
                        continue
        
        return False
    
    def is_personal_date_field(self, field_name: str) -> bool:
        """Check if field name indicates a personal date (like date of birth)"""
        field_lower = field_name.lower()
        
        # Extract entity and field components
        entity_prefix, clean_field, is_compound = self.extract_entity_and_field(field_lower)
        
        # Check both the full field and the clean field part
        fields_to_check = [field_lower, clean_field] if is_compound else [field_lower]
        
        personal_date_keywords = [
            'dob', 'dateofbirth', 'birthdate', 'birthday', 'bday', 'birth', 'born',
            'date_of_birth', 'birth_date', 'dateborn', 'date_born'
        ]
        
        for field_to_check in fields_to_check:
            if any(keyword in field_to_check for keyword in personal_date_keywords):
                return True
        
        return False
    
    def analyze_values(self, values: List[Any]) -> Dict[str, Any]:
        """Enhanced value analysis with pattern matching"""
        results = {
            'patterns_found': [],
            'categories': [],
            'confidence': 'Low',
            'unique_values': []
        }
        
        unique_values = list(dict.fromkeys([str(v) for v in values[:5]]))
        results['unique_values'] = unique_values
        
        for value in unique_values:
            value_str = str(value).strip()
            
            for pattern_name, compiled_pattern in self.compiled_patterns.items():
                if compiled_pattern.match(value_str):
                    # Enhanced check: Skip date patterns if they contain time
                    if pattern_name.startswith(('date_')):
                        if self.has_datetime_values([value_str]):
                            continue
                    
                    results['patterns_found'].append(pattern_name)
                    
                    if pattern_name in self.pattern_mappings:
                        results['categories'].extend(self.pattern_mappings[pattern_name])
        
        results['categories'] = list(set(results['categories']))
        results['patterns_found'] = list(set(results['patterns_found']))
        
        if results['patterns_found']:
            results['confidence'] = 'High'
        
        return results
    
    def analyze_field(self, field_path: str, values: List[Any]):
        """Enhanced field analysis with exact matching and entity prefix support"""
        final_key = self.extract_final_key(field_path)
        category = self.get_field_category(field_path)
        
        if category == 'unknown':
            return
        
        # Check developer overrides first
        if final_key in self.developer_overrides['manual_whitelist']:
            self.excluded_fields.append({
                'field_path': field_path,
                'final_key': final_key,
                'category': category,
                'reason': '👨‍💻 Developer manually excluded this field',
                'unique_values': [str(v) for v in values[:5]] if values else [],
                'match_type': 'manual_whitelist'
            })
            return
        
        # Check if developer manually added to blacklist
        developer_manual = final_key in self.developer_overrides['manual_blacklist']
        
        if developer_manual:
            print(f"🎯 Developer override: '{final_key}' manually blacklisted")
            
            analysis_result = {
                'field_path': field_path,
                'final_key': final_key,
                'category': category,
                'blacklisted': True,
                'reasons': [f"👨‍💻 Developer manually added '{final_key}' to blacklist"],
                'categories_detected': ['DEVELOPER_MANUAL'],
                'unique_values': [str(v) for v in values[:5]] if values else [],
                'confidence': 'High',
                'exact_match': True,
                'entity_prefix': None,
                'key_based': True,
                'value_based': False,
                'developer_manual': True,
                'match_type': 'exact_match'
            }
            
            if category == 'headers':
                self.headers_blacklist.add(final_key)
            elif category in ['request', 'response']:
                self.payload_blacklist.add(final_key)
            
            self.exact_match_blacklisted.append(analysis_result)
            return
        
        # Standard exclusion checks
        if self.should_exclude(final_key):
            self.excluded_fields.append({
                'field_path': field_path,
                'final_key': final_key,
                'category': category,
                'reason': 'Excluded - Common non-sensitive field',
                'unique_values': [str(v) for v in values[:5]] if values else [],
                'match_type': 'exclusion'
            })
            return
        
        if self.has_code_or_type_suffix(final_key):
            self.excluded_fields.append({
                'field_path': field_path,
                'final_key': final_key,
                'category': category,
                'reason': 'Excluded - Code/Type field (classification, not sensitive data)',
                'unique_values': [str(v) for v in values[:5]] if values else [],
                'match_type': 'exclusion'
            })
            return
        
        if self.is_boolean_field(values):
            self.excluded_fields.append({
                'field_path': field_path,
                'final_key': final_key,
                'category': category,
                'reason': 'Excluded - Boolean field (True/False values)',
                'unique_values': [str(v) for v in values[:5]] if values else [],
                'match_type': 'exclusion'
            })
            return
        
        if self.is_uuid_field(values):
            self.excluded_fields.append({
                'field_path': field_path,
                'final_key': final_key,
                'category': category,
                'reason': 'Excluded - UUID field (system identifiers)',
                'unique_values': [str(v) for v in values[:5]] if values else [],
                'match_type': 'exclusion'
            })
            return
        
        # Enhanced datetime exclusion (but not for personal dates)
        if values and self.has_datetime_values(values) and not self.is_personal_date_field(final_key):
            self.excluded_fields.append({
                'field_path': field_path,
                'final_key': final_key,
                'category': category,
                'reason': 'Excluded - Contains timestamps/datetime (not personal dates)',
                'unique_values': [str(v) for v in values[:5]] if values else [],
                'match_type': 'exclusion'
            })
            return
        
        # Initialize analysis result
        entity_prefix, clean_field, is_compound = self.extract_entity_and_field(final_key)
        
        analysis_result = {
            'field_path': field_path,
            'final_key': final_key,
            'category': category,
            'blacklisted': False,
            'reasons': [],
            'categories_detected': [],
            'unique_values': [str(v) for v in values[:5]] if values else [],
            'confidence': 'Low',
            'exact_match': None,
            'entity_prefix': entity_prefix,
            'is_compound': is_compound,
            'clean_field': clean_field,
            'key_based': False,
            'value_based': False,
            'developer_manual': False,
            'match_type': 'no_match'
        }
        
        # Enhanced exact keyword matching
        key_categories = self.exact_keyword_match(field_path)
        if key_categories:
            analysis_result['key_based'] = True
            analysis_result['categories_detected'].extend(key_categories)
            analysis_result['exact_match'] = True
            analysis_result['match_type'] = 'exact_match'
            
            if 'DEVELOPER_MANUAL' in key_categories:
                analysis_result['reasons'].append(f"👨‍💻 Developer manually added '{final_key}' to blacklist")
            else:
                if is_compound:
                    analysis_result['reasons'].append(
                        f"🎯 EXACT MATCH: '{final_key}' = entity '{entity_prefix}' + field '{clean_field}' → {', '.join(key_categories)}"
                    )
                else:
                    analysis_result['reasons'].append(
                        f"🎯 EXACT MATCH: '{final_key}' exactly matches sensitive keywords → {', '.join(key_categories)}"
                    )
        
        # Value-based analysis
        if values:
            value_analysis = self.analyze_values(values)
            analysis_result['unique_values'] = value_analysis['unique_values']
            
            if value_analysis['categories']:
                analysis_result['value_based'] = True
                analysis_result['categories_detected'].extend(value_analysis['categories'])
                analysis_result['reasons'].append(
                    f"🔍 VALUE MATCH: Values match patterns {value_analysis['patterns_found']} → {', '.join(value_analysis['categories'])}"
                )
                analysis_result['confidence'] = value_analysis['confidence']
                if not analysis_result['key_based']:
                    analysis_result['match_type'] = 'value_based'
        
        # Remove duplicates
        analysis_result['categories_detected'] = list(set(analysis_result['categories_detected']))
        
        # Determine if should be blacklisted
        analysis_result['blacklisted'] = bool(analysis_result['categories_detected'])
        
        if not analysis_result['blacklisted']:
            analysis_result['reasons'].append("❌ No exact matches or sensitive patterns detected")
            analysis_result['match_type'] = 'safe'
        
        # Add to appropriate blacklist and category
        if analysis_result['blacklisted']:
            if category == 'headers':
                self.headers_blacklist.add(final_key)
                print(f"🔒 Added '{final_key}' to headers blacklist")
            elif category in ['request', 'response']:
                self.payload_blacklist.add(final_key)
                print(f"🔒 Added '{final_key}' to payload blacklist")
            
            # Categorize by match type
            if analysis_result['key_based']:
                self.exact_match_blacklisted.append(analysis_result)
            else:
                self.value_based_blacklisted.append(analysis_result)
        else:
            self.safe_fields.append(analysis_result)
    
    def generate_properties(self, output_file: str = 'enhanced_application.properties'):
        """Generate enhanced application.properties file with exact matches only"""
        # Only include exact matches in the final configuration
        exact_match_payload = set()
        exact_match_headers = set()
        
        for result in self.exact_match_blacklisted:
            final_key = result['final_key']
            if result['category'] == 'headers':
                exact_match_headers.add(final_key)
            elif result['category'] in ['request', 'response']:
                exact_match_payload.add(final_key)
        
        content = f"""# Enhanced Telecom API Blacklist Configuration - EXACT MATCHING ONLY
# Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Pattern source: {self.patterns_file}
# Total fields analyzed: {len(self.exact_match_blacklisted) + len(self.value_based_blacklisted) + len(self.safe_fields)}
# Exact match fields blacklisted: {len(self.exact_match_blacklisted)}
# Value-based fields found: {len(self.value_based_blacklisted)}
# Safe fields: {len(self.safe_fields)}
# Smart exclusions: {len(self.excluded_fields)}

# 🎯 CONFIGURATION INCLUDES EXACT MATCHES ONLY
# ✅ Exact string matching (whole word boundaries) - NO FALSE POSITIVES
# ✅ Entity prefix detection (customerAge, personName, userEmail, etc.)
# ✅ Developer manual overrides
# ❌ Value-based matches excluded from final config (require manual review)

# EXACT MATCH BLACKLISTS ONLY
payload.blacklist={','.join(sorted(exact_match_payload))}
headers.blacklist={','.join(sorted(exact_match_headers))}
"""
        
        with open(output_file, 'w') as f:
            f.write(content)
        
        print(f"📄 Enhanced properties file generated: {output_file}")
        print(f"📊 Exact matches only: {len(exact_match_payload)} payload + {len(exact_match_headers)} headers")
        return output_file
    
    def save_developer_overrides(self, output_file: str = None):
        """Save current developer overrides to JSON file"""
        if output_file is None:
            output_file = self.developer_overrides_file
        
        overrides_data = {
            "manual_blacklist": list(self.developer_overrides['manual_blacklist']),
            "manual_whitelist": list(self.developer_overrides['manual_whitelist']),
            "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "description": "Developer overrides for blacklist generation"
        }
        
        with open(output_file, 'w') as f:
            json.dump(overrides_data, f, indent=2)
        
        print(f"💾 Developer overrides saved to: {output_file}")
        return output_file
    
    def generate_interactive_html_report(self, output_file: str = 'interactive_blacklist_report.html'):
        """Generate interactive HTML report with tabbed interface and Add/Remove buttons"""
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Enhanced Telecom API Blacklist Analysis - Developer Interface</title>
    <style>
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            line-height: 1.6; 
            background-color: #f5f7fa;
        }}
        .container {{ 
            max-width: 1600px; 
            margin: 0 auto; 
            background: white; 
            min-height: 100vh;
        }}
        .header {{ 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            padding: 30px; 
            text-align: center;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header h1 {{ margin: 0; font-size: 2.2em; }}
        .header h2 {{ margin: 10px 0 0 0; font-size: 1.3em; opacity: 0.9; }}
        
        .stats-bar {{
            background: #2c3e50;
            color: white;
            padding: 15px 30px;
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
            gap: 20px;
        }}
        .stat-item {{
            text-align: center;
            min-width: 120px;
        }}
        .stat-number {{ 
            font-size: 1.8em; 
            font-weight: bold; 
            color: #3498db;
        }}
        .stat-label {{ 
            font-size: 0.9em; 
            opacity: 0.8;
        }}
        
        .tab-container {{
            background: #ecf0f1;
            padding: 0;
        }}
        .tabs {{
            display: flex;
            background: #34495e;
            margin: 0;
            padding: 0;
            list-style: none;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .tab {{
            flex: 1;
            text-align: center;
        }}
        .tab button {{
            width: 100%;
            padding: 20px 15px;
            background: transparent;
            border: none;
            color: #bdc3c7;
            font-size: 1.1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            border-bottom: 3px solid transparent;
        }}
        .tab button:hover {{
            background: #2c3e50;
            color: white;
        }}
        .tab button.active {{
            background: #3498db;
            color: white;
            border-bottom-color: #e74c3c;
        }}
        
        .tab-content {{
            display: none;
            padding: 30px;
            min-height: 600px;
        }}
        .tab-content.active {{
            display: block;
        }}
        
        .section-header {{
            background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
            color: white;
            padding: 20px;
            margin: -30px -30px 30px -30px;
            text-align: center;
            font-size: 1.4em;
            font-weight: bold;
        }}
        .section-header.value-based {{
            background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%);
        }}
        .section-header.excluded {{
            background: linear-gradient(135deg, #27ae60 0%, #229954 100%);
        }}
        .section-header.safe {{
            background: linear-gradient(135deg, #16a085 0%, #138d75 100%);
        }}
        
        table {{ 
            width: 100%; 
            border-collapse: collapse; 
            margin: 20px 0; 
            background: white;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }}
        th {{ 
            background: #34495e;
            color: white; 
            padding: 15px 12px; 
            text-align: left; 
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        td {{ 
            padding: 12px; 
            border-bottom: 1px solid #ecf0f1; 
            vertical-align: top;
        }}
        tr:hover {{ 
            background-color: #f8f9fa; 
        }}
        
        .field-info {{
            display: flex;
            flex-direction: column;
            gap: 5px;
        }}
        .field-name {{ 
            font-weight: bold; 
            color: #2c3e50;
            font-size: 1.1em;
        }}
        .field-path {{ 
            font-family: 'Courier New', monospace; 
            background: #ecf0f1; 
            padding: 4px 8px; 
            border-radius: 4px;
            font-size: 0.85em;
            color: #7f8c8d;
        }}
        .field-category {{
            font-size: 0.8em;
            padding: 2px 8px;
            border-radius: 12px;
            font-weight: 500;
            display: inline-block;
            margin-top: 3px;
        }}
        .field-category.headers {{ background: #e8f5e9; color: #2e7d32; }}
        .field-category.request {{ background: #e3f2fd; color: #1565c0; }}
        .field-category.response {{ background: #fce4ec; color: #c2185b; }}
        
        .match-indicators {{
            display: flex;
            gap: 5px;
            flex-wrap: wrap;
            margin-top: 5px;
        }}
        .exact-match-indicator {{ 
            background: #27ae60; 
            color: white; 
            padding: 2px 6px; 
            border-radius: 12px; 
            font-size: 0.7em; 
            font-weight: bold;
        }}
        .compound-indicator {{ 
            background: #f39c12; 
            color: white; 
            padding: 2px 6px; 
            border-radius: 12px; 
            font-size: 0.7em; 
            font-weight: bold;
        }}
        .value-match-indicator {{ 
            background: #3498db; 
            color: white; 
            padding: 2px 6px; 
            border-radius: 12px; 
            font-size: 0.7em; 
            font-weight: bold;
        }}
        
        .entity-info {{ 
            background: #fff3e0; 
            padding: 8px; 
            border-radius: 4px; 
            margin-top: 5px;
            font-size: 0.9em;
            color: #e65100;
            border-left: 3px solid #ff9800;
        }}
        
        .sample-values {{
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
            background: #f8f9fa;
            padding: 8px;
            border-radius: 4px;
            max-height: 80px;
            overflow-y: auto;
        }}
        .sample-values .value {{
            display: block;
            padding: 2px 0;
            color: #495057;
        }}
        
        .category-tags {{
            display: flex;
            gap: 5px;
            flex-wrap: wrap;
        }}
        .category-tag {{ 
            background: #e9ecef; 
            color: #495057; 
            padding: 3px 8px; 
            border-radius: 12px; 
            font-size: 0.8em; 
            font-weight: 500;
        }}
        .category-tag.spi {{ background: #ffebee; color: #c62828; }}
        .category-tag.cpni {{ background: #fff3e0; color: #ef6c00; }}
        .category-tag.rpi {{ background: #f3e5f5; color: #7b1fa2; }}
        .category-tag.cso {{ background: #e8f5e9; color: #2e7d32; }}
        .category-tag.pci {{ background: #ffebee; color: #c62828; }}
        
        .action-column {{
            text-align: center;
            min-width: 120px;
        }}
        .btn {{
            padding: 8px 16px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: 600;
            font-size: 0.9em;
            transition: all 0.3s ease;
            margin: 2px;
        }}
        .btn-remove {{
            background: #e74c3c;
            color: white;
        }}
        .btn-remove:hover {{
            background: #c0392b;
            transform: translateY(-1px);
        }}
        .btn-add {{
            background: #27ae60;
            color: white;
        }}
        .btn-add:hover {{
            background: #229954;
            transform: translateY(-1px);
        }}
        
        .download-section {{
            background: #2c3e50;
            color: white;
            padding: 30px;
            margin: 30px -30px -30px -30px;
            text-align: center;
        }}
        .btn-download {{
            background: #3498db;
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 5px;
            font-size: 1.1em;
            font-weight: 600;
            cursor: pointer;
            margin: 10px;
            transition: all 0.3s ease;
        }}
        .btn-download:hover {{
            background: #2980b9;
            transform: translateY(-2px);
        }}
        
        .config-output {{
            background: #2c3e50;
            color: #ecf0f1;
            padding: 20px;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            white-space: pre-wrap;
            margin: 20px 0;
            font-size: 0.9em;
            line-height: 1.4;
        }}
        
        .search-box {{
            width: 100%;
            padding: 12px;
            margin: 20px 0;
            border: 2px solid #bdc3c7;
            border-radius: 5px;
            font-size: 1em;
        }}
        .search-box:focus {{
            outline: none;
            border-color: #3498db;
        }}
        
        .table-container {{
            max-height: 70vh;
            overflow-y: auto;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin: 20px 0;
        }}
        
        .alert {{
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
            border-left: 4px solid;
        }}
        .alert-info {{
            background: #d1ecf1;
            border-color: #17a2b8;
            color: #0c5460;
        }}
        .alert-warning {{
            background: #fff3cd;
            border-color: #ffc107;
            color: #856404;
        }}
        
        @media (max-width: 768px) {{
            .stats-bar {{
                flex-direction: column;
                text-align: center;
            }}
            .tabs {{
                flex-direction: column;
            }}
            .tab-content {{
                padding: 15px;
            }}
            table {{
                font-size: 0.8em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Enhanced Telecom API Blacklist Analysis</h1>
            <h2>Developer-Friendly Interface with Dynamic Field Management</h2>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <div class="stats-bar">
            <div class="stat-item">
                <div class="stat-number">{len(self.exact_match_blacklisted)}</div>
                <div class="stat-label">Exact Match</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{len(self.value_based_blacklisted)}</div>
                <div class="stat-label">Value-Based</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{len(self.excluded_fields)}</div>
                <div class="stat-label">Smart Exclusions</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{len(self.safe_fields)}</div>
                <div class="stat-label">Safe Fields</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{len(self.exact_match_blacklisted) + len(self.value_based_blacklisted) + len(self.excluded_fields) + len(self.safe_fields)}</div>
                <div class="stat-label">Total Fields</div>
            </div>
        </div>

        <div class="tab-container">
            <ul class="tabs">
                <li class="tab">
                    <button class="tab-button active" onclick="openTab(event, 'exact-match')">
                        🎯 Exact Match Blacklisted ({len(self.exact_match_blacklisted)})
                    </button>
                </li>
                <li class="tab">
                    <button class="tab-button" onclick="openTab(event, 'value-based')">
                        🔍 Value-Based Matches ({len(self.value_based_blacklisted)})
                    </button>
                </li>
                <li class="tab">
                    <button class="tab-button" onclick="openTab(event, 'excluded')">
                        ✅ Smart Exclusions ({len(self.excluded_fields)})
                    </button>
                </li>
                <li class="tab">
                    <button class="tab-button" onclick="openTab(event, 'safe')">
                        🛡️ Safe Fields ({len(self.safe_fields)})
                    </button>
                </li>
            </ul>

            <!-- Exact Match Blacklisted Tab -->
            <div id="exact-match" class="tab-content active">
                <div class="section-header">
                    🎯 Exact Match Blacklisted Fields
                    <div style="font-size: 0.8em; margin-top: 5px; opacity: 0.9;">
                        These fields matched exact keywords and are included in the final configuration
                    </div>
                </div>
                
                <input type="text" class="search-box" placeholder="🔍 Search exact match fields..." 
                       onkeyup="filterTable('exact-match-table', this.value)">
                
                <div class="table-container">
                    <table id="exact-match-table">
                        <thead>
                            <tr>
                                <th>Field Information</th>
                                <th>Match Details</th>
                                <th>Sample Values</th>
                                <th>Categories</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>"""

        # Generate Exact Match table rows
        for result in self.exact_match_blacklisted:
            field_name = result['final_key']
            field_path = result['field_path']
            category = result['category']
            
            # Field Information column
            field_info = f"""
                <div class="field-info">
                    <div class="field-name">{field_name}</div>
                    <div class="field-path">{field_path}</div>
                    <div class="field-category {category}">{category.upper()}</div>
                    <div class="match-indicators">
                        <span class="exact-match-indicator">EXACT MATCH</span>"""
            
            if result.get('is_compound'):
                field_info += f'<span class="compound-indicator">COMPOUND</span>'
            
            field_info += '</div>'
            
            if result.get('is_compound'):
                field_info += f"""
                    <div class="entity-info">
                        Entity: <strong>{result.get('entity_prefix', 'N/A')}</strong> + 
                        Field: <strong>{result.get('clean_field', 'N/A')}</strong>
                    </div>"""
            
            field_info += '</div>'
            
            # Match Details column
            match_details = '<br>'.join(result['reasons'])
            
            # Sample Values column
            sample_values = ''
            if result['unique_values']:
                sample_values = '<div class="sample-values">'
                for value in result['unique_values']:
                    sample_values += f'<span class="value">{value}</span>'
                sample_values += '</div>'
            
            # Categories column
            categories = ''
            if result['categories_detected']:
                categories = '<div class="category-tags">'
                for cat in result['categories_detected']:
                    if cat != 'DEVELOPER_MANUAL':
                        categories += f'<span class="category-tag {cat.lower()}">{cat}</span>'
                categories += '</div>'
            
            html_content += f"""
                            <tr data-field="{field_name}" data-category="{category}">
                                <td>{field_info}</td>
                                <td>{match_details}</td>
                                <td>{sample_values}</td>
                                <td>{categories}</td>
                                <td class="action-column">
                                    <button class="btn btn-remove" onclick="removeField('{field_name}', '{category}')">
                                        🗑️ Remove
                                    </button>
                                </td>
                            </tr>"""

        html_content += """
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Value-Based Matches Tab -->
            <div id="value-based" class="tab-content">
                <div class="section-header value-based">
                    🔍 Value-Based Matches
                    <div style="font-size: 0.8em; margin-top: 5px; opacity: 0.9;">
                        These fields matched value patterns but require manual review before adding to configuration
                    </div>
                </div>
                
                <input type="text" class="search-box" placeholder="🔍 Search value-based fields..." 
                       onkeyup="filterTable('value-based-table', this.value)">
                
                <div class="table-container">
                    <table id="value-based-table">
                        <thead>
                            <tr>
                                <th>Field Information</th>
                                <th>Match Details</th>
                                <th>Sample Values</th>
                                <th>Categories</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>"""

        # Generate Value-Based table rows
        for result in self.value_based_blacklisted:
            field_name = result['final_key']
            field_path = result['field_path']
            category = result['category']
            
            # Field Information column
            field_info = f"""
                <div class="field-info">
                    <div class="field-name">{field_name}</div>
                    <div class="field-path">{field_path}</div>
                    <div class="field-category {category}">{category.upper()}</div>
                    <div class="match-indicators">
                        <span class="value-match-indicator">VALUE MATCH</span>
                    </div>
                </div>"""
            
            # Match Details column
            match_details = '<br>'.join(result['reasons'])
            
            # Sample Values column
            sample_values = ''
            if result['unique_values']:
                sample_values = '<div class="sample-values">'
                for value in result['unique_values']:
                    sample_values += f'<span class="value">{value}</span>'
                sample_values += '</div>'
            
            # Categories column
            categories = ''
            if result['categories_detected']:
                categories = '<div class="category-tags">'
                for cat in result['categories_detected']:
                    categories += f'<span class="category-tag {cat.lower()}">{cat}</span>'
                categories += '</div>'
            
            html_content += f"""
                            <tr data-field="{field_name}" data-category="{category}">
                                <td>{field_info}</td>
                                <td>{match_details}</td>
                                <td>{sample_values}</td>
                                <td>{categories}</td>
                                <td class="action-column">
                                    <button class="btn btn-add" onclick="addField('{field_name}', '{category}')">
                                        ➕ Add
                                    </button>
                                </td>
                            </tr>"""

        html_content += """
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Smart Exclusions Tab -->
            <div id="excluded" class="tab-content">
                <div class="section-header excluded">
                    ✅ Smart Exclusions Applied
                    <div style="font-size: 0.8em; margin-top: 5px; opacity: 0.9;">
                        These fields were automatically excluded by smart logic
                    </div>
                </div>
                
                <input type="text" class="search-box" placeholder="🔍 Search excluded fields..." 
                       onkeyup="filterTable('excluded-table', this.value)">
                
                <div class="table-container">
                    <table id="excluded-table">
                        <thead>
                            <tr>
                                <th>Field Information</th>
                                <th>Exclusion Reason</th>
                                <th>Sample Values</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>"""

        # Generate Excluded fields table rows
        for exclusion in self.excluded_fields:
            field_name = exclusion['final_key']
            field_path = exclusion['field_path']
            category = exclusion.get('category', 'unknown')
            
            # Field Information column
            field_info = f"""
                <div class="field-info">
                    <div class="field-name">{field_name}</div>
                    <div class="field-path">{field_path}</div>
                    <div class="field-category {category}">{category.upper()}</div>
                </div>"""
            
            # Sample Values column
            sample_values = ''
            if exclusion.get('unique_values'):
                sample_values = '<div class="sample-values">'
                for value in exclusion['unique_values']:
                    sample_values += f'<span class="value">{value}</span>'
                sample_values += '</div>'
            
            html_content += f"""
                            <tr data-field="{field_name}" data-category="{category}">
                                <td>{field_info}</td>
                                <td>{exclusion['reason']}</td>
                                <td>{sample_values}</td>
                                <td class="action-column">
                                    <button class="btn btn-add" onclick="addField('{field_name}', '{category}')">
                                        ➕ Add
                                    </button>
                                </td>
                            </tr>"""

        html_content += """
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Safe Fields Tab -->
            <div id="safe" class="tab-content">
                <div class="section-header safe">
                    🛡️ Safe Fields
                    <div style="font-size: 0.8em; margin-top: 5px; opacity: 0.9;">
                        These fields showed no sensitive patterns and are considered safe
                    </div>
                </div>
                
                <input type="text" class="search-box" placeholder="🔍 Search safe fields..." 
                       onkeyup="filterTable('safe-table', this.value)">
                
                <div class="table-container">
                    <table id="safe-table">
                        <thead>
                            <tr>
                                <th>Field Information</th>
                                <th>Analysis Result</th>
                                <th>Sample Values</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>"""

        # Generate Safe fields table rows (show first 50 for performance)
        for result in self.safe_fields[:50]:
            field_name = result['final_key']
            field_path = result['field_path']
            category = result['category']
            
            # Field Information column
            field_info = f"""
                <div class="field-info">
                    <div class="field-name">{field_name}</div>
                    <div class="field-path">{field_path}</div>
                    <div class="field-category {category}">{category.upper()}</div>
                </div>"""
            
            # Analysis Result column
            analysis_result = result['reasons'][0] if result['reasons'] else 'No sensitive patterns detected'
            
            # Sample Values column
            sample_values = ''
            if result['unique_values']:
                sample_values = '<div class="sample-values">'
                for value in result['unique_values']:
                    sample_values += f'<span class="value">{value}</span>'
                sample_values += '</div>'
            
            html_content += f"""
                            <tr data-field="{field_name}" data-category="{category}">
                                <td>{field_info}</td>
                                <td>{analysis_result}</td>
                                <td>{sample_values}</td>
                                <td class="action-column">
                                    <button class="btn btn-add" onclick="addField('{field_name}', '{category}')">
                                        ➕ Add
                                    </button>
                                </td>
                            </tr>"""

        if len(self.safe_fields) > 50:
            html_content += f"""
                            <tr>
                                <td colspan="4" style="text-align: center; font-style: italic; color: #666; padding: 20px;">
                                    ... and {len(self.safe_fields) - 50} more safe fields
                                </td>
                            </tr>"""

        # Generate exact match payload and headers for config
        exact_match_payload = []
        exact_match_headers = []
        
        for result in self.exact_match_blacklisted:
            final_key = result['final_key']
            if result['category'] == 'headers':
                exact_match_headers.append(final_key)
            elif result['category'] in ['request', 'response']:
                exact_match_payload.append(final_key)

        html_content += f"""
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <div class="download-section">
            <h3>📄 Configuration & Downloads</h3>
            
            <div class="alert alert-info">
                <strong>Configuration Policy:</strong> Only exact match fields are included in the final configuration to prevent false positives. 
                Value-based matches require manual review and can be added using the Add button.
            </div>
            
            <div class="config-output">
# EXACT MATCH BLACKLISTS ONLY - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
payload.blacklist={','.join(sorted(exact_match_payload))}
headers.blacklist={','.join(sorted(exact_match_headers))}
            </div>
            
            <button class="btn-download" onclick="downloadConfig()">
                📋 Download Configuration (.properties)
            </button>
            <button class="btn-download" onclick="downloadOverrides()">
                ⚙️ Download Developer Overrides (.json)
            </button>
            <button class="btn-download" onclick="downloadReport()">
                📊 Download Full Report (.html)
            </button>
        </div>
    </div>

    <script>
        // Developer overrides data
        let developerOverrides = {{
            manual_blacklist: [],
            manual_whitelist: []
        }};

        // Current configuration data
        let exactMatchPayload = {json.dumps(sorted(exact_match_payload))};
        let exactMatchHeaders = {json.dumps(sorted(exact_match_headers))};

        function openTab(evt, tabName) {{
            var i, tabcontent, tabbuttons;
            
            // Hide all tab contents
            tabcontent = document.getElementsByClassName("tab-content");
            for (i = 0; i < tabcontent.length; i++) {{
                tabcontent[i].classList.remove("active");
            }}
            
            // Remove active class from all tab buttons
            tabbuttons = document.getElementsByClassName("tab-button");
            for (i = 0; i < tabbuttons.length; i++) {{
                tabbuttons[i].classList.remove("active");
            }}
            
            // Show the selected tab and mark button as active
            document.getElementById(tabName).classList.add("active");
            evt.currentTarget.classList.add("active");
        }}

        function filterTable(tableId, searchValue) {{
            const table = document.getElementById(tableId);
            const rows = table.getElementsByTagName("tr");
            const searchLower = searchValue.toLowerCase();
            
            for (let i = 1; i < rows.length; i++) {{ // Skip header row
                const row = rows[i];
                const cells = row.getElementsByTagName("td");
                let found = false;
                
                for (let j = 0; j < cells.length; j++) {{
                    if (cells[j].textContent.toLowerCase().includes(searchLower)) {{
                        found = true;
                        break;
                    }}
                }}
                
                row.style.display = found ? "" : "none";
            }}
        }}

        function removeField(fieldName, category) {{
            if (confirm(`Remove "${{fieldName}}" from blacklist?`)) {{
                // Add to manual whitelist
                if (!developerOverrides.manual_whitelist.includes(fieldName)) {{
                    developerOverrides.manual_whitelist.push(fieldName);
                }}
                
                // Remove from manual blacklist if present
                const blacklistIndex = developerOverrides.manual_blacklist.indexOf(fieldName);
                if (blacklistIndex > -1) {{
                    developerOverrides.manual_blacklist.splice(blacklistIndex, 1);
                }}
                
                // Remove from current configuration
                if (category === 'headers') {{
                    const index = exactMatchHeaders.indexOf(fieldName);
                    if (index > -1) exactMatchHeaders.splice(index, 1);
                }} else {{
                    const index = exactMatchPayload.indexOf(fieldName);
                    if (index > -1) exactMatchPayload.splice(index, 1);
                }}
                
                // Update UI
                updateConfigDisplay();
                updateOverridesDisplay();
                
                // Hide the row or move it to another tab
                const row = document.querySelector(`tr[data-field="${{fieldName}}"]`);
                if (row) {{
                    row.style.background = '#ffebee';
                    row.style.opacity = '0.6';
                    setTimeout(() => row.style.display = 'none', 1000);
                }}
                
                alert(`"${{fieldName}}" removed from blacklist and added to developer whitelist.`);
            }}
        }}

        function addField(fieldName, category) {{
            if (confirm(`Add "${{fieldName}}" to blacklist?`)) {{
                // Add to manual blacklist
                if (!developerOverrides.manual_blacklist.includes(fieldName)) {{
                    developerOverrides.manual_blacklist.push(fieldName);
                }}
                
                // Remove from manual whitelist if present
                const whitelistIndex = developerOverrides.manual_whitelist.indexOf(fieldName);
                if (whitelistIndex > -1) {{
                    developerOverrides.manual_whitelist.splice(whitelistIndex, 1);
                }}
                
                // Add to current configuration
                if (category === 'headers') {{
                    if (!exactMatchHeaders.includes(fieldName)) {{
                        exactMatchHeaders.push(fieldName);
                        exactMatchHeaders.sort();
                    }}
                }} else {{
                    if (!exactMatchPayload.includes(fieldName)) {{
                        exactMatchPayload.push(fieldName);
                        exactMatchPayload.sort();
                    }}
                }}
                
                // Update UI
                updateConfigDisplay();
                updateOverridesDisplay();
                
                // Highlight the row
                const row = document.querySelector(`tr[data-field="${{fieldName}}"]`);
                if (row) {{
                    row.style.background = '#e8f5e9';
                    row.style.opacity = '0.6';
                    setTimeout(() => row.style.display = 'none', 1000);
                }}
                
                alert(`"${{fieldName}}" added to blacklist and developer overrides.`);
            }}
        }}

        function updateConfigDisplay() {{
            const configElement = document.querySelector('.config-output');
            const now = new Date().toISOString().slice(0, 19).replace('T', ' ');
            configElement.textContent = `# EXACT MATCH BLACKLISTS ONLY - ${{now}}
payload.blacklist=${{exactMatchPayload.join(',')}}
headers.blacklist=${{exactMatchHeaders.join(',')}}`;
        }}

        function updateOverridesDisplay() {{
            // Update stats if needed
            console.log('Developer Overrides Updated:', developerOverrides);
        }}

        function downloadConfig() {{
            const configContent = document.querySelector('.config-output').textContent;
            const blob = new Blob([configContent], {{ type: 'text/plain' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'enhanced_application.properties';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }}

        function downloadOverrides() {{
            const overridesData = {{
                ...developerOverrides,
                last_updated: new Date().toISOString().slice(0, 19).replace('T', ' '),
                description: "Developer overrides for blacklist generation"
            }};
            
            const blob = new Blob([JSON.stringify(overridesData, null, 2)], {{ type: 'application/json' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'developer_overrides.json';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }}

        function downloadReport() {{
            const blob = new Blob([document.documentElement.outerHTML], {{ type: 'text/html' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'interactive_blacklist_report.html';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }}

        // Initialize page
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('Interactive Blacklist Report Loaded');
            console.log('Exact Match Fields:', exactMatchPayload.length + exactMatchHeaders.length);
        }});
    </script>
</body>
</html>
"""

        with open(output_file, 'w') as f:
            f.write(html_content)
        
        print(f"📄 Interactive HTML report generated: {output_file}")
        return output_file
    
    def print_enhanced_summary(self):
        """Print enhanced console summary"""
        total_fields = len(self.exact_match_blacklisted) + len(self.value_based_blacklisted) + len(self.safe_fields)
        
        print("\n" + "="*80)
        print("        ENHANCED BLACKLIST ANALYSIS - DEVELOPER INTERFACE")
        print("="*80)
        print(f"🎯 Matching Type: EXACT STRING MATCHING + VALUE PATTERNS")
        print(f"🏢 Entity Prefixes: {len(self.entity_prefixes)} configured")
        print(f"📊 Total fields analyzed: {total_fields}")
        
        print(f"\n📂 FIELD CATEGORIZATION:")
        print(f"   🎯 Exact match blacklisted: {len(self.exact_match_blacklisted)}")
        print(f"   🔍 Value-based matches: {len(self.value_based_blacklisted)}")
        print(f"   ✅ Smart exclusions: {len(self.excluded_fields)}")
        print(f"   🛡️ Safe fields: {len(self.safe_fields)}")
        
        # Calculate final configuration counts
        exact_payload = len([r for r in self.exact_match_blacklisted if r['category'] in ['request', 'response']])
        exact_headers = len([r for r in self.exact_match_blacklisted if r['category'] == 'headers'])
        
        print(f"\n📋 FINAL CONFIGURATION (Exact Matches Only):")
        print(f"   payload.blacklist: {exact_payload} fields")
        print(f"   headers.blacklist: {exact_headers} fields")
        
        print(f"\n💾 DEVELOPER OVERRIDES:")
        print(f"   Manual blacklist: {len(self.developer_overrides['manual_blacklist'])} fields")
        print(f"   Manual whitelist: {len(self.developer_overrides['manual_whitelist'])} fields")
        
        print(f"\n🎯 Key Features:")
        print(f"   ✅ Tabbed interface for easy field review")
        print(f"   ✅ Add/Remove buttons for dynamic management")
        print(f"   ✅ Downloadable developer overrides")
        print(f"   ✅ Search functionality for large field sets")
        print(f"   ✅ Exact matches only in final configuration")
        print(f"   ✅ Value-based matches require manual review")
    
    def analyze_data(self, data_file: str):
        """Analyze the extracted data with enhanced exact matching"""
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        # Analyze each field in the data
        for item in data.get('data', []):
            for field_path, values in item.items():
                if field_path == 'curl':  # Skip curl commands
                    continue
                self.analyze_field(field_path, values)
        
        return {
            'total_fields': len(self.exact_match_blacklisted) + len(self.value_based_blacklisted) + len(self.safe_fields),
            'exact_match_blacklisted': len(self.exact_match_blacklisted),
            'value_based_blacklisted': len(self.value_based_blacklisted),
            'excluded_fields': len(self.excluded_fields),
            'safe_fields': len(self.safe_fields)
        }

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python enhanced_blacklist_generator.py <postman_extraction_results.json> [enhanced_patterns_config.json]")
        print("Example: python enhanced_blacklist_generator.py data.json enhanced_patterns_config.json")
        return
    
    data_file = sys.argv[1]
    patterns_file = sys.argv[2] if len(sys.argv) > 2 else 'enhanced_patterns_config.json'
    
    if not os.path.exists(data_file):
        print(f"❌ Data file {data_file} not found")
        return
    
    print("🚀 Starting ENHANCED blacklist analysis with Developer Interface...")
    print("🎯 NEW: Developer-friendly tabbed interface")
    print("🔧 NEW: Dynamic Add/Remove field management")
    print("💾 NEW: Downloadable developer overrides")
    print("🔍 NEW: Search and filter capabilities")
    print(f"📄 Data source: {data_file}")
    print(f"⚙️  Enhanced patterns: {patterns_file}")
    
    try:
        generator = EnhancedTelecomBlacklistGenerator(patterns_file)
        
        # Analyze the data
        summary = generator.analyze_data(data_file)
        
        # Generate outputs
        properties_file = generator.generate_properties()
        html_report = generator.generate_interactive_html_report()
        overrides_file = generator.save_developer_overrides()
        
        # Print console summary
        generator.print_enhanced_summary()
        
        print(f"\n📄 Generated files:")
        print(f"   📋 Enhanced properties: {properties_file}")
        print(f"   🎯 Interactive HTML report: {html_report}")
        print(f"   💾 Developer overrides: {overrides_file}")
        print(f"   ⚙️  Enhanced patterns config: {patterns_file}")
        
        print(f"\n✅ Enhanced analysis complete with Developer Interface!")
        print(f"🎯 Key Features:")
        print(f"   • Interactive tabbed interface for easy field review")
        print(f"   • Dynamic Add/Remove buttons for field management")
        print(f"   • Downloadable developer overrides JSON")
        print(f"   • Search and filter functionality")
        print(f"   • Exact matches only in final configuration")
        print(f"   • Value-based matches require manual review")
        print(f"   • Automatic override loading on subsequent runs")
        
        print(f"\n📖 Results Summary:")
        print(f"   📊 Total fields: {summary['total_fields']}")
        print(f"   🎯 Exact match blacklisted: {summary['exact_match_blacklisted']}")
        print(f"   🔍 Value-based matches: {summary['value_based_blacklisted']}")
        print(f"   ✅ Smart exclusions: {summary['excluded_fields']}")
        print(f"   🛡️ Safe fields: {summary['safe_fields']}")
        
        print(f"\n🔧 How to use the Developer Interface:")
        print(f"   1. Open {html_report} in your browser")
        print(f"   2. Review exact match fields in the first tab")
        print(f"   3. Use Remove button to exclude false positives")
        print(f"   4. Review value-based matches and add legitimate fields")
        print(f"   5. Download developer overrides to persist changes")
        print(f"   6. Re-run this script to apply overrides automatically")
        
    except Exception as e:
        print(f"❌ Error during enhanced analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()