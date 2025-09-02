#!/usr/bin/env python3
"""
AAS 서버 데이터를 AASX-main simulator 형식으로 변환하는 모듈

AAS 서버의 J1,J2,J3,M1,M2,M3 데이터를 
AASX-main simulator가 요구하는 JSON 형식으로 변환합니다.
"""

import json
import os
import sys
from typing import Dict, List, Any, Optional
from aas_query_client import AASQueryClient
from pathlib import Path

class SimulationDataConverter:
    """AAS 데이터를 AASX simulator 형식으로 변환하는 클래스"""
    
    def __init__(self, aas_ip: str, aas_port: int):
        self.client = AASQueryClient(aas_ip, aas_port)
        self.job_ids = ['J1', 'J2', 'J3']
        self.machine_ids = ['M1', 'M2', 'M3']
    
    def fetch_all_aas_data(self) -> Dict[str, Any]:
        """AAS 서버에서 모든 시뮬레이션 관련 데이터를 가져옵니다."""
        print("🔍 AAS 서버에서 데이터 수집 중...")
        
        aas_data = {
            'jobs': {},
            'machines': {},
            'operations': [],
            'error_jobs': [],
            'error_machines': []
        }
        
        # Job 데이터 수집
        for job_id in self.job_ids:
            print(f"  📋 Job {job_id} 조회 중...")
            try:
                # Job은 AAS Shell로 저장됨: urn:factory:job:J1
                job_shell_id = f"urn:factory:job:{job_id}"
                job_shell = self.client.get_shell_by_id(job_shell_id)
                job_submodel = self.client.get_submodel_by_id(job_shell_id)
                
                if job_shell:
                    aas_data['jobs'][job_id] = {
                        'type': 'shell',
                        'data': job_shell
                    }
                    print(f"    ✅ Shell로 발견: {job_shell.get('idShort', job_id)}")
                elif job_submodel:
                    aas_data['jobs'][job_id] = {
                        'type': 'submodel', 
                        'data': job_submodel
                    }
                    print(f"    ✅ Submodel로 발견: {job_submodel.get('idShort', job_id)}")
                else:
                    aas_data['error_jobs'].append(job_id)
                    print(f"    ❌ {job_id} 데이터를 찾을 수 없음")
            except Exception as e:
                aas_data['error_jobs'].append(job_id)
                print(f"    ❌ {job_id} 조회 실패: {e}")
        
        # Machine 데이터 수집
        for machine_id in self.machine_ids:
            print(f"  🔧 Machine {machine_id} 조회 중...")
            try:
                # Machine은 AAS Shell로 저장됨: urn:factory:machine:M1
                machine_shell_id = f"urn:factory:machine:{machine_id}"
                machine_shell = self.client.get_shell_by_id(machine_shell_id)
                machine_submodel = self.client.get_submodel_by_id(machine_shell_id)
                
                if machine_shell:
                    aas_data['machines'][machine_id] = {
                        'type': 'shell',
                        'data': machine_shell
                    }
                    print(f"    ✅ Shell로 발견: {machine_shell.get('idShort', machine_id)}")
                elif machine_submodel:
                    aas_data['machines'][machine_id] = {
                        'type': 'submodel',
                        'data': machine_submodel
                    }
                    print(f"    ✅ Submodel로 발견: {machine_submodel.get('idShort', machine_id)}")
                else:
                    aas_data['error_machines'].append(machine_id)
                    print(f"    ❌ {machine_id} 데이터를 찾을 수 없음")
            except Exception as e:
                aas_data['error_machines'].append(machine_id)
                print(f"    ❌ {machine_id} 조회 실패: {e}")
        
        print(f"✅ 데이터 수집 완료: Jobs {len(aas_data['jobs'])}/{len(self.job_ids)}, "
              f"Machines {len(aas_data['machines'])}/{len(self.machine_ids)}")
        
        return aas_data
    
    def convert_to_aasx_jobs(self, aas_data: Dict[str, Any]) -> List[Dict]:
        """AAS Job 데이터를 AASX-main jobs.json 형식으로 변환"""
        print("🔄 Jobs 데이터 변환 중...")
        
        jobs = []
        
        for job_id, job_info in aas_data['jobs'].items():
            job_data = job_info['data']
            
            # AAS에서 operations 정보 추출
            operations = self._extract_operations_from_job(job_data)
            
            aasx_job = {
                "job_id": job_id,
                "part_id": f"P{job_id[1:]}",  # J1 -> P1
                "operations": operations
            }
            
            jobs.append(aasx_job)
            print(f"  ✅ {job_id}: {len(operations)}개 operations")
        
        return jobs
    
    def convert_to_aasx_machines(self, aas_data: Dict[str, Any]) -> List[Dict]:
        """AAS Machine 데이터를 AASX-main machines.json 형식으로 변환"""
        print("🔄 Machines 데이터 변환 중...")
        
        machines = []
        
        for machine_id, machine_info in aas_data['machines'].items():
            machine_data = machine_info['data']
            
            # 기본 머신 정보 구성
            aasx_machine = {
                "machine_id": machine_id,
                "name": machine_data.get('idShort', machine_id),
                "type": self._extract_machine_type(machine_data),
                "status": "idle",  # 기본값
                "capacity": 1      # 기본값
            }
            
            machines.append(aasx_machine)
            print(f"  ✅ {machine_id}: {aasx_machine['type']}")
        
        return machines
    
    def convert_to_aasx_operations(self, aas_data: Dict[str, Any]) -> List[Dict]:
        """모든 operations를 수집하여 AASX-main operations.json 형식으로 변환"""
        print("🔄 Operations 데이터 변환 중...")
        
        operations = []
        
        for job_id, job_info in aas_data['jobs'].items():
            job_data = job_info['data']
            
            # Job에서 operations 추출
            job_operations = self._extract_detailed_operations(job_data, job_id)
            operations.extend(job_operations)
        
        print(f"  ✅ 총 {len(operations)}개 operations 변환")
        return operations
    
    def generate_default_data(self) -> Dict[str, Any]:
        """기본 시뮬레이션 데이터를 생성합니다 (AAS 조회 실패 시 fallback)"""
        print("📝 기본 시뮬레이션 데이터 생성 중...")
        
        # 기본 jobs.json 데이터
        jobs = [
            {"job_id": "J1", "part_id": "P1", "operations": ["O11", "O12", "O13"]},
            {"job_id": "J2", "part_id": "P2", "operations": ["O21", "O22"]},
            {"job_id": "J3", "part_id": "P3", "operations": ["O31", "O32"]}
        ]
        
        # 기본 machines.json 데이터
        machines = [
            {"machine_id": "M1", "name": "Machine-1", "type": "drilling", "status": "idle", "capacity": 1},
            {"machine_id": "M2", "name": "Machine-2", "type": "welding", "status": "idle", "capacity": 1},
            {"machine_id": "M3", "name": "Machine-3", "type": "testing", "status": "idle", "capacity": 1}
        ]
        
        # 기본 operations.json 데이터
        operations = [
            {"operation_id": "O11", "job_id": "J1", "type": "drilling", "machines": ["M1", "M2"]},
            {"operation_id": "O12", "job_id": "J1", "type": "welding", "machines": ["M2", "M3"]},
            {"operation_id": "O13", "job_id": "J1", "type": "testing", "machines": ["M1"]},
            {"operation_id": "O21", "job_id": "J2", "type": "drilling", "machines": ["M1"]},
            {"operation_id": "O22", "job_id": "J2", "type": "welding", "machines": ["M2"]},
            {"operation_id": "O31", "job_id": "J3", "type": "testing", "machines": ["M3"]},
            {"operation_id": "O32", "job_id": "J3", "type": "drilling", "machines": ["M1"]}
        ]
        
        # 기본 operation_durations.json 데이터
        operation_durations = {}
        for op in operations:
            for machine in op["machines"]:
                key = f"{op['operation_id']}_{machine}"
                operation_durations[key] = {
                    "distribution": "normal",
                    "mean": 10.0,
                    "std": 2.0
                }
        
        # 기본 machine_transfer_time.json 데이터
        machine_transfer_time = {}
        for from_m in ["M1", "M2", "M3"]:
            for to_m in ["M1", "M2", "M3"]:
                if from_m != to_m:
                    machine_transfer_time[f"{from_m}_{to_m}"] = {
                        "distribution": "uniform",
                        "low": 2.0,
                        "high": 5.0
                    }
        
        # 기본 routing_result.json 데이터 (정적 할당)
        routing_result = [
            {"operation_id": "O11", "job_id": "J1", "assigned_machine": "M1"},
            {"operation_id": "O12", "job_id": "J1", "assigned_machine": "M2"},
            {"operation_id": "O13", "job_id": "J1", "assigned_machine": "M1"},
            {"operation_id": "O21", "job_id": "J2", "assigned_machine": "M1"},
            {"operation_id": "O22", "job_id": "J2", "assigned_machine": "M2"},
            {"operation_id": "O31", "job_id": "J3", "assigned_machine": "M3"},
            {"operation_id": "O32", "job_id": "J3", "assigned_machine": "M1"}
        ]
        
        # 기본 machines 초기 상태
        initial_machine_status = {}
        for machine in machines:
            initial_machine_status[machine["machine_id"]] = {
                "status": "idle",
                "queue_length": 0,
                "current_job": None
            }
        
        return {
            "jobs": jobs,
            "machines": machines,
            "operations": operations,
            "operation_durations": operation_durations,
            "machine_transfer_time": machine_transfer_time,
            "routing_result": routing_result,
            "initial_machine_status": initial_machine_status
        }
    
    def _extract_operations_from_job(self, job_data: Dict) -> List[str]:
        """Job 데이터에서 operation ID 리스트를 추출"""
        # SubmodelElements에서 operations 정보 찾기
        elements = job_data.get('submodelElements', [])
        
        operations = []
        for element in elements:
            if element.get('idShort', '').lower() in ['operations', 'operation_list', 'ops']:
                value = element.get('value', '')
                if isinstance(value, str):
                    try:
                        # JSON 문자열인 경우 파싱
                        parsed_ops = json.loads(value)
                        if isinstance(parsed_ops, list):
                            operations = parsed_ops
                            break
                    except json.JSONDecodeError:
                        # 단순 문자열인 경우 분할
                        operations = [op.strip() for op in value.split(',')]
                        break
                elif isinstance(value, list):
                    operations = value
                    break
        
        # 기본값: job_id 기반 operations 생성
        if not operations:
            job_id = job_data.get('idShort', job_data.get('id', 'J1'))
            if job_id.startswith('J'):
                job_num = job_id[1:]
                operations = [f"O{job_num}1", f"O{job_num}2"]
        
        return operations
    
    def _extract_detailed_operations(self, job_data: Dict, job_id: str) -> List[Dict]:
        """Job에서 상세한 operation 정보를 추출"""
        operations = []
        operation_ids = self._extract_operations_from_job(job_data)
        
        for i, op_id in enumerate(operation_ids):
            # 기본 operation 타입 결정
            if 'drill' in op_id.lower() or i == 0:
                op_type = "drilling"
                machines = ["M1", "M2"]
            elif 'weld' in op_id.lower() or i == 1:
                op_type = "welding"
                machines = ["M2", "M3"]
            else:
                op_type = "testing"
                machines = ["M1", "M3"]
            
            operations.append({
                "operation_id": op_id,
                "job_id": job_id,
                "type": op_type,
                "machines": machines
            })
        
        return operations
    
    def _extract_machine_type(self, machine_data: Dict) -> str:
        """Machine 데이터에서 타입을 추출"""
        machine_id = machine_data.get('idShort', machine_data.get('id', ''))
        
        # idShort나 description에서 타입 추출 시도
        for element in machine_data.get('submodelElements', []):
            if element.get('idShort', '').lower() in ['type', 'machine_type', 'category']:
                return element.get('value', 'general')
        
        # 기본값: machine_id 기반 추정
        if 'M1' in machine_id:
            return "drilling"
        elif 'M2' in machine_id:
            return "welding"
        elif 'M3' in machine_id:
            return "testing"
        else:
            return "general"
    
    def save_to_directory(self, aasx_data: Dict[str, Any], output_dir: str) -> None:
        """변환된 데이터를 지정된 디렉토리에 저장"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        print(f"💾 AASX-main simulator 형식으로 저장 중: {output_dir}")
        
        files_to_save = [
            ('jobs.json', aasx_data['jobs']),
            ('machines.json', aasx_data['machines']),
            ('operations.json', aasx_data['operations']),
            ('operation_durations.json', aasx_data['operation_durations']),
            ('machine_transfer_time.json', aasx_data['machine_transfer_time']),
            ('routing_result.json', aasx_data['routing_result']),
            ('initial_machine_status.json', aasx_data['initial_machine_status'])
        ]
        
        for filename, data in files_to_save:
            file_path = output_path / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"  ✅ {filename}")
        
        print(f"🎯 모든 파일 저장 완료: {output_dir}")


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AAS 데이터를 AASX simulator 형식으로 변환')
    parser.add_argument('--aas-ip', default='127.0.0.1', help='AAS 서버 IP')
    parser.add_argument('--aas-port', type=int, default=5001, help='AAS 서버 포트')
    parser.add_argument('--output', default='./aasx_simulation_data', help='출력 디렉토리')
    parser.add_argument('--use-default', action='store_true', help='AAS 조회 없이 기본 데이터만 생성')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("AAS → AASX-main Simulator 데이터 변환기")
    print("=" * 80)
    
    converter = SimulationDataConverter(args.aas_ip, args.aas_port)
    
    if args.use_default:
        print("📝 기본 데이터 모드")
        aasx_data = converter.generate_default_data()
    else:
        print(f"🔍 AAS 서버 연결: {args.aas_ip}:{args.aas_port}")
        try:
            # AAS 데이터 수집
            aas_data = converter.fetch_all_aas_data()
            
            # AASX 형식으로 변환
            if aas_data['jobs'] or aas_data['machines']:
                print("🔄 AAS 데이터 변환 중...")
                jobs = converter.convert_to_aasx_jobs(aas_data)
                machines = converter.convert_to_aasx_machines(aas_data)
                operations = converter.convert_to_aasx_operations(aas_data)
                
                # 기본 데이터와 결합
                default_data = converter.generate_default_data()
                
                aasx_data = {
                    "jobs": jobs if jobs else default_data["jobs"],
                    "machines": machines if machines else default_data["machines"],
                    "operations": operations if operations else default_data["operations"],
                    "operation_durations": default_data["operation_durations"],
                    "machine_transfer_time": default_data["machine_transfer_time"],
                    "routing_result": default_data["routing_result"],
                    "initial_machine_status": default_data["initial_machine_status"]
                }
            else:
                print("⚠️  AAS 데이터 부족, 기본 데이터 사용")
                aasx_data = converter.generate_default_data()
                
        except Exception as e:
            print(f"❌ AAS 연결 실패: {e}")
            print("📝 기본 데이터로 대체")
            aasx_data = converter.generate_default_data()
    
    # 데이터 저장
    converter.save_to_directory(aasx_data, args.output)
    
    print("\n📊 변환 완료 요약:")
    print(f"  Jobs: {len(aasx_data['jobs'])}개")
    print(f"  Machines: {len(aasx_data['machines'])}개")
    print(f"  Operations: {len(aasx_data['operations'])}개")
    print(f"  Output: {args.output}")
    
    print("\n🚀 다음 단계:")
    print("1. 생성된 JSON 파일들을 AASX-main simulator로 테스트")
    print("2. PVC에 데이터 저장 로직 구현")
    print("3. Docker 이미지에 AASX-main simulator 통합")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()