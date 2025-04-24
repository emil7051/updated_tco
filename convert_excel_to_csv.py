import pandas as pd
import os
import sys

def convert_excel_to_csv(excel_file, output_dir=None):
    """
    Convert all sheets in an Excel file to separate CSV files.
    
    Args:
        excel_file (str): Path to the Excel file
        output_dir (str, optional): Directory to save CSV files. If None, will use current directory.
    """
    if output_dir is None:
        output_dir = os.path.dirname(excel_file) or '.'
    
    # Make sure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Get filename without extension
    base_name = os.path.splitext(os.path.basename(excel_file))[0]
    
    print(f"Converting {excel_file} to CSV files...")
    
    # Read all sheets
    excel = pd.ExcelFile(excel_file)
    sheet_names = excel.sheet_names
    
    for sheet_name in sheet_names:
        print(f"Processing sheet: {sheet_name}")
        df = pd.read_excel(excel, sheet_name=sheet_name)
        
        # Create CSV filename
        csv_file = os.path.join(output_dir, f"{base_name}_{sheet_name}.csv")
        
        # Save to CSV
        df.to_csv(csv_file, index=False)
        print(f"Created: {csv_file}")
    
    print("Conversion complete!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python convert_excel_to_csv.py path/to/excel_file.xlsx [output_directory]")
        sys.exit(1)
    
    excel_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    convert_excel_to_csv(excel_file, output_dir) 