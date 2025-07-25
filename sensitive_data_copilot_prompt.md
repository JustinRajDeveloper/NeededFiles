# Copilot Prompt: Sensitive Data Detection and Masking

## Task Overview
Analyze the provided cURL command and its expected response to identify fields containing sensitive data that need to be masked according to SPI, CPNI, RPI, CSO, and PCI compliance requirements.

## Instructions
When given a cURL command, analyze both the request payload and expected response to identify sensitive fields. Use the classification system below to minimize false positives while ensuring comprehensive coverage.

## Field Classification System

### SAFE PATTERNS (Never Flag - Whitelist)
These patterns should NEVER be flagged as sensitive, even if they contain keywords like "id" or "name":

**Technical/System Fields:**
```
- request_id, session_id, transaction_id, correlation_id, trace_id
- message_id, order_id, product_id, category_id, sku_id
- organization_id, company_id, department_id, role_id, team_id
- system_id, application_id, service_id, component_id, module_id
- database_id, table_id, record_id, entity_id
- filename, username, hostname, domain_name, class_name
- method_name, function_name, server_name, service_name
- api_version, schema_version, format_type
```

### HIGH SENSITIVITY (Always Flag - Immediate Masking Required)

**1. SPI (Sensitive Personal Information)**
```
Fields matching these patterns:
- ssn, social_security_number, tax_id, taxpayer_id
- passport_number, passport_id, visa_number
- driver_license, drivers_license, dl_number, license_number
- national_id, citizen_id, government_id
- personal_id, individual_id, identity_number
- first_name, last_name, full_name, given_name, family_name
- middle_name, legal_name, birth_name, maiden_name
- date_of_birth, dob, birth_date, birthday
- personal_email, private_email, home_email
```

**2. CPNI (Customer Proprietary Network Information)**
```
Fields matching these patterns:
- account_balance, balance_due, outstanding_balance
- billing_amount, payment_amount, monthly_charges
- lines_on_account, number_of_lines, line_count
- usage_details, call_records, data_usage
- service_address, installation_address, service_location
- account_number, customer_account, billing_account
- phone_number, mobile_number, telephone, contact_number
- home_phone, work_phone, cell_phone, primary_phone
```

**3. RPI (Regulated Personal Information)**
```
Fields matching these patterns:
- geolocation, gps_coordinates, latitude, longitude
- location_data, position_data, tracking_data
- ip_address, mac_address, device_id, imei
- biometric_data, fingerprint, facial_recognition
- health_records, medical_data, diagnosis, prescription
- background_check, criminal_history, court_records
```

**4. CSO (Customer Security Operations)**
```
Fields matching these patterns:
- password, pwd, passcode, pin, security_code
- secret, api_key, auth_token, access_token, refresh_token
- private_key, public_key, certificate, encryption_key
- otp, one_time_password, verification_code, auth_code
- security_question, security_answer, challenge_response
- mechid_password, service_password, system_password
```

**5. PCI (Payment Card Industry)**
```
Fields matching these patterns:
- credit_card, card_number, cc_number, pan, primary_account_number
- debit_card, payment_card, card_details
- cvv, cvc, cid, security_code, card_code, verification_code
- expiry_date, exp_date, expiration_date, valid_thru
- cardholder_name, name_on_card, billing_name
- routing_number, account_number, bank_account, iban, swift_code
```

### MEDIUM SENSITIVITY (Context-Dependent - Analyze Before Flagging)

**Customer/User Identifiers (Flag only if linked to personal data):**
```
- user_id, customer_id (only if in personal context)
- email, email_address (only if personal/private)
- address, street_address, mailing_address (only if residential)
- age, gender, marital_status (only in personal context)
```

## Analysis Process

### Step 1: Parse the cURL Command
1. Extract the request URL and identify the API endpoint
2. Parse request headers for sensitive data
3. Parse request body/payload for field names and values
4. Identify the expected response structure

### Step 2: Apply Whitelist Filter
1. Check each field against SAFE PATTERNS first
2. If field matches safe pattern, mark as SAFE and skip further analysis
3. Document why certain fields are considered safe

### Step 3: Apply Sensitivity Classification
1. Check remaining fields against HIGH SENSITIVITY patterns
2. For MEDIUM SENSITIVITY fields, analyze the context:
   - Is this a user-facing API vs internal system API?
   - Does the endpoint handle personal vs business data?
   - Are there other indicators of personal data in the request?

### Step 4: Value Pattern Analysis
Analyze actual values (if provided) for sensitive patterns:
```
- SSN format: XXX-XX-XXXX or XXXXXXXXX
- Credit card format: XXXX-XXXX-XXXX-XXXX or 16 digits
- Phone format: (XXX) XXX-XXXX or similar
- Email format: user@domain.com
- Date format suggesting DOB: MM/DD/YYYY
- ZIP codes, coordinates, IP addresses
```

## Output Format

Provide your analysis in this format:

```
## ANALYSIS RESULTS

### API Endpoint Analysis
- **Endpoint**: [URL path]
- **Purpose**: [Brief description of API function]
- **Risk Level**: [High/Medium/Low]

### SENSITIVE FIELDS DETECTED

#### HIGH PRIORITY (Immediate Masking Required)
| Field Name | Category | Reason | Masking Strategy |
|------------|----------|---------|------------------|
| field_name | PCI/SPI/etc | Pattern match | Full/Partial mask |

#### MEDIUM PRIORITY (Review Required)
| Field Name | Category | Context | Recommendation |
|------------|----------|---------|----------------|
| field_name | CPNI/etc | Context details | Mask/Monitor/Safe |

### SAFE FIELDS (No Masking Required)
- field1: Technical identifier
- field2: System reference
- field3: Business logic field

### RECOMMENDATIONS
1. [Specific masking recommendations]
2. [Additional security considerations]
3. [Monitoring suggestions]
```

## Example Usage Instruction

**Input**: Provide the cURL command like this:
```bash
curl -X POST https://api.example.com/users \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "12345",
    "first_name": "John",
    "ssn": "123-45-6789",
    "request_id": "req_789"
  }'
```

**Expected**: The copilot will analyze and return the structured analysis showing which fields need masking and which are safe.

## Key Principles
1. **Whitelist First**: Always check safe patterns before flagging
2. **Context Matters**: Consider the API's purpose and data flow
3. **Minimize False Positives**: Err on the side of not flagging technical fields
4. **Comprehensive Coverage**: Ensure all regulated data types are covered
5. **Clear Justification**: Always explain why a field is or isn't flagged