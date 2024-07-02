import pandas as pd
from neptoon.data_management.crns_data_hub import CRNSDataHub
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
