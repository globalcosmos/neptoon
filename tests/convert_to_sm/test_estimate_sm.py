from neptoon.convert_to_sm.estimate_sm import NeutronsToSM
import pytest
import pandas as pd
import numpy as np


@pytest.fixture
def sample_crns_data():
    return pd.DataFrame(
        {
            "corrected_epithermal_neutron_count": np.random.randint(
                500, 1500, 100
            ),
            "epithermal_neutrons_smoothed": np.random.randint(500, 1500, 100),
        }
    )


@pytest.fixture
def neutrons_to_sm_instance(sample_crns_data):
    return NeutronsToSM(
        crns_data_frame=sample_crns_data,
        n0=1000,
        dry_soil_bulk_density=1.4,
        lattice_water=0.05,
        soil_organic_carbon=0.02,
    )


def test_initialization(neutrons_to_sm_instance):
    assert neutrons_to_sm_instance.n0 == 1000
    assert neutrons_to_sm_instance.dry_soil_bulk_density == 1.4
    assert neutrons_to_sm_instance.lattice_water == 0.05
    assert neutrons_to_sm_instance.soil_organic_carbon == 0.02
    assert isinstance(neutrons_to_sm_instance.crns_data_frame, pd.DataFrame)


def test_property_getters(neutrons_to_sm_instance):
    assert (
        neutrons_to_sm_instance.corrected_neutrons_col_name
        == "corrected_epithermal_neutron_count"
    )
    assert (
        neutrons_to_sm_instance.soil_moisture_col_name == "soil_moisture_crns"
    )
    assert (
        neutrons_to_sm_instance.depth_column_name == "crns_measurement_depth"
    )
    assert (
        neutrons_to_sm_instance.smoothed_neutrons_col_name
        == "epithermal_neutrons_smoothed"
    )


def test_convert_soc_to_wsom():
    assert NeutronsToSM._convert_soc_to_wsom(0.1) == pytest.approx(0.0556)
    assert NeutronsToSM._convert_soc_to_wsom(0) == 0


def test_smooth_neutron_count(neutrons_to_sm_instance):
    original_data = neutrons_to_sm_instance.crns_data_frame[
        "corrected_epithermal_neutron_count"
    ].copy()
    neutrons_to_sm_instance.smooth_neutron_count(smooth_window=3)
    smoothed_data = neutrons_to_sm_instance.crns_data_frame[
        "epithermal_neutrons_smoothed"
    ]

    assert not smoothed_data.equals(original_data)
    assert (
        smoothed_data.iloc[2:].notna().all()
    )  # First two values should be NaN due to rolling window
    assert len(smoothed_data) == len(original_data)


def test_calculate_sm_estimates(neutrons_to_sm_instance):
    neutrons_to_sm_instance.smooth_neutron_count()
    neutrons_to_sm_instance.calculate_sm_estimates()

    assert (
        "soil_moisture_crns" in neutrons_to_sm_instance.crns_data_frame.columns
    )


def test_process_data(neutrons_to_sm_instance):
    neutrons_to_sm_instance.process_data()

    assert (
        "epithermal_neutrons_smoothed"
        in neutrons_to_sm_instance.crns_data_frame.columns
    )
    assert (
        "soil_moisture_crns" in neutrons_to_sm_instance.crns_data_frame.columns
    )
    assert (
        "crns_measurement_depth"
        in neutrons_to_sm_instance.crns_data_frame.columns
    )
