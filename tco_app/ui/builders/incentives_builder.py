"""Incentives and policy builder for UI context."""

from typing import Dict, List, Set
from tco_app.src import Any, Dict as DictType, pd, st
from tco_app.src.constants import DataColumns


class IncentivesBuilder:
    """Builds incentives and policy configuration context."""

    def __init__(self, data_tables: DictType[str, pd.DataFrame]):
        self.data_tables = data_tables
        self.selected_incentives: Set[str] = set()
        self.incentive_descriptions = {
            "stamp_duty_exemption": "Stamp Duty Exemption - Remove stamp duty fee entirely for BEV vehicles",
            "registration_exemption": "Registration Fee Exemption - Exempt from annual registration fees",
            "accelerated_depreciation": "Accelerated Depreciation - Enhanced tax depreciation rate",
            "instant_asset_writeoff": "Instant Asset Write-off - Immediate tax deduction of full vehicle cost",
            "green_loan": "Green Finance Loan - Reduced interest rate on vehicle financing",
            "diesel_fuel_tax_credit": "Diesel Fuel Tax Credit - Tax credit for diesel fuel use",
            "electricity_rate_discount": "EV Electricity Rate - Discounted electricity for charging",
            "toll_road_exemption": "Toll Road Exemption - Free toll road access for EVs",
            "battery_replacement_subsidy": "Battery Replacement Subsidy - Support for battery replacement costs",
            "purchase_rebate_aud": "Purchase Rebate - Direct rebate on vehicle purchase price",
            "charging_infrastructure_subsidy": "Infrastructure Subsidy - Support for charging equipment costs",
            "carbon_price_redemption": "Carbon Credits - Generate carbon credits for emissions reduction",
            "battery_recycling_credit": "Battery Recycling Credit - End-of-life battery recycling incentive",
            "insurance_discount": "Insurance Discount - Reduced insurance costs for EVs"
        }

    def configure_incentives(self) -> "IncentivesBuilder":
        """Handle incentives configuration UI."""
        incentives_df = self.data_tables.get("incentives", pd.DataFrame())
        
        if incentives_df.empty:
            st.warning("No incentives data available")
            return self
        
        # Initialize session state for incentives if not exists
        if "incentive_select_all" not in st.session_state:
            st.session_state.incentive_select_all = False
        if "incentive_clear_all" not in st.session_state:
            st.session_state.incentive_clear_all = False
            
        # Group incentives by type
        bev_incentives = incentives_df[incentives_df["drivetrain"] == "BEV"]["incentive_type"].unique()
        diesel_incentives = incentives_df[incentives_df["drivetrain"] == "Diesel"]["incentive_type"].unique()
        all_incentives = list(bev_incentives) + list(diesel_incentives)
        
        # Get default active incentives (where incentive_flag = 1)
        default_active = set(incentives_df[incentives_df["incentive_flag"] == 1]["incentive_type"].values)
        
        # Quick select options at the top
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Select All", key="select_all_incentives"):
                st.session_state.incentive_select_all = True
                st.session_state.incentive_clear_all = False
        with col2:
            if st.button("Clear All", key="clear_all_incentives"):
                st.session_state.incentive_clear_all = True
                st.session_state.incentive_select_all = False
        with col3:
            # This will be updated after collecting selections
            selected_count_placeholder = st.empty()
        
        st.markdown("---")
        st.markdown("**Available Policies & Incentives**")
        st.info("💡 Select which government policies and incentives to include in the analysis")
        
        # Determine checkbox values based on button clicks
        def get_checkbox_value(incentive: str) -> bool:
            if st.session_state.incentive_select_all:
                return True
            elif st.session_state.incentive_clear_all:
                return False
            else:
                # Use session state if exists, otherwise use default
                key = f"incentive_{incentive}"
                if key in st.session_state:
                    return st.session_state[key]
                return incentive in default_active
        
        # BEV Incentives
        if len(bev_incentives) > 0:
            st.markdown("**🔋 Battery Electric Vehicle Incentives**")
            
            # Group related incentives
            purchase_incentives = ["stamp_duty_exemption", "registration_exemption", "purchase_rebate_aud"]
            operational_incentives = ["electricity_rate_discount", "toll_road_exemption", "insurance_discount"]
            tax_incentives = ["accelerated_depreciation", "instant_asset_writeoff", "green_loan"]
            sustainability_incentives = ["carbon_price_redemption", "battery_recycling_credit", "battery_replacement_subsidy"]
            infrastructure_incentives = ["charging_infrastructure_subsidy"]
            
            # Purchase incentives
            with st.container():
                st.markdown("*Purchase Support*")
                for incentive in purchase_incentives:
                    if incentive in bev_incentives:
                        desc = self.incentive_descriptions.get(incentive, incentive)
                        checkbox_value = get_checkbox_value(incentive)
                        if st.checkbox(desc, value=checkbox_value, key=f"incentive_{incentive}"):
                            self.selected_incentives.add(incentive)
            
            # Operational incentives
            with st.container():
                st.markdown("*Operational Benefits*")
                for incentive in operational_incentives:
                    if incentive in bev_incentives:
                        desc = self.incentive_descriptions.get(incentive, incentive)
                        checkbox_value = get_checkbox_value(incentive)
                        if st.checkbox(desc, value=checkbox_value, key=f"incentive_{incentive}"):
                            self.selected_incentives.add(incentive)
            
            # Tax incentives
            with st.container():
                st.markdown("*Tax Benefits*")
                for incentive in tax_incentives:
                    if incentive in bev_incentives:
                        desc = self.incentive_descriptions.get(incentive, incentive)
                        checkbox_value = get_checkbox_value(incentive)
                        if st.checkbox(desc, value=checkbox_value, key=f"incentive_{incentive}"):
                            self.selected_incentives.add(incentive)
            
            # Sustainability incentives
            with st.container():
                st.markdown("*Sustainability Support*")
                for incentive in sustainability_incentives:
                    if incentive in bev_incentives:
                        desc = self.incentive_descriptions.get(incentive, incentive)
                        checkbox_value = get_checkbox_value(incentive)
                        if st.checkbox(desc, value=checkbox_value, key=f"incentive_{incentive}"):
                            self.selected_incentives.add(incentive)
            
            # Infrastructure incentives
            with st.container():
                st.markdown("*Infrastructure Support*")
                for incentive in infrastructure_incentives:
                    if incentive in bev_incentives:
                        desc = self.incentive_descriptions.get(incentive, incentive)
                        checkbox_value = get_checkbox_value(incentive)
                        if st.checkbox(desc, value=checkbox_value, key=f"incentive_{incentive}"):
                            self.selected_incentives.add(incentive)
        
        # Diesel Incentives
        if len(diesel_incentives) > 0:
            st.markdown("---")
            st.markdown("**⛽ Diesel Vehicle Incentives**")
            for incentive in diesel_incentives:
                desc = self.incentive_descriptions.get(incentive, incentive)
                checkbox_value = get_checkbox_value(incentive)
                if st.checkbox(desc, value=checkbox_value, key=f"incentive_{incentive}"):
                    self.selected_incentives.add(incentive)
        
        # Update selected count
        selected_count_placeholder.metric("Selected", len(self.selected_incentives))
        
        # Reset the button states after processing
        if st.session_state.incentive_select_all or st.session_state.incentive_clear_all:
            st.session_state.incentive_select_all = False
            st.session_state.incentive_clear_all = False
            st.rerun()
        
        return self

    def build(self) -> DictType[str, Any]:
        """Return incentives context."""
        # For backward compatibility, set apply_incentives to True if any incentive is selected
        apply_incentives = len(self.selected_incentives) > 0
        
        # Update the incentives dataframe to reflect selections
        if "incentives" in self.data_tables:
            modified_incentives = self.data_tables["incentives"].copy()
            # Set incentive_flag based on selections
            modified_incentives["incentive_flag"] = modified_incentives["incentive_type"].apply(
                lambda x: 1 if x in self.selected_incentives else 0
            )
        else:
            modified_incentives = pd.DataFrame()
        
        return {
            "apply_incentives": apply_incentives,
            "selected_incentives": list(self.selected_incentives),
            "modified_incentives": modified_incentives
        } 