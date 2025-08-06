#!/usr/bin/env python3
"""
Mock AAS Server v6
Flask 기반 AAS REST API 서버 (시점별 동적 데이터 지원)
"""

from flask import Flask, jsonify, request, abort
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# Flask 앱 초기화
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['JSON_SORT_KEYS'] = False

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AASMockServer:
    """AAS Mock Server with timepoint-based data"""
    
    def __init__(self, data_dir: str = "../aas_data"):
        self.data_dir = data_dir
        self.shells_dir = os.path.join(data_dir, "shells")
        self.submodels_dir = os.path.join(data_dir, "submodels")
        
        # 데이터 로드
        self.shells = {}
        self.submodels = {}
        self.timepoint_submodels = {}  # 시점별 Submodel 저장
        
        self.load_data()
        logger.info(f"✅ Server initialized with {len(self.shells)} shells")
    
    def load_data(self):
        """AAS 데이터 로드"""
        # Shell 로드
        if os.path.exists(self.shells_dir):
            for filename in os.listdir(self.shells_dir):
                if filename.endswith(".json"):
                    filepath = os.path.join(self.shells_dir, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        shell = json.load(f)
                        shell_id = shell.get("id")
                        self.shells[shell_id] = shell
                        logger.info(f"  Loaded shell: {shell_id}")
        
        # Submodel 로드
        if os.path.exists(self.submodels_dir):
            for filename in os.listdir(self.submodels_dir):
                if filename.endswith(".json"):
                    filepath = os.path.join(self.submodels_dir, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        submodel = json.load(f)
                        submodel_id = submodel.get("id")
                        
                        # 시점별 Submodel 구분
                        if "_T" in filename:
                            # 시점별 데이터 (예: CNC001_OperationalData_T4.json)
                            timepoint = filename.split("_T")[1].replace(".json", "")
                            timepoint = f"T{timepoint}"
                            
                            if timepoint not in self.timepoint_submodels:
                                self.timepoint_submodels[timepoint] = {}
                            self.timepoint_submodels[timepoint][submodel_id] = submodel
                        else:
                            # 정적 데이터
                            self.submodels[submodel_id] = submodel
    
    def map_timestamp_to_timepoint(self, timestamp: Optional[str]) -> str:
        """timestamp를 timepoint(T1-T5)로 매핑"""
        if not timestamp:
            return "T4"  # 기본값: 실패 시점
        
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            hour = dt.hour
            
            if hour <= 8:
                return "T1"
            elif hour <= 10:
                return "T2"
            elif hour <= 12:
                return "T3"
            elif hour <= 14:
                return "T4"
            else:
                return "T5"
        except:
            return "T4"
    
    def get_submodel_at_time(self, submodel_id: str, timestamp: Optional[str]) -> Optional[Dict]:
        """특정 시점의 Submodel 조회"""
        # 정적 Submodel 확인
        if submodel_id in self.submodels:
            return self.submodels[submodel_id]
        
        # 시점별 Submodel 조회
        timepoint = self.map_timestamp_to_timepoint(timestamp)
        if timepoint in self.timepoint_submodels:
            if submodel_id in self.timepoint_submodels[timepoint]:
                return self.timepoint_submodels[timepoint][submodel_id]
        
        # 가장 가까운 시점 데이터 반환
        for tp in ["T4", "T3", "T2", "T1", "T5"]:
            if tp in self.timepoint_submodels:
                if submodel_id in self.timepoint_submodels[tp]:
                    return self.timepoint_submodels[tp][submodel_id]
        
        return None
    
    def get_cooling_machines(self) -> List[Dict]:
        """냉각이 필요한 기계 조회"""
        cooling_machines = []
        
        for shell_id, shell in self.shells.items():
            if "Machine" in shell_id:
                # TechnicalData에서 cooling_required 확인
                machine_id = shell.get("idShort")
                tech_data_id = f"urn:aas:sm:{machine_id}:TechnicalData"
                tech_data = self.submodels.get(tech_data_id)
                
                if tech_data:
                    # CoolingRequired 속성 찾기
                    for element in tech_data.get("submodelElements", []):
                        if element.get("idShort") == "CoolingRequired":
                            if element.get("value") == "true":
                                cooling_machines.append({
                                    "machine_id": machine_id,
                                    "shell_id": shell_id,
                                    "cooling_required": True
                                })
                                break
        
        return cooling_machines
    
    def get_failed_jobs(self, date: str) -> List[Dict]:
        """특정 날짜의 실패한 작업 조회"""
        failed_jobs = []
        timepoint = "T4"  # 실패 시점
        
        # 모든 기계의 JobHistory 확인
        for shell_id, shell in self.shells.items():
            if "Machine" in shell_id:
                machine_id = shell.get("idShort")
                job_history_id = f"urn:aas:sm:{machine_id}:JobHistory"
                
                # T4 시점의 JobHistory 조회
                if timepoint in self.timepoint_submodels:
                    job_history = self.timepoint_submodels[timepoint].get(job_history_id)
                    
                    if job_history:
                        for job_element in job_history.get("submodelElements", []):
                            # Job 정보 추출
                            job_data = {
                                "job_id": job_element.get("idShort"),
                                "machine_id": machine_id
                            }
                            
                            # Job 속성 추출
                            for prop in job_element.get("value", []):
                                id_short = prop.get("idShort")
                                value = prop.get("value")
                                
                                if id_short == "Status" and value == "FAILED":
                                    job_data["status"] = value
                                elif id_short == "ProductId":
                                    job_data["product_id"] = value
                                elif id_short == "FailureReason":
                                    job_data["failure_reason"] = value
                                elif id_short == "ErrorDetails":
                                    job_data["error_details"] = value
                                elif id_short == "StartTime":
                                    job_data["start_time"] = value
                            
                            # FAILED 상태인 작업만 추가
                            if job_data.get("status") == "FAILED":
                                failed_jobs.append(job_data)
        
        return failed_jobs


# 서버 인스턴스 생성
server = AASMockServer()


# ===== REST API 엔드포인트 =====

@app.route('/health', methods=['GET'])
def health_check():
    """헬스 체크"""
    return jsonify({"status": "healthy", "message": "AAS Mock Server v6 is running"})


@app.route('/shells', methods=['GET'])
def get_shells():
    """모든 AAS Shell 조회"""
    return jsonify(list(server.shells.values()))


@app.route('/shells/<path:aas_id>', methods=['GET'])
def get_shell(aas_id):
    """특정 AAS Shell 조회"""
    # URL 디코딩
    aas_id = aas_id.replace("%3A", ":")
    
    shell = server.shells.get(aas_id)
    if shell:
        return jsonify(shell)
    
    # ID로 찾기 실패하면 idShort로 찾기
    for shell_id, shell_data in server.shells.items():
        if shell_data.get("idShort") == aas_id:
            return jsonify(shell_data)
    
    return jsonify({"error": f"Shell not found: {aas_id}"}), 404


@app.route('/shells/<path:aas_id>/submodels', methods=['GET'])
def get_shell_submodels(aas_id):
    """Shell의 Submodel 목록 조회"""
    aas_id = aas_id.replace("%3A", ":")
    
    shell = server.shells.get(aas_id)
    if shell:
        return jsonify(shell.get("submodels", []))
    
    return jsonify({"error": f"Shell not found: {aas_id}"}), 404


@app.route('/submodels/<path:submodel_id>', methods=['GET'])
def get_submodel(submodel_id):
    """Submodel 조회"""
    # URL 디코딩
    submodel_id = submodel_id.replace("%3A", ":")
    
    # timestamp 파라미터 확인
    timestamp = request.args.get('timestamp')
    
    submodel = server.get_submodel_at_time(submodel_id, timestamp)
    if submodel:
        return jsonify(submodel)
    
    return jsonify({"error": f"Submodel not found: {submodel_id}"}), 404


# ===== Goal별 특수 엔드포인트 =====

@app.route('/api/machines/cooling-required', methods=['GET'])
def get_cooling_required_machines():
    """냉각이 필요한 기계 조회 (Goal 1)"""
    machines = server.get_cooling_machines()
    logger.info(f"Cooling machines requested: {len(machines)} found")
    return jsonify(machines)


@app.route('/api/jobs/failed', methods=['GET'])
def get_failed_jobs():
    """실패한 작업 조회 (Goal 1)"""
    date = request.args.get('date', '2025-07-17')
    jobs = server.get_failed_jobs(date)
    logger.info(f"Failed jobs requested for {date}: {len(jobs)} found")
    return jsonify(jobs)


@app.route('/api/products/cooling-required', methods=['GET'])
def get_cooling_products():
    """냉각이 필요한 제품 조회"""
    cooling_products = []
    
    for shell_id, shell in server.shells.items():
        if "Product" in shell_id:
            product_id = shell.get("idShort")
            req_id = f"urn:aas:sm:{product_id}:Requirements"
            requirements = server.submodels.get(req_id)
            
            if requirements:
                for element in requirements.get("submodelElements", []):
                    if element.get("idShort") == "RequiresCooling":
                        if element.get("value") == "true":
                            cooling_products.append(product_id)
                            break
    
    return jsonify(cooling_products)


# ===== Goal 4: Product Tracking 엔드포인트 =====

@app.route('/api/products/<product_id>/location', methods=['GET'])
def get_product_location(product_id):
    """제품 위치 조회 (Goal 4)"""
    include_history = request.args.get('history', 'false').lower() == 'true'
    timepoint = request.args.get('timepoint', 'T4')
    
    tracking_id = f"urn:aas:sm:{product_id}:TrackingInfo"
    
    # 현재 위치 조회 (지정된 시점 또는 최신)
    current = server.get_submodel_at_time(tracking_id, timepoint)
    
    if not current:
        return jsonify({"error": f"Tracking info not found for {product_id}"}), 404
    
    # 현재 위치 정보 추출
    current_location = {}
    for element in current.get("submodelElements", []):
        id_short = element.get("idShort")
        value = element.get("value")
        current_location[id_short] = value
    
    result = {
        "product_id": product_id,
        "current_location": current_location,
        "timepoint": timepoint
    }
    
    # 이력 조회 (옵션)
    if include_history:
        history = []
        for tp in ["T1", "T2", "T3", "T4", "T5"]:
            location_data = server.get_submodel_at_time(tracking_id, tp)
            if location_data:
                location_info = {}
                for element in location_data.get("submodelElements", []):
                    id_short = element.get("idShort")
                    value = element.get("value")
                    location_info[id_short] = value
                
                history.append({
                    "timepoint": tp,
                    "location": location_info
                })
        result["history"] = history
    
    logger.info(f"Product location requested for {product_id} at {timepoint}")
    return jsonify(result)


@app.route('/api/products/tracking', methods=['GET'])
def get_all_product_tracking():
    """모든 제품의 현재 위치 조회"""
    timepoint = request.args.get('timepoint', 'T4')
    tracking_data = []
    
    for shell_id, shell in server.shells.items():
        if "Product" in shell_id:
            product_id = shell.get("idShort")
            tracking_id = f"urn:aas:sm:{product_id}:TrackingInfo"
            
            location_data = server.get_submodel_at_time(tracking_id, timepoint)
            if location_data:
                location_info = {"product_id": product_id}
                for element in location_data.get("submodelElements", []):
                    id_short = element.get("idShort")
                    value = element.get("value")
                    location_info[id_short] = value
                tracking_data.append(location_info)
    
    logger.info(f"All product tracking requested at {timepoint}: {len(tracking_data)} products")
    return jsonify(tracking_data)


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Starting AAS Mock Server v6")
    print("=" * 60)
    print(f"📁 Data directory: {server.data_dir}")
    print(f"🔧 Loaded {len(server.shells)} shells")
    print(f"📦 Loaded {len(server.submodels)} static submodels")
    print(f"⏰ Timepoints available: {list(server.timepoint_submodels.keys())}")
    print("=" * 60)
    print("🌐 Server running at: http://localhost:5001")
    print("📍 Goal 4 endpoints:")
    print("   - GET /api/products/<product_id>/location")
    print("   - GET /api/products/tracking")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5001, debug=True)