# Simple AASX Simulator Docker Image (no pandas/numpy dependencies)
FROM python:3.9-slim

WORKDIR /app

# 단순화된 AASX 시뮬레이터 복사
COPY simple_aasx_runner.py /app/

# 작업 디렉토리 생성 (PVC 마운트 지점)
RUN mkdir -p /data/current /data/scenarios

# 실행 가능하게 설정
RUN chmod +x /app/simple_aasx_runner.py

# 기본 명령어
CMD ["python", "/app/simple_aasx_runner.py"]