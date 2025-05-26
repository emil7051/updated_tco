"""Charging configuration builders for UI context."""

import logging

from tco_app.src import UI_CONFIG, VALIDATION_LIMITS, Any, Dict, Optional, pd, st
from tco_app.src.constants import DataColumns

logger = logging.getLogger(__name__)


class ChargingConfigurationBuilder:
    """Builds charging configuration context."""

    def __init__(self, data_tables: Dict[str, pd.DataFrame]):
        self.data_tables = data_tables
        self.charging_approach = None
        self.charging_mix = None
        self.selected_charging = None

    def configure_charging(self) -> "ChargingConfigurationBuilder":
        """Handle charging configuration UI."""
        charging_options = self.data_tables["charging_options"]

        self.charging_approach = st.radio(
            "Charging Approach",
            ["Single Charging Option", "Mixed Charging (Time-of-Use)"],
            index=0,
            help="Choose between a single charging method or a mix of different charging options"
        )

        use_charging_mix = self.charging_approach == "Mixed Charging (Time-of-Use)"

        if use_charging_mix:
            self.charging_mix = self._configure_mixed_charging(charging_options)
            # Get the first charging ID as default for mixed charging
            self.selected_charging = (
                charging_options.iloc[0][DataColumns.CHARGING_ID]
                if len(charging_options) > 0
                else None
            )
            logger.debug(
                f"Mixed charging - selected_charging set to: {self.selected_charging}"
            )
        else:
            self.selected_charging = self._configure_single_charging(charging_options)
            logger.debug(
                f"Single charging - selected_charging set to: {self.selected_charging}"
            )
            self.charging_mix = None

        logger.debug(f"Final charging_mix: {self.charging_mix}")
        return self

    def _configure_mixed_charging(
        self, charging_options: pd.DataFrame
    ) -> Optional[Dict[int, float]]:
        """Configure mixed charging with time-of-use allocation."""
        st.markdown(
            f"Allocate percentage of charging per option (must sum to {UI_CONFIG.CHARGING_MIX_TOTAL}%)"
        )
        st.info("💡 Use this to model realistic charging patterns with different rates at different times")
        
        charging_percentages: Dict[int, float] = {}
        total_percentage = 0
        default_pct = UI_CONFIG.CHARGING_MIX_TOTAL // len(charging_options)

        for idx, option in charging_options.iterrows():
            pct = st.slider(
                f"{option[DataColumns.CHARGING_APPROACH]} (${option[DataColumns.PER_KWH_PRICE]:.2f}/kWh)",
                0,
                UI_CONFIG.CHARGING_MIX_TOTAL,
                default_pct,
                UI_CONFIG.CHARGING_MIX_STEP,
                key=f"cm_{idx}",
                help=f"Percentage of charging using {option[DataColumns.CHARGING_APPROACH]}"
            )
            charging_percentages[option[DataColumns.CHARGING_ID]] = (
                pct / UI_CONFIG.CHARGING_MIX_TOTAL
            )
            total_percentage += pct

        if total_percentage != UI_CONFIG.CHARGING_MIX_TOTAL:
            st.warning(
                f"⚠️ Total allocation must equal {UI_CONFIG.CHARGING_MIX_TOTAL}% (current: {total_percentage}%)"
            )
            return None
        else:
            st.success(f"✅ Total allocation: {total_percentage}%")
            return charging_percentages

    def _configure_single_charging(self, charging_options: pd.DataFrame) -> int:
        """Configure single charging option."""
        return st.selectbox(
            "Primary Charging Approach",
            charging_options[DataColumns.CHARGING_ID].tolist(),
            format_func=lambda x: charging_options[
                charging_options[DataColumns.CHARGING_ID] == x
            ]
            .loc[:, [DataColumns.CHARGING_APPROACH, DataColumns.PER_KWH_PRICE]]
            .apply(lambda r: f"{r.iloc[0]} (${r.iloc[1]:.2f}/kWh)", axis=1)
            .iloc[0],
            key="primary_charging_selector",
            help="Select the primary method for charging your electric vehicle"
        )

    def build(self) -> Dict[str, Any]:
        """Return charging configuration context."""
        result = {
            DataColumns.CHARGING_APPROACH: self.charging_approach,
            "charging_mix": self.charging_mix,
            "selected_charging": self.selected_charging,
        }
        logger.debug(f"ChargingConfigurationBuilder.build() returning: {result}")
        return result


class InfrastructureBuilder:
    """Builds infrastructure configuration context."""

    def __init__(self, data_tables: Dict[str, pd.DataFrame]):
        self.data_tables = data_tables
        self.selected_infrastructure = None
        self.fleet_size = None

    def configure_infrastructure(self) -> "InfrastructureBuilder":
        """Handle infrastructure configuration UI."""
        infrastructure_options = self.data_tables["infrastructure_options"]

        self.selected_infrastructure = st.selectbox(
            "Charging Infrastructure",
            infrastructure_options[DataColumns.INFRASTRUCTURE_ID].tolist(),
            format_func=lambda x: infrastructure_options[
                infrastructure_options[DataColumns.INFRASTRUCTURE_ID] == x
            ].iloc[0][DataColumns.INFRASTRUCTURE_DESCRIPTION],
            key="infrastructure_selector",
            help="Choose the type of charging infrastructure for your fleet"
        )

        self.fleet_size = st.number_input(
            "Fleet Size",
            VALIDATION_LIMITS.MIN_FLEET_SIZE,
            VALIDATION_LIMITS.MAX_FLEET_SIZE,
            VALIDATION_LIMITS.MIN_FLEET_SIZE,
            VALIDATION_LIMITS.FLEET_SIZE_STEP,
            help="Number of vehicles sharing the infrastructure"
        )

        # Show infrastructure cost preview
        selected_infra = infrastructure_options[
            infrastructure_options[DataColumns.INFRASTRUCTURE_ID] == self.selected_infrastructure
        ].iloc[0]
        
        if self.fleet_size > 0:
            cost_per_vehicle = selected_infra[DataColumns.INFRASTRUCTURE_PRICE] / self.fleet_size
            st.info(f"💰 Infrastructure cost per vehicle: ${cost_per_vehicle:,.0f}")

        return self

    def build(self) -> Dict[str, Any]:
        """Return infrastructure context."""
        return {
            "selected_infrastructure": self.selected_infrastructure,
            "fleet_size": self.fleet_size,
        }
