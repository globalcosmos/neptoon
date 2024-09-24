import pandas as pd
from neptoon.data_hub.crns_data_hub import CRNSDataHub
from neptoon.column_names.column_information import ColumnInfo
from neptoon.site_information import SiteInformation
import pytest


@pytest.fixture
def sample_crns_data():
    return pd.DataFrame(
        {
            "date_time": pd.date_range(
                start="2023-01-01", periods=5, freq="h"
            ),
            "epithermal_neutrons_raw": [100, 110, 105, 115, 108],
            "epithermal_neutrons_cph": [100, 110, 105, 115, 108],
            "air_pressure": [1000, 1005, 1002, 998, 1001],
            "air_relative_humidity": [80, 75, 76, 65, 89],
            "air_temperature": [23, 24, 25, 23, 20],
        }
    ).set_index("date_time")


@pytest.fixture
def example_data_hub(sample_crns_data):
    return CRNSDataHub(crns_data_frame=sample_crns_data)


def test_crns_data_hub_initialization(sample_crns_data):
    """
    Assert that the data_hub is initialised correctly
    """
    data_hub = CRNSDataHub(crns_data_frame=sample_crns_data)
    assert isinstance(data_hub, CRNSDataHub)
    assert data_hub.crns_data_frame.equals(sample_crns_data)


@pytest.fixture
def example_site_information():
    site_information = SiteInformation(
        site_name="test",
        latitude=51.37,
        longitude=12.55,
        elevation=140,
        reference_incoming_neutron_value=150,
        dry_soil_bulk_density=1.4,
        lattice_water=0.01,
        soil_organic_carbon=0,
        # mean_pressure=900,
        cutoff_rigidity=2.94,
        site_biomass=1,
        n0=200,
    )
    return site_information


def test_prepare_site_information(example_site_information, example_data_hub):
    data_hub = example_data_hub
    data_hub.update_site_information(
        new_site_information=example_site_information
    )
    data_hub.prepare_static_values()

    assert "dry_soil_bulk_density" in data_hub.crns_data_frame.columns
    assert data_hub.crns_data_frame["dry_soil_bulk_density"].median() == 1.4


@pytest.fixture
def sample_crns_data_corrected():
    return pd.DataFrame(
        {
            "date_time": pd.date_range(
                start="2023-01-01", periods=5, freq="h"
            ),
            str(ColumnInfo.Name.EPI_NEUTRON_COUNT_RAW): [
                100,
                110,
                105,
                115,
                108,
            ],
            str(ColumnInfo.Name.EPI_NEUTRON_COUNT_FINAL): [
                100,
                110,
                105,
                115,
                108,
            ],
            str(ColumnInfo.Name.AIR_PRESSURE): [1000, 1005, 1002, 998, 1001],
            str(ColumnInfo.Name.AIR_RELATIVE_HUMIDITY): [80, 75, 76, 65, 89],
            str(ColumnInfo.Name.AIR_TEMPERATURE): [23, 24, 25, 23, 20],
            str(ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_FINAL): [
                110,
                120,
                130,
                120,
                120,
            ],
            str(ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_LOWER_COUNT): [
                100,
                110,
                120,
                110,
                110,
            ],
            str(ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_UPPER_COUNT): [
                120,
                130,
                140,
                130,
                130,
            ],
        }
    ).set_index("date_time")


@pytest.fixture
def sample_hub_corrected(sample_crns_data_corrected, example_site_information):
    return CRNSDataHub(
        crns_data_frame=sample_crns_data_corrected,
        site_information=example_site_information,
    )


def test_produce_soil_moisture_estimates_default(sample_hub_corrected):
    """
    Check if soil moisture column is added
    """
    sample_hub_corrected.produce_soil_moisture_estimates()

    assert (
        str(ColumnInfo.Name.SOIL_MOISTURE)
        in sample_hub_corrected.crns_data_frame.columns
    )
    print(sample_hub_corrected.crns_data_frame)


def test_produce_soil_moisture_estimates(sample_hub_corrected):
    """
    Test if changes occur when custom values are submitted.
    """
    data_hub = sample_hub_corrected
    data_hub.prepare_static_values()
    data_hub.produce_soil_moisture_estimates()
    first_df_out = data_hub.crns_data_frame[str(ColumnInfo.Name.SOIL_MOISTURE)]

    data_hub2 = sample_hub_corrected
    data_hub2.prepare_static_values()
    data_hub2.produce_soil_moisture_estimates(n0=10, dry_soil_bulk_density=1)
    second_df_out = data_hub2.crns_data_frame[
        str(ColumnInfo.Name.SOIL_MOISTURE)
    ]
    with pytest.raises(AssertionError):
        pd.testing.assert_series_equal(first_df_out, second_df_out)
