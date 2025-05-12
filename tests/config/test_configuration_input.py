from neptoon.config.configuration_input import ConfigurationManager, BaseConfig

from pathlib import Path
import tempfile
import yaml
from copy import deepcopy
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
        station_object.time_series_data.key_column_info.thermal_neutron_columns
        is None
    )
    assert (
        station_object.calibration.key_column_names.profile_id == "Profile_ID"
    )

def test_working_dir_system():
    """
    Test the working_directory functionality using a
    platform-independent approach.
    
    This test verifies: 1. Default behavior: paths are resolved relative
    to config file location 2. Custom behavior: paths are resolved
    relative to specified working_directory
    """

    
    mock_file_path = Path(__file__).parent / "mock_data" / "test_station.yaml"
    
    with open(mock_file_path, 'r') as f:
        original_config = yaml.safe_load(f)
    
    # Create temporary directory for test
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir).resolve()
        
        # Create a copy of the YAML in the temp directory
        temp_yaml_path = temp_dir_path / "temp_test_station.yaml"
        
        # Make nested data directory
        data_dir_name = "custom_data_dir"
        data_dir = temp_dir_path / data_dir_name
        data_dir.mkdir()
        
        # 1. First test: Default behavior (no working_directory)
        with open(temp_yaml_path, 'w') as f:
            # Add a relative path to be resolved
            modified_config = deepcopy(original_config)
            if 'raw_data_parse_options' not in modified_config:
                modified_config['raw_data_parse_options'] = {}
            modified_config['raw_data_parse_options']['data_location'] = data_dir_name
            yaml.dump(modified_config, f)
        
        # Load the config
        config_manager = ConfigurationManager()
        config_manager.load_configuration(str(temp_yaml_path))
        sensor_config = config_manager.get_config("sensor")
        
        # Verify resolved path is a child of the config directory
        actual_path = Path(sensor_config.raw_data_parse_options.data_location).resolve()
        assert actual_path.is_relative_to(temp_dir_path), \
            f"Default resolution: Path {actual_path} should be under {temp_dir_path}"
        assert actual_path.name == data_dir_name, \
            f"Default resolution: Path should end with {data_dir_name}, got {actual_path.name}"
        
        # 2. Second test: With working_directory specified
        with tempfile.TemporaryDirectory() as working_dir:
            working_dir_path = Path(working_dir).resolve()
            
            # Create the same directory structure in working_dir
            working_data_dir = working_dir_path / data_dir_name
            working_data_dir.mkdir()
            
            # Modify config to include working_directory
            modified_config['working_directory'] = str(working_dir_path)
            
            with open(temp_yaml_path, 'w') as f:
                yaml.dump(modified_config, f)
            
            # Load the modified config
            config_manager = ConfigurationManager()
            config_manager.load_configuration(str(temp_yaml_path))
            sensor_config = config_manager.get_config("sensor")
            
            # Verify resolved path is a child of the working directory
            actual_path = Path(sensor_config.raw_data_parse_options.data_location).resolve()
            assert actual_path.is_relative_to(working_dir_path), \
                f"Working dir resolution: Path {actual_path} should be under {working_dir_path}"
            assert actual_path.name == data_dir_name, \
                f"Working dir resolution: Path should end with {data_dir_name}, got {actual_path.name}"