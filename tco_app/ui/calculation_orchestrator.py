"""Orchestrates TCO calculations after UI context is built."""

from tco_app.src import pd, logging, Dict, Any
from tco_app.src.constants import DataColumns, ParameterKeys, Drivetrain

from tco_app.services.tco_calculation_service import (
    TCOCalculationService,
    ComparisonResult,
    TCOResult,
)
from tco_app.services.dtos import (
    CalculationRequest,
    CalculationParameters,
)
from tco_app.repositories import VehicleRepository, ParametersRepository
from tco_app.src.exceptions import VehicleNotFoundError, CalculationError

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
            # degradation_rate_override and replacement_cost_override need keys from ui_context if they exist
            degradation_rate_override=self.ui_context.get(
                "battery_degradation_rate_override"
            ),  # Example key
            replacement_cost_override=self.ui_context.get(
                "battery_replacement_cost_override"
            ),  # Example key
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
            incentives=self.params_repo.get_incentives(),  # Assuming incentives from repo are scenario-modified
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
        description_col = "description"  # Based on data/dictionary/battery_params.csv
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

            ui_results = self._transform_results_for_ui(
                comparison_result,
                bev_request,  # Pass requests for context data
                diesel_request,
            )

            logger.info("TCO calculations complete using new service.")
            return ui_results

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

    def _transform_single_tco_result_for_ui(
        self, tco_result: TCOResult, request: CalculationRequest
    ) -> Dict[str, Any]:
        """Transforms a single TCOResult into the dict structure expected by the UI."""
        if tco_result is None or request is None:
            return {}

        # Ensure all keys accessed from tco_result.annual_costs_breakdown exist or have defaults
        annual_energy = tco_result.annual_costs_breakdown.get("annual_energy_cost", 0.0)
        annual_maint = tco_result.annual_costs_breakdown.get(
            "annual_maintenance_cost", 0.0
        )
        annual_reg = tco_result.annual_costs_breakdown.get("registration_annual", 0.0)
        annual_ins = tco_result.annual_costs_breakdown.get("insurance_annual", 0.0)

        # Ensure all keys for emissions exist or have defaults
        co2_per_km = tco_result.emissions_breakdown.get("co2_per_km", 0.0)
        annual_emissions = tco_result.emissions_breakdown.get("annual_emissions", 0.0)
        lifetime_emissions = tco_result.emissions_breakdown.get(
            "lifetime_emissions", 0.0
        )

        # TCO sub-dictionary
        tco_sub_dict = {
            "npv_total_cost": tco_result.tco_total_lifetime,
            "tco_per_km": tco_result.tco_per_km,
            "tco_per_tonne_km": tco_result.tco_per_tonne_km,
            "tco_lifetime": tco_result.tco_total_lifetime,
            "tco_annual": (
                tco_result.tco_total_lifetime / request.parameters.truck_life_years
                if request.parameters.truck_life_years > 0
                else 0
            ),
        }

        # Social TCO sub-dictionary (from domain.externalities.calculate_social_tco)
        # The TCOResult.social_tco_total_lifetime is the main value.
        # If the full dict from calculate_social_tco is needed, it should be stored in TCOResult.
        # For now, using the lifetime value and replicating structure if needed.
        social_tco_dict_transformed = {
            "social_tco_lifetime": tco_result.social_tco_total_lifetime,
            # Add per_km, per_tonne_km from the externalities_result['social_tco'] if available and needed
        }

        result_dict = {
            "vehicle_data": request.vehicle_data,
            "fees": request.fees_data,  # Series
            "energy_cost_per_km": tco_result.energy_cost_per_km,
            "annual_costs": {
                "annual_energy_cost": annual_energy,
                "annual_maintenance_cost": annual_maint,
                "registration_annual": annual_reg,
                "insurance_annual": annual_ins,
                "annual_operating_cost": tco_result.annual_operating_cost,
            },
            "emissions": {
                "co2_per_km": co2_per_km,
                "annual_emissions": annual_emissions,
                "lifetime_emissions": lifetime_emissions,
            },
            "acquisition_cost": tco_result.acquisition_cost,
            "residual_value": tco_result.residual_value,
            "battery_replacement": tco_result.npv_battery_replacement_cost,  # Was NPV of cost
            "npv_annual_cost": tco_result.npv_annual_operating_cost,
            "tco": tco_sub_dict,
            "externalities": tco_result.externalities_breakdown,  # Full breakdown from domain
            "social_tco": social_tco_dict_transformed,  # Lifetime value primarily
            # BEV-specific fields
            "charging_requirements": tco_result.charging_requirements,
            "infrastructure_costs": tco_result.infrastructure_costs_breakdown,
            "weighted_electricity_price": tco_result.weighted_electricity_price,
            # Context data
            "annual_kms": request.parameters.annual_kms,
            "truck_life_years": request.parameters.truck_life_years,
            "discount_rate": request.parameters.discount_rate,
            "scenario": {
                "name": request.parameters.scenario_name
            },  # Matches TCOResult.scenario_meta
            "charging_options": request.charging_options,  # Pass through full table if UI needs it
        }
        if request.parameters.charging_mix:
            result_dict["charging_mix"] = request.parameters.charging_mix

        # Selected infrastructure description was in old model, get it if available
        if (
            request.drivetrain == Drivetrain.BEV
            and not request.infrastructure_options.empty
        ):
            selected_infra_series = request.infrastructure_options[
                request.infrastructure_options[DataColumns.INFRASTRUCTURE_ID]
                == request.parameters.selected_infrastructure_id
            ]
            if not selected_infra_series.empty:
                result_dict["selected_infrastructure_description"] = (
                    selected_infra_series.iloc[0].get(
                        DataColumns.INFRASTRUCTURE_DESCRIPTION
                    )
                )

        return result_dict

    def _transform_results_for_ui(
        self,
        comparison: ComparisonResult,
        bev_request: CalculationRequest,
        diesel_request: CalculationRequest,
    ) -> Dict[str, Any]:
        """Transform service results to UI-expected format."""

        bev_ui_results = self._transform_single_tco_result_for_ui(
            comparison.base_vehicle_result, bev_request
        )
        diesel_ui_results = self._transform_single_tco_result_for_ui(
            comparison.comparison_vehicle_result, diesel_request
        )

        # Comparison metrics directly from ComparisonResult (which got them from domain.sensitivity.metrics)
        # Need to ensure keys in ComparisonResult match what UI expects or map them here.
        # The plan had specific keys for comparison_metrics, let's try to match that.
        # `comparison.tco_savings_lifetime` is (diesel_tco - bev_tco)
        # `comparison.annual_operating_cost_savings` is (diesel_op_cost - bev_op_cost)
        # `comparison.emissions_reduction_lifetime_co2e` is (diesel_emissions - bev_emissions)
        # `comparison.payback_period_years` is price_parity_year

        # The calculate_comparative_metrics returns a dict with keys like:
        # 'upfront_cost_difference', 'annual_operating_savings', 'price_parity_year',
        # 'emission_savings_lifetime', 'abatement_cost', 'bev_to_diesel_tco_ratio'
        # The TCOCalculationService.compare_vehicles populates ComparisonResult from this.
        # So, the fields in ComparisonResult should be used here.

        final_comparison_metrics = {
            "upfront_cost_difference": comparison.upfront_cost_difference,  # BEV - Diesel (from sensitivity_metrics)
            "annual_operating_savings": comparison.annual_operating_cost_savings,  # Already (Diesel - BEV)
            "price_parity_year": comparison.payback_period_years,
            "emission_savings_lifetime": comparison.emissions_reduction_lifetime_co2e,  # Already (Diesel - BEV)
            "abatement_cost": comparison.abatement_cost,
            "bev_to_diesel_tco_ratio": comparison.bev_to_diesel_tco_ratio,
        }
        # If abatement_cost and bev_to_diesel_tco_ratio are needed, they should be added to ComparisonResult dataclass
        # and populated in TCOCalculationService.compare_vehicles from the output of sensitivity_metrics.calculate_comparative_metrics.
        # For now, they are omitted if not in ComparisonResult.

        # Reconstruct the UI-expected structure
        return {
            "bev_results": bev_ui_results,
            "diesel_results": diesel_ui_results,
            "comparison_metrics": final_comparison_metrics,
            # Vehicle data and fees expected by sensitivity page
            "bev_vehicle_data": bev_request.vehicle_data,
            "diesel_vehicle_data": diesel_request.vehicle_data,
            "bev_fees": bev_request.fees_data,
            "diesel_fees": diesel_request.fees_data,
            # Charging and infrastructure options
            "charging_options": bev_request.charging_options,
            "infrastructure_options": bev_request.infrastructure_options,
            # Pass through other data points the UI might expect
            "financial_params_with_ui": bev_request.financial_params,
            "battery_params_with_ui": bev_request.battery_params,
            "emission_factors": bev_request.emission_factors,
            "incentives": bev_request.incentives,
            # Scalar values from UI context, often passed through
            "selected_charging": self.ui_context["selected_charging"],
            "selected_infrastructure": self.ui_context["selected_infrastructure"],
            "annual_kms": self.ui_context["annual_kms"],
            "truck_life_years": self.ui_context["truck_life_years"],
            "discount_rate": self.ui_context["discount_rate"],
            "fleet_size": self.ui_context.get("fleet_size", 1),
            "charging_mix": self.ui_context.get("charging_mix"),
            "apply_incentives": self.ui_context.get("apply_incentives", True),
            "scenario_meta": self.ui_context.get("scenario_meta", {}),
        }
