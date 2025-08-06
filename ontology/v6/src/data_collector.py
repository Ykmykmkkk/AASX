"""
Data Collector for v6 AAS Integration
다양한 데이터 소스에서 데이터 수집 (AAS API, Snapshot, SPARQL)
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    logging.warning("⚠️ requests module not available, using snapshot data only")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataCollector:
    """다중 소스 데이터 수집기"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self.get_default_config()
        self.snapshot_dir = "./snapshots"
        self.cache = {}  # 캐시
        
    def get_default_config(self) -> Dict[str, Any]:
        """기본 설정"""
        return {
            "aas_server": {
                "primary": "http://localhost:5001",
                "fallback": "http://localhost:5002"
            },
            "sparql_endpoint": "http://localhost:3030/production/sparql",
            "snapshot_store": "../snapshots",
            "timeout": 5
        }
    
    def collect_from_aas(self, endpoint: str, method: str = "GET", 
                        params: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """AAS Server에서 데이터 수집"""
        if not HAS_REQUESTS:
            logger.warning(f"⚠️ Requests not available, skipping AAS: {endpoint}")
            return None
            
        # 우선 Mock Server 시도
        base_url = self.config["aas_server"]["primary"]
        url = f"{base_url}{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                params=params,
                timeout=self.config["timeout"]
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Collected from AAS: {endpoint}")
                return response.json()
            else:
                logger.warning(f"⚠️ AAS returned {response.status_code}: {endpoint}")
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️ AAS request failed: {e}")
            
        # Fallback to secondary server
        if self.config["aas_server"]["fallback"]:
            return self._try_fallback_aas(endpoint, method, params)
            
        return None
    
    def _try_fallback_aas(self, endpoint: str, method: str, 
                         params: Optional[Dict]) -> Optional[Dict[str, Any]]:
        """Fallback AAS Server 시도"""
        if not HAS_REQUESTS:
            return None
            
        base_url = self.config["aas_server"]["fallback"]
        url = f"{base_url}{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                params=params,
                timeout=self.config["timeout"]
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Collected from fallback AAS: {endpoint}")
                return response.json()
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Fallback AAS also failed: {e}")
            
        return None
    
    def collect_from_snapshot(self, timepoint: str, data_path: str) -> Optional[Any]:
        """스냅샷 저장소에서 데이터 수집"""
        # 스냅샷 파일 찾기
        snapshot_files = [
            f for f in os.listdir(self.snapshot_dir)
            if f.startswith(f"snapshot_{timepoint}_") and f.endswith(".json")
        ]
        
        if not snapshot_files:
            logger.warning(f"⚠️ No snapshot found for {timepoint}")
            return None
            
        snapshot_file = os.path.join(self.snapshot_dir, snapshot_files[0])
        
        try:
            with open(snapshot_file, 'r', encoding='utf-8') as f:
                snapshot_data = json.load(f)
                
            # 데이터 경로 탐색
            if not data_path:
                return snapshot_data
                
            result = snapshot_data
            for key in data_path.split('.'):
                if key and key in result:
                    result = result[key]
                elif not key:
                    continue
                else:
                    logger.warning(f"⚠️ Path {data_path} not found in snapshot")
                    return None
                    
            logger.info(f"✅ Collected from snapshot: {timepoint}/{data_path}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to read snapshot: {e}")
            return None
    
    def collect_machines_with_cooling(self) -> List[Dict[str, Any]]:
        """냉각 기능이 있는 기계 수집"""
        # AAS API 시도
        endpoint = "/api/machines/cooling-required"
        machines = self.collect_from_aas(endpoint)
        
        if machines:
            return machines
            
        # Fallback to snapshot
        logger.info("📂 Falling back to snapshot data for machines")
        snapshot_data = self.collect_from_snapshot("T2", "machines")
        
        if snapshot_data:
            # 냉각 필요한 기계만 필터링
            cooling_machines = []
            for machine_id, machine_data in snapshot_data.items():
                if machine_data.get("cooling_required", False):
                    cooling_machines.append(machine_data)
            return cooling_machines
            
        return []
    
    def collect_job_history(self, date: str, timepoint: str = "T4") -> List[Dict[str, Any]]:
        """작업 이력 수집"""
        # 스냅샷에서 수집 (T4: 실패 시점)
        jobs = self.collect_from_snapshot(timepoint, "jobs")
        
        if not jobs:
            # AAS API fallback
            endpoint = f"/api/jobs/history"
            params = {"date": date}
            jobs = self.collect_from_aas(endpoint, params=params)
            
        return jobs or []
    
    def collect_sensor_data(self, machine_id: str, timepoint: str) -> Optional[Dict[str, Any]]:
        """센서 데이터 수집"""
        # 스냅샷에서 수집
        sensor_data = self.collect_from_snapshot(timepoint, f"sensor_data")
        
        if sensor_data and machine_id in sensor_data:
            return sensor_data[machine_id]
            
        # AAS API fallback
        endpoint = f"/shells/Machine-{machine_id}/submodels/OperationalData/timeseries"
        return self.collect_from_aas(endpoint)
    
    def collect_product_info(self, product_id: str) -> Optional[Dict[str, Any]]:
        """제품 정보 수집"""
        # AAS API 시도
        endpoint = f"/shells/Product-{product_id}"
        product = self.collect_from_aas(endpoint)
        
        if product:
            return product
            
        # 스냅샷 fallback
        products = self.collect_from_snapshot("T1", "products")
        if products and product_id in products:
            return products[product_id]
            
        return None
    
    def collect_machine_schedule(self, timepoint: str = "T2") -> Dict[str, Any]:
        """기계 스케줄 수집"""
        machines = self.collect_from_snapshot(timepoint, "machines")
        
        if not machines:
            # AAS API fallback
            endpoint = "/api/machines/schedule"
            machines = self.collect_from_aas(endpoint)
            
        return machines or {}
    
    def filter_failed_jobs(self, jobs: List[Dict[str, Any]], 
                          cooling_products: List[str],
                          cooling_machines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """실패한 작업 필터링"""
        failed_jobs = []
        
        # cooling_machines에서 machine_id 추출
        cooling_machine_ids = []
        if cooling_machines:
            if isinstance(cooling_machines[0], dict):
                cooling_machine_ids = [m.get("machine_id") for m in cooling_machines]
            else:
                cooling_machine_ids = cooling_machines
        
        logger.info(f"  Products requiring cooling: {cooling_products}")
        logger.info(f"  Machines with cooling: {cooling_machine_ids}")
        logger.info(f"  Total jobs to filter: {len(jobs) if jobs else 0}")
        
        if jobs:
            for job in jobs:
                if (job.get("status") == "FAILED" and
                    job.get("product_id") in cooling_products and
                    job.get("machine_id") in cooling_machine_ids):
                    
                    failed_jobs.append(job)
                    logger.info(f"    Found failed job: {job.get('job_id')}")
                
        logger.info(f"🔍 Filtered {len(failed_jobs)} failed jobs with cooling")
        return failed_jobs


if __name__ == "__main__":
    # 테스트
    collector = DataCollector()
    
    # 냉각 기계 수집
    print("\n🏭 Collecting cooling machines:")
    machines = collector.collect_machines_with_cooling()
    print(f"  Found {len(machines)} machines with cooling")
    
    # 작업 이력 수집
    print("\n📋 Collecting job history:")
    jobs = collector.collect_job_history("2025-07-17")
    print(f"  Found {len(jobs)} jobs")
    
    # 센서 데이터 수집
    print("\n📊 Collecting sensor data:")
    sensor = collector.collect_sensor_data("CNC001", "T4")
    if sensor:
        print(f"  Temperature: {sensor['summary']['avg_temperature']}°C")
        print(f"  Anomaly score: {sensor['summary']['anomaly_score']}")