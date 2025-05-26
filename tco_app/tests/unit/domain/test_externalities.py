import math

from tco_app.domain.externalities import (
    calculate_externalities,
    calculate_social_benefit_metrics,
    calculate_social_tco,
    prepare_externality_comparison,
)
from tco_app.src import pd
from tco_app.src.constants import DataColumns, Drivetrain


class TestExternalitiesDomain:
    def test_calculate_externalities_detailed_table(self):
        vehicle = pd.Series(
            {
                DataColumns.VEHICLE_TYPE: "Rigid",
                DataColumns.VEHICLE_DRIVETRAIN: Drivetrain.BEV,
            }
        )
        ext_df = pd.DataFrame(
            {
                DataColumns.VEHICLE_CLASS.value: ["Rigid", "Rigid", "Rigid"],
                DataColumns.VEHICLE_DRIVETRAIN.value: [Drivetrain.BEV, Drivetrain.BEV, Drivetrain.BEV],
                DataColumns.POLLUTANT_TYPE.value: ["CO2e", "NOx", "externalities_total"],
                DataColumns.COST_PER_KM.value: [0.01, 0.02, 0.05],
            }
        )

        res = calculate_externalities(vehicle, ext_df, 10000, 5, 0.0)

        assert math.isclose(res["externality_per_km"], 0.05)
        assert res["annual_externality_cost"] == 0.05 * 10000
        assert res["lifetime_externality_cost"] == 0.05 * 10000 * 5
        assert res["npv_externality"] == 0.05 * 10000 * 5
        assert set(res["breakdown"].keys()) == {"CO2e", "NOx"}
        assert res["breakdown"]["CO2e"]["annual_cost"] == 0.01 * 10000

    def test_calculate_externalities_fallback_table(self):
        vehicle = pd.Series(
            {
                DataColumns.VEHICLE_DRIVETRAIN: Drivetrain.DIESEL,
                DataColumns.LITRES_PER100KM: 30,
            }
        )
        factors = pd.DataFrame({"fuel_type": ["diesel"], "co2_per_unit": [2.5]})

        res = calculate_externalities(vehicle, factors, 10000, 5, 0.0)

        expected_per_km = (30 / 100) * 2.5 / 1000 * 100
        assert math.isclose(res["externality_per_km"], expected_per_km)
        assert res["breakdown"] == {
            "CO2e": {
                "cost_per_km": expected_per_km,
                "annual_cost": expected_per_km * 10000,
                "lifetime_cost": expected_per_km * 10000 * 5,
                "npv_cost": expected_per_km * 10000 * 5,
            }
        }

    def test_calculate_externalities_fallback_table_bev(self):
        vehicle = pd.Series(
            {
                DataColumns.VEHICLE_DRIVETRAIN: Drivetrain.BEV,
                DataColumns.KWH_PER100KM: 50,
            }
        )
        factors = pd.DataFrame({"fuel_type": ["electricity"], "co2_per_unit": [2.0]})

        res = calculate_externalities(vehicle, factors, 10000, 5, 0.0)

        expected_per_km = 50 * 2.0 / 1000
        assert math.isclose(res["externality_per_km"], expected_per_km)
        assert res["breakdown"] == {
            "CO2e": {
                "cost_per_km": expected_per_km,
                "annual_cost": expected_per_km * 10000,
                "lifetime_cost": expected_per_km * 10000 * 5,
                "npv_cost": expected_per_km * 10000 * 5,
            }
        }

    def test_helper_delegation_detailed(self, monkeypatch):
        vehicle = pd.Series(
            {
                DataColumns.VEHICLE_TYPE: "Rigid",
                DataColumns.VEHICLE_DRIVETRAIN: Drivetrain.BEV,
            }
        )
        ext_df = pd.DataFrame(
            {
                DataColumns.VEHICLE_CLASS.value: ["Rigid"],
                DataColumns.VEHICLE_DRIVETRAIN.value: [Drivetrain.BEV],
                DataColumns.POLLUTANT_TYPE.value: ["CO2e"],
                DataColumns.COST_PER_KM.value: [0.1],
            }
        )

        called = {}

        def fake_detailed(v, d, a, t, r):
            called["detailed"] = True
            return 0.1, {}

        def fake_proxy(*args, **kwargs):
            called["proxy"] = True
            return 0.0, {}

        monkeypatch.setattr(
            "tco_app.domain.externalities._compute_detailed_externalities",
            fake_detailed,
        )
        monkeypatch.setattr(
            "tco_app.domain.externalities._compute_co2_proxy",
            fake_proxy,
        )

        calculate_externalities(vehicle, ext_df, 100, 5, 0.0)

        assert called.get("detailed") is True
        assert called.get("proxy") is None

    def test_helper_delegation_proxy(self, monkeypatch):
        vehicle = pd.Series(
            {
                DataColumns.VEHICLE_DRIVETRAIN: Drivetrain.DIESEL,
                DataColumns.LITRES_PER100KM: 30,
            }
        )
        factors = pd.DataFrame({"fuel_type": ["diesel"], "co2_per_unit": [2.5]})

        called = {}

        def fake_detailed(*args, **kwargs):
            called["detailed"] = True
            return 0.0, {}

        def fake_proxy(v, d, a, t, r):
            called["proxy"] = True
            return 0.1, {}

        monkeypatch.setattr(
            "tco_app.domain.externalities._compute_detailed_externalities",
            fake_detailed,
        )
        monkeypatch.setattr(
            "tco_app.domain.externalities._compute_co2_proxy",
            fake_proxy,
        )

        calculate_externalities(vehicle, factors, 100, 5, 0.0)

        assert called.get("proxy") is True
        assert called.get("detailed") is None

    def test_calculate_social_tco_metrics(self):
        tco_metrics = {
            "npv_total_cost": 100000,
            "annual_kms": 10000,
            "truck_life_years": 5,
            DataColumns.PAYLOAD_T: 10,
        }
        ext_metrics = {"npv_externality": 5000}

        res = calculate_social_tco(tco_metrics, ext_metrics)

        assert res["social_tco_lifetime"] == 105000
        assert math.isclose(res["social_tco_per_km"], 105000 / 50000)
        assert math.isclose(res["social_tco_per_tonne_km"], 105000 / 50000 / 10)
        assert math.isclose(
            res["externality_percentage"],
            (5000 / 105000) * 100,
        )

    def test_prepare_externality_comparison(self):
        bev_ext = {
            "externality_per_km": 0.1,
            "breakdown": {
                "CO2": {"cost_per_km": 0.07},
                "NOx": {"cost_per_km": 0.03},
            },
        }
        diesel_ext = {
            "externality_per_km": 0.2,
            "breakdown": {
                "CO2": {"cost_per_km": 0.15},
                "NOx": {"cost_per_km": 0.05},
            },
        }

        comp = prepare_externality_comparison(bev_ext, diesel_ext)

        assert comp["bev_total"] == 0.1
        assert comp["diesel_total"] == 0.2
        assert comp["total_savings"] == 0.1
        assert comp["total_savings_percent"] == 50.0
        assert len(comp["breakdown"]) == 2
        assert comp["breakdown"][0]["pollutant_type"] == "CO2"
        assert math.isclose(comp["breakdown"][0]["savings_per_km"], 0.08)

    def test_calculate_social_benefit_metrics(self):
        bev_results = {
            "acquisition_cost": 120000,
            "annual_costs": {"annual_operating_cost": 10000},
            "externalities": {"annual_externality_cost": 500},
        }
        diesel_results = {
            "acquisition_cost": 100000,
            "annual_costs": {"annual_operating_cost": 15000},
            "externalities": {"annual_externality_cost": 1500},
        }

        metrics = calculate_social_benefit_metrics(
            bev_results,
            diesel_results,
            annual_kms=10000,
            truck_life_years=5,
            discount_rate=0.0,
        )

        assert metrics["bev_premium"] == 20000
        assert metrics["annual_operating_savings"] == 5000
        assert metrics["annual_externality_savings"] == 1000
        assert metrics["total_annual_benefits"] == 6000
        assert metrics["npv_benefits"] == 6000 * 5
        assert math.isclose(metrics["social_benefit_cost_ratio"], 1.5)
        assert math.isclose(metrics["simple_payback_period"], 20000 / 6000)
        assert math.isclose(metrics["social_payback_period"], 20000 / 6000)
