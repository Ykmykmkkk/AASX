#!/bin/bash

# AAS Mock Server v6 시작 스크립트

echo "=============================="
echo "🚀 Starting AAS Mock Server v6"
echo "=============================="

# 현재 디렉토리 확인
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$SCRIPT_DIR/.."

cd "$PROJECT_DIR"

# Python 버전 확인
echo "📌 Python version:"
python3 --version

# Flask 설치 확인
echo ""
echo "📦 Checking Flask installation..."
python3 -c "import flask; print(f'  Flask version: {flask.__version__}')" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "⚠️  Flask not installed. Installing..."
    pip3 install flask
fi

# requests 설치 확인
echo ""
echo "📦 Checking requests installation..."
python3 -c "import requests; print(f'  Requests version: {requests.__version__}')" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "⚠️  Requests not installed. Installing..."
    pip3 install requests
fi

# 서버 시작
echo ""
echo "=============================="
echo "🌐 Starting server..."
echo "=============================="
cd src
python3 mock_server.py