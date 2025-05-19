# Implementation Plan: Step-by-Step Guide

This document provides a detailed, step-by-step plan for implementing the Australian Heavy Vehicle TCO Modeller application, breaking down the development process into manageable chunks.

## Phase 1: Project Setup & Core Data Models

### Step 1: Project Structure & Environment Setup (Estimated time: 1 day)

1. Create the project directory structure:
   ```
   aus-heavy-vehicle-tco/
   ├── app.py
   ├── requirements.txt
   ├── README.md
   ├── tco_model/
   ├── ui/
   ├── utils/
   ├── config/
   └── tests/
   ```

2. Create and populate `requirements.txt`:
   ```
   streamlit>=1.24.0
   pandas>=1.5.3
   numpy>=1.24.3
   numpy-financial>=1.0
   plotly>=5.14.1
   pydantic>=2.0.0
   pyyaml>=6.0
   openpyxl>=3.1.2
   pytest>=7.3.1
   ```

3. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

4. Create a minimal `app.py` to test the environment:
   ```python
   import streamlit as st
   
   st.title("Australian Heavy Vehicle TCO Modeller")
   st.write("Environment setup complete!")
   ```

5. Run the application to test:
   ```bash
   streamlit run app.py
   ```

### Step 2: Core Type Definitions and Constants (Estimated time: 0.5 day)

1. Create `config/constants.py` with application-wide constants:
   ```python
   """
   Constants used throughout the TCO Model application.
   """
   
   # General Constants
   DEFAULT_DESCRIPTION = ""
   DEFAULT_SCENARIO_NAME = "New Scenario"
   CURRENT_YEAR = 2023
   DEFAULT_CURRENCY = "AUD"
   
   # Analysis Constants
   MIN_ANALYSIS_YEARS = 1
   MAX_ANALYSIS_YEARS = 30
   
   # File Paths
   DEFAULT_CONFIG_DIR = "config"
   SCENARIOS_DIR = f"{DEFAULT_CONFIG_DIR}/scenarios"
   DEFAULTS_DIR = f"{DEFAULT_CONFIG_DIR}/defaults"
   
   # Calculation Constants
   DIESEL_CO2_EMISSION_FACTOR = 2.68  # kg CO2e/L of diesel
   DIESEL_ENERGY_CONTENT = 10.0  # kWh/L of diesel
   KWH_TO_MJ_FACTOR = 3.6  # 1 kWh = 3.6 MJ
   
   # Conversion Constants
   MJ_TO_KWH_FACTOR = 1 / KWH_TO_MJ_FACTOR
   L_TO_KM_FACTOR = 100  # 1 L/100km = 1 km/L
   
   # UI Constants
   PAGE_TITLE = "Heavy Vehicle TCO Modeller"
   PAGE_ICON = "🚚"
   PAGE_LAYOUT = "wide"
   SIDEBAR_STATE = "expanded"
   APP_TITLE = "Australian Heavy Vehicle TCO Modeller"
   APP_DESCRIPTION = """
   Compare the Total Cost of Ownership (TCO) for Battery Electric Trucks (BETs) 
   and Internal Combustion Engine (ICE) diesel trucks in Australia.
   """
   ```

2. Create `utils/conversions.py` with custom types and conversion functions:
   ```python
   """
   Utility functions for converting between different units and formats.
   """
   from typing import Dict, List, Optional, Union, NewType
   from config.constants import (
       DEFAULT_CURRENCY, DIESEL_ENERGY_CONTENT, KWH_TO_MJ_FACTOR
   )
   
   # Custom Types
   Percentage = NewType('Percentage', float)
   Decimal = NewType('Decimal', float)
   LitersPer100KM = NewType('LitersPer100KM', float)
   KWHPerKM = NewType('KWHPerKM', float)
   KWH = NewType('KWH', float)
   MJ = NewType('MJ', float)
   YearIndex = NewType('YearIndex', int)
   AUD = NewType('AUD', float)
   Kilometres = NewType('Kilometres', float)
   CalendarYear = NewType('CalendarYear', int)
   
   def percentage_to_decimal(percentage: Percentage) -> Decimal:
       """Convert a percentage value to its decimal equivalent."""
       return Decimal(percentage / 100.0)
   
   def decimal_to_percentage(decimal: Decimal) -> Percentage:
       """Convert a decimal value to its percentage equivalent."""
       return Percentage(decimal * 100.0)
   
   def l_per_100km_to_kwh_per_km(fuel_consumption: LitersPer100KM, 
                               energy_conversion_factor: float = DIESEL_ENERGY_CONTENT) -> KWHPerKM:
       """Convert diesel fuel consumption in L/100km to energy consumption in kWh/km."""
       return KWHPerKM((fuel_consumption / 100.0) * energy_conversion_factor)
   
   def kwh_to_mj(kwh: KWH) -> MJ:
       """Convert kilowatt-hours to megajoules."""
       return MJ(kwh * KWH_TO_MJ_FACTOR)
   
   def format_currency(value: Union[float, AUD], currency: str = DEFAULT_CURRENCY) -> str:
       """Format a value as currency."""
       return f"{currency} {value:,.2f}"
   ```

### Step 3: Financial Utilities (Estimated time: 0.5 day)

Create `utils/financial.py` with financial calculation functions:

```python
"""
Financial utility functions for the TCO Model.
"""
from typing import Dict, List, Optional, Tuple, NewType, Union, TypedDict
import numpy as np
from utils.conversions import percentage_to_decimal, Decimal, Percentage

# Custom Types for Financial Domain
AUD = NewType('AUD', float)
Years = NewType('Years', int)
Rate = NewType('Rate', float)

def calculate_loan_payment(
    principal: AUD,
    interest_rate: Percentage,
    loan_term_years: Years
) -> AUD:
    """Calculate regular loan payment using the PMT formula."""
    r_decimal: Decimal = percentage_to_decimal(interest_rate)
    rate_per_period: Rate = Rate(r_decimal / 12)
    n_payments: int = loan_term_years * 12
    
    if rate_per_period == 0:
        return AUD(principal / n_payments)
    
    payment = principal * (rate_per_period * (1 + rate_per_period)**n_payments) / ((1 + rate_per_period)**n_payments - 1)
    return AUD(payment)

def calculate_residual_value(
    initial_value: AUD,
    age_years: Years,
    depreciation_rate: Percentage
) -> AUD:
    """Calculate residual value using exponential depreciation."""
    r_decimal: Decimal = percentage_to_decimal(depreciation_rate)
    effective_rate = min(r_decimal, Decimal(1.0))
    residual_value: float = initial_value * (1 - effective_rate) ** age_years
    return AUD(max(0.0, residual_value))
```

### Step 4: Vehicle Models (Estimated time: 1 day)

Create `tco_model/vehicles.py` to define the vehicle classes:

```python
"""
Vehicle classes for the TCO Model.
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional, Union, Literal, Protocol
from pydantic import BaseModel, Field, model_validator, ConfigDict
import math

from utils.financial import AUD, Years, Percentage
from utils.conversions import Kilometres, KWH, LitersPer100KM, KWHPerKM, Decimal, CalendarYear

# Type Aliases
ResidualValueProjections = Dict[Years, Percentage]
BatteryCostProjections = Dict[CalendarYear, AUD]

# Strategy Protocols
class EnergyConsumptionStrategy(Protocol):
    """Protocol defining the interface for energy consumption strategies."""
    def calculate_consumption(self, distance_km: Kilometres) -> float:
        """Calculate energy consumption for a given distance."""
        ...
    
    @property
    def unit(self) -> str:
        """Return the unit of energy consumption."""
        ...

class MaintenanceStrategy(Protocol):
    """Protocol defining the interface for maintenance cost strategies."""
    def calculate_base_annual_cost(self, vehicle: 'Vehicle', scenario: 'Scenario') -> AUD:
        """Calculate the base annual maintenance cost."""
        ...

# Strategy Implementations
class DieselConsumptionStrategy:
    """Strategy for calculating diesel consumption."""
    def __init__(self, l_per_km: float):
        self.l_per_km = l_per_km
    
    def calculate_consumption(self, distance_km: Kilometres) -> float:
        """Returns consumption in Litres."""
        return float(distance_km) * self.l_per_km
    
    @property
    def unit(self) -> str:
        return "L"

class ElectricConsumptionStrategy:
    """Strategy for calculating electricity consumption."""
    def __init__(self, kwh_per_km: KWHPerKM):
        self.kwh_per_km = kwh_per_km
    
    def calculate_consumption(self, distance_km: Kilometres) -> KWH:
        """Returns consumption in KWH."""
        consumption_float = float(distance_km) * float(self.kwh_per_km)
        return KWH(consumption_float)
    
    @property
    def unit(self) -> str:
        return "kWh"

# Base Vehicle Model
class Vehicle(BaseModel, ABC):
    """Abstract base class for all vehicle types."""
    
    name: str = Field(..., description="Unique identifier for the vehicle.")
    vehicle_type: Literal["rigid", "articulated"] = Field(..., description="Type of heavy vehicle.")
    base_purchase_price_aud: AUD = Field(..., gt=0, description="Initial purchase price in AUD.")
    lifespan_years: Years = Field(..., gt=0, description="Expected operational lifespan in years.")
    residual_value_percent_projections: ResidualValueProjections = Field(
        ...,
        description="Residual value percentage (0.0-1.0) at specific years."
    )
    base_registration_cost_aud: AUD = Field(..., ge=0, description="Base annual registration cost in AUD.")
    
    model_config = ConfigDict(extra='allow')
    
    @property
    @abstractmethod
    def energy_consumption_strategy(self) -> EnergyConsumptionStrategy:
        """Return the appropriate energy consumption strategy."""
        pass
    
    def calculate_energy_consumption(self, distance_km: Kilometres) -> float:
        """Calculate energy consumption for a given distance."""
        return self.energy_consumption_strategy.calculate_consumption(distance_km)
    
    def calculate_annual_energy_cost(
        self, annual_mileage_km: Kilometres, energy_price_aud_per_unit: AUD
    ) -> AUD:
        """Calculate annual energy cost based on consumption and price."""
        consumption: float = self.calculate_energy_consumption(annual_mileage_km)
        cost_float = consumption * float(energy_price_aud_per_unit)
        return AUD(cost_float)
    
    def calculate_residual_value_aud(self, age_years: Years) -> AUD:
        """Calculate residual value at a given age using interpolation."""
        if age_years < 0:
            raise ValueError("Age must be non-negative.")
        
        sorted_years = sorted(self.residual_value_percent_projections.keys())
        
        if not sorted_years:
            return AUD(0.0)
        
        if age_years <= sorted_years[0]:
            year1, pct1 = Years(0), Percentage(1.0)
            year2, pct2 = sorted_years[0], self.residual_value_percent_projections[sorted_years[0]]
        elif age_years >= sorted_years[-1]:
            return AUD(self.base_purchase_price_aud * float(self.residual_value_percent_projections[sorted_years[-1]]))
        else:
            # Find years that bracket the age
            for i in range(len(sorted_years) - 1):
                if sorted_years[i] <= age_years < sorted_years[i+1]:
                    year1, pct1 = sorted_years[i], self.residual_value_percent_projections[sorted_years[i]]
                    year2, pct2 = sorted_years[i+1], self.residual_value_percent_projections[sorted_years[i+1]]
                    break
            else:
                return AUD(self.base_purchase_price_aud * float(self.residual_value_percent_projections[sorted_years[-1]]))
        
        # Linear interpolation
        if year2 == year1:
            current_value_pct_float = float(pct1)
        else:
            current_value_pct_float = float(pct1) + (float(age_years) - float(year1)) * (float(pct2) - float(pct1)) / (float(year2) - float(year1))
        
        current_value_pct_float = max(0.0, min(1.0, current_value_pct_float))
        return AUD(self.base_purchase_price_aud * current_value_pct_float)
    
    @property
    @abstractmethod
    def maintenance_strategy(self) -> MaintenanceStrategy:
        """Return the appropriate maintenance cost strategy."""
        pass

# Electric Vehicle Model
class ElectricVehicle(Vehicle):
    """Electric vehicle implementation."""
    
    battery_capacity_kwh: KWH = Field(..., gt=0)
    energy_consumption_kwh_per_km: KWHPerKM = Field(..., gt=0)
    battery_warranty_years: Years = Field(default=Years(8), ge=0)
    battery_pack_cost_aud_per_kwh_projections: BatteryCostProjections = Field(...)
    battery_cycle_life: int = Field(default=1500, gt=0)
    battery_depth_of_discharge_percent: Percentage = Field(default=Percentage(80.0), ge=0, le=100.0)
    charging_efficiency_percent: Percentage = Field(default=Percentage(90.0), gt=0, le=100.0)
    purchase_price_annual_decrease_rate_real: Decimal = Field(default=Decimal(0.0), ge=0)
    
    _strategy_instance: Optional[ElectricConsumptionStrategy] = None
    _maintenance_strategy_instance: Optional[ElectricMaintenanceStrategy] = None
    
    @property
    def energy_consumption_strategy(self) -> ElectricConsumptionStrategy:
        """Return the electric consumption strategy."""
        if self._strategy_instance is None:
            self._strategy_instance = ElectricConsumptionStrategy(self.energy_consumption_kwh_per_km)
        return self._strategy_instance
    
    def calculate_battery_degradation_factor(self, age_years: Years, total_mileage_km: Kilometres) -> float:
        """Estimate battery capacity degradation factor (0.0-1.0)."""
        if age_years < 0 or total_mileage_km < 0:
            raise ValueError("Age and mileage must be non-negative.")
        
        # Battery degradation model parameters
        CYCLE_AGING_WEIGHT = 0.7
        CALENDAR_AGING_WEIGHT = 0.3
        END_OF_LIFE_THRESHOLD_LOSS_FRACTION = 0.2
        
        # Calculate energy throughput
        charging_efficiency_frac = float(self.charging_efficiency_percent) / 100.0
        if charging_efficiency_frac == 0:
            return 1.0
        
        # Calculate equivalent cycles
        energy_drawn_from_grid_per_km = KWHPerKM(self.energy_consumption_kwh_per_km / charging_efficiency_frac)
        total_energy_throughput_kwh = KWH(float(total_mileage_km) * float(energy_drawn_from_grid_per_km))
        
        depth_of_discharge_frac = float(self.battery_depth_of_discharge_percent) / 100.0
        usable_capacity_per_cycle_kwh = KWH(self.battery_capacity_kwh * depth_of_discharge_frac)
        
        if usable_capacity_per_cycle_kwh == 0:
            return 1.0
        
        equivalent_cycles = float(total_energy_throughput_kwh) / float(usable_capacity_per_cycle_kwh)
        
        # Calculate degradation factors
        cycle_degradation = min(1.0, equivalent_cycles / self.battery_cycle_life) if self.battery_cycle_life > 0 else 0.0
        calendar_degradation = min(1.0, float(age_years) / float(self.lifespan_years)) if self.lifespan_years > 0 else 0.0
        
        # Combined degradation
        total_normalized_degradation = (CYCLE_AGING_WEIGHT * cycle_degradation + CALENDAR_AGING_WEIGHT * calendar_degradation)
        
        # Calculate remaining capacity
        remaining_capacity_fraction = max(0.0, 1.0 - (total_normalized_degradation * END_OF_LIFE_THRESHOLD_LOSS_FRACTION))
        
        return remaining_capacity_fraction
    
    @property
    def maintenance_strategy(self) -> MaintenanceStrategy:
        """Return the electric maintenance strategy."""
        if self._maintenance_strategy_instance is None:
            self._maintenance_strategy_instance = ElectricMaintenanceStrategy()
        return self._maintenance_strategy_instance

# Diesel Vehicle Model
class DieselVehicle(Vehicle):
    """Diesel vehicle implementation."""
    
    fuel_consumption_l_per_100km: LitersPer100KM = Field(..., gt=0)
    co2_emission_factor_kg_per_l: float = Field(..., ge=0)
    
    _fuel_consumption_l_per_km: float = 0.0
    _strategy_instance: Optional[DieselConsumptionStrategy] = None
    _maintenance_strategy_instance: Optional[DieselMaintenanceStrategy] = None
    
    @model_validator(mode='after')
    def _calculate_l_per_km(self) -> 'DieselVehicle':
        """Calculate L/km from L/100km."""
        if self.fuel_consumption_l_per_100km is not None:
            self._fuel_consumption_l_per_km = float(self.fuel_consumption_l_per_100km) / 100.0
        return self
    
    @property
    def fuel_consumption_l_per_km(self) -> float:
        """Get the fuel consumption in L/km."""
        if self._fuel_consumption_l_per_km == 0.0 and self.fuel_consumption_l_per_100km > 0:
            self._fuel_consumption_l_per_km = float(self.fuel_consumption_l_per_100km) / 100.0
        return self._fuel_consumption_l_per_km
    
    @property
    def energy_consumption_strategy(self) -> DieselConsumptionStrategy:
        """Return the diesel consumption strategy."""
        if self._strategy_instance is None:
            l_per_km = self.fuel_consumption_l_per_km
            self._strategy_instance = DieselConsumptionStrategy(l_per_km)
        return self._strategy_instance
    
    @property
    def maintenance_strategy(self) -> MaintenanceStrategy:
        """Return the diesel maintenance strategy."""
        if self._maintenance_strategy_instance is None:
            self._maintenance_strategy_instance = DieselMaintenanceStrategy()
        return self._maintenance_strategy_instance

# Maintenance Strategy Implementations
class DieselMaintenanceStrategy:
    """Strategy for calculating diesel vehicle maintenance costs."""
    def calculate_base_annual_cost(self, vehicle: Vehicle, scenario: 'Scenario') -> AUD:
        vehicle_typed: DieselVehicle = vehicle
        class_prefix: str = vehicle_typed.vehicle_type
        detail_key = f"{class_prefix}_diesel"
        
        # Get maintenance details from scenario
        if detail_key not in scenario.maintenance_costs_detailed:
            return AUD(0.0)
        
        maint_details = scenario.maintenance_costs_detailed[detail_key]
        try:
            min_cost = float(maint_details.get('annual_cost_min_aud', 0))
            max_cost = float(maint_details.get('annual_cost_max_aud', 0))
            base_annual_cost_float = (min_cost + max_cost) / 2.0
            return AUD(base_annual_cost_float)
        except (TypeError, ValueError):
            return AUD(0.0)

class ElectricMaintenanceStrategy:
    """Strategy for calculating electric vehicle maintenance costs."""
    def calculate_base_annual_cost(self, vehicle: Vehicle, scenario: 'Scenario') -> AUD:
        vehicle_typed: ElectricVehicle = vehicle
        class_prefix: str = vehicle_typed.vehicle_type
        detail_key = f"{class_prefix}_bet"
        
        # Get maintenance details from scenario
        if detail_key not in scenario.maintenance_costs_detailed:
            return AUD(0.0)
        
        maint_details = scenario.maintenance_costs_detailed[detail_key]
        try:
            min_cost = float(maint_details.get('annual_cost_min_aud', 0))
            max_cost = float(maint_details.get('annual_cost_max_aud', 0))
            base_annual_cost_float = (min_cost + max_cost) / 2.0
            return AUD(base_annual_cost_float)
        except (TypeError, ValueError):
            return AUD(0.0)
```

### Step 5: Scenario Models (Estimated time: 1.5 days)

Create `tco_model/scenarios.py` to define the scenario models:

```python
"""
Scenario models for the TCO Model.
"""
import os
import yaml
import logging
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from pydantic import (
    BaseModel, ConfigDict, Field, PrivateAttr, ValidationInfo,
    field_validator, model_validator
)

from .vehicles import ElectricVehicle, DieselVehicle
from utils.conversions import CalendarYear

logger = logging.getLogger(__name__)

# Component Models for Scenario
class EconomicParameters(BaseModel):
    discount_rate_percent_real: float = Field(..., description="Real annual discount rate (e.g., 3.0 for 3%)", ge=0)
    inflation_rate_percent: Optional[float] = Field(2.5, description="Assumed general inflation rate (e.g., 2.5 for 2.5%)", ge=0)

class OperationalParameters(BaseModel):
    annual_mileage_km: float = Field(..., description="Average annual kilometers driven", gt=0)

class FinancingOptions(BaseModel):
    financing_method: str = Field("loan", description="Method of vehicle acquisition (cash or loan)")
    down_payment_percent: float = Field(20.0, description="Down payment percentage for loan financing", ge=0, le=100.0)
    loan_term_years: int = Field(5, description="Loan term in years", gt=0)
    loan_interest_rate_percent: float = Field(5.0, description="Annual interest rate for loan", ge=0)

class InfrastructureCosts(BaseModel):
    """Models costs associated with charging infrastructure."""
    charger_hardware_costs_aud: Optional[Dict[str, float]] = Field(None, description="Costs for different types of charger hardware (AUD)")
    selected_charger_cost_aud: float = Field(..., description="Cost of the selected charger hardware (AUD)", ge=0)
    selected_installation_cost_aud: float = Field(..., description="Cost of installing the selected charger (AUD)", ge=0)
    charger_maintenance_annual_rate_percent: float = Field(1.0, description="Annual charger maintenance as a percentage of hardware cost", ge=0)
    charger_lifespan_years: int = Field(10, description="Lifespan of the charger in years", gt=0)
    model_config = ConfigDict(extra='allow')

class ElectricityPricePoint(BaseModel):
    """Represents a single price point, which could be a single value or a range."""
    price_aud_per_kwh_or_range: Union[float, List[float]] = Field(..., description="Price in AUD/kWh or a [min, max] range")
    
    @field_validator('price_aud_per_kwh_or_range')
    @classmethod
    def check_list_length(cls, v):
        if isinstance(v, list):
            if len(v) != 2:
                raise ValueError("Price range list must contain exactly two values [min, max]")
            if v[0] > v[1]:
                raise ValueError("Min price cannot be greater than max price in range")
        return v

    def get_average_price_aud_per_kwh(self) -> float:
        """Returns the average price, or the single value if not a range."""
        if isinstance(self.price_aud_per_kwh_or_range, list):
            return sum(self.price_aud_per_kwh_or_range) / 2.0
        return float(self.price_aud_per_kwh_or_range)

class ElectricityPriceScenario(BaseModel):
    """Represents projected electricity prices for a named scenario."""
    name: str
    prices: Dict[int, ElectricityPricePoint]  # Year -> PricePoint

class ElectricityPriceProjections(BaseModel):
    """Container for multiple electricity price scenarios."""
    scenarios: List[ElectricityPriceScenario]
    selected_scenario_name: str = Field(..., description="Name of the electricity price scenario to use")
    
    @model_validator(mode='before')
    @classmethod
    def check_selected_scenario_exists(cls, values):
        scenarios = values.get('scenarios')
        selected_name = values.get('selected_scenario_name')
        if scenarios and selected_name:
            if not any(s.get('name') == selected_name for s in scenarios if isinstance(s, dict)) and \
               not any(s.name == selected_name for s in scenarios if not isinstance(s, dict)):
                raise ValueError(f"Selected electricity scenario '{selected_name}' not found in provided scenarios.")
        return values

class DieselPriceScenarioData(BaseModel):
    """Represents diesel price data, either a single value or yearly projections."""
    price_aud_per_l_or_projection: Union[float, Dict[int, float]] = Field(..., description="Constant price (AUD/L) or projection {year: price}")
    
    def get_price_aud_per_l_for_year(self, year: int) -> float:
        """Gets the diesel price for a specific year using interpolation/extrapolation."""
        if isinstance(self.price_aud_per_l_or_projection, (int, float)):
            return float(self.price_aud_per_l_or_projection)
        elif isinstance(self.price_aud_per_l_or_projection, dict):
            prices = self.price_aud_per_l_or_projection
            if not prices:
                raise ValueError("Diesel price projection dictionary cannot be empty.")
                
            sorted_proj_years = sorted(prices.keys())
            
            if year in prices:
                return float(prices[year])
            elif year < sorted_proj_years[0]:
                return float(prices[sorted_proj_years[0]])
            elif year > sorted_proj_years[-1]:
                return float(prices[sorted_proj_years[-1]])
            else:
                # Interpolate linearly
                prev_year = max(y for y in sorted_proj_years if y < year)
                next_year = min(y for y in sorted_proj_years if y > year)
                prev_price = float(prices[prev_year])
                next_price = float(prices[next_year])
                
                interpolation_factor = (year - prev_year) / (next_year - prev_year)
                interpolated_price = prev_price + interpolation_factor * (next_price - prev_price)
                return interpolated_price
        else:
            raise ValueError(f"Invalid diesel price data format: {self.price_aud_per_l_or_projection}")

class DieselPriceScenario(BaseModel):
    """Represents a named diesel price scenario."""
    name: str
    data: DieselPriceScenarioData

class DieselPriceProjections(BaseModel):
    """Container for multiple diesel price scenarios."""
    scenarios: List[DieselPriceScenario]
    selected_scenario_name: str = Field(..., description="Name of the diesel price scenario to use")
    
    @model_validator(mode='before')
    @classmethod
    def check_selected_scenario_exists(cls, values):
        scenarios = values.get('scenarios')
        selected_name = values.get('selected_scenario_name')
        if scenarios and selected_name:
            if not any(s.get('name') == selected_name for s in scenarios if isinstance(s, dict)) and \
               not any(s.name == selected_name for s in scenarios if not isinstance(s, dict)):
                raise ValueError(f"Selected diesel scenario '{selected_name}' not found in provided scenarios.")
        return values

class InsuranceRegistrationDetail(BaseModel):
    """Detailed insurance and registration costs."""
    base_annual_cost_aud: float = Field(..., description="Base annual cost (AUD)", ge=0)
    cost_type: str = Field("fixed", description="Type of cost ('fixed', 'percentage_of_value')")
    annual_rate_percent_of_value: Optional[float] = Field(None, description="Annual rate as % of vehicle value", ge=0)
    model_config = ConfigDict(extra='allow')

class InsuranceRegistrationCosts(BaseModel):
    """Container for insurance and registration costs per vehicle type."""
    electric: InsuranceRegistrationDetail
    diesel: InsuranceRegistrationDetail

class CarbonTaxConfig(BaseModel):
    include_carbon_tax: bool = Field(True, description="Include carbon tax in calculations")
    initial_rate_aud_per_tonne_co2e: float = Field(0.0, description="Initial carbon tax rate (AUD/tonne CO2e)", ge=0)
    annual_increase_rate_percent: float = Field(0.0, description="Annual increase rate for carbon tax", ge=0)

class RoadUserChargeConfig(BaseModel):
    include_road_user_charge: bool = Field(True, description="Include road user charge in calculations")
    initial_charge_aud_per_km: float = Field(0.0, description="Initial road user charge (AUD/km)", ge=0)
    annual_increase_rate_percent: float = Field(0.0, description="Annual increase rate for road user charge", ge=0)

class GeneralCostIncreaseRates(BaseModel):
    maintenance_annual_increase_rate_percent: float = Field(0.0, description="Annual increase rate for maintenance costs", ge=0)
    insurance_annual_increase_rate_percent: float = Field(0.0, description="Annual increase rate for insurance costs", ge=0)
    registration_annual_increase_rate_percent: float = Field(0.0, description="Annual increase rate for registration costs", ge=0)

class BatteryReplacementConfig(BaseModel):
    enable_battery_replacement: bool = Field(True, description="Enable battery replacement logic")
    annual_degradation_rate_percent: float = Field(2.0, description="Annual battery capacity degradation rate", ge=0, le=100.0)
    replacement_threshold_fraction: Optional[float] = Field(0.7, description="Capacity threshold (fraction, 0 to 1) to trigger replacement", ge=0, le=1.0)
    force_replacement_year_index: Optional[int] = Field(None, description="Force battery replacement in this specific year index (0-based)", ge=0)

# Main Scenario Model
class Scenario(BaseModel):
    """Represents a TCO calculation scenario using composed parameter objects."""

    # General
    name: str = Field(default="Default Scenario", description="Unique identifier for the scenario")
    description: Optional[str] = Field(None, description="Optional description")
    analysis_period_years: int = Field(..., description="Duration of the analysis in years", gt=0)
    analysis_start_year: int = Field(datetime.now().year, description="Starting calendar year for the analysis")

    # Economic Parameters
    economic_parameters: EconomicParameters

    # Operational Parameters
    operational_parameters: OperationalParameters

    # Vehicles
    electric_vehicle: ElectricVehicle
    diesel_vehicle: DieselVehicle

    # Financing Options
    financing_options: FinancingOptions

    # Infrastructure
    infrastructure_costs: InfrastructureCosts

    # Price Projections
    electricity_price_projections: ElectricityPriceProjections
    diesel_price_projections: DieselPriceProjections

    # Other costs
    maintenance_costs_detailed: Dict[str, Dict[str, Any]] = Field(..., description="Detailed maintenance costs keyed by type")
    insurance_registration_costs: InsuranceRegistrationCosts
    carbon_tax_config: CarbonTaxConfig
    road_user_charge_config: RoadUserChargeConfig

    # General cost increases
    general_cost_increase_rates: GeneralCostIncreaseRates

    # Battery replacement
    battery_replacement_config: BatteryReplacementConfig

    # Optional explicit battery costs
    battery_pack_cost_aud_per_kwh_projections: Optional[Dict[int, float]] = Field(None, description="Optional: Explicit battery pack cost projections (AUD/kWh by year)")

    # Internal state for caching
    _generated_prices_cache: Dict[str, List[float]] = PrivateAttr(default_factory=dict)

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True
    )

    @property
    def analysis_end_year(self) -> int:
        """Calculate the end year from start_year and analysis_years."""
        return self.analysis_start_year + self.analysis_period_years - 1

    @property
    def analysis_calendar_years(self) -> List[int]:
        """Returns the list of calendar years in the analysis period."""
        return list(range(self.analysis_start_year, self.analysis_start_year + self.analysis_period_years))

    @model_validator(mode='after')
    def _calculate_and_cache_annual_prices(self) -> 'Scenario':
        """Generate annual price series for relevant costs after model initialization."""
        self._generated_prices_cache = {}
        
        years = self.analysis_period_years
        start_year = self.analysis_start_year

        # Carbon Tax and Road User Charge
        ct_base = self.carbon_tax_config.initial_rate_aud_per_tonne_co2e
        ct_inc = self.carbon_tax_config.annual_increase_rate_percent / 100.0
        ruc_base = self.road_user_charge_config.initial_charge_aud_per_km
        ruc_inc = self.road_user_charge_config.annual_increase_rate_percent / 100.0

        self._generated_prices_cache['carbon_tax_rate_aud_per_tonne'] = [ct_base * ((1 + ct_inc) ** i) for i in range(years)]
        self._generated_prices_cache['road_user_charge_aud_per_km'] = [ruc_base * ((1 + ruc_inc) ** i) for i in range(years)]

        # Electricity Prices
        elec_prices = []
        if self.electricity_price_projections:
            selected_scen_name = self.electricity_price_projections.selected_scenario_name
            selected_scen = next((s for s in self.electricity_price_projections.scenarios if s.name == selected_scen_name), None)
            if selected_scen:
                 proj_prices = selected_scen.prices
                 sorted_proj_years = sorted(proj_prices.keys())

                 for i in range(years):
                     current_year = start_year + i
                     if current_year in proj_prices:
                         elec_prices.append(proj_prices[current_year].get_average_price_aud_per_kwh())
                     elif current_year < sorted_proj_years[0]:
                          elec_prices.append(proj_prices[sorted_proj_years[0]].get_average_price_aud_per_kwh())
                     elif current_year > sorted_proj_years[-1]:
                          elec_prices.append(proj_prices[sorted_proj_years[-1]].get_average_price_aud_per_kwh())
                     else:
                         # Interpolate
                         prev_year = max(y for y in sorted_proj_years if y < current_year)
                         next_year = min(y for y in sorted_proj_years if y > current_year)
                         prev_price = proj_prices[prev_year].get_average_price_aud_per_kwh()
                         next_price = proj_prices[next_year].get_average_price_aud_per_kwh()
                         interpolation_factor = (current_year - prev_year) / (next_year - prev_year)
                         interpolated_price = prev_price + interpolation_factor * (next_price - prev_price)
                         elec_prices.append(interpolated_price)
            else:
                 raise ValueError(f"Selected electricity scenario '{selected_scen_name}' not found.")
        else:
             raise ValueError("Electricity price projections are required.")

        self._generated_prices_cache['electricity_price_aud_per_kwh'] = elec_prices

        # Diesel Prices
        diesel_prices = []
        if self.diesel_price_projections:
            selected_scen_name = self.diesel_price_projections.selected_scenario_name
            selected_scen = next((s for s in self.diesel_price_projections.scenarios if s.name == selected_scen_name), None)
            if selected_scen:
                 for i in range(years):
                      current_year = start_year + i
                      diesel_prices.append(selected_scen.data.get_price_aud_per_l_for_year(current_year))
            else:
                 raise ValueError(f"Selected diesel scenario '{selected_scen_name}' not found.")
        else:
             raise ValueError("Diesel price projections are required.")

        self._generated_prices_cache['diesel_price_aud_per_l'] = diesel_prices

        return self

    def get_annual_price(self, cost_type_key: str, calculation_year_index: int) -> Optional[float]:
        """Retrieve a pre-calculated annual price for a given cost type and year index."""
        if calculation_year_index < 0 or calculation_year_index >= self.analysis_period_years:
            return None

        if not self._generated_prices_cache:
             self._calculate_and_cache_annual_prices()

        price_series = self._generated_prices_cache.get(cost_type_key)
        if price_series is None:
            return None

        if calculation_year_index >= len(price_series):
             return None

        return price_series[calculation_year_index]

    @field_validator('battery_replacement_config')
    @classmethod
    def check_replacement_year_bounds(cls, v: BatteryReplacementConfig, info: ValidationInfo):
        """Validate that force_replacement_year_index is within the analysis period if set."""
        if v.force_replacement_year_index is not None and 'analysis_period_years' in info.data:
             analysis_years = info.data['analysis_period_years']
             if v.force_replacement_year_index >= analysis_years:
                 raise ValueError(f"force_replacement_year_index ({v.force_replacement_year_index}) "
                                  f"must be less than analysis_period_years ({analysis_years}). Note: 0-based index.")
        return v

    @classmethod
    def from_file(cls, filepath: str) -> 'Scenario':
        """Load a scenario from a YAML file."""
        logger.info(f"Loading scenario from: {filepath}")
        if not os.path.exists(filepath):
            logger.error(f"Scenario file not found: {filepath}")
            raise FileNotFoundError(f"Scenario file not found: {filepath}")
        try:
            with open(filepath, 'r') as f:
                data = yaml.safe_load(f)
            if data is None:
                 raise ValueError(f"YAML file is empty or invalid: {filepath}")
            scenario = cls(**data)
            logger.info(f"Successfully loaded scenario: {scenario.name}")
            return scenario
        except Exception as e:
            logger.error(f"Error creating Scenario object from file {filepath}: {e}", exc_info=True)
            raise ValueError(f"Error creating Scenario object from file: {e}") from e

    def to_file(self, filepath: str) -> None:
        """Save the current scenario configuration to a YAML file."""
        logger.info(f"Saving scenario '{self.name}' to: {filepath}")
        try:
            data_to_save = self.model_dump(exclude={'_generated_prices_cache'})

            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            with open(filepath, 'w') as f:
                yaml.dump(data_to_save, f, sort_keys=False, default_flow_style=False)
            logger.info(f"Successfully saved scenario '{self.name}'.")
        except Exception as e:
            logger.error(f"Error saving scenario '{self.name}' to file {filepath}: {e}", exc_info=True)
            raise IOError(f"Failed to save scenario to {filepath}") from e
```

## Phase 2: Cost Components and TCO Calculator

### Step 6: Cost Components (Estimated time: 1.5 days)

Create `tco_model/components.py` to define the cost component classes:

```python
"""
Cost component classes for the TCO Model.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type, List
import numpy as np
import numpy_financial as npf
import logging
from pydantic import PrivateAttr
import math

# Import types from utils
from utils.financial import AUD, Years, Percentage, Rate
from utils.conversions import Kilometres, KWH, LitersPer100KM, KWHPerKM, YearIndex, CalendarYear

# Import vehicle and scenario classes
from .vehicles import Vehicle, ElectricVehicle, DieselVehicle
from .scenarios import Scenario

logger = logging.getLogger(__name__)

# Battery costs dictionary type
BatteryCostProjections = Dict[CalendarYear, AUD]

def get_battery_cost_per_kwh(year: CalendarYear, scenario: Scenario, vehicle: Optional[Vehicle] = None) -> AUD:
    """
    Gets the battery cost per kWh (AUD) for a given calendar year.
    
    Args:
        year: The calendar year to get the cost for
        scenario: The scenario object with potential projections
        vehicle: Optional vehicle with potential projections
        
    Returns:
        Battery cost per kWh in AUD
    """
    costs = None
    
    # 1. Check Scenario object for explicitly provided projections
    if scenario.battery_pack_cost_aud_per_kwh_projections:
        costs = scenario.battery_pack_cost_aud_per_kwh_projections
        
    # 2. Check Vehicle object if it's an EV
    elif isinstance(vehicle, ElectricVehicle) and vehicle.battery_pack_cost_aud_per_kwh_projections:
        costs = vehicle.battery_pack_cost_aud_per_kwh_projections
    
    # Handle case where no cost data is available
    if not costs:
        fallback_cost = AUD(100.0)
        logger.warning(f"No battery cost data found for year {year}. Using fallback cost: {fallback_cost:.2f} AUD/kWh")
        return fallback_cost
    
    # Sort years for interpolation/extrapolation
    sorted_years = sorted(costs.keys())
    
    if year in costs:
        return costs[year]
    elif year < sorted_years[0]:
        # Extrapolate backwards (use first available year's cost)
        return costs[sorted_years[0]]
    elif year > sorted_years[-1]:
        # Extrapolate forwards (use last available year's cost)
        return costs[sorted_years[-1]]
    else:
        # Interpolate linearly between the two closest years
        prev_year = max(y for y in sorted_years if y < year)
        next_year = min(y for y in sorted_years if y > year)
        prev_cost = costs[prev_year]
        next_cost = costs[next_year]
        
        interpolation_factor = (year - prev_year) / (next_year - prev_year)
        interpolated_cost = prev_cost + interpolation_factor * (next_cost - prev_cost)
        return interpolated_cost


class CostComponent(ABC):
    """Abstract base class for all cost components."""

    @abstractmethod
    def calculate_annual_cost(
        self,
        year: CalendarYear,
        vehicle: Vehicle,
        scenario: Scenario,
        calculation_year_index: YearIndex,
        total_mileage_km: Kilometres
    ) -> AUD:
        """
        Calculate the cost (AUD) for this component for a specific calendar year.

        Args:
            year: The calendar year of analysis (e.g., 2025, 2026).
            vehicle: The specific Vehicle instance (Electric or Diesel).
            scenario: The Scenario object containing all parameters.
            calculation_year_index: The zero-based index of the calculation year within the analysis period.
            total_mileage_km: The total mileage accumulated by the vehicle before the start of this year.

        Returns:
            The calculated cost for this component in the given year (in AUD).
        """
        pass


class AcquisitionCost(CostComponent):
    """Handles vehicle acquisition costs (purchase price and loan payments)."""

    def calculate_annual_cost(
        self, year: CalendarYear, vehicle: Vehicle, scenario: Scenario,
        calculation_year_index: YearIndex, total_mileage_km: Kilometres
    ) -> AUD:
        """Return the vehicle acquisition cost (AUD) based on financing method."""

        financing_method: str = scenario.financing_options.financing_method.lower()
        purchase_price: AUD = vehicle.base_purchase_price_aud

        if financing_method == 'cash':
            # Full purchase price in year 0 (index 0), 0 otherwise
            return purchase_price if calculation_year_index == 0 else AUD(0.0)

        elif financing_method == 'loan':
            down_payment_percent: Percentage = scenario.financing_options.down_payment_percent
            loan_term_years: Years = scenario.financing_options.loan_term_years
            interest_rate_percent: Percentage = scenario.financing_options.loan_interest_rate_percent

            if calculation_year_index == 0:
                # Year 0: Down payment
                down_payment_fraction: float = float(down_payment_percent) / 100.0
                down_payment: AUD = AUD(purchase_price * down_payment_fraction)
                return down_payment
            elif 1 <= calculation_year_index <= loan_term_years:
                # Years 1 to loan_term: Calculate annual loan payment
                down_payment_fraction = float(down_payment_percent) / 100.0
                loan_amount: AUD = AUD(purchase_price * (1.0 - down_payment_fraction))
                interest_rate_fraction: Rate = Rate(float(interest_rate_percent) / 100.0)

                # Handle zero interest rate separately to avoid numpy errors
                if interest_rate_fraction == 0:
                    annual_payment_float = float(loan_amount) / loan_term_years if loan_term_years > 0 else 0.0
                elif loan_term_years > 0:
                    # Use npf.pmt
                    annual_payment_float = -npf.pmt(interest_rate_fraction, loan_term_years, float(loan_amount))
                else:
                    annual_payment_float = 0.0  # No payment if term is 0

                return AUD(annual_payment_float)
            else:
                # After loan term, cost is 0
                return AUD(0.0)
        else:
            raise ValueError(f"Unsupported financing method: {scenario.financing_options.financing_method}")


class EnergyCost(CostComponent):
    """Handles energy costs (fuel/electricity)."""

    def calculate_annual_cost(
        self, year: CalendarYear, vehicle: Vehicle, scenario: Scenario,
        calculation_year_index: YearIndex, total_mileage_km: Kilometres
    ) -> AUD:
        """Calculate energy cost (AUD) for the specified year using scenario prices and the vehicle's strategy."""
        annual_mileage: Kilometres = scenario.operational_parameters.annual_mileage_km

        # Determine the correct price key based on the vehicle's energy unit
        energy_unit: str = vehicle.energy_consumption_strategy.unit
        energy_price_key: str
        if energy_unit == 'kWh':
            energy_price_key = 'electricity_price_aud_per_kwh'
        elif energy_unit == 'L':
            energy_price_key = 'diesel_price_aud_per_l'
        else:
            raise TypeError(f"Unsupported energy unit '{energy_unit}' from vehicle's strategy.")

        # Get the energy price for this year
        energy_price_opt: Optional[float] = scenario.get_annual_price(energy_price_key, calculation_year_index)
        if energy_price_opt is None:
             raise ValueError(f"{energy_unit} price (key: {energy_price_key}) for year {year} (index {calculation_year_index}) not found")
        energy_price_aud_per_unit: AUD = AUD(energy_price_opt)

        # Calculate the annual energy cost
        annual_cost: AUD = vehicle.calculate_annual_energy_cost(
            annual_mileage_km=annual_mileage,
            energy_price_aud_per_unit=energy_price_aud_per_unit
        )
        return annual_cost


class MaintenanceCost(CostComponent):
    """Calculates annual maintenance costs using a strategy pattern."""

    def calculate_annual_cost(
        self, year: CalendarYear, vehicle: Vehicle, scenario: Scenario,
        calculation_year_index: YearIndex, total_mileage_km: Kilometres
    ) -> AUD:
        """
        Calculates the maintenance cost (AUD) for a given year using the vehicle's strategy.
        Applies the general annual maintenance increase rate.
        """
        # Get the appropriate strategy from the vehicle
        strategy = vehicle.maintenance_strategy

        # Calculate the base annual cost using the strategy
        base_annual_cost: AUD = strategy.calculate_base_annual_cost(vehicle, scenario)

        # Apply general annual increase rate from scenario
        increase_rate_percent: Percentage = scenario.general_cost_increase_rates.maintenance_annual_increase_rate_percent
        increase_factor: float = (1.0 + (float(increase_rate_percent) / 100.0)) ** calculation_year_index
        adjusted_annual_cost: AUD = AUD(base_annual_cost * increase_factor)

        return adjusted_annual_cost


class InfrastructureCost(CostComponent):
    """Calculates annual infrastructure costs (charger installation and maintenance)."""

    _installation_cost_calculated: bool = PrivateAttr(default=False)

    def reset(self) -> None:
        """Reset the state for a new calculation run."""
        self._installation_cost_calculated = False

    def calculate_annual_cost(
        self, year: CalendarYear, vehicle: Vehicle, scenario: Scenario,
        calculation_year_index: YearIndex, total_mileage_km: Kilometres
    ) -> AUD:
        """Calculates the annual infrastructure cost (AUD) (installation + maintenance)."""
        if not isinstance(vehicle, ElectricVehicle):
            return AUD(0.0)  # No infrastructure cost for non-EVs

        infra_config = scenario.infrastructure_costs
        annual_cost_float: float = 0.0

        # Installation cost (assumed in year 0)
        if calculation_year_index == 0 and not self._installation_cost_calculated:
            annual_cost_float += float(infra_config.selected_charger_cost_aud)
            annual_cost_float += float(infra_config.selected_installation_cost_aud)
            self._installation_cost_calculated = True

        # Annual Maintenance Cost (percentage of hardware cost)
        maintenance_rate_percent: Percentage = infra_config.charger_maintenance_annual_rate_percent
        maintenance_rate_fraction: float = float(maintenance_rate_percent) / 100.0
        charger_cost: AUD = infra_config.selected_charger_cost_aud
        annual_cost_float += float(charger_cost) * maintenance_rate_fraction

        return AUD(annual_cost_float)


class BatteryReplacementCost(CostComponent):
    """Calculates the cost of battery replacement based on degradation or forced year."""

    _replacement_year_index: Optional[YearIndex] = PrivateAttr(default=None)
    _cost_calculated: bool = PrivateAttr(default=False)

    def reset(self) -> None:
        """Reset state for a new calculation run."""
        self._replacement_year_index = None
        self._cost_calculated = False

    def calculate_annual_cost(
        self, year: CalendarYear, vehicle: Vehicle, scenario: Scenario,
        calculation_year_index: YearIndex, total_mileage_km: Kilometres
    ) -> AUD:
        """Calculate battery replacement cost (AUD), which occurs only once."""
        # Only applies to electric vehicles
        if not isinstance(vehicle, ElectricVehicle):
            return AUD(0.0)

        # Get battery replacement config from scenario
        config = scenario.battery_replacement_config

        # Check if battery replacement is enabled
        if not config.enable_battery_replacement:
            return AUD(0.0)

        # If cost already calculated for this run, return 0
        if self._cost_calculated:
            return AUD(0.0)

        # Determine if replacement happens THIS year
        replacement_occurs_this_year: bool = False
        
        if self._replacement_year_index is None:  # Only determine replacement year once
            # Check for forced replacement first
            forced_year_index: Optional[YearIndex] = config.force_replacement_year_index
            if forced_year_index is not None and forced_year_index == calculation_year_index:
                self._replacement_year_index = calculation_year_index
                replacement_occurs_this_year = True
            else:
                # Check degradation threshold if not forced
                degradation_threshold: Optional[float] = config.replacement_threshold_fraction
                if degradation_threshold is not None:
                    # Calculate current degradation state
                    age_years = Years(calculation_year_index)
                    remaining_capacity_fraction: float = vehicle.calculate_battery_degradation_factor(age_years, total_mileage_km)

                    if remaining_capacity_fraction <= degradation_threshold:
                        self._replacement_year_index = calculation_year_index
                        replacement_occurs_this_year = True
        elif self._replacement_year_index == calculation_year_index:
             replacement_occurs_this_year = True  # Already determined replacement happens now

        # If replacement happens this year, calculate and return cost
        if replacement_occurs_this_year:
            # Calculate the replacement cost
            battery_capacity: KWH = vehicle.battery_capacity_kwh
            cost_per_kwh: AUD = get_battery_cost_per_kwh(year, scenario, vehicle)
            replacement_cost: AUD = AUD(float(battery_capacity) * float(cost_per_kwh))
            self._cost_calculated = True
            return replacement_cost
        
        return AUD(0.0)  # No replacement cost this year


class InsuranceCost(CostComponent):
    """Calculates annual insurance costs."""

    def calculate_annual_cost(
        self, year: CalendarYear, vehicle: Vehicle, scenario: Scenario,
        calculation_year_index: YearIndex, total_mileage_km: Kilometres
    ) -> AUD:
        """
        Calculates the insurance cost (AUD) for a given year.
        Uses detailed costs from scenario, potentially based on vehicle value.
        Applies the annual insurance increase rate.
        """
        ins_reg_costs = scenario.insurance_registration_costs
        increase_rate_percent: Percentage = scenario.general_cost_increase_rates.insurance_annual_increase_rate_percent

        # Get the correct detail object based on vehicle type
        detail: Any
        if isinstance(vehicle, ElectricVehicle):
            detail = ins_reg_costs.electric
        elif isinstance(vehicle, DieselVehicle):
            detail = ins_reg_costs.diesel
        else:
             raise TypeError("Vehicle type not supported for InsuranceCost calculation.")

        # Calculate base cost for the year based on type
        base_cost_float: float = 0.0
        if detail.cost_type == 'fixed':
            base_cost_float = float(detail.base_annual_cost_aud)
        elif detail.cost_type == 'percentage_of_value':
            rate_percent: Optional[Percentage] = detail.annual_rate_percent_of_value
            if rate_percent is None:
                 raise ValueError(f"Insurance cost type is 'percentage_of_value' but annual_rate_percent_of_value is not set")
            
            # Calculate based on current vehicle value
            age_years = Years(calculation_year_index)
            current_value: AUD = vehicle.calculate_residual_value_aud(age_years)
            base_cost_float = float(current_value) * (float(rate_percent) / 100.0)
        else:
            raise ValueError(f"Unsupported insurance cost_type: {detail.cost_type}")

        # Apply annual increase rate
        increase_factor: float = (1.0 + (float(increase_rate_percent) / 100.0)) ** calculation_year_index
        adjusted_annual_cost_float: float = base_cost_float * increase_factor
        return AUD(adjusted_annual_cost_float)


class RegistrationCost(CostComponent):
    """Calculates annual registration costs."""

    def calculate_annual_cost(
        self, year: CalendarYear, vehicle: Vehicle, scenario: Scenario,
        calculation_year_index: YearIndex, total_mileage_km: Kilometres
    ) -> AUD:
        """
        Calculates the registration cost (AUD) for a given year.
        Uses the base cost from the vehicle and applies the scenario's increase rate.
        """
        # Get base registration cost from vehicle
        base_cost: AUD = vehicle.base_registration_cost_aud
        
        # Get the annual increase rate from scenario
        increase_rate_percent: Percentage = scenario.general_cost_increase_rates.registration_annual_increase_rate_percent

        # Apply annual increase rate
        increase_factor: float = (1.0 + (float(increase_rate_percent) / 100.0)) ** calculation_year_index
        adjusted_annual_cost_float: float = float(base_cost) * increase_factor
        return AUD(adjusted_annual_cost_float)


class ResidualValue(CostComponent):
    """Calculates the residual value (negative cost) in the final year."""

    def calculate_annual_cost(
        self, year: CalendarYear, vehicle: Vehicle, scenario: Scenario,
        calculation_year_index: YearIndex, total_mileage_km: Kilometres
    ) -> AUD:
        """
        Returns the negative residual value (AUD) only in the final year of the analysis period.
        """
        # Determine the final year index
        analysis_period: Years = scenario.analysis_period_years
        final_year_index: YearIndex = YearIndex(analysis_period - 1)

        # Only apply in the final year
        if calculation_year_index == final_year_index:
            # Calculate residual value at the end of the analysis period
            age_at_end: Years = analysis_period
            residual_value: AUD = vehicle.calculate_residual_value_aud(age_at_end)
            # Return as a negative cost
            return AUD(-float(residual_value))
        else:
            return AUD(0.0)


class CarbonTaxCost(CostComponent):
    """Calculates annual carbon tax cost for diesel vehicles."""

    def calculate_annual_cost(
        self, year: CalendarYear, vehicle: Vehicle, scenario: Scenario,
        calculation_year_index: YearIndex, total_mileage_km: Kilometres
    ) -> AUD:
        """
        Calculates the carbon tax cost (AUD) based on emissions and the annual tax rate.
        Applies only to diesel vehicles if enabled in the scenario.
        """
        # Only applies to diesel vehicles
        if not isinstance(vehicle, DieselVehicle):
            return AUD(0.0)

        # Check if carbon tax is enabled
        if not scenario.carbon_tax_config.include_carbon_tax:
            return AUD(0.0)

        # Get annual mileage
        annual_mileage: Kilometres = scenario.operational_parameters.annual_mileage_km

        # Calculate annual fuel consumption
        fuel_consumption_l: float = vehicle.calculate_energy_consumption(annual_mileage)

        # Calculate annual CO2 emissions in tonnes
        co2_kg_per_l: float = vehicle.co2_emission_factor_kg_per_l
        total_co2_kg: float = fuel_consumption_l * co2_kg_per_l
        total_co2_tonnes: float = total_co2_kg / 1000.0

        # Get the carbon tax rate for the current year
        tax_rate_key: str = 'carbon_tax_rate_aud_per_tonne'
        tax_rate_opt: Optional[float] = scenario.get_annual_price(tax_rate_key, calculation_year_index)

        if tax_rate_opt is None:
             raise ValueError(f"Carbon tax rate (key: {tax_rate_key}) for year {year} (index {calculation_year_index}) not found")
        tax_rate_aud_per_tonne: AUD = AUD(tax_rate_opt)

        # Calculate annual carbon tax cost
        annual_tax_cost_float: float = total_co2_tonnes * float(tax_rate_aud_per_tonne)
        return AUD(annual_tax_cost_float)


class RoadUserChargeCost(CostComponent):
    """Calculates annual road user charge cost."""

    def calculate_annual_cost(
        self, year: CalendarYear, vehicle: Vehicle, scenario: Scenario,
        calculation_year_index: YearIndex, total_mileage_km: Kilometres
    ) -> AUD:
        """
        Calculates the road user charge (AUD) based on annual mileage and the annual charge rate.
        Applies only if enabled in the scenario.
        """
        # Check if road user charge is enabled
        if not scenario.road_user_charge_config.include_road_user_charge:
            return AUD(0.0)

        # Get annual mileage
        annual_mileage: Kilometres = scenario.operational_parameters.annual_mileage_km

        # Get the road user charge rate for the current year
        charge_rate_key: str = 'road_user_charge_aud_per_km'
        charge_rate_opt: Optional[float] = scenario.get_annual_price(charge_rate_key, calculation_year_index)

        if charge_rate_opt is None:
             raise ValueError(f"Road user charge rate (key: {charge_rate_key}) for year {year} (index {calculation_year_index}) not found")
        charge_aud_per_km: AUD = AUD(charge_rate_opt)

        # Calculate annual road user charge cost
        annual_charge_cost_float: float = float(annual_mileage) * float(charge_aud_per_km)
        return AUD(annual_charge_cost_float)
```

### Step 7: TCO Calculator (Estimated time: 2 days)

Create `tco_model/optimizations.py` for performance utilities:

```python
"""
Optimization utilities for TCO model calculations.

This module provides performance optimizations and caching mechanisms
to improve calculation speed and efficiency for the TCO model.
"""

import functools
import time
import logging
from typing import Any, Callable, Dict, Optional, TypeVar

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Type variable for generic function annotations
T = TypeVar('T')

class PerformanceMonitor:
    """
    A utility class for monitoring the performance of model calculations.
    
    Provides timing and profiling capabilities to identify bottlenecks.
    """
    
    def __init__(self):
        self.timings: Dict[str, float] = {}
        self.call_counts: Dict[str, int] = {}
    
    def reset(self) -> None:
        """Reset all performance metrics."""
        self.timings = {}
        self.call_counts = {}
    
    def record(self, operation: str, duration: float) -> None:
        """Record the timing for an operation."""
        self.timings[operation] = self.timings.get(operation, 0) + duration
        self.call_counts[operation] = self.call_counts.get(operation, 0) + 1
    
    def get_report(self) -> Dict[str, Any]:
        """
        Get a report of all performance metrics.
        
        Returns:
            Dict containing timing and call count information
        """
        report = {
            'timings': {k: round(v, 4) for k, v in self.timings.items()},
            'call_counts': self.call_counts.copy(),
            'avg_times': {
                k: round(v / self.call_counts.get(k, 1), 4) 
                for k, v in self.timings.items()
            }
        }
        
        # Calculate total time and percentage breakdown
        total_time = sum(self.timings.values())
        if total_time > 0:
            report['total_time'] = round(total_time, 4)
            report['percentages'] = {
                k: round((v / total_time) * 100, 2) 
                for k, v in self.timings.items()
            }
        
        return report

# Create a global instance for use across the application
performance_monitor = PerformanceMonitor()

def timed(operation_name: str) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator that times the execution of a function and records metrics.
    
    Args:
        operation_name: Name to use for the timing record
        
    Returns:
        Decorated function that includes timing
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            start_time = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            
            # Record timing information
            performance_monitor.record(operation_name, elapsed)
            
            return result
        return wrapper
    return decorator

def cached(cache_key: str) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator that caches the result of a function based on a key.
    
    Args:
        cache_key: Template string for the cache key
        
    Returns:
        Decorated function that uses caching
    """
    cache: Dict[str, Any] = {}
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Format the cache key using the first arg (typically self)
            # and any named keyword args mentioned in the key template
            key_parts = []
            if args and hasattr(args[0], 'name'):
                key_parts.append(args[0].name)
            
            for k in kwargs:
                if k in cache_key and hasattr(kwargs[k], 'name'):
                    key_parts.append(kwargs[k].name)
            
            actual_key = cache_key
            for i, part in enumerate(key_parts):
                actual_key = actual_key.replace(f"${i}", str(part))
            
            # Check cache
            if actual_key in cache:
                logger.debug(f"Cache hit for {func.__name__} with key '{actual_key}'")
                return cache[actual_key]
            
            # Calculate and cache
            result = func(*args, **kwargs)
            cache[actual_key] = result
            logger.debug(f"Cached result for {func.__name__} with key '{actual_key}'")
            return result
        
        # Add a method to clear the cache
        def clear_cache() -> None:
            cache.clear()
            logger.debug(f"Cache cleared for {func.__name__}")
        
        wrapper.clear_cache = clear_cache
        return wrapper
    
    return decorator

def optimize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Optimize a DataFrame for memory usage and performance.
    
    Args:
        df: DataFrame to optimize
        
    Returns:
        Optimized DataFrame with reduced memory footprint
    """
    result = df.copy()
    
    # Optimize numeric columns
    for col in result.select_dtypes(include=['int']).columns:
        result[col] = pd.to_numeric(result[col], downcast='integer')
        
    for col in result.select_dtypes(include=['float']).columns:
        result[col] = pd.to_numeric(result[col], downcast='float')
    
    # Convert object columns with few unique values to category
    for col in result.select_dtypes(include=['object']).columns:
        if result[col].nunique() / len(result) < 0.5:  # If less than 50% unique values
            result[col] = result[col].astype('category')
    
    return result

def vectorized_calculation(func: Callable[[float], float]) -> Callable[[np.ndarray], np.ndarray]:
    """
    Convert a scalar function to a vectorized one that can operate on arrays.
    
    Args:
        func: Function that operates on a single value
        
    Returns:
        Vectorized function that operates on arrays
    """
    return np.vectorize(func)
```

Create `tco_model/model.py` to implement the TCO calculator:

```python
"""
TCO Calculator for the Heavy Vehicle TCO Modeller.

This module provides the core calculation engine that computes the
Total Cost of Ownership (TCO) for electric and diesel vehicles.
"""

# Standard library imports
import logging
from typing import Dict, List, Optional, Tuple, Type, Any, Set, Union
import time

# Third-party imports
import numpy as np
import pandas as pd

# Application-specific imports
from .components import (
    AcquisitionCost, BatteryReplacementCost, CarbonTaxCost, CostComponent, 
    EnergyCost, InfrastructureCost, InsuranceCost, MaintenanceCost,
    RegistrationCost, ResidualValue, RoadUserChargeCost
)
from .scenarios import Scenario
from .vehicles import DieselVehicle, ElectricVehicle, Vehicle
from .optimizations import (
    timed, optimize_dataframe, performance_monitor, 
    vectorized_calculation, cached
)

logger = logging.getLogger(__name__)

class TCOCalculator:
    """
    Calculates and compares Total Cost of Ownership for electric and diesel vehicles.
    
    This class handles the full TCO calculation workflow including:
    - Determining applicable cost components based on vehicle type and scenario
    - Calculating annual costs for each component
    - Applying discounting and aggregating costs
    - Computing key metrics like LCOD and parity year
    """

    def __init__(self):
        """Initialize the TCO Calculator with a standard set of cost components."""
        # Define the standard list of component classes to use
        self._component_classes: List[Type[CostComponent]] = [
            AcquisitionCost,
            EnergyCost,
            MaintenanceCost,
            InfrastructureCost,
            BatteryReplacementCost,
            InsuranceCost,
            RegistrationCost,
            CarbonTaxCost,
            RoadUserChargeCost,
            ResidualValue  # Keep ResidualValue last as it's often negative
        ]
        # Component instance cache to avoid recreating component objects
        self._component_cache: Dict[Type[CostComponent], CostComponent] = {}
        
        # Performance tracking
        self._performance_stats = performance_monitor

    def _get_applicable_components(self, vehicle: Vehicle, scenario: Scenario) -> List[CostComponent]:
        """
        Returns instances of components applicable to the vehicle type and scenario settings.
        
        Args:
            vehicle: The vehicle to calculate costs for
            scenario: The scenario containing calculation parameters
            
        Returns:
            List of applicable cost component instances
        """
        applicable_components = []
        
        # Process each component class
        for comp_class in self._component_classes:
            # Get or create component instance
            component = self._get_component_instance(comp_class)
            
            # Check if component should be applied to this vehicle/scenario
            if not self._is_component_applicable(component, vehicle, scenario):
                continue
                
            # Reset stateful components for a new calculation run
            self._reset_component_if_needed(component)
                
            applicable_components.append(component)

        return applicable_components

    def _get_component_instance(self, component_class: Type[CostComponent]) -> CostComponent:
        """Get a cached component instance or create a new one if not cached."""
        if component_class not in self._component_cache:
            self._component_cache[component_class] = component_class()
        return self._component_cache[component_class]
    
    def _reset_component_if_needed(self, component: CostComponent) -> None:
        """Reset a stateful component if it has a reset method."""
        if hasattr(component, 'reset') and callable(getattr(component, 'reset')):
            component.reset()
        
    def _is_component_applicable(self, component: CostComponent, vehicle: Vehicle, scenario: Scenario) -> bool:
        """
        Determines if a cost component applies to the given vehicle and scenario.
        
        Args:
            component: The cost component to check
            vehicle: The vehicle to check applicability for
            scenario: The scenario containing configuration parameters
            
        Returns:
            True if the component is applicable, False otherwise
        """
        # EV-specific components (only apply to ElectricVehicle)
        if isinstance(component, (InfrastructureCost, BatteryReplacementCost)):
            if not isinstance(vehicle, ElectricVehicle):
                return False
                
            # Additionally check if battery replacement is enabled
            if isinstance(component, BatteryReplacementCost) and not scenario.battery_replacement_config.enable_battery_replacement:
                return False
        
        # Diesel-specific components (only apply to DieselVehicle)
        if isinstance(component, CarbonTaxCost):
            if not isinstance(vehicle, DieselVehicle) or not scenario.carbon_tax_config.include_carbon_tax:
                return False
        
        # Components that depend on scenario flags
        if isinstance(component, RoadUserChargeCost) and not scenario.road_user_charge_config.include_road_user_charge:
            return False
        
        return True

    @timed("annual_costs_calculation")
    def _calculate_annual_costs_undiscounted(self, vehicle: Vehicle, scenario: Scenario) -> pd.DataFrame:
        """
        Calculate undiscounted annual costs for each applicable component for a single vehicle.
        
        Args:
            vehicle: The vehicle to calculate costs for
            scenario: The scenario containing calculation parameters
            
        Returns:
            DataFrame with undiscounted annual costs by component and year
        """
        # Get applicable components for this vehicle and scenario
        applicable_components = self._get_applicable_components(vehicle, scenario)
        component_names = [comp.__class__.__name__ for comp in applicable_components]
        
        # Initialize base calculation arrays
        analysis_years = scenario.analysis_period_years
        year_indices = np.array(range(analysis_years))
        calendar_years = np.array(scenario.analysis_calendar_years)
        
        # Pre-calculate cumulative mileage for all years (for components that need it)
        annual_mileage = scenario.operational_parameters.annual_mileage_km
        mileage_array = np.concatenate(([0.0], np.cumsum(np.full(analysis_years - 1, annual_mileage))))
        
        # Create dataframe shell
        annual_costs_data = {
            'Year': calendar_years,
            'YearIndex': year_indices,
            **{name: np.zeros(analysis_years) for name in component_names}
        }
        
        # Process each component and calculate costs
        for component in applicable_components:
            comp_name = component.__class__.__name__
            annual_costs_data[comp_name] = self._calculate_component_costs(
                component=component,
                years=calendar_years,
                year_indices=year_indices,
                vehicle=vehicle,
                scenario=scenario,
                cumulative_mileage_start_of_year=mileage_array
            )
        
        # Convert to DataFrame and add a Total column
        df = pd.DataFrame(annual_costs_data)
        df['Total'] = df[[col for col in df.columns if col not in ['Year', 'YearIndex']]].sum(axis=1)
        
        # Set Year as index
        df.set_index('Year', inplace=True)
        
        # Optimize the dataframe for memory usage
        return optimize_dataframe(df)

    def _calculate_component_costs(self, component, years, year_indices, vehicle, scenario, cumulative_mileage_start_of_year) -> np.ndarray:
        """
        Calculate costs for a single component across all years.
        
        Args:
            component: Cost component to calculate
            years: Array of calendar years
            year_indices: Array of year indices (0-based)
            vehicle: Vehicle object
            scenario: Scenario object
            cumulative_mileage_start_of_year: Array of cumulative mileage at the start of each year index
            
        Returns:
            Array of annual costs for this component
        """
        costs = np.zeros(len(years))
        
        # Process each year
        for i, year_index in enumerate(year_indices):
            current_year = years[i]
            current_mileage = cumulative_mileage_start_of_year[i]
            costs[i] = self._calculate_year_cost(
                component=component,
                year=current_year,
                calculation_year_index=year_index,
                vehicle=vehicle,
                scenario=scenario, 
                total_mileage_km=current_mileage
            )
                
        return costs
    
    def _calculate_year_cost(self, component, year, calculation_year_index, vehicle, scenario, total_mileage_km) -> float:
        """Calculate cost for a specific component and year with error handling."""
        try:
            cost = component.calculate_annual_cost(
                year=year,
                vehicle=vehicle,
                scenario=scenario,
                calculation_year_index=calculation_year_index,
                total_mileage_km=total_mileage_km
            )
            return cost if pd.notna(cost) else 0.0
        except Exception as e:
            logger.error(f"Error calculating {component.__class__.__name__} for {vehicle.name} "
                        f"in year index {calculation_year_index}: {e}", exc_info=True)
            return 0.0  # Return zero if calculation fails

    @timed("discounting")
    def _apply_discounting(self, undiscounted_df: pd.DataFrame, scenario: Scenario) -> pd.DataFrame:
        """
        Apply discounting to annual costs to get present values.
        
        Args:
            undiscounted_df: DataFrame with undiscounted annual costs
            scenario: The scenario object containing the discount rate
            
        Returns:
            DataFrame with discounted annual costs
        """
        if undiscounted_df.empty:
            logger.warning("Empty DataFrame provided for discounting, returning empty DataFrame.")
            return pd.DataFrame()
        
        # Make a copy to avoid modifying the original
        discounted_df = undiscounted_df.copy()
        
        # Calculate discount factors using vectorized operations
        years = np.arange(len(discounted_df))
        discount_rate_percent = scenario.economic_parameters.discount_rate_percent_real
        discount_rate = discount_rate_percent / 100.0
        discount_factors = 1 / np.power(1 + discount_rate, years)
        
        # Apply discount factors to all cost columns except 'Year' and 'YearIndex'
        cost_columns = [col for col in discounted_df.columns if col not in ['Year', 'YearIndex']]
        for col in cost_columns:
            discounted_df[col] = discounted_df[col] * discount_factors
        
        return optimize_dataframe(discounted_df)

    @cached("tco_calculation:$0")
    def calculate(self, scenario: Scenario) -> Dict[str, Any]:
        """
        Perform the full TCO calculation for the given scenario.
        
        Uses caching to avoid redundant calculations for the same scenario.
        
        Args:
            scenario: The Scenario object containing all input parameters.
            
        Returns:
            A dictionary containing detailed results including undiscounted and discounted
            annual costs, total TCO, LCOD, parity year, and analysis years.
        """
        # Start timing the calculation
        start_time = time.time()
        logger.info(f"Starting TCO calculation for scenario: {scenario.name}")
        
        # Initialize results with scenario metadata
        results = {
            'scenario_name': scenario.name,
            'analysis_period_years': scenario.analysis_period_years,
            'start_year': scenario.analysis_start_year,
            'discount_rate_percent': scenario.economic_parameters.discount_rate_percent_real,
            'vehicles': {
                'electric': {'name': scenario.electric_vehicle.name},
                'diesel': {'name': scenario.diesel_vehicle.name}
            },
            'errors': [],
            'warnings': []
        }
        
        try:
            # Calculate undiscounted annual costs for both vehicle types
            logger.info(f"Calculating costs for {scenario.electric_vehicle.name} (Electric)")
            electric_undisc = self._calculate_annual_costs_undiscounted(scenario.electric_vehicle, scenario)
            
            logger.info(f"Calculating costs for {scenario.diesel_vehicle.name} (Diesel)")
            diesel_undisc = self._calculate_annual_costs_undiscounted(scenario.diesel_vehicle, scenario)
            
            results['vehicles']['electric']['undiscounted_annual_costs'] = electric_undisc
            results['vehicles']['diesel']['undiscounted_annual_costs'] = diesel_undisc
            
            # Apply discounting
            logger.info("Applying discounting...")
            electric_disc = self._apply_discounting(electric_undisc, scenario)
            diesel_disc = self._apply_discounting(diesel_undisc, scenario)
            
            results['vehicles']['electric']['discounted_annual_costs'] = electric_disc
            results['vehicles']['diesel']['discounted_annual_costs'] = diesel_disc
            
            # Calculate total TCO (sum of discounted total costs)
            total_tco_ev = electric_disc['Total'].sum() if not electric_disc.empty else 0
            total_tco_diesel = diesel_disc['Total'].sum() if not diesel_disc.empty else 0
            
            results['vehicles']['electric']['total_discounted_tco'] = total_tco_ev
            results['vehicles']['diesel']['total_discounted_tco'] = total_tco_diesel
            logger.info(f"Total Discounted TCO - EV: {total_tco_ev:,.2f}, Diesel: {total_tco_diesel:,.2f}")
            
            # Calculate Levelized Cost of Driving (LCOD) using discounted TCO
            results['vehicles']['electric']['lcod_aud_per_km'] = self._calculate_lcod(total_tco_ev, scenario)
            results['vehicles']['diesel']['lcod_aud_per_km'] = self._calculate_lcod(total_tco_diesel, scenario)
            
            # Calculate TCO difference
            results['tco_difference'] = total_tco_diesel - total_tco_ev
            
            # Find parity year using undiscounted cumulative costs
            results['parity_info'] = self._find_parity_year_undiscounted(
                electric_cumulative_undisc=electric_undisc['Total'].cumsum(),
                diesel_cumulative_undisc=diesel_undisc['Total'].cumsum(),
                calendar_years=scenario.analysis_calendar_years
            )
            
            # Record calculation time
            elapsed = time.time() - start_time
            self._performance_stats.record("total_calculation", elapsed)
            results['calculation_time_s'] = round(elapsed, 4)
            
            return results
            
        except Exception as e:
            logger.error(f"Error during TCO calculation: {e}", exc_info=True)
            results['error'] = f"Calculation failed: {e}"
            return results  # Return partial results with error message
    
    def _calculate_lcod(self, total_discounted_tco: float, scenario: Scenario) -> Optional[float]:
        """
        Calculate Levelized Cost of Driving (per km).
        
        Uses total discounted TCO divided by total undiscounted mileage.
        
        Args:
            total_discounted_tco: The total discounted TCO value
            scenario: The scenario containing mileage and analysis period data
            
        Returns:
            LCOD value in AUD/km or None if calculation fails
        """
        if total_discounted_tco is None or np.isnan(total_discounted_tco):
            logger.warning("Cannot calculate LCOD with invalid TCO value")
            return None
            
        # Calculate total undiscounted mileage over the analysis period
        total_undiscounted_km = scenario.operational_parameters.annual_mileage_km * scenario.analysis_period_years
        
        if total_undiscounted_km == 0:
            logger.warning("Total undiscounted mileage is zero, cannot calculate LCOD.")
            return None
            
        lcod = total_discounted_tco / total_undiscounted_km
        return lcod

    def _find_parity_year_undiscounted(
        self, 
        electric_cumulative_undisc: pd.Series, 
        diesel_cumulative_undisc: pd.Series, 
        calendar_years: List[int]
    ) -> Dict[str, Any]:
        """
        Find the first year when undiscounted electric cumulative TCO is <= undiscounted diesel cumulative TCO.
        
        Args:
            electric_cumulative_undisc: Cumulative electric vehicle costs (undiscounted)
            diesel_cumulative_undisc: Cumulative diesel vehicle costs (undiscounted)
            calendar_years: The calendar years corresponding to each index
            
        Returns:
            Dictionary with parity information
        """
        parity_info = {
            'parity_year_undiscounted': None,
            'parity_year_index': None,
            'ev_cumulative_at_parity': None,
            'diesel_cumulative_at_parity': None
        }
        
        try:
            if electric_cumulative_undisc.empty or diesel_cumulative_undisc.empty:
                logger.warning("Empty cost series provided for parity calculation")
                return parity_info
                
            # Find indices where electric <= diesel
            parity_indices = electric_cumulative_undisc.index[electric_cumulative_undisc <= diesel_cumulative_undisc]
            
            if not parity_indices.empty:
                first_parity_index = parity_indices[0]
                parity_info['parity_year_index'] = first_parity_index
                parity_info['parity_year_undiscounted'] = calendar_years[first_parity_index]
                parity_info['ev_cumulative_at_parity'] = float(electric_cumulative_undisc.iloc[first_parity_index])
                parity_info['diesel_cumulative_at_parity'] = float(diesel_cumulative_undisc.iloc[first_parity_index])
                logger.info(f"TCO parity found in calendar year {parity_info['parity_year_undiscounted']}")
            else:
                logger.info("Parity not reached within analysis period")
                
            return parity_info
                
        except Exception as e:
            logger.error(f"Error finding undiscounted parity year: {e}", exc_info=True)
            return parity_info
    
    def invalidate_cache(self) -> None:
        """Invalidate the calculation cache."""
        if hasattr(self.calculate, 'clear_cache'):
            self.calculate.clear_cache()
            logger.info("TCO calculation cache cleared")

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for recent calculations."""
        return self._performance_stats.get_report()
    
    def reset_performance_stats(self) -> None:
        """Reset all performance tracking metrics."""
        self._performance_stats.reset()
        logger.info("Performance statistics reset.")
```

## Phase 3: UI Components and State Management

### Step 8: UI Base Classes and State Management (Estimated time: 1 day)

Create `ui/state.py` to manage the application state:

```python
"""
Handles Streamlit session state management for the TCO Model application.
"""

import streamlit as st
import logging
from typing import Dict, Any, Optional

from tco_model.scenarios import Scenario
from config.config_manager import ConfigurationManager
from pydantic import ValidationError

logger = logging.getLogger(__name__)

class ConfigManager:
    """
    Manages scenario loading and state transformation for the UI.
    This class centralizes scenario file loading and UI state preparation.
    """

    @classmethod
    def load_scenario(cls, filepath: str) -> Optional[Scenario]:
        """
        Load a scenario from the given file path using Scenario.from_file.

        Args:
            filepath: Path to the scenario file.

        Returns:
            Scenario object if loaded successfully, None otherwise.
        """
        if not filepath:
            logger.error("load_scenario called without a filepath.")
            return None

        try:
            # Scenario.from_file handles existence checks and validation
            scenario: Scenario = Scenario.from_file(filepath)
            logger.info(f"Scenario loaded: {scenario.name} from {filepath}")
            return scenario
        except FileNotFoundError:
            logger.error(f"Scenario file not found at: {filepath}")
            st.error(f"Error: Scenario file not found at {filepath}")
            return None
        except ValidationError as e:
            logger.error(f"Error validating scenario file ({filepath}): {e}")
            st.error(f"Error loading or validating scenario file {filepath}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error loading scenario file {filepath}: {e}", exc_info=True)
            st.error(f"An unexpected error occurred while loading {filepath}. Check logs.")
            return None

    @classmethod
    def setup_battery_replacement_ui_state(cls, scenario: Scenario) -> None:
        """
        Set up the UI state for battery replacement options based on scenario config.

        Args:
            scenario: The Scenario object with nested battery replacement config.
        """
        # Access config through the nested model
        config = scenario.battery_replacement_config
        if config.enable_battery_replacement:
            if config.force_replacement_year_index is not None:
                # Set UI mode based on which model config is set
                st.session_state['battery_replace_mode'] = "Fixed Year"
            elif config.replacement_threshold_fraction is not None:
                st.session_state['battery_replace_mode'] = "Capacity Threshold"
            else:
                # Default UI mode if specific settings aren't present but replacement is enabled
                st.session_state['battery_replace_mode'] = "Fixed Year"
                logger.warning("Battery replacement enabled but neither year nor threshold set. Defaulting UI mode to 'Fixed Year'.")
        else:
            # Default UI mode if replacement is disabled
            st.session_state['battery_replace_mode'] = "Fixed Year"

def initialize_session_state() -> None:
    """
    Initialize the Streamlit session state with the default Scenario object.

    Loads the base default configuration using ConfigurationManager, creates a
    default Scenario object, and stores it directly in st.session_state['scenario'].
    Sets up UI-specific state like battery replacement mode.
    """
    # Use 'scenario' as the key for the main object
    if 'scenario' not in st.session_state:
        try:
            core_config_manager = ConfigurationManager()
            # Get scenario config from default scenario file
            default_config = core_config_manager.get_scenario_config()

            if not default_config:
                 logger.error("ConfigurationManager did not provide default configuration.")
                 st.error("Failed to load default configuration. Check logs.")
                 st.stop()
                 return

            # Create a Scenario from the config
            scenario: Scenario = Scenario(**default_config)
            logger.info("Default scenario created from base configuration.")

            # Store the Scenario object directly in session state
            st.session_state['scenario'] = scenario

            # Set up battery replacement UI state based on the default scenario
            ConfigManager.setup_battery_replacement_ui_state(st.session_state['scenario'])

            # Initialize calculation results to None
            if 'calculation_results' not in st.session_state:
                st.session_state['calculation_results'] = None

        except ValidationError as val_err:
             logger.error(f"Validation error initializing Scenario from default config: {val_err}", exc_info=True)
             st.error(f"Error validating default configuration: {val_err}")
             st.stop()
        except Exception as e:
            logger.error(f"Unexpected error during state initialization: {e}", exc_info=True)
            st.error(f"An unexpected error occurred during state initialization: {e}")
            st.stop()
```

Create `ui/widgets/base.py` to define base UI widgets:

```python
"""
Base classes for UI widgets in the TCO Model application.
"""

from abc import ABC, abstractmethod
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class BaseWidget(ABC):
    """Base class for all UI widgets."""
    
    def __init__(self, key_prefix: str = ""):
        """
        Initialize the widget.
        
        Args:
            key_prefix: Optional prefix for session state keys to avoid collisions
        """
        self.key_prefix = key_prefix
        
    def get_key(self, key: str) -> str:
        """
        Get a unique session state key for this widget.
        
        Args:
            key: Base key name
            
        Returns:
            Prefixed key name
        """
        return f"{self.key_prefix}_{key}" if self.key_prefix else key
    
    @abstractmethod
    def render(self, params: Dict[str, Any]) -> None:
        """
        Render the widget in the Streamlit UI.
        
        Args:
            params: Current parameters from session state
        """
        pass
```

### Step 9: Sidebar Input Widgets (Estimated time: 1.5 days)

Create `ui/widgets/input_widgets/sidebar.py` to define sidebar widgets:

```python
"""
Sidebar input widgets for the TCO Model application.
"""

import streamlit as st
import logging
from typing import Any, Optional, List
from abc import abstractmethod

from ui.widgets.base import BaseWidget
from tco_model.scenarios import Scenario

logger = logging.getLogger(__name__)

class SidebarWidget(BaseWidget):
    """Base class for sidebar input sections."""
    
    def __init__(self, section_title: str, expanded: bool = False, key_prefix: str = ""):
        """
        Initialize a sidebar section widget.
        
        Args:
            section_title: Title of the section
            expanded: Whether the section is expanded by default
            key_prefix: Optional prefix for session state keys
        """
        super().__init__(key_prefix)
        self.section_title = section_title
        self.expanded = expanded
        
    def render(self, scenario: Scenario) -> None:
        """
        Render the input section in an expander.
        
        Args:
            scenario: The current Scenario object from session state
        """
        with st.sidebar.expander(self.section_title, expanded=self.expanded):
            self.render_content(scenario)
    
    @abstractmethod
    def render_content(self, scenario: Scenario) -> None:
        """
        Render the content inside the expander.
        
        Args:
            scenario: The current Scenario object from session state
        """
        pass


class SidebarManager(BaseWidget):
    """Manager widget that assembles all sidebar sections."""
    
    def __init__(self, sections: List[SidebarWidget]):
        """
        Initialize with a list of sidebar section widgets.
        
        Args:
            sections: List of sidebar widgets to render
        """
        super().__init__()
        self.sections = sections
    
    def render(self, scenario: Scenario) -> None:
        """
        Render the complete sidebar with all sections.
        
        Args:
            scenario: The current Scenario object from session state
        """
        st.sidebar.title("Scenario Parameters")
        
        # Render each section
        for section in self.sections:
            section.render(scenario)
```

Create `ui/widgets/input_widgets/general.py` for general parameters:

```python
"""
General input widgets for the TCO Model application.
"""

import streamlit as st
import datetime
import logging
from typing import Any

from ui.widgets.input_widgets.sidebar import SidebarWidget
from config import constants
from tco_model.scenarios import Scenario

logger = logging.getLogger(__name__)

class GeneralInputWidget(SidebarWidget):
    """Widget for general scenario parameters."""
    
    def __init__(self, expanded: bool = True):
        super().__init__("General", expanded)
        
    def render_content(self, scenario: Scenario) -> None:
        """
        Render the general parameters UI section.
        
        Args:
            scenario: Current scenario object
        """
        # Scenario Name
        st.text_input(
            "Scenario Name", 
            key="scenario.name",
            value=scenario.name
        )
        
        # Start Year
        current_year = datetime.datetime.now().year
        st.number_input(
            "Start Year", 
            min_value=current_year - 10, 
            max_value=current_year + 30,
            step=1, 
            format="%d", 
            key="scenario.analysis_start_year",
            value=scenario.analysis_start_year
        )
        
        # Analysis Period
        st.number_input(
            "Analysis Period (Years)",
            min_value=constants.MIN_ANALYSIS_YEARS, 
            max_value=constants.MAX_ANALYSIS_YEARS,
            step=1, 
            format="%d", 
            key="scenario.analysis_period_years",
            value=scenario.analysis_period_years,
            help="Duration of the analysis in years (1-30)."
        )
        
        # Description
        st.text_area(
            "Description", 
            key="scenario.description",
            value=scenario.description if scenario.description else ""
        )


class EconomicInputWidget(SidebarWidget):
    """Widget for economic parameters."""
    
    def __init__(self, expanded: bool = False):
        super().__init__("Economic", expanded)
        
    def render_content(self, scenario: Scenario) -> None:
        """
        Render the economic parameters UI section.
        
        Args:
            scenario: Current scenario object
        """
        # Discount Rate
        st.number_input(
            "Discount Rate (%)", 
            min_value=0.0, 
            max_value=20.0, 
            step=0.1, 
            format="%.1f", 
            key="scenario.economic_parameters.discount_rate_percent_real",
            value=scenario.economic_parameters.discount_rate_percent_real,
            help="Real discount rate (0-20%)."
        )
        
        # Inflation Rate
        st.number_input(
            "Inflation Rate (%)", 
            min_value=0.0, 
            max_value=10.0, 
            step=0.1, 
            format="%.1f", 
            key="scenario.economic_parameters.inflation_rate_percent",
            value=scenario.economic_parameters.inflation_rate_percent,
            help="General inflation rate (0-10%)."
        )
        
        # Financing Method
        finance_method_key = "scenario.financing_options.financing_method"
        st.selectbox(
            "Financing Method", 
            options=["loan", "cash"], 
            key=finance_method_key,
            index=0 if scenario.financing_options.financing_method == "loan" else 1
        )
        
        # Only show loan parameters if loan financing is selected
        if st.session_state.get(finance_method_key) == 'loan':
            st.number_input(
                "Loan Term (years)", 
                min_value=1, 
                max_value=15, 
                step=1, 
                key="scenario.financing_options.loan_term_years",
                value=scenario.financing_options.loan_term_years,
                help="Duration of the vehicle loan financing."
            )
            
            st.number_input(
                "