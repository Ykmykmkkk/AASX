# dummy_simulator/simulator.Dockerfile
FROM python:3.9-slim
WORKDIR /app
# /data는 볼륨 마운트로 제공되므로 디렉토리 생성 불필요
COPY simulator.py .
CMD ["python", "simulator.py"]