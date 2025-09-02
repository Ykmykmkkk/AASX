"""
AAS Server Query Client
표준 AAS 서버에 등록된 데이터를 조회하는 클라이언트
"""

import requests
import base64
import json
from typing import Optional, List, Dict, Any

def base64url_encode(s: str) -> str:
    """Encode string s to Base64Url without padding."""
    b64 = base64.b64encode(s.encode('utf-8')).decode('utf-8')
    return b64.rstrip('=').replace('+', '-').replace('/', '_')

def pretty_print_json(data: Any, indent: int = 2):
    """Helper function to pretty print JSON data."""
    if data:
        print(json.dumps(data, indent=indent, ensure_ascii=False))

class AASQueryClient:
    """AAS Server Query Client for retrieving registered data"""
    
    def __init__(self, ip: str, port: int):
        self.base_url = f"http://{ip}:{port}"
        self.ip = ip
        self.port = port
    
    def get_all_shells(self) -> Optional[List[Dict]]:
        """
        Get all Asset Administration Shells from the server.
        
        Returns:
            List of AAS objects or None if error
        """
        url = f"{self.base_url}/shells"
        try:
            response = requests.get(url)
            response.raise_for_status()
            shells = response.json()
            print(f"Found {len(shells)} Asset Administration Shells")
            return shells
        except requests.RequestException as e:
            print(f"Failed to get shells: {e}")
            return None
    
    def get_shell_by_id(self, aas_id: str) -> Optional[Dict]:
        """
        Get a specific Asset Administration Shell by ID.
        
        Args:
            aas_id: Plain AAS ID (will be Base64URL encoded)
        
        Returns:
            AAS object or None if error
        """
        encoded_id = base64url_encode(aas_id)
        url = f"{self.base_url}/shells/{encoded_id}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Failed to get shell {aas_id}: {e}")
            return None
    
    def get_all_submodels(self) -> Optional[List[Dict]]:
        """
        Get all Submodels from the server.
        
        Returns:
            List of Submodel objects or None if error
        """
        url = f"{self.base_url}/submodels"
        try:
            response = requests.get(url)
            response.raise_for_status()
            submodels = response.json()
            print(f"Found {len(submodels)} Submodels")
            return submodels
        except requests.RequestException as e:
            print(f"Failed to get submodels: {e}")
            return None
    
    def get_submodel_by_id(self, submodel_id: str) -> Optional[Dict]:
        """
        Get a specific Submodel by ID.
        
        Args:
            submodel_id: Plain Submodel ID (will be Base64URL encoded)
        
        Returns:
            Submodel object or None if error
        """
        encoded_id = base64url_encode(submodel_id)
        url = f"{self.base_url}/submodels/{encoded_id}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Failed to get submodel {submodel_id}: {e}")
            return None
    
    def get_submodel_elements(self, submodel_id: str) -> Optional[List[Dict]]:
        """
        Get all SubmodelElements from a specific Submodel.
        
        Args:
            submodel_id: Plain Submodel ID
        
        Returns:
            List of SubmodelElement objects or None if error
        """
        encoded_id = base64url_encode(submodel_id)
        url = f"{self.base_url}/submodels/{encoded_id}/submodel-elements"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Failed to get submodel elements for {submodel_id}: {e}")
            return None
    
    def get_submodel_element_by_path(self, submodel_id: str, element_path: str) -> Optional[Dict]:
        """
        Get a specific SubmodelElement by its path within a Submodel.
        
        Args:
            submodel_id: Plain Submodel ID
            element_path: Path to the element (e.g., "Property1" or "Collection1.Property2")
        
        Returns:
            SubmodelElement object or None if error
        """
        encoded_id = base64url_encode(submodel_id)
        url = f"{self.base_url}/submodels/{encoded_id}/submodel-elements/{element_path}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Failed to get element {element_path} from submodel {submodel_id}: {e}")
            return None
    
    def get_concept_descriptions(self) -> Optional[List[Dict]]:
        """
        Get all Concept Descriptions from the server.
        
        Returns:
            List of ConceptDescription objects or None if error
        """
        url = f"{self.base_url}/concept-descriptions"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Failed to get concept descriptions: {e}")
            return None
    
    def query_shells_by_asset_id(self, asset_id: str) -> Optional[List[Dict]]:
        """
        Query Asset Administration Shells by Asset ID.
        
        Args:
            asset_id: Asset ID to search for
        
        Returns:
            List of matching AAS objects or None if error
        """
        url = f"{self.base_url}/lookup/shells"
        params = {"assetIds": asset_id}
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Failed to query shells by asset ID {asset_id}: {e}")
            return None
    
    def get_server_description(self) -> Optional[Dict]:
        """
        Get server description/metadata.
        
        Returns:
            Server description object or None if error
        """
        url = f"{self.base_url}/description"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Failed to get server description: {e}")
            return None
    
    def get_shell_submodels(self, aas_id: str) -> Optional[List[Dict]]:
        """
        Get all Submodels referenced by a specific AAS.
        
        Args:
            aas_id: Plain AAS ID
        
        Returns:
            List of Submodel references or None if error
        """
        encoded_id = base64url_encode(aas_id)
        url = f"{self.base_url}/shells/{encoded_id}/submodel-refs"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Failed to get submodel refs for shell {aas_id}: {e}")
            return None
    
    def search_submodels_by_semantic_id(self, semantic_id: str) -> Optional[List[Dict]]:
        """
        Search Submodels by semantic ID.
        
        Args:
            semantic_id: Semantic ID to search for
        
        Returns:
            List of matching Submodels or None if error
        """
        url = f"{self.base_url}/submodels"
        params = {"semanticId": semantic_id}
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Failed to search submodels by semantic ID {semantic_id}: {e}")
            return None

# Example usage
if __name__ == "__main__":
    # Configuration
    IP = "192.168.50.159"  # Change to your AAS server IP
    PORT = 5001       # Change to your AAS server port

    # Create client instance
    client = AASQueryClient(IP, PORT)
    
    print("=" * 60)
    print("AAS Server Query Examples")
    print("=" * 60)
    
    # 1. Get all Asset Administration Shells
    print("\n1. Fetching all Asset Administration Shells:")
    shells = client.get_all_shells()
    if shells:
        for shell in shells[:5]:  # Show first 5
            print(f"  - ID: {shell.get('id', 'N/A')}")
            print(f"    idShort: {shell.get('idShort', 'N/A')}")
    
    # 2. Get all Submodels
    print("\n2. Fetching all Submodels:")
    submodels = client.get_all_submodels()
    if submodels:
        for sm in submodels[:5]:  # Show first 5
            print(f"  - ID: {sm.get('id', 'N/A')}")
            print(f"    idShort: {sm.get('idShort', 'N/A')}")
            print(f"    kind: {sm.get('kind', 'N/A')}")
    
    # 3. Get specific examples from factory automation
    print("\n3. Factory Automation Specific Queries:")
    
    # 3.1 Get CNC-01 machine
    print("\n  3.1 CNC-01 Machine:")
    cnc_shell = client.get_shell_by_id("urn:factory:machine:cnc-01")
    if cnc_shell:
        print(f"    Found: {cnc_shell.get('idShort', 'N/A')}")
        print(f"    Asset Kind: {cnc_shell.get('assetInformation', {}).get('assetKind', 'N/A')}")
    
    # 3.2 Get Job Log
    print("\n  3.2 Job Log Submodel:")
    job_log = client.get_submodel_by_id("urn:factory:submodel:job_log")
    if job_log:
        print(f"    ID: {job_log.get('id')}")
        print(f"    Elements count: {len(job_log.get('submodelElements', []))}")
    
    # 3.3 Get Process Specification
    print("\n  3.3 Process Specification:")
    process_spec = client.get_submodel_by_id("urn:factory:submodel:process_specification:all")
    if process_spec:
        elements = process_spec.get('submodelElements', [])
        for elem in elements[:3]:  # Show first 3 products
            print(f"    - Product: {elem.get('idShort', 'N/A')}")
    
    # 3.4 Get Product Tracking
    print("\n  3.4 Product Tracking (Product-C):")
    tracking = client.get_submodel_by_id("urn:factory:submodel:tracking_data:product-c")
    if tracking:
        print(f"    Submodel found: {tracking.get('idShort', 'N/A')}")
        elements = tracking.get('submodelElements', [])
        if elements:
            # Parse the value (it's a JSON string)
            value_str = elements[0].get('value', '{}')
            try:
                value_data = json.loads(value_str)
                print(f"    Current Location: {value_data.get('current_location', 'N/A')}")
                print(f"    Current Process: {value_data.get('current_process', 'N/A')}")
                print(f"    Progress: {value_data.get('progress_percentage', 0)}%")
            except json.JSONDecodeError:
                print(f"    Raw value: {value_str}")
    
    # 4. Get machine capabilities
    print("\n4. Machine Capabilities:")
    for machine in ["cnc-01", "welder-01", "painter-01"]:
        capability = client.get_submodel_by_id(f"urn:factory:submodel:capability:{machine}")
        if capability:
            print(f"  - {machine}: Found capability submodel")
    
    # 5. Get machine status
    print("\n5. Machine Status:")
    for machine in ["cnc-01", "cnc-02", "press-01"]:
        status = client.get_submodel_by_id(f"urn:factory:submodel:status:{machine}")
        if status:
            elements = status.get('submodelElements', [])
            if elements:
                value_str = elements[0].get('value', '{}')
                try:
                    value_data = json.loads(value_str)
                    print(f"  - {machine}: Status = {value_data.get('status', 'N/A')}")
                except:
                    print(f"  - {machine}: Found status submodel")
    
    print("\n" + "=" * 60)
    print("Query Complete")
    print("=" * 60)