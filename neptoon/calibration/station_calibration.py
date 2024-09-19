import pandas as pd
import numpy as np
from neptoon.data_management.column_information import ColumnInfo


class SampleProfile:

    latest_pid = 0

    __slots__ = [
        # Input
        "pid",  # arbitrary profile id
        "soil_moisture_gravimetric",  # soil moisture values in g/g
        "sm_total_grv",  # soil moisture values in g/g
        "sm_total_vol",  # soil moisture values in g/g
        "depth",  # depth values in cm
        "bulk_density",  # bulk density
        "bulk_density_mean",
        "distance",  # distance from the CRNS in m
        "lattice_water",  # lattice water in g/g
        "soil_organic_carbon",  # soil organic carbon in g/g
        # Calculated
        "D86",  # penetration depth
        "w_r",  # radial weight of this profile
        "sm_total_weghted_avg_vol",  # vertically weighted average sm
        "sm_total_weighted_avg_grv",  # vertically weighted average sm
        "data",  # DataFrame
    ]

    def __init__(
        self,
        soil_moisture_gravimetric,
        depth,
        bulk_density,
        distance=1,
        lattice_water=None,
        soil_organic_carbon=None,
        pid=None,
    ):
        """
        Initialise SampleProfile instance.

        Parameters
        ----------
        soil_moisture_gravimetric : array
            array of soil moisture gravimetric values in g/g
        depth : array
            The depth of each soil moisture sample
        bulk_density : array
            bulk density of the samples in g/cm^3
        distance : int, optional
            distance of the profile from the sensor, by default 1
        lattice_water : array-like, optional
            Lattice water from the samples , by default 0
        soil_organic_carbon : int, optional
            _description_, by default 0
        pid : _type_, optional
            _description_, by default None
        """

        # Vector data
        if pid is None:
            SampleProfile.latest_pid += 1
            self.pid = SampleProfile.latest_pid
        else:
            self.pid = pid

        self.soil_moisture_gravimetric = np.array(soil_moisture_gravimetric)
        self.depth = np.array(depth)
        self.bulk_density = np.array(bulk_density)
        self.bulk_density_mean = np.array(bulk_density).mean()
        self.soil_organic_carbon = (
            np.array(soil_organic_carbon)
            if soil_organic_carbon is None
            else np.zeros_like(soil_moisture_gravimetric)
        )
        self.lattice_water = self.lattice_water = (
            np.array(lattice_water)
            if lattice_water is not None
            else np.zeros_like(soil_moisture_gravimetric)
        )
        self.data = None
        self.update_data()

        # Scalar values
        self.distance = distance
        self.D86 = np.nan
        self.sm_tot_wavg_grv = np.nan
        self.sm_tot_wavg_vol = np.nan
        self.w_r = np.nan

    def update_data(self):
        """
        Update the internal DataFrame with current values and perform
        calculations.
        """
        if not self.data:
            self.data = pd.DataFrame()

        self.data["pid"] = self.pid
        self.data["soil_moisture_gravimetric"] = self.soil_moisture_gravimetric
        self.data["depth"] = self.depth
        self.data["bulk_density"] = self.bulk_density
        self.data["lattice_water"] = self.lattice_water
        self.data["soil_organic_carbon"] = self.soil_organic_carbon

        if "weight" not in self.data.columns:
            self.data["weight"] = np.nan

        self._calculate_sm_total_vol()
        self._calculate_sm_total_grv()
        self.data["sm_tot_vol"] = self.sm_tot_vol
        self.data["sm_tot_grv"] = self.sm_tot_grv

    def _calculate_sm_total_vol(self):
        """
        Calculate total volumetric soil moisture.
        """
        sm_tot_vol = (
            self.data["soil_moisture_gravimetric"]
            + self.data["lattice_water"]
            + self.data["soil_organic_carbon"] * 0.555
        ) * self.data["bulk_density"]
        self.sm_tot_vol = sm_tot_vol

    def _calculate_sm_total_grv(self):
        """
        Calculate total gravimetric soil moisture.
        """
        sm_tot_grv = (
            self.data["soil_moisture_gravimetric"]
            + self.data["lattice_water"]
            + self.data["soil_organic_carbon"] * 0.555
        )
        self.sm_tot_grv = sm_tot_grv


class PrepareCalibrationData:

    def __init__(
        self,
        calibration_data_frame: pd.DataFrame,
        date_time_column_name: str = str(ColumnInfo.Name.DATE_TIME),
        sample_depth_column: str = str(ColumnInfo.Name.CALIB_DEPTH_OF_SAMPLE),
        distance_column: str = str(ColumnInfo.Name.CALIB_DISTANCE_TO_SENSOR),
        bulk_density_of_sample_column: str = str(
            ColumnInfo.Name.CALIB_BULK_DENSITY
        ),
    ):
        self.calibration_data_frame = calibration_data_frame
        self.date_time_column_name = date_time_column_name
        self.sample_depth_column = sample_depth_column
        self.distance_column = distance_column
        self.bulk_density_of_sample_column = bulk_density_of_sample_column
        self._ensure_date_time_index()

        self.unique_calibration_days = np.unique(
            self.calibration_data_frame[self.date_time_column_name]
        )
        self.list_of_profiles = []

    def _ensure_date_time_index(self):

        self.calibration_data_frame[self.date_time_column_name] = (
            pd.to_datetime(
                self.calibration_data_frame[self.date_time_column_name],
                utc=True,
            )
        )
