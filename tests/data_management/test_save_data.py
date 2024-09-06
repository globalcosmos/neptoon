import pandas as pd
from neptoon.data_management.save_data import SaveAndArchiveOutputs
from neptoon.data_management.site_information import SiteInformation
from neptoon.data_management.data_audit import DataAuditLog, log_key_step


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


def sample_flags_data():
    return pd.DataFrame(
        {
            "date_time": pd.date_range(
                start="2023-01-01", periods=5, freq="h"
            ),
            "epithermal_neutrons_raw": [
                "UNFLAGGED",
                "UNFLAGGED",
                "BAD",
                "UNFLAGGED",
                "UNFLAGGED",
            ],
            "epithermal_neutrons_cph": [
                "UNFLAGGED",
                "BAD",
                "UNFLAGGED",
                "UNFLAGGED",
                "UNFLAGGED",
            ],
            "air_pressure": [
                "UNFLAGGED",
                "UNFLAGGED",
                "UNFLAGGED",
                "BAD",
                "UNFLAGGED",
            ],
            "air_relative_humidity": [
                "BAD",
                "UNFLAGGED",
                "UNFLAGGED",
                "UNFLAGGED",
                "UNFLAGGED",
            ],
            "air_temperature": [
                "UNFLAGGED",
                "UNFLAGGED",
                "UNFLAGGED",
                "UNFLAGGED",
                "BAD",
            ],
        }
    ).set_index("date_time")


def sample_site_information():
    site_information = SiteInformation(
        site_name="Test_Site",
        latitude=51.37,
        longitude=12.55,
        elevation=140,
        reference_incoming_neutron_value=150,
        dry_soil_bulk_density=1.4,
        lattice_water=0.01,
        soil_organic_carbon=0,
        n0=700,
        cutoff_rigidity=2.94,
        site_biomass=1,
    )
    return site_information


df = sample_crns_data()
flag_df = sample_flags_data()
site_info = sample_site_information()

DataAuditLog.create()


@log_key_step("f")
def dummyfunc(f=1):
    return f


dummyfunc()


test_saver = SaveAndArchiveOutputs(
    "process_test_site",
    processed_data_frame=df,
    flag_data_frame=flag_df,
    site_information=site_info,
    append_yaml_hash_to_folder_name=True,
)
test_saver.save_outputs()
