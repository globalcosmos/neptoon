# import pandas as pd
from pathlib import Path
from neptoon.workflow.process_with_yaml import (
    ProcessWithYaml,
)
from neptoon.config import ConfigurationManager
from neptoon.data_audit import DataAuditLog

config = ConfigurationManager()

sensor_config_path = Path.cwd() / "configuration_files" / "A101_station.yaml"
processing_config_path = (
    Path.cwd() / "configuration_files" / "v1_processing_method.yaml"
)

config.load_configuration(
    file_path=sensor_config_path,
)
config.load_configuration(
    file_path=processing_config_path,
)

# DataAuditLog.create()
yaml_processor = ProcessWithYaml(configuration_object=config)


#### START TEMPORARY
from neptoon.workflow.process_with_yaml import QualityAssessmentWithYaml
from neptoon.quality_control.saqc_methods_and_params import YamlRegistry
from neptoon.quality_control import QualityCheck

yaml_processor.create_data_hub(return_data_hub=False)
yaml_processor._attach_nmdb_data()
yaml_processor._prepare_static_values()
yaml_processor._apply_quality_assessment(
    name_of_target="raw_neutrons",
    partial_config=yaml_processor.process_info.neutron_quality_assessment,
)


yaml_processor._apply_quality_assessment(
    partial_config=yaml_processor.station_info.input_data_qa,
    name_of_target=None,
)


# qa_builder = QualityAssessmentWithYaml(
#     partial_config=yaml_processor.process_info.neutron_quality_assessment,
#     station_info=yaml_processor.station_info,
#     name_of_target="raw_neutrons",
# )

# qa_dict = qa_builder.partial_config.model_dump()

# # If name of target use that, else loop through targets.
# name_of_target = "raw_neutrons"
# target_dict = qa_dict["raw_neutrons"]


# for check_method, check_params in target_dict.items():
#     if isinstance(check_params, dict):
#         target = YamlRegistry.get_target(name_of_target)
#         method = YamlRegistry.get_method(check_method)
#         params = check_params
#         check = QualityCheck(target=target, method=method, parameters=params)


### END


## OPTION 1:
data_hub = yaml_processor.create_data_hub()

## OPTION 2:
yaml_processor.run_full_process()
# data_hub.site_information
yaml_processor.data_hub.crns_data_frame
