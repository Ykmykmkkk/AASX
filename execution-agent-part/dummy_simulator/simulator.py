# dummy_simulator/simulator.py
import json
import time
import sys
import pathlib

# 고정된 경로에서 입력 파일 읽기
INPUT_FILE = pathlib.Path("/data/current/simulation_inputs.json")

# All diagnostic messages to stderr
print("Dummy simulator started...", file=sys.stderr)

# 입력 데이터가 있는지 확인 (실제 시뮬레이터는 이 데이터를 사용)
if INPUT_FILE.exists():
    with open(INPUT_FILE, 'r') as f:
        input_data = json.load(f)
    print(f"INFO: Input data loaded successfully for product {input_data['order']['product_id']}.", file=sys.stderr)
else:
    print(f"WARN: Input file not found at {INPUT_FILE}", file=sys.stderr)

time.sleep(3) # 3초간 복잡한 계산을 하는 척

print("Dummy simulator finished.", file=sys.stderr)

# 최종 결과 JSON을 표준 출력(stdout)으로 print - 반드시 마지막에!
result = {
    "predicted_completion_time": "2025-08-11T16:30:00Z",
    "confidence": 0.85,
    "details": "Simulation based on provided inputs."
}
print(json.dumps(result))