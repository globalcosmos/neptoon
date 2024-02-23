from cosmosbase.configuration.configuration_input import (
    ConfigurationObject,
    ConfigurationManager,
)
import yaml
from pathlib import Path
import pickle


def test_configuration_object_creation():
    """
    Test to check that the recursive configuration object creation
    occurs as expected. It is checked against a pickled version.
    """
    mock_file_path = Path(__file__).parent / "mock_data" / "test_station.yaml"
    pickle_file_path = Path(__file__).parent / "mock_data" / "config_obj.pkl"

    with open(mock_file_path, "r") as file:
        yaml_file = yaml.safe_load(file)
        whole_yaml_file = yaml_file

    output = ConfigurationObject(whole_yaml_file)
    output_dict = output.to_dict()

    with open(pickle_file_path, "rb") as pkl_file:
        expected_output = pickle.load(pkl_file)
        expected_output_dict = expected_output.to_dict()

    assert output_dict == expected_output_dict
