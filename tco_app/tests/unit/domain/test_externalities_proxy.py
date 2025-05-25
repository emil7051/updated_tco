import math

from tco_app.domain.externalities import _compute_co2_proxy
from tco_app.src import pd
from tco_app.src.constants import DataColumns, Drivetrain


class TestComputeCO2Proxy:
    def test_with_matching_fuel_type(self):
        """When emission factors contain the vehicle fuel type, use that value."""
        vehicle = pd.Series(
            {
                DataColumns.VEHICLE_DRIVETRAIN: Drivetrain.DIESEL,
                DataColumns.LITRES_PER100KM: 30,
            }
        )
        emission_factors = pd.DataFrame(
            {"fuel_type": ["diesel"], "co2_per_unit": [2.5]}
        )

        total, breakdown = _compute_co2_proxy(vehicle, emission_factors, 10000, 5, 0.0)

        expected_per_km = (30 / 100) * 2.5 / 1000 * 100
        assert math.isclose(total, expected_per_km)
        assert breakdown == {
            "CO2e": {
                "cost_per_km": expected_per_km,
                "annual_cost": expected_per_km * 10000,
                "lifetime_cost": expected_per_km * 10000 * 5,
                "npv_cost": expected_per_km * 10000 * 5,
            }
        }

    def test_fallback_to_mean_when_missing_fuel_type(self):
        """Fallback to mean emission factor if specific fuel type is absent."""
        vehicle = pd.Series(
            {
                DataColumns.VEHICLE_DRIVETRAIN: Drivetrain.BEV,
                DataColumns.KWH_PER100KM: 20,
            }
        )
        emission_factors = pd.DataFrame(
            {
                "fuel_type": ["diesel", "hydrogen"],
                "co2_per_unit": [2.0, 1.0],
            }
        )

        total, breakdown = _compute_co2_proxy(vehicle, emission_factors, 10000, 5, 0.0)

        mean_factor = (2.0 + 1.0) / 2
        expected_per_km = (20 / 100) * mean_factor / 1000 * 100
        assert math.isclose(total, expected_per_km)
        assert breakdown["CO2e"]["cost_per_km"] == expected_per_km
        assert breakdown["CO2e"]["annual_cost"] == expected_per_km * 10000
        assert breakdown["CO2e"]["lifetime_cost"] == expected_per_km * 10000 * 5
        assert breakdown["CO2e"]["npv_cost"] == expected_per_km * 10000 * 5
