"""Consolidated TCO Calculation Service."""

# Domain module imports - to be reviewed based on model_runner logic
from tco_app.domain import (  # battery is not directly used by model_runner top level
    energy,
    externalities,
    finance,
)
from tco_app.domain.finance_payload import calculate_payload_penalty_costs
from tco_app.domain.sensitivity import (
    metrics as sensitivity_metrics,
)  # Added import for calculate_comparative_metrics
from tco_app.repositories import ParametersRepository, VehicleRepository  # Added

# NEW: centralised DTOs
from tco_app.services.dtos import CalculationRequest, ComparisonResult, TCOResult
from tco_app.services.helpers import (
    get_residual_value_parameters,
)
from tco_app.src import Any, Dict, logging
from tco_app.src.constants import DataColumns, Drivetrain
from tco_app.src.exceptions import CalculationError
from tco_app.src.utils.battery import (
    calculate_battery_replacement,
)  # Used by model_runner
from tco_app.src.utils.energy import weighted_electricity_price  # Used by model_runner

logger = logging.getLogger(__name__)


class TCOCalculationService:
    def __init__(
        self, vehicle_repo: VehicleRepository, params_repo: ParametersRepository
    ):
        self.vehicle_repo = vehicle_repo
        self.params_repo = params_repo
        # UI Overrides for diesel_price, carbon_price etc. from CalculationParameters
        # are expected to be applied to financial_params/battery_params DataFrames
        # *before* they are passed into CalculationRequest, or handled inside the
        # relevant `calculate_*` methods if they are simple value replacements.
        # The current `calculate_single_vehicle_tco` doesn't explicitly use these overrides from `request.parameters`
        # directly, but assumes they are reflected in the DataFrames like `request.financial_params`.

    def calculate_single_vehicle_tco(self, request: CalculationRequest) -> TCOResult:
        """
        Calculates the Total Cost of Ownership (TCO) and related metrics for a single vehicle
        based on the provided CalculationRequest.

        This method orchestrates calls to various domain modules (energy, finance, externalities)
        to compute different aspects of the TCO.
        """
        logger.info(
            f"Starting TCO calculation for vehicle: {request.vehicle_data.get(DataColumns.VEHICLE_ID, 'N/A')}"
        )

        try:
            logger.debug("About to calculate energy costs...")
            energy_costs = self._calculate_energy_costs(request)
            logger.debug("Energy costs calculated successfully")

            logger.debug("About to calculate annual costs...")
            annual_costs = self._calculate_annual_costs(request, energy_costs)
            logger.debug("Annual costs calculated successfully")

            logger.debug("About to calculate acquisition costs...")
            acquisition_costs = self._calculate_acquisition_costs(request)
            logger.debug("Acquisition costs calculated successfully")

            logger.debug("About to calculate battery costs...")
            battery_costs = self._calculate_battery_costs(request)
            logger.debug("Battery costs calculated successfully")

            logger.debug("About to calculate externalities...")
            externalities = self._calculate_externalities(request)
            logger.debug("Externalities calculated successfully")

            logger.debug("About to calculate infrastructure costs...")
            infrastructure_costs = self._calculate_infrastructure_costs(request)
            logger.debug("Infrastructure costs calculated successfully")

            logger.debug("About to assemble TCO result...")
            return self._assemble_tco_result(
                request,
                energy_costs,
                annual_costs,
                acquisition_costs,
                battery_costs,
                externalities,
                infrastructure_costs,
            )

        except Exception as e:
            vehicle_id_for_error = (
                request.vehicle_data.get(DataColumns.VEHICLE_ID, "N/A")
                if request and hasattr(request, "vehicle_data")
                else "N/A"
            )
            logger.error(
                f"TCO calculation failed for vehicle {vehicle_id_for_error}: {e}",
                exc_info=True,
            )
            raise CalculationError(
                f"Failed to calculate TCO for vehicle {vehicle_id_for_error}: {str(e)}"
            ) from e

    def _calculate_energy_costs(self, request: CalculationRequest) -> Dict[str, Any]:
        """Calculate energy costs and emissions for the vehicle."""
        logger.debug("Calculating energy and annual costs.")

        energy_cost_per_km = energy.calculate_energy_costs(
            request.vehicle_data,
            request.fees_data,
            request.charging_options,
            request.financial_params,
            request.parameters.selected_charging_profile_id,
            (
                request.parameters.charging_mix
                if request.drivetrain == Drivetrain.BEV
                else None
            ),
        )

        emissions_result = energy.calculate_emissions(
            request.vehicle_data,
            request.emission_factors,
            request.parameters.annual_kms,
            request.parameters.truck_life_years,
        )

        return {
            "energy_cost_per_km": energy_cost_per_km,
            "emissions_result": emissions_result,
        }

    def _calculate_annual_costs(
        self, request: CalculationRequest, energy_costs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate annual operating costs."""
        logger.debug("Calculating annual costs.")

        annual_costs_result = finance.calculate_annual_costs(
            request.vehicle_data,
            request.fees_data,
            energy_costs["energy_cost_per_km"],
            request.parameters.annual_kms,
            request.incentives,
            request.parameters.apply_incentives,
        )

        npv_annual_operating_cost = finance.calculate_npv(
            annual_costs_result["annual_operating_cost"],
            request.parameters.discount_rate,
            request.parameters.truck_life_years,
        )

        return {
            "annual_costs_result": annual_costs_result,
            "npv_annual_operating_cost": npv_annual_operating_cost,
        }

    def _calculate_acquisition_costs(
        self, request: CalculationRequest
    ) -> Dict[str, Any]:
        """Calculate acquisition cost and residual value."""
        logger.debug("Calculating acquisition cost and residual value.")

        acquisition_cost = finance.calculate_acquisition_cost(
            request.vehicle_data,
            request.fees_data,
            request.incentives,
            request.parameters.apply_incentives,
        )

        # Retrieve depreciation parameters via central helper
        initial_dep, annual_dep = get_residual_value_parameters(
            request.financial_params
        )

        residual_value = finance.calculate_residual_value(
            request.vehicle_data,
            request.parameters.truck_life_years,
            initial_dep,
            annual_dep,
        )

        return {"acquisition_cost": acquisition_cost, "residual_value": residual_value}

    def _calculate_battery_costs(self, request: CalculationRequest) -> Dict[str, Any]:
        """Calculate battery replacement costs (BEV only)."""
        logger.debug("Calculating battery costs.")

        npv_battery_replacement_cost = 0.0
        if request.drivetrain == Drivetrain.BEV:
            npv_battery_replacement_cost = calculate_battery_replacement(
                request.vehicle_data,
                request.battery_params,
                request.parameters.truck_life_years,
                request.parameters.discount_rate,
            )

        return {"npv_battery_replacement_cost": npv_battery_replacement_cost}

    def _calculate_externalities(self, request: CalculationRequest) -> Dict[str, Any]:
        """Calculate externality costs."""
        logger.debug("Calculating externalities.")

        externalities_result = externalities.calculate_externalities(
            request.vehicle_data,
            request.externalities_data,
            request.parameters.annual_kms,
            request.parameters.truck_life_years,
            request.parameters.discount_rate,
        )

        return externalities_result

    def _calculate_infrastructure_costs(
        self, request: CalculationRequest
    ) -> Dict[str, Any]:
        """Calculate infrastructure costs and charging requirements (BEV only)."""
        logger.debug("Calculating infrastructure costs.")

        npv_infrastructure_cost_vehicle = 0.0
        infrastructure_costs_breakdown_vehicle = None
        charging_requirements_vehicle = None

        if request.drivetrain == Drivetrain.BEV:
            # Get selected infrastructure data
            selected_infra_df = request.infrastructure_options[
                request.infrastructure_options[DataColumns.INFRASTRUCTURE_ID]
                == request.parameters.selected_infrastructure_id
            ]
            if selected_infra_df.empty:
                raise CalculationError(
                    f"Selected infrastructure ID {request.parameters.selected_infrastructure_id} not found."
                )
            selected_infra_data = selected_infra_df.iloc[0]

            charging_requirements_vehicle = energy.calculate_charging_requirements(
                request.vehicle_data, request.parameters.annual_kms, selected_infra_data
            )

            # Calculate raw infrastructure costs
            infra_costs_raw = finance.calculate_infrastructure_costs(
                selected_infra_data,
                request.parameters.truck_life_years,
                request.parameters.discount_rate,
                request.parameters.fleet_size,
            )

            # Apply incentives to infrastructure
            infra_costs_with_incentives = finance.apply_infrastructure_incentives(
                infra_costs_raw, request.incentives, request.parameters.apply_incentives
            )
            infra_costs_with_incentives["fleet_size"] = request.parameters.fleet_size

            infrastructure_costs_breakdown_vehicle = infra_costs_with_incentives

            # The value to add to TCO is the per-vehicle share of NPV of infrastructure
            npv_infrastructure_cost_vehicle = infra_costs_with_incentives.get(
                "npv_per_vehicle_with_incentives",
                infra_costs_with_incentives["npv_per_vehicle"],
            )

        return {
            "npv_infrastructure_cost": npv_infrastructure_cost_vehicle,
            "infrastructure_costs_breakdown": infrastructure_costs_breakdown_vehicle,
            "charging_requirements": charging_requirements_vehicle,
        }

    def _assemble_tco_result(
        self,
        request: CalculationRequest,
        energy_costs: Dict[str, Any],
        annual_costs: Dict[str, Any],
        acquisition_costs: Dict[str, Any],
        battery_costs: Dict[str, Any],
        externalities: Dict[str, Any],
        infrastructure_costs: Dict[str, Any],
    ) -> TCOResult:
        """Assemble the final TCO result from all calculated components."""
        logger.debug("Assembling TCO result.")

        # Calculate raw TCO (before infrastructure)
        tco_breakdown_result = finance.calculate_tco(
            request.vehicle_data,
            request.fees_data,
            annual_costs["annual_costs_result"],
            acquisition_costs["acquisition_cost"],
            acquisition_costs["residual_value"],
            battery_costs["npv_battery_replacement_cost"],
            annual_costs["npv_annual_operating_cost"],
            request.parameters.annual_kms,
            request.parameters.truck_life_years,
        )

        # Calculate final TCO including infrastructure
        tco_total_lifetime_final = (
            tco_breakdown_result["tco_lifetime"]
            + infrastructure_costs["npv_infrastructure_cost"]
        )

        # Calculate social TCO
        social_tco_total_lifetime = tco_total_lifetime_final + externalities.get(
            "npv_externality", 0.0
        )

        # Calculate per-km and per-tonne-km metrics
        final_tco_per_km, final_tco_per_tonne_km = self._calculate_tco_metrics(
            tco_total_lifetime_final, request
        )

        # Calculate weighted electricity price for BEV
        weighted_elec_price = None
        if request.drivetrain == Drivetrain.BEV and request.parameters.charging_mix:
            weighted_elec_price = weighted_electricity_price(
                request.parameters.charging_mix, request.charging_options
            )

        return TCOResult(
            vehicle_id=request.vehicle_data.get(
                DataColumns.VEHICLE_ID, "unknown_vehicle"
            ),
            tco_total_lifetime=tco_total_lifetime_final,
            tco_per_km=final_tco_per_km,
            tco_per_tonne_km=final_tco_per_tonne_km,
            social_tco_total_lifetime=social_tco_total_lifetime,
            acquisition_cost=acquisition_costs["acquisition_cost"],
            residual_value=acquisition_costs["residual_value"],
            npv_annual_operating_cost=annual_costs["npv_annual_operating_cost"],
            npv_battery_replacement_cost=battery_costs["npv_battery_replacement_cost"],
            npv_infrastructure_cost=infrastructure_costs["npv_infrastructure_cost"],
            annual_operating_cost=annual_costs["annual_costs_result"][
                "annual_operating_cost"
            ],
            energy_cost_per_km=energy_costs["energy_cost_per_km"],
            lifetime_emissions_co2e=energy_costs["emissions_result"][
                "lifetime_emissions"
            ],
            annual_emissions_co2e=energy_costs["emissions_result"]["annual_emissions"],
            co2e_per_km=energy_costs["emissions_result"]["co2_per_km"],
            annual_costs_breakdown=annual_costs["annual_costs_result"],
            tco_breakdown=tco_breakdown_result,
            externalities_breakdown=externalities,
            emissions_breakdown=energy_costs["emissions_result"],
            charging_requirements=infrastructure_costs["charging_requirements"],
            infrastructure_costs_breakdown=infrastructure_costs[
                "infrastructure_costs_breakdown"
            ],
            weighted_electricity_price=weighted_elec_price,
            scenario_meta={"name": request.parameters.scenario_name},
        )

    def _calculate_tco_metrics(
        self, tco_total_lifetime: float, request: CalculationRequest
    ) -> tuple[float, float]:
        """Calculate per-km and per-tonne-km TCO metrics."""
        tco_per_km = 0.0
        tco_per_tonne_km = 0.0

        if (
            request.parameters.annual_kms > 0
            and request.parameters.truck_life_years > 0
        ):
            total_lifetime_kms = (
                request.parameters.annual_kms * request.parameters.truck_life_years
            )
            tco_per_km = tco_total_lifetime / total_lifetime_kms
            payload_t = request.vehicle_data.get(DataColumns.PAYLOAD_T, 0)
            if payload_t > 0:
                tco_per_tonne_km = tco_per_km / payload_t

        return tco_per_km, tco_per_tonne_km

    def compare_vehicles(
        self,
        base_vehicle_request: CalculationRequest,
        comparison_vehicle_request: CalculationRequest,
    ) -> ComparisonResult:
        """
        Compares TCO of two vehicles (e.g., a BEV vs. a Diesel).

        Typically, base_vehicle_request would be for the new technology (e.g., BEV)
        and comparison_vehicle_request for the incumbent (e.g., Diesel).
        The savings are usually calculated as (Incumbent - New Tech).
        """
        logger.info(
            f"Starting TCO comparison between {base_vehicle_request.vehicle_data.get(DataColumns.VEHICLE_ID, 'Base')} and {comparison_vehicle_request.vehicle_data.get(DataColumns.VEHICLE_ID, 'Comparison')}"
        )

        base_tco_result = self.calculate_single_vehicle_tco(base_vehicle_request)
        comparison_tco_result = self.calculate_single_vehicle_tco(
            comparison_vehicle_request
        )

        # Calculate payload penalties if comparing BEV vs Diesel
        payload_penalties = None
        if (base_vehicle_request.drivetrain == Drivetrain.BEV and 
            comparison_vehicle_request.drivetrain == Drivetrain.DIESEL):
            # Create temporary dictionaries for payload calculation
            bev_temp = {
                "vehicle_data": base_vehicle_request.vehicle_data,
                "annual_kms": base_vehicle_request.parameters.annual_kms,
                "truck_life_years": base_vehicle_request.parameters.truck_life_years,
                "energy_cost_per_km": base_tco_result.energy_cost_per_km,
                "annual_costs": {
                    "annual_operating_cost": base_tco_result.annual_operating_cost,
                    "annual_energy_cost": base_tco_result.annual_costs_breakdown.get("annual_energy_cost", 0),
                    "annual_maintenance_cost": base_tco_result.annual_costs_breakdown.get("annual_maintenance_cost", 0),
                    "insurance_annual": base_tco_result.annual_costs_breakdown.get("insurance_annual", 0),
                    "registration_annual": base_tco_result.annual_costs_breakdown.get("registration_annual", 0),
                },
                "tco": {
                    "npv_total_cost": base_tco_result.tco_total_lifetime,
                    "tco_per_tonne_km": base_tco_result.tco_per_tonne_km,
                },
            }
            
            diesel_temp = {
                "vehicle_data": comparison_vehicle_request.vehicle_data,
                "annual_kms": comparison_vehicle_request.parameters.annual_kms,
                "truck_life_years": comparison_vehicle_request.parameters.truck_life_years,
                "energy_cost_per_km": comparison_tco_result.energy_cost_per_km,
                "annual_costs": {
                    "annual_operating_cost": comparison_tco_result.annual_operating_cost,
                    "annual_energy_cost": comparison_tco_result.annual_costs_breakdown.get("annual_energy_cost", 0),
                    "annual_maintenance_cost": comparison_tco_result.annual_costs_breakdown.get("annual_maintenance_cost", 0),
                    "insurance_annual": comparison_tco_result.annual_costs_breakdown.get("insurance_annual", 0),
                    "registration_annual": comparison_tco_result.annual_costs_breakdown.get("registration_annual", 0),
                },
                "tco": {
                    "npv_total_cost": comparison_tco_result.tco_total_lifetime,
                    "tco_per_tonne_km": comparison_tco_result.tco_per_tonne_km,
                },
            }
            
            payload_penalties = calculate_payload_penalty_costs(
                bev_temp, diesel_temp, base_vehicle_request.financial_params
            )

        # Create ComparisonResult with basic data
        tco_savings = (
            comparison_tco_result.tco_total_lifetime
            - base_tco_result.tco_total_lifetime
        )
        
        # Adjust TCO savings if payload penalties exist
        if payload_penalties and payload_penalties.get("has_penalty", False):
            # Adjust BEV TCO with payload penalty
            adjusted_bev_tco = payload_penalties["bev_adjusted_lifetime_tco"]
            tco_savings = comparison_tco_result.tco_total_lifetime - adjusted_bev_tco
        
        # Ensure annual_kms and truck_life_years are consistent for the comparison.
        # Using values from the base_vehicle_request as representative.
        annual_kms_for_comparison = base_vehicle_request.parameters.annual_kms
        truck_life_years_for_comparison = (
            base_vehicle_request.parameters.truck_life_years
        )
        
        # Create initial ComparisonResult
        comparison_output = ComparisonResult(
            base_vehicle_result=base_tco_result,
            comparison_vehicle_result=comparison_tco_result,
            tco_savings_lifetime=tco_savings,
            annual_kms=annual_kms_for_comparison,
            truck_life_years=truck_life_years_for_comparison,
            payload_penalties=payload_penalties,
        )

        # Calculate comparative metrics using the new DTO-based function
        comparative_metrics_dict = sensitivity_metrics.calculate_comparative_metrics_from_dto(
            comparison_output
        )

        # Populate ComparisonResult with all relevant metrics from the dictionary
        upfront_diff = comparative_metrics_dict.get("upfront_cost_difference")
        annual_op_savings = comparative_metrics_dict.get("annual_operating_savings")
        price_parity = comparative_metrics_dict.get("price_parity_year")
        emission_savings = comparative_metrics_dict.get("emission_savings_lifetime")
        abatement = comparative_metrics_dict.get("abatement_cost")
        ratio = comparative_metrics_dict.get("bev_to_diesel_tco_ratio")

        # Update the ComparisonResult with calculated metrics
        comparison_output.annual_operating_cost_savings = annual_op_savings
        comparison_output.emissions_reduction_lifetime_co2e = emission_savings
        comparison_output.payback_period_years = price_parity
        comparison_output.upfront_cost_difference = upfront_diff
        comparison_output.abatement_cost = abatement
        comparison_output.bev_to_diesel_tco_ratio = ratio

        logger.info(
            f"TCO comparison completed using domain.sensitivity.metrics.calculate_comparative_metrics_from_dto. Lifetime TCO Savings ({base_tco_result.vehicle_id} vs {comparison_tco_result.vehicle_id}): {tco_savings:.2f}"
        )
        return comparison_output
