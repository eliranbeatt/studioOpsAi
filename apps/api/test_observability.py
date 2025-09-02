#!/usr/bin/env python3
"""
Test script for Langfuse observability integration
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.observability_service import observability_service

def test_observability():
    """Test Langfuse observability integration"""
    print("Testing Langfuse observability integration...")
    
    # Check if Langfuse is enabled
    print(f"Langfuse enabled: {observability_service.enabled}")
    
    if observability_service.enabled:
        print("✓ Langfuse client initialized successfully")
        
        # Test creating a trace
        trace_id = observability_service.create_trace(
            name="test_trace",
            user_id="test_user",
            metadata={"test": "data"}
        )
        
        if trace_id:
            print(f"✓ Trace created successfully: {trace_id}")
            
            # Test creating a span
            span_id = observability_service.create_span(
                trace_id=trace_id,
                name="test_span",
                metadata={"span_test": "data"}
            )
            
            if span_id:
                print(f"✓ Span created successfully: {span_id}")
            else:
                print("✗ Failed to create span")
                
            # Test creating an event
            event_id = observability_service.create_event(
                trace_id=trace_id,
                name="test_event",
                metadata={"event_test": "data"}
            )
            
            if event_id:
                print(f"✓ Event created successfully: {event_id}")
            else:
                print("✗ Failed to create event")
                
            # Test error tracking
            error_id = observability_service.track_error(
                trace_id=trace_id,
                error_type="TestError",
                error_message="This is a test error",
                context={"test_context": "data"}
            )
            
            if error_id:
                print(f"✓ Error tracked successfully: {error_id}")
            else:
                print("✗ Failed to track error")
                
            # Flush events
            observability_service.flush()
            print("✓ Events flushed successfully")
            
        else:
            print("✗ Failed to create trace")
            
    else:
        print("⚠ Langfuse is disabled. Check your environment variables:")
        print(f"  LANGFUSE_PUBLIC_KEY: {os.getenv('LANGFUSE_PUBLIC_KEY')}")
        print(f"  LANGFUSE_SECRET_KEY: {os.getenv('LANGFUSE_SECRET_KEY')}")
        print(f"  LANGFUSE_HOST: {os.getenv('LANGFUSE_HOST')}")
        print("\nTo enable Langfuse, set the required environment variables.")

if __name__ == "__main__":
    test_observability()