"""
Docker Executor Module
외부 서비스를 Docker 컨테이너로 실행
"""

import json
import os
import tempfile
import shutil
import subprocess
from typing import Dict, Any
from datetime import datetime

try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    print("Warning: docker-py not installed. Using subprocess fallback.")

class DockerExecutor:
    def __init__(self):
        """Docker 클라이언트 초기화"""
        self.client = None
        
        if DOCKER_AVAILABLE:
            try:
                self.client = docker.from_env()
                print("Docker client initialized successfully")
            except Exception as e:
                print(f"Warning: Docker not available: {e}")
                self.client = None
        else:
            # subprocess로 Docker 사용 가능 여부 확인
            try:
                result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
                if result.returncode == 0:
                    print("Docker CLI available (using subprocess)")
                else:
                    print("Docker not available")
            except FileNotFoundError:
                print("Docker not installed")
    
    def execute_container(self, image_name: str, input_data: Dict[str, Any], 
                         input_files: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Docker 컨테이너 실행
        
        Args:
            image_name: Docker 이미지 이름
            input_data: 입력 데이터 (JSON으로 전달)
            input_files: 추가 입력 파일들 {filename: filepath}
            
        Returns:
            실행 결과 딕셔너리
        """
        if not self.client:
            return {
                "error": "Docker not available",
                "fallback": "Using simulation mode"
            }
        
        # 임시 디렉토리 생성
        with tempfile.TemporaryDirectory() as temp_dir:
            input_dir = os.path.join(temp_dir, "input")
            output_dir = os.path.join(temp_dir, "output")
            os.makedirs(input_dir)
            os.makedirs(output_dir)
            
            # 입력 파일 복사
            if input_files:
                for filename, filepath in input_files.items():
                    if os.path.exists(filepath):
                        shutil.copy(filepath, os.path.join(input_dir, filename))
                        print(f"Copied {filename} to input directory")
            
            # 입력 데이터를 JSON 파일로 저장
            input_json_path = os.path.join(input_dir, "input_data.json")
            with open(input_json_path, 'w') as f:
                json.dump(input_data, f, indent=2)
            
            try:
                # Docker 컨테이너 실행
                print(f"Running Docker container: {image_name}")
                container = self.client.containers.run(
                    image_name,
                    volumes={
                        input_dir: {'bind': '/data/input', 'mode': 'ro'},
                        output_dir: {'bind': '/data/output', 'mode': 'rw'}
                    },
                    remove=True,
                    detach=False,
                    stdout=True,
                    stderr=True
                )
                
                # 컨테이너 로그 출력
                if isinstance(container, bytes):
                    print("Container output:", container.decode('utf-8'))
                
                # 결과 파일 읽기
                result_file = os.path.join(output_dir, "result.json")
                if os.path.exists(result_file):
                    with open(result_file, 'r') as f:
                        result = json.load(f)
                        print("Successfully retrieved results from container")
                        return result
                else:
                    return {
                        "error": "No result file generated",
                        "container_output": container.decode('utf-8') if isinstance(container, bytes) else str(container)
                    }
                    
            except docker.errors.ContainerError as e:
                error_output = None
                if hasattr(e, 'stderr') and e.stderr:
                    error_output = e.stderr.decode('utf-8')
                elif hasattr(e, 'output') and e.output:
                    error_output = e.output.decode('utf-8')
                
                return {
                    "error": f"Container execution failed: {str(e)}",
                    "exit_code": e.exit_status if hasattr(e, 'exit_status') else None,
                    "output": error_output
                }
            except docker.errors.ImageNotFound:
                return {
                    "error": f"Docker image '{image_name}' not found",
                    "suggestion": f"Build the image first: docker build -t {image_name} ."
                }
            except Exception as e:
                return {
                    "error": f"Unexpected error: {e}",
                    "type": type(e).__name__
                }
    
    def simulate_docker_execution(self, service_type: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Docker가 없을 때 시뮬레이션 모드
        """
        print(f"Simulating Docker execution for {service_type}")
        
        if service_type == "job-processor":
            # Job processor 시뮬레이션
            jobs = input_data.get("jobs", [])
            return {
                "service": "job-processor",
                "version": "1.0.0",
                "processed_at": datetime.now().isoformat(),
                "mode": "simulation",
                "total_jobs": len(jobs),
                "processed_jobs": len(jobs),
                "jobs": jobs[:5],  # 처음 5개만
                "statistics": {
                    "failed_count": sum(1 for j in jobs if j.get("status") == "Failed"),
                    "completed_count": sum(1 for j in jobs if j.get("status") == "Completed")
                }
            }
        
        return {
            "service": service_type,
            "mode": "simulation",
            "message": "Docker not available, returning simulated results"
        }