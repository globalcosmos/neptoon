import pandas as pd
from neptoon.hub import CRNSDataHub
from neptoon.columns import ColumnInfo
from neptoon.config.configuration_input import SensorInfo
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
def example_sensor_information():
    site_information = SensorInfo(
        name="test",
        country="DEU",
        identifier="101",
        latitude=51.37,
        longitude=12.55,
        elevation=140,
        time_zone=1,
        install_date=pd.to_datetime("14/03/2015", dayfirst=True),
        reference_incoming_neutron_value=150,
        avg_dry_soil_bulk_density=1.4,
        avg_lattice_water=0.01,
        avg_soil_organic_carbon=0,
        # mean_pressure=900,
        site_cutoff_rigidity=2.94,
        site_biomass=1,
        n0=200,
    )
    return site_information


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
            str(ColumnInfo.Name.ABSOLUTE_HUMIDITY): [10, 15, 15, 20, 10],
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
def sample_hub_corrected(
    sample_crns_data_corrected, example_sensor_information
):
    return CRNSDataHub(
        crns_data_frame=sample_crns_data_corrected,
        sensor_info=example_sensor_information,
    )


def test_produce_soil_moisture_estimates_default(sample_hub_corrected):
    """
    Check if soil moisture column is added
    """
    sample_hub_corrected.produce_soil_moisture_estimates(
        n0=2000,
        dry_soil_bulk_density=1.4,
        lattice_water=0.01,
        soil_organic_carbon=0.01,
    )

    assert (
        str(ColumnInfo.Name.SOIL_MOISTURE_VOL)
        in sample_hub_corrected.crns_data_frame.columns
    )
    print(sample_hub_corrected.crns_data_frame)
