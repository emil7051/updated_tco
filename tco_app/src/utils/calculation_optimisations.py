"""Optimised calculation utilities."""

from tco_app.src import np
from tco_app.src import pd
from typing import List, Tuple, Dict
import numba


@numba.jit(nopython=True)
def fast_npv(cash_flows: np.ndarray, discount_rate: float) -> float:
    """Fast NPV calculation using Numba.

    Args:
        cash_flows: Array of cash flows
        discount_rate: Discount rate as decimal

    Returns:
        Net present value
    """
    npv = 0.0
    for t, cf in enumerate(cash_flows):
        npv += cf / ((1 + discount_rate) ** (t + 1))
    return npv


def vectorised_annual_costs(
    base_cost: float, growth_rate: float, years: int
) -> np.ndarray:
    """Return an array of annual costs.

    The earlier implementation relied on NumPy vectorisation, which carries a
    noticeable fixed overhead that dominates when *years* is very small (as in
    the unit-test that benchmarks 50 iterations).  A branch that swaps to a
    plain Python implementation for small arrays yields a consistent speed-up
    whilst still returning a NumPy-compatible *array-like* structure.
    """
    factor = 1.0 + growth_rate

    # For very small vectors, use pure Python to avoid NumPy overhead
    if years <= 100:
        result = []
        for year in range(years):
            cost = base_cost * (factor ** year)
            result.append(cost)
        return np.array(result)

    # For medium vectors, use NumPy pre-allocation with direct calculation for precision
    elif years <= 1000:
        out = np.empty(years, dtype=float)
        for i in range(years):
            out[i] = base_cost * (factor ** i)
        return out

    # For large vectors, NumPy vectorisation becomes beneficial
    else:
        exponents = np.arange(years, dtype=float)
        return base_cost * np.power(factor, exponents)


def batch_vehicle_lookup(
    vehicle_models: pd.DataFrame, vehicle_ids: List[str]
) -> pd.DataFrame:
    """Efficiently lookup multiple vehicles at once.

    Args:
        vehicle_models: DataFrame with vehicle data
        vehicle_ids: List of vehicle IDs

    Returns:
        DataFrame with requested vehicles
    """
    from tco_app.src.constants import DataColumns

    # Use isin for efficient filtering
    mask = vehicle_models[DataColumns.VEHICLE_ID].isin(vehicle_ids)
    return vehicle_models[mask]


@numba.jit(nopython=True)
def fast_discount_factors(discount_rate: float, years: int) -> np.ndarray:
    """Calculate discount factors using optimised computation.

    Args:
        discount_rate: Discount rate as decimal
        years: Number of years

    Returns:
        Array of discount factors
    """
    factors = np.zeros(years)
    base = 1.0 + discount_rate

    for i in range(years):
        factors[i] = 1.0 / (base ** (i + 1))

    return factors


def optimised_tco_calculation(
    annual_costs: np.ndarray,
    acquisition_cost: float,
    residual_value: float,
    discount_rate: float,
) -> float:
    """Optimised TCO calculation using vectorised operations.

    Args:
        annual_costs: Array of annual costs
        acquisition_cost: Initial acquisition cost
        residual_value: End-of-life residual value
        discount_rate: Discount rate as decimal

    Returns:
        Total cost of ownership
    """
    years = len(annual_costs)
    discount_factors = fast_discount_factors(discount_rate, years)

    # NPV of annual costs
    npv_annual = np.sum(annual_costs * discount_factors)

    # NPV of residual value (subtract as it's a benefit)
    npv_residual = residual_value / ((1 + discount_rate) ** years)

    return acquisition_cost + npv_annual - npv_residual


def batch_parameter_lookup(
    params_df: pd.DataFrame, param_keys: List[str], key_column: str, value_column: str
) -> Dict[str, float]:
    """Efficiently lookup multiple parameters at once.

    Args:
        params_df: DataFrame with parameters
        param_keys: List of parameter keys to lookup
        key_column: Column name containing keys
        value_column: Column name containing values

    Returns:
        Dictionary mapping keys to values
    """
    # Filter to requested keys only
    mask = params_df[key_column].isin(param_keys)
    filtered_df = params_df[mask]

    # Create lookup dictionary
    return dict(zip(filtered_df[key_column], filtered_df[value_column]))


@numba.jit(nopython=True)
def fast_cumulative_sum(values: np.ndarray) -> np.ndarray:
    """Fast cumulative sum calculation.

    Args:
        values: Array of values

    Returns:
        Cumulative sum array
    """
    result = np.zeros_like(values)
    result[0] = values[0]

    for i in range(1, len(values)):
        result[i] = result[i - 1] + values[i]

    return result


def optimised_emissions_calculation(
    annual_kms: float, emission_factor: float, years: int
) -> Tuple[float, float]:
    """Optimised emissions calculation.

    Args:
        annual_kms: Annual kilometres travelled
        emission_factor: Emission factor (kg CO2/km)
        years: Number of years

    Returns:
        Tuple of (annual_emissions, lifetime_emissions)
    """
    annual_emissions = annual_kms * emission_factor
    lifetime_emissions = annual_emissions * years

    return annual_emissions, lifetime_emissions
