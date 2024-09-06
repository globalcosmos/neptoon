import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from neptoon.data_management.save_data import SaveAndArchiveOutputs
from neptoon.data_management.site_information import SiteInformation
from neptoon.data_management.data_audit import DataAuditLog, log_key_step


# # @pytest.fixture
# def sample_crns_data():
#     return pd.DataFrame(
#         {
#             "date_time": pd.date_range(
#                 start="2023-01-01", periods=5, freq="h"
#             ),
#             "epithermal_neutrons_raw": [100, 110, 105, 115, 108],
#             "epithermal_neutrons_cph": [100, 110, 105, 115, 108],
#             "air_pressure": [1000, 1005, 1002, 998, 1001],
#             "air_relative_humidity": [80, 75, 76, 65, 89],
#             "air_temperature": [23, 24, 25, 23, 20],
#         }
#     ).set_index("date_time")


UNFLAGGED = "UNFLAGGED"
BAD = "BAD"


@pytest.fixture
def sample_data():
    processed_df = pd.DataFrame(
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
    )
    flag_df = pd.DataFrame(
        {
            "date_time": pd.date_range(
                start="2023-01-01", periods=5, freq="h"
            ),
            "epithermal_neutrons_raw": [
                UNFLAGGED,
                UNFLAGGED,
                UNFLAGGED,
                BAD,
                BAD,
            ],
            "epithermal_neutrons_cph": [
                UNFLAGGED,
                BAD,
                BAD,
                UNFLAGGED,
                UNFLAGGED,
            ],
            "air_pressure": [
                UNFLAGGED,
                UNFLAGGED,
                UNFLAGGED,
                UNFLAGGED,
                UNFLAGGED,
            ],
            "air_relative_humidity": [
                UNFLAGGED,
                UNFLAGGED,
                BAD,
                UNFLAGGED,
                UNFLAGGED,
            ],
            "air_temperature": [
                UNFLAGGED,
                UNFLAGGED,
                UNFLAGGED,
                UNFLAGGED,
                UNFLAGGED,
            ],
        }
    )
    site_info = Mock(spec=SiteInformation)
    site_info.site_name = "TestSite"
    return processed_df, flag_df, site_info


@pytest.fixture
def save_and_archive(sample_data, tmp_path):
    processed_df, flag_df, site_info = sample_data
    return SaveAndArchiveOutputs(
        folder_name="test_folder",
        processed_data_frame=processed_df,
        flag_data_frame=flag_df,
        site_information=site_info,
        save_folder_location=tmp_path,
    )


def test_init(save_and_archive, tmp_path):
    """
    Tests intantiation of SaveAndArchiveOutputs
    """
    assert save_and_archive.folder_name == "test_folder"
    assert save_and_archive.save_folder_location == tmp_path
    assert not save_and_archive.append_yaml_hash_to_folder_name
    assert not save_and_archive.use_custom_column_names
    assert save_and_archive.custom_column_names_dict is None


def test_validate_save_folder(save_and_archive, tmp_path):
    """
    Tests that the folder name validation works as expected.
    """
    assert save_and_archive._validate_save_folder(tmp_path) == tmp_path
    assert save_and_archive._validate_save_folder(str(tmp_path)) == tmp_path
    assert save_and_archive._validate_save_folder(None) == Path.cwd()


def test_create_save_folder(save_and_archive, tmp_path):
    """
    Tests that the save folder is correctly created
    """
    save_and_archive.site_information.site_name = "TestSite2"
    save_and_archive.create_save_folder()
    expected_path = tmp_path / "test_folder"
    assert expected_path.exists()
    assert expected_path.is_dir()
    assert save_and_archive.full_folder_location == expected_path


def test_create_save_folder_existing(save_and_archive, tmp_path):
    """
    Tests that no save folder made when existing.
    """
    (tmp_path / "test_folder").mkdir()
    with pytest.raises(FileExistsError):
        save_and_archive.create_save_folder()


def test_append_hash_to_folder_name(save_and_archive, tmp_path):
    folder_path = tmp_path / "test_folder"
    folder_path.mkdir()
    (folder_path / "data_audit_log").mkdir()
    (folder_path / "data_audit_log" / "unknown").mkdir()
    hash_file = folder_path / "data_audit_log" / "unknown" / "hash.txt"
    hash_file.write_text("123456abcdef")
    new_path = save_and_archive.append_hash_to_folder_name(folder_path)
    assert new_path == tmp_path / "test_folder_123456"
    assert new_path.exists()
    assert not folder_path.exists()


# def sample_flags_data():
#     return pd.DataFrame(
#         {
#             "date_time": pd.date_range(
#                 start="2023-01-01", periods=5, freq="h"
#             ),
#             "epithermal_neutrons_raw": [
#                 "UNFLAGGED",
#                 "UNFLAGGED",
#                 "BAD",
#                 "UNFLAGGED",
#                 "UNFLAGGED",
#             ],
#             "epithermal_neutrons_cph": [
#                 "UNFLAGGED",
#                 "BAD",
#                 "UNFLAGGED",
#                 "UNFLAGGED",
#                 "UNFLAGGED",
#             ],
#             "air_pressure": [
#                 "UNFLAGGED",
#                 "UNFLAGGED",
#                 "UNFLAGGED",
#                 "BAD",
#                 "UNFLAGGED",
#             ],
#             "air_relative_humidity": [
#                 "BAD",
#                 "UNFLAGGED",
#                 "UNFLAGGED",
#                 "UNFLAGGED",
#                 "UNFLAGGED",
#             ],
#             "air_temperature": [
#                 "UNFLAGGED",
#                 "UNFLAGGED",
#                 "UNFLAGGED",
#                 "UNFLAGGED",
#                 "BAD",
#             ],
#         }
#     ).set_index("date_time")


# def sample_site_information():
#     site_information = SiteInformation(
#         site_name="Test_Site",
#         latitude=51.37,
#         longitude=12.55,
#         elevation=140,
#         reference_incoming_neutron_value=150,
#         dry_soil_bulk_density=1.4,
#         lattice_water=0.01,
#         soil_organic_carbon=0,
#         n0=700,
#         cutoff_rigidity=2.94,
#         site_biomass=1,
#     )
#     return site_information


# df = sample_crns_data()
# flag_df = sample_flags_data()
# site_info = sample_site_information()

# DataAuditLog.create()


# @log_key_step("f")
# def dummyfunc(f=1):
#     return f


# dummyfunc()


# test_saver = SaveAndArchiveOutputs(
#     "process_test_site",
#     processed_data_frame=df,
#     flag_data_frame=flag_df,
#     site_information=site_info,
#     append_yaml_hash_to_folder_name=True,
# )
# test_saver.save_outputs()
