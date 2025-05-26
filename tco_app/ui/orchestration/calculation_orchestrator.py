"""Orchestrates TCO calculations after UI context is built."""

from tco_app.repositories import ParametersRepository, VehicleRepository
from tco_app.services.dtos import CalculationParameters, CalculationRequest
from tco_app.services.tco_calculation_service import (
    ComparisonResult,
    TCOCalculationService,
    TCOResult,
)
from tco_app.src import Any, Dict, logging, pd
from tco_app.src.constants import DataColumns, Drivetrain, ParameterKeys
from tco_app.src.exceptions import CalculationError, VehicleNotFoundError

logger = logging.getLogger(__name__)


class CalculationOrchestrator:
    """Orchestrates TCO calculations using UI context."""

    def __init__(
        self, data_tables: Dict[str, pd.DataFrame], ui_context: Dict[str, Any]
    ):
        self.data_tables = data_tables
        self.ui_context = ui_context
        # modified_tables contains tables after scenario application.
        # These should be passed to the repositories if the repositories are expected
        # to serve scenario-modified data. Or, ensure scenarios are applied before data_tables
        # is passed to this orchestrator/repositories.
        self.modified_tables = ui_context.get("modified_tables", data_tables)

        # Initialize repositories with potentially modified tables if that's the contract.
        # If repositories should always use base data, then pass self.data_tables. For now, using modified.
        self.vehicle_repo = VehicleRepository(self.modified_tables)
        self.params_repo = ParametersRepository(self.modified_tables)

        # Initialize the new calculation service
        self.tco_service = TCOCalculationService(
            vehicle_repo=self.vehicle_repo, params_repo=self.params_repo
        )

    def _build_calculation_request(self, vehicle_id: str) -> CalculationRequest:
        """Build a CalculationRequest from UI context and data tables."""

        vehicle_data_series = self.vehicle_repo.get_vehicle_by_id(vehicle_id)
        fees_data_series = self.vehicle_repo.get_fees_by_vehicle_id(vehicle_id)

        # Build parameters from UI context
        # Note: selected_charging and selected_infrastructure from UI context are IDs.
        parameters = CalculationParameters(
            annual_kms=self.ui_context["annual_kms"],
            truck_life_years=self.ui_context["truck_life_years"],
            discount_rate=self.ui_context["discount_rate"],
            fleet_size=self.ui_context.get("fleet_size", 1),
            apply_incentives=self.ui_context.get("apply_incentives", True),
            charging_mix=self.ui_context.get("charging_mix"),
            selected_charging_profile_id=self.ui_context[
                "selected_charging"
            ],  # Assuming this is the ID
            selected_infrastructure_id=self.ui_context[
                "selected_infrastructure"
            ],  # Assuming this is the ID
            scenario_name=self.ui_context.get("scenario_meta", {}).get(
                "name", "Default"
            ),
            diesel_price_override=self.ui_context.get(
                ParameterKeys.DIESEL_PRICE
            ),  # Using ParameterKeys for consistency
            carbon_price_override=self.ui_context.get(ParameterKeys.CARBON_PRICE),
            # Battery parameter overrides from UI context
            degradation_rate_override=self.ui_context.get("degradation_rate"),
            replacement_cost_override=self.ui_context.get("replacement_cost"),
        )

        # Parameters like diesel_price_override from CalculationParameters are intended to inform
        # how the financial_params DataFrame (and others) might be adjusted.
        # This adjustment should happen *before* creating the CalculationRequest,
        # or the TCOCalculationService needs to be aware of these overrides.
        # For now, we pass the already modified tables (from scenarios) and the override params.
        # The _apply_ui_overrides_to_params method mentioned in the plan would handle this.

        financial_params_for_request = self._apply_ui_overrides_to_financial_params(
            self.params_repo.get_financial_params(), parameters
        )
        battery_params_for_request = self._apply_ui_overrides_to_battery_params(
            self.params_repo.get_battery_params(), parameters
        )

        # Get incentives from modified tables if available, otherwise from repo
        incentives_for_request = self.modified_tables.get("incentives")
        if incentives_for_request is None or incentives_for_request.empty:
            incentives_for_request = self.params_repo.get_incentives()

        return CalculationRequest(
            vehicle_data=vehicle_data_series,
            fees_data=fees_data_series,
            parameters=parameters,
            charging_options=self.params_repo.get_charging_options(),
            infrastructure_options=self.params_repo.get_infrastructure_options(),
            financial_params=financial_params_for_request,  # Pass the adjusted DF
            battery_params=battery_params_for_request,  # Pass the adjusted DF
            emission_factors=self.params_repo.get_emission_factors(),
            externalities_data=self.params_repo.get_externalities_data(),
            incentives=incentives_for_request,  # Use modified incentives from UI
        )

    def _apply_ui_overrides_to_financial_params(
        self, financial_params_df: pd.DataFrame, calc_params: CalculationParameters
    ) -> pd.DataFrame:
        """Apply UI overrides to a copy of the financial parameters DataFrame."""
        if financial_params_df.empty:
            return pd.DataFrame()
        df_copy = financial_params_df.copy()
        if calc_params.diesel_price_override is not None:
            mask = (
                df_copy[DataColumns.FINANCE_DESCRIPTION] == ParameterKeys.DIESEL_PRICE
            )
            df_copy.loc[mask, DataColumns.FINANCE_DEFAULT_VALUE] = (
                calc_params.diesel_price_override
            )
        if calc_params.carbon_price_override is not None:
            mask = (
                df_copy[DataColumns.FINANCE_DESCRIPTION] == ParameterKeys.CARBON_PRICE
            )
            df_copy.loc[mask, DataColumns.FINANCE_DEFAULT_VALUE] = (
                calc_params.carbon_price_override
            )
        # Add more overrides here if needed
        return df_copy

    def _apply_ui_overrides_to_battery_params(
        self, battery_params_df: pd.DataFrame, calc_params: CalculationParameters
    ) -> pd.DataFrame:
        """Apply UI overrides to a copy of the battery parameters DataFrame."""
        if battery_params_df.empty:
            logger.warning(
                "Battery parameters DataFrame is empty. Cannot apply UI overrides."
            )
            return pd.DataFrame()

        df_copy = battery_params_df.copy()

        # Ensure the required columns exist
        description_col = "battery_description"  # Match actual CSV column name
        value_col = "default_value"  # Based on data/dictionary/battery_params.csv

        if description_col not in df_copy.columns or value_col not in df_copy.columns:
            logger.error(
                f"Battery parameters DataFrame is missing required columns: '{description_col}' or '{value_col}'. Cannot apply overrides."
            )
            return df_copy  # Return original copy if columns are missing

        if calc_params.degradation_rate_override is not None:
            mask = df_copy[description_col] == ParameterKeys.DEGRADATION_RATE.value
            if mask.any():
                df_copy.loc[mask, value_col] = calc_params.degradation_rate_override
                logger.debug(
                    f"Applied degradation_rate_override: {calc_params.degradation_rate_override}"
                )
            else:
                logger.warning(
                    f"Parameter key '{ParameterKeys.DEGRADATION_RATE.value}' not found in battery_params_df description column."
                )

        if calc_params.replacement_cost_override is not None:
            mask = df_copy[description_col] == ParameterKeys.REPLACEMENT_COST.value
            if mask.any():
                df_copy.loc[mask, value_col] = calc_params.replacement_cost_override
                logger.debug(
                    f"Applied replacement_cost_override: {calc_params.replacement_cost_override}"
                )
            else:
                logger.warning(
                    f"Parameter key '{ParameterKeys.REPLACEMENT_COST.value}' not found in battery_params_df description column."
                )

        return df_copy

    def perform_calculations(self) -> Dict[str, Any]:
        """Perform all TCO calculations and return complete context."""
        logger.info("Starting TCO calculations using new TCOCalculationService...")

        try:
            bev_request = self._build_calculation_request(
                self.ui_context["selected_bev_id"]
            )
            diesel_request = self._build_calculation_request(
                self.ui_context["comparison_diesel_id"]
            )

            comparison_result = self.tco_service.compare_vehicles(
                base_vehicle_request=bev_request,  # Assuming BEV is the base for comparison metrics
                comparison_vehicle_request=diesel_request,
            )

            # Always return DTOs directly
            return self._prepare_dto_results(
                comparison_result,
                bev_request,
                diesel_request,
            )

        except VehicleNotFoundError as e:
            # Consider if st.error is appropriate here or if exceptions should propagate
            # For now, logging and returning empty/error structure
            logger.error(f"Vehicle not found during TCO calculation: {e}")
            # return self._empty_results_placeholder() # Placeholder for error result structure
            raise  # Re-raise for now, UI layer can catch and display
        except CalculationError:
            logger.error("Calculation error during TCO calculation")
            # return self._empty_results_placeholder()
            raise
        except Exception:  # Catch any other unexpected error
            logger.exception("Unexpected error in TCO calculations")
            # return self._empty_results_placeholder()
            raise

    def _prepare_dto_results(
        self,
        comparison: ComparisonResult,
        bev_request: CalculationRequest,
        diesel_request: CalculationRequest,
    ) -> Dict[str, Any]:
        """Prepare results with DTOs for components that support them."""
        # Add context data to the DTOs
        bev_result = comparison.base_vehicle_result
        diesel_result = comparison.comparison_vehicle_result
        
        # Store request data on the DTOs for UI components that need it
        bev_result.vehicle_data = bev_request.vehicle_data
        diesel_result.vehicle_data = diesel_request.vehicle_data
        
        # Store annual_kms and truck_life_years on DTOs if not already there
        bev_result.annual_kms = bev_request.parameters.annual_kms
        bev_result.truck_life_years = bev_request.parameters.truck_life_years
        diesel_result.annual_kms = diesel_request.parameters.annual_kms
        diesel_result.truck_life_years = diesel_request.parameters.truck_life_years
        
        return {
            "bev_results": bev_result,  # Return DTO directly
            "diesel_results": diesel_result,  # Return DTO directly
            "comparison": comparison,  # Return ComparisonResult DTO
            # Legacy fields for compatibility
            "comparison_metrics": {
                "upfront_cost_difference": comparison.upfront_cost_difference,
                "annual_operating_savings": comparison.annual_operating_cost_savings,
                "price_parity_year": comparison.payback_period_years,
                "emission_savings_lifetime": comparison.emissions_reduction_lifetime_co2e,
                "abatement_cost": comparison.abatement_cost,
                "bev_to_diesel_tco_ratio": comparison.bev_to_diesel_tco_ratio,
            },
            # Keep other context data for pages that need it
            "annual_kms": self.ui_context["annual_kms"],
            "truck_life_years": self.ui_context["truck_life_years"],
            "discount_rate": self.ui_context["discount_rate"],
            "fleet_size": self.ui_context.get("fleet_size", 1),
            "charging_mix": self.ui_context.get("charging_mix"),
            "apply_incentives": self.ui_context.get("apply_incentives", True),
            "scenario_meta": self.ui_context.get("scenario_meta", {}),
            "selected_incentives": self.ui_context.get("selected_incentives", []),
            # Data tables for pages that need them
            "charging_options": bev_request.charging_options,
            "infrastructure_options": bev_request.infrastructure_options,
            "financial_params_with_ui": bev_request.financial_params,
            "battery_params_with_ui": bev_request.battery_params,
            "emission_factors": bev_request.emission_factors,
            "externalities_data": bev_request.externalities_data,  # Add externalities data
            "incentives": bev_request.incentives,
            # Pass through UI context selections
            "selected_charging": self.ui_context["selected_charging"],
            "selected_infrastructure": self.ui_context["selected_infrastructure"],
            # Vehicle data for sensitivity page
            "bev_vehicle_data": bev_request.vehicle_data,
            "diesel_vehicle_data": diesel_request.vehicle_data,
            "bev_fees": pd.DataFrame([bev_request.fees_data]) if isinstance(bev_request.fees_data, pd.Series) else bev_request.fees_data,
            "diesel_fees": pd.DataFrame([diesel_request.fees_data]) if isinstance(diesel_request.fees_data, pd.Series) else diesel_request.fees_data,
        }
