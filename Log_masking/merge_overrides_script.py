#!/usr/bin/env python3
"""
Merge Developer Overrides Script
Merges developer_overrides.json into patterns_config.json
"""

import json
import sys
import os
from datetime import datetime

def merge_overrides(overrides_file: str, patterns_file: str):
    """Merge developer overrides into patterns configuration"""
    
    # Check if files exist
    if not os.path.exists(overrides_file):
        print(f"❌ Override file {overrides_file} not found")
        return False
    
    if not os.path.exists(patterns_file):
        print(f"❌ Patterns file {patterns_file} not found")
        return False
    
    try:
        # Load override file
        with open(overrides_file, 'r') as f:
            overrides = json.load(f)
        
        print(f"📄 Loaded overrides from {overrides_file}")
        print(f"   • Manual blacklist: {len(overrides.get('manual_blacklist', []))} fields")
        print(f"   • Manual whitelist: {len(overrides.get('manual_whitelist', []))} fields")
        
        # Load patterns file
        with open(patterns_file, 'r') as f:
            patterns = json.load(f)
        
        print(f"📄 Loaded patterns from {patterns_file}")
        
        # Backup original patterns file
        backup_file = f"{patterns_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        with open(backup_file, 'w') as f:
            json.dump(patterns, f, indent=2)
        print(f"💾 Created backup: {backup_file}")
        
        # Get current overrides
        current_overrides = patterns.get('developer_overrides', {})
        current_blacklist = set(current_overrides.get('manual_blacklist', []))
        current_whitelist = set(current_overrides.get('manual_whitelist', []))
        
        # Merge new overrides
        new_blacklist = set(overrides.get('manual_blacklist', []))
        new_whitelist = set(overrides.get('manual_whitelist', []))
        
        # Combine with existing (union)
        combined_blacklist = current_blacklist.union(new_blacklist)
        combined_whitelist = current_whitelist.union(new_whitelist)
        
        # Remove conflicts (whitelist takes precedence)
        final_blacklist = combined_blacklist - combined_whitelist
        final_whitelist = combined_whitelist
        
        # Update patterns config
        patterns['developer_overrides'] = {
            'manual_blacklist': sorted(list(final_blacklist)),
            'manual_whitelist': sorted(list(final_whitelist)),
            'last_updated': datetime.now().isoformat(),
            'merged_from': overrides_file
        }
        
        # Save updated patterns file
        with open(patterns_file, 'w') as f:
            json.dump(patterns, f, indent=2)
        
        print(f"✅ Successfully merged overrides into {patterns_file}")
        print(f"📊 Final counts:")
        print(f"   • Total manual blacklist: {len(final_blacklist)} fields")
        print(f"   • Total manual whitelist: {len(final_whitelist)} fields")
        
        if final_blacklist:
            print(f"📋 Manual blacklist fields:")
            for field in sorted(list(final_blacklist))[:10]:
                print(f"   ✅ {field}")
            if len(final_blacklist) > 10:
                print(f"   ... and {len(final_blacklist) - 10} more")
        
        if final_whitelist:
            print(f"📋 Manual whitelist fields:")
            for field in sorted(list(final_whitelist))[:10]:
                print(f"   ❌ {field}")
            if len(final_whitelist) > 10:
                print(f"   ... and {len(final_whitelist) - 10} more")
        
        # Clean up override file
        os.remove(overrides_file)
        print(f"🗑️  Removed {overrides_file} (merged successfully)")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON: {e}")
        return False
    except Exception as e:
        print(f"❌ Error during merge: {e}")
        return False

def main():
    if len(sys.argv) != 3:
        print("Usage: python merge_overrides.py <developer_overrides.json> <patterns_config.json>")
        print("Example: python merge_overrides.py developer_overrides.json patterns_config.json")
        return
    
    overrides_file = sys.argv[1]
    patterns_file = sys.argv[2]
    
    print("🔄 Starting developer overrides merge...")
    print(f"📄 Override file: {overrides_file}")
    print(f"⚙️  Patterns file: {patterns_file}")
    
    success = merge_overrides(overrides_file, patterns_file)
    
    if success:
        print("\n✅ Merge completed successfully!")
        print("🚀 You can now re-run the blacklist analysis to see your manual overrides applied.")
    else:
        print("\n❌ Merge failed. Please check the error messages above.")

if __name__ == "__main__":
    main()