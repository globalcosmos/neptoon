import pandas as pd

from neptoon.data_management.process_with_yaml import ProcessWithYaml
from neptoon.configuration.configuration_input import ConfigurationManager

config = ConfigurationManager()
config.load_and_validate_configuration(
    "station",
    "/Users/power/Documents/code/neptoon/configuration_files/A101_station.yaml",
)
station_config = config.get_configuration("station")
