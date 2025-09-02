# aas_mock_server/server.py
import json
from flask import Flask, jsonify, abort
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리를 경로에 추가합니다.
sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import AAS_DATA_FILE_PATH

app = Flask(__name__)

# 서버 시작 시 AAS 데이터를 메모리에 로드합니다.
try:
    with open(AAS_DATA_FILE_PATH, 'r', encoding='utf-8') as f:
        aas_data = json.load(f)
        # 빠른 조회를 위해 Submodel을 id 기준으로 딕셔너리로 만듭니다.
        submodels_by_id = {sm['id']: sm for sm in aas_data.get('submodels', [])}
        print("✅ AAS Mock Data loaded successfully.")
except FileNotFoundError:
    print(f"❌ ERROR: AAS data file not found at {AAS_DATA_FILE_PATH}")
    aas_data = {}
    submodels_by_id = {}


@app.route('/submodels/<path:submodel_id>', methods=['GET'])
def get_submodel_by_id(submodel_id: str):
    """
    URL 경로로 받은 URN ID를 사용하여 Submodel을 찾습니다.
    ID는 base64url 인코딩되어 전달될 수 있습니다.
    """
    # Try to decode from base64url if it looks like base64
    import base64
    try:
        # Attempt to decode base64url
        padding = 4 - (len(submodel_id) % 4) if len(submodel_id) % 4 else 0
        decoded_id = base64.urlsafe_b64decode(submodel_id + '=' * padding).decode('utf-8')
        if decoded_id.startswith('urn:'):
            submodel_id = decoded_id
    except:
        # If decoding fails, use the original ID
        pass
    
    if submodel_id in submodels_by_id:
        return jsonify(submodels_by_id[submodel_id])
    
    abort(404, description=f"Submodel with id '{submodel_id}' not found.")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)