#!/usr/bin/env python
import sys
import os

# Test imports
try:
    print("Testing backend imports...")
    import backend
    print("✓ Backend imported successfully")
except Exception as e:
    print(f"✗ Import error: {e}")
    import traceback
    traceback.print_exc()
