import pandas as pd
from neptoon.data_management.crns_data_hub import CRNSDataHub
from neptoon.data_management.site_information import SiteInformation
import pytest


@pytest.fixture
def sample_crns_data():
    return pd.DataFrame(
        {
            "date_time": pd.date_range(
                start="2023-01-01", periods=5, freq="h"
            ),
            "epithermal_neutrons": [100, 110, 105, 115, 108],
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
    )
    return site_information


def test_prepare_site_information(example_site_information, example_data_hub):
    data_hub = example_data_hub
    data_hub.update_site_information(
        new_site_information=example_site_information
    )
    data_hub.prepare_static_values()

    assert "bulk_density" in data_hub.crns_data_frame.columns
    assert data_hub.crns_data_frame["bulk_density"].median() == 1.4
