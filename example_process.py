from pathlib import Path
import math
import pandas as pd
from neptoon.quality_assesment.quality_assesment import (
    QualityAssessmentFlagBuilder,
    FlagRangeCheck,
    FlagSpikeDetectionUniLOF,
)

from neptoon.data_management.crns_data_hub import CRNSDataHub

from neptoon.data_management.site_information import SiteInformation

from neptoon.neutron_correction.neutron_correction import (
    CorrectionType,
    CorrectionTheory,
)
from neptoon.neutron_correction.correction_classes import Correction

from neptoon.data_management.data_audit import (
    DataAuditLog,
)
from neptoon.data_ingest_and_formatting.data_ingest import (
    ManageFileCollection, 
    ParseFilesIntoDataFrame,
    FormatDataForCRNSDataHub,
)

import logging
logger = logging.getLogger(__name__)
import time
import streamlit as st

def import_crns_dataframe_and_format(filename):
    """
    This is a pseudo function that will eventually be replaced by the
    ingest routines. For now it converts a sample dataset into a format
    (which we can update later).
    """
    cwd = Path.cwd()
    crns_df_path = cwd / "tests" / "sample_crns_data" / filename
    crns_df = pd.read_csv(crns_df_path)
    crns_df["date_time_utc"] = pd.to_datetime(
        crns_df["date_time_utc"], dayfirst=True
    )
    crns_df.set_index(crns_df["date_time_utc"], inplace=True)
    crns_df.drop(["date_time_utc"], axis=1, inplace=True)
    crns_df = crns_df.replace("noData", math.nan)
    crns_df["epithermal_neutrons"] = pd.to_numeric(
        crns_df["epithermal_neutrons"]
    )
    crns_df["thermal_neutrons"] = pd.to_numeric(crns_df["thermal_neutrons"])
    crns_df["air_temperature"] = pd.to_numeric(crns_df["air_temperature"])
    crns_df["air_relative_humidity"] = pd.to_numeric(
        crns_df["air_relative_humidity"]
    )
    crns_df["precipitation"] = pd.to_numeric(crns_df["precipitation"])
    crns_df["air_pressure"] = pd.to_numeric(crns_df["air_pressure"])

    return crns_df


def run(*args, **kwargs):

    logger.info("🏃 Create audit log ")
    DataAuditLog.create()

    logger.info("🏃 Import CSV")
    crns_df = import_crns_dataframe_and_format("CUC001.csv")
    
    logger.info("🏃 Make site information")
    site_information = SiteInformation(
        latitude=51.37,
        longitude=12.55,
        elevation=140,
        reference_incoming_neutron_value=150,
        bulk_density=1.4,
        lattice_water=0.01,
        soil_organic_carbon=0,
        # mean_pressure=900,
        cutoff_rigidity=2.94,
    )

    site_information.add_custom_value("n0", 1000)
    site_information.add_custom_value("biomass", 1)

    logger.info("🏃 Make DataHub")
    data_hub = CRNSDataHub(
        crns_data_frame=crns_df, site_information=site_information
    )
    data_hub.validate_dataframe(schema="initial_check")

    logger.info("🏃 Attach NMDB data")
    data_hub.attach_nmdb_data(
    station = "JUNG",
    new_column_name = "incoming_neutron_intensity",
    resolution = "60",
    nmdb_table = "revori"
    )

    logger.info("🏃 Flagging")
    qa_flags = QualityAssessmentFlagBuilder()
    qa_flags.add_check(
        FlagRangeCheck("air_relative_humidity", min_val=0, max_val=100),
        FlagRangeCheck("precipitation", min_val=0, max_val=20),
        FlagSpikeDetectionUniLOF("epithermal_neutrons"),
        # ...
    )

    data_hub.apply_quality_flags(custom_flags=qa_flags)

    logger.info("🏃 Corrections")
    data_hub.select_correction(
        correction_type=CorrectionType.INCOMING_INTENSITY,
        correction_theory=CorrectionTheory.ZREDA_2012,
    )
    data_hub.select_correction(
        correction_type=CorrectionType.HUMIDITY,
        correction_theory=CorrectionTheory.ROSOLEM_2013
    )

    data_hub.select_correction(
        correction_type=CorrectionType.PRESSURE,
    )

    # data_hub.select_correction(
    #     correction_type=CorrectionType.ABOVE_GROUND_BIOMASS
    # )

    data_hub.correct_neutrons()

    logger.info("🏃 Produce soil moisture")
    data_hub.produce_soil_moisture_estimates()

    logger.info("🏃 Saving audit log")
    DataAuditLog.archive_and_delete_log(site_name="TestQA")

    logger.info("✅ Finished task")

    st.session_state["data"] = data_hub.crns_data_frame