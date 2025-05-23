"""High-level calculation service orchestrating domain logic."""
from typing import Dict, Any, Optional
import logging
from dataclasses import dataclass
from datetime import datetime

from tco_app.domain import energy, finance, externalities, battery
from tco_app.src.exceptions import CalculationError
from tco_app.src.constants import DataColumns, ParameterKeys
from tco_app.src.utils.safe_operations import safe_get_parameter

logger = logging.getLogger(__name__)


@dataclass
class CalculationRequest:
    """Request object for TCO calculation."""
    vehicle_data: Any
    fees_data: Any
    scenario_params: Dict[str, Any]
    charging_options: Any
    infrastructure_options: Any
    financial_params: Any
    battery_params: Any
    emission_factors: Any
    incentives: Any
    
    # Calculation parameters
    annual_kms: int
    truck_life_years: int
    discount_rate: float
    fleet_size: int = 1
    apply_incentives: bool = True
    charging_mix: Optional[Dict[int, float]] = None


@dataclass
class CalculationResult:
    """Result object for TCO calculation."""
    vehicle_id: str
    tco_lifetime: float
    tco_per_km: float
    tco_per_tonne_km: float
    annual_operating_cost: float
    acquisition_cost: float
    residual_value: float
    emissions_lifetime: float
    emissions_per_km: float
    
    # Detailed breakdowns
    energy_costs: Dict[str, float]
    maintenance_costs: Dict[str, float]
    infrastructure_costs: Optional[Dict[str, float]]
    externality_costs: Dict[str, float]
    
    # Metadata
    calculation_timestamp: str
    scenario_name: str


class CalculationService:
    """Service for orchestrating TCO calculations."""
    
    def __init__(self):
        """Initialise calculation service."""
        self._cache = {}
    
    def calculate_vehicle_tco(
        self, request: CalculationRequest
    ) -> CalculationResult:
        """Calculate complete TCO for a single vehicle.
        
        Args:
            request: Calculation request with all parameters
            
        Returns:
            Complete TCO calculation result
            
        Raises:
            CalculationError: If calculation fails
        """
        try:
            vehicle_id = request.vehicle_data.get(DataColumns.VEHICLE_ID, 'unknown')
            
            # Step 1: Energy calculations
            energy_cost_per_km = self._calculate_energy_costs(request)
            
            # Step 2: Annual costs
            annual_result = self._calculate_annual_costs(
                request, energy_cost_per_km
            )
            
            # Step 3: Acquisition and financing
            acquisition_cost = self._calculate_acquisition_costs(request)
            
            # Step 4: Depreciation and residual
            residual_value = self._calculate_residual_value(request, acquisition_cost)
            
            # Step 5: Battery (if applicable)
            battery_cost = self._calculate_battery_costs(request)
            
            # Step 6: Infrastructure (if applicable)
            infra_result = self._calculate_infrastructure_costs(request)
            
            # Step 7: Externalities
            externality_result = self._calculate_externalities(request)
            
            # Step 8: Calculate NPV of annual costs
            npv_annual_cost = finance.calculate_npv(
                annual_result['annual_operating_cost'],
                request.truck_life_years,
                request.discount_rate
            )
            
            # Step 9: Aggregate TCO
            tco_result = finance.calculate_tco(
                request.vehicle_data,
                request.fees_data,
                annual_result,
                acquisition_cost,
                residual_value,
                battery_cost,
                npv_annual_cost,
                request.annual_kms,
                request.truck_life_years
            )
            
            # Step 10: Calculate emissions
            emissions_result = energy.calculate_emissions(
                request.vehicle_data,
                request.emission_factors,
                request.annual_kms,
                request.truck_life_years
            )
            
            return CalculationResult(
                vehicle_id=vehicle_id,
                tco_lifetime=tco_result['tco_lifetime'],
                tco_per_km=tco_result['tco_per_km'],
                tco_per_tonne_km=tco_result['tco_per_tonne_km'],
                annual_operating_cost=annual_result['annual_operating_cost'],
                acquisition_cost=acquisition_cost,
                residual_value=residual_value,
                emissions_lifetime=emissions_result['lifetime_emissions'],
                emissions_per_km=emissions_result['co2_per_km'],
                energy_costs={'energy_cost_per_km': energy_cost_per_km},
                maintenance_costs={
                    'annual_maintenance': annual_result['annual_maintenance_cost']
                },
                infrastructure_costs=infra_result,
                externality_costs=externality_result,
                calculation_timestamp=datetime.now().isoformat(),
                scenario_name=request.scenario_params.get('scenario_name', 'Unknown')
            )
            
        except Exception as e:
            logger.error(
                f"TCO calculation failed for vehicle {request.vehicle_data.get('vehicle_id')}: {e}",
                exc_info=True
            )
            raise CalculationError(
                f"Failed to calculate TCO: {str(e)}",
                calculation_type="vehicle_tco"
            ) from e
    
    def compare_vehicles(
        self,
        bev_request: CalculationRequest,
        diesel_request: CalculationRequest
    ) -> Dict[str, Any]:
        """Compare TCO between BEV and diesel vehicles.
        
        Args:
            bev_request: Calculation request for BEV
            diesel_request: Calculation request for diesel
            
        Returns:
            Comparison metrics and results
        """
        bev_result = self.calculate_vehicle_tco(bev_request)
        diesel_result = self.calculate_vehicle_tco(diesel_request)
        
        comparison = {
            'bev_result': bev_result,
            'diesel_result': diesel_result,
            'metrics': self._calculate_comparison_metrics(
                bev_result, diesel_result
            )
        }
        
        return comparison
    
    def _calculate_energy_costs(
        self, request: CalculationRequest
    ) -> float:
        """Calculate energy-related costs."""
        # Delegate to domain module
        return energy.calculate_energy_costs(
            request.vehicle_data,
            request.fees_data,
            request.charging_options,
            request.financial_params,
            request.scenario_params.get('selected_charging'),
            request.charging_mix
        )
    
    def _calculate_annual_costs(
        self, request: CalculationRequest, energy_cost_per_km: float
    ) -> Dict[str, float]:
        """Calculate annual operating costs."""
        return finance.calculate_annual_costs(
            request.vehicle_data,
            request.fees_data,
            energy_cost_per_km,
            request.annual_kms,
            request.incentives,
            request.apply_incentives
        )
    
    def _calculate_acquisition_costs(
        self, request: CalculationRequest
    ) -> float:
        """Calculate acquisition costs."""
        return finance.calculate_acquisition_cost(
            request.vehicle_data,
            request.fees_data,
            request.incentives,
            request.apply_incentives
        )
    
    def _calculate_residual_value(
        self, request: CalculationRequest, acquisition_cost: float
    ) -> float:
        """Calculate residual value."""
        discount_rate = request.discount_rate
        truck_life_years = request.truck_life_years
        
        return finance.calculate_residual_value(
            acquisition_cost,
            truck_life_years,
            discount_rate,
            request.financial_params
        )
    
    def _calculate_battery_costs(
        self, request: CalculationRequest
    ) -> float:
        """Calculate battery replacement costs."""
        from tco_app.src.constants import Drivetrain
        
        if request.vehicle_data.get(DataColumns.VEHICLE_DRIVETRAIN) != Drivetrain.BEV:
            return 0.0
        
        # Use battery domain module if it has calculate_battery_cost function
        # For now, return 0 as the battery module appears to be minimal
        return 0.0
    
    def _calculate_infrastructure_costs(
        self, request: CalculationRequest
    ) -> Optional[Dict[str, float]]:
        """Calculate infrastructure costs."""
        if request.infrastructure_options is None:
            return None
        
        return finance.calculate_infrastructure_costs(
            request.infrastructure_options,
            request.truck_life_years,
            request.discount_rate,
            request.fleet_size
        )
    
    def _calculate_externalities(
        self, request: CalculationRequest
    ) -> Dict[str, float]:
        """Calculate externality costs."""
        # Get carbon price from financial parameters
        try:
            carbon_price = safe_get_parameter(
                request.financial_params,
                ParameterKeys.CARBON_PRICE
            )
        except Exception:
            carbon_price = 0.0
        
        # Calculate emissions
        emissions_result = energy.calculate_emissions(
            request.vehicle_data,
            request.emission_factors,
            request.annual_kms,
            request.truck_life_years
        )
        
        # Calculate carbon cost
        carbon_cost_annual = emissions_result['annual_emissions'] * carbon_price / 1000  # Convert to tonnes
        carbon_cost_lifetime = emissions_result['lifetime_emissions'] * carbon_price / 1000
        
        return {
            'carbon_cost_annual': carbon_cost_annual,
            'carbon_cost_lifetime': carbon_cost_lifetime,
            'carbon_price_per_tonne': carbon_price
        }
    
    def _calculate_comparison_metrics(
        self,
        bev_result: CalculationResult,
        diesel_result: CalculationResult
    ) -> Dict[str, float]:
        """Calculate comparison metrics between vehicles."""
        return {
            'tco_difference': bev_result.tco_lifetime - diesel_result.tco_lifetime,
            'tco_ratio': bev_result.tco_lifetime / diesel_result.tco_lifetime if diesel_result.tco_lifetime != 0 else 0,
            'emissions_savings': (
                diesel_result.emissions_lifetime - bev_result.emissions_lifetime
            ),
            'operating_cost_savings': (
                diesel_result.annual_operating_cost - 
                bev_result.annual_operating_cost
            ),
            'acquisition_cost_difference': (
                bev_result.acquisition_cost - diesel_result.acquisition_cost
            )
        } 