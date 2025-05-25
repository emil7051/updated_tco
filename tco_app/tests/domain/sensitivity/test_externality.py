import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

from tco_app.domain.sensitivity.externality import perform_externality_sensitivity

# Assuming DataColumns might be needed for DataFrame keys if not using raw strings
# from tco_app.src.constants import DataColumns


@pytest.fixture
def mock_bev_vehicle_data():
    # vehicle_class might be used by the actual calculate_externalities,
    # but our mock below simplifies this.
    return pd.Series({"vehicle_id": 1, "drivetrain": "BEV", "vehicle_class": "Rigid"})


@pytest.fixture
def mock_diesel_vehicle_data():
    return pd.Series(
        {"vehicle_id": 2, "drivetrain": "Diesel", "vehicle_class": "Articulated"}
    )


@pytest.fixture
def mock_bev_results(mock_bev_vehicle_data):
    return {
        "vehicle_data": mock_bev_vehicle_data,
        "tco": {"tco_per_km": 1.0, "tco_lifetime": 100000},
        "emissions": {"lifetime_emissions": 5000},  # kg
    }


@pytest.fixture
def mock_diesel_results(mock_diesel_vehicle_data):
    return {
        "vehicle_data": mock_diesel_vehicle_data,
        "tco": {"tco_per_km": 0.8, "tco_lifetime": 80000},
        "emissions": {"lifetime_emissions": 20000},  # kg
    }


@pytest.fixture
def mock_externalities_data():
    # Using a single row as our mock for calculate_externalities will simplify
    # and focus on the modification of this cost_per_km value.
    return pd.DataFrame(
        {
            "vehicle_class": ["Rigid"],
            "pollutant_type": ["externalities_total"],
            "cost_per_km": [0.1],
        }
    )


def test_perform_externality_sensitivity_default_range(
    mock_bev_results, mock_diesel_results, mock_externalities_data
):
    annual_kms = 20000
    truck_life_years = 10
    discount_rate = 0.05

    with patch(
        "tco_app.domain.sensitivity.externality.calculate_externalities"
    ) as mock_calc_ext, patch(
        "tco_app.domain.sensitivity.externality.calculate_social_tco"
    ) as mock_calc_social_tco:

        def side_effect_calc_ext(
            vehicle_data, modified_ext_df, an_kms, tr_life, disc_rate
        ):
            # Mock uses the first (and only) cost_per_km from the modified data
            base_cost_per_km = modified_ext_df["cost_per_km"].iloc[0]
            # Simplified total externalities for mock
            total_ext = base_cost_per_km * an_kms * tr_life
            if vehicle_data["drivetrain"] == "BEV":
                # BEV externalities are 50% of the modified base
                val = base_cost_per_km * 0.5
                return {
                    "externality_per_km": val,
                    "total_externalities": total_ext * 0.5,
                }
            else:  # Diesel
                # Diesel externalities are 100% of the modified base
                val = base_cost_per_km * 1.0
                return {
                    "externality_per_km": val,
                    "total_externalities": total_ext * 1.0,
                }

        def side_effect_calc_social_tco(tco_results, ext_results):
            return {
                "social_tco_per_km": tco_results["tco_per_km"]
                + ext_results["externality_per_km"],
                "social_tco_lifetime": tco_results["tco_lifetime"]
                + ext_results["total_externalities"],
            }

        mock_calc_ext.side_effect = side_effect_calc_ext
        mock_calc_social_tco.side_effect = side_effect_calc_social_tco

        results = perform_externality_sensitivity(
            bev_results=mock_bev_results,
            diesel_results=mock_diesel_results,
            externalities_data=mock_externalities_data,
            annual_kms=annual_kms,
            truck_life_years=truck_life_years,
            discount_rate=discount_rate,
        )

        assert len(results) == 4  # Default range: [-50, 0, 50, 100]
        expected_pct_changes = [-50, 0, 50, 100]
        original_ext_cost_per_km = mock_externalities_data["cost_per_km"].iloc[0]

        for i, res_item in enumerate(results):
            pct = expected_pct_changes[i]
            assert res_item["percent_change"] == pct

            modified_input_cost = original_ext_cost_per_km * (1 + pct / 100)

            expected_bev_ext_per_km = modified_input_cost * 0.5
            expected_diesel_ext_per_km = modified_input_cost * 1.0

            assert res_item["bev_externality_per_km"] == pytest.approx(
                expected_bev_ext_per_km
            )
            assert res_item["diesel_externality_per_km"] == pytest.approx(
                expected_diesel_ext_per_km
            )

            assert res_item["bev_tco_per_km"] == mock_bev_results["tco"]["tco_per_km"]
            assert (
                res_item["diesel_tco_per_km"]
                == mock_diesel_results["tco"]["tco_per_km"]
            )

            expected_bev_social_tco_per_km = (
                mock_bev_results["tco"]["tco_per_km"] + expected_bev_ext_per_km
            )
            expected_diesel_social_tco_per_km = (
                mock_diesel_results["tco"]["tco_per_km"] + expected_diesel_ext_per_km
            )
            assert res_item["bev_social_tco_per_km"] == pytest.approx(
                expected_bev_social_tco_per_km
            )
            assert res_item["diesel_social_tco_per_km"] == pytest.approx(
                expected_diesel_social_tco_per_km
            )

            # Simplified total externalities for abatement cost check
            bev_total_ext = (modified_input_cost * 0.5) * annual_kms * truck_life_years
            diesel_total_ext = (
                (modified_input_cost * 1.0) * annual_kms * truck_life_years
            )

            bev_social_lifetime = (
                mock_bev_results["tco"]["tco_lifetime"] + bev_total_ext
            )
            diesel_social_lifetime = (
                mock_diesel_results["tco"]["tco_lifetime"] + diesel_total_ext
            )

            emission_savings = (
                mock_diesel_results["emissions"]["lifetime_emissions"]
                - mock_bev_results["emissions"]["lifetime_emissions"]
            )
            if emission_savings > 0:
                expected_abatement_cost = (
                    bev_social_lifetime - diesel_social_lifetime
                ) / (emission_savings / 1000)
            else:
                expected_abatement_cost = float("inf")
            assert res_item["social_abatement_cost"] == pytest.approx(
                expected_abatement_cost
            )

        assert mock_calc_ext.call_count == 4 * 2
        assert mock_calc_social_tco.call_count == 4 * 2


def test_perform_externality_sensitivity_custom_range(
    mock_bev_results, mock_diesel_results, mock_externalities_data
):
    annual_kms = 20000
    truck_life_years = 10
    discount_rate = 0.05
    custom_range = [-20, 0, 20]

    # Using MagicMock to simplify return values for this specific test focus
    with patch(
        "tco_app.domain.sensitivity.externality.calculate_externalities",
        MagicMock(
            return_value={"externality_per_km": 0.05, "total_externalities": 10000}
        ),
    ) as mock_calc_ext, patch(
        "tco_app.domain.sensitivity.externality.calculate_social_tco",
        MagicMock(
            return_value={"social_tco_per_km": 1.05, "social_tco_lifetime": 110000}
        ),
    ) as mock_calc_social_tco:

        results = perform_externality_sensitivity(
            bev_results=mock_bev_results,
            diesel_results=mock_diesel_results,
            externalities_data=mock_externalities_data,
            annual_kms=annual_kms,
            truck_life_years=truck_life_years,
            discount_rate=discount_rate,
            sensitivity_range=custom_range,
        )
        assert len(results) == len(custom_range)
        for i, res_item in enumerate(results):
            assert res_item["percent_change"] == custom_range[i]

        assert mock_calc_ext.call_count == len(custom_range) * 2
        assert mock_calc_social_tco.call_count == len(custom_range) * 2


def test_perform_externality_sensitivity_zero_emission_savings(
    mock_bev_results, mock_diesel_results, mock_externalities_data
):
    mock_diesel_results_modified = mock_diesel_results.copy()
    # Ensure emission_savings is zero
    mock_diesel_results_modified["emissions"] = mock_bev_results["emissions"].copy()

    with patch(
        "tco_app.domain.sensitivity.externality.calculate_externalities",
        MagicMock(
            return_value={"externality_per_km": 0.05, "total_externalities": 10000}
        ),
    ), patch(
        "tco_app.domain.sensitivity.externality.calculate_social_tco",
        MagicMock(
            return_value={"social_tco_per_km": 1.05, "social_tco_lifetime": 110000}
        ),
    ):
        results = perform_externality_sensitivity(
            bev_results=mock_bev_results,
            diesel_results=mock_diesel_results_modified,
            externalities_data=mock_externalities_data,
            annual_kms=10000,
            truck_life_years=10,
            discount_rate=0.05,
            sensitivity_range=[0],  # Single point for simplicity
        )
        assert len(results) == 1
        assert results[0]["social_abatement_cost"] == float("inf")


def test_perform_externality_sensitivity_negative_emission_savings(
    mock_bev_results, mock_diesel_results, mock_externalities_data
):
    mock_bev_results_modified = mock_bev_results.copy()
    # Ensure emission_savings is negative (BEV emits more)
    mock_bev_results_modified["emissions"] = {
        "lifetime_emissions": mock_diesel_results["emissions"]["lifetime_emissions"]
        + 1000
    }

    with patch(
        "tco_app.domain.sensitivity.externality.calculate_externalities",
        MagicMock(
            return_value={"externality_per_km": 0.05, "total_externalities": 10000}
        ),
    ), patch(
        "tco_app.domain.sensitivity.externality.calculate_social_tco",
        MagicMock(
            return_value={"social_tco_per_km": 1.05, "social_tco_lifetime": 110000}
        ),
    ):
        results = perform_externality_sensitivity(
            bev_results=mock_bev_results_modified,
            diesel_results=mock_diesel_results,
            externalities_data=mock_externalities_data,
            annual_kms=10000,
            truck_life_years=10,
            discount_rate=0.05,
            sensitivity_range=[0],
        )
        assert len(results) == 1
        assert results[0]["social_abatement_cost"] == float("inf")
