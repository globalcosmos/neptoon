# import pandas as pd
from pathlib import Path
from neptoon.workflow import ProcessWithYaml
from neptoon.config import ConfigurationManager
from magazine import Magazine, Publish

Magazine.active = True

# from neptoon.data_audit import DataAuditLog

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


# Magazine.topics
# with Publish("Report-FSC001_station.pdf", "FSC001 data") as M:
#     for topic in Magazine.topics:
#         M.add_topic(topic)
#         M.add_figure(topic)
