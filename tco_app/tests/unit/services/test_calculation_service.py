"""Tests for the CalculationService."""
import pytest
import pandas as pd
from unittest.mock import Mock, patch
from dataclasses import asdict

from tco_app.services.calculation_service import (
    CalculationService, CalculationRequest, CalculationResult
)
from tco_app.src.constants import DataColumns, Drivetrain
from tco_app.src.exceptions import CalculationError


class TestCalculationService:
    """Test cases for CalculationService."""
    
    @pytest.fixture
    def service(self):
        """Create a CalculationService instance."""
        return CalculationService()
    
    @pytest.fixture
    def sample_request(self):
        """Create a sample calculation request."""
        vehicle_data = {
            DataColumns.VEHICLE_ID: 'TEST_BEV',
            DataColumns.VEHICLE_DRIVETRAIN: Drivetrain.BEV,
            DataColumns.PAYLOAD_T: 10.0,
            DataColumns.KWH_PER100KM: 100.0,
            DataColumns.BATTERY_CAPACITY_KWH: 200.0
        }
        
        financial_params = pd.DataFrame([
            {'finance_description': 'discount_rate_percent', 'default_value': 0.07},
            {'finance_description': 'carbon_price', 'default_value': 50.0}
        ])
        
        emission_factors = pd.DataFrame([
            {'fuel_type': 'electricity', 'emission_standard': 'Grid', 'co2_per_unit': 0.5}
        ])
        
        return CalculationRequest(
            vehicle_data=vehicle_data,
            fees_data=pd.DataFrame(),
            scenario_params={'scenario_name': 'Test Scenario'},
            charging_options=pd.DataFrame(),
            infrastructure_options=None,
            financial_params=financial_params,
            battery_params=pd.DataFrame(),
            emission_factors=emission_factors,
            incentives=pd.DataFrame(),
            annual_kms=50000,
            truck_life_years=10,
            discount_rate=0.07
        )
    
    @patch('tco_app.services.calculation_service.energy')
    @patch('tco_app.services.calculation_service.finance')
    def test_calculate_vehicle_tco_basic(self, mock_finance, mock_energy, service, sample_request):
        """Test basic TCO calculation."""
        # Mock domain module responses
        mock_energy.calculate_energy_costs.return_value = 0.25
        mock_energy.calculate_emissions.return_value = {
            'co2_per_km': 0.05,
            'annual_emissions': 2500,
            'lifetime_emissions': 25000
        }
        
        mock_finance.calculate_annual_costs.return_value = {
            'annual_operating_cost': 15000,
            'annual_maintenance_cost': 5000
        }
        mock_finance.calculate_acquisition_cost.return_value = 100000
        mock_finance.calculate_residual_value.return_value = 20000
        mock_finance.calculate_npv.return_value = 120000
        mock_finance.calculate_tco.return_value = {
            'tco_lifetime': 200000,
            'tco_per_km': 0.40,
            'tco_per_tonne_km': 0.04
        }
        
        # Execute calculation
        result = service.calculate_vehicle_tco(sample_request)
        
        # Verify result structure
        assert isinstance(result, CalculationResult)
        assert result.vehicle_id == 'TEST_BEV'
        assert result.tco_lifetime == 200000
        assert result.tco_per_km == 0.40
        assert result.scenario_name == 'Test Scenario'
        assert 'energy_cost_per_km' in result.energy_costs
        
        # Verify domain module calls
        mock_energy.calculate_energy_costs.assert_called_once()
        mock_finance.calculate_annual_costs.assert_called_once()
        mock_finance.calculate_acquisition_cost.assert_called_once()
    
    @patch('tco_app.services.calculation_service.energy')
    def test_calculate_energy_costs_error_handling(self, mock_energy, service, sample_request):
        """Test error handling in TCO calculation."""
        # Mock an error in energy calculation
        mock_energy.calculate_energy_costs.side_effect = Exception("Energy calculation failed")
        
        # Verify exception is properly wrapped
        with pytest.raises(CalculationError) as exc_info:
            service.calculate_vehicle_tco(sample_request)
        
        assert "Failed to calculate TCO" in str(exc_info.value)
        assert exc_info.value.calculation_type == "vehicle_tco"
    
    @patch('tco_app.services.calculation_service.energy')
    @patch('tco_app.services.calculation_service.finance')
    def test_compare_vehicles(self, mock_finance, mock_energy, service, sample_request):
        """Test vehicle comparison functionality."""
        # Create a diesel request
        diesel_request = CalculationRequest(
            vehicle_data={
                DataColumns.VEHICLE_ID: 'TEST_DIESEL',
                DataColumns.VEHICLE_DRIVETRAIN: Drivetrain.DIESEL,
                DataColumns.PAYLOAD_T: 10.0
            },
            fees_data=pd.DataFrame(),
            scenario_params={'scenario_name': 'Test Scenario'},
            charging_options=pd.DataFrame(),
            infrastructure_options=None,
            financial_params=sample_request.financial_params,
            battery_params=pd.DataFrame(),
            emission_factors=sample_request.emission_factors,
            incentives=pd.DataFrame(),
            annual_kms=50000,
            truck_life_years=10,
            discount_rate=0.07
        )
        
        # Mock responses
        mock_energy.calculate_energy_costs.return_value = 0.25
        mock_energy.calculate_emissions.return_value = {
            'co2_per_km': 0.05,
            'annual_emissions': 2500,
            'lifetime_emissions': 25000
        }
        
        mock_finance.calculate_annual_costs.return_value = {
            'annual_operating_cost': 15000,
            'annual_maintenance_cost': 5000
        }
        mock_finance.calculate_acquisition_cost.return_value = 100000
        mock_finance.calculate_residual_value.return_value = 20000
        mock_finance.calculate_npv.return_value = 120000
        mock_finance.calculate_tco.return_value = {
            'tco_lifetime': 200000,
            'tco_per_km': 0.40,
            'tco_per_tonne_km': 0.04
        }
        
        # Execute comparison
        comparison = service.compare_vehicles(sample_request, diesel_request)
        
        # Verify result structure
        assert 'bev_result' in comparison
        assert 'diesel_result' in comparison
        assert 'metrics' in comparison
        
        metrics = comparison['metrics']
        assert 'tco_difference' in metrics
        assert 'tco_ratio' in metrics
        assert 'emissions_savings' in metrics
    
    def test_calculation_request_dataclass(self):
        """Test CalculationRequest dataclass functionality."""
        request = CalculationRequest(
            vehicle_data={'test': 'data'},
            fees_data=pd.DataFrame(),
            scenario_params={},
            charging_options=pd.DataFrame(),
            infrastructure_options=None,
            financial_params=pd.DataFrame(),
            battery_params=pd.DataFrame(),
            emission_factors=pd.DataFrame(),
            incentives=pd.DataFrame(),
            annual_kms=50000,
            truck_life_years=10,
            discount_rate=0.07
        )
        
        # Test default values
        assert request.fleet_size == 1
        assert request.apply_incentives is True
        assert request.charging_mix is None
        
        # Test that it can be converted to dict
        request_dict = asdict(request)
        assert 'vehicle_data' in request_dict
        assert 'annual_kms' in request_dict
    
    def test_calculation_result_dataclass(self):
        """Test CalculationResult dataclass functionality."""
        result = CalculationResult(
            vehicle_id='TEST',
            tco_lifetime=100000.0,
            tco_per_km=0.50,
            tco_per_tonne_km=0.05,
            annual_operating_cost=10000.0,
            acquisition_cost=80000.0,
            residual_value=15000.0,
            emissions_lifetime=50000.0,
            emissions_per_km=0.1,
            energy_costs={'test': 1.0},
            maintenance_costs={'test': 2.0},
            infrastructure_costs={'test': 3.0},
            externality_costs={'test': 4.0},
            calculation_timestamp='2024-01-01T00:00:00',
            scenario_name='Test'
        )
        
        # Test that it can be converted to dict
        result_dict = asdict(result)
        assert 'vehicle_id' in result_dict
        assert 'tco_lifetime' in result_dict
        assert result_dict['vehicle_id'] == 'TEST' 