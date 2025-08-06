"""
Data Collector v2 for v6 AAS Integration
AAS Server 우선, 로컬 스냅샷은 fallback
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
import sys

# AAS Client import
try:
    from aas_client import AASClient
    HAS_AAS_CLIENT = True
except ImportError:
    HAS_AAS_CLIENT = False
    logging.warning("⚠️ AAS Client not available")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataCollectorV2:
    """다중 소스 데이터 수집기 v2"""
    
    def __init__(self, aas_base_url: str = "http://localhost:5001"):
        self.aas_client = AASClient(aas_base_url) if HAS_AAS_CLIENT else None
        self.snapshot_dir = "./snapshots"
        self.cache = {}
        
        # AAS Server 연결 확인
        if self.aas_client:
            if self.aas_client.health_check():
                logger.info("✅ Connected to AAS Server")
            else:
                logger.warning("⚠️ AAS Server not responding, will use fallback")
                self.aas_client = None
    
    def collect_from_aas(self, endpoint: str, method: str = "GET",
                        params: Optional[Dict] = None) -> Optional[Any]:
        """AAS Server에서 데이터 수집"""
        if not self.aas_client:
            logger.warning("⚠️ AAS Client not available")
            return None
        
        try:
            # 특수 엔드포인트 처리
            if "cooling-required" in endpoint and "machines" in endpoint:
                return self.aas_client.get_cooling_machines()
            elif "cooling-required" in endpoint and "products" in endpoint:
                return self.aas_client.get_cooling_products()
            elif "failed" in endpoint and "jobs" in endpoint:
                date = params.get("date", "2025-07-17") if params else "2025-07-17"
                return self.aas_client.get_failed_jobs(date)
            elif "/api/products/" in endpoint and "/location" in endpoint:
                # Goal 4: Product location endpoint
                product_id = endpoint.split("/api/products/")[1].split("/location")[0]
                include_history = params.get("history", False) if params else False
                timepoint = params.get("timepoint", "T4") if params else "T4"
                return self.aas_client.get_product_location(product_id, include_history, timepoint)
            elif "/api/products/tracking" in endpoint:
                # Goal 4: All product tracking
                timepoint = params.get("timepoint", "T4") if params else "T4"
                return self.aas_client.get_all_product_tracking(timepoint)
            elif endpoint.startswith("/shells/"):
                shell_id = endpoint.split("/shells/")[1]
                return self.aas_client.get_shell(shell_id)
            elif endpoint.startswith("/submodels/"):
                submodel_id = endpoint.split("/submodels/")[1]
                timestamp = params.get("timestamp") if params else None
                return self.aas_client.get_submodel(submodel_id, timestamp)
            else:
                # 일반 API 호출
                return self.aas_client.call_api(endpoint, method, params)
        except Exception as e:
            logger.error(f"❌ AAS API call failed: {e}")
            return None
    
    def collect_from_snapshot(self, timepoint: str, data_path: str) -> Optional[Any]:
        """로컬 스냅샷에서 데이터 수집 (fallback)"""
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
            
            logger.info(f"📂 Collected from local snapshot: {timepoint}/{data_path}")
            return result
        except Exception as e:
            logger.error(f"❌ Failed to read snapshot: {e}")
            return None
    
    def collect_machines_with_cooling(self) -> List[Dict[str, Any]]:
        """냉각 기능이 있는 기계 수집"""
        # 1차: AAS Server
        machines = self.collect_from_aas("/api/machines/cooling-required")
        
        if machines:
            logger.info(f"✅ Got {len(machines)} cooling machines from AAS Server")
            return machines
        
        # 2차: 로컬 스냅샷 fallback
        logger.info("📂 Falling back to local snapshot for machines")
        snapshot_data = self.collect_from_snapshot("T2", "machines")
        
        if snapshot_data:
            cooling_machines = []
            for machine_id, machine_data in snapshot_data.items():
                if machine_data.get("cooling_required", False):
                    cooling_machines.append({
                        "machine_id": machine_id,
                        "cooling_required": True
                    })
            return cooling_machines
        
        return []
    
    def collect_cooling_products(self) -> List[str]:
        """냉각이 필요한 제품 수집"""
        # 1차: AAS Server
        products = self.collect_from_aas("/api/products/cooling-required")
        
        if products:
            logger.info(f"✅ Got {len(products)} cooling products from AAS Server")
            return products
        
        # 2차: 로컬 스냅샷 fallback
        logger.info("📂 Falling back to local snapshot for products")
        snapshot_data = self.collect_from_snapshot("T1", "products")
        
        if snapshot_data:
            cooling_products = []
            for product_id, product_data in snapshot_data.items():
                if product_data.get("requires_cooling", False):
                    cooling_products.append(product_id)
            return cooling_products
        
        # 3차: 하드코딩 fallback
        logger.warning("⚠️ Using hardcoded cooling products")
        return ["Product-B1", "Product-C1"]
    
    def collect_job_history(self, date: str, timepoint: str = "T4") -> List[Dict[str, Any]]:
        """작업 이력 수집"""
        # 1차: AAS Server
        jobs = self.collect_from_aas("/api/jobs/failed", params={"date": date})
        
        if jobs:
            logger.info(f"✅ Got {len(jobs)} failed jobs from AAS Server")
            return jobs
        
        # 2차: 로컬 스냅샷 fallback
        logger.info("📂 Falling back to local snapshot for jobs")
        jobs = self.collect_from_snapshot(timepoint, "jobs")
        
        return jobs or []
    
    def collect_operational_data(self, machine_id: str, timestamp: str) -> Optional[Dict[str, Any]]:
        """운영 데이터 수집"""
        # AAS Server에서 Submodel 조회
        submodel_id = f"urn:aas:sm:{machine_id}:OperationalData"
        operational_data = self.collect_from_aas(
            f"/submodels/{submodel_id}",
            params={"timestamp": timestamp}
        )
        
        if operational_data:
            logger.info(f"✅ Got operational data for {machine_id} at {timestamp}")
            return operational_data
        
        # Fallback to snapshot
        timepoint = self.map_timestamp_to_timepoint(timestamp)
        return self.collect_from_snapshot(timepoint, f"machines.{machine_id}")
    
    def map_timestamp_to_timepoint(self, timestamp: str) -> str:
        """timestamp를 timepoint로 변환"""
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
    
    def filter_failed_jobs(self, jobs: List[Dict[str, Any]],
                          cooling_products: List[str],
                          cooling_machines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """실패한 작업 필터링"""
        failed_jobs = []
        
        # cooling_machines에서 machine_id 추출
        cooling_machine_ids = []
        if cooling_machines:
            for machine in cooling_machines:
                if isinstance(machine, dict):
                    cooling_machine_ids.append(machine.get("machine_id"))
                else:
                    cooling_machine_ids.append(machine)
        
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
    
    # ===== Goal 4: Product Tracking Methods =====
    
    def collect_product_location(self, product_id: str, 
                                include_history: bool = False,
                                timepoint: str = "T4") -> Optional[Dict[str, Any]]:
        """제품 위치 수집 (Goal 4)"""
        # 1차: AAS Server
        if self.aas_client:
            location = self.aas_client.get_product_location(
                product_id, include_history, timepoint
            )
            if location:
                logger.info(f"✅ Got location for {product_id} from AAS Server")
                return location
        
        # 2차: 로컬 스냅샷 fallback
        logger.info(f"📂 Falling back to local snapshot for {product_id} location")
        
        # 현재 위치 찾기
        current_location = self._find_product_in_snapshot(product_id, timepoint)
        
        result = {
            "product_id": product_id,
            "current_location": current_location,
            "timepoint": timepoint
        }
        
        # 이력 조회
        if include_history:
            history = []
            for tp in ["T1", "T2", "T3", "T4", "T5"]:
                loc = self._find_product_in_snapshot(product_id, tp)
                if loc:
                    history.append({
                        "timepoint": tp,
                        "location": loc
                    })
            result["history"] = history
        
        return result
    
    def _find_product_in_snapshot(self, product_id: str, timepoint: str) -> Dict[str, Any]:
        """스냅샷에서 제품 위치 찾기"""
        jobs = self.collect_from_snapshot(timepoint, "jobs")
        machines = self.collect_from_snapshot(timepoint, "machines")
        
        if not jobs:
            return {
                "Zone": "Storage",
                "Station": "Warehouse",
                "Status": "STORED",
                "RFID": f"TAG-{product_id.replace('Product-', '')}"
            }
        
        # 제품의 작업 찾기
        for job in jobs:
            if job.get("product_id") == product_id:
                machine_id = job.get("machine_id")
                machine = machines.get(machine_id, {}) if machines else {}
                
                location = machine.get("location", {})
                status = job.get("status")
                
                # 상태에 따른 위치 결정
                if status in ["RUNNING", "FAILED"]:
                    station = machine_id
                    tracking_status = "ERROR" if status == "FAILED" else "PROCESSING"
                elif status == "COMPLETED":
                    station = "QC_Station"
                    tracking_status = "COMPLETED"
                else:
                    station = "Buffer_Area"
                    tracking_status = "WAITING"
                
                return {
                    "Zone": location.get("zone", "Unknown"),
                    "Station": station,
                    "Coordinates": location.get("coordinates", "0,0,0"),
                    "Status": tracking_status,
                    "JobId": job.get("job_id", ""),
                    "Progress": str(job.get("progress", 0)),
                    "RFID": f"TAG-{product_id.replace('Product-', '')}",
                    "LastUpdate": job.get("start_time", "")
                }
        
        # 작업이 없는 경우
        return {
            "Zone": "Storage",
            "Station": "Warehouse",
            "Status": "STORED",
            "RFID": f"TAG-{product_id.replace('Product-', '')}"
        }
    
    def collect_all_product_tracking(self, timepoint: str = "T4") -> List[Dict[str, Any]]:
        """모든 제품의 현재 위치 수집"""
        # 1차: AAS Server
        if self.aas_client:
            tracking = self.aas_client.get_all_product_tracking(timepoint)
            if tracking:
                logger.info(f"✅ Got tracking for {len(tracking)} products from AAS Server")
                return tracking
        
        # 2차: 로컬 스냅샷 fallback
        logger.info("📂 Falling back to local snapshot for all product tracking")
        
        # 스냅샷에서 모든 제품 찾기
        products = self.collect_from_snapshot("T1", "products")
        if not products:
            return []
        
        tracking_data = []
        for product_id in products.keys():
            location = self._find_product_in_snapshot(product_id, timepoint)
            if location:
                location["product_id"] = product_id
                tracking_data.append(location)
        
        return tracking_data


if __name__ == "__main__":
    # 테스트
    print("=" * 60)
    print("🔍 Testing Data Collector v2")
    print("=" * 60)
    
    collector = DataCollectorV2()
    
    # 냉각 기계 수집
    print("\n🏭 Collecting cooling machines:")
    machines = collector.collect_machines_with_cooling()
    print(f"  Found {len(machines)} machines")
    for machine in machines:
        print(f"    - {machine.get('machine_id')}")
    
    # 냉각 제품 수집
    print("\n❄️ Collecting cooling products:")
    products = collector.collect_cooling_products()
    print(f"  Found {len(products)} products")
    for product in products:
        print(f"    - {product}")
    
    # 실패 작업 수집
    print("\n❌ Collecting failed jobs:")
    jobs = collector.collect_job_history("2025-07-17")
    print(f"  Found {len(jobs)} jobs")
    for job in jobs:
        print(f"    - {job.get('job_id')}: {job.get('failure_reason')}")
    
    # 필터링 테스트
    if machines and products and jobs:
        print("\n🔍 Testing filter:")
        filtered = collector.filter_failed_jobs(jobs, products, machines)
        print(f"  Filtered: {len(filtered)} failed jobs with cooling")
    
    # Goal 4: 제품 위치 추적 테스트
    print("\n" + "=" * 60)
    print("📍 Testing Goal 4: Product Tracking")
    print("=" * 60)
    
    # 특정 제품 위치
    print("\n📦 Product-B1 location:")
    location = collector.collect_product_location("Product-B1", include_history=True)
    if location:
        current = location.get("current_location", {})
        print(f"  Current: Zone={current.get('Zone')}, Station={current.get('Station')}")
        print(f"  Status: {current.get('Status')}")
        if "history" in location:
            print(f"  History: {len(location['history'])} timepoints")
    
    # 모든 제품 추적
    print("\n🌍 All product tracking:")
    all_tracking = collector.collect_all_product_tracking("T4")
    print(f"  Tracking {len(all_tracking)} products")
    for track in all_tracking:
        print(f"    - {track.get('product_id')}: {track.get('Zone')} / {track.get('Station')}")