#!/usr/bin/env python3
"""
Final fix for timestamp format consistency
"""

import os

def fix_timestamp_format():
    """Fix the timestamp format in minimal_api.py"""
    
    api_file = 'apps/api/minimal_api.py'
    
    with open(api_file, 'r') as f:
        content = f.read()
    
    # Replace the fix_datetime_tz function with a better implementation
    old_function = '''def fix_datetime_tz(dt):
    """Ensure datetime has timezone info for consistent API responses"""
    if dt is None:
        return None
    if hasattr(dt, 'tzinfo') and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc).isoformat()
    return dt.isoformat()'''
    
    new_function = '''def fix_datetime_tz(dt):
    """Ensure datetime has timezone info for consistent API responses"""
    if dt is None:
        return None
    if hasattr(dt, 'tzinfo'):
        if dt.tzinfo is None:
            # Add UTC timezone if missing
            return dt.replace(tzinfo=timezone.utc).isoformat()
        else:
            # Ensure consistent format with +00:00 instead of Z
            iso_str = dt.isoformat()
            if iso_str.endswith('Z'):
                return iso_str[:-1] + '+00:00'
            return iso_str
    return str(dt)'''
    
    content = content.replace(old_function, new_function)
    
    with open(api_file, 'w') as f:
        f.write(content)
    
    print("✅ Updated timestamp formatting function")

if __name__ == "__main__":
    fix_timestamp_format()