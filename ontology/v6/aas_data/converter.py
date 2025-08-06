#!/usr/bin/env python3
"""
Snapshot to AAS Converter
스냅샷 데이터를 AAS Shell/Submodel 구조로 변환
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any
import sys
sys.path.append('../src')

from standards.aas_models import (
    AssetAdministrationShell,
    AssetInformation,
    Submodel,
    Property,
    SubmodelElementCollection,
    Reference,
    Key
)


class SnapshotToAASConverter:
    """스냅샷 데이터를 AAS 표준 형식으로 변환"""
    
    def __init__(self, snapshot_dir: str = "../snapshots", output_dir: str = "./"):
        self.snapshot_dir = snapshot_dir
        self.output_dir = output_dir
        self.shells_dir = os.path.join(output_dir, "shells")
        self.submodels_dir = os.path.join(output_dir, "submodels")
        
        # 디렉토리 생성
        os.makedirs(self.shells_dir, exist_ok=True)
        os.makedirs(self.submodels_dir, exist_ok=True)
        
    def convert_all_snapshots(self):
        """모든 스냅샷을 AAS 형식으로 변환"""
        print("🔄 Converting snapshots to AAS format...")
        
        # 각 시점별로 변환
        for timepoint in ["T1", "T2", "T3", "T4", "T5"]:
            snapshot_file = self.find_snapshot_file(timepoint)
            if snapshot_file:
                print(f"\n📁 Processing {timepoint}...")
                self.convert_snapshot(snapshot_file, timepoint)
        
        print("\n✅ Conversion complete!")
    
    def find_snapshot_file(self, timepoint: str) -> str:
        """특정 시점의 스냅샷 파일 찾기"""
        files = os.listdir(self.snapshot_dir)
        for file in files:
            if file.startswith(f"snapshot_{timepoint}_") and file.endswith(".json"):
                return os.path.join(self.snapshot_dir, file)
        return None
    
    def convert_snapshot(self, snapshot_file: str, timepoint: str):
        """단일 스냅샷을 AAS 형식으로 변환"""
        with open(snapshot_file, 'r', encoding='utf-8') as f:
            snapshot = json.load(f)
        
        # 기계 변환
        for machine_id, machine_data in snapshot.get("machines", {}).items():
            self.convert_machine(machine_id, machine_data, snapshot, timepoint)
        
        # 제품 변환 (T1에서만)
        if timepoint == "T1":
            for product_id, product_data in snapshot.get("products", {}).items():
                self.convert_product(product_id, product_data)
        
        # 제품 위치 추적 데이터 생성 (현재 시점만 - T4 중심)
        # T4 시점만 TrackingInfo 생성 (Goal 4 단순화)
        if timepoint == "T4":
            jobs = snapshot.get("jobs", [])
            machines = snapshot.get("machines", {})
            products_in_jobs = set()
            
            for job in jobs:
                product_id = job.get("product_id")
                machine_id = job.get("machine_id")
                if product_id and machine_id:
                    products_in_jobs.add(product_id)
                    machine_data = machines.get(machine_id, {})
                    tracking_info = self.create_product_tracking_data(
                        product_id, job, machine_data, timepoint
                    )
                    # 현재 위치만 저장 (시점 suffix 제거)
                    self.save_submodel(tracking_info, f"{product_id}_TrackingInfo")
            
            # 작업에 없는 제품들의 기본 위치 데이터
            all_products = snapshot.get("products", {}).keys() if timepoint == "T1" else []
            for product_id in all_products:
                if product_id not in products_in_jobs:
                    tracking_info = self.create_product_tracking_data(
                        product_id, None, {}, timepoint
                    )
                    self.save_submodel(tracking_info, f"{product_id}_TrackingInfo")
    
    def convert_machine(self, machine_id: str, machine_data: Dict, 
                       snapshot: Dict, timepoint: str):
        """기계 데이터를 AAS Shell과 Submodel로 변환"""
        
        # 1. Machine Shell 생성
        shell = {
            "modelType": "AssetAdministrationShell",
            "id": f"urn:aas:Machine:{machine_id}",
            "idShort": machine_id,
            "assetInformation": {
                "assetKind": "Instance",
                "globalAssetId": f"urn:company:machines:{machine_id.lower()}"
            },
            "submodels": [
                {
                    "type": "ModelReference",
                    "keys": [{
                        "type": "Submodel",
                        "value": f"urn:aas:sm:{machine_id}:Nameplate"
                    }]
                },
                {
                    "type": "ModelReference",
                    "keys": [{
                        "type": "Submodel",
                        "value": f"urn:aas:sm:{machine_id}:TechnicalData"
                    }]
                },
                {
                    "type": "ModelReference",
                    "keys": [{
                        "type": "Submodel",
                        "value": f"urn:aas:sm:{machine_id}:OperationalData"
                    }]
                },
                {
                    "type": "ModelReference",
                    "keys": [{
                        "type": "Submodel",
                        "value": f"urn:aas:sm:{machine_id}:JobHistory"
                    }]
                }
            ]
        }
        
        # Shell 저장 (T1에서만)
        if timepoint == "T1":
            shell_file = os.path.join(self.shells_dir, f"{machine_id}.json")
            with open(shell_file, 'w', encoding='utf-8') as f:
                json.dump(shell, f, indent=2, ensure_ascii=False)
            print(f"  ✓ Shell: {machine_id}")
        
        # 2. Nameplate Submodel (정적, T1에서만)
        if timepoint == "T1":
            nameplate = {
                "modelType": "Submodel",
                "id": f"urn:aas:sm:{machine_id}:Nameplate",
                "idShort": "Nameplate",
                "semanticId": {
                    "type": "ExternalReference",
                    "keys": [{
                        "type": "GlobalReference",
                        "value": "0173-1#02-AAO677#002"  # ZVEI Digital Nameplate
                    }]
                },
                "submodelElements": [
                    {
                        "modelType": "Property",
                        "idShort": "ManufacturerName",
                        "value": machine_data.get("name", "").split()[0],
                        "valueType": "xs:string"
                    },
                    {
                        "modelType": "Property",
                        "idShort": "ProductDesignation",
                        "value": machine_data.get("name", ""),
                        "valueType": "xs:string"
                    },
                    {
                        "modelType": "Property",
                        "idShort": "SerialNumber",
                        "value": f"SN-{machine_id}",
                        "valueType": "xs:string"
                    }
                ]
            }
            self.save_submodel(nameplate, f"{machine_id}_Nameplate")
        
        # 3. TechnicalData Submodel (정적, T1에서만)
        if timepoint == "T1":
            technical = {
                "modelType": "Submodel",
                "id": f"urn:aas:sm:{machine_id}:TechnicalData",
                "idShort": "TechnicalData",
                "submodelElements": [
                    {
                        "modelType": "Property",
                        "idShort": "MachineType",
                        "value": machine_data.get("type", ""),
                        "valueType": "xs:string"
                    },
                    {
                        "modelType": "Property",
                        "idShort": "CoolingRequired",
                        "value": str(machine_data.get("cooling_required", False)).lower(),
                        "valueType": "xs:boolean"
                    },
                    {
                        "modelType": "Property",
                        "idShort": "Zone",
                        "value": machine_data.get("location", {}).get("zone", ""),
                        "valueType": "xs:string"
                    },
                    {
                        "modelType": "Property",
                        "idShort": "Coordinates",
                        "value": machine_data.get("location", {}).get("coordinates", ""),
                        "valueType": "xs:string"
                    }
                ]
            }
            self.save_submodel(technical, f"{machine_id}_TechnicalData")
        
        # 4. OperationalData Submodel (동적, 모든 시점)
        sensor_data = snapshot.get("sensor_data", {}).get(machine_id, {})
        operational = {
            "modelType": "Submodel",
            "id": f"urn:aas:sm:{machine_id}:OperationalData",
            "idShort": "OperationalData",
            "semanticId": {
                "type": "ExternalReference",
                "keys": [{
                    "type": "GlobalReference",
                    "value": "0173-1#02-AAV232#002"  # Operational Data
                }]
            },
            "submodelElements": [
                {
                    "modelType": "Property",
                    "idShort": "Status",
                    "value": machine_data.get("status", "IDLE"),
                    "valueType": "xs:string",
                    "timestamp": machine_data.get("timestamp", "")
                },
                {
                    "modelType": "Property",
                    "idShort": "HealthScore",
                    "value": str(machine_data.get("health_score", 100)),
                    "valueType": "xs:integer"
                },
                {
                    "modelType": "Property",
                    "idShort": "Temperature",
                    "value": str(sensor_data.get("summary", {}).get("avg_temperature", 20)),
                    "valueType": "xs:float",
                    "unit": "°C"
                },
                {
                    "modelType": "Property",
                    "idShort": "CoolantFlow",
                    "value": str(sensor_data.get("summary", {}).get("avg_coolant_flow", 0)),
                    "valueType": "xs:float",
                    "unit": "L/min"
                },
                {
                    "modelType": "Property",
                    "idShort": "Pressure",
                    "value": str(sensor_data.get("summary", {}).get("avg_pressure", 5)),
                    "valueType": "xs:float",
                    "unit": "bar"
                },
                {
                    "modelType": "Property",
                    "idShort": "Vibration",
                    "value": str(sensor_data.get("summary", {}).get("avg_vibration", 2)),
                    "valueType": "xs:float",
                    "unit": "mm/s"
                }
            ]
        }
        self.save_submodel(operational, f"{machine_id}_OperationalData_{timepoint}")
        
        # 5. JobHistory Submodel (동적, 모든 시점)
        jobs = snapshot.get("jobs", [])
        machine_jobs = [job for job in jobs if job.get("machine_id") == machine_id]
        
        job_history = {
            "modelType": "Submodel",
            "id": f"urn:aas:sm:{machine_id}:JobHistory",
            "idShort": "JobHistory",
            "submodelElements": []
        }
        
        for job in machine_jobs:
            job_element = {
                "modelType": "SubmodelElementCollection",
                "idShort": job.get("job_id", ""),
                "value": [
                    {
                        "modelType": "Property",
                        "idShort": "ProductId",
                        "value": job.get("product_id", ""),
                        "valueType": "xs:string"
                    },
                    {
                        "modelType": "Property",
                        "idShort": "Status",
                        "value": job.get("status", ""),
                        "valueType": "xs:string"
                    },
                    {
                        "modelType": "Property",
                        "idShort": "Progress",
                        "value": str(job.get("progress", 0)),
                        "valueType": "xs:integer"
                    },
                    {
                        "modelType": "Property",
                        "idShort": "StartTime",
                        "value": job.get("start_time", ""),
                        "valueType": "xs:dateTime"
                    }
                ]
            }
            
            # 실패 이유 추가
            if job.get("status") == "FAILED":
                job_element["value"].extend([
                    {
                        "modelType": "Property",
                        "idShort": "FailureReason",
                        "value": job.get("failure_reason", ""),
                        "valueType": "xs:string"
                    },
                    {
                        "modelType": "Property",
                        "idShort": "ErrorDetails",
                        "value": job.get("error_details", ""),
                        "valueType": "xs:string"
                    }
                ])
            
            job_history["submodelElements"].append(job_element)
        
        if machine_jobs:
            self.save_submodel(job_history, f"{machine_id}_JobHistory_{timepoint}")
    
    def convert_product(self, product_id: str, product_data: Dict):
        """제품 데이터를 AAS Shell과 Submodel로 변환"""
        
        # Product Shell
        shell = {
            "modelType": "AssetAdministrationShell",
            "id": f"urn:aas:Product:{product_id}",
            "idShort": product_id,
            "assetInformation": {
                "assetKind": "Type",
                "globalAssetId": f"urn:company:products:{product_id.lower()}"
            },
            "submodels": [
                {
                    "type": "ModelReference",
                    "keys": [{
                        "type": "Submodel",
                        "value": f"urn:aas:sm:{product_id}:Specification"
                    }]
                },
                {
                    "type": "ModelReference",
                    "keys": [{
                        "type": "Submodel",
                        "value": f"urn:aas:sm:{product_id}:Requirements"
                    }]
                },
                {
                    "type": "ModelReference",
                    "keys": [{
                        "type": "Submodel",
                        "value": f"urn:aas:sm:{product_id}:TrackingInfo"
                    }]
                }
            ]
        }
        
        shell_file = os.path.join(self.shells_dir, f"{product_id}.json")
        with open(shell_file, 'w', encoding='utf-8') as f:
            json.dump(shell, f, indent=2, ensure_ascii=False)
        print(f"  ✓ Product Shell: {product_id}")
        
        # Specification Submodel
        specification = {
            "modelType": "Submodel",
            "id": f"urn:aas:sm:{product_id}:Specification",
            "idShort": "Specification",
            "submodelElements": [
                {
                    "modelType": "Property",
                    "idShort": "ProductName",
                    "value": product_data.get("name", ""),
                    "valueType": "xs:string"
                },
                {
                    "modelType": "Property",
                    "idShort": "CriticalTemperature",
                    "value": str(product_data.get("critical_temp", 30)),
                    "valueType": "xs:float",
                    "unit": "°C"
                }
            ]
        }
        self.save_submodel(specification, f"{product_id}_Specification")
        
        # Requirements Submodel
        requirements = {
            "modelType": "Submodel",
            "id": f"urn:aas:sm:{product_id}:Requirements",
            "idShort": "Requirements",
            "submodelElements": [
                {
                    "modelType": "Property",
                    "idShort": "RequiresCooling",
                    "value": str(product_data.get("requires_cooling", False)).lower(),
                    "valueType": "xs:boolean"
                },
                {
                    "modelType": "Property",
                    "idShort": "MinTemperature",
                    "value": str(product_data.get("normal_temp_range", [20, 25])[0]),
                    "valueType": "xs:float",
                    "unit": "°C"
                },
                {
                    "modelType": "Property",
                    "idShort": "MaxTemperature",
                    "value": str(product_data.get("normal_temp_range", [20, 25])[1]),
                    "valueType": "xs:float",
                    "unit": "°C"
                }
            ]
        }
        self.save_submodel(requirements, f"{product_id}_Requirements")
    
    def create_product_tracking_data(self, product_id: str, job_data: Dict, machine_data: Dict, timepoint: str):
        """제품 위치 추적 데이터 생성 (Goal 4용 - 단순화)"""
        # 작업 상태에 따른 위치 결정
        if job_data:
            machine_id = job_data.get("machine_id")
            status = job_data.get("status")
            
            # 상태에 따른 위치와 타입 결정
            if status in ["RUNNING", "FAILED"]:
                location = machine_id
                location_type = "Machine"
                tracking_status = "ERROR" if status == "FAILED" else "PROCESSING"
            elif status == "COMPLETED":
                location = "QC_Station"
                location_type = "QC"
                tracking_status = "COMPLETED"
            else:
                location = "Buffer_Area"
                location_type = "Buffer"
                tracking_status = "WAITING"
        else:
            # 작업이 없는 경우 기본값
            location = "Warehouse"
            location_type = "Storage"
            tracking_status = "STORED"
        
        tracking_info = {
            "modelType": "Submodel",
            "id": f"urn:aas:sm:{product_id}:TrackingInfo",
            "idShort": "TrackingInfo",
            "semanticId": {
                "type": "ExternalReference",
                "keys": [{
                    "type": "GlobalReference",
                    "value": "0173-1#02-AAV558#001"  # Tracking and Tracing
                }]
            },
            "submodelElements": [
                {
                    "modelType": "Property",
                    "idShort": "CurrentLocation",
                    "value": location,
                    "valueType": "xs:string"
                },
                {
                    "modelType": "Property",
                    "idShort": "LocationType",
                    "value": location_type,
                    "valueType": "xs:string"
                },
                {
                    "modelType": "Property",
                    "idShort": "Status",
                    "value": tracking_status,
                    "valueType": "xs:string"
                },
                {
                    "modelType": "Property",
                    "idShort": "LastUpdate",
                    "value": job_data.get("start_time", "") if job_data else "",
                    "valueType": "xs:dateTime"
                }
            ]
        }
        
        return tracking_info
    
    def save_submodel(self, submodel: Dict, filename: str):
        """Submodel을 파일로 저장"""
        filepath = os.path.join(self.submodels_dir, f"{filename}.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(submodel, f, indent=2, ensure_ascii=False)
        print(f"  ✓ Submodel: {filename}")


if __name__ == "__main__":
    converter = SnapshotToAASConverter()
    converter.convert_all_snapshots()