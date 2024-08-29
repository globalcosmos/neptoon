from neptoon.convert_to_sm.estimate_sm import NeutronsToSM
from neptoon.data_management.column_information import ColumnInfo
import pytest
import pandas as pd
import numpy as np


@pytest.fixture
def sample_crns_data():
    """
    Create sample data for testing.

    Returns
    -------
    pd.DataFrame
        Sample CRNS data.
    """
    np.random.seed(42)
    data = {
        str(ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT): np.random.randint(
            500, 1500, 100
        ),
        str(
            ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_FINAL
        ): np.random.randint(500, 1500, 100),
    }
    return pd.DataFrame(data)


@pytest.fixture
def neutrons_to_sm_instance(sample_crns_data):
    """
    Create an instance of NeutronsToSM for testing.

    Parameters
    ----------
    sample_crns_data : pd.DataFrame
        Sample CRNS data.

    Returns
    -------
    NeutronsToSM
        An instance of NeutronsToSM with sample data.
    """
    return NeutronsToSM(
        crns_data_frame=sample_crns_data,
        n0=1000,
        dry_soil_bulk_density=1.4,
        lattice_water=0.05,
        soil_organic_carbon=0.02,
    )


def test_initialization(neutrons_to_sm_instance):
    """Test the initialization of NeutronsToSM instance."""
    assert neutrons_to_sm_instance.n0 == 1000
    assert neutrons_to_sm_instance.dry_soil_bulk_density == 1.4
    assert neutrons_to_sm_instance.lattice_water == 0.05
    assert neutrons_to_sm_instance.soil_organic_carbon == 0.02
    assert isinstance(neutrons_to_sm_instance.crns_data_frame, pd.DataFrame)


def test_property_getters(neutrons_to_sm_instance):
    """Test the property getters of NeutronsToSM instance."""
    assert neutrons_to_sm_instance.corrected_neutrons_col_name == str(
        ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT
    )
    assert neutrons_to_sm_instance.soil_moisture_col_name == str(
        ColumnInfo.Name.SOIL_MOISTURE
    )
    assert neutrons_to_sm_instance.depth_column_name == str(
        ColumnInfo.Name.SOIL_MOISTURE_MEASURMENT_DEPTH
    )
    assert neutrons_to_sm_instance.smoothed_neutrons_col_name == str(
        ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_FINAL
    )


def test_convert_soc_to_wsom():
    """Test the static method _convert_soc_to_wsom."""
    assert NeutronsToSM._convert_soc_to_wsom(0.1) == pytest.approx(0.0556)
    assert NeutronsToSM._convert_soc_to_wsom(0) == 0


def test_calculate_sm_estimates(neutrons_to_sm_instance):
    """Test the calculate_sm_estimates method."""
    neutrons_to_sm_instance.calculate_sm_estimates()
    assert (
        str(ColumnInfo.Name.SOIL_MOISTURE)
        in neutrons_to_sm_instance.crns_data_frame.columns
    )


def test_process_data(neutrons_to_sm_instance):
    """Test the process_data method."""
    neutrons_to_sm_instance.process_data()
    assert (
        str(ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_FINAL)
        in neutrons_to_sm_instance.crns_data_frame.columns
    )
    assert (
        str(ColumnInfo.Name.SOIL_MOISTURE)
        in neutrons_to_sm_instance.crns_data_frame.columns
    )
    assert (
        str(ColumnInfo.Name.SOIL_MOISTURE_MEASURMENT_DEPTH)
        in neutrons_to_sm_instance.crns_data_frame.columns
    )
