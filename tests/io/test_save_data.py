import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import Mock
from neptoon.io.save import SaveAndArchiveOutputs
from neptoon.config.configuration_input import SensorInfo

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
    site_info = Mock(spec=SensorInfo)
    site_info.name = "TestSite"
    return processed_df, flag_df, site_info


@pytest.fixture
def save_and_archive(sample_data, tmp_path):
    processed_df, flag_df, site_info = sample_data
    return SaveAndArchiveOutputs(
        folder_name="test_folder",
        processed_data_frame=processed_df,
        flag_data_frame=flag_df,
        sensor_info=site_info,
        save_folder_location=tmp_path,
    )


def test_init(save_and_archive, tmp_path):
    """
    Tests intantiation of SaveAndArchiveOutputs
    """
    assert save_and_archive.folder_name == "test_folder"
    assert save_and_archive.save_folder_location == tmp_path
    assert save_and_archive.append_timestamp
    assert not save_and_archive.use_custom_column_names
    assert save_and_archive.custom_column_names_dict is None


def test_validate_save_folder(save_and_archive, tmp_path):
    """
    Tests that the folder name validation works as expected.
    """
    assert save_and_archive._validate_save_folder(tmp_path) == tmp_path
    assert save_and_archive._validate_save_folder(str(tmp_path)) == tmp_path
    assert save_and_archive._validate_save_folder(None) == Path.cwd()


def test_append_hash_to_folder_name(save_and_archive, tmp_path):
    """
    Test appending the hash to the folder.
    """
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


def test_mask_bad_data(save_and_archive):
    """
    Test data masking
    """
    masked_df = save_and_archive.mask_bad_data()
    assert pd.isna(masked_df["epithermal_neutrons_raw"][3])
    assert pd.isna(masked_df["epithermal_neutrons_cph"][1])
    assert pd.isna(masked_df["epithermal_neutrons_cph"][2])
    assert masked_df["epithermal_neutrons_raw"][0] == 100
