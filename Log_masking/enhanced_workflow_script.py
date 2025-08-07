#!/usr/bin/env python3
"""
Enhanced Complete Telecom API Analysis Workflow
Includes pattern-based blacklist generation with consolidated output
"""

import os
import sys
import subprocess
import json

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} failed: {e}")
        return False

def check_file_exists(file_path, description):
    """Check if a file exists"""
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description} not found: {file_path}")
        return False

def show_patterns_info():
    """Show information about patterns configuration"""
    print("\n📋 PATTERN CONFIGURATION INFO")
    print("-" * 50)
    print("The analysis uses patterns from 'patterns_config.json':")
    print("📁 Keywords: Sensitive field name patterns (SPI, CPNI, RPI, CSO, PCI)")
    print("🔍 Value patterns: Regex patterns for sensitive values")
    print("🧠 Fuzzy rules: Intelligent matching for abbreviations")
    print("⚠️  Exclusions: Fields to never blacklist")
    print("\n💡 You can customize patterns by editing patterns_config.json")

def main():
    print("🚀 Enhanced Telecom API Blacklist Generation Workflow")
    print("=" * 70)
    
    # Check if collection file exists
    collection_file = "your-collection.json"
    if not check_file_exists(collection_file, "Postman collection file"):
        print("\n📋 Please export your Postman collection and save as 'your-collection.json'")
        print("Instructions:")
        print("1. Open Postman")
        print("2. Click on your collection")
        print("3. Click the '...' menu → Export")
        print("4. Choose 'Collection v2.1' format")
        print("5. Save as 'your-collection.json' in this directory")
        return False
    
    # Step 1: Extract data from Postman collection
    print(f"\n📊 STEP 1: EXTRACTING DATA FROM POSTMAN COLLECTION")
    print("-" * 50)
    
    if not run_command("python run_processor.py", "Postman data extraction"):
        return False
    
    # Check if extraction results exist
    extraction_file = "postman_extraction_results.json"
    if not check_file_exists(extraction_file, "Extraction results"):
        return False
    
    # Step 2: Generate consolidated blacklist
    print(f"\n🧠 STEP 2: GENERATING CONSOLIDATED BLACKLIST")
    print("-" * 50)
    
    if not run_command(f"python blacklist_generator.py {extraction_file}", "Blacklist generation"):
        return False
    
    # Check generated files
    generated_files = [
        ("application.properties", "Application properties"),
        ("blacklist_detailed_table.html", "Detailed review table"),
        ("patterns_config.json", "Patterns configuration")
    ]
    
    all_files_exist = True
    for file_path, description in generated_files:
        if not check_file_exists(file_path, description):
            all_files_exist = False
    
    if not all_files_exist:
        return False
    
    # Show results summary
    print(f"\n📋 STEP 3: RESULTS SUMMARY")
    print("-" * 50)
    
    try:
        # Load and display summary from application.properties
        with open("application.properties", 'r') as f:
            props_content = f.read()
        
        # Extract blacklist counts
        payload_line = [line for line in props_content.split('\n') if line.startswith('payload.blacklist=')]
        headers_line = [line for line in props_content.split('\n') if line.startswith('headers.blacklist=')]
        
        if payload_line:
            payload_fields = payload_line[0].split('=')[1]
            payload_count = len([f for f in payload_fields.split(',') if f.strip()]) if payload_fields.strip() else 0
            print(f"📦 Payload blacklist: {payload_count} fields")
            if payload_count > 0:
                preview = payload_fields[:100] + "..." if len(payload_fields) > 100 else payload_fields
                print(f"   Preview: {preview}")
        
        if headers_line:
            headers_fields = headers_line[0].split('=')[1]
            headers_count = len([f for f in headers_fields.split(',') if f.strip()]) if headers_fields.strip() else 0
            print(f"📋 Headers blacklist: {headers_count} fields")
            if headers_count > 0:
                preview = headers_fields[:100] + "..." if len(headers_fields) > 100 else headers_fields
                print(f"   Preview: {preview}")
        
    except Exception as e:
        print(f"⚠️  Could not load summary: {e}")
    
    # Show pattern info
    show_patterns_info()
    
    # Step 4: Usage instructions
    print(f"\n📋 STEP 4: NEXT ACTIONS")
    print("-" * 50)
    print("📄 Files ready for use:")
    print(f"   • application.properties (copy to your application)")
    print(f"   • blacklist_detailed_table.html (open in browser for review)")
    print(f"   • patterns_config.json (customize patterns as needed)")
    print()
    print("🎯 Recommended workflow:")
    print("1. 📖 Open blacklist_detailed_table.html in your browser")
    print("2. 👀 Review all blacklisted fields for accuracy")
    print("3. ✅ Verify no sensitive fields were missed")
    print("4. ⚙️  Customize patterns_config.json if needed")
    print("5. 📝 Copy application.properties entries to your app")
    print("6. 🧪 Test your APIs with blacklist applied")
    
    print(f"\n✅ WORKFLOW COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    print("💡 Pro tip: Run this workflow regularly when your APIs change")
    print("🔄 Rerun analysis anytime by: python blacklist_generator.py postman_extraction_results.json")
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print(f"\n🎉 All steps completed successfully!")
        print(f"👀 Next: Open blacklist_detailed_table.html to review decisions")
    else:
        print(f"\n💥 Workflow failed. Please check the errors above.")
        sys.exit(1)