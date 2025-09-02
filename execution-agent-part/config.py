# config.py
import os
from pathlib import Path

# 이 파일이 있는 디렉토리를 기준으로 모든 경로를 설정합니다.
BASE_DIR = Path(__file__).resolve().parent

# 온톨로지 및 AAS 데이터 파일 경로
ONTOLOGY_FILE_PATH = BASE_DIR / "ontology" / "factory_ontology_v2_final_corrected.ttl"
AAS_DATA_FILE_PATH = BASE_DIR / "aas_mock_server" / "data" / "aas_model_final_expanded.json"

# ============================================================
# AAS 서버 설정 - 외부 표준 AAS 서버 전용
# ============================================================
# 
# ⚠️ 중요: 현재 Mock 서버는 사용하지 않습니다.
# 이 시스템은 외부 표준 AAS 서버(localhost:5001)와 통신합니다.
# K8s 환경에서는 kubernetes.docker.internal:5001을 통해 호스트의 서버에 접근합니다.
#
# ============================================================

# 서버 타입 선택: "mock" 또는 "standard"
# 환경변수 USE_STANDARD_SERVER가 "true"면 표준 서버 사용
# 현재는 항상 표준 서버를 사용하도록 설정되어 있음
USE_STANDARD_SERVER = os.environ.get("USE_STANDARD_SERVER", "true").lower() == "true"  # 기본값을 "true"로 변경

if USE_STANDARD_SERVER:
    # ===== 표준 AAS 서버 설정 (현재 사용 중) =====
    AAS_SERVER_TYPE = "standard"
    
    # 표준 서버 IP와 포트
    # K8s 환경에서는 kubernetes.docker.internal 사용
    # 로컬 환경에서는 127.0.0.1 사용
    AAS_SERVER_IP = os.environ.get("AAS_SERVER_IP", "127.0.0.1")  
    AAS_SERVER_PORT = int(os.environ.get("AAS_SERVER_PORT", 5001))  # 외부 표준 서버 포트
    
    # URL 형식으로도 제공 (기존 코드 호환성)
    AAS_SERVER_URL = f"http://{AAS_SERVER_IP}:{AAS_SERVER_PORT}"
    
    print(f"🔄 Using STANDARD AAS Server at {AAS_SERVER_URL}")
else:
    # ===== Mock AAS 서버 설정 (현재 미사용 - 레거시 코드) =====
    # ⚠️ 주의: Mock 서버는 더 이상 사용되지 않습니다.
    # 이 코드는 하위 호환성을 위해 유지되고 있습니다.
    AAS_SERVER_TYPE = "mock"
    
    # Mock 서버 URL (사용되지 않음)
    AAS_SERVER_URL = os.environ.get("AAS_SERVER_URL", "http://127.0.0.1:5001")
    
    # IP와 포트로 분리 (표준 서버와 일관성 유지)
    from urllib.parse import urlparse
    parsed = urlparse(AAS_SERVER_URL)
    AAS_SERVER_IP = parsed.hostname or "127.0.0.1"
    AAS_SERVER_PORT = parsed.port or 5001
    
    print(f"📦 [DEPRECATED] Mock AAS Server configuration (not in use)")

# ============================================================
# 작업 디렉토리 설정 - 환경별 동적 경로 해결
# ============================================================

# 시뮬레이션 작업 디렉토리 설정
SIMULATION_WORK_DIR = os.environ.get("SIMULATION_WORK_DIR", None)  # None이면 자동 감지
FORCE_LOCAL_MODE = os.environ.get("FORCE_LOCAL_MODE", "false").lower() == "true"

# 디버그 정보 출력 (개발 중에만 사용)
DEBUG_MODE = os.environ.get("DEBUG_MODE", "false").lower() == "true"
if DEBUG_MODE:
    print(f"[DEBUG] Server Type: {AAS_SERVER_TYPE}")
    print(f"[DEBUG] Server IP: {AAS_SERVER_IP}")
    print(f"[DEBUG] Server Port: {AAS_SERVER_PORT}")
    print(f"[DEBUG] Ontology Path: {ONTOLOGY_FILE_PATH}")
    print(f"[DEBUG] AAS Data Path: {AAS_DATA_FILE_PATH}")
    print(f"[DEBUG] Simulation Work Dir: {SIMULATION_WORK_DIR}")
    print(f"[DEBUG] Force Local Mode: {FORCE_LOCAL_MODE}")