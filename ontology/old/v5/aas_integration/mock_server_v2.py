"""
Mock AAS REST API Server v2
Implements standard-compliant AAS REST API for testing
"""

from flask import Flask, jsonify, request
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
from .utils import encode_base64_url, decode_base64_url, safe_get_nested
from .standards.mock_data_generator import MockDataGenerator


app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mock_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Data storage
SHELLS = {}
SUBMODELS = {}
JOB_HISTORY = []


def load_mock_data():
    """Load mock data from generated files"""
    global SHELLS, SUBMODELS, JOB_HISTORY
    
    logger.info("Loading mock data...")
    
    # Ensure mock data exists
    data_dir = Path("aas_integration/mock_data")
    if not data_dir.exists() or not any(data_dir.glob("shells/*.json")):
        logger.info("Generating mock data...")
        generator = MockDataGenerator()
        generator.generate_all_data()
    
    # Load shells
    shells_dir = data_dir / "shells"
    for shell_file in shells_dir.glob("*.json"):
        with open(shell_file, 'r') as f:
            shell = json.load(f)
            shell_id = shell['id']
            SHELLS[shell_id] = shell
            logger.info(f"Loaded shell: {shell['idShort']}")
    
    # Load submodels
    submodels_dir = data_dir / "submodels"
    for submodel_file in submodels_dir.glob("*.json"):
        with open(submodel_file, 'r') as f:
            submodel = json.load(f)
            submodel_id = submodel['id']
            SUBMODELS[submodel_id] = submodel
            logger.info(f"Loaded submodel: {submodel['idShort']}")
    
    # Load job history
    job_file = data_dir / "job_history.json"
    if job_file.exists():
        with open(job_file, 'r') as f:
            data = json.load(f)
            JOB_HISTORY = data.get('jobs', [])
            logger.info(f"Loaded {len(JOB_HISTORY)} job history records")
    
    logger.info(f"Total: {len(SHELLS)} shells, {len(SUBMODELS)} submodels, {len(JOB_HISTORY)} jobs")


# API Routes

@app.route('/shells', methods=['GET'])
def get_shells():
    """Get all Asset Administration Shells"""
    asset_ids = request.args.get('assetIds')
    
    shells = list(SHELLS.values())
    
    # Filter by asset ID if provided
    if asset_ids:
        filtered = []
        for shell in shells:
            asset_info = shell.get('assetInformation', {})
            if asset_info.get('globalAssetId') == asset_ids:
                filtered.append(shell)
            else:
                # Check specific asset IDs
                for specific_id in asset_info.get('specificAssetIds', []):
                    if specific_id.get('value') == asset_ids:
                        filtered.append(shell)
                        break
        shells = filtered
    
    logger.info(f"GET /shells - returning {len(shells)} shells")
    return jsonify(shells)


@app.route('/shells/<path:aas_id>', methods=['GET'])
def get_shell(aas_id):
    """Get a specific Asset Administration Shell"""
    try:
        # Decode the BASE64-URL encoded ID
        decoded_id = decode_base64_url(aas_id)
        
        if decoded_id in SHELLS:
            logger.info(f"GET /shells/{aas_id} - found")
            return jsonify(SHELLS[decoded_id])
        else:
            logger.warning(f"GET /shells/{aas_id} - not found")
            return jsonify({"error": "Shell not found"}), 404
    except Exception as e:
        logger.error(f"Error decoding shell ID: {e}")
        return jsonify({"error": "Invalid shell ID"}), 400


@app.route('/shells/<path:aas_id>/submodels', methods=['GET'])
def get_shell_submodels(aas_id):
    """Get all submodels of a shell"""
    try:
        decoded_id = decode_base64_url(aas_id)
        
        if decoded_id not in SHELLS:
            return jsonify({"error": "Shell not found"}), 404
        
        shell = SHELLS[decoded_id]
        submodel_refs = shell.get('submodels', [])
        
        # Get actual submodels based on references
        submodels = []
        for ref in submodel_refs:
            # Extract submodel ID from reference
            keys = ref.get('keys', [])
            if keys:
                submodel_id = keys[-1]['value']
                if submodel_id in SUBMODELS:
                    submodels.append(SUBMODELS[submodel_id])
        
        logger.info(f"GET /shells/{aas_id}/submodels - returning {len(submodels)} submodels")
        return jsonify(submodels)
    except Exception as e:
        logger.error(f"Error getting submodels: {e}")
        return jsonify({"error": "Invalid request"}), 400


@app.route('/shells/<path:aas_id>/submodels/<path:submodel_id>', methods=['GET'])
def get_shell_submodel(aas_id, submodel_id):
    """Get a specific submodel of a shell"""
    try:
        decoded_aas_id = decode_base64_url(aas_id)
        decoded_submodel_id = decode_base64_url(submodel_id)
        
        if decoded_aas_id not in SHELLS:
            return jsonify({"error": "Shell not found"}), 404
        
        if decoded_submodel_id in SUBMODELS:
            logger.info(f"GET /shells/{aas_id}/submodels/{submodel_id} - found")
            return jsonify(SUBMODELS[decoded_submodel_id])
        else:
            logger.warning(f"GET /shells/{aas_id}/submodels/{submodel_id} - not found")
            return jsonify({"error": "Submodel not found"}), 404
    except Exception as e:
        logger.error(f"Error getting submodel: {e}")
        return jsonify({"error": "Invalid request"}), 400


@app.route('/shells/<path:aas_id>/submodels/<path:submodel_id>/submodel-elements/<path:element_path>', methods=['GET'])
def get_submodel_element(aas_id, submodel_id, element_path):
    """Get a specific submodel element"""
    try:
        decoded_aas_id = decode_base64_url(aas_id)
        decoded_submodel_id = decode_base64_url(submodel_id)
        
        if decoded_aas_id not in SHELLS:
            return jsonify({"error": "Shell not found"}), 404
        
        if decoded_submodel_id not in SUBMODELS:
            return jsonify({"error": "Submodel not found"}), 404
        
        submodel = SUBMODELS[decoded_submodel_id]
        
        # Navigate through the element path
        element = safe_get_nested(submodel, f"submodelElements.{element_path}")
        
        if element:
            logger.info(f"GET element {element_path} - found")
            return jsonify(element)
        else:
            logger.warning(f"GET element {element_path} - not found")
            return jsonify({"error": "Element not found"}), 404
    except Exception as e:
        logger.error(f"Error getting element: {e}")
        return jsonify({"error": "Invalid request"}), 400


# Custom API endpoints for specific queries

@app.route('/api/machines/cooling-required', methods=['GET'])
def get_cooling_machines():
    """Get machines that require cooling"""
    machines = []
    
    for shell_id, shell in SHELLS.items():
        if not shell_id.startswith('urn:aas:Machine:'):
            continue
        
        # Find technical data submodel
        id_short = shell['idShort']
        tech_data_id = f"urn:aas:TechnicalData:{id_short}"
        
        if tech_data_id in SUBMODELS:
            tech_data = SUBMODELS[tech_data_id]
            
            # Check for cooling requirement
            for element in tech_data.get('submodelElements', []):
                if element.get('idShort') == 'GeneralTechnicalProperties':
                    for prop in element.get('value', []):
                        if prop.get('idShort') == 'requires_cooling_during_production':
                            # Fixed: Check for both 'true' string and True boolean
                            if prop.get('value') == 'true' or prop.get('value') == True:
                                machines.append({
                                    'id': id_short,
                                    'shell_id': shell_id,
                                    'name': shell.get('idShort'),
                                    'requires_cooling': True
                                })
    
    logger.info(f"GET /api/machines/cooling-required - returning {len(machines)} machines")
    return jsonify(machines)


@app.route('/api/products/cooling-required', methods=['GET'])
def get_cooling_products():
    """Get products that require cooling"""
    products = []
    
    for shell_id, shell in SHELLS.items():
        if not shell_id.startswith('urn:aas:Product:'):
            continue
        
        # Find manufacturing requirements submodel
        id_short = shell['idShort']
        mfg_req_id = f"urn:aas:ManufacturingRequirements:{id_short}"
        
        if mfg_req_id in SUBMODELS:
            mfg_req = SUBMODELS[mfg_req_id]
            
            # Check for cooling requirement
            for element in mfg_req.get('submodelElements', []):
                if element.get('idShort') == 'ProcessRequirements':
                    for prop in element.get('value', []):
                        if prop.get('idShort') == 'requires_cooling_during_production':
                            # Fixed: Check for both 'true' string and True boolean
                            if prop.get('value') == 'true' or prop.get('value') == True:
                                products.append({
                                    'id': id_short,
                                    'shell_id': shell_id,
                                    'name': shell.get('idShort'),
                                    'requires_cooling': True
                                })
    
    logger.info(f"GET /api/products/cooling-required - returning {len(products)} products")
    return jsonify(products)


@app.route('/api/jobs/failed', methods=['GET'])
def get_failed_jobs():
    """Get failed jobs with optional date filter"""
    date = request.args.get('date')
    
    failed_jobs = [job for job in JOB_HISTORY if job['status'] == 'FAILED']
    
    # Filter by date if provided
    if date:
        filtered = []
        for job in failed_jobs:
            try:
                job_date = job['start_time'].split('T')[0]
                if job_date == date:
                    filtered.append(job)
            except:
                pass
        failed_jobs = filtered
    
    logger.info(f"GET /api/jobs/failed - returning {len(failed_jobs)} jobs")
    return jsonify(failed_jobs)


@app.route('/api/jobs/by-machine/<machine_id>', methods=['GET'])
def get_jobs_by_machine(machine_id):
    """Get jobs for a specific machine"""
    date = request.args.get('date')
    
    jobs = [job for job in JOB_HISTORY if job.get('machine_id') == machine_id]
    
    # Filter by date if provided
    if date:
        filtered = []
        for job in jobs:
            try:
                job_date = job['start_time'].split('T')[0]
                if job_date == date:
                    filtered.append(job)
            except:
                pass
        jobs = filtered
    
    logger.info(f"GET /api/jobs/by-machine/{machine_id} - returning {len(jobs)} jobs")
    return jsonify(jobs)


@app.route('/api/product/<product_id>/location', methods=['GET'])
def get_product_location(product_id):
    """Get current location of a product"""
    # Find latest job with this product
    product_jobs = [job for job in JOB_HISTORY if job.get('product_id') == product_id]
    
    if not product_jobs:
        # Check if product exists
        product_shell_id = f"urn:aas:Product:{product_id}"
        if product_shell_id in SHELLS:
            return jsonify({
                'product_id': product_id,
                'current_location': 'warehouse',
                'status': 'IN_STORAGE',
                'location_type': 'storage'
            })
        else:
            return jsonify({'error': 'Product not found'}), 404
    
    # Sort by end time and get latest
    product_jobs.sort(key=lambda x: x.get('end_time', ''), reverse=True)
    latest_job = product_jobs[0]
    
    result = {
        'product_id': product_id,
        'current_location': latest_job.get('machine_id'),
        'last_job_id': latest_job.get('job_id'),
        'last_update': latest_job.get('end_time'),
        'status': latest_job.get('status'),
        'location_type': 'machine'
    }
    
    logger.info(f"GET /api/product/{product_id}/location - found at {result['current_location']}")
    return jsonify(result)


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'data_loaded': {
            'shells': len(SHELLS),
            'submodels': len(SUBMODELS),
            'jobs': len(JOB_HISTORY)
        }
    })


# Error handlers

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500


# Initialize data on startup
def init_server():
    """Initialize server with mock data"""
    try:
        load_mock_data()
        logger.info("Mock AAS Server v2 initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize server: {e}")
        raise


if __name__ == '__main__':
    init_server()
    logger.info("Starting Mock AAS Server v2 on http://localhost:5001")
    app.run(host='0.0.0.0', port=5001, debug=False)