"""Centralised imports for common dependencies.

This module provides a single point of import for commonly used libraries
to reduce duplication and ensure consistent import patterns across the codebase.
"""

# Core data manipulation libraries
import pandas as pd
import numpy as np

# UI framework
import streamlit as st

# Common typing imports
from typing import (
    Any, Dict, List, Optional, Tuple, Union,
    Mapping, Sequence, Protocol, Iterable
)

# Standard library common imports
import logging
from dataclasses import dataclass, field
from datetime import datetime
import json
import hashlib
from functools import lru_cache
from pathlib import Path

# Export all commonly used imports
__all__ = [
    # Data libraries
    'pd', 'np', 'st',
    # Typing
    'Any', 'Dict', 'List', 'Optional', 'Tuple', 'Union',
    'Mapping', 'Sequence', 'Protocol', 'Iterable',
    # Standard library
    'logging', 'dataclass', 'field', 'datetime', 'json', 
    'hashlib', 'lru_cache', 'Path'
] 