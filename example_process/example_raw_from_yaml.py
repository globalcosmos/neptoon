# import pandas as pd
from pathlib import Path
from neptoon.data_management.process_with_yaml import ProcessWithYaml
from neptoon.configuration.configuration_input import ConfigurationManager
from neptoon.data_management.data_audit import DataAuditLog

# from neptoon.quality_assesment.quality_assesment import FlagRangeCheck


def load_configuration():
    config = ConfigurationManager()

    # abspath = Path.cwd()
    abspath = Path("example_process")

    station_config_path = (
        abspath / "configuration_files" / "Sheepdrove02.yaml"
    )  # "A101_station.yaml"
    processing_config_path = (
        abspath / "configuration_files" / "v1_processing_method.yaml"
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
    yaml_processor.create_data_hub(return_data_hub=False)

    return yaml_processor


def run_full_process(yaml_processor):

    ## OPTION 2:
    yaml_processor.run_full_process()

    return yaml_processor

    # yaml_processor.data_hub.crns_data_frame
