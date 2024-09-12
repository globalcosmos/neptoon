# import pandas as pd

from neptoon.data_management.process_with_yaml import ProcessWithYaml
from neptoon.configuration.configuration_input import ConfigurationManager

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
# data_hub = yaml_processor.create_data_hub()
yaml_processor.create_data_hub(return_data_hub=False)
yaml_processor._attach_nmdb_data()
yaml_processor._prepare_static_values()

yaml_processor.data_hub.crns_data_frame
