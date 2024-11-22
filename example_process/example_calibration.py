# %%
import pandas
from pathlib import Path
from neptoon.calibration.station_calibration import (
    CalibrationConfiguration,
    CalibrationStation,
)

import logging

logger = logging.getLogger(__name__)
import streamlit as st


# %%
def calibrate(
    sampling_csv,
    crns_csv,
    *args,
    **kwargs,
):

    logger.info("🏃 Loading data ")
    calibration_data = pandas.read_csv(
        (Path.cwd() / Path(sampling_csv)),
        skipinitialspace=True,
    )
    crns_data = pandas.read_csv(
        Path.cwd() / Path(crns_csv),
        index_col=0,
        parse_dates=True,
    )

    calib_config = CalibrationConfiguration(
        date_time_column_name="DateTime_utc",
        distance_column="Distance_to_CRNS_m",
        sample_depth_column="Profile_Depth_cm",
        bulk_density_of_sample_column="DryBulkDensity_g_cm3",
        soil_moisture_gravimetric_column="SoilMoisture_g_g",
        soil_organic_carbon_column="SoilOrganicCarbon_g_g",
        lattice_water_column="LatticeWater_g_g",
        profile_id_column="Profile_ID",
        air_humidity_column_name="AirHumidity_gapfilled",
        neutron_column_name="NeutronCount_Epithermal_MovAvg24h_corrected",
    )

    calibration_station = CalibrationStation(
        calibration_data=calibration_data,
        time_series_data=crns_data,
        config=calib_config,
    )

    logger.info("🏃 Optimizing N0 ")

    estimate_n0 = calibration_station.find_n0_value()
    # print(f"N0 number is {estimate_n0}")

    logger.info("✅ Done")

    return (
        estimate_n0,
        crns_data,
        calibration_station.return_calibration_results_data_frame(),
    )
