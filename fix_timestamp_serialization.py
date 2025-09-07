#!/usr/bin/env python3
"""
Fix Timestamp Serialization Issues
Addresses the timestamp format inconsistency between API and DB
"""

import os
import re

def fix_timestamp_serialization():
    """Fix timestamp serialization in API files"""
    
    api_files = [
        'apps/api/minimal_api.py',
        'apps/api/mcp_server.py',
        'apps/api/simple_api.py'
    ]
    
    for file_path in api_files:
        if not os.path.exists(file_path):
            print(f"⚠️  File not found: {file_path}")
            continue
            
        print(f"\n=== Fixing {file_path} ===")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix 1: Add timezone-aware isoformat for datetime objects
        # Replace .isoformat() with proper timezone handling
        patterns_to_fix = [
            (r'(\w+)\.isoformat\(\)', r'\1.isoformat() if \1.tzinfo else \1.replace(tzinfo=timezone.utc).isoformat()'),
            (r'row\[(\d+)\]\.isoformat\(\)', r'(row[\1].isoformat() if row[\1].tzinfo else row[\1].replace(tzinfo=timezone.utc).isoformat()) if row[\1] else None')
        ]
        
        for pattern, replacement in patterns_to_fix:
            content = re.sub(pattern, replacement, content)
        
        # Add timezone import if not present
        if 'from datetime import' in content and 'timezone' not in content:
            content = re.sub(
                r'from datetime import ([^,\n]+)',
                r'from datetime import \1, timezone',
                content
            )
        elif 'import datetime' in content and 'timezone' not in content:
            content = content.replace('import datetime', 'import datetime\nfrom datetime import timezone')
        elif 'timezone' not in content:
            # Add import at the top
            lines = content.split('\n')
            import_line = 'from datetime import timezone'
            
            # Find the best place to insert the import
            insert_idx = 0
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    insert_idx = i + 1
                elif line.strip() == '' and insert_idx > 0:
                    break
            
            lines.insert(insert_idx, import_line)
            content = '\n'.join(lines)
        
        # Write back if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed timestamp serialization in {file_path}")
        else:
            print(f"ℹ️  No changes needed in {file_path}")

def create_datetime_utility():
    """Create a utility function for consistent datetime serialization"""
    
    utility_content = '''"""
Datetime utilities for consistent API serialization
"""
from datetime import datetime, timezone
from typing import Optional, Any

def serialize_datetime(dt: Optional[datetime]) -> Optional[str]:
    """
    Serialize datetime to ISO format with timezone info
    Ensures consistency between API and database representations
    """
    if dt is None:
        return None
    
    # Ensure timezone info is present
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt.isoformat()

def serialize_row_datetime(row_value: Any) -> Optional[str]:
    """
    Serialize datetime from database row to ISO format with timezone
    """
    if row_value is None:
        return None
    
    if isinstance(row_value, datetime):
        return serialize_datetime(row_value)
    
    return str(row_value)

def ensure_timezone_aware(dt: datetime) -> datetime:
    """
    Ensure datetime object has timezone info (defaults to UTC)
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt
'''
    
    with open('apps/api/datetime_utils.py', 'w') as f:
        f.write(utility_content)
    
    print("✅ Created apps/api/datetime_utils.py")

if __name__ == "__main__":
    print("=== Fixing Timestamp Serialization Issues ===")
    fix_timestamp_serialization()
    create_datetime_utility()
    print("\n✅ Timestamp serialization fixes completed")
    print("\nNext steps:")
    print("1. Update API files to use the new datetime utilities")
    print("2. Test API responses to ensure consistent timezone format")
    print("3. Run integration tests to verify fixes")