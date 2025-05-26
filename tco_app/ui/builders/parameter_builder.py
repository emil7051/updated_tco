"""Parameter input builders for UI context."""

from tco_app.src import VALIDATION_LIMITS, Any, Dict, pd, st
from tco_app.src.constants import DataColumns, ParameterKeys
from tco_app.src.utils.data_access import BatteryParameters, FinancialParameters


class ParameterInputBuilder:
    """Builds parameter input context."""

    def __init__(self, data_tables: Dict[str, pd.DataFrame], vehicle_type: str):
        self.data_tables = data_tables
        self.vehicle_type = vehicle_type
        self.parameters = {}

    def collect_operating_parameters(self) -> "ParameterInputBuilder":
        """Collect operating parameters from UI."""
        operating_params = self.data_tables["operating_params"]
        default_params = operating_params[
            operating_params[DataColumns.VEHICLE_TYPE] == self.vehicle_type
        ].iloc[0]

        self.parameters["annual_kms"] = st.number_input(
            "Annual Distance (km)",
            VALIDATION_LIMITS.MIN_ANNUAL_KMS,
            VALIDATION_LIMITS.MAX_ANNUAL_KMS,
            int(default_params["annual_kms"]),
            VALIDATION_LIMITS.ANNUAL_KMS_STEP,
        )

        self.parameters["truck_life_years"] = st.number_input(
            "Vehicle Lifetime (years)",
            VALIDATION_LIMITS.MIN_TRUCK_LIFE_YEARS,
            VALIDATION_LIMITS.MAX_TRUCK_LIFE_YEARS,
            int(default_params["truck_life_years"]),
            VALIDATION_LIMITS.TRUCK_LIFE_STEP,
        )

        return self

    def collect_financial_parameters(
        self, financial_params: pd.DataFrame
    ) -> "ParameterInputBuilder":
        """Collect financial parameters from UI."""
        fin_params = FinancialParameters(financial_params)

        self.parameters["discount_rate"] = (
            st.slider(
                "Discount Rate (%)",
                0.0,
                15.0,
                float(fin_params.discount_rate * 100),
                0.5,
            )
            / 100
        )

        self.parameters[ParameterKeys.DIESEL_PRICE] = st.number_input(
            "Diesel Price (AUD/L)", 
            VALIDATION_LIMITS.MIN_DIESEL_PRICE, 
            VALIDATION_LIMITS.MAX_DIESEL_PRICE, 
            float(fin_params.diesel_price), 
            VALIDATION_LIMITS.DIESEL_PRICE_STEP
        )

        self.parameters[ParameterKeys.CARBON_PRICE] = st.number_input(
            "Carbon Price ($/tonne CO₂)", 0, 500, int(fin_params.carbon_price), 5
        )

        return self

    def collect_battery_parameters(
        self, battery_params: pd.DataFrame
    ) -> "ParameterInputBuilder":
        """Collect battery parameters from UI."""
        bat_params = BatteryParameters(battery_params)

        self.parameters["degradation_rate"] = (
            st.slider(
                "Annual Battery Degradation (%)",
                0.0,
                10.0,
                float(bat_params.degradation_rate * 100),
                0.1,
            )
            / 100
        )

        self.parameters["replacement_cost"] = st.number_input(
            "Battery Replacement Cost ($/kWh)",
            50,
            500,
            int(bat_params.replacement_cost_per_kwh),
            10,
        )

        return self

    def build(self) -> Dict[str, Any]:
        """Return parameters context."""
        return self.parameters


def build_fuel_price_input(fin_params: FinancialParameters) -> float:
    """Build diesel fuel price input.

    Args:
        fin_params: Financial parameters with default diesel price

    Returns:
        Selected diesel fuel price
    """
    from tco_app.src.config import VALIDATION_LIMITS
    
    return st.number_input(
        "Diesel Price (AUD/L)", 
        VALIDATION_LIMITS.MIN_DIESEL_PRICE, 
        VALIDATION_LIMITS.MAX_DIESEL_PRICE, 
        float(fin_params.diesel_price), 
        VALIDATION_LIMITS.DIESEL_PRICE_STEP
    )
