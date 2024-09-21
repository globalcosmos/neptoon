# import pandas as pd
from pathlib import Path
from neptoon.data_management.process_with_yaml import ProcessWithYaml
from neptoon.configuration.configuration_input import ConfigurationManager

# from neptoon.quality_assesment.quality_assesment import FlagRangeCheck

config = ConfigurationManager()

station_config_path = Path("./configuration_files/A101_station.yaml")
processing_config_path = Path(
    "./configuration_files/v1_processing_method.yaml"
)
config.load_and_validate_configuration(
    name="station",
    file_path=station_config_path,
)
config.load_and_validate_configuration(
    name="processing",
    file_path=processing_config_path,
)
y = config.get_configuration("processing")

# tmp = config.get_configuration('station')
yaml_processor = ProcessWithYaml(configuration_object=config)

## OPTION 1:
# data_hub = yaml_processor.create_data_hub()

## OPTION 2:
yaml_processor.run_full_process()
