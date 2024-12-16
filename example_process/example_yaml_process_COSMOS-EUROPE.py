# import pandas as pd
from pathlib import Path
from neptoon.workflow import ProcessWithYaml
from neptoon.config import ConfigurationManager
from neptoon.data_audit import DataAuditLog


config = ConfigurationManager()

station_config_path = (
    Path.cwd() / "configuration_files" / "FSC001_station.yaml"
)
processing_config_path = (
    Path.cwd() / "configuration_files" / "v1_processing_method.yaml"
)
config.load_configuration(
    file_path=station_config_path,
)
config.load_configuration(
    file_path=processing_config_path,
)

yaml_processor = ProcessWithYaml(configuration_object=config)

## OPTION 1:
# data_hub = yaml_processor.create_data_hub()

## OPTION 2:
# DataAuditLog.create()
yaml_processor.run_full_process()
