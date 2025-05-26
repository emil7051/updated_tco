"""Script to replace magic strings with constants."""
import os
import re
from typing import List, Tuple

# Define replacements
REPLACEMENTS = [
    # Column names - Finance
    ("'finance_description'", "DataColumns.FINANCE_DESCRIPTION"),
    ('"finance_description"', "DataColumns.FINANCE_DESCRIPTION"),
    ("'default_value'", "DataColumns.FINANCE_DEFAULT_VALUE"),
    ('"default_value"', "DataColumns.FINANCE_DEFAULT_VALUE"),
    
    # Column names - Battery
    ("'battery_description'", "DataColumns.BATTERY_DESCRIPTION"),
    ('"battery_description"', "DataColumns.BATTERY_DESCRIPTION"),
    
    # Column names - Vehicle
    ("'vehicle_id'", "DataColumns.VEHICLE_ID"),
    ('"vehicle_id"', "DataColumns.VEHICLE_ID"),
    ("'vehicle_type'", "DataColumns.VEHICLE_TYPE"),
    ('"vehicle_type"', "DataColumns.VEHICLE_TYPE"),
    ("'vehicle_drivetrain'", "DataColumns.VEHICLE_DRIVETRAIN"),
    ('"vehicle_drivetrain"', "DataColumns.VEHICLE_DRIVETRAIN"),
    ("'vehicle_model'", "DataColumns.VEHICLE_MODEL"),
    ('"vehicle_model"', "DataColumns.VEHICLE_MODEL"),
    ("'payload_t'", "DataColumns.PAYLOAD_T"),
    ('"payload_t"', "DataColumns.PAYLOAD_T"),
    ("'msrp_price'", "DataColumns.MSRP_PRICE"),
    ('"msrp_price"', "DataColumns.MSRP_PRICE"),
    ("'range_km'", "DataColumns.RANGE_KM"),
    ('"range_km"', "DataColumns.RANGE_KM"),
    ("'battery_capacity_kwh'", "DataColumns.BATTERY_CAPACITY_KWH"),
    ('"battery_capacity_kwh"', "DataColumns.BATTERY_CAPACITY_KWH"),
    ("'kwh_per100km'", "DataColumns.KWH_PER100KM"),
    ('"kwh_per100km"', "DataColumns.KWH_PER100KM"),
    ("'litres_per100km'", "DataColumns.LITRES_PER100KM"),
    ('"litres_per100km"', "DataColumns.LITRES_PER100KM"),
    ("'comparison_pair_id'", "DataColumns.COMPARISON_PAIR_ID"),
    ('"comparison_pair_id"', "DataColumns.COMPARISON_PAIR_ID"),
    
    # Column names - Charging
    ("'charging_id'", "DataColumns.CHARGING_ID"),
    ('"charging_id"', "DataColumns.CHARGING_ID"),
    ("'charging_approach'", "DataColumns.CHARGING_APPROACH"),
    ('"charging_approach"', "DataColumns.CHARGING_APPROACH"),
    ("'per_kwh_price'", "DataColumns.PER_KWH_PRICE"),
    ('"per_kwh_price"', "DataColumns.PER_KWH_PRICE"),
    
    # Column names - Infrastructure
    ("'infrastructure_id'", "DataColumns.INFRASTRUCTURE_ID"),
    ('"infrastructure_id"', "DataColumns.INFRASTRUCTURE_ID"),
    ("'infrastructure_description'", "DataColumns.INFRASTRUCTURE_DESCRIPTION"),
    ('"infrastructure_description"', "DataColumns.INFRASTRUCTURE_DESCRIPTION"),
    ("'infrastructure_price'", "DataColumns.INFRASTRUCTURE_PRICE"),
    ('"infrastructure_price"', "DataColumns.INFRASTRUCTURE_PRICE"),
    
    # Parameter keys
    ("'diesel_price'", "ParameterKeys.DIESEL_PRICE"),
    ('"diesel_price"', "ParameterKeys.DIESEL_PRICE"),
    ("'discount_rate_percent'", "ParameterKeys.DISCOUNT_RATE"),
    ('"discount_rate_percent"', "ParameterKeys.DISCOUNT_RATE"),
    ("'carbon_price'", "ParameterKeys.CARBON_PRICE"),
    ('"carbon_price"', "ParameterKeys.CARBON_PRICE"),
    ("'initial_depreciation_percent'", "ParameterKeys.INITIAL_DEPRECIATION"),
    ('"initial_depreciation_percent"', "ParameterKeys.INITIAL_DEPRECIATION"),
    ("'annual_depreciation_percent'", "ParameterKeys.ANNUAL_DEPRECIATION"),
    ('"annual_depreciation_percent"', "ParameterKeys.ANNUAL_DEPRECIATION"),
    ("'replacement_per_kwh_price'", "ParameterKeys.REPLACEMENT_COST"),
    ('"replacement_per_kwh_price"', "ParameterKeys.REPLACEMENT_COST"),
    ("'degradation_annual_percent'", "ParameterKeys.DEGRADATION_RATE"),
    ('"degradation_annual_percent"', "ParameterKeys.DEGRADATION_RATE"),
    ("'minimum_capacity_percent'", "ParameterKeys.MINIMUM_CAPACITY"),
    ('"minimum_capacity_percent"', "ParameterKeys.MINIMUM_CAPACITY"),
]

def update_file(filepath: str, replacements: List[Tuple[str, str]]) -> bool:
    """Update a single file with replacements."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    updated = False
    
    # Check if constants are imported
    has_import = "from tco_app.src.constants import" in content
    
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
            updated = True
    
    if updated and not has_import:
        # Add import at the top
        lines = content.split('\n')
        import_added = False
        
        for i, line in enumerate(lines):
            if line.startswith('from') or line.startswith('import'):
                # Add after first import
                lines.insert(i + 1, 
                    "from tco_app.src.constants import DataColumns, ParameterKeys"
                )
                import_added = True
                break
        
        if not import_added:
            lines.insert(0, 
                "from tco_app.src.constants import DataColumns, ParameterKeys"
            )
        
        content = '\n'.join(lines)
    
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    
    return False

def process_directory(root_dir: str):
    """Process all Python files in directory."""
    updated_files = []
    
    for root, dirs, files in os.walk(root_dir):
        # Skip test directories and virtual environments
        if any(skip in root for skip in ['tests', 'venv', '.venv', 'site-packages']):
            continue
            
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                if update_file(filepath, REPLACEMENTS):
                    updated_files.append(filepath)
    
    return updated_files

# Run the replacement
if __name__ == "__main__":
    updated = process_directory('tco_app')
    print(f"Updated {len(updated)} files:")
    for f in updated:
        print(f"  - {f}") 