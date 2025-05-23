from tco_app.src.utils.safe_operations import safe_iloc_zero
"""Charging configuration builders for UI context."""
from typing import Dict, Any, Optional
from tco_app.src.constants import DataColumns, ParameterKeys
import pandas as pd
import streamlit as st


class ChargingConfigurationBuilder:
    """Builds charging configuration context."""
    
    def __init__(self, data_tables: Dict[str, pd.DataFrame]):
        self.data_tables = data_tables
        self.charging_approach = None
        self.charging_mix = None
        self.selected_charging = None
    
    def configure_charging(self) -> 'ChargingConfigurationBuilder':
        """Handle charging configuration UI."""
        charging_options = self.data_tables['charging_options']
        
        self.charging_approach = st.radio(
            'Charging Approach',
            ['Single Charging Option', 'Mixed Charging (Time-of-Use)'],
            index=0,
        )
        
        use_charging_mix = self.charging_approach == 'Mixed Charging (Time-of-Use)'
        
        if use_charging_mix:
            self.charging_mix = self._configure_mixed_charging(charging_options)
            self.selected_charging = safe_iloc_zero(charging_options, DataColumns.CHARGING_ID, context="charging_options lookup")
        else:
            self.selected_charging = self._configure_single_charging(charging_options)
            self.charging_mix = None
        
        return self
    
    def _configure_mixed_charging(self, charging_options: pd.DataFrame) -> Optional[Dict[int, float]]:
        """Configure mixed charging with time-of-use allocation."""
        st.markdown('Allocate percentage of charging per option (must sum to 100%)')
        charging_percentages: Dict[int, float] = {}
        total_percentage = 0
        default_pct = 100 // len(charging_options)
        
        for idx, option in charging_options.iterrows():
            pct = st.slider(
                option[DataColumns.CHARGING_APPROACH], 
                0, 100, 
                default_pct, 
                5, 
                key=f'cm_{idx}'
            )
            charging_percentages[option[DataColumns.CHARGING_ID]] = pct / 100
            total_percentage += pct
        
        if total_percentage != 100:
            st.warning(f'Total allocation must equal 100% (current {total_percentage}%)')
            return None
        else:
            return charging_percentages
    
    def _configure_single_charging(self, charging_options: pd.DataFrame) -> int:
        """Configure single charging option."""
        return st.selectbox(
            'Primary Charging Approach',
            charging_options[DataColumns.CHARGING_ID].tolist(),
            format_func=lambda x: charging_options[charging_options[DataColumns.CHARGING_ID] == x]
            .loc[:, [DataColumns.CHARGING_APPROACH, DataColumns.PER_KWH_PRICE]]
            .apply(lambda r: f"{r.iloc[0]} (${r.iloc[1]:.2f}/kWh)", axis=1)
            .iloc[0],
        )
    
    def build(self) -> Dict[str, Any]:
        """Return charging configuration context."""
        return {
            DataColumns.CHARGING_APPROACH: self.charging_approach,
            'charging_mix': self.charging_mix,
            'selected_charging': self.selected_charging
        }


class InfrastructureBuilder:
    """Builds infrastructure configuration context."""
    
    def __init__(self, data_tables: Dict[str, pd.DataFrame]):
        self.data_tables = data_tables
        self.selected_infrastructure = None
        self.fleet_size = None
        self.apply_incentives = None
    
    def configure_infrastructure(self) -> 'InfrastructureBuilder':
        """Handle infrastructure configuration UI."""
        infrastructure_options = self.data_tables['infrastructure_options']
        
        self.selected_infrastructure = st.selectbox(
            'Charging Infrastructure',
            infrastructure_options[DataColumns.INFRASTRUCTURE_ID].tolist(),
            format_func=lambda x: infrastructure_options[
                infrastructure_options[DataColumns.INFRASTRUCTURE_ID] == x
            ].iloc[0][DataColumns.INFRASTRUCTURE_DESCRIPTION],
        )
        
        self.fleet_size = st.number_input(
            'Number of Vehicles Sharing Infrastructure', 
            1, 1000, 1, 1
        )
        
        self.apply_incentives = st.checkbox('Apply Incentives', value=True)
        
        return self
    
    def build(self) -> Dict[str, Any]:
        """Return infrastructure context."""
        return {
            'selected_infrastructure': self.selected_infrastructure,
            'fleet_size': self.fleet_size,
            'apply_incentives': self.apply_incentives
        } 