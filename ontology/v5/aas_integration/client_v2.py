"""
AAS REST API Client v2
Implements standard-compliant communication with AAS servers
"""

import requests
from typing import Dict, Any, Optional, List
from .utils import encode_base64_url, build_aas_path, parse_aas_datetime, safe_get_nested
import json


class AASClientV2:
    """Client for interacting with AAS REST API v2"""
    
    def __init__(self, base_url: str = "http://localhost:5001"):
        """
        Initialize AAS client
        
        Args:
            base_url: Base URL of the AAS server
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def get_all_shells(self) -> List[Dict[str, Any]]:
        """
        Get all Asset Administration Shells
        
        Returns:
            List of AAS descriptors
        """
        try:
            response = self.session.get(f"{self.base_url}/shells")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching shells: {e}")
            return []
    
    def get_shell(self, shell_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific Asset Administration Shell
        
        Args:
            shell_id: Shell identifier (will be BASE64-URL encoded)
            
        Returns:
            AAS data or None if not found
        """
        try:
            path = build_aas_path(shell_id)
            response = self.session.get(f"{self.base_url}{path}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"⚠️ Shell not found: {shell_id}")
            else:
                print(f"❌ HTTP error fetching shell: {e}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching shell: {e}")
            return None
    
    def get_all_submodels_of_shell(self, shell_id: str) -> List[Dict[str, Any]]:
        """
        Get all submodels of a shell
        
        Args:
            shell_id: Shell identifier
            
        Returns:
            List of submodel descriptors
        """
        try:
            path = build_aas_path(shell_id)
            response = self.session.get(f"{self.base_url}{path}/submodels")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching submodels: {e}")
            return []
    
    def get_submodel(self, shell_id: str, submodel_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific submodel of a shell
        
        Args:
            shell_id: Shell identifier
            submodel_id: Submodel identifier
            
        Returns:
            Submodel data or None if not found
        """
        try:
            path = build_aas_path(shell_id, submodel_id)
            response = self.session.get(f"{self.base_url}{path}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"⚠️ Submodel not found: {submodel_id}")
            else:
                print(f"❌ HTTP error fetching submodel: {e}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching submodel: {e}")
            return None
    
    def get_submodel_element(self, shell_id: str, submodel_id: str, 
                           element_path: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific submodel element
        
        Args:
            shell_id: Shell identifier
            submodel_id: Submodel identifier
            element_path: Element path (dot notation)
            
        Returns:
            Element data or None if not found
        """
        try:
            path = build_aas_path(shell_id, submodel_id, element_path)
            response = self.session.get(f"{self.base_url}{path}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching element: {e}")
            return None
    
    def query_shells_by_asset_id(self, asset_id: str) -> List[Dict[str, Any]]:
        """
        Query shells by asset ID
        
        Args:
            asset_id: Asset identifier
            
        Returns:
            List of matching shells
        """
        try:
            params = {'assetIds': asset_id}
            response = self.session.get(f"{self.base_url}/shells", params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error querying shells: {e}")
            return []
    
    # High-level API methods for specific use cases
    
    def get_machines_requiring_cooling(self) -> List[Dict[str, Any]]:
        """
        Get all machines that require cooling during production
        
        Returns:
            List of machines with cooling requirements
        """
        machines = []
        shells = self.get_all_shells()
        
        for shell in shells:
            shell_id = shell.get('id', '')
            
            # Skip non-machine shells
            if not shell_id.startswith('urn:aas:Machine:'):
                continue
            
            # Get technical data submodel
            tech_data = self.get_submodel(shell_id, f"urn:aas:TechnicalData:{shell['idShort']}")
            
            if tech_data:
                # Look for cooling requirement in technical properties
                elements = tech_data.get('submodelElements', [])
                for element in elements:
                    if element.get('idShort') == 'GeneralTechnicalProperties':
                        for prop in element.get('value', []):
                            if prop.get('idShort') == 'requires_cooling_during_production':
                                if prop.get('value') == 'true' or prop.get('value') == True:
                                    machines.append({
                                        'id': shell['idShort'],
                                        'shell_id': shell_id,
                                        'requires_cooling': True
                                    })
                                break
        
        return machines
    
    def get_products_requiring_cooling(self) -> List[Dict[str, Any]]:
        """
        Get all products that require cooling during production
        
        Returns:
            List of products with cooling requirements
        """
        products = []
        shells = self.get_all_shells()
        
        for shell in shells:
            shell_id = shell.get('id', '')
            
            # Skip non-product shells
            if not shell_id.startswith('urn:aas:Product:'):
                continue
            
            # Get manufacturing requirements submodel
            mfg_req = self.get_submodel(shell_id, f"urn:aas:ManufacturingRequirements:{shell['idShort']}")
            
            if mfg_req:
                # Look for cooling requirement
                elements = mfg_req.get('submodelElements', [])
                for element in elements:
                    if element.get('idShort') == 'ProcessRequirements':
                        for prop in element.get('value', []):
                            if prop.get('idShort') == 'requires_cooling_during_production':
                                if prop.get('value') == 'true' or prop.get('value') == True:
                                    products.append({
                                        'id': shell['idShort'],
                                        'shell_id': shell_id,
                                        'requires_cooling': True
                                    })
                                break
        
        return products
    
    def get_job_history(self, machine_id: str, date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get job history for a machine
        
        Args:
            machine_id: Machine identifier
            date: Optional date filter (YYYY-MM-DD)
            
        Returns:
            List of jobs
        """
        jobs = []
        
        # Get operational data submodel
        shell_id = f"urn:aas:Machine:{machine_id}"
        op_data = self.get_submodel(shell_id, f"urn:aas:OperationalData:{machine_id}")
        
        if not op_data:
            return jobs
        
        # Extract job history
        elements = op_data.get('submodelElements', [])
        for element in elements:
            if element.get('idShort') == 'JobHistory':
                for job_element in element.get('value', []):
                    job = {}
                    for prop in job_element.get('value', []):
                        key = prop.get('idShort', '').lower()
                        if key == 'jobid':
                            job['job_id'] = prop.get('value')
                        elif key == 'productid':
                            job['product_id'] = prop.get('value')
                        elif key == 'starttime':
                            job['start_time'] = prop.get('value')
                        elif key == 'endtime':
                            job['end_time'] = prop.get('value')
                        elif key == 'status':
                            job['status'] = prop.get('value')
                        elif key == 'errorcode':
                            job['error_code'] = prop.get('value')
                    
                    # Apply date filter if provided
                    if date and 'start_time' in job:
                        try:
                            job_date = parse_aas_datetime(job['start_time']).strftime('%Y-%m-%d')
                            if job_date != date:
                                continue
                        except:
                            continue
                    
                    if job:
                        job['machine_id'] = machine_id
                        jobs.append(job)
        
        return jobs
    
    def get_machine_current_status(self, machine_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current status of a machine
        
        Args:
            machine_id: Machine identifier
            
        Returns:
            Current status or None
        """
        shell_id = f"urn:aas:Machine:{machine_id}"
        op_data = self.get_submodel(shell_id, f"urn:aas:OperationalData:{machine_id}")
        
        if not op_data:
            return None
        
        status = {'machine_id': machine_id}
        
        # Extract current status
        elements = op_data.get('submodelElements', [])
        for element in elements:
            if element.get('idShort') == 'CurrentStatus':
                for prop in element.get('value', []):
                    key = prop.get('idShort', '')
                    if key == 'OperatingState':
                        status['state'] = prop.get('value')
                    elif key == 'CurrentUtilization':
                        status['utilization'] = float(prop.get('value', 0))
                    elif key == 'CurrentJob':
                        status['current_job'] = prop.get('value')
        
        return status if 'state' in status else None
    
    def test_connection(self) -> bool:
        """
        Test connection to AAS server
        
        Returns:
            True if connection successful
        """
        try:
            response = self.session.get(f"{self.base_url}/shells")
            return response.status_code == 200
        except:
            return False