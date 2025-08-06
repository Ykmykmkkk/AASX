#!/usr/bin/env python3
"""
Snapshot Data Generator for v6 AAS Integration
냉각 실패 시나리오에 대한 5개 시점 데이터 생성
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
import random

class SnapshotGenerator:
    def __init__(self, base_path: str = "./"):
        self.base_path = base_path
        self.snapshot_dir = os.path.join(base_path, "snapshots")
        os.makedirs(self.snapshot_dir, exist_ok=True)
        
        # 5개 시점 정의
        self.timepoints = {
            "T1": datetime(2025, 7, 17, 8, 0, 0),   # 작업 시작
            "T2": datetime(2025, 7, 17, 10, 0, 0),  # 정상 작동
            "T3": datetime(2025, 7, 17, 12, 0, 0),  # 이상 징후
            "T4": datetime(2025, 7, 17, 14, 0, 0),  # 냉각 실패
            "T5": datetime(2025, 7, 17, 16, 0, 0),  # 복구 후 재시작
        }
        
        # 기계 정보
        self.machines = {
            "CNC001": {
                "name": "DMG MORI DMU 50",
                "type": "CNC",
                "cooling_required": True,
                "zone": "Zone-A",
                "coordinates": "10.5,20.3,0"
            },
            "CNC002": {
                "name": "HAAS VF-2SS",
                "type": "CNC", 
                "cooling_required": True,
                "zone": "Zone-A",
                "coordinates": "15.2,20.3,0"
            },
            "CNC003": {
                "name": "Mazak VARIAXIS i-700",
                "type": "CNC",
                "cooling_required": False,
                "zone": "Zone-B",
                "coordinates": "30.1,10.5,0"
            },
            "3DP001": {
                "name": "Stratasys F370",
                "type": "3D_PRINTER",
                "cooling_required": False,
                "zone": "Zone-C",
                "coordinates": "40.0,30.0,0"
            }
        }
        
        # 제품 정보
        self.products = {
            "Product-B1": {
                "name": "Aluminum Housing",
                "requires_cooling": True,
                "normal_temp_range": [20, 25],
                "critical_temp": 30
            },
            "Product-C1": {
                "name": "Titanium Component",
                "requires_cooling": True,
                "normal_temp_range": [18, 23],
                "critical_temp": 28
            },
            "Product-A1": {
                "name": "Precision Gear",
                "requires_cooling": False,
                "normal_temp_range": [15, 35],
                "critical_temp": 45
            }
        }
        
    def generate_machine_status(self, machine_id: str, timepoint: str) -> Dict[str, Any]:
        """시점별 기계 상태 생성"""
        machine = self.machines[machine_id]
        
        # 시점별 상태 매핑
        status_map = {
            "T1": {"CNC001": "IDLE", "CNC002": "IDLE", "CNC003": "IDLE", "3DP001": "IDLE"},
            "T2": {"CNC001": "RUNNING", "CNC002": "RUNNING", "CNC003": "RUNNING", "3DP001": "IDLE"},
            "T3": {"CNC001": "WARNING", "CNC002": "WARNING", "CNC003": "RUNNING", "3DP001": "IDLE"},
            "T4": {"CNC001": "ERROR", "CNC002": "ERROR", "CNC003": "RUNNING", "3DP001": "IDLE"},
            "T5": {"CNC001": "RUNNING", "CNC002": "IDLE", "CNC003": "IDLE", "3DP001": "RUNNING"}
        }
        
        health_map = {
            "T1": {"CNC001": 95, "CNC002": 93, "CNC003": 90, "3DP001": 88},
            "T2": {"CNC001": 92, "CNC002": 90, "CNC003": 88, "3DP001": 88},
            "T3": {"CNC001": 75, "CNC002": 70, "CNC003": 85, "3DP001": 88},
            "T4": {"CNC001": 45, "CNC002": 40, "CNC003": 83, "3DP001": 88},
            "T5": {"CNC001": 80, "CNC002": 85, "CNC003": 82, "3DP001": 87}
        }
        
        return {
            "machine_id": machine_id,
            "name": machine["name"],
            "type": machine["type"],
            "status": status_map[timepoint][machine_id],
            "health_score": health_map[timepoint][machine_id],
            "cooling_required": machine["cooling_required"],
            "location": {
                "zone": machine["zone"],
                "coordinates": machine["coordinates"]
            },
            "timestamp": self.timepoints[timepoint].isoformat()
        }
    
    def generate_job_data(self, timepoint: str) -> List[Dict[str, Any]]:
        """시점별 작업 데이터 생성"""
        jobs = []
        
        if timepoint in ["T1", "T2"]:
            # 작업 시작 및 정상 작동
            jobs.extend([
                {
                    "job_id": "JOB-001",
                    "product_id": "Product-B1",
                    "machine_id": "CNC002",
                    "status": "IN_PROGRESS" if timepoint == "T2" else "PENDING",
                    "start_time": self.timepoints["T1"].isoformat(),
                    "progress": 40 if timepoint == "T2" else 0,
                    "current_operation": "CUTTING" if timepoint == "T2" else "SETUP"
                },
                {
                    "job_id": "JOB-002", 
                    "product_id": "Product-C1",
                    "machine_id": "CNC001",
                    "status": "IN_PROGRESS" if timepoint == "T2" else "PENDING",
                    "start_time": self.timepoints["T1"].isoformat(),
                    "progress": 35 if timepoint == "T2" else 0,
                    "current_operation": "CUTTING" if timepoint == "T2" else "SETUP"
                },
                {
                    "job_id": "JOB-004",
                    "product_id": "Product-A1",
                    "machine_id": "CNC003",
                    "status": "IN_PROGRESS" if timepoint == "T2" else "PENDING",
                    "start_time": self.timepoints["T1"].isoformat(),
                    "progress": 30 if timepoint == "T2" else 0,
                    "current_operation": "CUTTING" if timepoint == "T2" else "SETUP"
                }
            ])
            
        elif timepoint == "T3":
            # 이상 징후 발생
            jobs.extend([
                {
                    "job_id": "JOB-001",
                    "product_id": "Product-B1",
                    "machine_id": "CNC002",
                    "status": "IN_PROGRESS",
                    "start_time": self.timepoints["T1"].isoformat(),
                    "progress": 65,
                    "current_operation": "COOLING",
                    "warning": "Temperature rising above normal"
                },
                {
                    "job_id": "JOB-002",
                    "product_id": "Product-C1",
                    "machine_id": "CNC001",
                    "status": "IN_PROGRESS",
                    "start_time": self.timepoints["T1"].isoformat(),
                    "progress": 60,
                    "current_operation": "COOLING",
                    "warning": "Coolant flow decreasing"
                },
                {
                    "job_id": "JOB-004",
                    "product_id": "Product-A1",
                    "machine_id": "CNC003",
                    "status": "IN_PROGRESS",
                    "start_time": self.timepoints["T1"].isoformat(),
                    "progress": 55,
                    "current_operation": "ASSEMBLY"
                }
            ])
            
        elif timepoint == "T4":
            # 냉각 실패
            jobs.extend([
                {
                    "job_id": "JOB-001",
                    "product_id": "Product-B1",
                    "machine_id": "CNC002",
                    "status": "FAILED",
                    "start_time": self.timepoints["T1"].isoformat(),
                    "end_time": self.timepoints["T4"].isoformat(),
                    "progress": 65,
                    "current_operation": "COOLING",
                    "failure_reason": "cooling_system_error",
                    "error_details": "Temperature exceeded critical threshold"
                },
                {
                    "job_id": "JOB-002",
                    "product_id": "Product-C1",
                    "machine_id": "CNC001",
                    "status": "FAILED",
                    "start_time": self.timepoints["T1"].isoformat(),
                    "end_time": self.timepoints["T4"].isoformat(),
                    "progress": 60,
                    "current_operation": "COOLING",
                    "failure_reason": "temperature_exceeded",
                    "error_details": "Coolant pump failure"
                },
                {
                    "job_id": "JOB-003",
                    "product_id": "Product-B1",
                    "machine_id": "CNC002",
                    "status": "FAILED",
                    "start_time": self.timepoints["T2"].isoformat(),
                    "end_time": self.timepoints["T4"].isoformat(),
                    "progress": 45,
                    "current_operation": "COOLING",
                    "failure_reason": "coolant_flow_insufficient",
                    "error_details": "Coolant flow rate below minimum"
                },
                {
                    "job_id": "JOB-004",
                    "product_id": "Product-A1",
                    "machine_id": "CNC003",
                    "status": "COMPLETED",
                    "start_time": self.timepoints["T1"].isoformat(),
                    "end_time": self.timepoints["T4"].isoformat(),
                    "progress": 100,
                    "current_operation": "COMPLETED"
                }
            ])
            
        elif timepoint == "T5":
            # 복구 후 재시작
            jobs.extend([
                {
                    "job_id": "JOB-006",
                    "product_id": "Product-B1",
                    "machine_id": "CNC001",
                    "status": "IN_PROGRESS",
                    "start_time": self.timepoints["T5"].isoformat(),
                    "progress": 15,
                    "current_operation": "CUTTING"
                },
                {
                    "job_id": "JOB-005",
                    "product_id": "Product-D1",
                    "machine_id": "3DP001",
                    "status": "IN_PROGRESS",
                    "start_time": self.timepoints["T5"].isoformat(),
                    "progress": 10,
                    "current_operation": "PRINTING"
                }
            ])
            
        return jobs
    
    def generate_sensor_data(self, machine_id: str, timepoint: str) -> Dict[str, Any]:
        """시점별 센서 데이터 생성"""
        timestamp = self.timepoints[timepoint]
        
        # 기본 센서 값
        base_values = {
            "CNC001": {"temp": 22, "pressure": 5.0, "vibration": 2.0, "coolant_flow": 10.0},
            "CNC002": {"temp": 23, "pressure": 5.2, "vibration": 2.1, "coolant_flow": 9.8},
            "CNC003": {"temp": 25, "pressure": 4.8, "vibration": 1.9, "coolant_flow": 0},
            "3DP001": {"temp": 20, "pressure": 1.0, "vibration": 0.5, "coolant_flow": 0}
        }
        
        # 시점별 변화
        if timepoint == "T1":
            # 정상
            multiplier = 1.0
        elif timepoint == "T2":
            # 약간 상승
            multiplier = 1.1
        elif timepoint == "T3":
            # 이상 징후
            multiplier = 1.4 if machine_id in ["CNC001", "CNC002"] else 1.1
        elif timepoint == "T4":
            # 임계치 초과
            multiplier = 1.8 if machine_id in ["CNC001", "CNC002"] else 1.1
        elif timepoint == "T5":
            # 복구
            multiplier = 1.05
            
        base = base_values[machine_id]
        
        # 시계열 데이터 생성 (10분 간격)
        timeseries = []
        for i in range(12):  # 2시간 데이터
            time = timestamp - timedelta(minutes=110) + timedelta(minutes=i*10)
            noise = random.uniform(0.95, 1.05)
            
            timeseries.append({
                "timestamp": time.isoformat(),
                "temperature": round(base["temp"] * multiplier * noise, 1),
                "pressure": round(base["pressure"] * noise, 2),
                "vibration": round(base["vibration"] * noise, 2),
                "coolant_flow": round(base["coolant_flow"] * multiplier * noise, 1) if base["coolant_flow"] > 0 else 0
            })
            
        return {
            "machine_id": machine_id,
            "timepoint": timepoint,
            "timestamp": timestamp.isoformat(),
            "summary": {
                "avg_temperature": round(base["temp"] * multiplier, 1),
                "avg_pressure": round(base["pressure"], 2),
                "avg_vibration": round(base["vibration"], 2),
                "avg_coolant_flow": round(base["coolant_flow"] * multiplier, 1) if base["coolant_flow"] > 0 else 0,
                "anomaly_score": 0.8 if timepoint == "T4" and machine_id in ["CNC001", "CNC002"] else 0.2
            },
            "timeseries": timeseries
        }
    
    def generate_snapshot(self, timepoint: str) -> Dict[str, Any]:
        """특정 시점의 전체 스냅샷 생성"""
        snapshot = {
            "metadata": {
                "timepoint": timepoint,
                "timestamp": self.timepoints[timepoint].isoformat(),
                "description": self.get_timepoint_description(timepoint),
                "version": "1.0"
            },
            "machines": {},
            "jobs": self.generate_job_data(timepoint),
            "sensor_data": {},
            "products": self.products
        }
        
        # 각 기계의 상태와 센서 데이터 생성
        for machine_id in self.machines:
            snapshot["machines"][machine_id] = self.generate_machine_status(machine_id, timepoint)
            snapshot["sensor_data"][machine_id] = self.generate_sensor_data(machine_id, timepoint)
            
        return snapshot
    
    def get_timepoint_description(self, timepoint: str) -> str:
        """시점별 설명"""
        descriptions = {
            "T1": "작업 시작 - 모든 시스템 정상",
            "T2": "정상 작동 - 작업 진행 중",
            "T3": "이상 징후 - 온도 상승 및 냉각 시스템 경고",
            "T4": "냉각 실패 - 임계 온도 초과로 작업 실패",
            "T5": "복구 후 재시작 - 시스템 복구 및 새 작업 시작"
        }
        return descriptions.get(timepoint, "Unknown timepoint")
    
    def save_snapshot(self, timepoint: str, snapshot: Dict[str, Any]):
        """스냅샷을 파일로 저장"""
        filename = f"snapshot_{timepoint}_{snapshot['metadata']['timestamp'].replace(':', '-')}.json"
        filepath = os.path.join(self.snapshot_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(snapshot, f, indent=2, ensure_ascii=False)
            
        print(f"✅ Saved {timepoint}: {filepath}")
        
    def generate_all_snapshots(self):
        """모든 시점의 스냅샷 생성"""
        print("🔄 Generating snapshots for cooling failure scenario...")
        print("=" * 60)
        
        for timepoint in self.timepoints:
            snapshot = self.generate_snapshot(timepoint)
            self.save_snapshot(timepoint, snapshot)
            print(f"   - {timepoint}: {self.get_timepoint_description(timepoint)}")
            
        print("=" * 60)
        print(f"✅ Generated {len(self.timepoints)} snapshots in {self.snapshot_dir}")
        
        # 메타데이터 파일 생성
        self.save_metadata()
        
    def save_metadata(self):
        """스냅샷 메타데이터 파일 생성"""
        metadata = {
            "scenario": "Cooling System Failure",
            "timepoints": {
                tp: {
                    "timestamp": ts.isoformat(),
                    "description": self.get_timepoint_description(tp)
                }
                for tp, ts in self.timepoints.items()
            },
            "machines": self.machines,
            "products": self.products,
            "generated_at": datetime.now().isoformat()
        }
        
        filepath = os.path.join(self.snapshot_dir, "metadata.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
            
        print(f"📄 Saved metadata: {filepath}")


if __name__ == "__main__":
    generator = SnapshotGenerator()
    generator.generate_all_snapshots()