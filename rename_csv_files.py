import os
import glob

def rename_files():
    # Paths
    tables_path = "tco_app/data/tables"
    dictionary_path = "tco_app/data/dictionary"
    
    # Rename files in tables directory
    for file_path in glob.glob(os.path.join(tables_path, "*.csv")):
        file_name = os.path.basename(file_path)
        # Remove the 'tco_tidytables_' prefix and fix double .csv extension
        new_name = file_name.replace('tco_tidytables_', '').replace('.csv.csv', '.csv')
        new_path = os.path.join(tables_path, new_name)
        os.rename(file_path, new_path)
        print(f"Renamed: {file_name} -> {new_name}")
    
    # Rename files in dictionary directory
    for file_path in glob.glob(os.path.join(dictionary_path, "*.csv")):
        file_name = os.path.basename(file_path)
        # Remove the 'tco_data_dictionary_' prefix and fix double .csv extension
        new_name = file_name.replace('tco_data_dictionary_', '').replace('.csv.csv', '.csv')
        new_path = os.path.join(dictionary_path, new_name)
        os.rename(file_path, new_path)
        print(f"Renamed: {file_name} -> {new_name}")

if __name__ == "__main__":
    rename_files() 

