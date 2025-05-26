"""Debug page for import diagnostics."""
import streamlit as st
import sys
import os
import importlib.util

def render():
    """Render import debug information."""
    st.header("Import Debug Information")
    
    # Show Python and environment info
    st.subheader("Environment Information")
    st.write(f"Python version: {sys.version}")
    st.write(f"Current working directory: {os.getcwd()}")
    st.write(f"__file__: {__file__}")
    
    # Show Python path
    st.subheader("Python Path (first 10 entries)")
    for i, path in enumerate(sys.path[:10]):
        st.write(f"{i}: {path}")
    
    # Check if components directory exists
    st.subheader("Directory Structure Check")
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    components_dir = os.path.join(project_root, 'tco_app', 'ui', 'components')
    st.write(f"Project root: {project_root}")
    st.write(f"Components dir: {components_dir}")
    st.write(f"Components dir exists: {os.path.exists(components_dir)}")
    
    if os.path.exists(components_dir):
        st.write("Files in components directory:")
        for file in os.listdir(components_dir):
            st.write(f"  - {file}")
    
    # Try various import methods
    st.subheader("Import Attempts")
    
    # Method 1: Package import
    try:
        from tco_app.ui.components import SensitivityContext
        st.success("✅ Method 1: Package import successful")
    except ImportError as e:
        st.error(f"❌ Method 1 failed: {e}")
    
    # Method 2: Direct module import
    try:
        import tco_app.ui.components.sensitivity_components as sc
        st.success("✅ Method 2: Direct module import successful")
    except ImportError as e:
        st.error(f"❌ Method 2 failed: {e}")
    
    # Method 3: Add to path and import
    try:
        if components_dir not in sys.path:
            sys.path.insert(0, components_dir)
        import sensitivity_components
        st.success("✅ Method 3: Path manipulation import successful")
    except ImportError as e:
        st.error(f"❌ Method 3 failed: {e}")
    
    # Method 4: importlib
    try:
        sensitivity_file = os.path.join(components_dir, 'sensitivity_components.py')
        spec = importlib.util.spec_from_file_location("sensitivity_components", sensitivity_file)
        sensitivity_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sensitivity_module)
        st.success("✅ Method 4: importlib import successful")
    except Exception as e:
        st.error(f"❌ Method 4 failed: {e}")
    
    # Check __init__.py
    st.subheader("__init__.py Check")
    init_file = os.path.join(components_dir, '__init__.py')
    st.write(f"__init__.py exists: {os.path.exists(init_file)}")
    if os.path.exists(init_file):
        st.write(f"__init__.py size: {os.path.getsize(init_file)} bytes") 