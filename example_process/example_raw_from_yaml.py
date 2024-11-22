# import pandas as pd
from pathlib import Path
from neptoon.data_management.process_with_yaml import ProcessWithYaml
from neptoon.configuration.configuration_input import ConfigurationManager
from neptoon.data_management.data_audit import DataAuditLog

# from neptoon.quality_assesment.quality_assesment import FlagRangeCheck
import logging

logger = logging.getLogger(__name__)
import streamlit as st


def load_configuration():

    logger.info("🏃 Loading configuration ")

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

    logger.info("🏃 Processing configuration ")
    DataAuditLog.create()
    yaml_processor = ProcessWithYaml(configuration_object=config)

    logger.info("🏃 Creating Data Hub ")

    ## OPTION 1:
    yaml_processor.create_data_hub(return_data_hub=False)

    logger.info("✅ Done")

    return yaml_processor


def run_full_process(yaml_processor):

    ## OPTION 2:
    logger.info("🏃 Processing data... ")
    # yaml_processor.run_full_process()

    yaml_processor.create_data_hub(return_data_hub=False)
    logger.info("🏃 Attaching NMDB ")
    yaml_processor._attach_nmdb_data()
    yaml_processor._prepare_static_values()
    # QA raw N spikes
    logger.info("🏃 Quality assessment ")
    yaml_processor._apply_quality_assessment(
        name_of_section="flag_raw_neutrons",
        partial_config=(
            yaml_processor.process_info.neutron_quality_assessment.flag_raw_neutrons
        ),
    )
    logger.info("🏃 Corrections ")
    yaml_processor._select_corrections()
    yaml_processor._correct_neutrons()
    logger.info("🏃 Quality assessment ")
    yaml_processor._apply_quality_assessment(
        name_of_section="flag_corrected_neutrons",
        partial_config=(
            yaml_processor.process_info.neutron_quality_assessment.flag_raw_neutrons
        ),
    )
    logger.info("🏃 Soil moisture conversion ")
    yaml_processor._produce_soil_moisture_estimates()
    logger.info("🏃 Saving output ")
    yaml_processor._save_data()

    logger.info("✅ Done")
    return yaml_processor

    # yaml_processor.data_hub.crns_data_frame
