from neptoon.config.configuration_input import ConfigurationManager, BaseConfig

from pathlib import Path

# import pytest


def test_returned_config_config_type():
    """
    Assert the config is stored as a BaseConfig type
    """
    mock_file_path = Path(__file__).parent / "mock_data" / "test_station.yaml"
    config_manager = ConfigurationManager()
    config_manager.load_configuration(mock_file_path)
    station_object = config_manager.get_config("sensor")
    assert isinstance(station_object, BaseConfig)


def test_configuration_management_integration_test():
    """
    The canary.

    Integration test to ensure the  total process is running as we
    expect. Will load, validate and get the test_station.yaml file.
    """
    mock_file_path = Path(__file__).parent / "mock_data" / "test_station.yaml"
    config_manager = ConfigurationManager()
    config_manager.load_configuration(mock_file_path)
    station_object = config_manager.get_config("sensor")

    assert station_object.sensor_info.country == "Germany"
    assert (
        station_object.time_series_data.key_column_info.thermal_neutrons
        is None
    )
    assert station_object.calibration.key_column_names.profile == "PROF"


# def test_loading_yaml_file():
#     """
#     Test initial loading of YAML file is as expected.
#     """
#     mock_file_path = Path(__file__).parent / "mock_data" / "test_station.yaml"
#     loader = PreLoadConfigurationYaml()
#     loader.import_whole_yaml_file(mock_file_path)

#     assert type(loader.whole_yaml_file) is dict


# def test_configuration_management_integration_fail():
#     """
#     Tests the NameError designed to prevent unexpected naming of
#     configuration files
#     """
#     mock_file_path = Path(__file__).parent / "mock_data" / "test_station.yaml"
#     config_manager = ConfigurationManager()
#     with pytest.raises(NameError):
#         config_manager.load_and_validate_configuration(
#             "bad_name", mock_file_path
#         )
