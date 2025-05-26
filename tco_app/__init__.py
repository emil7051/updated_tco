"""TCO Application package.

This package contains the Total Cost of Ownership (TCO) calculator application
for comparing Battery Electric Vehicles (BEV) and diesel vehicles.
"""

import sys
import os

# Ensure the package root is in the Python path
package_root = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(package_root)

if project_root not in sys.path:
    sys.path.insert(0, project_root)
