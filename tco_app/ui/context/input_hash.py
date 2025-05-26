"""Utility for hashing user inputs to detect changes."""

import hashlib
import json
from typing import Any, Dict


def generate_input_hash(inputs: Dict[str, Any]) -> str:
    """Generate a hash from user inputs to detect changes.
    
    Args:
        inputs: Dictionary of user inputs from sidebar
        
    Returns:
        SHA256 hash of the inputs
    """
    # Create a copy and remove non-hashable items
    hashable_inputs = {}
    
    for key, value in inputs.items():
        # Skip dataframes and other non-serialisable objects
        if key in ["modified_tables", "bev_vehicle_data", "diesel_vehicle_data"]:
            # For dataframes, we'll use their shape and key values
            if hasattr(value, "shape"):
                hashable_inputs[f"{key}_shape"] = str(value.shape)
            elif isinstance(value, dict):
                # For modified_tables, just track table names and shapes
                hashable_inputs[f"{key}_keys"] = sorted(value.keys())
        elif hasattr(value, "to_dict"):
            # Handle pandas Series/DataFrames
            hashable_inputs[key] = value.to_dict()
        else:
            # Regular values
            hashable_inputs[key] = value
    
    # Convert to JSON string with sorted keys for consistent hashing
    json_str = json.dumps(hashable_inputs, sort_keys=True, default=str)
    
    # Generate SHA256 hash
    return hashlib.sha256(json_str.encode()).hexdigest() 