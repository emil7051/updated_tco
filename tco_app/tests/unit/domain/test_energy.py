import pytest
from tco_app.src import pd, CALC_DEFAULTS
from tco_app.domain.energy import calculate_charging_requirements
from tco_app.src.constants import DataColumns, Drivetrain


@pytest.mark.parametrize(
    "drivetrain,desc,expected_power",
    [
        (Drivetrain.BEV, "Depot charger 80 kW", 80.0),
        (Drivetrain.BEV, "Fast charger high kW", CALC_DEFAULTS.DEFAULT_CHARGER_POWER_KW),
        (Drivetrain.DIESEL, None, 0.0),
    ],
)
def test_calculate_charging_requirements(drivetrain, desc, expected_power):
    annual_kms = 36500
    vehicle = pd.Series({DataColumns.VEHICLE_DRIVETRAIN: drivetrain, DataColumns.KWH_PER100KM: 20})
    infra = None
    if desc is not None:
        infra = pd.Series({DataColumns.INFRASTRUCTURE_DESCRIPTION: desc})

    result = calculate_charging_requirements(vehicle, annual_kms, infra)

    if drivetrain == Drivetrain.BEV:
        daily_distance = annual_kms / CALC_DEFAULTS.DAYS_PER_YEAR
        daily_kwh_required = daily_distance * 20 / 100
        expected_time = daily_kwh_required / expected_power if expected_power else 0
        expected_max = 24 / expected_time if expected_time else 0

        assert set(result.keys()) == {
            "daily_distance",
            "daily_kwh_required",
            "charger_power",
            "charging_time_per_day",
            "max_vehicles_per_charger",
        }
        assert result["daily_distance"] == pytest.approx(daily_distance)
        assert result["daily_kwh_required"] == pytest.approx(daily_kwh_required)
        assert result["charger_power"] == pytest.approx(expected_power)
        assert result["charging_time_per_day"] == pytest.approx(expected_time)
        assert result["max_vehicles_per_charger"] == pytest.approx(expected_max)
    else:
        assert result == {
            "daily_distance": 0,
            "daily_kwh_required": 0,
            "charger_power": 0,
            "charging_time_per_day": 0,
            "max_vehicles_per_charger": 0,
        }
