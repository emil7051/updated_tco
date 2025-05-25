from unittest.mock import Mock

import pytest

from tco_app.repositories import ParametersRepository, VehicleRepository
from tco_app.services.dtos import CalculationParameters, CalculationRequest
from tco_app.services.tco_calculation_service import TCOCalculationService
from tco_app.src import pd
from tco_app.src.constants import DataColumns


class TestTCOMetrics:
    """Unit tests for _calculate_tco_metrics in TCOCalculationService."""

    @pytest.fixture
    def service(self):
        return TCOCalculationService(
            Mock(spec=VehicleRepository), Mock(spec=ParametersRepository)
        )

    def _minimal_request(
        self, annual_kms: int, truck_life_years: int, payload: float = 5.0
    ):
        params = CalculationParameters(
            annual_kms=annual_kms,
            truck_life_years=truck_life_years,
            discount_rate=0.07,
            selected_charging_profile_id=1,
            selected_infrastructure_id=1,
        )
        vehicle = pd.Series({DataColumns.PAYLOAD_T: payload})
        empty_series = pd.Series(dtype=float)
        empty_df = pd.DataFrame()
        return CalculationRequest(
            vehicle_data=vehicle,
            fees_data=empty_series,
            parameters=params,
            charging_options=empty_df,
            infrastructure_options=empty_df,
            financial_params=empty_df,
            battery_params=empty_df,
            emission_factors=empty_df,
            externalities_data=empty_df,
            incentives=empty_df,
        )

    def test_metrics_non_zero(self, service):
        """Ensure per-km and per-tonne-km metrics are calculated correctly."""
        request = self._minimal_request(
            annual_kms=100000, truck_life_years=10, payload=5
        )
        tco_per_km, tco_per_tonne_km = service._calculate_tco_metrics(
            1_000_000, request
        )

        assert pytest.approx(tco_per_km) == 1_000_000 / (100000 * 10)
        assert pytest.approx(tco_per_tonne_km) == (1_000_000 / (100000 * 10)) / 5

    @pytest.mark.parametrize("annual_kms, truck_life_years", [(0, 10), (100000, 0)])
    def test_metrics_zero_inputs(self, service, annual_kms, truck_life_years):
        """If annual_kms or truck_life_years are zero, metrics should be zero."""
        request = self._minimal_request(
            annual_kms=annual_kms, truck_life_years=truck_life_years, payload=5
        )
        tco_per_km, tco_per_tonne_km = service._calculate_tco_metrics(
            1_000_000, request
        )

        assert tco_per_km == 0
        assert tco_per_tonne_km == 0
