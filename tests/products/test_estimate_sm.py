from neptoon.products.estimate_sm import NeutronsToSM
from neptoon.columns import ColumnInfo
from neptoon.corrections.theory.neutrons_to_soil_moisture import (
    neutrons_to_total_grav_soil_moisture_koehli_etal_2021,
)
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
        str(ColumnInfo.Name.EPI_NEUTRON_COUNT_RAW): np.random.randint(
            500, 1500, 100
        ),
        str(ColumnInfo.Name.EPI_NEUTRON_COUNT_CPH): np.random.randint(
            500, 1500, 100
        ),
        str(ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT): np.random.randint(
            500, 1500, 100
        ),
        str(
            ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_FINAL
        ): np.random.randint(500, 1500, 100),
        str(ColumnInfo.Name.AIR_TEMPERATURE): np.random.randint(10, 15, 100),
        str(ColumnInfo.Name.AIR_RELATIVE_HUMIDITY): np.random.randint(
            50, 60, 100
        ),
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
    assert neutrons_to_sm_instance.soil_moisture_vol_col_name == str(
        ColumnInfo.Name.SOIL_MOISTURE_VOL
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
    neutrons_to_sm_instance.calculate_sm_estimates(
        neutron_data_column_name=str(
            ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_FINAL
        ),
        soil_moisture_column_write_name_vol=str(
            ColumnInfo.Name.SOIL_MOISTURE_VOL
        ),
    )
    assert (
        str(ColumnInfo.Name.SOIL_MOISTURE_VOL)
        in neutrons_to_sm_instance.crns_data_frame.columns
    )


####### TEST KOEHLI


@pytest.fixture
def neutrons_to_sm_instance_koehli_no_hum(sample_crns_data):
    """
    Create an instance of NeutronsToSM for testing when using Koehli
    method

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
        conversion_theory="koehli_etal_2021",
    )


@pytest.fixture
def neutrons_to_sm_instance_koehli_with_hum(sample_crns_data):
    """
    Create an instance of NeutronsToSM for testing when using Koehli
    method

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
        conversion_theory="koehli_etal_2021",
    )


def test_koehli_method_nans_not_processed():
    """
    Tests if the koehli method will process a nan value
    """
    nan_neut = neutrons_to_total_grav_soil_moisture_koehli_etal_2021(
        neutron_count=np.nan, n0=2000, air_humidity=8
    )
    nan_hum = neutrons_to_total_grav_soil_moisture_koehli_etal_2021(
        neutron_count=1000, n0=2000, air_humidity=np.nan
    )

    assert pd.isna(nan_neut)
    assert pd.isna(nan_hum)


def test_koehli_method_no_abs_hum(
    neutrons_to_sm_instance_koehli_no_hum,
):
    """
    Test koehli method when abs hum and hum data missing
    """
    neutrons_to_sm_instance_koehli_no_hum.calculate_sm_estimates(
        neutron_data_column_name=str(
            ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_FINAL
        ),
        soil_moisture_column_write_name_vol=str(
            ColumnInfo.Name.SOIL_MOISTURE_VOL
        ),
    )
    assert (
        str(ColumnInfo.Name.ABSOLUTE_HUMIDITY)
        in neutrons_to_sm_instance_koehli_no_hum.crns_data_frame.columns
    )
    assert (
        str(ColumnInfo.Name.SOIL_MOISTURE_VOL)
        in neutrons_to_sm_instance_koehli_no_hum.crns_data_frame.columns
    )


def test_koehli_method_no_abs_hum_missingdata(
    neutrons_to_sm_instance_koehli_no_hum,
):
    """
    Test koehli method when abs hum and hum data missing
    """
    with pytest.raises(KeyError):
        neutrons_to_sm_instance_koehli_no_hum.crns_data_frame.drop(
            str(ColumnInfo.Name.AIR_RELATIVE_HUMIDITY)
        )

        neutrons_to_sm_instance_koehli_no_hum.calculate_sm_estimates(
            neutron_data_column_name=str(
                ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_FINAL
            ),
            soil_moisture_column_write_name=str(
                ColumnInfo.Name.SOIL_MOISTURE_VOL
            ),
        )
