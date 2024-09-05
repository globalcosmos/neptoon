import pytest
import pandas as pd
from neptoon.data_management.save_data import SaveAndArchiveOutputs


# @pytest.fixture
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


df = sample_crns_data()

test_saver = SaveAndArchiveOutputs(
    "test_folder",
    processed_data_frame=df,
    flag_data_frame=df,
    site_information=None,
)

print(test_saver.save_folder_location)
