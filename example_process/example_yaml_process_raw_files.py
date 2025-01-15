# import pandas as pd
from pathlib import Path
from neptoon.workflow.process_with_yaml import ProcessWithYaml
from neptoon.config import ConfigurationManager
from neptoon.data_audit import DataAuditLog


config = ConfigurationManager()

station_config_path = Path("./configuration_files/A101_station.yaml")
processing_config_path = Path(
    "./configuration_files/v1_processing_method.yaml"
)

config.load_configuration(
    file_path=station_config_path,
)
config.load_configuration(
    file_path=processing_config_path,
)

DataAuditLog.create()
yaml_processor = ProcessWithYaml(configuration_object=config)

## OPTION 1:
# data_hub = yaml_processor.create_data_hub()

## OPTION 2:
yaml_processor.run_full_process()

yaml_processor.data_hub.create_figures()
