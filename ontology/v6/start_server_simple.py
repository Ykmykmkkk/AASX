#!/usr/bin/env python3
"""
Simple server starter for testing
Flask 없이도 기본 테스트 가능하도록
"""

import sys
import os

print("=" * 60)
print("⚠️ Mock Server requires Flask")
print("=" * 60)

try:
    import flask
    print("✅ Flask is installed")
    print(f"   Version: {flask.__version__}")
    
    # 서버 시작
    print("\n🚀 Starting Mock Server...")
    print("   URL: http://localhost:5001")
    print("   Press Ctrl+C to stop")
    print("=" * 60)
    
    os.chdir("src")
    exec(open("mock_server.py").read())
    
except ImportError:
    print("❌ Flask is not installed")
    print("\nTo install Flask:")
    print("  pip3 install flask")
    print("\nOr use virtual environment:")
    print("  python3 -m venv venv")
    print("  source venv/bin/activate")
    print("  pip install flask requests")
    
    print("\n⚠️ Running tests in FALLBACK mode (local snapshots only)")
    print("=" * 60)