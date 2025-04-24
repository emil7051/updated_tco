import streamlit as st
import pandas as pd
import os
import glob

@st.cache_data
def load_data():
    """
    Load all data tables from CSV files and return as a dictionary of DataFrames
    """
    # Base path to the data directory
    base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    
    # Path to the tables directory
    tables_path = os.path.join(base_path, "tables")
    
    # Dictionary to store all data tables
    data_tables = {}
    
    # Get all CSV files in the tables directory
    csv_files = glob.glob(os.path.join(tables_path, "*.csv"))
    
    # Load each CSV file into a separate DataFrame
    for file_path in csv_files:
        # Extract the table name from the file name (without extension)
        file_name = os.path.basename(file_path)
        table_name = os.path.splitext(file_name)[0]
        
        # Load the CSV file
        data_tables[table_name] = pd.read_csv(file_path)
    
    return data_tables
