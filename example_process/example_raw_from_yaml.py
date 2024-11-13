# import pandas as pd
from pathlib import Path
from neptoon.products.process_with_yaml import ProcessWithYaml
from neptoon.config.configuration_input import ConfigurationManager
from neptoon.quality_control.data_audit import DataAuditLog

config = ConfigurationManager()

station_config_path = Path.cwd() / "configuration_files" / "A101_station.yaml"
processing_config_path = (
    Path.cwd() / "configuration_files" / "v1_processing_method.yaml"
)

config.load_and_validate_configuration(
    name="station",
    file_path=station_config_path,
)
config.load_and_validate_configuration(
    name="processing",
    file_path=processing_config_path,
)

DataAuditLog.create()
yaml_processor = ProcessWithYaml(configuration_object=config)

## OPTION 1:
data_hub = yaml_processor.create_data_hub()

## OPTION 2:
yaml_processor.run_full_process()
data_hub.site_information
yaml_processor.data_hub.crns_data_frame
