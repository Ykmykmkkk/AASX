"""
Utility functions for AAS Integration
"""

import base64
import urllib.parse
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
import json


def encode_base64_url(identifier: str) -> str:
    """
    Encode identifier to BASE64-URL format as per AAS specification
    
    Args:
        identifier: The identifier to encode
        
    Returns:
        BASE64-URL encoded string
    """
    # Convert to bytes and encode to base64
    encoded_bytes = base64.urlsafe_b64encode(identifier.encode('utf-8'))
    # Convert to string and remove padding
    encoded_str = encoded_bytes.decode('utf-8').rstrip('=')
    return encoded_str


def decode_base64_url(encoded: str) -> str:
    """
    Decode BASE64-URL encoded identifier
    
    Args:
        encoded: BASE64-URL encoded string
        
    Returns:
        Decoded identifier
    """
    # Add padding if needed
    padding = 4 - (len(encoded) % 4)
    if padding != 4:
        encoded += '=' * padding
    
    # Decode from base64
    decoded_bytes = base64.urlsafe_b64decode(encoded.encode('utf-8'))
    return decoded_bytes.decode('utf-8')


def build_aas_path(shell_id: str, submodel_id: Optional[str] = None, 
                   element_path: Optional[str] = None) -> str:
    """
    Build AAS API path with proper encoding
    
    Args:
        shell_id: Shell identifier
        submodel_id: Optional submodel identifier
        element_path: Optional element path within submodel
        
    Returns:
        Properly formatted API path
    """
    # Encode shell ID
    encoded_shell = encode_base64_url(shell_id)
    path = f"/shells/{encoded_shell}"
    
    if submodel_id:
        # Encode submodel ID
        encoded_submodel = encode_base64_url(submodel_id)
        path += f"/submodels/{encoded_submodel}"
        
        if element_path:
            # Element paths use dot notation
            path += f"/submodel-elements/{element_path}"
    
    return path


def parse_aas_datetime(datetime_str: str) -> datetime:
    """
    Parse AAS datetime string to Python datetime
    
    Args:
        datetime_str: DateTime string in ISO format
        
    Returns:
        Python datetime object
    """
    # Handle different datetime formats
    formats = [
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(datetime_str, fmt)
        except ValueError:
            continue
    
    # If all formats fail, try ISO format
    return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))


def format_aas_datetime(dt: datetime) -> str:
    """
    Format Python datetime to AAS datetime string
    
    Args:
        dt: Python datetime object
        
    Returns:
        ISO formatted datetime string
    """
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def extract_id_short(uri: str) -> str:
    """
    Extract idShort from URI or return as-is if not a URI
    
    Args:
        uri: URI or identifier string
        
    Returns:
        Extracted idShort
    """
    if uri.startswith(("http://", "https://", "urn:")):
        # Extract last part after / or :
        parts = uri.replace(":", "/").split("/")
        return parts[-1]
    return uri


def validate_dsl_input(dsl_input: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate DSL input structure and required fields
    
    Args:
        dsl_input: DSL input dictionary
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check required fields
    if "goal" not in dsl_input:
        return False, "Missing 'goal' field in DSL input"
    
    if "parameters" not in dsl_input:
        return False, "Missing 'parameters' field in DSL input"
    
    goal = dsl_input["goal"]
    parameters = dsl_input.get("parameters", {})
    
    # Validate based on goal type
    if goal == "query_failed_jobs_with_cooling":
        if "date" not in parameters:
            return False, "Missing 'date' in parameters for query_failed_jobs_with_cooling"
        
        # Validate date format
        try:
            datetime.strptime(parameters["date"], "%Y-%m-%d")
        except ValueError:
            return False, f"Invalid date format: {parameters['date']}. Expected YYYY-MM-DD"
    
    elif goal == "track_product_position":
        if "product_id" not in parameters:
            return False, "Missing 'product_id' in parameters for track_product_position"
    
    elif goal == "detect_product_anomalies":
        if "timeframe" not in parameters:
            return False, "Missing 'timeframe' in parameters for detect_product_anomalies"
    
    elif goal == "predict_job_completion_time":
        if "job_id" not in parameters:
            return False, "Missing 'job_id' in parameters for predict_job_completion_time"
    
    else:
        return False, f"Unknown goal: {goal}"
    
    return True, None


def merge_results(primary: List[Dict], fallback: List[Dict]) -> List[Dict]:
    """
    Merge results from primary and fallback sources
    
    Args:
        primary: Primary results
        fallback: Fallback results
        
    Returns:
        Merged results with duplicates removed
    """
    # Create a set of unique identifiers from primary results
    primary_ids = set()
    for item in primary:
        if "job_id" in item:
            primary_ids.add(item["job_id"])
        elif "product_id" in item:
            primary_ids.add(item["product_id"])
        elif "id" in item:
            primary_ids.add(item["id"])
    
    # Add fallback results that aren't in primary
    merged = primary.copy()
    for item in fallback:
        item_id = None
        if "job_id" in item:
            item_id = item["job_id"]
        elif "product_id" in item:
            item_id = item["product_id"]
        elif "id" in item:
            item_id = item["id"]
        
        if item_id and item_id not in primary_ids:
            merged.append(item)
    
    return merged


def filter_by_date(items: List[Dict], date_field: str, target_date: str) -> List[Dict]:
    """
    Filter items by date
    
    Args:
        items: List of items to filter
        date_field: Name of the date field
        target_date: Target date in YYYY-MM-DD format
        
    Returns:
        Filtered list
    """
    filtered = []
    for item in items:
        if date_field in item:
            try:
                item_date = parse_aas_datetime(item[date_field])
                if item_date.strftime("%Y-%m-%d") == target_date:
                    filtered.append(item)
            except:
                # Skip items with invalid dates
                continue
    
    return filtered


def calculate_duration(start_time: str, end_time: str) -> float:
    """
    Calculate duration between two timestamps in minutes
    
    Args:
        start_time: Start timestamp
        end_time: End timestamp
        
    Returns:
        Duration in minutes
    """
    try:
        start = parse_aas_datetime(start_time)
        end = parse_aas_datetime(end_time)
        duration = (end - start).total_seconds() / 60
        return round(duration, 2)
    except:
        return 0.0


def safe_get_nested(data: Dict[str, Any], path: str, default: Any = None) -> Any:
    """
    Safely get nested dictionary value using dot notation
    
    Args:
        data: Dictionary to search
        path: Dot-separated path (e.g., "submodel.property.value")
        default: Default value if path not found
        
    Returns:
        Value at path or default
    """
    keys = path.split('.')
    current = data
    
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        elif isinstance(current, list) and key.isdigit():
            index = int(key)
            if 0 <= index < len(current):
                current = current[index]
            else:
                return default
        else:
            return default
    
    return current


def format_error_response(error_type: str, message: str, details: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Format standardized error response
    
    Args:
        error_type: Type of error
        message: Error message
        details: Optional additional details
        
    Returns:
        Formatted error response
    """
    response = {
        "error": True,
        "error_type": error_type,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    
    if details:
        response["details"] = details
    
    return response


def format_success_response(data: Any, message: Optional[str] = None, 
                          metadata: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Format standardized success response
    
    Args:
        data: Response data
        message: Optional success message
        metadata: Optional metadata
        
    Returns:
        Formatted success response
    """
    response = {
        "success": True,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
    
    if message:
        response["message"] = message
    
    if metadata:
        response["metadata"] = metadata
    
    return response