from neptoon.configuration.configuration_input import (
    # ConfigurationObject,
    ConfigurationManager,
    PreLoadConfigurationYaml,
)

# import yaml
from pathlib import Path

# import pickle
import pytest


def test_configuration_management_integration_test():
    """
    The canary.

    Integration test to ensure the  total process is running as we
    expect. Will load, validate and get the test_station.yaml file.
    """
    mock_file_path = Path(__file__).parent / "mock_data" / "test_station.yaml"
    config_manager = ConfigurationManager()
    config_manager.load_and_validate_configuration("station", mock_file_path)
    station_object = config_manager.get_configuration("station")

    assert station_object.general_site_metadata.site_country == "Germany"
    assert type(station_object.crns_sensor_information.multiple_tubes) is bool
    assert (
        station_object.timeseries_data_format.key_column_names.thermal_neutrons
        is None
    )
    assert (
        station_object.calibration_data_format.key_column_names.profile
        == "PROF"
    )


def test_loading_yaml_file():
    """
    Test initial loading of YAML file is as expected.
    """
    mock_file_path = Path(__file__).parent / "mock_data" / "test_station.yaml"
    loader = PreLoadConfigurationYaml()
    loader.import_whole_yaml_file(mock_file_path)

    assert type(loader.whole_yaml_file) is dict


# def test_configuration_object_creation():
#     """
#     Test to check that the recursive configuration object creation
#     occurs as expected. It is checked against a pickled version.
#     """
#     mock_file_path = Path(__file__).parent / "mock_data" / "test_station.yaml"
#     pickle_file_path = Path(__file__).parent / "mock_data" / "config_obj.pkl"

#     with open(mock_file_path, "r") as file:
#         yaml_file = yaml.safe_load(file)
#         whole_yaml_file = yaml_file

#     output = ConfigurationObject(whole_yaml_file)
#     output_dict = output.to_dict()

#     with open(pickle_file_path, "rb") as pkl_file:
#         expected_output = pickle.load(pkl_file)
#         expected_output_dict = expected_output.to_dict()

#     assert output_dict == expected_output_dict


def test_configuration_management_integration_fail():
    """
    Tests the NameError designed to prevent unexpected naming of
    configuration files
    """
    mock_file_path = Path(__file__).parent / "mock_data" / "test_station.yaml"
    config_manager = ConfigurationManager()
    with pytest.raises(NameError):
        config_manager.load_and_validate_configuration(
            "bad_name", mock_file_path
        )
