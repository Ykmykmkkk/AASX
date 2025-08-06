#!/usr/bin/env python3
"""
AAS Client v2
REST API 클라이언트 for AAS Server
"""

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    import urllib.request
    import urllib.parse
    import json as json_module
    
from typing import Dict, List, Optional, Any
import logging
from urllib.parse import quote

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AASClient:
    """AAS REST API 클라이언트"""
    
    def __init__(self, base_url: str = "http://localhost:5001"):
        self.base_url = base_url
        if HAS_REQUESTS:
            self.session = requests.Session()
            self.session.headers.update({
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            })
        else:
            self.session = None
            logger.warning("⚠️ Running in fallback mode without requests")
    
    def health_check(self) -> bool:
        """서버 상태 확인"""
        if not HAS_REQUESTS:
            return False
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def get_shells(self) -> List[Dict[str, Any]]:
        """모든 Shell 조회"""
        if not HAS_REQUESTS:
            logger.warning("⚠️ Cannot get shells without requests module")
            return []
        try:
            response = self.session.get(f"{self.base_url}/shells")
            response.raise_for_status()
            shells = response.json()
            logger.info(f"Retrieved {len(shells)} shells")
            return shells
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get shells: {e}")
            return []
    
    def get_shell(self, aas_id: str) -> Optional[Dict[str, Any]]:
        """특정 Shell 조회"""
        try:
            # URL 인코딩
            encoded_id = quote(aas_id, safe='')
            response = self.session.get(f"{self.base_url}/shells/{encoded_id}")
            response.raise_for_status()
            shell = response.json()
            logger.info(f"Retrieved shell: {aas_id}")
            return shell
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get shell {aas_id}: {e}")
            return None
    
    def get_shell_submodels(self, aas_id: str) -> List[Dict[str, Any]]:
        """Shell의 Submodel 목록 조회"""
        try:
            encoded_id = quote(aas_id, safe='')
            response = self.session.get(f"{self.base_url}/shells/{encoded_id}/submodels")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get submodels for {aas_id}: {e}")
            return []
    
    def get_submodel(self, submodel_id: str, 
                    timestamp: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Submodel 조회"""
        try:
            encoded_id = quote(submodel_id, safe='')
            url = f"{self.base_url}/submodels/{encoded_id}"
            
            params = {}
            if timestamp:
                params['timestamp'] = timestamp
                logger.info(f"Requesting submodel at timestamp: {timestamp}")
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            submodel = response.json()
            logger.info(f"Retrieved submodel: {submodel_id}")
            return submodel
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get submodel {submodel_id}: {e}")
            return None
    
    def get_cooling_machines(self) -> List[Dict[str, Any]]:
        """냉각이 필요한 기계 조회"""
        try:
            response = self.session.get(f"{self.base_url}/api/machines/cooling-required")
            response.raise_for_status()
            machines = response.json()
            logger.info(f"Retrieved {len(machines)} cooling machines")
            return machines
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get cooling machines: {e}")
            return []
    
    def get_failed_jobs(self, date: str = "2025-07-17") -> List[Dict[str, Any]]:
        """실패한 작업 조회"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/jobs/failed",
                params={"date": date}
            )
            response.raise_for_status()
            jobs = response.json()
            logger.info(f"Retrieved {len(jobs)} failed jobs for {date}")
            return jobs
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get failed jobs: {e}")
            return []
    
    def get_cooling_products(self) -> List[str]:
        """냉각이 필요한 제품 조회"""
        try:
            response = self.session.get(f"{self.base_url}/api/products/cooling-required")
            response.raise_for_status()
            products = response.json()
            logger.info(f"Retrieved {len(products)} cooling products")
            return products
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get cooling products: {e}")
            return []
    
    def get_product_location(self, product_id: str, 
                           include_history: bool = False,
                           timepoint: str = "T4") -> Optional[Dict[str, Any]]:
        """제품 위치 조회 (Goal 4)"""
        try:
            params = {
                "history": "true" if include_history else "false",
                "timepoint": timepoint
            }
            response = self.session.get(
                f"{self.base_url}/api/products/{product_id}/location",
                params=params
            )
            response.raise_for_status()
            location = response.json()
            logger.info(f"Retrieved location for {product_id} at {timepoint}")
            return location
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get product location: {e}")
            return None
    
    def get_all_product_tracking(self, timepoint: str = "T4") -> List[Dict[str, Any]]:
        """모든 제품의 현재 위치 조회"""
        try:
            params = {"timepoint": timepoint}
            response = self.session.get(
                f"{self.base_url}/api/products/tracking",
                params=params
            )
            response.raise_for_status()
            tracking = response.json()
            logger.info(f"Retrieved tracking for {len(tracking)} products at {timepoint}")
            return tracking
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get all product tracking: {e}")
            return []
    
    def call_api(self, endpoint: str, method: str = "GET", 
                params: Optional[Dict] = None, 
                data: Optional[Dict] = None) -> Optional[Any]:
        """일반 API 호출"""
        if not HAS_REQUESTS:
            logger.warning("⚠️ Cannot call API without requests module")
            return None
        try:
            url = f"{self.base_url}{endpoint}"
            
            if method == "GET":
                response = self.session.get(url, params=params)
            elif method == "POST":
                response = self.session.post(url, json=data, params=params)
            elif method == "PUT":
                response = self.session.put(url, json=data, params=params)
            elif method == "DELETE":
                response = self.session.delete(url, params=params)
            else:
                logger.error(f"Unsupported method: {method}")
                return None
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API call failed: {endpoint} - {e}")
            return None


if __name__ == "__main__":
    # 테스트
    client = AASClient()
    
    print("🔍 Testing AAS Client...")
    print("-" * 40)
    
    # 헬스 체크
    if client.health_check():
        print("✅ Server is healthy")
    else:
        print("❌ Server is not responding")
        exit(1)
    
    # Shell 조회
    print("\n📦 Getting shells...")
    shells = client.get_shells()
    print(f"  Found {len(shells)} shells")
    
    if shells:
        # 첫 번째 Shell 상세 조회
        first_shell = shells[0]
        shell_id = first_shell.get("id")
        print(f"\n📋 Getting shell details: {shell_id}")
        shell = client.get_shell(shell_id)
        if shell:
            print(f"  idShort: {shell.get('idShort')}")
            print(f"  Submodels: {len(shell.get('submodels', []))}")
    
    # 냉각 기계 조회
    print("\n🏭 Getting cooling machines...")
    cooling_machines = client.get_cooling_machines()
    print(f"  Found {len(cooling_machines)} machines")
    for machine in cooling_machines:
        print(f"    - {machine.get('machine_id')}")
    
    # 냉각 제품 조회
    print("\n❄️ Getting cooling products...")
    cooling_products = client.get_cooling_products()
    print(f"  Found {len(cooling_products)} products")
    for product in cooling_products:
        print(f"    - {product}")
    
    # 실패 작업 조회
    print("\n❌ Getting failed jobs...")
    failed_jobs = client.get_failed_jobs("2025-07-17")
    print(f"  Found {len(failed_jobs)} failed jobs")
    for job in failed_jobs:
        print(f"    - {job.get('job_id')}: {job.get('failure_reason')}")
    
    # Goal 4: 제품 위치 추적 테스트
    print("\n📍 Testing Product Tracking (Goal 4)...")
    
    # 특정 제품 위치 조회
    print("\n  Getting location for Product-B1...")
    location = client.get_product_location("Product-B1", include_history=True)
    if location:
        current = location.get("current_location", {})
        print(f"    Current: Zone={current.get('Zone')}, Station={current.get('Station')}")
        print(f"    Status: {current.get('Status')}")
        if "history" in location:
            print(f"    History: {len(location['history'])} timepoints")
    
    # 모든 제품 추적
    print("\n  Getting all product tracking...")
    all_tracking = client.get_all_product_tracking("T4")
    print(f"    Tracking {len(all_tracking)} products")
    for track in all_tracking[:3]:  # 처음 3개만 출력
        print(f"      - {track.get('product_id')}: {track.get('Zone')} / {track.get('Station')}")