#!/usr/bin/env python3
"""
Start Mock AAS Server v6 with correct paths
"""

import os
import sys

# v6 루트 디렉토리로 이동
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# src를 Python path에 추가
sys.path.insert(0, os.path.join(script_dir, 'src'))

print("=" * 60)
print("🚀 Starting AAS Mock Server v6")
print("=" * 60)
print(f"📁 Working directory: {os.getcwd()}")
print(f"📦 AAS data directory: {os.path.join(script_dir, 'aas_data')}")
print("=" * 60)

# Mock server import 및 실행
from src.mock_server import app, server

# 데이터 디렉토리 재설정
server.data_dir = os.path.join(script_dir, "aas_data")
server.shells_dir = os.path.join(server.data_dir, "shells")
server.submodels_dir = os.path.join(server.data_dir, "submodels")

# 데이터 다시 로드
server.shells = {}
server.submodels = {}
server.timepoint_submodels = {}
server.load_data()

print(f"🔧 Loaded {len(server.shells)} shells")
print(f"📦 Loaded {len(server.submodels)} static submodels")
print(f"⏰ Timepoints available: {list(server.timepoint_submodels.keys())}")
print("=" * 60)
print("🌐 Server running at: http://localhost:5001")
print("=" * 60)

app.run(host='0.0.0.0', port=5001, debug=True)