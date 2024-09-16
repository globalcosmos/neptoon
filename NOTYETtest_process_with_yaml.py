# import pandas as pd

from neptoon.data_management.process_with_yaml import ProcessWithYaml
from neptoon.configuration.configuration_input import ConfigurationManager

# from neptoon.quality_assesment.quality_assesment import FlagRangeCheck

config = ConfigurationManager()
config.load_and_validate_configuration(
    name="station",
    file_path="/Users/power/Documents/code/neptoon/configuration_files/A101_station.yaml",
)
config.load_and_validate_configuration(
    name="processing",
    file_path="/Users/power/Documents/code/neptoon/configuration_files/v1_processing_method.yaml",
)
y = config.get_configuration("processing")

# tmp = config.get_configuration('station')
yaml_processor = ProcessWithYaml(configuration_object=config)

## OPTION 1:
# data_hub = yaml_processor.create_data_hub()

## OPTION 2:
yaml_processor.run_full_process()
x = yaml_processor.data_hub.flags_data_frame
