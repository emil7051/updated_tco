from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Protocol

import pandas as pd
import streamlit as st

# --------------------------------------------------------------------------------------
# Data-layer abstraction (step 8 of CODEBASE_IMPROVEMENTS.md)
# --------------------------------------------------------------------------------------


class TableRepository(Protocol):
    """Read-only repository abstraction for tabular CSV/Parquet assets."""

    def get(self, table_name: str) -> pd.DataFrame:  # pragma: no cover – protocol
        ...

    def list_tables(self) -> List[str]:  # pragma: no cover – protocol
        ...


class CSVRepository:
    """Filesystem-backed repository where each table is a *\\*.csv* file."""

    def __init__(self, root_dir: str | Path):
        self.root_dir = Path(root_dir).expanduser().resolve()

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------

    def list_tables(self) -> List[str]:
        return [p.stem for p in self.root_dir.glob('*.csv')]

    def get(self, table_name: str) -> pd.DataFrame:
        path = self.root_dir / f'{table_name}.csv'
        if not path.exists():
            raise FileNotFoundError(f'No table named "{table_name}" under {self.root_dir}')
        return pd.read_csv(path)


# --------------------------------------------------------------------------------------
# Helper – factory
# --------------------------------------------------------------------------------------


def _default_repository() -> TableRepository:
    """Return a *TableRepository* inferred from environment or defaults."""

    env_dir = os.getenv('TCO_DATA_DIR')
    if env_dir:
        base = Path(env_dir)
    else:
        # Keep parity with legacy path: <package_root>/data/tables
        base = Path(__file__).resolve().parent.parent / 'data' / 'tables'

    return CSVRepository(base)


# --------------------------------------------------------------------------------------
# Public façade – preserves legacy signature so call-sites remain untouched.
# --------------------------------------------------------------------------------------


@st.cache_data
def load_data(repo: TableRepository | None = None) -> Dict[str, pd.DataFrame]:
    """Return all available tables as *DataFrame*s keyed by file stem.

    Parameters
    ----------
    repo
        Optional custom repository (e.g. *ParquetRepository* in future).  Falls
        back to a CSV repository rooted at *$TCO_DATA_DIR* or the historic
        `tco_app/data/tables` location.
    """

    repository = repo or _default_repository()
    return {name: repository.get(name) for name in repository.list_tables()}
