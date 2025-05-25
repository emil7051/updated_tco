"""Centralised imports for common dependencies.

This module provides a single point of import for commonly used libraries
to reduce duplication and ensure consistent import patterns across the codebase.
"""

import hashlib
import json

# Standard library common imports
import logging
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache
from pathlib import Path

# Common typing imports
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Protocol,
    Sequence,
    Tuple,
    Union,
)

import numpy as np

# Core data manipulation libraries
import pandas as pd

# UI framework
import streamlit as st

# Export all commonly used imports
__all__ = [
    # Data libraries
    "pd",
    "np",
    "st",
    # Typing
    "Any",
    "Dict",
    "List",
    "Optional",
    "Tuple",
    "Union",
    "Mapping",
    "Sequence",
    "Protocol",
    "Iterable",
    # Standard library
    "logging",
    "dataclass",
    "field",
    "datetime",
    "json",
    "hashlib",
    "lru_cache",
    "Path",
]
